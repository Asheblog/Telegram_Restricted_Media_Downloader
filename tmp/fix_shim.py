# coding=UTF-8
"""修正兼容 shim：直接显式转发模块级名字，不做花样。"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
SRC = REPO / "module" / "adapters" / "webui" / "operations.py"

SHIM = '''# coding=UTF-8
"""兼容 shim —— 实现已迁到 ``module.webops.operations``（编排层）。

保留本路径的原因：测试用例通过字符串 patch 目标引用本模块
（``module.adapters.webui.operations.PARSE_ARGS`` / ``.TransferStore`` /
``.WebUiServer`` / ``.parse_link``），改名会让这些 patch 静默失效。
本文件只转发名字，不含任何实现。
"""
from module.webops.operations import *  # noqa: F401,F403
from module.webops.operations import (  # noqa: F401
    _WEB_UI_DELEGATE_METHODS,
    ORPHAN_CLEANUP_INTERVAL_SECONDS,
    WebOperationsFacade,
    WebOperationsMixin,
    _require_web_task_manager,
)

# 以下名字在实现模块里是被 import 进来的；测试把它当 patch 目标（字符串路径），
# 因此必须在本模块命名空间可见，否则 patch 会静默失效（打到不存在的属性上）。
from module.webops.operations import (  # noqa: F401
    CommentDelayScheduler,
    GlobalConfig,
    MediaManager,
    PARSE_ARGS,
    PikpakIntegrationManager,
    TransferStatus,
    TransferStore,
    UserConfig,
    WebUiServer,
    is_docker,
    parse_link,
)
'''
SRC.write_text(SHIM, encoding="utf-8")
print("shim rewritten:", len(SHIM.splitlines()), "lines")
