# coding=UTF-8
import base64
import hmac
import json
import os
import socket
import threading
import webbrowser

from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional
from urllib.parse import urlparse, unquote

from module import log
from module.enums import ENVIRON
from module.transfer_store import TransferStore
from module.web_ui_assets import WEB_UI_HTML
from module.web_commands import (
    COMMAND_HELP,
    WebCommand,
    normalize_command_payload,
    primary_links_for_task
)


class WebUiServer:
    def __init__(
            self,
            store: TransferStore,
            task_submitter: Optional[Callable[[int], None]] = None,
            summary_provider: Optional[Callable[[], dict]] = None,
            listener_remover: Optional[Callable[[str], bool]] = None,
            host: str = '127.0.0.1',
            port: int = 0,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        self.store = store
        self.task_submitter = task_submitter
        self.summary_provider = summary_provider
        self.listener_remover = listener_remover
        self.host = host
        self.port = self.resolve_port(port)
        self.username = (username or '').strip()
        self.password = password or ''
        self.httpd: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
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

    def validate_auth_config(self) -> None:
        if bool(self.username) != bool(self.password):
            raise ValueError('TRMD_WEB_USERNAME 和 TRMD_WEB_PASSWORD 必须同时设置。')
        if self.requires_auth and not self.auth_enabled:
            raise ValueError('WebUI 对外监听时必须设置 TRMD_WEB_USERNAME 和 TRMD_WEB_PASSWORD。')

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

    def start(self, open_browser: bool = True) -> None:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                log.info('[WebUI] ' + fmt, *args)

            def _send_auth_required(self):
                data = json.dumps(
                    {'error': 'Authentication required.'},
                    ensure_ascii=False
                ).encode('utf-8')
                self.send_response(HTTPStatus.UNAUTHORIZED)
                self.send_header('www-authenticate', 'Basic realm="TRMD WebUI"')
                self.send_header('content-type', 'application/json; charset=utf-8')
                self.send_header('cache-control', 'no-store')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _check_auth(self):
                if server.is_authorized(self.headers.get('authorization')):
                    return True
                self._send_auth_required()
                return False

            def _send_json(self, payload, status=HTTPStatus.OK):
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                self.send_response(status)
                self.send_header('content-type', 'application/json; charset=utf-8')
                self.send_header('cache-control', 'no-store')
                self.send_header('content-length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _send_html(self):
                data = WEB_UI_HTML.encode('utf-8')
                self.send_response(HTTPStatus.OK)
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

            def do_GET(self):
                if not self._check_auth():
                    return
                parsed = urlparse(self.path)
                if parsed.path in ('/', '/index.html'):
                    self._send_html()
                    return
                if parsed.path == '/api/commands/help':
                    self._send_json({'commands': COMMAND_HELP})
                    return
                if parsed.path == '/api/runtime/summary':
                    summary_provider = getattr(server, 'summary_provider', None)
                    summary = summary_provider() if callable(summary_provider) else {}
                    self._send_json(summary)
                    return
                if parsed.path == '/api/tasks':
                    self._send_json({'tasks': server.store.list_tasks()})
                    return
                if parsed.path.startswith('/api/tasks/'):
                    task_id = parsed.path.rsplit('/', 1)[-1]
                    if not task_id.isdigit():
                        self._send_json({'error': 'Invalid task id.'}, HTTPStatus.BAD_REQUEST)
                        return
                    payload = server.store.task_payload(int(task_id))
                    if not payload:
                        self._send_json({'error': 'Task not found.'}, HTTPStatus.NOT_FOUND)
                        return
                    self._send_json(payload)
                    return
                self._send_json({'error': 'Not found.'}, HTTPStatus.NOT_FOUND)

            def do_POST(self):
                if not self._check_auth():
                    return
                parsed = urlparse(self.path)
                if parsed.path == '/api/runtime/exit':
                    payload = self._read_json()
                    reason = str(payload.get('reason') or 'Requested from WebUI.').strip()
                    task_id = server.store.create_task(
                        command=WebCommand.EXIT,
                        payload={'reason': reason},
                        source_link=WebCommand.EXIT,
                        target_link='',
                        target_profile='runtime'
                    )
                    if server.task_submitter:
                        server.task_submitter(task_id)
                    self._send_json({'task_id': task_id}, HTTPStatus.ACCEPTED)
                    return
                if parsed.path != '/api/tasks':
                    self._send_json({'error': 'Not found.'}, HTTPStatus.NOT_FOUND)
                    return
                try:
                    payload = self._read_json()
                    command = str(payload.get('command') or WebCommand.DOWNLOAD).strip()
                    command_payload = payload.get('payload')
                    if not isinstance(command_payload, dict):
                        command_payload = {
                            key: value for key, value in payload.items()
                            if key not in ('command', 'payload')
                        }
                    normalized_payload = normalize_command_payload(command, command_payload)
                    primary = primary_links_for_task(command, normalized_payload)
                    task_id = server.store.create_task(
                        command=command,
                        payload=normalized_payload,
                        source_link=primary.get('source_link') or '',
                        target_link=primary.get('target_link') or '',
                        target_profile=primary.get('target_profile') or 'generic',
                        start_id=normalized_payload.get('start_id'),
                        end_id=normalized_payload.get('end_id')
                    )
                    if server.task_submitter and command in WebCommand.MUTATING:
                        server.task_submitter(task_id)
                    self._send_json({'task_id': task_id}, HTTPStatus.CREATED)
                except Exception as e:
                    log.exception('[WebUI] 创建任务失败。')
                    self._send_json({'error': str(e)}, HTTPStatus.BAD_REQUEST)

            def do_DELETE(self):
                if not self._check_auth():
                    return
                parsed = urlparse(self.path)
                if not parsed.path.startswith('/api/listeners/'):
                    self._send_json({'error': 'Not found.'}, HTTPStatus.NOT_FOUND)
                    return
                listener_id = unquote(parsed.path[len('/api/listeners/'):])
                remover = getattr(server, 'listener_remover', None)
                if not callable(remover):
                    self._send_json({'error': 'Listener removal is not available.'}, HTTPStatus.BAD_REQUEST)
                    return
                if remover(listener_id):
                    self._send_json({'removed': True})
                    return
                self._send_json({'error': 'Listener not found.'}, HTTPStatus.NOT_FOUND)

        self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        auth_status = 'enabled' if self.auth_enabled else 'disabled'
        log.info(f'WebUI started at {self.url}, auth={auth_status}')
        if open_browser:
            try:
                webbrowser.open(self.url)
            except Exception as e:
                log.warning(f'无法自动打开浏览器: {e}')

    def stop(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.thread = None


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
