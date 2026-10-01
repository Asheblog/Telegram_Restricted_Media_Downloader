# coding=UTF-8
"""/api/auth* routes."""

from http import HTTPStatus


def handle_get(handler, server, parsed) -> bool:
    if parsed.path != '/api/auth/status':
        return False
    if server.auth_provider:
        handler._send_json(server.auth_provider.get_state())
    else:
        handler._send_json({'step': 'none', 'error': None, 'user': None})
    return True


def handle_post_public(handler, server, parsed) -> bool:
    """Login is the only write route reachable without a session cookie.

    ``/api/auth/logout`` 不再走公开分支——它必须穿过鉴权门，返回 401 而不是
    200，未授权者也就无法再用「logout 200 / 其它 401」枚举路由白名单。
    """
    if parsed.path != '/api/auth/login':
        return False
    _handle_login(handler, server)
    return True


def handle_post(handler, server, parsed) -> bool:
    if parsed.path == '/api/auth/logout':
        _handle_logout(handler, server)
        return True
    if parsed.path != '/api/auth/submit':
        return False
    payload = handler._read_json()
    if server.auth_provider:
        server.auth_provider.submit(payload)
        handler._send_json({'accepted': True})
    else:
        handler._send_error('no_auth_provider', 'No auth provider configured.', HTTPStatus.SERVICE_UNAVAILABLE)
    return True


def _handle_login(handler, server) -> None:
    payload = handler._read_json()
    username = str(payload.get('username') or '').strip()
    password = str(payload.get('password') or '')
    remember_me = bool(payload.get('remember_me'))
    if not username or not password:
        handler._send_json({'error': '请输入用户名和密码。'}, HTTPStatus.BAD_REQUEST)
        return
    if not server.validate_credentials(username, password):
        _reject_login(handler, server, username)
        return
    server.clear_login_failures(handler, username)
    token = server._generate_session_token()
    cookie = server._create_session_cookie(
        token,
        remember_me=remember_me,
        secure=server.cookie_secure_required(handler),
    )
    handler._send_json({'success': True}, HTTPStatus.OK, {'Set-Cookie': cookie})


def _reject_login(handler, server, username: str) -> None:
    """Count the failure first, then answer.

    限流只累计**错误凭据**：口令正确时上面已经放行并清零计数，攻击者无法靠
    打满失败窗口把管理员锁在门外（不把反爆破做成可用性攻击）。
    """
    retry_after = server.register_login_failure(handler, username)
    if retry_after > 0:
        handler._send_json(
            {
                'error_code': 'too_many_attempts',
                'error': f'登录失败次数过多，请在 {retry_after} 秒后重试。',
            },
            HTTPStatus.TOO_MANY_REQUESTS,
            {'retry-after': str(retry_after)},
        )
        return
    handler._send_json({'error': '用户名或密码错误。'}, HTTPStatus.UNAUTHORIZED)


def _handle_logout(handler, server) -> None:
    """Requires a valid session (the auth gate runs before this handler)."""
    cookie = server._clear_session_cookie(
        secure=server.cookie_secure_required(handler)
    )
    handler._send_json({'success': True}, HTTPStatus.OK, {'Set-Cookie': cookie})
