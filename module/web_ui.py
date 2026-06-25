# coding=UTF-8
import base64
import datetime
import hmac
import json
import os
import socket
import threading
import webbrowser

from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional
from urllib.parse import unquote, urlparse

from module import log
from module.enums import ENVIRON
from module.transfer_store import TransferStore
from module.web_ui_assets import WEB_UI_HTML


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


class WebUiServer:
    def __init__(
            self,
            store: TransferStore,
            task_submitter: Optional[Callable[[int], None]] = None,
            settings_provider: Optional[Callable[[], dict]] = None,
            settings_updater: Optional[Callable[[dict], dict]] = None,
            operations=None,
            host: str = '127.0.0.1',
            port: int = 0,
            username: Optional[str] = None,
            password: Optional[str] = None
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

            def _send_error(self, error_code, fallback, status):
                self._send_json(
                    {
                        'error_code': error_code,
                        'error': fallback
                    },
                    status
                )

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

            def _task_id_from_path(self):
                task_id = self.path.rsplit('/', 1)[-1]
                if not task_id.isdigit():
                    self._send_error('invalid_task_id', 'Invalid task id.', HTTPStatus.BAD_REQUEST)
                    return None
                return int(task_id)

            def do_GET(self):
                if not self._check_auth():
                    return
                parsed = urlparse(self.path)
                if parsed.path in ('/', '/index.html'):
                    self._send_html()
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
                    task_id = self._task_id_from_path()
                    if task_id is None:
                        return
                    payload = server.store.task_payload(task_id)
                    if not payload:
                        self._send_error('task_not_found', 'Task not found.', HTTPStatus.NOT_FOUND)
                        return
                    self._send_json(payload)
                    return
                self._send_error('not_found', 'Not found.', HTTPStatus.NOT_FOUND)

            def do_POST(self):
                if not self._check_auth():
                    return
                parsed = urlparse(self.path)
                if parsed.path == '/api/watches':
                    try:
                        payload = self._read_json()
                        result = server.create_watch(payload)
                        self._send_json(result, HTTPStatus.CREATED)
                    except WebUiApiError as e:
                        self._send_error(e.error_code, e.message, e.status)
                    except Exception as e:
                        log.exception('[WebUI] 创建实时监听失败。')
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
                        log.exception('[WebUI] 导出统计表失败。')
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
                        log.exception('[WebUI] 创建上传任务失败。')
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
                        log.exception('[WebUI] 创建频道下载失败。')
                        self._send_json(
                            {
                                'error_code': 'create_channel_download_failed',
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
                    source_link = str(payload.get('source_link') or '').strip()
                    target_link = str(payload.get('target_link') or 'https://t.me/pikpak_bot').strip()
                    target_profile = str(payload.get('target_profile') or 'pikpak').strip()
                    include_comment = bool(payload.get('include_comment'))
                    start_id = payload.get('start_id')
                    end_id = payload.get('end_id')
                    if not source_link:
                        self._send_error('source_link_required', 'Source link is required.', HTTPStatus.BAD_REQUEST)
                        return
                    if not target_link:
                        self._send_error('target_link_required', 'Target link is required.', HTTPStatus.BAD_REQUEST)
                        return
                    start_id = int(start_id) if start_id not in (None, '') else None
                    end_id = int(end_id) if end_id not in (None, '') else None
                    if (start_id is None) != (end_id is None):
                        self._send_error('range_ids_required', 'Start ID and End ID must be provided together.', HTTPStatus.BAD_REQUEST)
                        return
                    if start_id is not None and end_id is not None:
                        if end_id < start_id:
                            self._send_error('range_end_before_start', 'End ID must be greater than or equal to Start ID.', HTTPStatus.BAD_REQUEST)
                            return
                        normalized_source = source_link.rstrip('/')
                        if normalized_source.count('/') >= 4 and normalized_source.rsplit('/', 1)[-1].isdigit():
                            self._send_error('range_source_must_be_chat_link', 'Range transfer source must be a chat link, not a message link.', HTTPStatus.BAD_REQUEST)
                            return
                    task_id = server.store.create_task(
                        source_link=source_link,
                        target_link=target_link,
                        target_profile=target_profile,
                        start_id=start_id,
                        end_id=end_id,
                        include_comment=include_comment
                    )
                    if server.task_submitter:
                        server.task_submitter(task_id)
                    self._send_json({'task_id': task_id}, HTTPStatus.CREATED)
                except Exception as e:
                    log.exception('[WebUI] 创建任务失败。')
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
                    log.exception('[WebUI] 更新设置失败。')
                    self._send_json(
                        {
                            'error_code': 'update_settings_failed',
                            'error': str(e)
                        },
                        HTTPStatus.BAD_REQUEST
                    )

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
                deleted = server.store.delete_task(task_id)
                if not deleted:
                    self._send_error('task_not_found', 'Task not found.', HTTPStatus.NOT_FOUND)
                    return
                self._send_json({'deleted': True, 'task_id': task_id})

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

    def get_settings(self) -> dict:
        if self.settings_provider:
            return self.settings_provider()
        return load_runtime_settings()

    def list_watches(self) -> list:
        if self.operations and hasattr(self.operations, 'list_watches'):
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
        if self.operations and hasattr(self.operations, 'create_watch'):
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

    def delete_watch(self, watch_id: str) -> bool:
        if self.operations and hasattr(self.operations, 'delete_watch'):
            return bool(self.operations.delete_watch(watch_id))
        return False

    def statistics(self) -> dict:
        if self.operations and hasattr(self.operations, 'statistics'):
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
        if self.operations and hasattr(self.operations, 'export_table'):
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
        if self.operations and hasattr(self.operations, 'create_upload'):
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
        if self.operations and hasattr(self.operations, 'create_channel_download'):
            return self.operations.create_channel_download(normalized)
        raise WebUiApiError('channel_download_operations_unavailable', 'Channel download operations are unavailable.', HTTPStatus.SERVICE_UNAVAILABLE)

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
        target=user.config.copy(),
        patch=payload.get('user', {}) if isinstance(payload, dict) else {},
        allowed={
            'api_id', 'api_hash', 'bot_token', 'session_directory', 'save_directory',
            'temp_directory', 'max_tasks', 'max_retries', 'download_type', 'is_shutdown',
            'proxy'
        }
    )
    global_settings = merge_allowed_settings(
        target=global_config.config.copy(),
        patch=payload.get('global', {}) if isinstance(payload, dict) else {},
        allowed={'notice', 'export_table', 'upload', 'forward_type', 'target_profiles'}
    )
    user.save_config(user_config)
    global_config.save_config(global_settings)
    return load_runtime_settings()


def merge_allowed_settings(target: dict, patch: dict, allowed: set) -> dict:
    if not isinstance(patch, dict):
        return target
    for key, value in patch.items():
        if key not in allowed:
            continue
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key] = merge_allowed_settings(
                target=target.get(key, {}).copy(),
                patch=value,
                allowed=set(target.get(key, {}).keys()) | set(value.keys())
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
