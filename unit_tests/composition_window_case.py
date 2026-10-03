# coding=UTF-8
"""组合根回归：DynamicAsyncWindow 必须 late-bind 全局配置的上传并发上限。

背景（实测）：``TrmdCompositionRoot.__init__`` 曾把 ``self.gc.upload_pending_limit``
（int，core/config.py:773）当作 ``limit_provider`` 传入。``DynamicAsyncWindow.current_limit`
调用该 provider 时抛 ``TypeError`` 并降级为 ``minimum=1``，于是全局配置
``upload.pending_limit``（默认 3）与热更新全部失效。

本用例在**真实组合根**上验证：
1. 装配时读取已存在的 ``.CONFIG.yaml`` 中的 ``upload.pending_limit``（非 1）；
2. 通过 ``GlobalConfig.save_config``（WebUI 热更新走的就是它）改值后动态生效；
3. 异步窗口按该限额放行对应数量的并发租约。

隔离方式沿用 integration 沙箱：``UserConfig``/``GlobalConfig`` 的路径在 import 时
由 ``sys.argv[0]`` 与 ``APPDATA``/``XDG_CONFIG_HOME`` 固化，因此每个场景都在独立子进程、
独立临时目录里完成 import、装配与断言，绝不触碰仓库或真实用户的配置文件。
"""

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_PREAMBLE = r'''
import asyncio
import os
import sys
from copy import deepcopy

_bootstrap_pending = os.environ.get("TRMD_BOOTSTRAP_PENDING")
if _bootstrap_pending:
    _global_dir = os.path.join(os.environ["APPDATA"], "TRMD")
    os.makedirs(_global_dir, exist_ok=True)
    with open(os.path.join(_global_dir, ".CONFIG.yaml"), "w", encoding="utf-8") as _fh:
        _fh.write("upload:\n  pending_limit: %s\n" % _bootstrap_pending)

sys.path.insert(0, os.environ["TRMD_REPO_ROOT"])
_sandbox = os.environ["TRMD_SANDBOX"]
_work = os.path.join(_sandbox, "work")
os.makedirs(_work, exist_ok=True)
os.chdir(_work)
_config_path = os.path.join(_work, "config.yaml")
sys.argv = [os.path.join(_sandbox, "trmd-test-entry.py"), "-c", _config_path, "-w", "0"]

from module.downloader import TelegramRestrictedMediaDownloader

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)
root = TelegramRestrictedMediaDownloader()
window = root.download_upload_window
'''


_SCENARIO_ASSEMBLY = r'''
assert root.gc.upload_pending_limit == 5, (
    "装配时 upload.pending_limit=5 未生效: %r" % (root.gc.upload_pending_limit,)
)
assert window.current_limit == 5, (
    "DynamicAsyncWindow.current_limit 应读取装配时的配置值 5，实际 %r"
    % (window.current_limit,)
)
print("SCENARIO_OK assembly")
'''


_SCENARIO_DYNAMIC = r'''
assert window.current_limit == 3, (
    "默认配置 3 未生效，current_limit 实际 %r" % (window.current_limit,)
)

_config = deepcopy(root.gc.config)
_config.setdefault("upload", {})["pending_limit"] = 5
root.gc.save_config(_config)
assert root.gc.upload_pending_limit == 5, (
    "save_config 后 upload_pending_limit 未更新: %r" % (root.gc.upload_pending_limit,)
)
assert window.current_limit == 5, (
    "save_config 改值后 current_limit 未动态更新，实际 %r" % (window.current_limit,)
)


async def _gate() -> None:
    releases = []
    for _ in range(5):
        releases.append(await asyncio.wait_for(window.acquire(), timeout=1.0))
    waiter = asyncio.create_task(window.acquire())
    await asyncio.sleep(0)
    assert not waiter.done(), "限额 5 用满后第 6 个 acquire 不应立即成功"
    assert window.active_count == 5, (
        "用满 5 个槽位后 active_count 应为 5，实际 %r" % (window.active_count,)
    )
    releases[0]()
    sixth = await asyncio.wait_for(waiter, timeout=1.0)
    assert window.active_count == 5
    for release in releases[1:]:
        release()
    sixth()
    assert window.active_count == 0


asyncio.run(_gate())
print("SCENARIO_OK dynamic")
'''


class CompositionWindowCase(unittest.TestCase):
    """每条场景都在独立子进程 + 独立 APPDATA 沙箱里跑真实组合根。"""

    def _run_scenario(self, body: str, bootstrap_pending: str = "") -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory(prefix="trmd-window-") as sandbox:
            script_path = os.path.join(sandbox, "scenario.py")
            with open(script_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(_PREAMBLE + body)
            env = os.environ.copy()
            env["APPDATA"] = os.path.join(sandbox, "appdata")
            env["XDG_CONFIG_HOME"] = os.path.join(sandbox, "appdata")
            env["TRMD_SANDBOX"] = sandbox
            env["TRMD_REPO_ROOT"] = ROOT
            env["TRMD_BOOTSTRAP_PENDING"] = bootstrap_pending
            env["PYTHONIOENCODING"] = "utf-8"
            return subprocess.run(
                [sys.executable, script_path],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                cwd=ROOT,
                timeout=180,
            )

    def test_real_root_reads_configured_pending_limit_at_assembly(self):
        result = self._run_scenario(_SCENARIO_ASSEMBLY, bootstrap_pending="5")
        self.assertEqual(
            0,
            result.returncode,
            "真实组合根在配置 upload.pending_limit=5 时未接线到窗口:\n"
            f"stdout={result.stdout}\nstderr={result.stderr}",
        )
        self.assertIn("SCENARIO_OK assembly", result.stdout)

    def test_real_root_tracks_gc_change_and_gates_acquires(self):
        result = self._run_scenario(_SCENARIO_DYNAMIC)
        self.assertEqual(
            0,
            result.returncode,
            "GlobalConfig 改值后窗口未动态更新或未按限额放行:\n"
            f"stdout={result.stdout}\nstderr={result.stderr}",
        )
        self.assertIn("SCENARIO_OK dynamic", result.stdout)


if __name__ == "__main__":
    unittest.main()
