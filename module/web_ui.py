# coding=UTF-8
"""Compatibility shim — implementation in module.adapters.webui.server."""
from module.adapters.webui.server import (  # noqa: F401
    WebUiServer,
    WebUiApiError,
    AuthProvider,
    get_web_host_from_env,
    get_web_password_from_env,
    get_web_port_from_env,
    get_web_username_from_env,
    merge_allowed_settings,
    sanitize_settings,
    parse_optional_timestamp,
    normalize_date_range,
    load_runtime_settings,
    save_runtime_settings,
    normalize_optional_int,
    is_message_link,
    normalize_detected_transfer_range,
)
