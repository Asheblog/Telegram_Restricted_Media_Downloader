# coding=UTF-8
"""组合根 getter 的"静默兜底"边界守卫。

## 为什么需要
`TrmdCompositionRoot` 里有一批协作方 getter。它们此前**统一**用
`getattr(self, "x", None)` 兜底，效果是把"初始化顺序写错"伪装成"能力缺失"：
下游拿到 None，于是走降级路径，而不是报错。

收紧（去掉兜底）这件事必须区分两类属性，否则会把真实降级路径打断：
- **构造期必赋值**（`__init__` 里 `self.x = self._new_*()`）：收紧后顺序错误
  会立刻 AttributeError —— 这是我们要的；
- **运行期才装配**（`transfer_store` / `user` / `uploader` / `my_id`）：
  首次访问前确实不存在，必须继续返回 None，否则"尚未装配"会变成崩溃。

本用例把这条边界**钉死**：谁被收紧、谁保留兜底，各自断言其行为。
这类守卫的价值在于 —— 若有人日后"统一"改回 getattr 兜底，或把运行期属性的
兜底也删掉，都会立刻失败。
"""
import sys
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


def _bare_root():
    """构造一个**不跑 __init__** 的组合根实例（模拟半构造宿主）。"""
    from module.composition_root import TrmdCompositionRoot

    return object.__new__(TrmdCompositionRoot)


class StrictGetterBoundaryCase(unittest.TestCase):
    """构造期必赋值的 getter：缺属性必须报错，不能静默 None。"""

    STRICT = (
        ("_app", "app"),
        ("_gc", "gc"),
        ("_loop", "loop"),
        ("_pb", "pb"),
        ("_watch_manager", "watch_manager"),
        ("_pikpak_manager", "pikpak_manager"),
        ("_progress_tracker", "progress_tracker"),
    )

    def test_strict_getters_raise_when_attribute_missing(self):
        for getter_name, attr in self.STRICT:
            with self.subTest(getter=getter_name):
                root = _bare_root()
                getter = getattr(root, getter_name)
                try:
                    value = getter()
                except AttributeError:
                    continue  # 期望：立刻报错
                self.fail(
                    f"{getter_name}() 在缺少 {attr} 时静默返回了 {value!r}；"
                    "该属性由 __init__ 保证存在，兜底会把初始化顺序错误藏起来"
                )

    def test_strict_getters_return_the_assigned_object(self):
        for getter_name, attr in self.STRICT:
            with self.subTest(getter=getter_name):
                root = _bare_root()
                marker = SimpleNamespace(name=attr)
                setattr(root, attr, marker)
                self.assertIs(
                    marker,
                    getattr(root, getter_name)(),
                    f"{getter_name}() 没有返回 self.{attr}",
                )


class TolerantGetterBoundaryCase(unittest.TestCase):
    """运行期才装配的 getter：缺属性必须返回 None（这是真实降级路径）。

    注意这里**刻意只列真正返回 None 的**：`_pikpak_archive_client` 看起来同类，
    实则内建了 `DisabledPikpakArchiveClient()` 兜底（一个"显式禁用"对象，
    与 None 语义不同），因此不在本清单 —— 断言它返回 None 会失败。
    """

    TOLERANT = (
        ("_transfer_store", "transfer_store", None),
        ("_runtime_user", "user", None),
        ("_uploader", "uploader", None),
        ("_my_id", "my_id", 0),
    )

    def test_tolerant_getters_return_default_when_missing(self):
        for getter_name, attr, default in self.TOLERANT:
            with self.subTest(getter=getter_name):
                root = _bare_root()
                getter = getattr(root, getter_name, None)
                if getter is None:
                    self.skipTest(f"{getter_name} 不存在")
                self.assertEqual(
                    default,
                    getter(),
                    f"{getter_name}() 在缺少 {attr} 时应返回 {default!r} —— "
                    "这些属性是运行期才装配的，首次访问前不存在是正常状态",
                )

    def test_pikpak_archive_client_falls_back_to_explicit_disabled_client(self):
        """它不属于上面那类：兜底是"显式禁用"对象，而不是 None。

        这个区别有实际意义 —— 调用方按"能拿到一个客户端"写，
        `DisabledPikpakArchiveClient` 会明确拒绝归档，而 None 会变成 AttributeError。
        """
        root = _bare_root()
        client = root._pikpak_archive_client()
        self.assertIsNotNone(
            client, "_pikpak_archive_client 应兜底为显式禁用的客户端而不是 None"
        )
        self.assertTrue(
            hasattr(client, "archive_file"),
            "兜底客户端必须仍具备 archive_file 接口，否则调用方会 AttributeError",
        )


class RequireFactoriesStillWorkCase(unittest.TestCase):
    """`_require_*` 仍须在缺属性时现场构造（恢复路径依赖这个能力）。"""

    def test_require_watch_manager_builds_when_missing(self):
        root = _bare_root()
        root.diagnostic = SimpleNamespace()
        root.transfer_store = None
        root.user = None
        manager = root._require_watch_manager()
        self.assertIsNotNone(manager, "_require_watch_manager 没有现场构造")
        self.assertIs(manager, root.watch_manager, "构造后没有回写到 self.watch_manager")


if __name__ == "__main__":
    unittest.main()
