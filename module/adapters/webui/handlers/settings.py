# coding=UTF-8
"""/api/settings* routes."""

from http import HTTPStatus

from module.adapters.webui.server import sanitize_settings
from module.adapters.webui.view_model import WebUiViewModel


def handle_get(handler, server, parsed) -> bool:
    if parsed.path != '/api/settings':
        return False
    settings = server.get_sanitized_settings()
    schema = server.settings_schema()
    handler._send_json({
        'settings': settings,
        'schema': schema,
        'settings_model': WebUiViewModel.settings_model(settings, schema)
    })
    return True


def handle_patch(handler, server, parsed) -> bool:
    if parsed.path != '/api/settings':
        return False
    try:
        payload = handler._read_json()
        settings = server.update_settings(payload)
        sanitized = sanitize_settings(settings)
        schema = server.settings_schema()
        handler._send_json({
            'settings': sanitized,
            'schema': schema,
            'settings_model': WebUiViewModel.settings_model(sanitized, schema)
        })
    except Exception as e:
        server.diagnostic.exception('[WebUI] 更新设置失败。')
        handler._send_json(
            {
                'error_code': 'update_settings_failed',
                'error': str(e)
            },
            HTTPStatus.BAD_REQUEST
        )
    return True
