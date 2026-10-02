# coding=UTF-8
"""门面委托契约守卫：45 个单语句转发方法的目标链必须**可解析且可调用**。

## 为什么需要
`TelegramRestrictedMediaDownloader` 是刻意保留的宽门面（89 个方法，其中 45 个是
单语句转发）。转发本身不是问题 —— 问题是**转发目标可能悄悄失效**：
被委托的服务方法改了名/被删了，门面方法仍然"看起来存在"，只在真实调用时才炸。
本仓库已有同类先例：`WebOperationsFacade` 的 `_WEB_UI_DELEGATE_METHODS`、
`WebTransferHost` 的 Protocol 契约守卫。

## 做法
用 AST 取出每个转发方法的目标链（如 `self._ensure_transfer_runner().wait_between_transfer_messages`），
在**用工厂装配好的真实实例**上解析该链，断言终点可调用。
不 mock 任何东西 —— 目标是验证"真实对象上这些委托成立"。
"""
import ast
import pathlib
import sys
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOWNLOADER = ROOT / "module" / "downloader.py"

# 这些方法的"目标链"不是普通属性路径，无法用统一方式解析，
# 逐个登记并说明为什么跳过（避免守卫把无关写法误判为失效）。
SKIP: dict[str, str] = {}

CLASS_NAME = "TelegramRestrictedMediaDownloader"


def _chain(node: ast.AST) -> list[str] | None:
    """把 `self._ensure_x().m` / `self.a.b` 还原成 ["_ensure_x", None, "m"] 形式。

    返回 None 表示无法解析（含非 self 起点、下标、调用实参等）。
    """
    # 剥掉外层调用（保留"这是一次调用"的信息）
    path: list[str] = []
    cur = node
    while True:
        if isinstance(cur, ast.Call):
            path.append(None)  # 标记：这里是一次调用
            cur = cur.func
            continue
        if isinstance(cur, ast.Attribute):
            path.append(cur.attr)
            cur = cur.value
            continue
        break
    if not isinstance(cur, ast.Name) or cur.id != "self":
        return None
    path.reverse()
    # 去掉开头多余的 call 标记
    while path and path[0] is None:
        path.pop(0)
    return path


def _delegation_targets() -> dict[str, list[str]]:
    tree = ast.parse(DOWNLOADER.read_text(encoding="utf-8"))
    cls = next(
        n
        for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == CLASS_NAME
    )
    out: dict[str, list[str]] = {}
    for c in cls.body:
        if not isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if c.name in SKIP:
            continue
        body = [
            s
            for s in c.body
            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
        ]
        if len(body) != 1 or not isinstance(body[0], ast.Return):
            continue
        expr = body[0].value
        if isinstance(expr, ast.Await):
            expr = expr.value
        if not isinstance(expr, ast.Call):
            continue
        path = _chain(expr.func)
        if path:
            out[c.name] = path
    return out


class FacadeDelegationContractCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.targets = _delegation_targets()
        cls.assertTrue(cls.targets, "未解析到任何委托方法 —— 解析器可能失效")

        # 用工厂装配实例。转发目标多为 _ensure_* 懒建协作者，
        # 因此需要一个"够用"的宿主：不跑 __init__，补最小装配态。
        from unit_tests.support.downloader_factory import build_downloader

        cls.host = build_downloader(with_task_manager=True)

    def test_every_delegation_resolves_to_a_callable(self):
        from module.adapters.pikpak.integration import PikpakIntegrationManager
        from module.transfer.runner import WebTransferRunner

        host = self.host
        # 转发目标经 `_ensure_*` 懒建。这里只预置两个"会被懒建"的协作者：
        # runner（纯对象）与 pikpak_manager（构造会碰 rclone/网络，故显式给替身参数）。
        # `transfer_engine` 不预置 —— 它是只读属性，且组合根已支持裸宿主
        # （`_create_standalone_transfer_engine` 内部全用 getattr 兜底）。
        host._transfer_runner = WebTransferRunner(host=host)
        host._pikpak_manager_impl = PikpakIntegrationManager(
            transfer_store_getter=lambda: host.transfer_store,
            pikpak_archive_client_getter=lambda: None,
            diagnostic=getattr(host, "diagnostic", None),
            gc_getter=lambda: getattr(host, "gc", None),
            refresh_counts=lambda task_id: None,
            cleanup_item_file=lambda *a, **k: None,
            app_getter=lambda: getattr(host, "app", None),
            system_log=None,
            schedule_deferred_archive=lambda **k: None,
        )

        unresolvable = []
        for method, path in sorted(self.targets.items()):
            with self.subTest(method=method, path=".".join(str(p) for p in path)):
                try:
                    resolved = self._resolve(host, path)
                except Exception as exc:  # noqa: BLE001 - 记录即可
                    unresolvable.append(f"{method} -> {path}: {type(exc).__name__}: {exc}")
                    continue
                if not callable(resolved):
                    unresolvable.append(f"{method} -> {path}: 解析结果不可调用（{resolved!r}）")
        self.assertEqual(
            [],
            unresolvable,
            "这些门面转发方法的目标链无法解析或不可调用：\n  "
            + "\n  ".join(unresolvable),
        )

    @staticmethod
    def _resolve(host, path):
        current = host
        for step in path:
            if step is None:
                current = current()  # 中间调用（如 _ensure_x()）
                continue
            if step.startswith("__") and not step.endswith("__"):
                # Python 名称改写：类内写 `obj.__x` 实际访问 `obj._Cls__x`。
                # 本守卫用 getattr 动态解析，必须自己补上改写，否则会误报。
                owner = type(current).__name__
                current = getattr(current, f"_{owner}{step}")
                continue
            current = getattr(current, step)
        return current


if __name__ == "__main__":
    unittest.main()
