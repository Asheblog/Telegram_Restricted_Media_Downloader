# coding=UTF-8
"""Remaining small API routes: download-records, system-logs, uploads, channel-downloads."""

from http import HTTPStatus
from urllib.parse import parse_qs
import time

from module.adapters.webui.server import WebUiApiError


def handle_get(handler, server, parsed) -> bool:
    if parsed.path == '/api/download-records':
        query = parse_qs(parsed.query)
        limit = handler._query_int(query, 'limit', 50)
        offset = handler._query_int(query, 'offset', 0)
        total = server.store.count_download_success_records()
        records = server.store.list_download_success_records(
            limit=limit,
            offset=offset
        )
        handler._send_json({
            'records': records,
            'total': total,
            'limit': limit,
            'offset': offset
        })
        return True

    if parsed.path == '/api/system-logs':
        query = parse_qs(parsed.query)
        limit = handler._query_int(query, 'limit', 50)
        offset = handler._query_int(query, 'offset', 0)
        category = (query.get('category') or [None])[0]
        level = (query.get('level') or [None])[0]
        trace_id = (query.get('trace_id') or [None])[0]
        watch_id = (query.get('watch_id') or [None])[0]
        today_only = (query.get('today') or ['0'])[0] in ('1', 'true', 'yes')
        tz_offset = handler._query_int(query, 'tz_offset', None)
        handler._send_json(server.list_system_logs(
            limit=limit,
            offset=offset,
            category=category,
            level=level,
            trace_id=trace_id,
            watch_id=watch_id,
            today_only=today_only,
            tz_offset_minutes=tz_offset
        ))
        return True

    if parsed.path == '/api/system-logs/export':
        query = parse_qs(parsed.query)
        category = (query.get('category') or [None])[0]
        level = (query.get('level') or [None])[0]
        trace_id = (query.get('trace_id') or [None])[0]
        watch_id = (query.get('watch_id') or [None])[0]
        today_only = (query.get('today') or ['0'])[0] in ('1', 'true', 'yes')
        tz_offset = handler._query_int(query, 'tz_offset', None)
        content = server.export_system_logs(
            category=category,
            level=level,
            trace_id=trace_id,
            watch_id=watch_id,
            today_only=today_only,
            tz_offset_minutes=tz_offset
        )
        stamp = time.strftime('%Y%m%d-%H%M%S')
        handler._send_text_download(content, f'system-logs-{stamp}.txt')
        return True

    return False


def handle_post(handler, server, parsed) -> bool:
    if parsed.path.startswith('/api/system-logs/') and parsed.path.endswith('/retry-archive'):
        suffix = parsed.path[len('/api/system-logs/'):-len('/retry-archive')]
        try:
            log_id = int(suffix)
        except (TypeError, ValueError):
            handler._send_error('invalid_log_id', 'Invalid system log id.', HTTPStatus.BAD_REQUEST)
            return True
        try:
            result = server.retry_archive_from_system_log(log_id)
            handler._send_json(result)
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 手动重试归档失败。')
            handler._send_json(
                {
                    'error_code': 'archive_retry_failed',
                    'error': str(e),
                },
                HTTPStatus.BAD_REQUEST,
            )
        return True

    if parsed.path == '/api/uploads':
        try:
            payload = handler._read_json()
            result = server.create_upload(payload)
            handler._send_json(result, HTTPStatus.ACCEPTED)
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 创建上传任务失败。')
            handler._send_json(
                {
                    'error_code': 'create_upload_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    if parsed.path == '/api/channel-downloads':
        try:
            payload = handler._read_json()
            result = server.create_channel_download(payload)
            handler._send_json(result, HTTPStatus.ACCEPTED)
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 创建频道下载失败。')
            handler._send_json(
                {
                    'error_code': 'create_channel_download_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    return False


def handle_delete(handler, server, parsed) -> bool:
    if parsed.path != '/api/download-records':
        return False
    cleared_count = server.store.clear_download_success_records()
    handler._send_json({'cleared': True, 'count': cleared_count})
    return True
