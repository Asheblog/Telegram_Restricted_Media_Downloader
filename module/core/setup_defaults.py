# coding=UTF-8
"""Core setup defaults: Telegram API credential check + --web first-run defaults.

Moved out of ``adapters.webui.setup`` so ``core`` no longer depends on the
webui adapter (layering inversion fix, arch-decouple Phase 2a). The webui
setup module re-exports these for back-compat.
"""
import os


def has_telegram_api_credentials(config: dict | None) -> bool:
    if not isinstance(config, dict):
        return False
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    if api_id in (None, "", 0, "0") or api_hash in (None, ""):
        return False
    try:
        int(api_id)
    except (TypeError, ValueError):
        return False
    return len(str(api_hash).strip()) >= 16


def apply_web_safe_user_defaults(config: dict) -> dict:
    """Fill non-interactive defaults for --web first run. Never prompts stdin."""
    if not isinstance(config, dict):
        return config
    dirs = _default_directories()
    if not config.get("save_directory"):
        config["save_directory"] = dirs["save_directory"]
    if not config.get("session_directory"):
        config["session_directory"] = dirs["session_directory"]
    if not config.get("temp_directory"):
        config["temp_directory"] = dirs["temp_directory"]
    if not config.get("download_type"):
        config["download_type"] = [
            "video", "photo", "document", "audio", "voice", "animation", "video_note"
        ]
    if config.get("is_shutdown") is None:
        config["is_shutdown"] = False
    proxy = config.get("proxy")
    if not isinstance(proxy, dict):
        proxy = {}
        config["proxy"] = proxy
    if proxy.get("enable_proxy") is None:
        proxy["enable_proxy"] = False
    max_tasks = config.get("max_tasks")
    if not isinstance(max_tasks, dict):
        max_tasks = {}
        config["max_tasks"] = max_tasks
    max_tasks.setdefault("download", 1)
    max_tasks.setdefault("upload", 1)
    max_retries = config.get("max_retries")
    if not isinstance(max_retries, dict):
        max_retries = {}
        config["max_retries"] = max_retries
    if max_retries.get("download") is None:
        max_retries["download"] = 5
    if max_retries.get("upload") is None:
        max_retries["upload"] = 3
    return config


def _default_directories() -> dict:
    if os.path.isdir("/app"):
        return {
            "save_directory": "/app/downloads",
            "session_directory": "/app/sessions",
            "temp_directory": "/app/temp",
        }
    cwd = os.getcwd()
    return {
        "save_directory": os.path.join(cwd, "downloads"),
        "session_directory": os.path.join(cwd, "sessions"),
        "temp_directory": os.path.join(cwd, "temp"),
    }


__all__ = ["has_telegram_api_credentials", "apply_web_safe_user_defaults"]
