# coding=UTF-8
"""全链路系统日志记录器，持久化到 TransferStore.system_logs。"""
from __future__ import annotations

import time
from typing import Any, Optional


class SystemLogTracer:
    """将监听/转发/下载/归档等链路事件写入 SQLite system_logs 表。"""

    def __init__(self, store=None, diagnostic=None):
        self._store = store
        self._diagnostic = diagnostic

    def bind(self, store=None, diagnostic=None) -> None:
        if store is not None:
            self._store = store
        if diagnostic is not None:
            self._diagnostic = diagnostic

    @staticmethod
    def make_trace_id(
            watch_id: Optional[str],
            source_chat_id: Optional[str | int],
            source_message_id: Optional[int]
    ) -> str:
        watch_part = watch_id or 'manual'
        chat_part = str(source_chat_id or 'unknown')
        msg_part = str(source_message_id or 0)
        return f'{watch_part}:{chat_part}:{msg_part}:{int(time.time() * 1000)}'

    def log(
            self,
            *,
            category: str,
            stage: str,
            message: str,
            level: str = 'info',
            trace_id: Optional[str] = None,
            watch_id: Optional[str] = None,
            source_chat_id: Optional[str | int] = None,
            source_message_id: Optional[int] = None,
            target_link: Optional[str] = None,
            details: Optional[dict[str, Any] | str] = None
    ) -> None:
        store = self._store
        if store is None or not hasattr(store, 'add_system_log'):
            return
        try:
            store.add_system_log(
                category=category,
                stage=stage,
                message=message,
                level=level,
                trace_id=trace_id,
                watch_id=watch_id,
                source_chat_id=str(source_chat_id) if source_chat_id is not None else None,
                source_message_id=int(source_message_id) if source_message_id is not None else None,
                target_link=target_link,
                details=details
            )
        except Exception as exc:
            diagnostic = self._diagnostic
            if diagnostic is not None and hasattr(diagnostic, 'debug'):
                diagnostic.debug(f'system log write failed: {exc}')
        diagnostic = self._diagnostic
        if diagnostic is None:
            return
        log_line = f'[{category}/{stage}] {message}'
        if details:
            log_line = f'{log_line} | {details}'
        if level == 'error' and hasattr(diagnostic, 'error'):
            diagnostic.error(log_line)
        elif level == 'warning' and hasattr(diagnostic, 'warning'):
            diagnostic.warning(log_line)
        elif hasattr(diagnostic, 'info'):
            diagnostic.info(log_line)
