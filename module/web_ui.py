# coding=UTF-8
import base64
import datetime
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
from module.adapters.webui.assets import WEB_UI_HTML, WEB_UI_MOBILE_HTML


LOGIN_PAGE_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TRMD · 登录</title>
<style>
  :root {
    --bg: #f7f8fa;
    --surface: #ffffff;
    --text: #17201b;
    --muted: #5b6670;
    --line: #d8dee4;
    --accent: #0f8f72;
    --accent-strong: #0a6f5a;
    --danger: #b42318;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 14px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    min-height: 100svh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }
  .login-page {
    width: 100%;
    max-width: 400px;
    display: grid;
    gap: 28px;
  }
  .login-brand {
    text-align: center;
    animation: loginFadeIn .5s ease both;
  }
  .login-brand__mark {
    width: 48px; height: 48px;
    border-radius: 12px;
    background: var(--accent);
    display: inline-grid;
    place-items: center;
    color: #fff;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 14px;
  }
  .login-brand h1 {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -.02em;
    color: var(--text);
  }
  .login-brand p {
    font-size: 13px;
    color: var(--muted);
    margin-top: 4px;
  }
  .login-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 18px 42px rgba(31, 48, 38, .08);
    animation: loginFadeIn .5s ease .1s both;
  }
  .login-card h2 {
    font-size: 18px;
    font-weight: 650;
    margin-bottom: 24px;
    color: var(--text);
  }
  .login-error {
    font-size: 13px;
    color: var(--danger);
    background: #fff4f2;
    border: 1px solid #f3b5ad;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 16px;
    display: none;
  }
  .login-error.visible { display: block; animation: loginShake .4s ease; }
  .login-field {
    margin-bottom: 18px;
  }
  .login-field label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    margin-bottom: 6px;
  }
  .login-field input {
    width: 100%;
    height: 42px;
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 0 12px;
    font-size: 14px;
    font-family: inherit;
    background: var(--surface);
    color: var(--text);
    transition: border-color .18s ease, box-shadow .18s ease;
    outline: none;
  }
  .login-field input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(15, 143, 114, .15);
  }
  .login-field input::placeholder {
    color: #9ca3af;
  }
  .login-options {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
  }
  .login-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 13px;
    color: var(--muted);
    user-select: none;
  }
  .login-checkbox input[type="checkbox"] {
    width: 16px; height: 16px;
    accent-color: var(--accent);
    cursor: pointer;
  }
  .login-submit {
    width: 100%;
    height: 44px;
    border: 0;
    border-radius: 6px;
    background: var(--accent);
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: background .18s ease, opacity .18s ease;
    font-family: inherit;
  }
  .login-submit:hover { background: var(--accent-strong); }
  .login-submit:disabled {
    cursor: not-allowed;
    opacity: .72;
  }
  .spinner {
    width: 18px; height: 18px;
    border: 2px solid rgba(255,255,255,.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: loginSpin .6s linear infinite;
    flex-shrink: 0;
  }
  @keyframes loginSpin { to { transform: rotate(360deg); } }
  @keyframes loginFadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes loginShake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-6px); }
    40%, 80% { transform: translateX(6px); }
  }
  @media (max-width: 480px) {
    body { padding: 20px; align-items: flex-start; padding-top: 12vh; }
    .login-card { padding: 24px; }
    .login-brand h1 { font-size: 22px; }
    .login-brand p { font-size: 12px; }
  }
</style>
</head>
<body>
<div class="login-page">
  <div class="login-brand">
    <div class="login-brand__mark" aria-hidden="true">T</div>
    <h1>TRMD</h1>
    <p>Telegram Restricted Media Downloader</p>
  </div>
  <div class="login-card">
    <h2>登录控制台</h2>
    <div class="login-error" id="login-error" role="alert"></div>
    <form id="login-form" method="post" autocomplete="on" novalidate>
      <div class="login-field">
        <label for="username">用户名</label>
        <input id="username" type="text" name="username" autocomplete="username" placeholder="请输入用户名" required autofocus>
      </div>
      <div class="login-field">
        <label for="password">密码</label>
        <input id="password" type="password" name="password" autocomplete="current-password" placeholder="请输入密码" required>
      </div>
      <div class="login-options">
        <label class="login-checkbox">
          <input type="checkbox" id="remember-me" name="remember_me">
          <span>保持登录 30 天</span>
        </label>
      </div>
      <button type="submit" id="login-submit" class="login-submit">
        <span id="login-btn-text">登 录</span>
      </button>
    </form>
  </div>
</div>
<script>
(function() {
  var form = document.getElementById('login-form');
  var errorEl = document.getElementById('login-error');
  var submitBtn = document.getElementById('login-submit');
  var btnText = document.getElementById('login-btn-text');

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.add('visible');
  }

  function hideError() {
    errorEl.textContent = '';
    errorEl.classList.remove('visible');
  }

  function setLoading(loading) {
    submitBtn.disabled = loading;
    if (loading) {
      btnText.innerHTML = '<span class="spinner"></span>登录中...';
    } else {
      btnText.textContent = '登 录';
    }
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    hideError();
    var username = document.getElementById('username').value.trim();
    var password = document.getElementById('password').value;
    if (!username) { showError('请输入用户名'); document.getElementById('username').focus(); return; }
    if (!password) { showError('请输入密码'); document.getElementById('password').focus(); return; }
    setLoading(true);
    try {
      var resp = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username,
          password: password,
          remember_me: document.getElementById('remember-me').checked
        })
      });
      var data = await resp.json();
      if (resp.ok && data.success) {
        window.location.href = '/';
      } else {
        showError(data.error || '登录失败，请检查用户名和密码。');
        setLoading(false);
        document.getElementById('password').value = '';
        document.getElementById('password').focus();
      }
    } catch (err) {
      showError('网络错误，请检查连接后重试。');
      setLoading(false);
    }
  });
})();
</script>
</body>
</html>'''


SENSITIVE_SETTING_KEYS = {
    'api_hash',
    'bot_token',
    'password',
    'username'
}


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
            diagnostic: Optional[IDiagnosticPort] = None
    ):
        self.store = store
        self.task_submitter = task_submitter
        self.settings_provider = settings_provider
        self.settings_updater = settings_updater
        self.operations = operations
        self.host = host
        self.port = self.resolve_port(port)
        self.username = (username or '').strip()
        self.password = password or ''
        self.diagnostic = diagnostic or default_diagnostic
        self.httpd: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.auth_provider: Optional[AuthProvider] = None
        self.validate_auth_config()

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
    SESSION_TOKEN_BYTES = 32

    def validate_auth_config(self) -> None:
        if bool(self.username) != bool(self.password):
            raise ValueError('TRMD_WEB_USERNAME 和 TRMD_WEB_PASSWORD 必须同时设置。')
        if self.requires_auth and not self.auth_enabled:
            raise ValueError('WebUI 对外监听时必须设置 TRMD_WEB_USERNAME 和 TRMD_WEB_PASSWORD。')

    def _generate_session_token(self) -> str:
        return secrets.token_hex(self.SESSION_TOKEN_BYTES)

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

    def _init_sessions(self) -> None:
        if not hasattr(self, '_sessions'):
            self._sessions: dict[str, float] = {}

    def _store_session(self, token: str) -> None:
        self._init_sessions()
        self._sessions[token] = time.time() + self.SESSION_MAX_AGE
        self._prune_expired_sessions()

    def validate_session_token(self, token: str) -> bool:
        self._init_sessions()
        expiry = self._sessions.get(token)
        if expiry is None:
            return False
        if time.time() > expiry:
            del self._sessions[token]
            return False
        return True

    def _prune_expired_sessions(self) -> None:
        self._init_sessions()
        now = time.time()
        expired = [t for t, exp in self._sessions.items() if now > exp]
        for t in expired:
            del self._sessions[t]

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

    def is_authorized(self, authorization: Optional[str]) -> bool:
        if not self.auth_enabled:
            return True
        if not authorization or not authorization.startswith('Basic '):
            return False
        try:
            raw = base64.b64decode(authorization[6:].strip()).decode('utf-8')
        except Exception:
            return False
        username, separator, password = raw.partition(':')
        if not separator:
            return False
        return (
            hmac.compare_digest(username, self.username)
            and hmac.compare_digest(password, self.password)
        )

    def validate_credentials(self, username: str, password: str) -> bool:
        if not self.auth_enabled:
            return True
        auth_header = 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()
        return self.is_authorized(auth_header)

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
                self.send_header('www-authenticate', 'Basic realm="TRMD WebUI"')
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
                """Check and apply auth silently. Returns True if authorized (may set _pending_cookie)."""
                if not server.auth_enabled:
                    return True
                session_token = server._get_request_cookie(self, server.SESSION_COOKIE_NAME)
                if session_token and server.validate_session_token(session_token):
                    self._pending_cookie = server._create_session_cookie(session_token)
                    return True
                if server.is_authorized(self.headers.get('authorization')):
                    token = server._generate_session_token()
                    server._store_session(token)
                    self._pending_cookie = server._create_session_cookie(token)
                    return True
                return False

            def _check_auth(self):
                path = urlparse(self.path).path
                if path in ('/api/auth/status', '/api/auth/submit', '/api/auth/login', '/api/auth/logout'):
                    return True
                if self._try_authorize():
                    return True
                self._send_auth_required()
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

            def _send_json(self, payload, status=HTTPStatus.OK):
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                self.send_response(status)
                self._write_pending_cookie()
                self.send_header('content-type', 'application/json; charset=utf-8')
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
                server._store_session(token)
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
                session_token = server._get_request_cookie(self, server.SESSION_COOKIE_NAME)
                if session_token:
                    server._init_sessions()
                    server._sessions.pop(session_token, None)
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

                # Page requests: show login page when unauthorized
                if parsed.path in ('/', '/index.html'):
                    if not self._check_page_auth():
                        self._send_login_page()
                        return
                    self._send_html()
                    return

                # API requests require auth
                if not self._check_auth():
                    return
                if parsed.path == '/api/auth/status':
                    if server.auth_provider:
                        self._send_json(server.auth_provider.get_state())
                    else:
                        self._send_json({'step': 'none', 'error': None, 'user': None})
                    return
                if parsed.path == '/api/tasks':
                    self._send_json({'tasks': server.store.list_tasks()})
                    return
                if parsed.path == '/api/settings':
                    self._send_json({
                        'settings': server.get_sanitized_settings(),
                        'schema': server.settings_schema()
                    })
                    return
                if parsed.path == '/api/download-records':
                    self._send_json({'records': server.store.list_download_success_records()})
                    return
                if parsed.path == '/api/statistics':
                    self._send_json(server.statistics())
                    return
                if parsed.path == '/api/watches':
                    self._send_json({'watches': server.list_watches()})
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
                        payload = server.store.task_summary(task_id)
                    else:
                        payload = server.store.task_payload(
                            task_id,
                            item_limit=self._query_int(query, 'items_limit', 200),
                            item_offset=self._query_int(query, 'items_offset', 0),
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
                    self._send_json(server.scan_media_for_cleanup(task_id=task_id))
                    return
                if parsed.path == '/api/media/cleanup-logs':
                    self._send_json({'logs': server.list_cleanup_logs()})
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
                if parsed.path == '/api/auth/submit':
                    payload = self._read_json()
                    if server.auth_provider:
                        server.auth_provider.submit(payload)
                        self._send_json({'accepted': True})
                    else:
                        self._send_error('no_auth_provider', 'No auth provider configured.', HTTPStatus.SERVICE_UNAVAILABLE)
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
                parsed = urlparse(self.path)
                if parsed.path != '/api/settings':
                    self._send_error('not_found', 'Not found.', HTTPStatus.NOT_FOUND)
                    return
                try:
                    payload = self._read_json()
                    settings = server.update_settings(payload)
                    self._send_json({
                        'settings': sanitize_settings(settings),
                        'schema': server.settings_schema()
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
                parsed = urlparse(self.path)
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
                deleted = server.delete_task(task_id)
                if not deleted:
                    self._send_error('task_not_found', 'Task not found.', HTTPStatus.NOT_FOUND)
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
        if not source_link:
            raise WebUiApiError('source_link_required', 'Source link is required.', HTTPStatus.BAD_REQUEST)
        if not target_link:
            raise WebUiApiError('target_link_required', 'Target link is required.', HTTPStatus.BAD_REQUEST)
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
        task_id = self.store.create_task(
            source_link=source_link,
            target_link=target_link,
            target_profile=target_profile,
            start_id=start_id,
            end_id=end_id,
            include_comment=include_comment
        )
        if self.task_submitter:
            self.task_submitter(task_id)
        return {'task_id': task_id}

    def detect_transfer_range(self, source_link: str) -> tuple[int, int]:
        if not isinstance(self.operations, IWebUiOperations):
            raise WebUiApiError(
                'transfer_range_detection_unavailable',
                'Transfer range detection is unavailable.',
                HTTPStatus.BAD_REQUEST
            )
        try:
            detected = normalize_detected_transfer_range(
                self.operations.detect_transfer_range(source_link)
            )
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

    def list_watches(self) -> list:
        if isinstance(self.operations, IWebUiOperations):
            return self.operations.list_watches()
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
            for link in source_links:
                if not link.startswith('https://t.me/'):
                    raise WebUiApiError('invalid_watch_source', 'Watch source link must start with https://t.me/.', HTTPStatus.BAD_REQUEST)
            payload = {**payload, 'source_links': source_links}
        else:
            source_link = str(payload.get('source_link') or '').strip()
            target_link = str(payload.get('target_link') or '').strip()
            include_comment = bool(payload.get('include_comment'))
            if not source_link:
                raise WebUiApiError('watch_source_required', 'Source link is required.', HTTPStatus.BAD_REQUEST)
            if not target_link:
                raise WebUiApiError('watch_target_required', 'Target link is required.', HTTPStatus.BAD_REQUEST)
            if not source_link.startswith('https://t.me/'):
                raise WebUiApiError('invalid_watch_source', 'Watch source link must start with https://t.me/.', HTTPStatus.BAD_REQUEST)
            if not target_link.startswith('https://t.me/'):
                raise WebUiApiError('invalid_watch_target', 'Watch target link must start with https://t.me/.', HTTPStatus.BAD_REQUEST)
            payload = {
                **payload,
                'source_link': source_link,
                'target_link': target_link,
                'include_comment': include_comment
            }
        if isinstance(self.operations, IWebUiOperations):
            try:
                return self.operations.create_watch(payload)
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
        if isinstance(self.operations, IWebUiOperations):
            try:
                return self.operations.update_watch(watch_id, payload)
            except ValueError as e:
                raise WebUiApiError(
                    'update_watch_failed',
                    str(e),
                    HTTPStatus.BAD_REQUEST
                )
        raise WebUiApiError('watch_operations_unavailable', 'Watch operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def delete_watch(self, watch_id: str) -> bool:
        if isinstance(self.operations, IWebUiOperations):
            return bool(self.operations.delete_watch(watch_id))
        return False

    def delete_task(self, task_id: int) -> bool:
        if isinstance(self.operations, IWebUiOperations):
            return bool(self.operations.delete_web_task(task_id))
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
            if isinstance(self.operations, IWebUiOperations):
                reset_items = int(self.operations.retry_failed_web_task(task_id))
            else:
                reset_items = self.store.retry_failed_items(task_id)
                if reset_items and self.task_submitter:
                    self.task_submitter(task_id)
            return {'task_id': task_id, 'action': action, 'reset_items': reset_items}
        if action == 'pause':
            if isinstance(self.operations, IWebUiOperations):
                ok = bool(self.operations.pause_web_task(task_id))
            else:
                self.store.update_task(task_id, status='paused')
                ok = True
            if not ok:
                raise WebUiApiError('task_action_failed', 'Task action failed.', HTTPStatus.BAD_REQUEST)
            return {'task_id': task_id, 'action': action}
        if action == 'resume':
            if isinstance(self.operations, IWebUiOperations):
                ok = bool(self.operations.resume_web_task(task_id))
            else:
                self.store.update_task(task_id, status='pending')
                ok = True
                if self.task_submitter:
                    self.task_submitter(task_id)
            if not ok:
                raise WebUiApiError('task_action_failed', 'Task action failed.', HTTPStatus.BAD_REQUEST)
            return {'task_id': task_id, 'action': action}
        raise WebUiApiError('invalid_task_action', 'Invalid task action.', HTTPStatus.BAD_REQUEST)

    def statistics(self) -> dict:
        if isinstance(self.operations, IWebUiOperations):
            return self.operations.statistics()
        return {
            'tables': {
                'link': {'available': False, 'rows': 0},
                'count': {'available': False, 'rows': 0},
                'upload': {'available': False, 'rows': 0}
            }
        }

    def export_table(self, table_type: str) -> dict:
        if table_type not in ('link', 'count', 'upload'):
            raise WebUiApiError('invalid_table_type', 'Table type must be link, count, or upload.', HTTPStatus.BAD_REQUEST)
        if isinstance(self.operations, IWebUiOperations):
            return self.operations.export_table(table_type)
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
        if isinstance(self.operations, IWebUiOperations):
            return self.operations.create_upload(payload)
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
        if isinstance(self.operations, IWebUiOperations):
            return self.operations.create_channel_download(normalized)
        raise WebUiApiError('channel_download_operations_unavailable', 'Channel download operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def scan_media_for_cleanup(self, task_id: int = None) -> dict:
        if isinstance(self.operations, IWebUiOperations):
            return self.operations.scan_media_for_cleanup(task_id=task_id)
        raise WebUiApiError('media_operations_unavailable', 'Media operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def cleanup_media_files(self, payload: dict) -> dict:
        if isinstance(self.operations, IWebUiOperations):
            return self.operations.cleanup_media_files(payload)
        raise WebUiApiError('media_operations_unavailable', 'Media operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

    def list_cleanup_logs(self) -> list:
        if isinstance(self.operations, IWebUiOperations):
            return self.operations.list_cleanup_logs()
        return []

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
            'upload_pending_limit': {'min': 1, 'max': 5},
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
    global_settings = merge_allowed_settings(
        target=deepcopy(global_config.config),
        patch=payload.get('global', {}) if isinstance(payload, dict) else {},
        allowed={'notice', 'export_table', 'upload', 'forward_type', 'target_profiles'},
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
            target[key] = value
    return target


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
