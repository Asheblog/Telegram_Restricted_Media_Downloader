# coding=UTF-8
"""WebUI 字符串派发契约测试。

背景（解耦审查结论）：WebUI 的调用链是
``handlers -> WebUiServer.<method> -> self._operation("名字") -> WebOperationsFacade``，
而 facade 的 40 个方法是在 ``operations.py`` 末尾用 ``setattr`` 反射生成的。
名字是字符串，写错时旧实现返回 ``None``，上层把它报成 503
「operations unavailable」—— 接线 bug 被伪装成服务故障。

本用例锁两件事：
1. server 里出现的每个 ``_operation("...")`` 名字都必须在 facade 上真的存在；
2. facade 在、名字不存在时必须显式失败（500 + operation_not_wired），不得退化成 503。
"""
import ast
import pathlib
import re
import sys
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]

from module.webops.operations import (  # noqa: E402
    WebOperationsFacade,
    _WEB_UI_DELEGATE_METHODS,
)
from module.adapters.webui.contracts import WebUiApiError
from module.adapters.webui.server import WebUiServer  # noqa: E402
# noqa: E402

sys.argv = _ORIGINAL_ARGV

SERVER_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "module" / "adapters" / "webui" / "server.py"
)
# facade 的实现已迁到编排层（webops），派发契约要对着实现文件断言。
FACADE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "module" / "webops" / "operations.py"
)


class WebUiDispatchContractCase(unittest.TestCase):
    def test_every_operation_name_exists_on_the_facade(self):
        """server 里每个 _operation("x") 的 x 都必须能被 facade 解析。"""
        source = SERVER_PATH.read_text(encoding="utf-8")
        names = set(re.findall(r"""_operation\(\s*["']([^"']+)["']\s*\)""", source))
        self.assertTrue(names, "未在 server.py 中找到任何 _operation 调用点")
        surface = set(_WEB_UI_DELEGATE_METHODS)
        missing = sorted(names - surface)
        self.assertEqual(
            [], missing,
            f"这些 _operation 名字在 WebOperationsFacade 上不存在：{missing}",
        )

    def test_facade_generates_every_declared_name(self):
        """facade 的 40 个方法都是 setattr 生成的，必须一个不少地挂上。"""
        missing = [n for n in _WEB_UI_DELEGATE_METHODS if not callable(getattr(WebOperationsFacade, n, None))]
        self.assertEqual([], missing)
        # 类体里不应出现"手写"的业务方法（只有 __init__）。
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "WebOperationsFacade":
                defined = [
                    child.name for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                self.assertEqual(["__init__"], defined)

    @staticmethod
    def _operations_stub():
        class _Ops:
            def create_upload(self, payload):
                return {"ok": payload}

        return _Ops()

    def test_missing_name_fails_loudly_instead_of_faking_a_503(self):
        """facade 在、方法名不存在 -> 500 operation_not_wired，而不是 503。"""
        server = WebUiServer(store=None, operations=self._operations_stub())
        self.assertTrue(callable(server._operation("create_upload")))
        with self.assertRaises(WebUiApiError) as ctx:
            server._operation("create_upload_typo")
        self.assertEqual("operation_not_wired", ctx.exception.error_code)
        self.assertEqual(500, ctx.exception.status)

    def test_unwired_operations_still_returns_none(self):
        """整套 operations 未接线（合法情形）仍返回 None，交给调用方回 503。"""
        server = WebUiServer(store=None, operations=None)
        self.assertIsNone(server._operation("create_upload"))


if __name__ == "__main__":
    unittest.main()
