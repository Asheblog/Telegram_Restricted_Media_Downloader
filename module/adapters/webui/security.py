# coding=UTF-8
"""WebUI HTTP 层安全策略。

集中三件事，供 HTTP handler 复用：

1. ``security_headers`` / ``hsts_enabled`` —— 每个响应都附带防嵌套、防嗅探、
   referrer 收紧的响应头；HSTS 只在「确认走 HTTPS」或「非 loopback 的生产姿态」
   下下发，避免明文跳转上白下发（RFC 6797 §7.2）。
2. ``cookie_secure_required`` —— 会话 Cookie 是否加 ``Secure``。判定顺序：
   显式 ``TRMD_WEB_COOKIE_SECURE`` → 代理 ``X-Forwarded-Proto`` → 直连 TLS →
   非 loopback 监听 / 存在反向代理头。本地 ``127.0.0.1`` 明文开发不会被误伤
   （浏览器会丢弃明文下发的 Secure Cookie）。
3. ``LoginThrottle`` —— 登录失败按「客户端 IP + 用户名」双维度窗口限流 + 指数退避。

本模块不 import ``module.adapters.webui.server``，避免与 handler 形成导入环。
"""

from __future__ import annotations

import collections
import ipaddress
import math
import os
import ssl
import threading
import time
from collections.abc import Callable
from urllib.parse import urlparse

from module.core.enums import ENVIRON

# 所有响应统一附带的安全头。
# 注意：CSP 只收口 frame-ancestors / base-uri / form-action / object-src，
# 不设置 default-src / script-src —— WebUI 的 SPA 与登录页都把脚本内联在 HTML 里。
SECURITY_HEADERS: tuple[tuple[str, str], ...] = (
    ("x-content-type-options", "nosniff"),
    ("x-frame-options", "DENY"),
    (
        "content-security-policy",
        (
            "frame-ancestors 'none'; base-uri 'self'; "
            "form-action 'self'; object-src 'none'"
        ),
    ),
    ("referrer-policy", "no-referrer"),
    ("permissions-policy", "geolocation=(), camera=(), microphone=()"),
)

HSTS_HEADER: tuple[str, str] = (
    "strict-transport-security",
    "max-age=31536000; includeSubDomains",
)

FORWARDED_PROTO_HEADER = "x-forwarded-proto"
PROXY_HINT_HEADERS = ("x-forwarded-for", "x-real-ip", "forwarded", "x-forwarded-host")

_TRUTHY = frozenset({"1", "true", "yes", "on", "enable", "enabled", "secure"})
_FALSY = frozenset({"0", "false", "no", "off", "disable", "disabled", "insecure"})


def _env_raw(name: str) -> str:
    return str(os.environ.get(name) or "").strip().lower()


def _env_flag(name: str, *, default: bool) -> bool:
    raw = _env_raw(name)
    if not raw:
        return default
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    return default


def _env_float(
    name: str, default: float, *, minimum: float = 0.0, maximum: float = 86400.0
) -> float:
    try:
        value = float(_env_raw(name) or default)
    except (TypeError, ValueError):
        return default
    return float(min(max(value, minimum), maximum))


def _env_int(name: str, default: int, *, minimum: int = 1, maximum: int = 100000) -> int:
    try:
        value = int(float(_env_raw(name) or default))
    except (TypeError, ValueError):
        return default
    return int(min(max(value, minimum), maximum))


def _header(handler, name: str) -> str:
    """Header lookup that also survives stdlib parse failures (``headers is None``)."""
    headers = getattr(handler, "headers", None)
    if headers is None:
        return ""
    return str(headers.get(name) or "")


def forwarded_proto(handler) -> str:
    """First hop of ``X-Forwarded-Proto`` (lower-case), or ``""``."""
    return _header(handler, FORWARDED_PROTO_HEADER).split(",")[0].strip().lower()


def is_tls_connection(handler) -> bool:
    return isinstance(getattr(handler, "connection", None), ssl.SSLSocket)


def is_proxied_request(handler) -> bool:
    """Whether the request carries reverse-proxy hop headers."""
    return any(_header(handler, name) for name in PROXY_HINT_HEADERS)


def request_is_https(handler) -> bool:
    """Positive HTTPS signal: proxy says https, or the socket itself is TLS."""
    proto = forwarded_proto(handler)
    if proto == "https":
        return True
    if proto == "http":
        return False
    return is_tls_connection(handler)


def hsts_enabled(handler, *, requires_auth: bool = False) -> bool:
    """HSTS is emitted only when the response really travelled over TLS.

    ``requires_auth`` (non-loopback listener) plus a proxy hop is treated as a
    TLS-terminated deployment: the WebUI is documented to sit behind a reverse
    proxy for remote access. Plain-HTTP clients ignore HSTS per RFC 6797 §7.2,
    so this cannot break a plain-HTTP LAN deployment.
    """
    proto = forwarded_proto(handler)
    if proto == "https":
        return True
    if proto == "http":
        return False
    if is_tls_connection(handler):
        return True
    return bool(requires_auth and is_proxied_request(handler))


def security_headers(handler, *, requires_auth: bool = False) -> list[tuple[str, str]]:
    """Headers appended to every response by the handler's ``end_headers``."""
    headers = list(SECURITY_HEADERS)
    if hsts_enabled(handler, requires_auth=requires_auth):
        headers.append(HSTS_HEADER)
    return headers


def cookie_secure_required(handler, *, requires_auth: bool = False) -> bool:
    """Whether the session cookie must carry the ``Secure`` attribute."""
    raw = _env_raw(ENVIRON.TRMD_WEB_COOKIE_SECURE)
    if raw:
        return raw in _TRUTHY
    proto = forwarded_proto(handler)
    if proto == "https":
        return True
    if proto == "http":
        return False
    if is_tls_connection(handler):
        return True
    if requires_auth:
        # 绑在非 loopback 地址上：按 ADR-0003 属于生产部署，默认要求 HTTPS。
        return True
    return is_proxied_request(handler)


def _normalize_netloc(netloc: str, scheme: str) -> str:
    netloc = netloc.strip().lower().rstrip(".")
    host_part, sep, port = netloc.rpartition(":")
    if (
        sep
        and port.isdigit()
        and (scheme, port) in (("https", "443"), ("http", "80"))
    ):
        return host_part
    return netloc


def _is_local_host(hostname: str) -> bool:
    """Whether a netloc host is loopback / private / link-local."""
    hostname = hostname.strip().strip("[]").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return bool(address.is_loopback or address.is_private or address.is_link_local)


def is_cross_origin_request(handler) -> bool:
    """Whether a browser-supplied ``Origin``/``Referer`` points at another site.

    比对基准是 ``Host`` 与 ``X-Forwarded-Host``。两种刻意的宽松处理：

    - 不带这两个头的非浏览器客户端（curl、脚本、单元测试）直接放行；
    - 反代把 ``Host`` 改写成回环 / 内网地址（nginx `proxy_pass` 且未
      `proxy_set_header Host $host` 时的默认行为）时**无法判断真实站点**，
      此时放行而不是把正常登录 403 掉——会话 Cookie 仍是 `SameSite=Lax`，
      跨站表单 POST 本身拿不到会话。

    需要严格模式（含回环 Host 也拒绝）或排障时可设
    ``TRMD_WEB_CSRF_ORIGIN_CHECK=off`` 关闭该检查。
    """
    if _env_raw(ENVIRON.TRMD_WEB_CSRF_ORIGIN_CHECK) in _FALSY:
        return False
    source = (_header(handler, "origin") or _header(handler, "referer")).strip()
    if not source:
        return False
    if source.lower() == "null":
        return True
    parsed = urlparse(source)
    if not parsed.netloc:
        return False
    origin_netloc = _normalize_netloc(parsed.netloc, parsed.scheme)
    known = tuple(
        netloc
        for netloc in (
            _normalize_netloc(_header(handler, "host"), parsed.scheme),
            _normalize_netloc(
                _header(handler, "x-forwarded-host").split(",", 1)[0], parsed.scheme
            ),
        )
        if netloc
    )
    if not known:
        return False
    if origin_netloc in known:
        return False
    # 反代把 Host 改写成了回环 / 内网地址时无法判断真实站点，放行。
    return not all(_is_local_host(netloc.rsplit(":", 1)[0]) for netloc in known)


class _Bucket:
    """Failure window + lockout state for one dimension value."""

    __slots__ = ("failures", "last_seen", "locked_until", "strikes")

    def __init__(self) -> None:
        self.failures: collections.deque[float] = collections.deque()
        self.locked_until: float = 0.0
        self.strikes: int = 0
        self.last_seen: float = 0.0


class LoginThrottle:
    """登录失败限流：IP + 用户名双维度窗口计数，超阈值后指数退避锁定。

    - 只统计**失败**尝试：凭据正确时直接放行并清空计数，攻击者无法靠打满
      限流把管理员锁在门外（避免把反爆破做成可用性攻击）。
    - 任一维度超过 ``max_failures`` 即进入锁定窗口；重复触发时窗口翻倍，
      上限 ``max_lockout_seconds``；长时间静默后 strikes 复位。
    - 线程安全：``ThreadingHTTPServer`` 每个连接一个线程。
    """

    def __init__(
        self,
        *,
        max_failures: int = 5,
        window_seconds: float = 60.0,
        lockout_seconds: float = 60.0,
        max_lockout_seconds: float = 900.0,
        max_tracked: int = 4096,
        clock: Callable[[], float] = time.monotonic,
        on_lockout: Callable[[list[tuple[str, int]]], None] | None = None,
    ) -> None:
        self.max_failures = int(max(1, max_failures))
        self.window_seconds = float(max(1.0, window_seconds))
        self.lockout_seconds = float(max(1.0, lockout_seconds))
        self.max_lockout_seconds = float(max(self.lockout_seconds, max_lockout_seconds))
        self.max_tracked = int(max(16, max_tracked))
        self._clock = clock
        self._on_lockout = on_lockout
        self._buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    @classmethod
    def from_env(
        cls,
        *,
        clock: Callable[[], float] = time.monotonic,
        on_lockout: Callable[[list[tuple[str, int]]], None] | None = None,
    ) -> LoginThrottle | None:
        """Build the throttle from environment, or ``None`` when disabled."""
        if not _env_flag(ENVIRON.TRMD_WEB_LOGIN_RATELIMIT, default=True):
            return None
        return cls(
            max_failures=_env_int(ENVIRON.TRMD_WEB_LOGIN_MAX_FAILURES, 5, minimum=1, maximum=1000),
            window_seconds=_env_float(
                ENVIRON.TRMD_WEB_LOGIN_WINDOW_SECONDS, 60.0, minimum=1.0, maximum=3600.0
            ),
            lockout_seconds=_env_float(
                ENVIRON.TRMD_WEB_LOGIN_LOCKOUT_SECONDS, 60.0, minimum=1.0, maximum=3600.0
            ),
            max_lockout_seconds=_env_float(
                ENVIRON.TRMD_WEB_LOGIN_MAX_LOCKOUT_SECONDS, 900.0, minimum=1.0, maximum=86400.0
            ),
            clock=clock,
            on_lockout=on_lockout,
        )

    @staticmethod
    def _keys(client_ip: str, username: str) -> tuple[str, ...]:
        keys: list[str] = []
        if client_ip:
            keys.append(f"ip:{client_ip}")
        if username:
            keys.append(f"user:{username.strip().lower()}")
        return tuple(keys)

    def retry_after(self, client_ip: str, username: str) -> int:
        """Seconds the caller must wait; ``0`` means the attempt is allowed."""
        now = self._clock()
        with self._lock:
            return self._retry_after_locked(now, self._keys(client_ip, username))

    def record_failure(self, client_ip: str, username: str) -> int:
        """Count one failed attempt and return the resulting retry-after seconds."""
        now = self._clock()
        keys = self._keys(client_ip, username)
        locked: list[tuple[str, int]] = []
        with self._lock:
            remaining = self._retry_after_locked(now, keys)
            if remaining:
                return remaining
            for key in keys:
                bucket = self._buckets.get(key)
                if bucket is None:
                    bucket = _Bucket()
                    self._buckets[key] = bucket
                if bucket.last_seen and now - bucket.last_seen > self.max_lockout_seconds:
                    bucket.strikes = 0
                bucket.last_seen = now
                bucket.failures.append(now)
                while bucket.failures and now - bucket.failures[0] > self.window_seconds:
                    bucket.failures.popleft()
                if len(bucket.failures) >= self.max_failures:
                    bucket.strikes += 1
                    delay = min(
                        self.lockout_seconds * (2 ** (bucket.strikes - 1)),
                        self.max_lockout_seconds,
                    )
                    bucket.locked_until = now + delay
                    bucket.failures.clear()
                    locked.append((key, math.ceil(delay)))
            self._enforce_capacity(now)
        if locked and self._on_lockout:
            self._on_lockout(locked)
        return max((seconds for _, seconds in locked), default=0)

    def record_success(self, client_ip: str, username: str) -> None:
        with self._lock:
            for key in self._keys(client_ip, username):
                self._buckets.pop(key, None)

    def _retry_after_locked(self, now: float, keys: tuple[str, ...]) -> int:
        seconds = 0.0
        for key in keys:
            bucket = self._buckets.get(key)
            if bucket is not None and bucket.locked_until > now:
                seconds = max(seconds, bucket.locked_until - now)
        return math.ceil(seconds)

    def _enforce_capacity(self, now: float) -> None:
        for key in [
            key
            for key, bucket in self._buckets.items()
            if not bucket.failures
            and bucket.locked_until <= now
            and now - bucket.last_seen > self.window_seconds
        ]:
            self._buckets.pop(key, None)
        overflow = len(self._buckets) - self.max_tracked
        if overflow <= 0:
            return
        for key, _ in sorted(self._buckets.items(), key=lambda item: item[1].last_seen)[:overflow]:
            self._buckets.pop(key, None)
