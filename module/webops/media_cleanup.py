# coding=UTF-8
"""WebUI 媒体清理编排。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出的第三组。
``MediaManager`` 的实例仍由宿主懒建（它依赖 app/transfer_store 的运行时目录），
本类只负责"扫描/清理/定时清理/日志"这层编排，因此可脱离宿主单独测试。
"""
from __future__ import annotations

import time
from typing import Callable, Optional

from module import log

ORPHAN_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60


class MediaCleanupOperations:
    """媒体文件扫描、清理与定时孤儿清理。"""

    def __init__(
        self,
        *,
        media_manager_getter: Callable[[], object],
        transfer_store_getter: Callable[[], object],
        diagnostic_getter: Callable[[], object],
    ) -> None:
        self._media_manager = media_manager_getter
        self._transfer_store = transfer_store_getter
        self._diagnostic = diagnostic_getter
        self._last_orphan_cleanup_at = 0.0

    def scan_media_for_cleanup(
            self,
            task_id: Optional[int] = None,
            items_limit: Optional[int] = None,
            items_offset: int = 0,
            orphans_limit: Optional[int] = None,
            orphans_offset: int = 0,
    ) -> dict:
        """扫描可清理的媒体文件。"""
        return self._media_manager().scan_all(
            task_id=task_id,
            items_limit=items_limit,
            items_offset=items_offset,
            orphans_limit=orphans_limit,
            orphans_offset=orphans_offset,
        )

    def cleanup_media_files(self, payload: dict) -> dict:
        """执行媒体文件清理。payload: {'item_ids': [...], 'file_paths': [...]}"""
        mm = self._media_manager()
        item_ids = payload.get("item_ids") or []
        file_paths = payload.get("file_paths") or []

        result = {
            "item_result": None,
            "orphan_result": None,
            "total_deleted_count": 0,
            "total_deleted_size": 0,
        }

        if item_ids:
            item_result = mm.cleanup_by_item_ids([int(i) for i in item_ids])
            result["item_result"] = item_result
            result["total_deleted_count"] += item_result["total_deleted_count"]
            result["total_deleted_size"] += item_result["total_deleted_size"]

        if file_paths:
            orphan_result = mm.cleanup_orphan_files(file_paths)
            result["orphan_result"] = orphan_result
            result["total_deleted_count"] += orphan_result["total_deleted_count"]
            result["total_deleted_size"] += orphan_result["total_deleted_size"]

        return result

    def maybe_run_scheduled_media_cleanup(self) -> None:
        if not self._transfer_store():
            return
        now = time.time()
        if now - self._last_orphan_cleanup_at < ORPHAN_CLEANUP_INTERVAL_SECONDS:
            return
        self._last_orphan_cleanup_at = now
        try:
            result = self._media_manager().auto_cleanup_orphan_files()
            deleted_count = int(result.get("total_deleted_count") or 0)
            if deleted_count:
                diagnostic = self._diagnostic()
                message = f"Auto orphan cleanup removed {deleted_count} file(s)."
                if diagnostic is not None:
                    diagnostic.info(message)
                else:
                    log.info(message)
        except Exception as error:  # noqa: BLE001 - 定时清理失败不能影响主循环
            log.warning(f"Scheduled orphan cleanup failed: {error}")

    def list_cleanup_logs(self) -> list:
        store = self._transfer_store()
        if not store:
            return []
        return store.list_cleanup_logs()
