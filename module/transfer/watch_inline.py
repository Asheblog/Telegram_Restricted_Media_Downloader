# coding=UTF-8
"""监听下载回退（Restricted Content Transfer）的内联 Transfer Task 辅助。"""
from __future__ import annotations

from typing import Optional

from module.transfer_store import ExecutionMode, TransferStatus


def source_link_belongs_to_watch(source_link: str, watch_source_link: str) -> bool:
    """判断消息级 source_link 是否属于监听的频道来源。"""
    if not source_link or not watch_source_link:
        return False
    src = str(source_link).rstrip('/')
    watch = str(watch_source_link).rstrip('/')
    if not src or not watch:
        return False
    if src == watch:
        return True
    # 避免 https://t.me/ctuxas 误匹配 https://t.me/ctuxas2/...
    return src.startswith(watch + '/')


def ensure_download_fallback_transfer_task(
        *,
        store,
        source_link: str,
        target_link: str,
        target_profile: str = 'pikpak',
        watch_id: Optional[str] = None,
        archive_by_author: bool = False,
) -> Optional[int]:
    """为监听/转发下载回退创建可见的 watch_inline Transfer Task，不入 web 队列。"""
    if store is None or not source_link or not target_link:
        return None
    if watch_id and not archive_by_author:
        watch = store.get_live_transfer_watch(watch_id) if hasattr(store, 'get_live_transfer_watch') else None
        if isinstance(watch, dict):
            archive_by_author = bool(watch.get('archive_by_author'))
    task_id = store.create_task(
        source_link=source_link,
        target_link=target_link,
        target_profile=target_profile or 'pikpak',
        execution_mode=ExecutionMode.WATCH_INLINE,
        watch_id=watch_id,
        archive_by_author=archive_by_author,
    )
    store.update_task(
        task_id,
        status=TransferStatus.RUNNING,
        total_items=1,
        started=True,
        assignment_completed=True,
    )
    store.add_event(
        task_id,
        f'Watch inline download-fallback task created: {source_link}',
        level='info',
    )
    return task_id


def is_watch_inline_task(task: Optional[dict]) -> bool:
    if not task:
        return False
    return (task.get('execution_mode') or ExecutionMode.WEB_QUEUE) == ExecutionMode.WATCH_INLINE
