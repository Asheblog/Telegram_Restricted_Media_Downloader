# coding=UTF-8
"""/api/watches* routes."""

from http import HTTPStatus
from urllib.parse import parse_qs, unquote

from module.adapters.webui.server import WebUiApiError
import time


def handle_get(handler, server, parsed) -> bool:
    if parsed.path == '/api/watches/forward/export':
        payload = server.export_forward_watches()
        stamp = time.strftime('%Y%m%d-%H%M%S')
        handler._send_json_download(payload, f'forward-watches-{stamp}.json')
        return True

    if parsed.path == '/api/watches':
        query = parse_qs(parsed.query)
        tz_offset = handler._query_optional_int(query, 'tz_offset')
        handler._send_json({'watches': server.list_watches(tz_offset_minutes=tz_offset)})
        return True

    if parsed.path.startswith('/api/watches/') and parsed.path.endswith('/events'):
        watch_path = parsed.path[len('/api/watches/'):][:-len('/events')]
        watch_id = unquote(watch_path)
        if not watch_id:
            handler._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
            return True
        query = parse_qs(parsed.query)
        limit = handler._query_int(query, 'limit', 50)
        offset = handler._query_int(query, 'offset', 0)
        today_only = str((query.get('today') or [''])[0]).lower() in ('1', 'true', 'yes')
        tz_offset = handler._query_optional_int(query, 'tz_offset')
        status = str((query.get('status') or [''])[0]).strip() or None
        if status and status not in ('success', 'skipped', 'failure'):
            handler._send_error('invalid_status', 'Invalid status filter.', HTTPStatus.BAD_REQUEST)
            return True
        try:
            result = server.list_watch_events(
                watch_id,
                limit=limit,
                offset=offset,
                today_only=today_only,
                tz_offset_minutes=tz_offset,
                status=status
            )
        except ValueError as exc:
            if str(exc) == 'invalid_status':
                handler._send_error('invalid_status', 'Invalid status filter.', HTTPStatus.BAD_REQUEST)
                return True
            raise
        if not result:
            handler._send_error('watch_not_found', 'Watch not found.', HTTPStatus.NOT_FOUND)
            return True
        handler._send_json(result)
        return True

    if parsed.path.startswith('/api/watches/') and parsed.path.endswith('/download-tasks'):
        watch_path = parsed.path[len('/api/watches/'):][:-len('/download-tasks')]
        watch_id = unquote(watch_path)
        if not watch_id:
            handler._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
            return True
        query = parse_qs(parsed.query)
        limit = handler._query_int(query, 'limit', 200)
        payload = server.view_model.watch_download_tasks(watch_id, limit=limit)
        if payload is None:
            handler._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
            return True
        handler._send_json(payload)
        return True

    if parsed.path.startswith('/api/watches/') and parsed.path.endswith('/deferred-comments'):
        watch_path = parsed.path[len('/api/watches/'):][:-len('/deferred-comments')]
        watch_id = unquote(watch_path)
        if not watch_id:
            handler._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
            return True
        result = server.list_deferred_discussion_captures(watch_id)
        if result is None:
            handler._send_error('watch_not_found', 'Watch not found.', HTTPStatus.NOT_FOUND)
            return True
        handler._send_json(result)
        return True

    return False


def handle_post(handler, server, parsed) -> bool:
    if parsed.path == '/api/watches/forward/import':
        try:
            payload = handler._read_json()
            result = server.import_forward_watches(payload)
            handler._send_json(result)
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 导入监听转发失败。')
            handler._send_json(
                {
                    'error_code': 'import_forward_watches_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    if parsed.path == '/api/watches':
        try:
            payload = handler._read_json()
            result = server.create_watch(payload)
            handler._send_json(result, HTTPStatus.CREATED)
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 创建实时监听失败。')
            handler._send_json(
                {
                    'error_code': 'create_watch_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    if parsed.path.startswith('/api/watches/') and (
            parsed.path.endswith('/cancel')
            or parsed.path.endswith('/run-now')
            or parsed.path.endswith('/retry')
    ):
        # /api/watches/{watch_id}/deferred-comments/{id}/cancel|run-now|retry
        body_path = parsed.path[len('/api/watches/'):]
        if body_path.endswith('/cancel'):
            action = 'cancel'
            suffix = '/cancel'
        elif body_path.endswith('/run-now'):
            action = 'run-now'
            suffix = '/run-now'
        else:
            action = 'retry'
            suffix = '/retry'
        remainder = body_path[:-len(suffix)]
        marker = '/deferred-comments/'
        if marker not in remainder:
            handler._send_error('not_found', 'Not found.', HTTPStatus.NOT_FOUND)
            return True
        watch_part, capture_part = remainder.split(marker, 1)
        watch_id = unquote(watch_part)
        if not watch_id or not capture_part.isdigit():
            handler._send_error('invalid_watch_id', 'Invalid deferred comment id.', HTTPStatus.BAD_REQUEST)
            return True
        capture_id = int(capture_part)
        try:
            if action == 'cancel':
                ok = server.cancel_deferred_discussion_capture(watch_id, capture_id)
            elif action == 'run-now':
                ok = server.run_deferred_discussion_capture_now(watch_id, capture_id)
            else:
                ok = server.retry_deferred_discussion_capture(watch_id, capture_id)
            if not ok:
                handler._send_error('deferred_comment_not_found', 'Deferred comment job not found.', HTTPStatus.NOT_FOUND)
                return True
            handler._send_json({'ok': True, 'action': action, 'id': capture_id})
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 操作延迟评论区任务失败。')
            handler._send_json(
                {'error_code': 'deferred_comment_action_failed', 'error': str(e)},
                HTTPStatus.BAD_REQUEST
            )
        return True

    return False


def handle_put(handler, server, parsed) -> bool:
    if not parsed.path.startswith('/api/watches/'):
        return False
    watch_id = unquote(parsed.path[len('/api/watches/'):])
    if not watch_id:
        handler._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
        return True
    try:
        payload = handler._read_json()
        result = server.update_watch(watch_id, payload)
        handler._send_json(result)
    except WebUiApiError as e:
        handler._send_error(e.error_code, e.message, e.status)
    except ValueError as e:
        handler._send_json(
            {'error_code': 'update_watch_failed', 'error': str(e)},
            HTTPStatus.BAD_REQUEST
        )
    except Exception as e:
        server.diagnostic.exception('[WebUI] 更新实时监听失败。')
        handler._send_json(
            {'error_code': 'update_watch_failed', 'error': str(e)},
            HTTPStatus.BAD_REQUEST
        )
    return True


def handle_delete(handler, server, parsed) -> bool:
    if not parsed.path.startswith('/api/watches/'):
        return False
    watch_id = unquote(parsed.path[len('/api/watches/'):])
    if not watch_id:
        handler._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
        return True
    deleted = server.delete_watch(watch_id)
    if not deleted:
        handler._send_error('watch_not_found', 'Watch not found.', HTTPStatus.NOT_FOUND)
        return True
    handler._send_json({'deleted': True, 'watch_id': watch_id})
    return True
