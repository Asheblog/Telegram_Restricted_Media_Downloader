# coding=UTF-8
"""Build structured statistics payloads for WebUI dashboards."""

from __future__ import annotations

from enum import Enum
from typing import Any

from module.enums import DownloadType, UploadStatus

_MEDIA_TYPES: tuple[tuple[str, str, str, str], ...] = (
    (DownloadType.VIDEO, 'success_video', 'failure_video', 'skip_video'),
    (DownloadType.PHOTO, 'success_photo', 'failure_photo', 'skip_photo'),
    (DownloadType.DOCUMENT, 'success_document', 'failure_document', 'skip_document'),
    (DownloadType.AUDIO, 'success_audio', 'failure_audio', 'skip_audio'),
    (DownloadType.VOICE, 'success_voice', 'failure_voice', 'skip_voice'),
    (DownloadType.ANIMATION, 'success_animation', 'failure_animation', 'skip_animation'),
    (DownloadType.VIDEO_NOTE, 'success_video_note', 'failure_video_note', 'skip_video_note'),
)


def _format_file_size(number: int) -> str:
    value = float(number or 0)
    units = ('B', 'KiB', 'MiB', 'GiB', 'TiB')
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == 'B':
                return f'{int(value)} {unit}'
            return f'{value:.2f} {unit}'
        value /= 1024
    return f'{number} B'


def _link_status(complete_num: int, member_num: int, error_msg: dict | None) -> str:
    if error_msg:
        return 'error'
    if member_num > 0 and complete_num >= member_num:
        return 'complete'
    return 'progress'


def _link_error_text(error_msg: dict | None) -> str:
    if not error_msg:
        return ''
    if 'all_member' in error_msg:
        return str(error_msg.get('all_member') or '')
    return '; '.join(f'{name}: {err}' for name, err in error_msg.items())


def _upload_status_value(status: Any) -> str:
    if isinstance(status, Enum):
        return str(status.value)
    return str(status)


def build_count_rows(app: Any) -> list[dict]:
    rows: list[dict] = []
    for media_type, success_key, failure_key, skip_key in _MEDIA_TYPES:
        success = len(getattr(app, success_key))
        failure = len(getattr(app, failure_key))
        skip = len(getattr(app, skip_key))
        rows.append({
            'type': media_type,
            'success': success,
            'failure': failure,
            'skip': skip,
            'total': success + failure + skip,
        })
    return rows


def count_has_data(app: Any) -> bool:
    return any(row['total'] > 0 for row in build_count_rows(app))


def empty_statistics_app() -> Any:
    """Return an app-like object with empty download counters."""

    class _EmptyApp:
        pass

    app = _EmptyApp()
    for _, success_key, failure_key, skip_key in _MEDIA_TYPES:
        setattr(app, success_key, set())
        setattr(app, failure_key, set())
        setattr(app, skip_key, set())
    return app


def build_statistics_payload(
        link_info: dict,
        app: Any,
        upload_tasks: set,
) -> dict:
    links: list[dict] = []
    complete_links = 0
    progress_links = 0
    error_links = 0
    rate_sum = 0.0
    rate_count = 0

    for link, info in link_info.items():
        complete_num = int(info.get('complete_num') or 0)
        member_num = int(info.get('member_num') or 0)
        error_msg = info.get('error_msg') or {}
        if member_num > 0:
            rate = round(complete_num / member_num * 100, 2)
            rate_sum += rate
            rate_count += 1
        else:
            rate = 0.0
        status = _link_status(complete_num, member_num, error_msg)
        if status == 'complete':
            complete_links += 1
        elif status == 'error':
            error_links += 1
        else:
            progress_links += 1
        file_names = info.get('file_name') or set()
        links.append({
            'link': link,
            'complete_num': complete_num,
            'member_num': member_num,
            'rate': rate,
            'file_count': len(file_names),
            'status': status,
            'error': _link_error_text(error_msg),
        })

    count_rows = build_count_rows(app)
    count_totals = {
        'success': sum(row['success'] for row in count_rows),
        'failure': sum(row['failure'] for row in count_rows),
        'skip': sum(row['skip'] for row in count_rows),
    }
    downloads_total = sum(count_totals.values())
    success_rate = round(count_totals['success'] / downloads_total * 100, 1) if downloads_total else 0.0

    upload_rows: list[dict] = []
    upload_by_status: dict[str, int] = {
        UploadStatus.PENDING: 0,
        UploadStatus.UPLOADING: 0,
        UploadStatus.SUCCESS: 0,
        UploadStatus.FAILURE: 0,
        UploadStatus.SENT: 0,
    }
    upload_completed = 0
    for task in upload_tasks:
        status = _upload_status_value(task.status)
        upload_by_status[status] = upload_by_status.get(status, 0) + 1
        if status in (UploadStatus.SUCCESS, UploadStatus.SENT):
            upload_completed += 1
        upload_rows.append({
            'chat_id': str(task.chat_id) if task.chat_id else '',
            'file': getattr(task, 'file_name', '') or getattr(task, 'file_path', ''),
            'size': _format_file_size(getattr(task, 'file_size', 0) or 0),
            'status': status,
            'error': getattr(task, 'error_msg', '') or '',
            'with_delete': bool(getattr(task, 'with_delete', False)),
        })

    count_available = count_has_data(app)
    link_available = bool(link_info)
    upload_available = bool(upload_tasks)

    return {
        'tables': {
            'link': {
                'available': link_available,
                'rows': len(link_info),
            },
            'count': {
                'available': count_available,
                'rows': len(count_rows) + (1 if count_available else 0),
            },
            'upload': {
                'available': upload_available,
                'rows': len(upload_tasks),
            },
        },
        'summary': {
            'links': len(link_info),
            'downloads_total': downloads_total,
            'success_rate': success_rate,
            'failure_count': count_totals['failure'],
            'skip_count': count_totals['skip'],
            'upload_tasks': len(upload_tasks),
            'upload_completed': upload_completed,
        },
        'links': links,
        'count_by_type': count_rows,
        'count_totals': count_totals,
        'link_completion': {
            'complete': complete_links,
            'progress': progress_links,
            'error': error_links,
            'avg_rate': round(rate_sum / rate_count, 1) if rate_count else 0.0,
        },
        'upload_by_status': [
            {'status': status, 'count': upload_by_status.get(status, 0)}
            for status in (
                UploadStatus.PENDING,
                UploadStatus.UPLOADING,
                UploadStatus.SUCCESS,
                UploadStatus.FAILURE,
                UploadStatus.SENT,
            )
        ],
        'upload_rows': upload_rows,
    }
