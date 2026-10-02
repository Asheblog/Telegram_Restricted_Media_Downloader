# coding=UTF-8
"""延迟评论区抓取（Deferred Discussion Reply Capture）编排。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出：装配
``CommentDelayScheduler``（executor / on_cancel / 活跃派生判定），把主贴转发后
的讨论区抓取推迟到配置时刻执行，以及"立即调度"入口。

依赖以回调注入 —— 被搬运代码里凡是通过名字间接可达的东西（``self.forward_discussion_replies``、
``self._record_watch_event``、``self.delete_web_task`` 等）都变成注入钩子，
否则宿主的 monkeypatch 会静默失效。
"""
from __future__ import annotations

import time
from typing import Callable, Optional

from module import log
from module.domain.archive_naming.source_folders import normalize_archive_title_source
from module.persistence.transfer_store import (
    DeferredDiscussionCaptureStatus,
    TransferStatus,
)
from module.transfer.comment_delay import CommentDelayScheduler


class DeferredDiscussionOperations:
    """延迟抓取调度器的装配与调度入口。"""

    def __init__(
        self,
        *,
        transfer_store_getter: Callable[[], object],
        user_getter: Callable[[], object],
        app_getter: Callable[[], object],
        gc_getter: Callable[[], object],
        loop_getter: Callable[[], object],
        forward_discussion_replies: Callable[..., object],
        record_watch_event: Callable[..., None],
        delete_web_task: Callable[[int], object],
    ) -> None:
        self._transfer_store = transfer_store_getter
        self._user = user_getter
        self._app = app_getter
        self._gc = gc_getter
        self._loop = loop_getter
        self._forward_discussion_replies = forward_discussion_replies
        self._record_watch_event = record_watch_event
        self._delete_web_task = delete_web_task
        self._scheduler: Optional[CommentDelayScheduler] = None

    # ── 调度器装配 ──

    def scheduler_if_started(self) -> Optional[CommentDelayScheduler]:
        """取已启动的调度器；尚未启动则返回 None（**不**触发启动）。

        删除监听时需要"若调度器已在跑，就取消该监听的延迟抓取"。用本方法而不是
        `ensure_scheduler()`：后者会连带启动调度器（含线程/循环挂载），
        在一个"只是删监听"的调用里产生副作用。
        """
        return self._scheduler

    def ensure_scheduler(self) -> CommentDelayScheduler:
        scheduler = self._scheduler
        if scheduler is None:
            store = self._transfer_store()

            async def executor(capture: dict):
                client = (
                    capture.get("client")
                    or self._user()
                    or getattr(self._app(), "client", None)
                )
                resolve_deep_link = False
                archive_by_author = False
                archive_title_source = "auto"
                watch_id = capture.get("watch_id")
                if watch_id and store is not None:
                    watch = store.get_live_transfer_watch(str(watch_id))
                    if watch:
                        resolve_deep_link = bool(watch.get("resolve_deep_link"))
                        archive_by_author = bool(watch.get("archive_by_author"))
                        archive_title_source = normalize_archive_title_source(
                            watch.get("archive_title_source")
                        )
                count = await self._forward_discussion_replies(
                    client=client,
                    source_chat_id=capture.get("source_chat_id"),
                    source_message_id=int(capture.get("source_message_id")),
                    target_chat_id=capture.get("target_chat_id"),
                    target_link=capture.get("target_link"),
                    watch_id=capture.get("watch_id"),
                    resolve_deep_link=resolve_deep_link,
                    archive_by_author=archive_by_author,
                    archive_title_source=archive_title_source,
                )
                watch_id = capture.get("watch_id")
                if watch_id:
                    self._record_watch_event(
                        watch_id,
                        capture.get("source_chat_id"),
                        capture.get("source_message_id"),
                        capture.get("target_chat_id"),
                        capture.get("target_link"),
                        "success" if count else "skipped",
                        f"延迟抓取评论区完成,匹配{count}条",
                    )
                return count

            def on_cancel(capture: dict):
                self.cancel_derived_tasks(capture)

            scheduler = CommentDelayScheduler(
                store=store,
                delay_minutes_getter=lambda: self._gc().get_comment_delay_minutes(),
                executor=executor,
                on_cancel=on_cancel,
                has_active_derived=self.has_active_derived_tasks,
            )
            self._scheduler = scheduler
        # 每次都重新 arm：首次调用可能来自没有运行 loop 的 WebUI 工作线程，
        # 传入 app loop 以便 start 走 call_soon_threadsafe。
        scheduler.start(loop=self._loop())
        return scheduler

    # ── 派生任务判定与取消 ──

    def _derived_tasks_started_after(self, capture: dict):
        """按 capture 的 updated_at 过滤出"本次抓取派生"的活跃任务。"""
        if not capture:
            return
        watch_id = capture.get("watch_id")
        if not watch_id:
            return
        store = self._transfer_store()
        started_at = str(capture.get("updated_at") or "")
        for task in store.list_tasks(limit=500, watch_id=watch_id):
            if task.get("status") not in (TransferStatus.PENDING, TransferStatus.RUNNING):
                continue
            created_at = str(task.get("created_at") or "")
            if started_at and created_at and created_at < started_at:
                continue
            yield task

    def has_active_derived_tasks(self, capture: dict) -> bool:
        return any(True for _ in self._derived_tasks_started_after(capture))

    def cancel_derived_tasks(self, capture: dict) -> None:
        """尽力取消正在跑的抓取所派生的转存任务。"""
        if not capture or capture.get("status") != DeferredDiscussionCaptureStatus.RUNNING:
            return
        for task in self._derived_tasks_started_after(capture):
            task_id = task.get("id")
            if task_id is None:
                continue
            try:
                self._delete_web_task(int(task_id))
            except Exception:  # noqa: BLE001 - 取消失败只记录
                log.exception("取消延迟评论区派生转存失败: task_id=%s", task_id)

    # ── 调度入口 ──

    async def schedule_or_forward(
            self,
            *,
            client,
            source_chat_id,
            source_message_id: int,
            target_chat_id,
            target_link: str,
            watch_id: Optional[str] = None,
            done_notice: Optional[bool] = True,
    ) -> Optional[dict]:
        scheduler = self.ensure_scheduler()
        scheduled = await scheduler.schedule(
            watch_id=watch_id or "",
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            target_chat_id=target_chat_id,
            target_link=target_link,
            client=client,
        )
        if scheduled is None:
            return None
        if watch_id:
            due_at = float(scheduled.get("due_at") or 0)
            delay_minutes = max(0, int(round((due_at - time.time()) / 60)))
            self._record_watch_event(
                watch_id,
                source_chat_id,
                source_message_id,
                target_chat_id,
                target_link,
                "success",
                f"已调度延迟抓取评论区,约{delay_minutes}分钟后执行",
            )
        return scheduled
