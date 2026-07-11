# coding=UTF-8
"""Deferred discussion reply capture scheduler for live forward watches."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Optional

from module.transfer_store import DeferredDiscussionCaptureStatus

log = logging.getLogger('logger_stdout')

Executor = Callable[[dict], Awaitable[Any]]
DelayGetter = Callable[[], int]


class CommentDelayScheduler:
    def __init__(
            self,
            store,
            delay_minutes_getter: DelayGetter,
            executor: Executor,
            *,
            sleep_seconds: float = 5.0,
            time_fn=time.time,
    ):
        self.store = store
        self.delay_minutes_getter = delay_minutes_getter
        self.executor = executor
        self.sleep_seconds = float(sleep_seconds)
        self.time_fn = time_fn
        self._task: Optional[asyncio.Task] = None
        self._stopped = False

    def start(self) -> None:
        self._stopped = False
        if self._task and not self._task.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._task = loop.create_task(self._loop(), name='comment-delay-scheduler')

    def stop(self) -> None:
        self._stopped = True
        task = self._task
        self._task = None
        if task and not task.done():
            task.cancel()

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
        delay_minutes = int(self.delay_minutes_getter() or 0)
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
        return self.store.cancel_deferred_discussion_capture(int(capture_id))

    def cancel_for_watch(self, watch_id: str) -> int:
        return self.store.cancel_deferred_discussion_captures_for_watch(watch_id)

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

    async def tick_once(self) -> int:
        claimed = self.store.claim_due_deferred_discussion_captures(now=self.time_fn())
        for capture in claimed:
            await self._execute_capture(capture)
        return len(claimed)

    async def _execute_capture(self, capture: dict) -> None:
        capture_id = int(capture['id']) if capture.get('id') is not None else None
        try:
            await self.executor(capture)
            if capture_id is not None:
                self.store.mark_deferred_discussion_capture(
                    capture_id,
                    DeferredDiscussionCaptureStatus.DONE,
                )
        except Exception as exc:
            log.exception('Deferred discussion capture failed: %s', capture_id)
            if capture_id is not None:
                self.store.mark_deferred_discussion_capture(
                    capture_id,
                    DeferredDiscussionCaptureStatus.FAILURE,
                    error_message=str(exc),
                )

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
