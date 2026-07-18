# coding=UTF-8
import base64
import datetime
import hashlib
import hmac
import json
import os
import re
import secrets
import socket
import threading
import time
import webbrowser

from copy import deepcopy
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional
from urllib.parse import unquote, urlparse, parse_qs

from module.diagnostics import default_diagnostic
from module.enums import ENVIRON
from module.ports import IWebUiOperations, IDiagnosticPort
from module.transfer_store import TransferStore
from module.adapters.webui.view_model import WebUiViewModel
from module.adapters.webui.assets import WEB_UI_HTML, WEB_UI_MOBILE_HTML, LOGIN_PAGE_HTML, FONTS


SENSITIVE_SETTING_KEYS = {
    'api_hash',
    'bot_token',
    'password',
    'username'
}

# WebUI SPA 视图路径（刷新后由前端按 pathname 恢复对应视图）
SPA_VIEW_PATHS = frozenset({
    '/',
    '/index.html',
    '/transfers',
    '/watches',
    '/downloads-uploads',
    '/statistics',
    '/records',
    '/media',
    '/archive-organize',
    '/system-logs',
    '/settings',
    '/profile',
})


def is_spa_page_path(path: str) -> bool:
    """Whether a GET path should serve the SPA shell (not /api or static files)."""
    if not path:
        return True
    if path.startswith('/api/') or path.startswith('/fonts/'):
        return False
    normalized = path.rstrip('/') or '/'
    if normalized in SPA_VIEW_PATHS or path == '/index.html':
        return True
    leaf = normalized.rsplit('/', 1)[-1]
    if leaf and '.' in leaf:
        return False
    # Unknown path without extension: still serve SPA so client can rewrite.
    return True


class WebUiApiError(Exception):
    def __init__(self, error_code: str, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status = status


def normalize_optional_int(value):
    return int(value) if value not in (None, '') else None


def is_message_link(link: str) -> bool:
    try:
        parsed = urlparse(str(link).strip())
    except ValueError:
        return False
    paths = [part for part in parsed.path.split('/') if part]
    if not paths:
        return False
    if paths[0] == 'c':
        return len(paths) >= 3 and paths[-1].isdigit()
    return len(paths) >= 2 and paths[-1].isdigit()


def normalize_detected_transfer_range(value) -> Optional[tuple[int, int]]:
    if value in (None, ''):
        return None
    if isinstance(value, dict):
        start_id = value.get('start_id')
        end_id = value.get('end_id')
    else:
        try:
            start_id, end_id = value
        except (TypeError, ValueError):
            return None
    if start_id in (None, '') or end_id in (None, ''):
        return None
    return int(start_id), int(end_id)


class AuthProvider:
    """Thread-safe auth provider for WebUI Telegram login flow."""

    STEP_PENDING = 'pending'
    STEP_PHONE = 'phone'
    STEP_CODE = 'code'
    STEP_PASSWORD = 'password'
    STEP_RECOVERY_CODE = 'recovery_code'
    STEP_EMAIL_CODE = 'email_code'
    STEP_SIGNUP = 'signup'
    STEP_DONE = 'done'
    STEP_ERROR = 'error'

    def __init__(self):
        self.step: str = self.STEP_PENDING
        self.message: str = ''
        self.hint: str = ''
        self.code_type: str = ''
        self.error: Optional[str] = None
        self.user_info: Optional[str] = None
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._input_value: Optional[dict] = None

    def wait_for_input(self) -> dict:
        self._event.clear()
        self._event.wait()
        with self._lock:
            val = self._input_value or {}
            self._input_value = None
        return val

    def submit(self, value: dict) -> None:
        with self._lock:
            self._input_value = value
            self.error = None
        self._event.set()

    def set_step(self, step: str, message: str = '', hint: str = '', code_type: str = ''):
        with self._lock:
            self.step = step
            self.message = message
            self.hint = hint
            self.code_type = code_type or step

    def set_error(self, error: str):
        with self._lock:
            self.error = error
            self.step = self.STEP_ERROR

    def set_done(self, user_info: str):
        with self._lock:
            self.step = self.STEP_DONE
            self.user_info = user_info
            self.error = None

    def get_state(self) -> dict:
        with self._lock:
            return {
                'step': self.step,
                'message': self.message,
                'hint': self.hint,
                'code_type': self.code_type,
                'error': self.error,
                'user': self.user_info
            }


class WebUiServer:
    SETUP_ALLOWED_PREFIXES = (
        '/api/auth/',
        '/api/setup/',
        '/api/settings',
    )

    def __init__(
            self,
            store: TransferStore,
            task_submitter: Optional[Callable[[int], None]] = None,
            settings_provider: Optional[Callable[[], dict]] = None,
            settings_updater: Optional[Callable[[dict], dict]] = None,
            operations: Optional[IWebUiOperations] = None,
            host: str = '127.0.0.1',
            port: int = 0,
            username: Optional[str] = None,
            password: Optional[str] = None,
            diagnostic: Optional[IDiagnosticPort] = None,
            deep_link_whitelist_getter: Optional[Callable[[], list]] = None,
            setup_status_provider: Optional[Callable[[], dict]] = None,
            setup_api_saver: Optional[Callable[[dict], dict]] = None,
            setup_rclone_configurer: Optional[Callable[[dict], dict]] = None,
            setup_rclone_skipper: Optional[Callable[[Optional[dict]], dict]] = None,
            setup_rclone_tester: Optional[Callable[[Optional[dict]], dict]] = None,
            setup_ready_checker: Optional[Callable[[], bool]] = None,
    ):
        self.store = store
        self.view_model = WebUiViewModel(store)
        self.task_submitter = task_submitter
        self.settings_provider = settings_provider
        self.settings_updater = settings_updater
        self.operations = operations
        self.host = host
        self.port = self.resolve_port(port)
        self.username = (username or '').strip()
        self.password = password or ''
        self.diagnostic = diagnostic or default_diagnostic
        self.deep_link_whitelist_getter = deep_link_whitelist_getter
        self.setup_status_provider = setup_status_provider
        self.setup_api_saver = setup_api_saver
        self.setup_rclone_configurer = setup_rclone_configurer
        self.setup_rclone_skipper = setup_rclone_skipper
        self.setup_rclone_tester = setup_rclone_tester
        self.setup_ready_checker = setup_ready_checker
        self.httpd: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.auth_provider: Optional[AuthProvider] = None
        self.validate_auth_config()

    def is_setup_ready(self) -> bool:
        checker = self.setup_ready_checker
        if callable(checker):
            try:
                return bool(checker())
            except Exception:
                return False
        return True

    def is_setup_path_allowed(self, path: str) -> bool:
        if path in ('/api/auth/login', '/api/auth/logout', '/api/auth/status', '/api/auth/submit'):
            return True
        if path == '/api/settings' or path.startswith('/api/settings?'):
            return True
        return any(path == prefix.rstrip('/') or path.startswith(prefix) for prefix in self.SETUP_ALLOWED_PREFIXES)

    def _require_deep_link_whitelist_if_enabled(self, resolve_deep_link: bool) -> None:
        if not resolve_deep_link:
            return
        getter = getattr(self, 'deep_link_whitelist_getter', None)
        whitelist = list(getter() or []) if callable(getter) else []
        if not whitelist:
            raise WebUiApiError(
                'deep_link_whitelist_required',
                '已开启深链取片，请先在系统设置填写资源 bot 白名单。',
                HTTPStatus.BAD_REQUEST,
            )

    def _operation(self, name: str):
        if self.operations is None:
            return None
        method = getattr(self.operations, name, None)
        return method if callable(method) else None

    @staticmethod
    def resolve_port(port: int) -> int:
        env_port = int(port or 0)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('', env_port))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return int(sock.getsockname()[1])

    @property
    def url(self) -> str:
        return f'http://{self.host}:{self.port}'

    @property
    def auth_enabled(self) -> bool:
        return bool(self.username and self.password)

    @property
    def requires_auth(self) -> bool:
        return self.host not in ('127.0.0.1', 'localhost', '::1')

    SESSION_COOKIE_NAME = 'trmd_session'
    SESSION_MAX_AGE = 30 * 24 * 60 * 60  # 30 days
    SESSION_NONCE_BYTES = 16

    def validate_auth_config(self) -> None:
        if bool(self.username) != bool(self.password):
            raise ValueError('TRMD_WEB_USERNAME 和 TRMD_WEB_PASSWORD 必须同时设置。')
        if self.requires_auth and not self.auth_enabled:
            raise ValueError('WebUI 对外监听时必须设置 TRMD_WEB_USERNAME 和 TRMD_WEB_PASSWORD。')

    def _session_signing_key(self) -> bytes:
        material = f'{self.username}\0{self.password}'.encode('utf-8')
        return hashlib.sha256(b'trmd-webui-session\0' + material).digest()

    def _sign_session_payload(self, payload: str) -> str:
        return hmac.new(
            self._session_signing_key(),
            payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

    def _generate_session_token(self) -> str:
        expiry = int(time.time()) + self.SESSION_MAX_AGE
        nonce = secrets.token_hex(self.SESSION_NONCE_BYTES)
        payload = f'{expiry}.{nonce}'
        return f'{payload}.{self._sign_session_payload(payload)}'

    def _create_session_cookie(self, token: str, remember_me: bool = True) -> str:
        parts = [
            f'{self.SESSION_COOKIE_NAME}={token}',
            'Path=/',
            'HttpOnly',
            'SameSite=Lax',
        ]
        if remember_me:
            parts.insert(1, f'Max-Age={self.SESSION_MAX_AGE}')
        return '; '.join(parts)

    def validate_session_token(self, token: str) -> bool:
        if not token or not self.auth_enabled:
            return False
        parts = token.split('.')
        if len(parts) != 3:
            return False
        expiry_text, nonce, signature = parts
        if not expiry_text.isdigit() or not nonce or not signature:
            return False
        payload = f'{expiry_text}.{nonce}'
        expected = self._sign_session_payload(payload)
        if not hmac.compare_digest(signature, expected):
            return False
        if time.time() > int(expiry_text):
            return False
        return True

    @staticmethod
    def _get_request_cookie(handler: BaseHTTPRequestHandler, name: str) -> Optional[str]:
        cookie_header = handler.headers.get('cookie')
        if not cookie_header:
            return None
        prefix = f'{name}='
        for part in cookie_header.split(';'):
            part = part.strip()
            if part.startswith(prefix):
                return part[len(prefix):]
        return None

    def validate_credentials(self, username: str, password: str) -> bool:
        if not self.auth_enabled:
            return True
        return (
            secrets.compare_digest(username, self.username)
            and secrets.compare_digest(password, self.password)
        )

    def set_auth_provider(self, provider: "AuthProvider") -> None:
        self.auth_provider = provider

    def start(self, open_browser: bool = True) -> None:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                server.diagnostic.info('[WebUI] ' + fmt, *args)

            def _send_auth_required(self):
                data = json.dumps(
                    {
                        'error_code': 'auth_required',
                        'error': 'Authentication required.'
                    },
                    ensure_ascii=False
                ).encode('utf-8')
                self.send_response(HTTPStatus.UNAUTHORIZED)
                self.send_header('content-type', 'application/json; charset=utf-8')
                self.send_header('cache-control', 'no-store')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _write_pending_cookie(self):
                cookie = getattr(self, '_pending_cookie', None)
                if cookie:
                    self.send_header('Set-Cookie', cookie)
                    self._pending_cookie = None

            def _try_authorize(self):
                """Check and apply auth silently. Returns True if authorized."""
                if not server.auth_enabled:
                    return True
                session_token = server._get_request_cookie(self, server.SESSION_COOKIE_NAME)
                return bool(session_token and server.validate_session_token(session_token))

            def _check_auth(self):
                path = urlparse(self.path).path
                if path in ('/api/auth/login', '/api/auth/logout'):
                    return True
                if self._try_authorize():
                    return True
                self._send_auth_required()
                return False

            def _send_setup_required(self):
                data = json.dumps(
                    {
                        'error_code': 'setup_required',
                        'error': '请先完成初始化配置。',
                    },
                    ensure_ascii=False
                ).encode('utf-8')
                self.send_response(HTTPStatus.CONFLICT)
                self.send_header('content-type', 'application/json; charset=utf-8')
                self.send_header('cache-control', 'no-store')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _check_setup_ready(self):
                path = urlparse(self.path).path
                if not path.startswith('/api/'):
                    return True
                if server.is_setup_path_allowed(path):
                    return True
                if server.is_setup_ready():
                    return True
                self._send_setup_required()
                return False

            def _check_page_auth(self):
                """Check auth silently — returns bool without sending error response."""
                return self._try_authorize()

            def _send_login_page(self):
                data = LOGIN_PAGE_HTML.encode('utf-8')
                self.send_response(HTTPStatus.OK)
                self.send_header('content-type', 'text/html; charset=utf-8')
                self.send_header('cache-control', 'no-store')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _send_font(self, filename: str):
                b64_data = FONTS.get(filename)
                if not b64_data:
                    self._send_error('font_not_found', 'Font not found.', HTTPStatus.NOT_FOUND)
                    return
                font_bytes = base64.b64decode(b64_data)
                ext = filename.rsplit('.', 1)[-1] if '.' in filename else 'woff2'
                mime = {
                    'woff2': 'font/woff2',
                    'woff': 'font/woff',
                    'ttf': 'font/truetype',
                }.get(ext, 'font/woff2')
                self.send_response(HTTPStatus.OK)
                self.send_header('content-type', mime)
                self.send_header('cache-control', 'public, max-age=31536000, immutable')
                self.send_header('content-length', str(len(font_bytes)))
                self.end_headers()
                self.wfile.write(font_bytes)

            def _send_json(self, payload, status=HTTPStatus.OK):
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                self.send_response(status)
                self._write_pending_cookie()
                self.send_header('content-type', 'application/json; charset=utf-8')
                self.send_header('cache-control', 'no-store')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _send_text_download(self, content: str, filename: str):
                data = (content or '').encode('utf-8')
                self.send_response(HTTPStatus.OK)
                self._write_pending_cookie()
                self.send_header('content-type', 'text/plain; charset=utf-8')
                self.send_header(
                    'content-disposition',
                    f'attachment; filename="{filename}"'
                )
                self.send_header('cache-control', 'no-store')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _send_json_download(self, payload, filename: str):
                data = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
                self.send_response(HTTPStatus.OK)
                self._write_pending_cookie()
                self.send_header('content-type', 'application/json; charset=utf-8')
                self.send_header(
                    'content-disposition',
                    f'attachment; filename="{filename}"'
                )
                self.send_header('cache-control', 'no-store')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _send_error(self, error_code, fallback, status):
                self._send_json(
                    {
                        'error_code': error_code,
                        'error': fallback
                    },
                    status
                )

            def _send_html(self):
                ua = self.headers.get('user-agent', '')
                is_mobile = bool(re.search(r'Mobile|Android|iPhone|iPod', ua))
                html = WEB_UI_MOBILE_HTML if is_mobile else WEB_UI_HTML
                data = html.encode('utf-8')
                self.send_response(HTTPStatus.OK)
                self._write_pending_cookie()
                self.send_header('content-type', 'text/html; charset=utf-8')
                self.send_header('cache-control', 'no-store')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _read_json(self):
                length = int(self.headers.get('content-length') or '0')
                raw = self.rfile.read(length)
                if not raw:
                    return {}
                return json.loads(raw.decode('utf-8'))

            @staticmethod
            def _query_int(query: dict, key: str, default: int) -> int:
                try:
                    return int((query.get(key) or [str(default)])[0])
                except (ValueError, TypeError):
                    return default

            @staticmethod
            def _query_optional_int(query: dict, key: str) -> int | None:
                raw = (query.get(key) or [''])[0]
                if raw in ('', None):
                    return None
                try:
                    return int(raw)
                except (ValueError, TypeError):
                    return None

            def _task_id_from_path(self):
                task_path = urlparse(self.path).path
                task_id = task_path.rsplit('/', 1)[-1]
                if not task_id.isdigit():
                    self._send_error('invalid_task_id', 'Invalid task id.', HTTPStatus.BAD_REQUEST)
                    return None
                return int(task_id)

            def _handle_login(self):
                payload = self._read_json()
                username = str(payload.get('username') or '').strip()
                password = str(payload.get('password') or '')
                remember_me = bool(payload.get('remember_me'))
                if not username or not password:
                    self._send_json({'error': '请输入用户名和密码。'}, HTTPStatus.BAD_REQUEST)
                    return
                if not server.validate_credentials(username, password):
                    self._send_json({'error': '用户名或密码错误。'}, HTTPStatus.UNAUTHORIZED)
                    return
                token = server._generate_session_token()
                cookie = server._create_session_cookie(token, remember_me=remember_me)
                self.send_response(HTTPStatus.OK)
                self.send_header('Set-Cookie', cookie)
                self.send_header('content-type', 'application/json; charset=utf-8')
                self.send_header('cache-control', 'no-store')
                data = json.dumps({'success': True}).encode('utf-8')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _handle_logout(self):
                cookie = f'{server.SESSION_COOKIE_NAME}=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax'
                self.send_response(HTTPStatus.OK)
                self.send_header('Set-Cookie', cookie)
                self.send_header('content-type', 'application/json; charset=utf-8')
                self.send_header('cache-control', 'no-store')
                data = json.dumps({'success': True}).encode('utf-8')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                parsed = urlparse(self.path)

                # Font files (public, no auth required)
                if parsed.path.startswith('/fonts/'):
                    filename = parsed.path[len('/fonts/'):]
                    if filename and '/' not in filename:
                        self._send_font(filename)
                        return
                    self._send_error('invalid_font_path', 'Invalid font path.', HTTPStatus.BAD_REQUEST)
                    return

                # SPA page requests: show login page when unauthorized
                if is_spa_page_path(parsed.path):
                    if not self._check_page_auth():
                        self._send_login_page()
                        return
                    self._send_html()
                    return

                # API / other requests require auth
                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                if parsed.path == '/api/auth/status':
                    if server.auth_provider:
                        self._send_json(server.auth_provider.get_state())
                    else:
                        self._send_json({'step': 'none', 'error': None, 'user': None})
                    return
                if parsed.path == '/api/setup/status':
                    provider = server.setup_status_provider
                    if not callable(provider):
                        self._send_error('setup_unavailable', 'Setup status unavailable.', HTTPStatus.NOT_FOUND)
                        return
                    try:
                        self._send_json(provider())
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 读取初始化状态失败。')
                        self._send_error('setup_status_failed', str(e), HTTPStatus.BAD_REQUEST)
                    return
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
                    self._send_json(payload)
                    return
                if parsed.path == '/api/settings':
                    settings = server.get_sanitized_settings()
                    schema = server.settings_schema()
                    self._send_json({
                        'settings': settings,
                        'schema': schema,
                        'settings_model': WebUiViewModel.settings_model(settings, schema)
                    })
                    return
                if parsed.path == '/api/download-records':
                    query = parse_qs(parsed.query)
                    limit = self._query_int(query, 'limit', 50)
                    offset = self._query_int(query, 'offset', 0)
                    total = server.store.count_download_success_records()
                    records = server.store.list_download_success_records(
                        limit=limit,
                        offset=offset
                    )
                    self._send_json({
                        'records': records,
                        'total': total,
                        'limit': limit,
                        'offset': offset
                    })
                    return
                if parsed.path == '/api/statistics':
                    query = parse_qs(parsed.query)
                    tz_offset = self._query_optional_int(query, 'tz_offset')
                    self._send_json(server.statistics(tz_offset_minutes=tz_offset))
                    return
                if parsed.path == '/api/operations':
                    self._send_json({'operations': server.list_operations()})
                    return
                if parsed.path == '/api/watches/forward/export':
                    payload = server.export_forward_watches()
                    stamp = time.strftime('%Y%m%d-%H%M%S')
                    self._send_json_download(payload, f'forward-watches-{stamp}.json')
                    return
                if parsed.path == '/api/watches':
                    query = parse_qs(parsed.query)
                    tz_offset = self._query_optional_int(query, 'tz_offset')
                    self._send_json({'watches': server.list_watches(tz_offset_minutes=tz_offset)})
                    return
                if parsed.path.startswith('/api/watches/') and parsed.path.endswith('/events'):
                    watch_path = parsed.path[len('/api/watches/'):][:-len('/events')]
                    watch_id = unquote(watch_path)
                    if not watch_id:
                        self._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
                        return
                    query = parse_qs(parsed.query)
                    limit = self._query_int(query, 'limit', 50)
                    offset = self._query_int(query, 'offset', 0)
                    today_only = str((query.get('today') or [''])[0]).lower() in ('1', 'true', 'yes')
                    tz_offset = self._query_optional_int(query, 'tz_offset')
                    status = str((query.get('status') or [''])[0]).strip() or None
                    if status and status not in ('success', 'skipped', 'failure'):
                        self._send_error('invalid_status', 'Invalid status filter.', HTTPStatus.BAD_REQUEST)
                        return
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
                            self._send_error('invalid_status', 'Invalid status filter.', HTTPStatus.BAD_REQUEST)
                            return
                        raise
                    if not result:
                        self._send_error('watch_not_found', 'Watch not found.', HTTPStatus.NOT_FOUND)
                        return
                    self._send_json(result)
                    return
                if parsed.path.startswith('/api/watches/') and parsed.path.endswith('/download-tasks'):
                    watch_path = parsed.path[len('/api/watches/'):][:-len('/download-tasks')]
                    watch_id = unquote(watch_path)
                    if not watch_id:
                        self._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
                        return
                    query = parse_qs(parsed.query)
                    limit = self._query_int(query, 'limit', 200)
                    payload = server.view_model.watch_download_tasks(watch_id, limit=limit)
                    if payload is None:
                        self._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
                        return
                    self._send_json(payload)
                    return
                if parsed.path.startswith('/api/watches/') and parsed.path.endswith('/deferred-comments'):
                    watch_path = parsed.path[len('/api/watches/'):][:-len('/deferred-comments')]
                    watch_id = unquote(watch_path)
                    if not watch_id:
                        self._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
                        return
                    result = server.list_deferred_discussion_captures(watch_id)
                    if result is None:
                        self._send_error('watch_not_found', 'Watch not found.', HTTPStatus.NOT_FOUND)
                        return
                    self._send_json(result)
                    return
                if parsed.path.startswith('/api/tasks/'):
                    # 提取路径段: /api/tasks/123 或 /api/tasks/123/summary
                    subpath = parsed.path[len('/api/tasks/'):]
                    parts = [p for p in subpath.split('/') if p]
                    if not parts or not parts[0].isdigit():
                        self._send_error('invalid_task_id', 'Invalid task id.', HTTPStatus.BAD_REQUEST)
                        return
                    task_id = int(parts[0])
                    query = parse_qs(parsed.query)
                    if len(parts) > 1 and parts[1] == 'summary':
                        payload = server.view_model.task_summary(task_id)
                    else:
                        payload = server.view_model.task_detail(
                            task_id,
                            item_limit=self._query_int(query, 'items_limit', 200),
                            item_offset=self._query_int(query, 'items_offset', 0),
                            item_status=(query.get('item_status') or [''])[0] or None,
                            event_limit=self._query_int(query, 'events_limit', 100),
                            event_offset=self._query_int(query, 'events_offset', 0),
                        )
                    if not payload:
                        self._send_error('task_not_found', 'Task not found.', HTTPStatus.NOT_FOUND)
                        return
                    self._send_json(payload)
                    return
                if parsed.path == '/api/media/scan':
                    query = parse_qs(parsed.query)
                    task_id = self._query_int(query, 'task_id', 0) or None
                    items_limit = self._query_int(query, 'items_limit', 0) or None
                    items_offset = self._query_int(query, 'items_offset', 0)
                    orphans_limit = self._query_int(query, 'orphans_limit', 0) or None
                    orphans_offset = self._query_int(query, 'orphans_offset', 0)
                    self._send_json(server.scan_media_for_cleanup(
                        task_id=task_id,
                        items_limit=items_limit,
                        items_offset=items_offset,
                        orphans_limit=orphans_limit,
                        orphans_offset=orphans_offset,
                    ))
                    return
                if parsed.path == '/api/media/cleanup-logs':
                    self._send_json({'logs': server.list_cleanup_logs()})
                    return
                if parsed.path == '/api/archive/author-channels':
                    try:
                        self._send_json(server.list_archive_author_channels())
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 列出归档频道失败。')
                        self._send_json(
                            {
                                'error_code': 'archive_author_channels_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/archive/author-job':
                    query = parse_qs(parsed.query)
                    job_id = (query.get('id') or [None])[0]
                    active = (query.get('active') or ['0'])[0]
                    channel_folder = (query.get('channel_folder') or [None])[0]
                    try:
                        if str(active) in ('1', 'true', 'yes'):
                            self._send_json(server.get_active_archive_author_job(channel_folder))
                            return
                        if not job_id:
                            raise ValueError('id is required')
                        self._send_json(server.get_archive_author_job(str(job_id)))
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 查询归档整理进度失败。')
                        self._send_json(
                            {
                                'error_code': 'archive_author_job_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/system-logs':
                    query = parse_qs(parsed.query)
                    limit = self._query_int(query, 'limit', 50)
                    offset = self._query_int(query, 'offset', 0)
                    category = (query.get('category') or [None])[0]
                    level = (query.get('level') or [None])[0]
                    trace_id = (query.get('trace_id') or [None])[0]
                    watch_id = (query.get('watch_id') or [None])[0]
                    today_only = (query.get('today') or ['0'])[0] in ('1', 'true', 'yes')
                    tz_offset = self._query_int(query, 'tz_offset', None)
                    self._send_json(server.list_system_logs(
                        limit=limit,
                        offset=offset,
                        category=category,
                        level=level,
                        trace_id=trace_id,
                        watch_id=watch_id,
                        today_only=today_only,
                        tz_offset_minutes=tz_offset
                    ))
                    return
                if parsed.path == '/api/system-logs/export':
                    query = parse_qs(parsed.query)
                    category = (query.get('category') or [None])[0]
                    level = (query.get('level') or [None])[0]
                    trace_id = (query.get('trace_id') or [None])[0]
                    watch_id = (query.get('watch_id') or [None])[0]
                    today_only = (query.get('today') or ['0'])[0] in ('1', 'true', 'yes')
                    tz_offset = self._query_int(query, 'tz_offset', None)
                    content = server.export_system_logs(
                        category=category,
                        level=level,
                        trace_id=trace_id,
                        watch_id=watch_id,
                        today_only=today_only,
                        tz_offset_minutes=tz_offset
                    )
                    stamp = time.strftime('%Y%m%d-%H%M%S')
                    self._send_text_download(content, f'system-logs-{stamp}.txt')
                    return
                self._send_error('not_found', 'Not found.', HTTPStatus.NOT_FOUND)

            def do_POST(self):
                parsed = urlparse(self.path)

                # Public endpoints: login / logout
                if parsed.path == '/api/auth/login':
                    self._handle_login()
                    return
                if parsed.path == '/api/auth/logout':
                    self._handle_logout()
                    return

                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                if parsed.path == '/api/auth/submit':
                    payload = self._read_json()
                    if server.auth_provider:
                        server.auth_provider.submit(payload)
                        self._send_json({'accepted': True})
                    else:
                        self._send_error('no_auth_provider', 'No auth provider configured.', HTTPStatus.SERVICE_UNAVAILABLE)
                    return
                if parsed.path == '/api/setup/api':
                    if not callable(server.setup_api_saver):
                        self._send_error('setup_unavailable', 'Setup API unavailable.', HTTPStatus.NOT_FOUND)
                        return
                    try:
                        payload = self._read_json()
                        self._send_json(server.setup_api_saver(payload))
                    except ValueError as e:
                        self._send_error('invalid_setup_api', str(e), HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 保存 API 凭证失败。')
                        self._send_error('setup_api_failed', str(e), HTTPStatus.BAD_REQUEST)
                    return
                if parsed.path == '/api/setup/rclone':
                    if not callable(server.setup_rclone_configurer):
                        self._send_error('setup_unavailable', 'Setup rclone unavailable.', HTTPStatus.NOT_FOUND)
                        return
                    try:
                        payload = self._read_json()
                        self._send_json(server.setup_rclone_configurer(payload))
                    except ValueError as e:
                        self._send_error('invalid_setup_rclone', str(e), HTTPStatus.BAD_REQUEST)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 配置 rclone 失败。')
                        self._send_error('setup_rclone_failed', str(e), HTTPStatus.BAD_REQUEST)
                    return
                if parsed.path == '/api/setup/rclone/skip':
                    if not callable(server.setup_rclone_skipper):
                        self._send_error('setup_unavailable', 'Setup rclone skip unavailable.', HTTPStatus.NOT_FOUND)
                        return
                    try:
                        payload = self._read_json()
                        self._send_json(server.setup_rclone_skipper(payload))
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 跳过 rclone 失败。')
                        self._send_error('setup_rclone_skip_failed', str(e), HTTPStatus.BAD_REQUEST)
                    return
                if parsed.path == '/api/setup/rclone/test':
                    if not callable(server.setup_rclone_tester):
                        self._send_error('setup_unavailable', 'Setup rclone test unavailable.', HTTPStatus.NOT_FOUND)
                        return
                    try:
                        payload = self._read_json()
                        self._send_json(server.setup_rclone_tester(payload))
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 探测 rclone 失败。')
                        self._send_error('setup_rclone_test_failed', str(e), HTTPStatus.BAD_REQUEST)
                    return
                task_action = server.parse_task_action_path(parsed.path)
                if task_action:
                    task_id, action = task_action
                    try:
                        self._send_json(server.apply_task_action(task_id, action), HTTPStatus.ACCEPTED)
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 执行任务操作失败。')
                        self._send_json(
                            {
                                'error_code': 'task_action_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/watches/forward/import':
                    try:
                        payload = self._read_json()
                        result = server.import_forward_watches(payload)
                        self._send_json(result)
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 导入监听转发失败。')
                        self._send_json(
                            {
                                'error_code': 'import_forward_watches_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/watches':
                    try:
                        payload = self._read_json()
                        result = server.create_watch(payload)
                        self._send_json(result, HTTPStatus.CREATED)
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 创建实时监听失败。')
                        self._send_json(
                            {
                                'error_code': 'create_watch_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
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
                        self._send_error('not_found', 'Not found.', HTTPStatus.NOT_FOUND)
                        return
                    watch_part, capture_part = remainder.split(marker, 1)
                    watch_id = unquote(watch_part)
                    if not watch_id or not capture_part.isdigit():
                        self._send_error('invalid_watch_id', 'Invalid deferred comment id.', HTTPStatus.BAD_REQUEST)
                        return
                    capture_id = int(capture_part)
                    try:
                        if action == 'cancel':
                            ok = server.cancel_deferred_discussion_capture(watch_id, capture_id)
                        elif action == 'run-now':
                            ok = server.run_deferred_discussion_capture_now(watch_id, capture_id)
                        else:
                            ok = server.retry_deferred_discussion_capture(watch_id, capture_id)
                        if not ok:
                            self._send_error('deferred_comment_not_found', 'Deferred comment job not found.', HTTPStatus.NOT_FOUND)
                            return
                        self._send_json({'ok': True, 'action': action, 'id': capture_id})
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 操作延迟评论区任务失败。')
                        self._send_json(
                            {'error_code': 'deferred_comment_action_failed', 'error': str(e)},
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/tables/export':
                    try:
                        payload = self._read_json()
                        table_type = str(payload.get('table_type') or '').strip()
                        result = server.export_table(table_type)
                        self._send_json(result)
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 导出统计表失败。')
                        self._send_json(
                            {
                                'error_code': 'export_table_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/uploads':
                    try:
                        payload = self._read_json()
                        result = server.create_upload(payload)
                        self._send_json(result, HTTPStatus.ACCEPTED)
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 创建上传任务失败。')
                        self._send_json(
                            {
                                'error_code': 'create_upload_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/channel-downloads':
                    try:
                        payload = self._read_json()
                        result = server.create_channel_download(payload)
                        self._send_json(result, HTTPStatus.ACCEPTED)
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 创建频道下载失败。')
                        self._send_json(
                            {
                                'error_code': 'create_channel_download_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/media/cleanup':
                    try:
                        payload = self._read_json()
                        self._send_json(server.cleanup_media_files(payload))
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 媒体清理失败。')
                        self._send_json(
                            {
                                'error_code': 'media_cleanup_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/archive/author-scan':
                    try:
                        payload = self._read_json()
                        self._send_json(server.scan_archive_author_reorganize(payload))
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 作者归档扫描失败。')
                        self._send_json(
                            {
                                'error_code': 'archive_author_scan_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path == '/api/archive/author-reorganize':
                    try:
                        payload = self._read_json()
                        self._send_json(server.execute_archive_author_reorganize(payload))
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 作者归档整理失败。')
                        self._send_json(
                            {
                                'error_code': 'archive_author_reorganize_failed',
                                'error': str(e)
                            },
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                if parsed.path != '/api/tasks':
                    self._send_error('not_found', 'Not found.', HTTPStatus.NOT_FOUND)
                    return
                try:
                    payload = self._read_json()
                    self._send_json(server.create_task(payload), HTTPStatus.CREATED)
                except WebUiApiError as e:
                    self._send_error(e.error_code, e.message, e.status)
                except Exception as e:
                    server.diagnostic.exception('[WebUI] 创建任务失败。')
                    self._send_json(
                        {
                            'error_code': 'create_task_failed',
                            'error': str(e)
                        },
                        HTTPStatus.BAD_REQUEST
                    )

            def do_PATCH(self):
                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                parsed = urlparse(self.path)
                if parsed.path != '/api/settings':
                    self._send_error('not_found', 'Not found.', HTTPStatus.NOT_FOUND)
                    return
                try:
                    payload = self._read_json()
                    settings = server.update_settings(payload)
                    sanitized = sanitize_settings(settings)
                    schema = server.settings_schema()
                    self._send_json({
                        'settings': sanitized,
                        'schema': schema,
                        'settings_model': WebUiViewModel.settings_model(sanitized, schema)
                    })
                except Exception as e:
                    server.diagnostic.exception('[WebUI] 更新设置失败。')
                    self._send_json(
                        {
                            'error_code': 'update_settings_failed',
                            'error': str(e)
                        },
                        HTTPStatus.BAD_REQUEST
                    )

            def do_PUT(self):
                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                parsed = urlparse(self.path)
                if parsed.path.startswith('/api/watches/'):
                    watch_id = unquote(parsed.path[len('/api/watches/'):])
                    if not watch_id:
                        self._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        payload = self._read_json()
                        result = server.update_watch(watch_id, payload)
                        self._send_json(result)
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except ValueError as e:
                        self._send_json(
                            {'error_code': 'update_watch_failed', 'error': str(e)},
                            HTTPStatus.BAD_REQUEST
                        )
                    except Exception as e:
                        server.diagnostic.exception('[WebUI] 更新实时监听失败。')
                        self._send_json(
                            {'error_code': 'update_watch_failed', 'error': str(e)},
                            HTTPStatus.BAD_REQUEST
                        )
                    return
                self._send_error('not_found', 'Not found.', HTTPStatus.NOT_FOUND)

            def do_DELETE(self):
                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                parsed = urlparse(self.path)
                if parsed.path == '/api/download-records':
                    cleared_count = server.store.clear_download_success_records()
                    self._send_json({'cleared': True, 'count': cleared_count})
                    return
                if parsed.path.startswith('/api/watches/'):
                    watch_id = unquote(parsed.path[len('/api/watches/'):])
                    if not watch_id:
                        self._send_error('invalid_watch_id', 'Invalid watch id.', HTTPStatus.BAD_REQUEST)
                        return
                    deleted = server.delete_watch(watch_id)
                    if not deleted:
                        self._send_error('watch_not_found', 'Watch not found.', HTTPStatus.NOT_FOUND)
                        return
                    self._send_json({'deleted': True, 'watch_id': watch_id})
                    return
                if not parsed.path.startswith('/api/tasks/'):
                    self._send_error('not_found', 'Not found.', HTTPStatus.NOT_FOUND)
                    return
                task_id = self._task_id_from_path()
                if task_id is None:
                    return
                try:
                    deleted = server.delete_task(task_id)
                except Exception as e:
                    server.diagnostic.exception('[WebUI] 删除任务失败。')
                    self._send_json(
                        {
                            'error_code': 'delete_task_failed',
                            'error': str(e),
                            'detail': '删除失败',
                        },
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                if not deleted:
                    self._send_error(
                        'delete_task_failed',
                        'Task delete failed. Stop running transfers or retry after files are released.',
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                self._send_json({'deleted': True, 'task_id': task_id})

        self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        auth_status = 'enabled' if self.auth_enabled else 'disabled'
        self.diagnostic.info(f'WebUI started at {self.url}, auth={auth_status}')
        if open_browser:
            try:
                webbrowser.open(self.url)
            except Exception as e:
                self.diagnostic.warning(f'无法自动打开浏览器: {e}')

    def stop(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.thread = None

    def get_settings(self) -> dict:
        if self.settings_provider:
            return self.settings_provider()
        return load_runtime_settings()

    def create_task(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise WebUiApiError('invalid_payload', 'Invalid payload.', HTTPStatus.BAD_REQUEST)
        source_link = str(payload.get('source_link') or '').strip()
        target_link = str(payload.get('target_link') or 'https://t.me/pikpak_bot').strip()
        target_profile = str(payload.get('target_profile') or 'pikpak').strip()
        include_comment = bool(payload.get('include_comment'))
        resolve_deep_link = bool(payload.get('resolve_deep_link'))
        if not source_link:
            raise WebUiApiError('source_link_required', 'Source link is required.', HTTPStatus.BAD_REQUEST)
        if not target_link:
            raise WebUiApiError('target_link_required', 'Target link is required.', HTTPStatus.BAD_REQUEST)
        self._require_deep_link_whitelist_if_enabled(resolve_deep_link)
        start_id = normalize_optional_int(payload.get('start_id'))
        end_id = normalize_optional_int(payload.get('end_id'))
        if (start_id is None) != (end_id is None):
            raise WebUiApiError(
                'range_ids_required',
                'Start ID and End ID must be provided together.',
                HTTPStatus.BAD_REQUEST
            )
        source_is_message_link = is_message_link(source_link)
        if start_id is None and end_id is None and not source_is_message_link:
            start_id, end_id = self.detect_transfer_range(source_link)
        if start_id is not None and end_id is not None:
            if end_id < start_id:
                raise WebUiApiError(
                    'range_end_before_start',
                    'End ID must be greater than or equal to Start ID.',
                    HTTPStatus.BAD_REQUEST
                )
            if source_is_message_link:
                raise WebUiApiError(
                    'range_source_must_be_chat_link',
                    'Range transfer source must be a chat link, not a message link.',
                    HTTPStatus.BAD_REQUEST
                )
        from module.core.media_types import parse_media_types_payload
        media_types = parse_media_types_payload(payload.get('media_types'))
        task_id = self.store.create_task(
            source_link=source_link,
            target_link=target_link,
            target_profile=target_profile,
            start_id=start_id,
            end_id=end_id,
            include_comment=include_comment,
            resolve_deep_link=resolve_deep_link,
            media_types=media_types,
        )
        if self.task_submitter:
            self.task_submitter(task_id)
        return {'task_id': task_id}

    def detect_transfer_range(self, source_link: str) -> tuple[int, int]:
        detect = self._operation('detect_transfer_range')
        if not detect:
            raise WebUiApiError(
                'transfer_range_detection_unavailable',
                'Transfer range detection is unavailable.',
                HTTPStatus.BAD_REQUEST
            )
        try:
            detected = normalize_detected_transfer_range(detect(source_link))
        except WebUiApiError:
            raise
        except Exception as e:
            raise WebUiApiError(
                'transfer_range_detection_failed',
                str(e) or 'Transfer range detection failed.',
                HTTPStatus.BAD_REQUEST
            ) from e
        if detected is None:
            raise WebUiApiError(
                'transfer_range_empty',
                'No accessible messages were found for the source.',
                HTTPStatus.BAD_REQUEST
            )
        start_id, end_id = detected
        if start_id > end_id:
            raise WebUiApiError(
                'range_end_before_start',
                'End ID must be greater than or equal to Start ID.',
                HTTPStatus.BAD_REQUEST
            )
        return start_id, end_id

    def list_watches(self, tz_offset_minutes: int | None = None) -> list:
        list_watches = self._operation('list_watches')
        if list_watches:
            return list_watches(tz_offset_minutes=tz_offset_minutes)
        return []

    def create_watch(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise WebUiApiError('invalid_payload', 'Invalid payload.', HTTPStatus.BAD_REQUEST)
        watch_type = str(payload.get('type') or '').strip()
        if watch_type not in ('download', 'forward'):
            raise WebUiApiError('invalid_watch_type', 'Watch type must be download or forward.', HTTPStatus.BAD_REQUEST)
        if watch_type == 'download':
            source_links = payload.get('source_links')
            if isinstance(source_links, str):
                source_links = [source_links]
            source_links = [str(link).strip() for link in (source_links or []) if str(link).strip()]
            if not source_links:
                raise WebUiApiError('watch_source_required', 'At least one source link is required.', HTTPStatus.BAD_REQUEST)
            from module.core.media_types import parse_media_types_payload
            for link in source_links:
                if not link.startswith('https://t.me/'):
                    raise WebUiApiError('invalid_watch_source', 'Watch source link must start with https://t.me/.', HTTPStatus.BAD_REQUEST)
            payload = {
                **payload,
                'source_links': source_links,
                'media_types': parse_media_types_payload(payload.get('media_types')),
            }
        else:
            from module.core.media_types import parse_media_types_payload
            source_link = str(payload.get('source_link') or '').strip()
            target_link = str(payload.get('target_link') or '').strip()
            include_comment = bool(payload.get('include_comment'))
            resolve_deep_link = bool(payload.get('resolve_deep_link'))
            if not source_link:
                raise WebUiApiError('watch_source_required', 'Source link is required.', HTTPStatus.BAD_REQUEST)
            if not target_link:
                raise WebUiApiError('watch_target_required', 'Target link is required.', HTTPStatus.BAD_REQUEST)
            if not source_link.startswith('https://t.me/'):
                raise WebUiApiError('invalid_watch_source', 'Watch source link must start with https://t.me/.', HTTPStatus.BAD_REQUEST)
            if not target_link.startswith('https://t.me/'):
                raise WebUiApiError('invalid_watch_target', 'Watch target link must start with https://t.me/.', HTTPStatus.BAD_REQUEST)
            self._require_deep_link_whitelist_if_enabled(resolve_deep_link)
            payload = {
                **payload,
                'source_link': source_link,
                'target_link': target_link,
                'include_comment': include_comment,
                'resolve_deep_link': resolve_deep_link,
                'media_types': parse_media_types_payload(payload.get('media_types')),
            }
        create_watch = self._operation('create_watch')
        if create_watch:
            try:
                return create_watch(payload)
            except ValueError as e:
                if str(e) == 'watch_source_conflict':
                    raise WebUiApiError(
                        'watch_source_conflict',
                        'The same source cannot be watched by download and forward at the same time.',
                        HTTPStatus.CONFLICT
                    )
                if str(e) == 'watch_already_exists':
                    raise WebUiApiError(
                        'watch_already_exists',
                        'Watch already exists.',
                        HTTPStatus.CONFLICT
                    )
                raise
        raise WebUiApiError('watch_operations_unavailable', 'Watch operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def update_watch(self, watch_id: str, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise WebUiApiError('invalid_payload', 'Invalid payload.', HTTPStatus.BAD_REQUEST)
        from module.core.media_types import parse_media_types_payload
        resolve_deep_link = bool(payload.get('resolve_deep_link'))
        self._require_deep_link_whitelist_if_enabled(resolve_deep_link)
        payload = {
            **payload,
            'resolve_deep_link': resolve_deep_link,
            'media_types': parse_media_types_payload(payload.get('media_types')),
        }
        update_watch = self._operation('update_watch')
        if update_watch:
            try:
                return update_watch(watch_id, payload)
            except ValueError as e:
                raise WebUiApiError(
                    'update_watch_failed',
                    str(e),
                    HTTPStatus.BAD_REQUEST
                )
        raise WebUiApiError('watch_operations_unavailable', 'Watch operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def delete_watch(self, watch_id: str) -> bool:
        delete_watch = self._operation('delete_watch')
        if delete_watch:
            return bool(delete_watch(watch_id))
        return False

    def export_forward_watches(self) -> dict:
        export_forward_watches = self._operation('export_forward_watches')
        if export_forward_watches:
            return export_forward_watches()
        raise WebUiApiError(
            'watch_operations_unavailable',
            'Watch operations are unavailable.',
            HTTPStatus.SERVICE_UNAVAILABLE
        )

    def import_forward_watches(self, payload) -> dict:
        from module.transfer.forward_watch_backup import (
            normalize_forward_watch_entry,
            parse_forward_watch_import_payload,
        )

        entries, parse_errors = parse_forward_watch_import_payload(payload)
        fatal_codes = {
            'invalid_payload',
            'invalid_kind',
            'unsupported_version',
            'missing_watches',
            'invalid_watches',
        }
        for code in parse_errors:
            if code in fatal_codes:
                raise WebUiApiError(
                    code,
                    'Invalid forward watch backup file.',
                    HTTPStatus.BAD_REQUEST
                )

        result = {
            'created': 0,
            'skipped': 0,
            'failed': 0,
            'errors': [],
            'watches': [],
        }
        for index, raw in enumerate(entries):
            entry = normalize_forward_watch_entry(raw)
            if not entry:
                result['failed'] += 1
                result['errors'].append({'index': index, 'code': 'invalid_entry'})
                continue
            try:
                created = self.create_watch({'type': 'forward', **entry})
            except WebUiApiError as exc:
                if exc.error_code == 'watch_already_exists':
                    result['skipped'] += 1
                    continue
                result['failed'] += 1
                error = {
                    'index': index,
                    'code': exc.error_code,
                    'message': exc.message,
                }
                if exc.error_code == 'watch_source_conflict':
                    error['source_link'] = entry['source_link']
                result['errors'].append(error)
                continue
            result['created'] += 1
            result['watches'].extend(created.get('watches') or [])
        return result

    def list_deferred_discussion_captures(self, watch_id: str) -> Optional[dict]:
        op = self._operation('list_deferred_discussion_captures')
        if not op:
            return {'captures': [], 'total': 0}
        return op(watch_id)

    def cancel_deferred_discussion_capture(self, watch_id: str, capture_id: int) -> bool:
        op = self._operation('cancel_deferred_discussion_capture')
        if not op:
            return False
        return bool(op(watch_id, capture_id))

    def run_deferred_discussion_capture_now(self, watch_id: str, capture_id: int) -> bool:
        op = self._operation('run_deferred_discussion_capture_now')
        if not op:
            return False
        return bool(op(watch_id, capture_id))

    def retry_deferred_discussion_capture(self, watch_id: str, capture_id: int) -> bool:
        op = self._operation('retry_deferred_discussion_capture')
        if not op:
            return False
        return bool(op(watch_id, capture_id))

    def list_watch_events(
            self,
            watch_id: str,
            limit: int = 50,
            offset: int = 0,
            today_only: bool = False,
            tz_offset_minutes: int | None = None,
            status: str | None = None
    ):
        list_watch_events = self._operation('list_watch_events')
        if list_watch_events:
            return list_watch_events(
                watch_id,
                limit=limit,
                offset=offset,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes,
                status=status
            )
        return None

    def delete_task(self, task_id: int) -> bool:
        delete_web_task = self._operation('delete_web_task')
        if delete_web_task:
            return bool(delete_web_task(task_id))
        return self.store.delete_task(task_id)

    @staticmethod
    def parse_task_action_path(path: str):
        prefix = '/api/tasks/'
        if not path.startswith(prefix):
            return None
        parts = [part for part in path[len(prefix):].split('/') if part]
        if len(parts) != 2 or not parts[0].isdigit():
            return None
        action = parts[1]
        if action not in ('pause', 'resume', 'retry-failed'):
            return None
        return int(parts[0]), action

    def apply_task_action(self, task_id: int, action: str) -> dict:
        if not self.store.get_task(task_id):
            raise WebUiApiError('task_not_found', 'Task not found.', HTTPStatus.NOT_FOUND)
        if action == 'retry-failed':
            retry_failed_web_task = self._operation('retry_failed_web_task')
            if retry_failed_web_task:
                reset_items = int(retry_failed_web_task(task_id))
            else:
                reset_items = self.store.retry_failed_items(task_id)
                if reset_items and self.task_submitter:
                    self.task_submitter(task_id)
            return {'task_id': task_id, 'action': action, 'reset_items': reset_items}
        if action == 'pause':
            pause_web_task = self._operation('pause_web_task')
            if pause_web_task:
                ok = bool(pause_web_task(task_id))
            else:
                self.store.update_task(task_id, status='paused')
                ok = True
            if not ok:
                raise WebUiApiError('task_action_failed', 'Task action failed.', HTTPStatus.BAD_REQUEST)
            return {'task_id': task_id, 'action': action}
        if action == 'resume':
            resume_web_task = self._operation('resume_web_task')
            if resume_web_task:
                ok = bool(resume_web_task(task_id))
            else:
                self.store.update_task(task_id, status='pending')
                ok = True
                if self.task_submitter:
                    self.task_submitter(task_id)
            if not ok:
                raise WebUiApiError('task_action_failed', 'Task action failed.', HTTPStatus.BAD_REQUEST)
            return {'task_id': task_id, 'action': action}
        raise WebUiApiError('invalid_task_action', 'Invalid task action.', HTTPStatus.BAD_REQUEST)

    def statistics(self, tz_offset_minutes: int | None = None) -> dict:
        statistics = self._operation('statistics')
        if statistics:
            try:
                return statistics(tz_offset_minutes=tz_offset_minutes)
            except TypeError:
                return statistics()
        from module.statistics_payload import build_statistics_payload

        store = getattr(self, 'transfer_store', None)
        if store is not None:
            from module.statistics_payload import DEFAULT_STATISTICS_WINDOW_DAYS

            rows = store.aggregate_channel_download_stats(
                days=DEFAULT_STATISTICS_WINDOW_DAYS,
                tz_offset_minutes=tz_offset_minutes,
            )
            return build_statistics_payload(
                rows,
                window_days=DEFAULT_STATISTICS_WINDOW_DAYS,
            )
        return build_statistics_payload([])

    def list_operations(self, limit: int = 50) -> list:
        list_operations = self._operation('list_operations')
        if list_operations:
            return list_operations(limit=limit)
        return []

    def export_table(self, table_type: str) -> dict:
        if table_type not in ('channel', 'link', 'count', 'upload'):
            raise WebUiApiError(
                'invalid_table_type',
                'Table type must be channel, link, count, or upload.',
                HTTPStatus.BAD_REQUEST,
            )
        export_table = self._operation('export_table')
        if export_table:
            return export_table(table_type)
        raise WebUiApiError('table_operations_unavailable', 'Table operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def create_upload(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise WebUiApiError('invalid_payload', 'Invalid payload.', HTTPStatus.BAD_REQUEST)
        path = str(payload.get('path') or '').strip()
        target_link = str(payload.get('target_link') or '').strip()
        recursive = bool(payload.get('recursive'))
        if not path:
            raise WebUiApiError('upload_path_required', 'Upload path is required.', HTTPStatus.BAD_REQUEST)
        if not target_link:
            raise WebUiApiError('upload_target_required', 'Target link is required.', HTTPStatus.BAD_REQUEST)
        if not target_link.startswith('https://t.me/') and target_link not in ('me', 'self'):
            raise WebUiApiError('invalid_upload_target', 'Upload target must be a Telegram link, me, or self.', HTTPStatus.BAD_REQUEST)
        normalized_path = os.path.abspath(os.path.expanduser(path))
        if not os.path.exists(normalized_path):
            raise WebUiApiError('upload_path_not_found', 'Upload path does not exist on the server.', HTTPStatus.BAD_REQUEST)
        if recursive and not os.path.isdir(normalized_path):
            raise WebUiApiError('upload_recursive_requires_directory', 'Recursive upload requires a directory.', HTTPStatus.BAD_REQUEST)
        payload = {**payload, 'path': normalized_path, 'target_link': target_link, 'recursive': recursive}
        create_upload = self._operation('create_upload')
        if create_upload:
            return create_upload(payload)
        raise WebUiApiError('upload_operations_unavailable', 'Upload operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def create_channel_download(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise WebUiApiError('invalid_payload', 'Invalid payload.', HTTPStatus.BAD_REQUEST)
        chat_link = str(payload.get('chat_link') or '').strip()
        if not chat_link:
            raise WebUiApiError('channel_link_required', 'Channel link is required.', HTTPStatus.BAD_REQUEST)
        if not chat_link.startswith('https://t.me/'):
            raise WebUiApiError('invalid_channel_link', 'Channel link must start with https://t.me/.', HTTPStatus.BAD_REQUEST)
        allowed_types = set(self.settings_schema()['download_type'])
        download_type = payload.get('download_type') or sorted(allowed_types)
        if isinstance(download_type, str):
            download_type = [download_type]
        download_type = [str(item).strip() for item in download_type if str(item).strip()]
        if not download_type:
            raise WebUiApiError('channel_download_type_required', 'At least one download type is required.', HTTPStatus.BAD_REQUEST)
        invalid_types = [item for item in download_type if item not in allowed_types]
        if invalid_types:
            raise WebUiApiError('invalid_channel_download_type', 'Invalid channel download type.', HTTPStatus.BAD_REQUEST)
        keywords = payload.get('keywords') or []
        if isinstance(keywords, str):
            keywords = [part.strip() for part in keywords.split(',') if part.strip()]
        else:
            keywords = [str(part).strip() for part in keywords if str(part).strip()]
        normalized = {
            **payload,
            'chat_link': chat_link,
            'download_type': download_type,
            'keywords': keywords,
            'include_comment': bool(payload.get('include_comment')),
            'date_range': normalize_date_range(payload.get('date_range'))
        }
        create_channel_download = self._operation('create_channel_download')
        if create_channel_download:
            return create_channel_download(normalized)
        raise WebUiApiError('channel_download_operations_unavailable', 'Channel download operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def scan_media_for_cleanup(
            self,
            task_id: int = None,
            items_limit: int = None,
            items_offset: int = 0,
            orphans_limit: int = None,
            orphans_offset: int = 0,
    ) -> dict:
        scan_media_for_cleanup = self._operation('scan_media_for_cleanup')
        if scan_media_for_cleanup:
            return scan_media_for_cleanup(
                task_id=task_id,
                items_limit=items_limit,
                items_offset=items_offset,
                orphans_limit=orphans_limit,
                orphans_offset=orphans_offset,
            )
        raise WebUiApiError('media_operations_unavailable', 'Media operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def cleanup_media_files(self, payload: dict) -> dict:
        cleanup_media_files = self._operation('cleanup_media_files')
        if cleanup_media_files:
            return cleanup_media_files(payload)
        raise WebUiApiError('media_operations_unavailable', 'Media operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def list_archive_author_channels(self) -> dict:
        op = self._operation('list_archive_author_channels')
        if op:
            return op()
        raise WebUiApiError(
            'archive_author_unavailable',
            'Archive author tools are unavailable.',
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def scan_archive_author_reorganize(self, payload: dict) -> dict:
        op = self._operation('scan_archive_author_reorganize')
        if op:
            return op(payload)
        raise WebUiApiError(
            'archive_author_unavailable',
            'Archive author tools are unavailable.',
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def execute_archive_author_reorganize(self, payload: dict) -> dict:
        op = self._operation('execute_archive_author_reorganize')
        if op:
            return op(payload)
        raise WebUiApiError(
            'archive_author_unavailable',
            'Archive author tools are unavailable.',
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def get_archive_author_job(self, job_id: str) -> dict:
        op = self._operation('get_archive_author_job')
        if op:
            return op(job_id)
        raise WebUiApiError(
            'archive_author_unavailable',
            'Archive author tools are unavailable.',
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def get_active_archive_author_job(self, channel_folder: str | None = None) -> dict:
        op = self._operation('get_active_archive_author_job')
        if op:
            return op(channel_folder)
        raise WebUiApiError(
            'archive_author_unavailable',
            'Archive author tools are unavailable.',
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def list_cleanup_logs(self) -> list:
        list_cleanup_logs = self._operation('list_cleanup_logs')
        if list_cleanup_logs:
            return list_cleanup_logs()
        return []

    def list_system_logs(
            self,
            limit: int = 50,
            offset: int = 0,
            category: str | None = None,
            level: str | None = None,
            trace_id: str | None = None,
            watch_id: str | None = None,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ) -> dict:
        list_system_logs = self._operation('list_system_logs')
        if list_system_logs:
            return list_system_logs(
                limit=limit,
                offset=offset,
                category=category,
                level=level,
                trace_id=trace_id,
                watch_id=watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes
            )
        if self.store and hasattr(self.store, 'list_system_logs'):
            logs, total = self.store.list_system_logs(
                limit=limit,
                offset=offset,
                category=category,
                level=level,
                trace_id=trace_id,
                watch_id=watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes
            )
            return {
                'logs': logs,
                'total': total,
                'limit': limit,
                'offset': offset,
                'retention_days': self.store.SYSTEM_LOGS_RETENTION_DAYS
            }
        return {'logs': [], 'total': 0, 'limit': limit, 'offset': offset}

    def export_system_logs(
            self,
            category: str | None = None,
            level: str | None = None,
            trace_id: str | None = None,
            watch_id: str | None = None,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ) -> str:
        export_system_logs = self._operation('export_system_logs')
        if export_system_logs:
            return export_system_logs(
                category=category,
                level=level,
                trace_id=trace_id,
                watch_id=watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes
            )
        from module.persistence.system_log import build_system_logs_export_text
        if self.store and hasattr(self.store, 'list_system_logs'):
            return build_system_logs_export_text(
                self.store,
                category=category,
                level=level,
                trace_id=trace_id,
                watch_id=watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes
            )
        return ''

    def get_sanitized_settings(self) -> dict:
        return sanitize_settings(self.get_settings())

    def update_settings(self, payload: dict) -> dict:
        if self.settings_updater:
            return self.settings_updater(payload)
        return save_runtime_settings(payload)

    @staticmethod
    def settings_schema() -> dict:
        return {
            'download_type': [
                'video', 'photo', 'audio', 'voice', 'animation', 'document', 'video_note'
            ],
            'forward_type': [
                'video', 'photo', 'audio', 'document', 'voice', 'text', 'animation', 'video_note'
            ],
            'message_filter': {
                'media_types': [
                    'video', 'photo', 'audio', 'document', 'voice', 'text', 'animation', 'video_note'
                ],
                'date_range': {'enabled': False},
                'keywords': {'enabled': False}
            },
            'upload_pending_limit': {'min': 1, 'max': 5},
            'comment_delay_minutes': {'min': 0, 'max': 1440},
            'deep_link': {
                'timeout_seconds': {'min': 1, 'max': 600},
                'min_interval_seconds': {'min': 0, 'max': 600},
            },
            'target_profiles': {
                'pikpak': {
                    'max_file_size': {'min': 1}
                }
            },
            'sensitive_keys': sorted(SENSITIVE_SETTING_KEYS)
        }


def sanitize_settings(value):
    if isinstance(value, dict):
        result = {}
        for key, nested in value.items():
            if key in SENSITIVE_SETTING_KEYS:
                result[key] = {
                    'configured': bool(nested),
                    'value': ''
                }
            else:
                result[key] = sanitize_settings(nested)
        return result
    if isinstance(value, list):
        return [sanitize_settings(item) for item in value]
    return value


def parse_optional_timestamp(value):
    if value in (None, ''):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        pass
    try:
        return datetime.datetime.fromisoformat(text).timestamp()
    except ValueError:
        raise WebUiApiError('invalid_date_range', 'Date range values must be timestamps or ISO datetimes.', HTTPStatus.BAD_REQUEST)


def normalize_date_range(value) -> dict:
    if not isinstance(value, dict):
        return {'start_date': None, 'end_date': None}
    start_date = parse_optional_timestamp(value.get('start_date'))
    end_date = parse_optional_timestamp(value.get('end_date'))
    if start_date is not None and end_date is not None and end_date < start_date:
        raise WebUiApiError('date_range_end_before_start', 'Date range end must be greater than or equal to start.', HTTPStatus.BAD_REQUEST)
    return {
        'start_date': start_date,
        'end_date': end_date
    }


def load_runtime_settings() -> dict:
    from module.config import GlobalConfig, UserConfig

    user = UserConfig()
    global_config = GlobalConfig()
    return {
        'user': {
            'config_path': user.config_path,
            'api_id': user.config.get('api_id'),
            'api_hash': user.config.get('api_hash'),
            'bot_token': user.config.get('bot_token'),
            'session_directory': user.config.get('session_directory'),
            'save_directory': user.config.get('save_directory'),
            'temp_directory': user.config.get('temp_directory'),
            'max_tasks': user.config.get('max_tasks'),
            'max_retries': user.config.get('max_retries'),
            'download_type': user.config.get('download_type'),
            'is_shutdown': user.config.get('is_shutdown'),
            'proxy': user.config.get('proxy')
        },
        'global': global_config.config
    }


def save_runtime_settings(payload: dict) -> dict:
    from module.config import GlobalConfig, UserConfig

    user = UserConfig()
    global_config = GlobalConfig()
    user_config = merge_allowed_settings(
        target=deepcopy(user.config),
        patch=payload.get('user', {}) if isinstance(payload, dict) else {},
        allowed={
            'api_id', 'api_hash', 'bot_token', 'session_directory', 'save_directory',
            'temp_directory', 'max_tasks', 'max_retries', 'download_type', 'is_shutdown',
            'proxy'
        },
        gc=global_config
    )
    user_config = UserConfig.normalize_runtime_numbers(user_config)
    global_settings = merge_allowed_settings(
        target=deepcopy(global_config.config),
        patch=payload.get('global', {}) if isinstance(payload, dict) else {},
        allowed={'notice', 'export_table', 'upload', 'forward_type', 'target_profiles', 'message_filter', 'live_watch', 'deep_link'},
        gc=global_config
    )
    user.save_config(user_config)
    global_config.save_config(global_settings)
    return load_runtime_settings()


def merge_allowed_settings(target: dict, patch: dict, allowed: set, gc=None) -> dict:
    if not isinstance(patch, dict):
        return target
    for key, value in patch.items():
        if key not in allowed:
            continue
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key] = merge_allowed_settings(
                target=deepcopy(target.get(key, {})),
                patch=value,
                allowed=set(target.get(key, {}).keys()) | set(value.keys()),
                gc=gc
            )
        elif key in SENSITIVE_SETTING_KEYS and value in (None, ''):
            continue
        else:
            target[key] = _coerce_type(target.get(key), value)
    return target


def _coerce_type(target_val, new_val):
    """将 new_val 转换为 target_val 的类型，防止 Web UI 表单字符串污染配置类型。"""
    if target_val is None or new_val is None:
        return new_val
    target_type = type(target_val)
    if target_type is bool:
        if isinstance(new_val, str):
            return new_val.lower() in ('true', '1', 'yes', 'on')
        return bool(new_val)
    if target_type is list and isinstance(new_val, str):
        # textarea / comma fields: avoid list("a\\nb") character-splitting
        return [
            part.strip()
            for part in new_val.replace(',', '\n').split('\n')
            if part.strip()
        ]
    try:
        return target_type(new_val)
    except (TypeError, ValueError):
        return new_val


def get_web_port_from_env(default: int = 0) -> int:
    try:
        return int(os.environ.get(ENVIRON.TRMD_WEB_PORT, default))
    except (TypeError, ValueError):
        return default


def get_web_host_from_env(default: str = '127.0.0.1') -> str:
    return os.environ.get(ENVIRON.TRMD_WEB_HOST, default)


def get_web_username_from_env() -> Optional[str]:
    return os.environ.get(ENVIRON.TRMD_WEB_USERNAME)


def get_web_password_from_env() -> Optional[str]:
    return os.environ.get(ENVIRON.TRMD_WEB_PASSWORD)
