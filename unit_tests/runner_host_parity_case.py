# coding=UTF-8
"""WebTransferRunner 与宿主 mixin 的「双实现」一致性契约测试。

## 为什么需要它
`WebTransferRunner` 的 4 个方法采用"宿主优先、本地兜底"：
`should_continue_web_transfer_task` / `should_continue_web_transfer_item` /
`should_start_next_web_transfer_item` / `settle_web_task_pause_request`。
宿主侧（`WebOperationsMixin` → `WebUITaskManager`）与 runner 侧各有一份实现，
而**两者的判定依据并不相同**：

| 方法 | 宿主侧依据 | runner 兜底依据 |
| --- | --- | --- |
| should_continue_web_transfer_task | task_manager 策略 | store 状态 != PAUSED |
| should_continue_web_transfer_item | store item 状态 ∈ {PENDING,RUNNING} | 同左（本项一致） |
| should_start_next_web_transfer_item | task_manager 策略 | store 状态 ∉ {PAUSING,PAUSED} |
| settle_web_task_pause_request | task_manager 结算 | store 状态机手工结算 |

现有测试只覆盖宿主一侧，因此**分歧不会被发现**。本测试对同一份 store 状态
分别取两条路径，断言结果一致 —— 一致性成立时它锁住契约；一旦有人在其中一侧
改了边界条件，它会立刻失败并把分歧摊开（而不是让生产路径与测试替身路径行为不同）。
"""
import asyncio
import sys
import tempfile
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from unit_tests.support.downloader_factory import build_downloader  # noqa: E402


class RunnerHostParityCase(unittest.TestCase):
    """同状态、两条路径、同一结论。"""

    def _make(self, store, task_id, *, with_task_manager: bool):
        from module.transfer.runner import WebTransferRunner

        downloader = build_downloader(
            transfer_store=store, with_task_manager=with_task_manager
        )
        downloader.diagnostic = SimpleNamespace(
            info=lambda *a, **k: None,
            warning=lambda *a, **k: None,
            error=lambda *a, **k: None,
        )
        return downloader, WebTransferRunner(host=downloader)

    def _both_paths(self, store, task_id, method):
        """返回 (宿主侧结果, runner 兜底结果)。"""
        host_dl, host_runner = self._make(store, task_id, with_task_manager=True)
        bare_dl, bare_runner = self._make(store, task_id, with_task_manager=False)
        kwargs = {} if method != "settle_web_task_pause_request" else {"before": "1"}

        def call(downloader, runner):
            if method == "should_continue_web_transfer_task":
                return downloader.should_continue_web_transfer_task(task_id)
            if method == "should_continue_web_transfer_item":
                return runner.should_continue_web_transfer_item(task_id)
            if method == "should_start_next_web_transfer_item":
                return runner.should_start_next_web_transfer_item(task_id)
            return asyncio.run(runner.settle_web_task_pause_request(task_id, **kwargs))

        return call(host_dl, host_runner), call(bare_dl, bare_runner)

    def _task_in_status(self, store, status):
        from module.persistence.transfer_store import TransferStatus

        task_id = store.create_task("https://t.me/source/1", "https://t.me/pikpak_bot")
        if status is not None:
            store.update_task(task_id, status=status)
        return task_id

    def test_should_continue_web_transfer_task_parity(self):
        from module.persistence.transfer_store import TransferStatus

        for status in (
            TransferStatus.PENDING,
            TransferStatus.RUNNING,
            TransferStatus.PAUSING,
            TransferStatus.PAUSED,
            TransferStatus.SUCCESS,
            TransferStatus.FAILURE,
        ):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
                    from module.persistence.transfer_store import TransferStore

                    store = TransferStore(directory=d)
                    task_id = self._task_in_status(store, status)
                    host_result, bare_result = self._both_paths(
                        store, task_id, "should_continue_web_transfer_task"
                    )
                    self.assertEqual(
                        host_result,
                        bare_result,
                        f"status={status} 时两条路径结论不同："
                        f"宿主侧={host_result} runner 兜底={bare_result}",
                    )
                    store.close()

    def test_should_start_next_web_transfer_item_parity(self):
        from module.persistence.transfer_store import TransferStatus

        for status in (
            TransferStatus.PENDING,
            TransferStatus.RUNNING,
            TransferStatus.PAUSING,
            TransferStatus.PAUSED,
            TransferStatus.SUCCESS,
        ):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
                    from module.persistence.transfer_store import TransferStore

                    store = TransferStore(directory=d)
                    task_id = self._task_in_status(store, status)
                    host_result, bare_result = self._both_paths(
                        store, task_id, "should_start_next_web_transfer_item"
                    )
                    self.assertEqual(
                        host_result,
                        bare_result,
                        f"status={status} 时两条路径结论不同："
                        f"宿主侧={host_result} runner 兜底={bare_result}",
                    )
                    store.close()

    def test_settle_web_task_pause_request_parity(self):
        from module.persistence.transfer_store import TransferStatus

        for status in (TransferStatus.PAUSING, TransferStatus.PAUSED, TransferStatus.RUNNING):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
                    from module.persistence.transfer_store import TransferStore

                    store = TransferStore(directory=d)
                    task_id = self._task_in_status(store, status)
                    host_result, bare_result = self._both_paths(
                        store, task_id, "settle_web_task_pause_request"
                    )
                    self.assertEqual(
                        host_result,
                        bare_result,
                        f"status={status} 时两条路径结论不同："
                        f"宿主侧={host_result} runner 兜底={bare_result}",
                    )
                    store.close()


if __name__ == "__main__":
    unittest.main()
