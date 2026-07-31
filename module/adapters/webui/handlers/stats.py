# coding=UTF-8
"""/api/statistics, operations, tables/export, diagnostics/export."""

from http import HTTPStatus
from urllib.parse import parse_qs
import os

from module.adapters.webui.server import WebUiApiError


def handle_get(handler, server, parsed) -> bool:
    if parsed.path == '/api/statistics':
        query = parse_qs(parsed.query)
        tz_offset = handler._query_optional_int(query, 'tz_offset')
        handler._send_json(server.statistics(tz_offset_minutes=tz_offset))
        return True

    if parsed.path == '/api/operations':
        handler._send_json({'operations': server.list_operations()})
        return True

    return False


def handle_post(handler, server, parsed) -> bool:
    if parsed.path == '/api/diagnostics/export':
        try:
            payload = handler._read_json()
            result = server.export_diagnostic_bundle(payload)
            path = str((result or {}).get('path') or '')
            filename = str((result or {}).get('filename') or 'trmd-diagnostic.zip')
            if not path:
                raise WebUiApiError(
                    'diagnostic_export_failed',
                    '诊断包路径为空。',
                    HTTPStatus.BAD_REQUEST,
                )
            with open(path, 'rb') as handle:
                data = handle.read()
            try:
                os.remove(path)
            except OSError:
                pass
            handler._send_bytes_download(
                data,
                filename,
                'application/zip',
            )
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except ValueError as e:
            code = str(e)
            if code == 'acknowledge_secrets_required':
                handler._send_error(
                    code,
                    '请先确认诊断包含登录态与密钥，仅私密传输。',
                    HTTPStatus.BAD_REQUEST,
                )
            elif code == 'transfer_store_unavailable':
                handler._send_error(code, '转存数据库不可用。', HTTPStatus.BAD_REQUEST)
            else:
                handler._send_error('diagnostic_export_failed', str(e), HTTPStatus.BAD_REQUEST)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 导出诊断包失败。')
            handler._send_error('diagnostic_export_failed', str(e), HTTPStatus.BAD_REQUEST)
        return True

    if parsed.path == '/api/tables/export':
        try:
            payload = handler._read_json()
            table_type = str(payload.get('table_type') or '').strip()
            result = server.export_table(table_type)
            handler._send_json(result)
        except WebUiApiError as e:
            handler._send_error(e.error_code, e.message, e.status)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 导出统计表失败。')
            handler._send_json(
                {
                    'error_code': 'export_table_failed',
                    'error': str(e)
                },
                HTTPStatus.BAD_REQUEST
            )
        return True

    return False
