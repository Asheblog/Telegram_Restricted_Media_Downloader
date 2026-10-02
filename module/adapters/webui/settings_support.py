# coding=UTF-8
"""WebUI 的环境变量读取与运行时设置合并/读写。

从 ``server.py`` **逐字搬移**：这一组是"配置面"，与 HTTP 请求编排无关 ——
环境变量决定监听地址/凭证，``merge_allowed_settings`` 决定哪些设置键可被改。

`merge_allowed_settings` 另被 ``webops.settings_operations`` 使用，
因此放在这里（而不是 server）能让 webops 不必依赖 1,900 行的 HTTP 模块。
"""
from __future__ import annotations

import json
from copy import deepcopy
from typing import Optional

import os

from module.adapters.webui.contracts import SENSITIVE_SETTING_KEYS, sanitize_settings
from module.core.enums import ENVIRON


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
