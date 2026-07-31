# coding=UTF-8
"""/api/archive/author* routes."""

from http import HTTPStatus
from urllib.parse import parse_qs

from module.adapters.webui.server import WebUiApiError


def handle_get(handler, server, parsed) -> bool:
    if parsed.path == '/api/archive/author-channels':
        try:
            handler._send_json(server.list_archive_author_channels())
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 列出归档频道失败。')
            handler._send_json(
                {
                    'error_code': 'archive_author_channels_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    if parsed.path == '/api/archive/author-job':
        query = parse_qs(parsed.query)
        job_id = (query.get('id') or [None])[0]
        active = (query.get('active') or ['0'])[0]
        channel_folder = (query.get('channel_folder') or [None])[0]
        try:
            if str(active) in ('1', 'true', 'yes'):
                handler._send_json(server.get_active_archive_author_job(channel_folder))
                return True
            if not job_id:
                raise ValueError('id is required')
            handler._send_json(server.get_archive_author_job(str(job_id)))
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 查询归档整理进度失败。')
            handler._send_json(
                {
                    'error_code': 'archive_author_job_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    if parsed.path == '/api/archive/author-plan-moves':
        query = parse_qs(parsed.query)
        try:
            handler._send_json(server.list_archive_author_plan_moves({
                'job_id': (query.get('job_id') or [None])[0],
                'channel_folder': (query.get('channel_folder') or [None])[0],
                'bucket': (query.get('bucket') or [''])[0],
                'offset': handler._query_int(query, 'offset', 0),
                'limit': handler._query_int(query, 'limit', 50),
            }))
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 查询归档迁移明细失败。')
            handler._send_json(
                {
                    'error_code': 'archive_author_plan_moves_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    return False


def handle_post(handler, server, parsed) -> bool:
    if parsed.path == '/api/archive/author-scan':
        try:
            payload = handler._read_json()
            handler._send_json(server.scan_archive_author_reorganize(payload))
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 作者归档扫描失败。')
            handler._send_json(
                {
                    'error_code': 'archive_author_scan_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    if parsed.path == '/api/archive/author-resolve':
        try:
            payload = handler._read_json()
            handler._send_json(server.resolve_archive_author_reorganize(payload))
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 作者归档重新解析失败。')
            handler._send_json(
                {
                    'error_code': 'archive_author_resolve_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    if parsed.path == '/api/archive/author-reorganize':
        try:
            payload = handler._read_json()
            handler._send_json(server.execute_archive_author_reorganize(payload))
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 作者归档整理失败。')
            handler._send_json(
                {
                    'error_code': 'archive_author_reorganize_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    if parsed.path == '/api/archive/author-job/stop':
        try:
            payload = handler._read_json()
            job_id = str(
                (payload or {}).get('id')
                or (payload or {}).get('job_id')
                or ''
            ).strip()
            handler._send_json(server.stop_archive_author_job(job_id))
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 停止归档整理失败。')
            handler._send_json(
                {
                    'error_code': 'archive_author_stop_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    return False
