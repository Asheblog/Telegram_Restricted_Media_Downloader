# coding=UTF-8
"""WebUI adapter 的共享叶子契约。

这里只放 **不依赖任何其它 webui 模块** 的最小契约：HTTP handler 与 HTTP 壳
（``server.py``）都需要它们，但如果 handler 反过来 import ``server``，就会形成
``server -> handlers`` / ``handlers -> server`` 的模块级导入环（实测确实存在）。

抽到叶子模块后：
- ``handlers/*`` 只依赖本模块，不再依赖 2033 行的 ``server``；
- ``server`` 从本模块导入，不再把这两个符号定义在自己身上；
- ``server`` 仍 re-export 这两个名字，兼容既有 `from ...server import ...` 写法。
"""
from http import HTTPStatus

SENSITIVE_SETTING_KEYS = {"api_hash", "bot_token", "password", "username"}

# WebUI SPA 视图路径（刷新后由前端按 pathname 恢复对应视图）
SPA_VIEW_PATHS = frozenset(
    {
        "/",
        "/index.html",
        "/transfers",
        "/watches",
        "/downloads-uploads",
        "/statistics",
        "/records",
        "/media",
        "/archive-organize",
        "/system-logs",
        "/settings",
        "/profile",
    }
)


def is_spa_page_path(path: str) -> bool:
    """Whether a GET path should serve the SPA shell (not /api or static files)."""
    if not path:
        return True
    if path.startswith("/api/") or path.startswith("/fonts/"):
        return False
    normalized = path.rstrip("/") or "/"
    if normalized in SPA_VIEW_PATHS or path == "/index.html":
        return True
    leaf = normalized.rsplit("/", 1)[-1]
    if leaf and "." in leaf:
        return False
    # Unknown path without extension: still serve SPA so client can rewrite.
    return True


class WebUiApiError(Exception):
    """HTTP 层可预期的业务错误：handler 与 server 共用，故置于叶子模块。"""

    def __init__(
        self, error_code: str, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status = status


def sanitize_settings(value):
    """递归脱敏：敏感字段只回传「是否已配置」，不回传内容。"""
    if isinstance(value, dict):
        result = {}
        for key, nested in value.items():
            if key in SENSITIVE_SETTING_KEYS:
                result[key] = {"configured": bool(nested), "value": ""}
            else:
                result[key] = sanitize_settings(nested)
        return result
    if isinstance(value, list):
        return [sanitize_settings(item) for item in value]
    return value


__all__ = [
    "SENSITIVE_SETTING_KEYS",
    "SPA_VIEW_PATHS",
    "WebUiApiError",
    "is_spa_page_path",
    "sanitize_settings",
]
