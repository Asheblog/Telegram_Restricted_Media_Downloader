# coding=UTF-8
"""HTML shell, login page, and font static serving."""

from http import HTTPStatus

from module.adapters.webui.assets import WEB_UI_HTML, WEB_UI_MOBILE_HTML, LOGIN_PAGE_HTML, FONTS

import base64
import re


def handle_get(handler, server, parsed) -> bool:
    """Serve fonts and SPA pages. Returns True if handled (before API auth gate)."""
    from module.adapters.webui.server import is_spa_page_path

    if parsed.path.startswith('/fonts/'):
        filename = parsed.path[len('/fonts/'):]
        if filename and '/' not in filename:
            _send_font(handler, filename)
            return True
        handler._send_error('invalid_font_path', 'Invalid font path.', HTTPStatus.BAD_REQUEST)
        return True

    if is_spa_page_path(parsed.path):
        if not handler._check_page_auth():
            _send_login_page(handler)
            return True
        _send_html(handler)
        return True

    return False


def _send_font(handler, filename: str) -> None:
    b64_data = FONTS.get(filename)
    if not b64_data:
        handler._send_error('font_not_found', 'Font not found.', HTTPStatus.NOT_FOUND)
        return
    font_bytes = base64.b64decode(b64_data)
    ext = filename.rsplit('.', 1)[-1] if '.' in filename else 'woff2'
    mime = {
        'woff2': 'font/woff2',
        'woff': 'font/woff',
        'ttf': 'font/truetype',
    }.get(ext, 'font/woff2')
    handler.send_response(HTTPStatus.OK)
    handler.send_header('content-type', mime)
    handler.send_header('cache-control', 'public, max-age=31536000, immutable')
    handler.send_header('content-length', str(len(font_bytes)))
    handler.end_headers()
    handler.wfile.write(font_bytes)


def _send_login_page(handler) -> None:
    data = LOGIN_PAGE_HTML.encode('utf-8')
    handler.send_response(HTTPStatus.OK)
    handler.send_header('content-type', 'text/html; charset=utf-8')
    handler.send_header('cache-control', 'no-store')
    handler.send_header('content-length', str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _send_html(handler) -> None:
    ua = handler.headers.get('user-agent', '')
    is_mobile = bool(re.search(r'Mobile|Android|iPhone|iPod', ua))
    html = WEB_UI_MOBILE_HTML if is_mobile else WEB_UI_HTML
    data = html.encode('utf-8')
    handler.send_response(HTTPStatus.OK)
    handler._write_pending_cookie()
    handler.send_header('content-type', 'text/html; charset=utf-8')
    handler.send_header('cache-control', 'no-store')
    handler.send_header('content-length', str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)
