# coding=UTF-8
"""WebUITaskManager 接线守门。

背景（解耦审查结论）：同一个 ``WebUITaskManager`` 有两处构造——
``composition_root.py`` 的主路径与 ``adapters/webui/operations.py`` 的兜底路径，
两处参数集不一致（27 项 vs 21 项）。差异本身在生产不可达（host 同名方法优先），
但真实风险是：**给 web_task_manager 新增一个必需 getter 却忘了在某处接线，
故障是静默的**（功能直接不生效，没有异常）。

本用例把不变量固定下来：
1. 构造器里每个 ``*_getter`` 形参，在 composition_root 的实例化处都必须
   **显式点名**（传值或显式 None），不允许遗漏；
2. 声明为显式 None 的必须是"有内置兜底实现"的可选项——一旦某处把它改成
   内部无兜底的必需依赖，这里会失败，提醒接线方补上。
"""
import ast
import pathlib
import re
import unittest

MODULE_DIR = pathlib.Path(__file__).resolve().parents[1] / "module"
TASK_MANAGER = MODULE_DIR / "webops" / "task_manager.py"
COMPOSITION_ROOT = MODULE_DIR / "composition_root.py"

# 有内置兜底实现、因此允许显式传 None 的形参。
OPTIONAL_GETTERS = {
    "should_continue_web_transfer_task_getter",  # None -> 回落到 transfer_store 判定
    "listener_restart_callback",
}

# 有内置兜底实现、因此允许在 composition_root 里完全省略的形参
# （不传即取默认 None，行为与显式传 None 等价）。
OMITTABLE_GETTERS = {
    # 省略时回落到 uploader.pause_uploads_for_task / cancel_uploads_for_task
    "cancel_task_downloads_getter",
    "cancel_task_uploads_getter",
    "pause_task_uploads_getter",
}


def _init_getter_params() -> set[str]:
    tree = ast.parse(TASK_MANAGER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "WebUITaskManager":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                    args = child.args
                    names = [a.arg for a in args.args + args.kwonlyargs]
                    return {n for n in names if n.endswith("_getter") or n == "listener_restart_callback"}
    raise AssertionError("未找到 WebUITaskManager.__init__")


def _composition_root_kwargs() -> dict[str, str]:
    """取 composition_root 里 WebUITaskManager(...) 的实参名 -> 源码文本。"""
    source = COMPOSITION_ROOT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        if name != "WebUITaskManager":
            continue
        kwargs = {}
        for kw in node.keywords:
            if kw.arg:
                kwargs[kw.arg] = ast.get_source_segment(source, kw.value) or ""
        return kwargs
    raise AssertionError("composition_root.py 里找不到 WebUITaskManager 实例化")


class WebUiTaskManagerWiringCase(unittest.TestCase):
    def test_every_getter_is_explicitly_wired_or_declared_optional(self):
        declared = _init_getter_params()
        wired = _composition_root_kwargs()
        missing = sorted(declared - set(wired) - OMITTABLE_GETTERS)
        self.assertEqual(
            [], missing,
            "WebUITaskManager 的这些 getter 在 composition_root 未接线（会静默失效）："
            f"{missing}",
        )

    def test_explicitly_none_getters_are_the_documented_optional_ones(self):
        wired = _composition_root_kwargs()
        explicit_none = {k for k, v in wired.items() if v.strip() == "None"}
        unexpected = sorted(explicit_none - OPTIONAL_GETTERS)
        self.assertEqual(
            [], unexpected,
            "这些 getter 被显式传 None，但不在'有内置兜底'清单里；"
            f"要么补上真实取值，要么确认后加入 OPTIONAL_GETTERS：{unexpected}",
        )

    def test_getter_params_are_not_silently_dropped_by_the_constructor(self):
        """构造器必须把每个 getter 形参存下来（避免漏赋值导致调用期 AttributeError）。"""
        source = TASK_MANAGER.read_text(encoding="utf-8")
        body = source.split("def __init__", 1)[1].split("\n    def ", 1)[0]
        for name in sorted(_init_getter_params()):
            self.assertIn(
                name, body,
                f"构造器签名声明了 {name}，但方法体里未使用它",
            )

    def test_no_unknown_kwarg_is_passed(self):
        """反向检查：接线处不能传构造器不接受的参数（改名后能立刻发现）。"""
        declared = _init_getter_params()
        tree = ast.parse(TASK_MANAGER.read_text(encoding="utf-8"))
        all_params = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "WebUITaskManager":
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                        all_params = {
                            a.arg for a in child.args.args + child.args.kwonlyargs
                        }
        wired = _composition_root_kwargs()
        unknown = sorted(set(wired) - all_params)
        self.assertEqual(
            [], unknown,
            f"composition_root 传了构造器不接受的参数：{unknown}（形参已改名？）",
        )
        self.assertTrue(declared, "未解析到任何 getter 形参，检查解析逻辑")


if __name__ == "__main__":
    unittest.main()
