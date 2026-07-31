# coding=UTF-8
"""/api/auth* routes."""

from http import HTTPStatus
import json


def handle_get(handler, server, parsed) -> bool:
    if parsed.path != '/api/auth/status':
        return False
    if server.auth_provider:
        handler._send_json(server.auth_provider.get_state())
    else:
        handler._send_json({'step': 'none', 'error': None, 'user': None})
    return True


def handle_post_public(handler, server, parsed) -> bool:
    """Login/logout — no auth cookie required."""
    if parsed.path == '/api/auth/login':
        _handle_login(handler, server)
        return True
    if parsed.path == '/api/auth/logout':
        _handle_logout(handler, server)
        return True
    return False


def handle_post(handler, server, parsed) -> bool:
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
        handler._send_json({'error': '用户名或密码错误。'}, HTTPStatus.UNAUTHORIZED)
        return
    token = server._generate_session_token()
    cookie = server._create_session_cookie(token, remember_me=remember_me)
    handler.send_response(HTTPStatus.OK)
    handler.send_header('Set-Cookie', cookie)
    handler.send_header('content-type', 'application/json; charset=utf-8')
    handler.send_header('cache-control', 'no-store')
    data = json.dumps({'success': True}).encode('utf-8')
    handler.send_header('content-length', str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _handle_logout(handler, server) -> None:
    cookie = f'{server.SESSION_COOKIE_NAME}=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax'
    handler.send_response(HTTPStatus.OK)
    handler.send_header('Set-Cookie', cookie)
    handler.send_header('content-type', 'application/json; charset=utf-8')
    handler.send_header('cache-control', 'no-store')
    data = json.dumps({'success': True}).encode('utf-8')
    handler.send_header('content-length', str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)
