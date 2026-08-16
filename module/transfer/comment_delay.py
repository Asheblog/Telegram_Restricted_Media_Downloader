# coding=UTF-8
"""Deferred discussion reply capture scheduler for live forward watches."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Optional

from module.persistence.transfer_store import DeferredDiscussionCaptureStatus

log = logging.getLogger('logger_stdout')

Executor = Callable[[dict], Awaitable[Any]]
DelayGetter = Callable[[], int]
CancelHook = Callable[[dict], Any]
ActiveDerivedChecker = Callable[[dict], bool]

_COMMENT_DELAY_MIN = 0
_COMMENT_DELAY_MAX = 1440


def normalize_optional_comment_delay_minutes(value) -> Optional[int]:
    """Parse optional per-watch delay. None/blank = inherit global; 0..1440 = override."""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        minutes = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError('invalid_comment_delay_minutes') from exc
    if minutes < _COMMENT_DELAY_MIN or minutes > _COMMENT_DELAY_MAX:
        raise ValueError('invalid_comment_delay_minutes')
    return minutes


class CommentDelayScheduler:
    def __init__(
            self,
            store,
            delay_minutes_getter: DelayGetter,
            executor: Executor,
            *,
            sleep_seconds: float = 5.0,
            time_fn=time.time,
            on_cancel: Optional[CancelHook] = None,
            has_active_derived: Optional[ActiveDerivedChecker] = None,
    ):
        self.store = store
        self.delay_minutes_getter = delay_minutes_getter
        self.executor = executor
        self.sleep_seconds = float(sleep_seconds)
        self.time_fn = time_fn
        self.on_cancel = on_cancel
        self.has_active_derived = has_active_derived
        self._task: Optional[asyncio.Task] = None
        self._stopped = False
        self._inflight: dict[int, asyncio.Task] = {}

    def start(self, loop=None) -> None:
        """Arm the background tick loop.

        Prefer the caller's explicit ``loop`` so WebUI worker threads can attach
        to the app event loop via ``call_soon_threadsafe``.
        """
        self._stopped = False
        if self._task and not self._task.done():
            return
        target = loop
        if target is None:
            try:
                target = asyncio.get_running_loop()
            except RuntimeError:
                return

        def _arm() -> None:
            if self._stopped:
                return
            if self._task and not self._task.done():
                return
            self._task = asyncio.get_running_loop().create_task(
                self._loop(),
                name='comment-delay-scheduler',
            )

        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is target:
            _arm()
        elif target.is_running():
            target.call_soon_threadsafe(_arm)

    def stop(self) -> None:
        self._stopped = True
        task = self._task
        self._task = None
        if task and not task.done():
            task.cancel()
        for inflight in list(self._inflight.values()):
            if not inflight.done():
                inflight.cancel()

    def _resolve_delay_minutes(self, watch_id: str) -> int:
        if watch_id:
            watch = self.store.get_live_transfer_watch(str(watch_id))
            if watch is not None:
                override = watch.get('comment_delay_minutes')
                if override is not None:
                    return int(override)
        return int(self.delay_minutes_getter() or 0)

    async def schedule(
            self,
            *,
            watch_id: str,
            source_chat_id: str | int,
            source_message_id: int,
            target_chat_id: str | int,
            target_link: str,
            client=None,
    ) -> Optional[dict]:
        delay_minutes = self._resolve_delay_minutes(watch_id)
        if delay_minutes <= 0:
            await self.executor({
                'watch_id': watch_id,
                'source_chat_id': str(source_chat_id),
                'source_message_id': int(source_message_id),
                'target_chat_id': str(target_chat_id),
                'target_link': target_link,
                'client': client,
                'due_at': self.time_fn(),
                'status': DeferredDiscussionCaptureStatus.PENDING,
            })
            return None
        due_at = self.time_fn() + delay_minutes * 60
        return self.store.schedule_deferred_discussion_capture(
            watch_id=watch_id,
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            target_chat_id=target_chat_id,
            target_link=target_link,
            due_at=due_at,
        )

    def cancel(self, capture_id: int) -> bool:
        capture = self.store.get_deferred_discussion_capture(int(capture_id))
        if not capture:
            return False
        status = capture.get('status')
        if status not in (
                DeferredDiscussionCaptureStatus.PENDING,
                DeferredDiscussionCaptureStatus.RUNNING,
        ):
            return False
        ok = self.store.cancel_deferred_discussion_capture(int(capture_id))
        if not ok:
            return False
        inflight = self._inflight.get(int(capture_id))
        if inflight and not inflight.done():
            inflight.cancel()
        if self.on_cancel:
            try:
                self.on_cancel(capture)
            except Exception:
                log.exception('Deferred discussion cancel hook failed: %s', capture_id)
        return True

    def cancel_for_watch(self, watch_id: str) -> int:
        captures = self.store.list_deferred_discussion_captures(watch_id=watch_id, limit=500)
        cancelled = 0
        for capture in captures:
            if capture.get('status') in (
                    DeferredDiscussionCaptureStatus.PENDING,
                    DeferredDiscussionCaptureStatus.RUNNING,
            ):
                if self.cancel(int(capture['id'])):
                    cancelled += 1
        return cancelled

    async def run_now(self, capture_id: int) -> bool:
        capture = self.store.get_deferred_discussion_capture(int(capture_id))
        if not capture or capture.get('status') != DeferredDiscussionCaptureStatus.PENDING:
            return False
        stamp = self.time_fn()
        self.store.mark_deferred_discussion_capture(
            int(capture_id),
            DeferredDiscussionCaptureStatus.RUNNING,
        )
        # Force due immediately for observability.
        with self.store.connect() as conn:
            conn.execute(
                'UPDATE deferred_discussion_captures SET due_at = ?, updated_at = ? WHERE id = ?',
                (stamp, self.store.utc_now(), int(capture_id))
            )
        capture = self.store.get_deferred_discussion_capture(int(capture_id))
        if not capture:
            return False
        await self._execute_capture(capture)
        return True

    async def retry(self, capture_id: int) -> bool:
        capture = self.store.get_deferred_discussion_capture(int(capture_id))
        if not capture:
            return False
        if capture.get('status') not in (
                DeferredDiscussionCaptureStatus.FAILURE,
                DeferredDiscussionCaptureStatus.CANCELLED,
        ):
            return False
        if not self.store.requeue_deferred_discussion_capture(
                int(capture_id),
                due_at=self.time_fn(),
        ):
            return False
        return await self.run_now(int(capture_id))

    def _reclaim_orphaned_running(self) -> int:
        """Requeue running rows with no live worker and no active derived transfers."""
        running = self.store.list_deferred_discussion_captures(
            statuses=[DeferredDiscussionCaptureStatus.RUNNING],
            limit=500,
        )
        keep_ids = {
            capture_id
            for capture_id, task in self._inflight.items()
            if task is not None and not task.done()
        }
        orphan_ids: list[int] = []
        for capture in running:
            capture_id = int(capture['id'])
            if capture_id in keep_ids:
                continue
            if self.has_active_derived and self.has_active_derived(capture):
                continue
            orphan_ids.append(capture_id)
        if not orphan_ids:
            return 0
        requeued = self.store.requeue_running_deferred_discussion_captures(
            orphan_ids,
            due_at=self.time_fn(),
        )
        return len(requeued)

    async def tick_once(self) -> int:
        self._reclaim_orphaned_running()
        claimed = self.store.claim_due_deferred_discussion_captures(now=self.time_fn())
        for capture in claimed:
            await self._execute_capture(capture)
        return len(claimed)

    async def _execute_capture(self, capture: dict) -> None:
        capture_id = int(capture['id']) if capture.get('id') is not None else None
        if capture_id is None:
            await self.executor(capture)
            return

        async def _run() -> None:
            await self.executor(capture)

        task = asyncio.create_task(_run(), name=f'deferred-discussion-{capture_id}')
        self._inflight[capture_id] = task
        try:
            await task
        except asyncio.CancelledError:
            current = self.store.get_deferred_discussion_capture(capture_id)
            if current and current.get('status') == DeferredDiscussionCaptureStatus.RUNNING:
                self.store.cancel_deferred_discussion_capture(capture_id)
            # Per-capture cancel must not abort the scheduler tick loop.
            return
        except Exception as exc:
            log.exception('Deferred discussion capture failed: %s', capture_id)
            current = self.store.get_deferred_discussion_capture(capture_id)
            if current and current.get('status') == DeferredDiscussionCaptureStatus.RUNNING:
                self.store.mark_deferred_discussion_capture(
                    capture_id,
                    DeferredDiscussionCaptureStatus.FAILURE,
                    error_message=str(exc),
                )
        else:
            current = self.store.get_deferred_discussion_capture(capture_id)
            if current and current.get('status') == DeferredDiscussionCaptureStatus.RUNNING:
                self.store.mark_deferred_discussion_capture(
                    capture_id,
                    DeferredDiscussionCaptureStatus.DONE,
                )
        finally:
            self._inflight.pop(capture_id, None)

    async def _loop(self) -> None:
        while not self._stopped:
            try:
                await self.tick_once()
            except Exception:
                log.exception('CommentDelayScheduler tick failed')
            try:
                await asyncio.sleep(self.sleep_seconds)
            except asyncio.CancelledError:
                break
