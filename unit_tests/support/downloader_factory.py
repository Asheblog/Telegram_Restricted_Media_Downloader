# coding=UTF-8
"""测试用宿主工厂：收口 ``object.__new__(TelegramRestrictedMediaDownloader)`` 手工装配。

## 为什么需要它
解耦审查实测：单元测试里有 **90 处** ``object.__new__(TelegramRestrictedMediaDownloader)``
后逐个塞属性（``transfer_store`` / ``loop`` / ``app`` / ``web_task_queue`` …），
其中最重的用法还**自己重抄了一遍宿主接线**（例如某测试里 25 行的
``WebUITaskManager(transfer_store_getter=…, loop_getter=…, …)``）。
后果有三：
1. 宿主新增一个必需属性时，测试不会失败，而是在运行期 ``AttributeError``；
2. 同一份接线散落在多个测试文件里，改一处要改多处；
3. 测试与"宿主有哪些属性"这个内部细节强耦合，正是上帝对象难拆的根因。

本模块把这些装配收口到一处：``build_downloader()`` 给出**一个可直接使用**的宿主，
并用 ``**overrides`` 支持测试只覆盖自己关心的那几项。

## 用法
```python
from unit_tests.support.downloader_factory import build_downloader

downloader = build_downloader(transfer_store=store)          # 最常用
downloader = build_downloader(with_task_manager=True, loop=loop)
```

注意：本模块在**函数内**导入宿主，避免 import 期触发 ``module.utils.parser``
的 ``argv`` 解析（那会让单独跑某个测试文件时 pytest 直接报 unrecognized arguments）。
"""
from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace
from typing import Any, Optional

__all__ = [
    "attach_task_manager",
    "attach_stub_task_manager",
    "build_downloader",
    "import_downloader_class",
]


def attach_stub_task_manager(downloader: Any, store: Any):
    """给宿主接一个"最小可用"的 WebUITaskManager（各 getter 返回空/None）。

    测试只需要 `web_task_manager` 存在时用这个，而不是每个文件再抄一遍
    十几个 `lambda: None` 的构造参数。需要真实行为时用 ``attach_task_manager``
    并显式传对应 getter。
    """
    from module.webops.task_manager import WebUITaskManager

    manager = WebUITaskManager(
        transfer_store_getter=lambda: store,
        diagnostic=SimpleNamespace(),
        loop_getter=lambda: None,
        web_task_queue=asyncio.Queue(),
        web_submitted_task_ids=set(),
        web_running_task_getter=lambda: None,
        web_running_task_setter=lambda value: None,
        web_running_task_id_getter=lambda: None,
        web_running_task_id_setter=lambda value: None,
        web_operation_queue=asyncio.Queue(),
        web_operations={},
    )
    downloader.web_task_manager = manager
    return manager


def _clean_argv_import(importer):
    """在干净 argv 下执行 import（parser 在 import 期解析 argv）。"""
    original = sys.argv
    sys.argv = [original[0]]
    try:
        return importer()
    finally:
        sys.argv = original


def import_downloader_class():
    """返回 ``TelegramRestrictedMediaDownloader`` 类（import 期 argv 已清理）。"""
    return _clean_argv_import(
        lambda: __import__(
            "module.downloader", fromlist=["TelegramRestrictedMediaDownloader"]
        ).TelegramRestrictedMediaDownloader
    )


def attach_task_manager(
    downloader: Any,
    store: Any,
    *,
    diagnostic: Any = None,
    loop: Any = None,
    web_task_queue: Any = None,
    web_operation_queue: Any = None,
    web_operations: Optional[dict] = None,
    submitted_task_ids: Optional[set] = None,
    **extra: Any,
):
    """按生产装配的同一套参数给宿主接上 ``WebUITaskManager``。

    与 ``composition_root`` 的接线保持同名形参，因此"宿主需要哪些 getter"
    这件事只在这里写一次。
    """
    from module.webops.task_manager import WebUITaskManager

    if web_task_queue is None:
        web_task_queue = getattr(downloader, "web_task_queue", None) or asyncio.Queue()
    if web_operation_queue is None:
        web_operation_queue = (
            getattr(downloader, "web_operation_queue", None) or asyncio.Queue()
        )
    if web_operations is None:
        web_operations = getattr(downloader, "web_operations", None) or {}
    if submitted_task_ids is None:
        submitted_task_ids = getattr(downloader, "web_submitted_task_ids", None) or set()

    manager = WebUITaskManager(
        transfer_store_getter=lambda: store,
        diagnostic=diagnostic if diagnostic is not None else SimpleNamespace(),
        loop_getter=lambda: loop,
        web_task_queue=web_task_queue,
        web_submitted_task_ids=submitted_task_ids,
        web_running_task_getter=lambda: getattr(downloader, "web_running_task", None),
        web_running_task_setter=lambda value: setattr(
            downloader, "web_running_task", value
        ),
        web_running_task_id_getter=lambda: getattr(
            downloader, "web_running_task_id", None
        ),
        web_running_task_id_setter=lambda value: setattr(
            downloader, "web_running_task_id", value
        ),
        web_operation_queue=web_operation_queue,
        web_operations=web_operations,
        uploader_getter=lambda: getattr(downloader, "uploader", None),
        **extra,
    )
    downloader.web_task_manager = manager
    return manager


def build_downloader(
    *,
    transfer_store: Any = None,
    app: Any = None,
    gc: Any = None,
    loop: Any = None,
    with_task_manager: bool = False,
    with_runtime_slots: bool = True,
    **overrides: Any,
):
    """构造一个可直接使用的宿主（绕过真实构造函数，与既有测试同一路径）。

    只填**必需且安全**的槽位；其余留给调用方用 ``**overrides`` 覆盖，
    避免工厂变成"又一个什么都塞的大对象"。
    """
    downloader_class = import_downloader_class()
    downloader = object.__new__(downloader_class)
    downloader.transfer_store = transfer_store
    downloader.loop = loop
    downloader.app = app if app is not None else SimpleNamespace(client=None)
    if gc is not None:
        downloader.gc = gc
    if with_runtime_slots:
        downloader.web_task_queue = asyncio.Queue()
        downloader.web_operation_queue = asyncio.Queue()
        downloader.web_submitted_task_ids = set()
        downloader.web_operations = {}
        downloader.web_running_task = None
        downloader.web_running_task_id = None
    for name, value in overrides.items():
        setattr(downloader, name, value)
    if with_task_manager:
        attach_task_manager(downloader, transfer_store, loop=loop)
    return downloader
