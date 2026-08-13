# coding=UTF-8
"""/api/setup* routes (named setup_api to avoid clashing with webui.setup)."""

from http import HTTPStatus


def handle_get(handler, server, parsed) -> bool:
    if parsed.path == '/api/setup/status':
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

    if parsed.path == '/api/setup/rclone/accounts':
        provider = getattr(server, 'pikpak_accounts_provider', None)
        if not callable(provider):
            handler._send_error('setup_unavailable', 'PikPak accounts unavailable.', HTTPStatus.NOT_FOUND)
            return True
        try:
            handler._send_json(provider())
        except Exception as e:
            server.diagnostic.exception('[WebUI] 读取 PikPak 账号列表失败。')
            handler._send_error('pikpak_accounts_failed', str(e), HTTPStatus.BAD_REQUEST)
        return True

    return False


def _run_setup_post(handler, server, *, fn_name, unavailable_msg, invalid_code,
                    log_message, log_success, catch_value_error=True) -> bool:
    """Shared POST handler skeleton: resolve the route callback, read JSON payload,
    dispatch, and map ValueError → 400 invalid / other → 400 failed. Always True."""
    fn = getattr(server, fn_name, None)
    if not callable(fn):
        handler._send_error('setup_unavailable', unavailable_msg, HTTPStatus.NOT_FOUND)
        return True
    try:
        payload = handler._read_json()
        handler._send_json(fn(payload))
    except ValueError as e:
        if catch_value_error:
            handler._send_error(invalid_code, str(e), HTTPStatus.BAD_REQUEST)
        else:
            server.diagnostic.exception(f'[WebUI] {log_message}。')
            handler._send_error(log_success, str(e), HTTPStatus.BAD_REQUEST)
    except Exception as e:
        server.diagnostic.exception(f'[WebUI] {log_message}。')
        handler._send_error(log_success, str(e), HTTPStatus.BAD_REQUEST)
    return True


def handle_post(handler, server, parsed) -> bool:
    if parsed.path == '/api/setup/api':
        return _run_setup_post(
            handler, server,
            fn_name='setup_api_saver',
            unavailable_msg='Setup API unavailable.', invalid_code='invalid_setup_api',
            log_message='保存 API 凭证失败', log_success='setup_api_failed',
        )

    if parsed.path == '/api/setup/rclone':
        return _run_setup_post(
            handler, server,
            fn_name='setup_rclone_configurer',
            unavailable_msg='Setup rclone unavailable.', invalid_code='invalid_setup_rclone',
            log_message='配置 rclone 失败', log_success='setup_rclone_failed',
        )

    if parsed.path == '/api/setup/rclone/skip':
        return _run_setup_post(
            handler, server,
            fn_name='setup_rclone_skipper',
            unavailable_msg='Setup rclone skip unavailable.', invalid_code='setup_rclone_skip_failed',
            log_message='跳过 rclone 失败', log_success='setup_rclone_skip_failed',
            catch_value_error=False,
        )

    if parsed.path == '/api/setup/rclone/test':
        return _run_setup_post(
            handler, server,
            fn_name='setup_rclone_tester',
            unavailable_msg='Setup rclone test unavailable.', invalid_code='setup_rclone_test_failed',
            log_message='探测 rclone 失败', log_success='setup_rclone_test_failed',
            catch_value_error=False,
        )

    if parsed.path == '/api/setup/rclone/account':
        return _run_setup_post(
            handler, server,
            fn_name='pikpak_account_adder',
            unavailable_msg='PikPak account add unavailable.', invalid_code='invalid_pikpak_account',
            log_message='添加 PikPak 账号失败', log_success='pikpak_account_add_failed',
        )

    if parsed.path == '/api/setup/rclone/switch':
        return _run_setup_post(
            handler, server,
            fn_name='pikpak_account_switcher',
            unavailable_msg='PikPak account switch unavailable.', invalid_code='invalid_pikpak_switch',
            log_message='切换 PikPak 账号失败', log_success='pikpak_switch_failed',
        )

    if parsed.path == '/api/setup/rclone/account/remove':
        return _run_setup_post(
            handler, server,
            fn_name='pikpak_account_remover',
            unavailable_msg='PikPak account remove unavailable.', invalid_code='invalid_pikpak_remove',
            log_message='删除 PikPak 账号失败', log_success='pikpak_remove_failed',
        )

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
