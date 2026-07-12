# coding=UTF-8
"""全链路系统日志记录器，持久化到 TransferStore.system_logs。"""
from __future__ import annotations

import json
import time
from typing import Any, Optional


def format_system_log_export_line(entry: dict[str, Any]) -> str:
    """Format one system log row to match WebUI「复制本页」line style."""
    time_text = entry.get('created_at') or '-'
    level = str(entry.get('level') or 'info').upper()
    category = entry.get('category') or '-'
    stage = entry.get('stage') or '-'
    message = entry.get('message') or ''
    parts: list[str] = []
    if entry.get('trace_id'):
        parts.append(f"Trace: {entry['trace_id']}")
    if entry.get('watch_id'):
        parts.append(f"Watch: {entry['watch_id']}")
    if entry.get('source_chat_id'):
        parts.append(f"chat: {entry['source_chat_id']}")
    if entry.get('source_message_id') is not None:
        parts.append(f"msg: {entry['source_message_id']}")
    if entry.get('target_link'):
        parts.append(f"target: {entry['target_link']}")
    details = entry.get('details')
    if details:
        try:
            parsed = json.loads(details) if isinstance(details, str) else details
            parts.append(json.dumps(parsed, ensure_ascii=False))
        except Exception:
            parts.append(str(details))
    context = ' | '.join(parts)
    line = f'[{time_text}] [{level}] [{category}/{stage}] {message}'
    if context:
        line = f'{line} | {context}'
    return line


def build_system_logs_export_text(
        store,
        *,
        category: str | None = None,
        level: str | None = None,
        trace_id: str | None = None,
        watch_id: str | None = None,
        today_only: bool = False,
        tz_offset_minutes: int | None = None
) -> str:
    """Export all matching system logs (not just one page) as plain text."""
    if store is None or not hasattr(store, 'list_system_logs'):
        return ''
    _, total = store.list_system_logs(
        limit=1,
        offset=0,
        category=category,
        level=level,
        trace_id=trace_id,
        watch_id=watch_id,
        today_only=today_only,
        tz_offset_minutes=tz_offset_minutes
    )
    if not total:
        return ''
    logs, _ = store.list_system_logs(
        limit=int(total),
        offset=0,
        category=category,
        level=level,
        trace_id=trace_id,
        watch_id=watch_id,
        today_only=today_only,
        tz_offset_minutes=tz_offset_minutes
    )
    return '\n'.join(format_system_log_export_line(entry) for entry in logs)


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
