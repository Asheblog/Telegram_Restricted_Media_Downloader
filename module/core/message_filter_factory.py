# coding=UTF-8
"""MessageFilter 工厂 — 媒体类型白名单与过滤器的装配点。

放在这里而不是 ``media_types.py``，是为了打断
``media_types -> filter -> media_types`` 导入环（架构守卫实测报出）：

- 本模块**只依赖 filter 与 media_types 两者**，自身不被任何地方反向依赖；
- ``media_types.py`` 不再 import ``MessageFilter``；
- ``build_runtime_message_filter`` 仅由本模块提供，调用方直接引用这个装配点。
"""
from __future__ import annotations

from typing import Any

from module.core.filter import MessageFilter
from module.core.media_types import resolve_allowed_media_types


def build_runtime_message_filter(
        message_filter_config: Any = None,
        media_types_override: Any = None,
) -> MessageFilter:
    """按 Media Type Allowlist（可带任务级 override）装配 MessageFilter。"""
    config = dict(message_filter_config or {})
    config['media_types'] = resolve_allowed_media_types(
        config.get('media_types'),
        media_types_override,
    )
    return MessageFilter(config)


__all__ = ["build_runtime_message_filter"]
