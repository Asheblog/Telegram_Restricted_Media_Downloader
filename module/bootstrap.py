# coding=UTF-8
"""Runtime bootstrap: all import-time side effects, explicitly invoked.

Importing this module is side-effect-free. Call :func:`initialize` once at the
process entry point (and from the composition root as an idempotent fallback)
to reproduce the historical behaviour of ``import module``.
"""
import atexit
import logging
import os
import threading
import time
from glob import glob
from logging.handlers import TimedRotatingFileHandler
from typing import TypeGuard, cast

import yaml
from rich.logging import RichHandler

from module.constants import (
    APPDATA_PATH,
    CONSOLE_LOG_LEVEL,
    CustomDumper,
    GLOBAL_CONFIG_PATH,
    INPUT_HISTORY_PATH,
    LOG_CLEANUP_INTERVAL_SECONDS,
    LOG_FORMAT,
    LOG_PATH,
    LOG_RETENTION_DAYS,
    LOG_TIME_FORMAT,
    MAX_RECORD_LENGTH,
    PLATFORM,
    SOFTWARE_SHORT_NAME,
    __update_date__,
    __version__,
    console,
    log,
)

_initialized = False
_init_lock = threading.Lock()
_log_cleanup_thread_started = False
_log_cleanup_lock = threading.Lock()

_VALID_LOG_LEVELS = (
    "CRITICAL",
    "FATAL",
    "ERROR",
    "WARN",
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
)


def read_input_history(history_path: str, max_record_len: int, **kwargs) -> None:
    if kwargs.get("platform") == "Windows":
        # 尝试读取历史记录文件。
        import readline  # type: ignore[import-not-found]

        readline.backend = "readline"  # type: ignore[attr-defined]
        try:  # noqa: SIM105
            readline.read_history_file(history_path)  # type: ignore[attr-defined]
        except FileNotFoundError:
            pass
        # 设置历史记录的最大长度。
        readline.set_history_length(max_record_len)  # type: ignore[attr-defined]
        # 注册退出时保存历史记录。
        atexit.register(readline.write_history_file, history_path)  # type: ignore[attr-defined]


def via_log_level(
    log_level: str | None,
    param_name: str,
    global_config: dict,
    default_level: int = logging.INFO,
) -> TypeGuard[str]:
    if log_level not in _VALID_LOG_LEVELS:
        try:
            with open(file=GLOBAL_CONFIG_PATH, mode="w", encoding="UTF-8") as file:
                global_config[param_name] = logging.getLevelName(default_level)
                yaml.dump(global_config, file)
        except OSError:
            pass
        return False
    return True


def cleanup_old_log_files(
    log_path: str = LOG_PATH,
    retention_days: int = LOG_RETENTION_DAYS,
    now: float | None = None,
) -> int:
    cutoff = (time.time() if now is None else now) - max(
        0, retention_days
    ) * 24 * 60 * 60
    removed = 0
    for candidate in glob(f"{log_path}.*"):
        if not os.path.isfile(candidate):
            continue
        try:  # noqa: SIM105
            if os.path.getmtime(candidate) < cutoff:
                os.remove(candidate)
                removed += 1
        except OSError:
            pass
    return removed


def start_periodic_log_cleanup(
    log_path: str = LOG_PATH,
    retention_days: int = LOG_RETENTION_DAYS,
    interval_seconds: int = LOG_CLEANUP_INTERVAL_SECONDS,
) -> None:
    """Start a daemon thread that removes rotated log files daily."""
    global _log_cleanup_thread_started
    with _log_cleanup_lock:
        if _log_cleanup_thread_started:
            return
        _log_cleanup_thread_started = True

    def _loop() -> None:
        while True:
            time.sleep(interval_seconds)
            try:  # noqa: SIM105
                cleanup_old_log_files(log_path=log_path, retention_days=retention_days)
            except OSError:
                pass

    threading.Thread(
        target=_loop,
        name="trmd-log-cleanup",
        daemon=True,
    ).start()


def initialize() -> None:
    """Perform all runtime side effects once. Idempotent."""
    global _initialized
    with _init_lock:
        if _initialized:
            return
        _initialized = True

    os.makedirs(APPDATA_PATH, exist_ok=True)  # v1.2.6修复初次运行打开报错问题。

    read_input_history(
        history_path=INPUT_HISTORY_PATH,
        max_record_len=MAX_RECORD_LENGTH,
        platform=PLATFORM,
    )

    cleanup_old_log_files()

    # 配置日志文件处理器(文件记录)
    file_log_level = logging.getLevelName(logging.INFO)
    console_log_level = logging.getLevelName(CONSOLE_LOG_LEVEL)
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(file=GLOBAL_CONFIG_PATH, encoding="UTF-8") as f:
                global_config = yaml.safe_load(f) or {}
            file_log_level_str = cast(
                "str | None", global_config.get("file_log_level")
            )
            console_log_level_str = cast(
                "str | None", global_config.get("console_log_level")
            )
            if via_log_level(
                log_level=file_log_level_str,
                param_name="file_log_level",
                global_config=global_config,
                default_level=logging.INFO,
            ):
                file_log_level = logging.getLevelName(file_log_level_str)
            if via_log_level(
                log_level=console_log_level_str,
                param_name="console_log_level",
                global_config=global_config,
                default_level=logging.WARNING,
            ):
                console_log_level = logging.getLevelName(console_log_level_str)
        except Exception:
            pass

    file_handler = TimedRotatingFileHandler(
        filename=LOG_PATH,
        when="midnight",
        interval=1,
        backupCount=LOG_RETENTION_DAYS,
        encoding="UTF-8",
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s" + " " + LOG_FORMAT, datefmt=LOG_TIME_FORMAT
        )
    )
    file_handler.setLevel(file_log_level)

    # 配置日志终端记录器(控制台输出)
    console_handler = RichHandler(
        level=console_log_level,  # 控制台只显示WARNING及以上级别。
        console=console,
        rich_tracebacks=True,
        show_path=False,
        omit_repeated_times=True,
        log_time_format=LOG_TIME_FORMAT,
    )
    # 配置日志记录器(根记录器设置为最低级别 DEBUG)
    logging.basicConfig(
        level=logging.DEBUG,  # 根记录器设置为DEBUG,允许所有日志通过。
        format=LOG_FORMAT,
        datefmt=LOG_TIME_FORMAT,
        handlers=[
            console_handler,  # 控制台:WARNING+
            file_handler,  # 文件:INFO+
        ],
    )
    log.info(f"{SOFTWARE_SHORT_NAME}:{__version__},更新日期:{__update_date__}。")
    log.info(f'文件日志等级:"{logging.getLevelName(file_log_level)}"。')
    log.info(f'终端日志等级:"{logging.getLevelName(console_log_level)}"。')
    start_periodic_log_cleanup()
    CustomDumper.add_representer(type(None), CustomDumper.represent_none)


__all__ = [
    "initialize",
    "read_input_history",
    "via_log_level",
    "cleanup_old_log_files",
    "start_periodic_log_cleanup",
]
