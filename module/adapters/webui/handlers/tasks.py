# coding=UTF-8
"""/api/tasks* routes."""

from http import HTTPStatus
from urllib.parse import parse_qs

from module.adapters.webui.server import WebUiApiError
from module.adapters.webui.view_model import WebUiViewModel


def handle_get(handler, server, parsed) -> bool:
    if parsed.path == '/api/tasks':
        settings = server.get_settings()
        user = (settings or {}).get('user') or {}
        payload = server.view_model.task_list()
        payload['metrics'] = {
            **server.view_model.transfer_speed_metrics(),
            **WebUiViewModel.disk_metrics([
                user.get('temp_directory'),
                user.get('save_directory'),
            ]),
        }
        handler._send_json(payload)
        return True

    if not parsed.path.startswith('/api/tasks/'):
        return False

    # 提取路径段: /api/tasks/123 或 /api/tasks/123/summary
    subpath = parsed.path[len('/api/tasks/'):]
    parts = [p for p in subpath.split('/') if p]
    if not parts or not parts[0].isdigit():
        handler._send_error('invalid_task_id', 'Invalid task id.', HTTPStatus.BAD_REQUEST)
        return True
    task_id = int(parts[0])
    query = parse_qs(parsed.query)
    if len(parts) > 1 and parts[1] == 'summary':
        payload = server.view_model.task_summary(task_id)
    else:
        payload = server.view_model.task_detail(
            task_id,
            item_limit=handler._query_int(query, 'items_limit', 200),
            item_offset=handler._query_int(query, 'items_offset', 0),
            item_status=(query.get('item_status') or [''])[0] or None,
            event_limit=handler._query_int(query, 'events_limit', 100),
            event_offset=handler._query_int(query, 'events_offset', 0),
        )
    if not payload:
        handler._send_error('task_not_found', 'Task not found.', HTTPStatus.NOT_FOUND)
        return True
    handler._send_json(payload)
    return True


def handle_post(handler, server, parsed) -> bool:
    task_action = server.parse_task_action_path(parsed.path)
    if task_action:
        task_id, action = task_action
        try:
            handler._send_json(server.apply_task_action(task_id, action), HTTPStatus.ACCEPTED)
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 执行任务操作失败。')
            handler._send_json(
                {
                    'error_code': 'task_action_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    if parsed.path != '/api/tasks':
        return False

    try:
        payload = handler._read_json()
        handler._send_json(server.create_task(payload), HTTPStatus.CREATED)
    except WebUiApiError as e:
        handler._send_error(e.error_code, e.message, e.status)
    except Exception as e:
        server.diagnostic.exception('[WebUI] 创建任务失败。')
        handler._send_json(
            {
                'error_code': 'create_task_failed',
                'error': str(e)
            },
            HTTPStatus.BAD_REQUEST
        )
    return True


def handle_delete(handler, server, parsed) -> bool:
    if not parsed.path.startswith('/api/tasks/'):
        return False
    task_id = handler._task_id_from_path()
    if task_id is None:
        return True
    try:
        deleted = server.delete_task(task_id)
    except Exception as e:
        server.diagnostic.exception('[WebUI] 删除任务失败。')
        handler._send_json(
            {
                'error_code': 'delete_task_failed',
                'error': str(e),
                'detail': '删除失败',
            },
            HTTPStatus.BAD_REQUEST,
        )
        return True
    if not deleted:
        handler._send_error(
            'delete_task_failed',
            'Task delete failed. Stop running transfers or retry after files are released.',
            HTTPStatus.BAD_REQUEST,
        )
        return True
    handler._send_json({'deleted': True, 'task_id': task_id})
    return True
