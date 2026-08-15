# coding=UTF-8
"""Package entry — re-exports constants and bootstrap symbols.

Importing ``module`` (or any submodule) is now side-effect-free: no directory
creation, file I/O, or thread spawning. Runtime side effects are performed by
``module.bootstrap.initialize`` (idempotent), invoked from the process entry
point and the composition root. See ``docs/specs/arch-decouple-phases.md``.
"""

import yaml  # noqa: F401  (re-exported for back-compat: ``from module import yaml``)

from module.bootstrap import (  # noqa: F401
    cleanup_old_log_files,
    initialize,
    read_input_history,
    start_periodic_log_cleanup,
    via_log_level,
)
from module.constants import (  # noqa: F401
    APPDATA_PATH,
    AUTHOR,
    CONSOLE_LOG_LEVEL,
    FILE_LOG_LEVEL,
    GLOBAL_CONFIG_NAME,
    GLOBAL_CONFIG_PATH,
    INPUT_HISTORY_PATH,
    LINK_PREVIEW_OPTIONS,
    LOG_CLEANUP_INTERVAL_SECONDS,
    LOG_FORMAT,
    LOG_PATH,
    LOG_RETENTION_DAYS,
    LOG_TIME_FORMAT,
    MAX_RECORD_LENGTH,
    PLATFORM,
    README,
    SLEEP_THRESHOLD,
    SOFTWARE_FULL_NAME,
    SOFTWARE_SHORT_NAME,
    CustomDumper,
    __copyright__,
    __license__,
    __update_date__,
    __version__,
    console,
    log,
)

__all__ = [
    "console",
    "log",
    "SLEEP_THRESHOLD",
    "AUTHOR",
    "__version__",
    "__license__",
    "__update_date__",
    "__copyright__",
    "SOFTWARE_FULL_NAME",
    "SOFTWARE_SHORT_NAME",
    "APPDATA_PATH",
    "GLOBAL_CONFIG_NAME",
    "GLOBAL_CONFIG_PATH",
    "PLATFORM",
    "INPUT_HISTORY_PATH",
    "MAX_RECORD_LENGTH",
    "LOG_PATH",
    "LOG_RETENTION_DAYS",
    "LOG_CLEANUP_INTERVAL_SECONDS",
    "LINK_PREVIEW_OPTIONS",
    "LOG_FORMAT",
    "FILE_LOG_LEVEL",
    "CONSOLE_LOG_LEVEL",
    "CustomDumper",
    "README",
    "initialize",
    "read_input_history",
    "via_log_level",
    "cleanup_old_log_files",
    "start_periodic_log_cleanup",
]
