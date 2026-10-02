# coding=UTF-8
"""Protocol 契约守卫：`WebTransferHost` 声明的能力必须与生产宿主真实提供的一致。

## 为什么需要
`module/transfer/runner.py` 里定义了 `WebTransferHost` Protocol（17 个成员），
而 runner 大量用 `getattr(host, 'x', None)` 软探测取宿主能力。审计把这类软探测
记为"68 处、需逐点判定可选/必需"—— 逐点判是**做不完且会反复腐烂**的。

本用例换一个可执行的判据：**Protocol 是声明的契约，就把它当契约来验证**。
- Protocol 声明了某成员，生产宿主（`TrmdCompositionRoot`）就必须真的提供它 ——
  否则声明是空头支票，而软探测会让缺失静默通过；
- 这样一旦有人改了宿主方法名却忘了改 Protocol（或反之），用例立刻失败，
  而不是等到运行期 `getattr` 返回 None 走进降级分支。

这比"逐个给 getattr 加断言"更耐用：它盯的是**契约**，不是某一处调用点。
"""
import ast
import pathlib
import sys
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

RUNNER_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "module"
    / "transfer"
    / "runner.py"
)

# Protocol 里有几项是**实例属性**（装配期赋值），类上不会有定义，
# 因此不能用 `hasattr(type(host), name)` 校验。逐项列出并注明来源，
# 这样"哪些是属性、哪些是方法"本身也是被文档化的契约。
INSTANCE_ATTRIBUTES: dict[str, str] = {
    "app": "TrmdCompositionRoot.__init__ 装配的 Application",
    "gc": "TrmdCompositionRoot.__init__ 装配的 GlobalConfig",
    "loop": "TrmdCompositionRoot.__init__ 解析/自建的事件循环",
    "transfer_store": "start_web_ui 时创建的 TransferStore（此前为 None）",
    "uploader": "运行期按需装配的 TelegramUploader（首启向导完成前为 None）",
}

RUNTIME_ONLY: dict[str, str] = {}


def _protocol_members(protocol_name: str) -> set[str]:
    """取 Protocol 类自身声明的成员名（不含 dunder、不含继承来的 object 成员）。"""
    tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    members: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == protocol_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("__"):
                        members.add(item.name)
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    members.add(item.target.id)
    return members


class WebTransferHostContractCase(unittest.TestCase):
    """Protocol 声明的成员，生产宿主必须提供。"""

    def setUp(self):
        self.members = _protocol_members("WebTransferHost")
        self.assertTrue(
            self.members,
            "未从 runner.py 解析到 WebTransferHost 的任何成员 —— "
            "要么 Protocol 被删/改名，要么本用例的解析需要更新",
        )

    def _production_host_class(self):
        """生产宿主类（真正被 runner 当作 host 的那个）。

        注意不是 `TrmdCompositionRoot`：runner 的 host 是**门面**
        `TelegramRestrictedMediaDownloader`（`composition_root` 组装它，
        并把 `self` 传给 runner 作 host —— 见 composition_root 的
        `WebTransferRunner(host=self)`，其中 self 是门面实例）。
        本用例按"Protocol 声明的成员能否在该类上解析"来验契约。
        """
        from unit_tests.support.downloader_factory import import_downloader_class

        return import_downloader_class()

    def test_production_host_provides_every_protocol_member(self):
        host_class = self._production_host_class()
        missing = []
        for name in sorted(self.members):
            if name in RUNTIME_ONLY:
                continue
            if hasattr(host_class, name):
                continue
            if name in INSTANCE_ATTRIBUTES:
                continue  # 实例属性，类上没有定义是正常的
            missing.append(name)
        self.assertEqual(
            [],
            missing,
            "WebTransferHost 声明了这些成员，但既不在生产宿主类上定义、也不在"
            f"INSTANCE_ATTRIBUTES 里登记：{missing}。软探测（getattr(host, x, None)）"
            "会让缺失静默通过，所以必须在这里拦住 —— 请让宿主实现它们，"
            "或把它们从 Protocol 移除/登记为实例属性。",
        )

    def test_instance_attribute_allowlist_has_no_stale_entries(self):
        """allowlist 不能腐烂：登记为实例属性的名字，必须真的不是类成员。

        否则哪天它变成了类方法，allowlist 会继续替它掩盖问题。
        """
        host_class = self._production_host_class()
        stale = [
            name
            for name in INSTANCE_ATTRIBUTES
            if name in self.members and hasattr(host_class, name)
        ]
        self.assertEqual(
            [],
            stale,
            f"这些名字已被登记为'实例属性'，但类上其实有定义：{stale} —— "
            "请从 INSTANCE_ATTRIBUTES 移除，让契约检查真正覆盖它们。",
        )

    def test_instance_attribute_allowlist_entries_are_protocol_members(self):
        """allowlist 里的名字必须确实在 Protocol 中，避免留下无意义的条目。"""
        extra = sorted(set(INSTANCE_ATTRIBUTES) - self.members)
        self.assertEqual(
            [],
            extra,
            f"INSTANCE_ATTRIBUTES 里这些名字不在 Protocol 中：{extra}",
        )

    def test_runner_local_methods_are_not_protocol_members(self):
        """runner 自己的实现不应出现在 Protocol 里（否则第 1 步优先会绕过宿主）。"""
        from module.transfer.runner import WebTransferRunner

        overlap = sorted(WebTransferRunner._RUNNER_LOCAL_METHODS & self.members)
        self.assertEqual(
            [],
            overlap,
            f"{overlap} 同时是 runner 本地方法又被 Protocol 声明；"
            "解析时本地优先，会绕过宿主覆盖 —— 请从 Protocol 移除或改名。",
        )

    def test_every_resolved_name_is_resolvable_on_a_complete_host(self):
        """_resolve_method 用到的名字，在宿主上必须能解析出**可调用**的实现。

        软探测的风险是"返回 None 后被当函数调"；这里直接验证解析结果可调用。
        宿主用工厂装配好的门面（不跑 `__init__`，避免真实网络/目录副作用），
        再补上 runner 解析路径需要的最小装配态。
        """
        from module.transfer.runner import WebTransferRunner
        from unit_tests.support.downloader_factory import build_downloader

        host = build_downloader(with_task_manager=True)
        runner = WebTransferRunner(host=host)
        names = ["check_type", "get_web_transfer_range_message",
                 "get_web_transfer_single_message",
                 "skip_missing_web_transfer_range_message",
                 "transfer_message_to_web_target",
                 "transfer_web_discussion_replies_to_target",
                 "wait_between_transfer_messages"]
        unresolvable = []
        for name in names:
            try:
                resolved = runner._resolve_method(name)
            except AttributeError:
                unresolvable.append(name)
                continue
            if not callable(resolved):
                unresolvable.append(name)
        self.assertEqual(
            [],
            unresolvable,
            f"这些名字在装配好的宿主上解析不出可调用实现：{unresolvable}",
        )

    def test_resolve_method_raises_for_unknown_name(self):
        """未知名字必须报错，不能静默返回 None。"""
        from module.transfer.runner import WebTransferRunner

        runner = WebTransferRunner(host=SimpleNamespace())
        with self.assertRaises(AttributeError):
            runner._resolve_method("definitely_not_a_method_xyz")


if __name__ == "__main__":
    unittest.main()
