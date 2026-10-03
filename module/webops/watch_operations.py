# coding=UTF-8
"""WebUI 监听（Live Transfer Watch）编排。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出的第四组：
监听记录增删改查、事件分页、以及删除监听时联动取消"延迟评论区抓取"。
依赖以 getter 显式注入，可脱离宿主单独测试。
"""
from __future__ import annotations

import asyncio
from typing import Callable, Optional

from module import log


class WatchOperations:
    """监听规则的对外操作面（含延迟评论区抓取的调度入口）。

    两条调度器 getter 刻意分开：

    - ``comment_delay_scheduler_getter``（窥视）：只取**已启动**的调度器，未启动返回
      ``None``。删除监听用它——删规则不应顺带把调度器线程/循环挂起来
      （见 deferred_discussion.py 的语义说明与 ADR0007）。
    - ``ensure_comment_delay_scheduler_getter``（主动）：必要时创建并启动调度器。
      cancel / run_now / retry 是用户主动动作，旧实现就是按需 ensure；用 peek
      会在调度器尚未启动时拿到 ``None`` 并抛 ``AttributeError``。

    两条 getter 都经宿主工厂解析，保证拿到的是 ``DeferredDiscussionOperations``
    持有的**同一个实例**（并发首次创建由那里的双检锁兜底）。
    """

    def __init__(
        self,
        *,
        watch_manager_getter: Callable[[], object],
        comment_delay_scheduler_getter: Callable[[], object],
        ensure_comment_delay_scheduler_getter: Callable[[], object],
        transfer_store_getter: Callable[[], object],
        loop_getter: Callable[[], object],
    ) -> None:
        self._watch_manager = watch_manager_getter
        self._comment_delay_scheduler = comment_delay_scheduler_getter
        self._ensure_comment_delay_scheduler = ensure_comment_delay_scheduler_getter
        self._transfer_store = transfer_store_getter
        self._loop = loop_getter

    def list_watches(self, tz_offset_minutes: Optional[int] = None) -> list:
        return self._watch_manager().list_watches(tz_offset_minutes=tz_offset_minutes)

    def mark_pending_watch(
        self, payload: dict, status: str, error_message: Optional[str] = None
    ) -> None:
        return self._watch_manager().mark_pending_watch(payload, status, error_message)

    def set_live_watch_status(
        self, watch_id: str, status: str, error_message: Optional[str] = None
    ) -> None:
        return self._watch_manager().set_live_watch_status(watch_id, status, error_message)

    def persisted_watches(self) -> list:
        return self._watch_manager().persisted_watches()

    def watch_payload_from_record(self, watch: dict) -> dict:
        return self._watch_manager().watch_payload_from_record(watch)

    def create_watch(self, payload: dict) -> dict:
        return self._watch_manager().create_watch(payload)

    def export_forward_watches(self) -> dict:
        return self._watch_manager().export_forward_watches()

    def delete_watch(self, watch_id: str) -> bool:
        """删除监听；先取消它的延迟评论区抓取，避免留孤儿定时任务。"""
        scheduler = self._comment_delay_scheduler()
        if scheduler is not None:
            try:
                scheduler.cancel_for_watch(watch_id)
            except Exception:  # noqa: BLE001 - 取消失败不应阻断删除
                log.exception("删除监听时取消延迟评论区失败: %s", watch_id)
        return self._watch_manager().delete_watch(watch_id)

    def update_watch(self, watch_id: str, payload: dict) -> dict:
        return self._watch_manager().update_watch(watch_id, payload)

    def list_watch_events(
            self,
            watch_id: str,
            limit: int = 50,
            offset: int = 0,
            today_only: bool = False,
            tz_offset_minutes: Optional[int] = None,
            status: Optional[str] = None,
    ):
        return self._watch_manager().list_watch_events(
            watch_id,
            limit=limit,
            offset=offset,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes,
            status=status,
        )

    # ── 延迟评论区抓取（Deferred Discussion Reply Capture）──
    # 这几个读写的是 store 的 deferred 表 + 调度器，不经 watch_manager。

    def list_deferred_discussion_captures(self, watch_id: str) -> dict:
        captures = self._transfer_store().list_deferred_discussion_captures(
            watch_id=watch_id, limit=500
        )
        return {"captures": captures, "total": len(captures)}

    def cancel_deferred_discussion_capture(self, watch_id: str, capture_id: int) -> bool:
        capture = self._owned_capture(watch_id, capture_id)
        if capture is None:
            return False
        return self._ensure_comment_delay_scheduler().cancel(int(capture_id))

    def run_deferred_discussion_capture_now(self, watch_id: str, capture_id: int) -> bool:
        if self._owned_capture(watch_id, capture_id) is None:
            return False
        loop = self._loop()
        if loop is None:
            return False
        future = asyncio.run_coroutine_threadsafe(
            self._ensure_comment_delay_scheduler().run_now(int(capture_id)), loop
        )
        return bool(future.result(timeout=180))

    def retry_deferred_discussion_capture(self, watch_id: str, capture_id: int) -> bool:
        if self._owned_capture(watch_id, capture_id) is None:
            return False
        loop = self._loop()
        if loop is None:
            return False
        future = asyncio.run_coroutine_threadsafe(
            self._ensure_comment_delay_scheduler().retry(int(capture_id)), loop
        )
        return bool(future.result(timeout=180))

    def _owned_capture(self, watch_id: str, capture_id: int):
        """取 capture 并校验归属；不存在或不属于该监听时返回 None。"""
        capture = self._transfer_store().get_deferred_discussion_capture(int(capture_id))
        if not capture or capture.get("watch_id") != watch_id:
            return None
        return capture
