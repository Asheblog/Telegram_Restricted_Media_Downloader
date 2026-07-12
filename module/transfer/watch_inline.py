# coding=UTF-8
"""监听下载回退（Restricted Content Transfer）的内联 Transfer Task 辅助。"""
from __future__ import annotations

from typing import Optional

from module.transfer_store import ExecutionMode, TransferStatus


def ensure_download_fallback_transfer_task(
        *,
        store,
        source_link: str,
        target_link: str,
        target_profile: str = 'pikpak',
) -> Optional[int]:
    """为监听/转发下载回退创建可见的 watch_inline Transfer Task，不入 web 队列。"""
    if store is None or not source_link or not target_link:
        return None
    task_id = store.create_task(
        source_link=source_link,
        target_link=target_link,
        target_profile=target_profile or 'pikpak',
        execution_mode=ExecutionMode.WATCH_INLINE,
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
