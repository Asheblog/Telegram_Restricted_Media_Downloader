# coding=UTF-8
import datetime
import hashlib
import hmac
import json
import os
import secrets
import socket
import threading
import time
import webbrowser
from copy import deepcopy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional
from urllib.parse import urlparse

from module.adapters.webui.contracts import (
    SENSITIVE_SETTING_KEYS,
    SPA_VIEW_PATHS,
    WebUiApiError,
    is_spa_page_path,
    sanitize_settings,
)
from module.adapters.webui.security import (
    LoginThrottle,
    cookie_secure_mode,
    cookie_secure_required,
    is_cross_origin_request,
    security_headers,
)
from module.adapters.webui.view_model import WebUiViewModel
from module.utils.diagnostics import default_diagnostic
from module.core.enums import ENVIRON
from module.ports import IDiagnosticPort, IWebUiOperations
from module.domain.archive_naming.source_folders import normalize_archive_title_source
from module.persistence.transfer_store import TransferStore

# JSON 请求体上限：WebUI 只收发控制数据（路径 / 链接 / 监听备份），不上传媒体本体。
MAX_JSON_BODY_BYTES = 8 * 1024 * 1024


def normalize_optional_int(value):
    return int(value) if value not in (None, "") else None


def is_message_link(link: str) -> bool:
    try:
        parsed = urlparse(str(link).strip())
    except ValueError:
        return False
    paths = [part for part in parsed.path.split("/") if part]
    if not paths:
        return False
    if paths[0] == "c":
        return len(paths) >= 3 and paths[-1].isdigit()
    return len(paths) >= 2 and paths[-1].isdigit()


def normalize_detected_transfer_range(value) -> Optional[tuple[int, int]]:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        start_id = value.get("start_id")
        end_id = value.get("end_id")
    else:
        try:
            start_id, end_id = value
        except (TypeError, ValueError):
            return None
    if start_id in (None, "") or end_id in (None, ""):
        return None
    return int(start_id), int(end_id)


class AuthProvider:
    """Thread-safe auth provider for WebUI Telegram login flow."""

    STEP_PENDING = "pending"
    STEP_PHONE = "phone"
    STEP_CODE = "code"
    STEP_PASSWORD = "password"
    STEP_RECOVERY_CODE = "recovery_code"
    STEP_EMAIL_CODE = "email_code"
    STEP_SIGNUP = "signup"
    STEP_DONE = "done"
    STEP_ERROR = "error"

    def __init__(self):
        self.step: str = self.STEP_PENDING
        self.message: str = ""
        self.hint: str = ""
        self.code_type: str = ""
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

    def set_step(
        self, step: str, message: str = "", hint: str = "", code_type: str = ""
    ):
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
                "step": self.step,
                "message": self.message,
                "hint": self.hint,
                "code_type": self.code_type,
                "error": self.error,
                "user": self.user_info,
            }


class WebUiServer:
    SETUP_ALLOWED_PREFIXES = (
        "/api/auth/",
        "/api/setup/",
        "/api/settings",
    )

    def __init__(
        self,
        store: TransferStore,
        task_submitter: Optional[Callable[[int], None]] = None,
        settings_provider: Optional[Callable[[], dict]] = None,
        settings_updater: Optional[Callable[[dict], dict]] = None,
        operations: Optional[IWebUiOperations] = None,
        host: str = "127.0.0.1",
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
        setup_bot_saver: Optional[Callable[[dict], dict]] = None,
        setup_bot_skipper: Optional[Callable[[Optional[dict]], dict]] = None,
        setup_ready_checker: Optional[Callable[[], bool]] = None,
        pikpak_accounts_provider: Optional[Callable[[], dict]] = None,
        pikpak_account_adder: Optional[Callable[[dict], dict]] = None,
        pikpak_account_switcher: Optional[Callable[[dict], dict]] = None,
        pikpak_account_remover: Optional[Callable[[dict], dict]] = None,
    ):
        self.store = store
        self.view_model = WebUiViewModel(store)
        self.task_submitter = task_submitter
        self.settings_provider = settings_provider
        self.settings_updater = settings_updater
        self.operations = operations
        self.host = host
        self.port = self.resolve_port(port)
        self.username = (username or "").strip()
        self.password = password or ""
        self.diagnostic = diagnostic or default_diagnostic
        self.deep_link_whitelist_getter = deep_link_whitelist_getter
        self.setup_status_provider = setup_status_provider
        self.setup_api_saver = setup_api_saver
        self.setup_rclone_configurer = setup_rclone_configurer
        self.setup_rclone_skipper = setup_rclone_skipper
        self.setup_rclone_tester = setup_rclone_tester
        self.setup_bot_saver = setup_bot_saver
        self.setup_bot_skipper = setup_bot_skipper
        self.setup_ready_checker = setup_ready_checker
        self.pikpak_accounts_provider = pikpak_accounts_provider
        self.pikpak_account_adder = pikpak_account_adder
        self.pikpak_account_switcher = pikpak_account_switcher
        self.pikpak_account_remover = pikpak_account_remover
        self.httpd: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.auth_provider: Optional[AuthProvider] = None
        self.login_throttle = LoginThrottle.from_env(on_lockout=self._report_login_lockout)
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
        if path in (
            "/api/auth/login",
            "/api/auth/logout",
            "/api/auth/status",
            "/api/auth/submit",
        ):
            return True
        if path == "/api/settings" or path.startswith("/api/settings?"):
            return True
        return any(
            path == prefix.rstrip("/") or path.startswith(prefix)
            for prefix in self.SETUP_ALLOWED_PREFIXES
        )

    def _require_deep_link_whitelist_if_enabled(self, resolve_deep_link: bool) -> None:
        if not resolve_deep_link:
            return
        getter = getattr(self, "deep_link_whitelist_getter", None)
        whitelist = list(getter() or []) if callable(getter) else []
        if not whitelist:
            raise WebUiApiError(
                "deep_link_whitelist_required",
                "已开启深链取片，请先在系统设置填写资源 bot 白名单。",
                HTTPStatus.BAD_REQUEST,
            )

    def _operation(self, name: str):
        """按名字取业务操作。

        返回 ``None`` **仅表示"整套 operations 未接线"**（调用方回 503 是对的）。
        如果 operations 在、但这个名字不存在，那是接线/改名错误，不是服务不可用：
        旧实现同样返回 ``None``，于是被上层报成 503「operations unavailable」，
        把 bug 伪装成故障。现在显式抛 500 并带上具体方法名。
        """
        if self.operations is None:
            return None
        method = getattr(self.operations, name, None)
        if callable(method):
            return method
        raise WebUiApiError(
            "operation_not_wired",
            f"WebUI operation {name!r} is not implemented by the operations facade.",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @staticmethod
    def resolve_port(port: int) -> int:
        env_port = int(port or 0)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("", env_port))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return int(sock.getsockname()[1])

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def auth_enabled(self) -> bool:
        return bool(self.username and self.password)

    @property
    def requires_auth(self) -> bool:
        return self.host not in ("127.0.0.1", "localhost", "::1")

    SESSION_COOKIE_NAME = "trmd_session"
    SESSION_MAX_AGE = 30 * 24 * 60 * 60  # 30 days
    SESSION_NONCE_BYTES = 16

    def validate_auth_config(self) -> None:
        if bool(self.username) != bool(self.password):
            raise ValueError("TRMD_WEB_USERNAME 和 TRMD_WEB_PASSWORD 必须同时设置。")
        if self.requires_auth and not self.auth_enabled:
            raise ValueError(
                "WebUI 对外监听时必须设置 TRMD_WEB_USERNAME 和 TRMD_WEB_PASSWORD。"
            )

    def _session_signing_key(self) -> bytes:
        material = f"{self.username}\0{self.password}".encode("utf-8")
        return hashlib.sha256(b"trmd-webui-session\0" + material).digest()

    def _sign_session_payload(self, payload: str) -> str:
        return hmac.new(
            self._session_signing_key(),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _generate_session_token(self) -> str:
        expiry = int(time.time()) + self.SESSION_MAX_AGE
        nonce = secrets.token_hex(self.SESSION_NONCE_BYTES)
        payload = f"{expiry}.{nonce}"
        return f"{payload}.{self._sign_session_payload(payload)}"

    def _create_session_cookie(
        self, token: str, remember_me: bool = True, secure: bool = False
    ) -> str:
        parts = [
            f"{self.SESSION_COOKIE_NAME}={token}",
            "Path=/",
            "HttpOnly",
            "SameSite=Lax",
        ]
        if secure:
            parts.append("Secure")
        if remember_me:
            parts.insert(1, f"Max-Age={self.SESSION_MAX_AGE}")
        return "; ".join(parts)

    def _clear_session_cookie(self, secure: bool = False) -> str:
        parts = [
            f"{self.SESSION_COOKIE_NAME}=",
            "Max-Age=0",
            "Path=/",
            "HttpOnly",
            "SameSite=Lax",
        ]
        if secure:
            parts.append("Secure")
        return "; ".join(parts)

    def security_headers(self, handler) -> list[tuple[str, str]]:
        """Security headers attached to every response served by this server."""
        return security_headers(handler, requires_auth=self.requires_auth)

    def cookie_secure_required(self, handler) -> bool:
        """Whether this request must get a ``Secure`` session cookie."""
        return cookie_secure_required(handler, requires_auth=self.requires_auth)

    @staticmethod
    def client_ip(handler) -> str:
        """Peer address of the TCP connection.

        不解析 ``X-Forwarded-For``：反代是否覆写该头不由本程序控制，信任它等于
        给攻击者一个「换个头就换桶」的限流绕过口子。反代部署下所有请求落在同一
        桶里是刻意的取舍（配合「凭据正确即放行」，正常登录不会被锁）。
        """
        address = getattr(handler, "client_address", None) or ()
        return str(address[0]) if len(address) > 0 else ""

    def register_login_failure(self, handler, username: str) -> int:
        """Record a failed login and return retry-after seconds (0 = not limited)."""
        if self.login_throttle is None:
            return 0
        return self.login_throttle.record_failure(self.client_ip(handler), username)

    def clear_login_failures(self, handler, username: str) -> None:
        if self.login_throttle is not None:
            self.login_throttle.record_success(self.client_ip(handler), username)

    def _report_login_lockout(self, locked: list[tuple[str, int]]) -> None:
        detail = ", ".join(f"{key}:{seconds}s" for key, seconds in locked)
        self.diagnostic.warning(f"[WebUI] 登录失败次数超限，已临时限流（{detail}）。")

    def validate_session_token(self, token: str) -> bool:
        if not token or not self.auth_enabled:
            return False
        parts = token.split(".")
        if len(parts) != 3:
            return False
        expiry_text, nonce, signature = parts
        if not expiry_text.isdigit() or not nonce or not signature:
            return False
        payload = f"{expiry_text}.{nonce}"
        expected = self._sign_session_payload(payload)
        if not hmac.compare_digest(signature, expected):
            return False
        if time.time() > int(expiry_text):
            return False
        return True

    @staticmethod
    def _get_request_cookie(
        handler: BaseHTTPRequestHandler, name: str
    ) -> Optional[str]:
        cookie_header = handler.headers.get("cookie")
        if not cookie_header:
            return None
        prefix = f"{name}="
        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith(prefix):
                return part[len(prefix) :]
        return None

    def validate_credentials(self, username: str, password: str) -> bool:
        if not self.auth_enabled:
            return True
        return secrets.compare_digest(
            username, self.username
        ) and secrets.compare_digest(password, self.password)

    def set_auth_provider(self, provider: "AuthProvider") -> None:
        self.auth_provider = provider

    def start(self, open_browser: bool = True) -> None:
        from module.adapters.webui.handlers import (
            auth,
            dispatch_delete,
            dispatch_get,
            dispatch_patch,
            dispatch_post,
            dispatch_put,
            static_pages,
        )

        server = self

        class Handler(BaseHTTPRequestHandler):
            # 不泄露 stdlib / Python 版本指纹（`Server: BaseHTTP/0.6 Python/3.x`）。
            server_version = "trmd-webui"
            sys_version = ""
            # stdlib 默认 HTTP/0.9 会在解析失败时抑制全部响应头（连状态行都没有，
            # 反向代理会判为 invalid upstream response）；抬到 HTTP/1.0 保证
            # 非法请求行也能拿到带状态行 + 安全头的正规响应。
            default_request_version = "HTTP/1.0"
            _response_started = False

            def log_message(self, fmt, *args):
                server.diagnostic.info("[WebUI] " + fmt, *args)

            def log_error(self, fmt, *args):
                server.diagnostic.warning("[WebUI] " + fmt, *args)

            def version_string(self) -> str:
                return self.server_version

            def send_response_only(self, code, message=None):
                self._response_started = True
                super().send_response_only(code, message)

            def end_headers(self):
                """Attach the security headers to every response, including errors."""
                for name, value in server.security_headers(self):
                    self.send_header(name, value)
                super().end_headers()

            def send_error(self, code, message=None, explain=None):
                """JSON error body instead of the stdlib HTML error page.

                覆盖后 ``OPTIONS``/``HEAD``/非法请求行等由 stdlib 触发的错误不再
                回吐 ``Unsupported method (...)`` 与 Python 版本指纹。
                """
                try:
                    fallback = HTTPStatus(code).phrase
                except ValueError:
                    fallback = "Error"
                detail = str(message or fallback)
                if detail.startswith("Unsupported method"):
                    # 不回显调用方自选的方法名（也是 stdlib 指纹的一部分）。
                    detail = "Unsupported method."
                self.log_error("code %s, message %s", code, message)
                self.close_connection = True
                self._send_json(
                    {
                        "error_code": f"http_{int(code)}",
                        "error": detail,
                    },
                    code,
                    {"connection": "close"},
                )

            def _send_auth_required(self):
                self._send_json(
                    {
                        "error_code": "auth_required",
                        "error": "Authentication required.",
                    },
                    HTTPStatus.UNAUTHORIZED,
                )

            def _write_pending_cookie(self):
                cookie = getattr(self, "_pending_cookie", None)
                if cookie:
                    self.send_header("Set-Cookie", cookie)
                    self._pending_cookie = None

            def _try_authorize(self):
                """Check and apply auth silently. Returns True if authorized."""
                if not server.auth_enabled:
                    return True
                session_token = server._get_request_cookie(
                    self, server.SESSION_COOKIE_NAME
                )
                return bool(
                    session_token and server.validate_session_token(session_token)
                )

            def _check_auth(self):
                """Auth gate.

                只放行「精确方法 + 精确路径」的登录入口；其余一律 401。这样
                ``GET /api/auth/login``（方法不支持）不再返回 ``404 not_found``，
                未授权者无法再用 404/401 差分枚举路由白名单。
                """
                path = urlparse(self.path).path
                if self.command == "POST" and path == "/api/auth/login":
                    return True
                if self._try_authorize():
                    return True
                self._send_auth_required()
                return False

            def _check_request_origin(self):
                """Reject browser-declared cross-site state-changing requests (CSRF).

                不因「未启用登录」而跳过：无凭证的本地部署同样不希望被跨站页面驱动。
                不带 ``Origin``/``Referer`` 的客户端（curl、脚本、单测）照旧放行。
                """
                if not is_cross_origin_request(self):
                    return True
                server.diagnostic.warning(
                    f"[WebUI] 已拒绝跨站状态变更请求: {self.path}"
                )
                self._send_error(
                    "cross_origin_forbidden",
                    "Cross-origin request rejected.",
                    HTTPStatus.FORBIDDEN,
                )
                return False

            def _send_setup_required(self):
                self._send_json(
                    {
                        "error_code": "setup_required",
                        "error": "请先完成初始化配置。",
                    },
                    HTTPStatus.CONFLICT,
                )

            def _check_setup_ready(self):
                path = urlparse(self.path).path
                if not path.startswith("/api/"):
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

            def _safe_write(self, data: bytes) -> None:
                """Never let a half-dead client socket turn into a stderr traceback."""
                try:
                    self.wfile.write(data)
                except OSError:
                    self.close_connection = True

            def _begin_response(self, status) -> bool:
                """Start a response; False when headers were already flushed."""
                if self._response_started:
                    self.close_connection = True
                    return False
                try:
                    self.send_response(status)
                except OSError:
                    self.close_connection = True
                    return False
                return True

            def _send_json(self, payload, status=HTTPStatus.OK, extra_headers=None):
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                if not self._begin_response(status):
                    return
                try:
                    self._write_pending_cookie()
                    for name, value in (extra_headers or {}).items():
                        self.send_header(name, value)
                    self.send_header("content-type", "application/json; charset=utf-8")
                    self.send_header("cache-control", "no-store")
                    self.send_header("content-length", str(len(data)))
                    self.end_headers()
                except OSError:
                    self.close_connection = True
                    return
                self._safe_write(data)

            def _send_text_download(self, content: str, filename: str):
                data = (content or "").encode("utf-8")
                if not self._begin_response(HTTPStatus.OK):
                    return
                try:
                    self._write_pending_cookie()
                    self.send_header("content-type", "text/plain; charset=utf-8")
                    self.send_header(
                        "content-disposition", f'attachment; filename="{filename}"'
                    )
                    self.send_header("cache-control", "no-store")
                    self.send_header("content-length", str(len(data)))
                    self.end_headers()
                except OSError:
                    self.close_connection = True
                    return
                self._safe_write(data)

            def _send_json_download(self, payload, filename: str):
                data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                if not self._begin_response(HTTPStatus.OK):
                    return
                try:
                    self._write_pending_cookie()
                    self.send_header("content-type", "application/json; charset=utf-8")
                    self.send_header(
                        "content-disposition", f'attachment; filename="{filename}"'
                    )
                    self.send_header("cache-control", "no-store")
                    self.send_header("content-length", str(len(data)))
                    self.end_headers()
                except OSError:
                    self.close_connection = True
                    return
                self._safe_write(data)

            def _send_bytes_download(
                self, data: bytes, filename: str, content_type: str
            ):
                payload = data or b""
                if not self._begin_response(HTTPStatus.OK):
                    return
                try:
                    self._write_pending_cookie()
                    self.send_header("content-type", content_type)
                    self.send_header(
                        "content-disposition", f'attachment; filename="{filename}"'
                    )
                    self.send_header("cache-control", "no-store")
                    self.send_header("content-length", str(len(payload)))
                    self.end_headers()
                except OSError:
                    self.close_connection = True
                    return
                self._safe_write(payload)

            def _send_error(self, error_code, fallback, status, extra_headers=None):
                self._send_json(
                    {"error_code": error_code, "error": fallback},
                    status,
                    extra_headers,
                )

            def _read_json(self, expect_object: bool = True):
                """Parse the request body; every malformed shape becomes a 4xx.

                非对象 JSON（``[]`` / ``123`` / ``null`` / ``"a"``）与非法 JSON 一律
                返回结构化 400，绝不抛到 ``socketserver`` 造成 502 / 连接重置。

                正文已由 ``_run`` → ``_consume_request_body`` 提前读完并缓存，
                这里不再碰 ``rfile``（否则会读到 EOF，把正常请求误判成空 body）。
                """
                raw_length = self.headers.get("content-length")
                try:
                    length = int(raw_length or "0")
                except (TypeError, ValueError):
                    raise WebUiApiError(
                        "invalid_content_length",
                        "Invalid Content-Length header.",
                        HTTPStatus.BAD_REQUEST,
                    )
                if length < 0:
                    raise WebUiApiError(
                        "invalid_content_length",
                        "Invalid Content-Length header.",
                        HTTPStatus.BAD_REQUEST,
                    )
                if length > MAX_JSON_BODY_BYTES:
                    raise WebUiApiError(
                        "request_body_too_large",
                        "Request body is too large.",
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    )
                raw = getattr(self, "_body_cache", None)
                if raw is None:
                    raw = b""
                if not raw:
                    return {}
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    raise WebUiApiError(
                        "invalid_json_body",
                        "Request body must be valid JSON.",
                        HTTPStatus.BAD_REQUEST,
                    )
                if expect_object and not isinstance(payload, dict):
                    raise WebUiApiError(
                        "invalid_json_body",
                        "Request body must be a JSON object.",
                        HTTPStatus.BAD_REQUEST,
                    )
                return payload

            @staticmethod
            def _query_int(query: dict, key: str, default: int) -> int:
                try:
                    return int((query.get(key) or [str(default)])[0])
                except (ValueError, TypeError):
                    return default

            @staticmethod
            def _query_optional_int(query: dict, key: str) -> int | None:
                raw = (query.get(key) or [""])[0]
                if raw in ("", None):
                    return None
                try:
                    return int(raw)
                except (ValueError, TypeError):
                    return None

            def _task_id_from_path(self):
                task_path = urlparse(self.path).path
                task_id = task_path.rsplit("/", 1)[-1]
                if not task_id.isdigit():
                    self._send_error(
                        "invalid_task_id", "Invalid task id.", HTTPStatus.BAD_REQUEST
                    )
                    return None
                return int(task_id)

            def _respond_unhandled(self, exc: Exception) -> None:
                """Last line of defense: structured 5xx instead of a dead connection.

                自身也必须绝不抛出——否则等于把异常又送回 socketserver（F-01 症状）。
                """
                try:
                    if isinstance(exc, WebUiApiError):
                        server.diagnostic.warning(
                            f"[WebUI] 请求失败 {self.command} {self.path}: {exc.error_code}"
                        )
                        self._send_error(exc.error_code, exc.message, exc.status)
                        return
                    server.diagnostic.exception(
                        f"[WebUI] 未捕获异常 {self.command} {self.path}，已返回 internal_error。"
                    )
                    self._send_error(
                        "internal_error",
                        "Internal server error.",
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                    )
                except Exception:  # noqa: BLE001 - 兜底路径不可再抛
                    self.close_connection = True

            def _consume_request_body(self) -> None:
                """请求一进来就把 body 读进内存缓存。

                为什么要提前读：HTTP 层有多处在**读 body 之前**就回错误（鉴权 401、
                跨站 403、setup 409、body 超限 413、Content-Length 非法 400）。
                只要还有字节留在套接字里，本服务器关闭连接时内核就会发 RST，而 RST
                会丢掉客户端内核中尚未取走的响应字节 —— 客户端在 `getresponse()`
                处随机拿到 `ConnectionAbortedError`，而不是我们发出的 4xx
                （实测：带 body 的未鉴权 POST 约 0.5%/请求，放大后 16.7%）。

                因此这里统一读完并缓存，`_read_json()` 之后只从缓存解析。
                上限仍按 MAX_JSON_BODY_BYTES 约束（超限留给 `_read_json` 回 413）。
                """
                self._body_cache = None
                raw_length = self.headers.get("content-length") if self.headers else None
                if not raw_length:
                    return
                try:
                    length = int(raw_length)
                except (TypeError, ValueError):
                    return  # 非法长度交给 _read_json 回 400
                if length < 0 or length > MAX_JSON_BODY_BYTES:
                    return  # 超限交给 _read_json 回 413，避免先吃掉巨量内存
                self._body_cache = self._read_exactly(length)

            def _read_exactly(self, length: int) -> bytes:
                chunks: list[bytes] = []
                remaining = length
                while remaining > 0:
                    try:
                        chunk = self.rfile.read(remaining)
                    except OSError:
                        self.close_connection = True
                        break
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                return b"".join(chunks)

            def _run(self, route) -> None:
                """Run one route with a catch-all so nothing escapes to socketserver."""
                self._response_started = False
                self._body_cache = None
                try:
                    # 先读干净请求体（见 _consume_request_body），避免早退路径留下未读
                    # 字节导致关闭连接时发 RST、客户端丢响应。
                    self._consume_request_body()
                except Exception:  # noqa: BLE001 - 读体失败也必须能回响应
                    self.close_connection = True
                try:
                    route()
                except Exception as exc:  # noqa: BLE001 - HTTP 边界必须兜底
                    self._respond_unhandled(exc)

            def _send_method_not_allowed(self):
                if not self._begin_response(HTTPStatus.METHOD_NOT_ALLOWED):
                    return
                try:
                    self.send_header(
                        "allow", "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
                    )
                    self.send_header("cache-control", "no-store")
                    self.send_header("content-length", "0")
                    self.end_headers()
                except OSError:
                    self.close_connection = True

            def do_OPTIONS(self):
                self._run(self._send_method_not_allowed)

            def do_HEAD(self):
                self._run(self._send_method_not_allowed)

            def _route_get(self):
                parsed = urlparse(self.path)
                if static_pages.handle_get(self, server, parsed):
                    return
                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                if dispatch_get(self, server, parsed):
                    return
                self._send_error("not_found", "Not found.", HTTPStatus.NOT_FOUND)

            def _route_post(self):
                parsed = urlparse(self.path)
                if not self._check_request_origin():
                    return
                if auth.handle_post_public(self, server, parsed):
                    return
                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                if dispatch_post(self, server, parsed):
                    return
                self._send_error("not_found", "Not found.", HTTPStatus.NOT_FOUND)

            def _route_patch(self):
                if not self._check_request_origin():
                    return
                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                parsed = urlparse(self.path)
                if dispatch_patch(self, server, parsed):
                    return
                self._send_error("not_found", "Not found.", HTTPStatus.NOT_FOUND)

            def _route_put(self):
                if not self._check_request_origin():
                    return
                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                parsed = urlparse(self.path)
                if dispatch_put(self, server, parsed):
                    return
                self._send_error("not_found", "Not found.", HTTPStatus.NOT_FOUND)

            def _route_delete(self):
                if not self._check_request_origin():
                    return
                if not self._check_auth():
                    return
                if not self._check_setup_ready():
                    return
                parsed = urlparse(self.path)
                if dispatch_delete(self, server, parsed):
                    return
                self._send_error("not_found", "Not found.", HTTPStatus.NOT_FOUND)

            def do_GET(self):
                self._run(self._route_get)

            def do_POST(self):
                self._run(self._route_post)

            def do_PATCH(self):
                self._run(self._route_patch)

            def do_PUT(self):
                self._run(self._route_put)

            def do_DELETE(self):
                self._run(self._route_delete)

        self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        auth_status = "enabled" if self.auth_enabled else "disabled"
        self.diagnostic.info(
            f"WebUI started at {self.url}, auth={auth_status}, "
            f"login_ratelimit={'on' if self.login_throttle else 'off'}, "
            f"cookie_secure={cookie_secure_mode()}"
        )
        if open_browser:
            try:
                webbrowser.open(self.url)
            except Exception as e:
                self.diagnostic.warning(f"无法自动打开浏览器: {e}")

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
            raise WebUiApiError(
                "invalid_payload", "Invalid payload.", HTTPStatus.BAD_REQUEST
            )
        source_link = str(payload.get("source_link") or "").strip()
        target_link = str(
            payload.get("target_link") or "https://t.me/pikpak_bot"
        ).strip()
        target_profile = str(payload.get("target_profile") or "pikpak").strip()
        include_comment = bool(payload.get("include_comment"))
        resolve_deep_link = bool(payload.get("resolve_deep_link"))
        archive_by_author = bool(payload.get("archive_by_author"))
        archive_title_source = normalize_archive_title_source(
            payload.get("archive_title_source")
        )
        if not source_link:
            raise WebUiApiError(
                "source_link_required",
                "Source link is required.",
                HTTPStatus.BAD_REQUEST,
            )
        if not target_link:
            raise WebUiApiError(
                "target_link_required",
                "Target link is required.",
                HTTPStatus.BAD_REQUEST,
            )
        self._require_deep_link_whitelist_if_enabled(resolve_deep_link)
        start_id = normalize_optional_int(payload.get("start_id"))
        end_id = normalize_optional_int(payload.get("end_id"))
        if (start_id is None) != (end_id is None):
            raise WebUiApiError(
                "range_ids_required",
                "Start ID and End ID must be provided together.",
                HTTPStatus.BAD_REQUEST,
            )
        source_is_message_link = is_message_link(source_link)
        if start_id is None and end_id is None and not source_is_message_link:
            start_id, end_id = self.detect_transfer_range(source_link)
        if start_id is not None and end_id is not None:
            if end_id < start_id:
                raise WebUiApiError(
                    "range_end_before_start",
                    "End ID must be greater than or equal to Start ID.",
                    HTTPStatus.BAD_REQUEST,
                )
            if source_is_message_link:
                raise WebUiApiError(
                    "range_source_must_be_chat_link",
                    "Range transfer source must be a chat link, not a message link.",
                    HTTPStatus.BAD_REQUEST,
                )
        from module.core.media_types import parse_media_types_payload

        media_types = parse_media_types_payload(payload.get("media_types"))
        task_id = self.store.create_task(
            source_link=source_link,
            target_link=target_link,
            target_profile=target_profile,
            start_id=start_id,
            end_id=end_id,
            include_comment=include_comment,
            resolve_deep_link=resolve_deep_link,
            archive_by_author=archive_by_author,
            archive_title_source=archive_title_source,
            media_types=media_types,
        )
        if self.task_submitter:
            self.task_submitter(task_id)
        return {"task_id": task_id}

    def detect_transfer_range(self, source_link: str) -> tuple[int, int]:
        detect = self._operation("detect_transfer_range")
        if not detect:
            raise WebUiApiError(
                "transfer_range_detection_unavailable",
                "Transfer range detection is unavailable.",
                HTTPStatus.BAD_REQUEST,
            )
        try:
            detected = normalize_detected_transfer_range(detect(source_link))
        except WebUiApiError:
            raise
        except Exception as e:
            raise WebUiApiError(
                "transfer_range_detection_failed",
                str(e) or "Transfer range detection failed.",
                HTTPStatus.BAD_REQUEST,
            ) from e
        if detected is None:
            raise WebUiApiError(
                "transfer_range_empty",
                "No accessible messages were found for the source.",
                HTTPStatus.BAD_REQUEST,
            )
        start_id, end_id = detected
        if start_id > end_id:
            raise WebUiApiError(
                "range_end_before_start",
                "End ID must be greater than or equal to Start ID.",
                HTTPStatus.BAD_REQUEST,
            )
        return start_id, end_id

    def list_watches(self, tz_offset_minutes: int | None = None) -> list:
        list_watches = self._operation("list_watches")
        if not list_watches:
            return []
        watches = list_watches(tz_offset_minutes=tz_offset_minutes)
        self.view_model.attach_download_counts_to_watches(watches)
        return watches

    def create_watch(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise WebUiApiError(
                "invalid_payload", "Invalid payload.", HTTPStatus.BAD_REQUEST
            )
        watch_type = str(payload.get("type") or "").strip()
        if watch_type not in ("download", "forward"):
            raise WebUiApiError(
                "invalid_watch_type",
                "Watch type must be download or forward.",
                HTTPStatus.BAD_REQUEST,
            )
        if watch_type == "download":
            source_links = payload.get("source_links")
            if isinstance(source_links, str):
                source_links = [source_links]
            source_links = [
                str(link).strip() for link in (source_links or []) if str(link).strip()
            ]
            if not source_links:
                raise WebUiApiError(
                    "watch_source_required",
                    "At least one source link is required.",
                    HTTPStatus.BAD_REQUEST,
                )
            from module.core.media_types import parse_media_types_payload

            for link in source_links:
                if not link.startswith("https://t.me/"):
                    raise WebUiApiError(
                        "invalid_watch_source",
                        "Watch source link must start with https://t.me/.",
                        HTTPStatus.BAD_REQUEST,
                    )
            payload = {
                **payload,
                "source_links": source_links,
                "archive_by_author": bool(payload.get("archive_by_author")),
                "archive_title_source": normalize_archive_title_source(
                    payload.get("archive_title_source")
                ),
                "media_types": parse_media_types_payload(payload.get("media_types")),
            }
        else:
            from module.core.media_types import parse_media_types_payload

            source_link = str(payload.get("source_link") or "").strip()
            target_link = str(payload.get("target_link") or "").strip()
            include_comment = bool(payload.get("include_comment"))
            resolve_deep_link = bool(payload.get("resolve_deep_link"))
            archive_by_author = bool(payload.get("archive_by_author"))
            archive_title_source = normalize_archive_title_source(
                payload.get("archive_title_source")
            )
            from module.transfer.comment_delay import (
                normalize_optional_comment_delay_minutes,
            )

            try:
                comment_delay_minutes = normalize_optional_comment_delay_minutes(
                    payload.get("comment_delay_minutes")
                )
            except ValueError:
                raise WebUiApiError(
                    "invalid_comment_delay_minutes",
                    "Comment delay must be empty (inherit) or an integer from 0 to 1440.",
                    HTTPStatus.BAD_REQUEST,
                )
            if not source_link:
                raise WebUiApiError(
                    "watch_source_required",
                    "Source link is required.",
                    HTTPStatus.BAD_REQUEST,
                )
            if not target_link:
                raise WebUiApiError(
                    "watch_target_required",
                    "Target link is required.",
                    HTTPStatus.BAD_REQUEST,
                )
            if not source_link.startswith("https://t.me/"):
                raise WebUiApiError(
                    "invalid_watch_source",
                    "Watch source link must start with https://t.me/.",
                    HTTPStatus.BAD_REQUEST,
                )
            if not target_link.startswith("https://t.me/"):
                raise WebUiApiError(
                    "invalid_watch_target",
                    "Watch target link must start with https://t.me/.",
                    HTTPStatus.BAD_REQUEST,
                )
            self._require_deep_link_whitelist_if_enabled(resolve_deep_link)
            payload = {
                **payload,
                "source_link": source_link,
                "target_link": target_link,
                "include_comment": include_comment,
                "resolve_deep_link": resolve_deep_link,
                "archive_by_author": archive_by_author,
                "archive_title_source": archive_title_source,
                "comment_delay_minutes": comment_delay_minutes,
                "media_types": parse_media_types_payload(payload.get("media_types")),
            }
        create_watch = self._operation("create_watch")
        if create_watch:
            try:
                return create_watch(payload)
            except ValueError as e:
                if str(e) == "watch_source_conflict":
                    raise WebUiApiError(
                        "watch_source_conflict",
                        "The same source cannot be watched by download and forward at the same time.",
                        HTTPStatus.CONFLICT,
                    )
                if str(e) == "watch_already_exists":
                    raise WebUiApiError(
                        "watch_already_exists",
                        "Watch already exists.",
                        HTTPStatus.CONFLICT,
                    )
                raise
        raise WebUiApiError(
            "watch_operations_unavailable",
            "Watch operations are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def update_watch(self, watch_id: str, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise WebUiApiError(
                "invalid_payload", "Invalid payload.", HTTPStatus.BAD_REQUEST
            )
        from module.core.media_types import parse_media_types_payload
        from module.transfer.comment_delay import (
            normalize_optional_comment_delay_minutes,
        )

        resolve_deep_link = bool(payload.get("resolve_deep_link"))
        self._require_deep_link_whitelist_if_enabled(resolve_deep_link)
        payload = {
            **payload,
            "resolve_deep_link": resolve_deep_link,
            "archive_by_author": bool(payload.get("archive_by_author")),
            "archive_title_source": normalize_archive_title_source(
                payload.get("archive_title_source")
            ),
            "media_types": parse_media_types_payload(payload.get("media_types")),
        }
        if "comment_delay_minutes" in payload:
            try:
                payload["comment_delay_minutes"] = (
                    normalize_optional_comment_delay_minutes(
                        payload.get("comment_delay_minutes")
                    )
                )
            except ValueError:
                raise WebUiApiError(
                    "invalid_comment_delay_minutes",
                    "Comment delay must be empty (inherit) or an integer from 0 to 1440.",
                    HTTPStatus.BAD_REQUEST,
                )
        update_watch = self._operation("update_watch")
        if update_watch:
            try:
                return update_watch(watch_id, payload)
            except ValueError as e:
                raise WebUiApiError(
                    "update_watch_failed", str(e), HTTPStatus.BAD_REQUEST
                )
        raise WebUiApiError(
            "watch_operations_unavailable",
            "Watch operations are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def delete_watch(self, watch_id: str) -> bool:
        delete_watch = self._operation("delete_watch")
        if delete_watch:
            return bool(delete_watch(watch_id))
        return False

    def export_forward_watches(self) -> dict:
        export_forward_watches = self._operation("export_forward_watches")
        if export_forward_watches:
            return export_forward_watches()
        raise WebUiApiError(
            "watch_operations_unavailable",
            "Watch operations are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def import_forward_watches(self, payload) -> dict:
        from module.transfer.forward_watch_backup import (
            normalize_forward_watch_entry,
            parse_forward_watch_import_payload,
        )

        entries, parse_errors = parse_forward_watch_import_payload(payload)
        fatal_codes = {
            "invalid_payload",
            "invalid_kind",
            "unsupported_version",
            "missing_watches",
            "invalid_watches",
        }
        for code in parse_errors:
            if code in fatal_codes:
                raise WebUiApiError(
                    code, "Invalid forward watch backup file.", HTTPStatus.BAD_REQUEST
                )

        result = {
            "created": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
            "watches": [],
        }
        for index, raw in enumerate(entries):
            entry = normalize_forward_watch_entry(raw)
            if not entry:
                result["failed"] += 1
                result["errors"].append({"index": index, "code": "invalid_entry"})
                continue
            try:
                created = self.create_watch({"type": "forward", **entry})
            except WebUiApiError as exc:
                if exc.error_code == "watch_already_exists":
                    result["skipped"] += 1
                    continue
                result["failed"] += 1
                error = {
                    "index": index,
                    "code": exc.error_code,
                    "message": exc.message,
                }
                if exc.error_code == "watch_source_conflict":
                    error["source_link"] = entry["source_link"]
                result["errors"].append(error)
                continue
            result["created"] += 1
            result["watches"].extend(created.get("watches") or [])
        return result

    def list_deferred_discussion_captures(self, watch_id: str) -> Optional[dict]:
        op = self._operation("list_deferred_discussion_captures")
        if not op:
            return {"captures": [], "total": 0}
        return op(watch_id)

    def cancel_deferred_discussion_capture(
        self, watch_id: str, capture_id: int
    ) -> bool:
        op = self._operation("cancel_deferred_discussion_capture")
        if not op:
            return False
        return bool(op(watch_id, capture_id))

    def run_deferred_discussion_capture_now(
        self, watch_id: str, capture_id: int
    ) -> bool:
        op = self._operation("run_deferred_discussion_capture_now")
        if not op:
            return False
        return bool(op(watch_id, capture_id))

    def retry_deferred_discussion_capture(self, watch_id: str, capture_id: int) -> bool:
        op = self._operation("retry_deferred_discussion_capture")
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
        status: str | None = None,
    ):
        list_watch_events = self._operation("list_watch_events")
        if list_watch_events:
            return list_watch_events(
                watch_id,
                limit=limit,
                offset=offset,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes,
                status=status,
            )
        return None

    def delete_task(self, task_id: int) -> bool:
        delete_web_task = self._operation("delete_web_task")
        if delete_web_task:
            return bool(delete_web_task(task_id))
        return self.store.delete_task(task_id)

    @staticmethod
    def parse_task_action_path(path: str):
        prefix = "/api/tasks/"
        if not path.startswith(prefix):
            return None
        parts = [part for part in path[len(prefix) :].split("/") if part]
        if len(parts) != 2 or not parts[0].isdigit():
            return None
        action = parts[1]
        if action not in ("pause", "resume", "retry-failed"):
            return None
        return int(parts[0]), action

    def apply_task_action(self, task_id: int, action: str) -> dict:
        if not self.store.get_task(task_id):
            raise WebUiApiError(
                "task_not_found", "Task not found.", HTTPStatus.NOT_FOUND
            )
        if action == "retry-failed":
            retry_failed_web_task = self._operation("retry_failed_web_task")
            if retry_failed_web_task:
                reset_items = int(retry_failed_web_task(task_id))
            else:
                reset_items = self.store.retry_failed_items(task_id)
                if reset_items and self.task_submitter:
                    self.task_submitter(task_id)
            return {"task_id": task_id, "action": action, "reset_items": reset_items}
        if action == "pause":
            pause_web_task = self._operation("pause_web_task")
            if pause_web_task:
                ok = bool(pause_web_task(task_id))
            else:
                self.store.update_task(task_id, status="paused")
                ok = True
            if not ok:
                raise WebUiApiError(
                    "task_action_failed", "Task action failed.", HTTPStatus.BAD_REQUEST
                )
            return {"task_id": task_id, "action": action}
        if action == "resume":
            resume_web_task = self._operation("resume_web_task")
            if resume_web_task:
                ok = bool(resume_web_task(task_id))
            else:
                self.store.update_task(task_id, status="pending")
                ok = True
                if self.task_submitter:
                    self.task_submitter(task_id)
            if not ok:
                raise WebUiApiError(
                    "task_action_failed", "Task action failed.", HTTPStatus.BAD_REQUEST
                )
            return {"task_id": task_id, "action": action}
        raise WebUiApiError(
            "invalid_task_action", "Invalid task action.", HTTPStatus.BAD_REQUEST
        )

    def statistics(self, tz_offset_minutes: int | None = None) -> dict:
        statistics = self._operation("statistics")
        if statistics:
            try:
                return statistics(tz_offset_minutes=tz_offset_minutes)
            except TypeError:
                return statistics()
        from module.adapters.webui.statistics_payload import build_statistics_payload

        store = getattr(self, "transfer_store", None)
        if store is not None:
            from module.adapters.webui.statistics_payload import DEFAULT_STATISTICS_WINDOW_DAYS

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
        list_operations = self._operation("list_operations")
        if list_operations:
            return list_operations(limit=limit)
        return []

    def export_table(self, table_type: str) -> dict:
        if table_type not in ("channel", "link", "count", "upload"):
            raise WebUiApiError(
                "invalid_table_type",
                "Table type must be channel, link, count, or upload.",
                HTTPStatus.BAD_REQUEST,
            )
        export_table = self._operation("export_table")
        if export_table:
            return export_table(table_type)
        raise WebUiApiError(
            "table_operations_unavailable",
            "Table operations are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def create_upload(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise WebUiApiError(
                "invalid_payload", "Invalid payload.", HTTPStatus.BAD_REQUEST
            )
        path = str(payload.get("path") or "").strip()
        target_link = str(payload.get("target_link") or "").strip()
        recursive = bool(payload.get("recursive"))
        if not path:
            raise WebUiApiError(
                "upload_path_required",
                "Upload path is required.",
                HTTPStatus.BAD_REQUEST,
            )
        if not target_link:
            raise WebUiApiError(
                "upload_target_required",
                "Target link is required.",
                HTTPStatus.BAD_REQUEST,
            )
        if not target_link.startswith("https://t.me/") and target_link not in (
            "me",
            "self",
        ):
            raise WebUiApiError(
                "invalid_upload_target",
                "Upload target must be a Telegram link, me, or self.",
                HTTPStatus.BAD_REQUEST,
            )
        normalized_path = os.path.abspath(os.path.expanduser(path))
        if not os.path.exists(normalized_path):
            raise WebUiApiError(
                "upload_path_not_found",
                "Upload path does not exist on the server.",
                HTTPStatus.BAD_REQUEST,
            )
        if recursive and not os.path.isdir(normalized_path):
            raise WebUiApiError(
                "upload_recursive_requires_directory",
                "Recursive upload requires a directory.",
                HTTPStatus.BAD_REQUEST,
            )
        payload = {
            **payload,
            "path": normalized_path,
            "target_link": target_link,
            "recursive": recursive,
        }
        create_upload = self._operation("create_upload")
        if create_upload:
            return create_upload(payload)
        raise WebUiApiError(
            "upload_operations_unavailable",
            "Upload operations are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def create_channel_download(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise WebUiApiError(
                "invalid_payload", "Invalid payload.", HTTPStatus.BAD_REQUEST
            )
        chat_link = str(payload.get("chat_link") or "").strip()
        if not chat_link:
            raise WebUiApiError(
                "channel_link_required",
                "Channel link is required.",
                HTTPStatus.BAD_REQUEST,
            )
        if not chat_link.startswith("https://t.me/"):
            raise WebUiApiError(
                "invalid_channel_link",
                "Channel link must start with https://t.me/.",
                HTTPStatus.BAD_REQUEST,
            )
        allowed_types = set(self.settings_schema()["download_type"])
        download_type = payload.get("download_type") or sorted(allowed_types)
        if isinstance(download_type, str):
            download_type = [download_type]
        download_type = [
            str(item).strip() for item in download_type if str(item).strip()
        ]
        if not download_type:
            raise WebUiApiError(
                "channel_download_type_required",
                "At least one download type is required.",
                HTTPStatus.BAD_REQUEST,
            )
        invalid_types = [item for item in download_type if item not in allowed_types]
        if invalid_types:
            raise WebUiApiError(
                "invalid_channel_download_type",
                "Invalid channel download type.",
                HTTPStatus.BAD_REQUEST,
            )
        keywords = payload.get("keywords") or []
        if isinstance(keywords, str):
            keywords = [part.strip() for part in keywords.split(",") if part.strip()]
        else:
            keywords = [str(part).strip() for part in keywords if str(part).strip()]
        normalized = {
            **payload,
            "chat_link": chat_link,
            "download_type": download_type,
            "keywords": keywords,
            "include_comment": bool(payload.get("include_comment")),
            "date_range": normalize_date_range(payload.get("date_range")),
        }
        create_channel_download = self._operation("create_channel_download")
        if create_channel_download:
            return create_channel_download(normalized)
        raise WebUiApiError(
            "channel_download_operations_unavailable",
            "Channel download operations are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def scan_media_for_cleanup(
        self,
        task_id: int = None,
        items_limit: int = None,
        items_offset: int = 0,
        orphans_limit: int = None,
        orphans_offset: int = 0,
    ) -> dict:
        scan_media_for_cleanup = self._operation("scan_media_for_cleanup")
        if scan_media_for_cleanup:
            return scan_media_for_cleanup(
                task_id=task_id,
                items_limit=items_limit,
                items_offset=items_offset,
                orphans_limit=orphans_limit,
                orphans_offset=orphans_offset,
            )
        raise WebUiApiError(
            "media_operations_unavailable",
            "Media operations are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def cleanup_media_files(self, payload: dict) -> dict:
        cleanup_media_files = self._operation("cleanup_media_files")
        if cleanup_media_files:
            return cleanup_media_files(payload)
        raise WebUiApiError(
            "media_operations_unavailable",
            "Media operations are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def list_archive_author_channels(self) -> dict:
        op = self._operation("list_archive_author_channels")
        if op:
            return op()
        raise WebUiApiError(
            "archive_author_unavailable",
            "Archive author tools are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def scan_archive_author_reorganize(self, payload: dict) -> dict:
        op = self._operation("scan_archive_author_reorganize")
        if op:
            return op(payload)
        raise WebUiApiError(
            "archive_author_unavailable",
            "Archive author tools are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def resolve_archive_author_reorganize(self, payload: dict) -> dict:
        op = self._operation("resolve_archive_author_reorganize")
        if op:
            return op(payload)
        raise WebUiApiError(
            "archive_author_unavailable",
            "Archive author tools are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def execute_archive_author_reorganize(self, payload: dict) -> dict:
        op = self._operation("execute_archive_author_reorganize")
        if op:
            return op(payload)
        raise WebUiApiError(
            "archive_author_unavailable",
            "Archive author tools are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def stop_archive_author_job(self, job_id: str) -> dict:
        op = self._operation("stop_archive_author_job")
        if op:
            return op(job_id)
        raise WebUiApiError(
            "archive_author_unavailable",
            "Archive author tools are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def list_archive_author_plan_moves(self, payload: dict) -> dict:
        op = self._operation("list_archive_author_plan_moves")
        if op:
            return op(payload)
        raise WebUiApiError(
            "archive_author_unavailable",
            "Archive author tools are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def get_archive_author_job(self, job_id: str) -> dict:
        op = self._operation("get_archive_author_job")
        if op:
            return op(job_id)
        raise WebUiApiError(
            "archive_author_unavailable",
            "Archive author tools are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def get_active_archive_author_job(self, channel_folder: str | None = None) -> dict:
        op = self._operation("get_active_archive_author_job")
        if op:
            return op(channel_folder)
        raise WebUiApiError(
            "archive_author_unavailable",
            "Archive author tools are unavailable.",
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def list_cleanup_logs(self) -> list:
        list_cleanup_logs = self._operation("list_cleanup_logs")
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
        tz_offset_minutes: int | None = None,
    ) -> dict:
        list_system_logs = self._operation("list_system_logs")
        if list_system_logs:
            return list_system_logs(
                limit=limit,
                offset=offset,
                category=category,
                level=level,
                trace_id=trace_id,
                watch_id=watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes,
            )
        if self.store and hasattr(self.store, "list_system_logs"):
            logs, total = self.store.list_system_logs(
                limit=limit,
                offset=offset,
                category=category,
                level=level,
                trace_id=trace_id,
                watch_id=watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes,
            )
            from module.persistence.system_log import annotate_system_logs_can_retry

            return {
                "logs": annotate_system_logs_can_retry(logs),
                "total": total,
                "limit": limit,
                "offset": offset,
                "retention_days": self.store.SYSTEM_LOGS_RETENTION_DAYS,
            }
        return {"logs": [], "total": 0, "limit": limit, "offset": offset}

    def retry_archive_from_system_log(self, log_id: int) -> dict:
        retry_fn = self._operation("retry_archive_from_system_log")
        if not retry_fn:
            raise WebUiApiError(
                "archive_retry_unavailable",
                "Archive retry is unavailable.",
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
        try:
            return retry_fn(int(log_id))
        except LookupError:
            raise WebUiApiError(
                "log_not_found",
                "System log not found.",
                HTTPStatus.NOT_FOUND,
            ) from None
        except ValueError as exc:
            code = str(exc) or "not_retryable"
            messages = {
                "not_retryable": "This system log cannot be retried.",
                "missing_metadata": "Archive retry metadata is incomplete.",
            }
            raise WebUiApiError(
                code if code in messages else "not_retryable",
                messages.get(code, "This system log cannot be retried."),
                HTTPStatus.BAD_REQUEST,
            ) from None
        except RuntimeError as exc:
            text = str(exc) or "archive_failed"
            if text == "retry_in_progress":
                raise WebUiApiError(
                    "retry_in_progress",
                    "Archive retry is already in progress.",
                    HTTPStatus.CONFLICT,
                ) from None
            raise WebUiApiError(
                "archive_failed",
                text,
                HTTPStatus.BAD_REQUEST,
            ) from None

    def export_system_logs(
        self,
        category: str | None = None,
        level: str | None = None,
        trace_id: str | None = None,
        watch_id: str | None = None,
        today_only: bool = False,
        tz_offset_minutes: int | None = None,
    ) -> str:
        export_system_logs = self._operation("export_system_logs")
        if export_system_logs:
            return export_system_logs(
                category=category,
                level=level,
                trace_id=trace_id,
                watch_id=watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes,
            )
        from module.persistence.system_log import build_system_logs_export_text

        if self.store and hasattr(self.store, "list_system_logs"):
            return build_system_logs_export_text(
                self.store,
                category=category,
                level=level,
                trace_id=trace_id,
                watch_id=watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes,
            )
        return ""

    def export_diagnostic_bundle(self, payload: dict | None = None) -> dict:
        export_fn = self._operation("export_diagnostic_bundle")
        if not export_fn:
            raise WebUiApiError(
                "diagnostic_export_unavailable",
                "诊断包导出不可用。",
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
        return export_fn(payload or {})

    def get_sanitized_settings(self) -> dict:
        return sanitize_settings(self.get_settings())

    def update_settings(self, payload: dict) -> dict:
        if self.settings_updater:
            return self.settings_updater(payload)
        return save_runtime_settings(payload)

    @staticmethod
    def settings_schema() -> dict:
        return {
            "download_type": [
                "video",
                "photo",
                "audio",
                "voice",
                "animation",
                "document",
                "video_note",
            ],
            "forward_type": [
                "video",
                "photo",
                "audio",
                "document",
                "voice",
                "text",
                "animation",
                "video_note",
            ],
            "message_filter": {
                "media_types": [
                    "video",
                    "photo",
                    "audio",
                    "document",
                    "voice",
                    "text",
                    "animation",
                    "video_note",
                ],
                "date_range": {"enabled": False},
                "keywords": {"enabled": False},
            },
            "upload_pending_limit": {"min": 1, "max": 5},
            "comment_delay_minutes": {"min": 0, "max": 1440},
            "transfer": {
                "item_stale_timeout_minutes": {"min": 1, "max": 180},
            },
            "deep_link": {
                "timeout_seconds": {"min": 1, "max": 600},
                "min_interval_seconds": {"min": 0, "max": 600},
            },
            "target_profiles": {"pikpak": {"max_file_size": {"min": 1}}},
            "sensitive_keys": sorted(SENSITIVE_SETTING_KEYS),
        }


def parse_optional_timestamp(value):
    if value in (None, ""):
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
        raise WebUiApiError(
            "invalid_date_range",
            "Date range values must be timestamps or ISO datetimes.",
            HTTPStatus.BAD_REQUEST,
        )


def normalize_date_range(value) -> dict:
    if not isinstance(value, dict):
        return {"start_date": None, "end_date": None}
    start_date = parse_optional_timestamp(value.get("start_date"))
    end_date = parse_optional_timestamp(value.get("end_date"))
    if start_date is not None and end_date is not None and end_date < start_date:
        raise WebUiApiError(
            "date_range_end_before_start",
            "Date range end must be greater than or equal to start.",
            HTTPStatus.BAD_REQUEST,
        )
    return {"start_date": start_date, "end_date": end_date}


def load_runtime_settings() -> dict:
    from module.core.config import GlobalConfig, UserConfig

    user = UserConfig()
    global_config = GlobalConfig()
    return {
        "user": {
            "config_path": user.config_path,
            "api_id": user.config.get("api_id"),
            "api_hash": user.config.get("api_hash"),
            "bot_token": user.config.get("bot_token"),
            "session_directory": user.config.get("session_directory"),
            "save_directory": user.config.get("save_directory"),
            "temp_directory": user.config.get("temp_directory"),
            "max_tasks": user.config.get("max_tasks"),
            "max_retries": user.config.get("max_retries"),
            "download_type": user.config.get("download_type"),
            "is_shutdown": user.config.get("is_shutdown"),
            "proxy": user.config.get("proxy"),
        },
        "global": global_config.config,
    }


def save_runtime_settings(payload: dict) -> dict:
    from module.core.config import GlobalConfig, UserConfig

    user = UserConfig()
    global_config = GlobalConfig()
    user_config = merge_allowed_settings(
        target=deepcopy(user.config),
        patch=payload.get("user", {}) if isinstance(payload, dict) else {},
        allowed={
            "api_id",
            "api_hash",
            "bot_token",
            "session_directory",
            "save_directory",
            "temp_directory",
            "max_tasks",
            "max_retries",
            "download_type",
            "is_shutdown",
            "proxy",
        },
        gc=global_config,
    )
    user_config = UserConfig.normalize_runtime_numbers(user_config)
    global_settings = merge_allowed_settings(
        target=deepcopy(global_config.config),
        patch=payload.get("global", {}) if isinstance(payload, dict) else {},
        allowed={
            "notice",
            "export_table",
            "upload",
            "forward_type",
            "target_profiles",
            "message_filter",
            "live_watch",
            "transfer",
            "deep_link",
        },
        gc=global_config,
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
                gc=gc,
            )
        elif key in SENSITIVE_SETTING_KEYS and value in (None, ""):
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
            return new_val.lower() in ("true", "1", "yes", "on")
        return bool(new_val)
    if target_type is list and isinstance(new_val, str):
        # textarea / comma fields: avoid list("a\\nb") character-splitting
        return [
            part.strip()
            for part in new_val.replace(",", "\n").split("\n")
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


def get_web_host_from_env(default: str = "127.0.0.1") -> str:
    return os.environ.get(ENVIRON.TRMD_WEB_HOST, default)


def get_web_username_from_env() -> Optional[str]:
    return os.environ.get(ENVIRON.TRMD_WEB_USERNAME)


def get_web_password_from_env() -> Optional[str]:
    return os.environ.get(ENVIRON.TRMD_WEB_PASSWORD)
