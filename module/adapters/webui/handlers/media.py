# coding=UTF-8
"""/api/media* routes."""

from http import HTTPStatus
from urllib.parse import parse_qs

from module.adapters.webui.server import WebUiApiError


def handle_get(handler, server, parsed) -> bool:
    if parsed.path == '/api/media/scan':
        query = parse_qs(parsed.query)
        task_id = handler._query_int(query, 'task_id', 0) or None
        items_limit = handler._query_int(query, 'items_limit', 0) or None
        items_offset = handler._query_int(query, 'items_offset', 0)
        orphans_limit = handler._query_int(query, 'orphans_limit', 0) or None
        orphans_offset = handler._query_int(query, 'orphans_offset', 0)
        handler._send_json(server.scan_media_for_cleanup(
            task_id=task_id,
            items_limit=items_limit,
            items_offset=items_offset,
            orphans_limit=orphans_limit,
            orphans_offset=orphans_offset,
        ))
        return True

    if parsed.path == '/api/media/cleanup-logs':
        handler._send_json({'logs': server.list_cleanup_logs()})
        return True

    return False


def handle_post(handler, server, parsed) -> bool:
    if parsed.path != '/api/media/cleanup':
        return False
    try:
        payload = handler._read_json()
        handler._send_json(server.cleanup_media_files(payload))
    except WebUiApiError as e:
        handler._send_error(e.error_code, e.message, e.status)
    except Exception as e:
        server.diagnostic.exception('[WebUI] 媒体清理失败。')
        handler._send_json(
            {
                'error_code': 'media_cleanup_failed',
                'error': str(e)
            },
            HTTPStatus.BAD_REQUEST
        )
    return True
