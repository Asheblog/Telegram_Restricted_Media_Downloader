# coding=UTF-8
"""全链路系统日志记录器，持久化到 TransferStore.system_logs。"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Optional

ARCHIVE_NOT_FOUND_STAGE = 'archive_not_found'
_NOT_FOUND_FILE_NAME_RE = re.compile(
    r'No PikPak file matched\s+(.+?)\.?\s*$',
    re.IGNORECASE,
)
_TITLE_STYLE_FILE_NAME_RE = re.compile(r'^\d+\s+-\s+')


def parse_system_log_details(entry: dict[str, Any] | None) -> dict[str, Any]:
    if not entry:
        return {}
    details = entry.get('details')
    if details is None or details == '':
        return {}
    if isinstance(details, dict):
        return dict(details)
    if isinstance(details, str):
        try:
            parsed = json.loads(details)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def extract_archive_file_name_from_message(message: str | None) -> Optional[str]:
    text = str(message or '').strip()
    if not text:
        return None
    match = _NOT_FOUND_FILE_NAME_RE.search(text)
    if not match:
        return None
    name = (match.group(1) or '').strip().rstrip('.')
    return name or None


def infer_archive_match_original_name(
        file_name: Optional[str],
        explicit: Any = None,
) -> Optional[bool]:
    if explicit is not None:
        return bool(explicit)
    if not file_name:
        return None
    if _TITLE_STYLE_FILE_NAME_RE.match(str(file_name)):
        return False
    return True


def resolve_archive_retry_meta(entry: dict[str, Any] | None) -> Optional[dict[str, Any]]:
    """Return archive retry payload for an archive_not_found log, else None."""
    if not entry:
        return None
    if entry.get('category') != 'archive' or entry.get('stage') != ARCHIVE_NOT_FOUND_STAGE:
        return None
    details = parse_system_log_details(entry)
    task_id = details.get('task_id')
    item_id = details.get('item_id')
    source_folder = details.get('source_folder')
    file_name = details.get('file_name') or extract_archive_file_name_from_message(entry.get('message'))
    match_original_name = infer_archive_match_original_name(
        file_name,
        details.get('match_original_name'),
    )
    source_link = entry.get('target_link') or details.get('source_link')
    meta: dict[str, Any] = {
        'source_folder': source_folder,
        'file_name': file_name,
        'source_link': source_link,
        'source_chat_id': entry.get('source_chat_id'),
        'source_message_id': entry.get('source_message_id'),
        'match_original_name': match_original_name,
        'file_size': details.get('file_size'),
    }
    if task_id not in (None, '') and item_id not in (None, ''):
        meta['task_id'] = int(task_id)
        meta['item_id'] = int(item_id)
        return meta
    if source_folder and file_name:
        return meta
    return None


def system_log_can_retry_archive(entry: dict[str, Any] | None) -> bool:
    return resolve_archive_retry_meta(entry) is not None


def archive_retry_inflight_key(meta: dict[str, Any] | None) -> Optional[str]:
    if not meta:
        return None
    task_id = meta.get('task_id')
    item_id = meta.get('item_id')
    if task_id not in (None, '') and item_id not in (None, ''):
        return f'item:{int(task_id)}:{int(item_id)}'
    chat_id = meta.get('source_chat_id')
    message_id = meta.get('source_message_id')
    if chat_id not in (None, '') and message_id not in (None, ''):
        return f'msg:{chat_id}:{int(message_id)}'
    folder = meta.get('source_folder')
    file_name = meta.get('file_name')
    if folder and file_name:
        return f'file:{folder}:{file_name}'
    return None


def annotate_system_logs_can_retry(logs: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    annotated = []
    for entry in logs or []:
        row = dict(entry)
        row['can_retry'] = system_log_can_retry_archive(row)
        annotated.append(row)
    return annotated


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
