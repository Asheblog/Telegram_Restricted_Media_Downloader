# coding=UTF-8
"""把 operations 实现搬到 module/webops/operations.py，旧路径留兼容 shim。"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
SRC = REPO / "module" / "adapters" / "webui" / "operations.py"
DST = REPO / "module" / "webops" / "operations.py"

text = SRC.read_text(encoding="utf-8")

OLD_DOC = '"""Web UI operations facade — IWebUiOperations / IWatchOps / ITaskOps seam."""'
NEW_DOC = (
    '"""WebUI 业务操作编排 —— IWebUiOperations / IWatchOps / ITaskOps 的实现。\n'
    "\n"
    "从 adapters/webui 迁出（原先与 HTTP 壳同目录）：本文件零 HTTP 原语，承载任务队列、\n"
    "监听、账号与安装向导、媒体清理、归档编排、诊断导出、统计等业务编排。\n"
    "\n"
    "放在 webops 编排层是刻意的依赖方向：编排组合适配器，而不是反过来。\n"
    "architecture_guard 的 test_no_layer_inversions 已登记该层（adapters 不得 import webops）。\n"
    "\n"
    "旧路径 module/adapters/webui/operations.py 保留为兼容 shim（测试里的 patch 目标\n"
    "依赖该字符串路径）。\n"
    '"""'
)
assert OLD_DOC in text, "docstring anchor missing"
text = text.replace(OLD_DOC, NEW_DOC, 1)

DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_text(text, encoding="utf-8")
print(f"moved -> {DST.name}: {len(text.splitlines())} lines")

# 旧路径写成兼容 shim
SHIM = '''# coding=UTF-8
"""兼容 shim —— 实现已迁到 ``module.webops.operations``（编排层）。

保留本路径的原因：测试用例通过字符串 patch 目标引用本模块
（``module.adapters.webui.operations.PARSE_ARGS`` / ``.TransferStore`` /
``.WebUiServer`` / ``.parse_link``），改名会让这些 patch 静默失效。
本文件只做名字转发，不含实现。
"""
from module.webops.operations import *  # noqa: F401,F403
from module.webops.operations import (  # noqa: F401
    PARSE_ARGS,
    TransferStore,
    WebOperationsFacade,
    WebOperationsMixin,
    WebUiServer,
    _ensure_transfer_store,
    _require_web_task_manager,
    parse_link,
)
'''
SRC.write_text(SHIM, encoding="utf-8")
print(f"shim  -> {SRC.name}: {len(SHIM.splitlines())} lines")
