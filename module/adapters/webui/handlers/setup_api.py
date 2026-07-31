# coding=UTF-8
"""/api/setup* routes (named setup_api to avoid clashing with webui.setup)."""

from http import HTTPStatus


def handle_get(handler, server, parsed) -> bool:
    if parsed.path != '/api/setup/status':
        return False
    provider = server.setup_status_provider
    if not callable(provider):
        handler._send_error('setup_unavailable', 'Setup status unavailable.', HTTPStatus.NOT_FOUND)
        return True
    try:
        handler._send_json(provider())
    except Exception as e:
        server.diagnostic.exception('[WebUI] 读取初始化状态失败。')
        handler._send_error('setup_status_failed', str(e), HTTPStatus.BAD_REQUEST)
    return True


def handle_post(handler, server, parsed) -> bool:
    if parsed.path == '/api/setup/api':
        if not callable(server.setup_api_saver):
            handler._send_error('setup_unavailable', 'Setup API unavailable.', HTTPStatus.NOT_FOUND)
            return True
        try:
            payload = handler._read_json()
            handler._send_json(server.setup_api_saver(payload))
        except ValueError as e:
            handler._send_error('invalid_setup_api', str(e), HTTPStatus.BAD_REQUEST)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 保存 API 凭证失败。')
            handler._send_error('setup_api_failed', str(e), HTTPStatus.BAD_REQUEST)
        return True

    if parsed.path == '/api/setup/rclone':
        if not callable(server.setup_rclone_configurer):
            handler._send_error('setup_unavailable', 'Setup rclone unavailable.', HTTPStatus.NOT_FOUND)
            return True
        try:
            payload = handler._read_json()
            handler._send_json(server.setup_rclone_configurer(payload))
        except ValueError as e:
            handler._send_error('invalid_setup_rclone', str(e), HTTPStatus.BAD_REQUEST)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 配置 rclone 失败。')
            handler._send_error('setup_rclone_failed', str(e), HTTPStatus.BAD_REQUEST)
        return True

    if parsed.path == '/api/setup/rclone/skip':
        if not callable(server.setup_rclone_skipper):
            handler._send_error('setup_unavailable', 'Setup rclone skip unavailable.', HTTPStatus.NOT_FOUND)
            return True
        try:
            payload = handler._read_json()
            handler._send_json(server.setup_rclone_skipper(payload))
        except Exception as e:
            server.diagnostic.exception('[WebUI] 跳过 rclone 失败。')
            handler._send_error('setup_rclone_skip_failed', str(e), HTTPStatus.BAD_REQUEST)
        return True

    if parsed.path == '/api/setup/rclone/test':
        if not callable(server.setup_rclone_tester):
            handler._send_error('setup_unavailable', 'Setup rclone test unavailable.', HTTPStatus.NOT_FOUND)
            return True
        try:
            payload = handler._read_json()
            handler._send_json(server.setup_rclone_tester(payload))
        except Exception as e:
            server.diagnostic.exception('[WebUI] 探测 rclone 失败。')
            handler._send_error('setup_rclone_test_failed', str(e), HTTPStatus.BAD_REQUEST)
        return True

    if parsed.path == '/api/setup/bot':
        if not callable(server.setup_bot_saver):
            handler._send_error('setup_unavailable', 'Setup bot unavailable.', HTTPStatus.NOT_FOUND)
            return True
        try:
            from module.adapters.webui.setup import BotTokenInvalidError, BotTokenNetworkError
            payload = handler._read_json()
            handler._send_json(server.setup_bot_saver(payload))
        except BotTokenInvalidError as e:
            handler._send_error('invalid_setup_bot', str(e), HTTPStatus.BAD_REQUEST)
        except BotTokenNetworkError as e:
            handler._send_error('setup_bot_network_failed', str(e), HTTPStatus.BAD_REQUEST)
        except ValueError as e:
            handler._send_error('invalid_setup_bot', str(e), HTTPStatus.BAD_REQUEST)
        except Exception as e:
            server.diagnostic.exception('[WebUI] 保存 Bot Token 失败。')
            handler._send_error('setup_bot_failed', str(e), HTTPStatus.BAD_REQUEST)
        return True

    if parsed.path == '/api/setup/bot/skip':
        if not callable(server.setup_bot_skipper):
            handler._send_error('setup_unavailable', 'Setup bot skip unavailable.', HTTPStatus.NOT_FOUND)
            return True
        try:
            payload = handler._read_json()
            handler._send_json(server.setup_bot_skipper(payload))
        except Exception as e:
            server.diagnostic.exception('[WebUI] 跳过 Bot Token 失败。')
            handler._send_error('setup_bot_skip_failed', str(e), HTTPStatus.BAD_REQUEST)
        return True

    return False
