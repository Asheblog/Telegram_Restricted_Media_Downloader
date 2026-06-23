# coding=UTF-8
import json
import os
import socket
import threading
import webbrowser

from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional
from urllib.parse import urlparse

from module import log
from module.enums import ENVIRON
from module.transfer_store import TransferStore
from module.web_ui_assets import WEB_UI_HTML


class WebUiServer:
    def __init__(
            self,
            store: TransferStore,
            task_submitter: Optional[Callable[[int], None]] = None,
            host: str = '127.0.0.1',
            port: int = 0
    ):
        self.store = store
        self.task_submitter = task_submitter
        self.host = host
        self.port = self.resolve_port(port)
        self.httpd: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None

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

    def start(self, open_browser: bool = True) -> None:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                log.info('[WebUI] ' + fmt, *args)

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
                parsed = urlparse(self.path)
                if parsed.path in ('/', '/index.html'):
                    self._send_html()
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
                parsed = urlparse(self.path)
                if parsed.path != '/api/tasks':
                    self._send_json({'error': 'Not found.'}, HTTPStatus.NOT_FOUND)
                    return
                try:
                    payload = self._read_json()
                    source_link = str(payload.get('source_link') or '').strip()
                    target_link = str(payload.get('target_link') or 'https://t.me/pikpak_bot').strip()
                    target_profile = str(payload.get('target_profile') or 'pikpak').strip()
                    start_id = payload.get('start_id')
                    end_id = payload.get('end_id')
                    if not source_link:
                        self._send_json({'error': 'Source link is required.'}, HTTPStatus.BAD_REQUEST)
                        return
                    if not target_link:
                        self._send_json({'error': 'Target link is required.'}, HTTPStatus.BAD_REQUEST)
                        return
                    start_id = int(start_id) if start_id not in (None, '') else None
                    end_id = int(end_id) if end_id not in (None, '') else None
                    if (start_id is None) != (end_id is None):
                        self._send_json({'error': 'Start ID and End ID must be provided together.'}, HTTPStatus.BAD_REQUEST)
                        return
                    if start_id is not None and end_id is not None:
                        if end_id < start_id:
                            self._send_json({'error': 'End ID must be greater than or equal to Start ID.'}, HTTPStatus.BAD_REQUEST)
                            return
                        normalized_source = source_link.rstrip('/')
                        if normalized_source.count('/') >= 4 and normalized_source.rsplit('/', 1)[-1].isdigit():
                            self._send_json({'error': 'Range transfer source must be a chat link, not a message link.'}, HTTPStatus.BAD_REQUEST)
                            return
                    task_id = server.store.create_task(
                        source_link=source_link,
                        target_link=target_link,
                        target_profile=target_profile,
                        start_id=start_id,
                        end_id=end_id
                    )
                    if server.task_submitter:
                        server.task_submitter(task_id)
                    self._send_json({'task_id': task_id}, HTTPStatus.CREATED)
                except Exception as e:
                    log.exception('[WebUI] 创建任务失败。')
                    self._send_json({'error': str(e)}, HTTPStatus.BAD_REQUEST)

        self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        log.info(f'WebUI started at {self.url}')
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
    return os.environ.get('TRMD_WEB_HOST', default)
