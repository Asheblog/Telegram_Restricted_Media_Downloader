# coding=UTF-8
"""延迟抓取调度器的并发首次创建：必须只建一个（双启动回归守卫）。

## 为什么需要它
WebUI 与主循环是**两个线程**：HTTP 工作线程会经 `delete_watch` /
`schedule_or_forward_discussion_replies` 首次触发 `ensure_scheduler()`，
主事件循环也会经 `start_web_ui → recover_web_runtime` 首次触发它。
原实现是裸的"检查-创建-赋值"（无锁），并发首次触发时：
- 线程 A 与 B 都看到 `self._scheduler is None`；
- 各自 `_build_scheduler()` 造一个，各自 `start()`；
- 结果**两个调度器同时在跑**，同一条延迟抓取被调度两次。

已有用例只做串行调用，抓不到这个交错。本用例用真线程 + 屏障强制并发，
断言"所有调用方拿到同一个实例、且构造只发生一次"。
"""
import sys
import threading
import time
import unittest
from unittest.mock import patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


class _FakeGc:
    def get_comment_delay_minutes(self):
        return 5


class _FakeStore:
    """调度器构造只用到 get_live_transfer_watch；启动路径不需要真实库。"""

    def get_live_transfer_watch(self, watch_id):
        return None

    def list_deferred_discussion_captures(self, **_kwargs):
        return []


class _FakeHost:
    """最小宿主：够 DeferredDiscussionOperations 的 getter 用。"""

    def __init__(self):
        self.transfer_store = _FakeStore()
        self.gc = _FakeGc()
        self.user = None
        self.app = None
        self.loop = None

    async def forward_discussion_replies(self, **_kwargs):
        return 0

    def _record_watch_event(self, *_args, **_kwargs):
        return None

    def delete_web_task(self, task_id):
        return True


def _make_ops():
    from module.webops.deferred_discussion import DeferredDiscussionOperations

    host = _FakeHost()
    return DeferredDiscussionOperations(
        transfer_store_getter=lambda: host.transfer_store,
        user_getter=lambda: host.user,
        app_getter=lambda: host.app,
        gc_getter=lambda: host.gc,
        loop_getter=lambda: host.loop,
        forward_discussion_replies=lambda **kw: host.forward_discussion_replies(**kw),
        record_watch_event=lambda *a, **kw: host._record_watch_event(*a, **kw),
        delete_web_task=lambda task_id: host.delete_web_task(task_id),
    )


class SchedulerConcurrentConstructionCase(unittest.TestCase):
    def test_concurrent_first_call_builds_exactly_one_scheduler(self):
        ops = _make_ops()
        build_count = 0
        build_lock = threading.Lock()
        original_build = ops._build_scheduler

        def counting_build():
            nonlocal build_count
            with build_lock:
                build_count += 1
            # 在"已判定为 None、还没赋值回去"的窗口里停一下。没有这步时
            # _build_scheduler 太快，GIL 不让线程在该窗口交错，**未加锁的实现也会通过**
            # （实测：去掉锁仍 4 passed，即测试无效）。加停滞后未加锁版本必然重复构造。
            time.sleep(0.05)
            return original_build()

        thread_count = 16
        barrier = threading.Barrier(thread_count)
        results = []
        errors = []

        def worker():
            try:
                barrier.wait(timeout=10)
                results.append(ops.ensure_scheduler())
            except Exception as exc:  # noqa: BLE001 - 线程内异常要带回主线程
                errors.append(exc)

        with patch.object(ops, "_build_scheduler", side_effect=counting_build):
            threads = [threading.Thread(target=worker) for _ in range(thread_count)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=20)

        self.assertEqual([], errors, f"并发调用抛异常：{errors}")
        self.assertEqual(
            thread_count,
            len(results),
            "并非所有线程都返回了调度器（可能有线程卡住）",
        )
        self.assertEqual(
            1,
            build_count,
            f"并发首次调用构造了 {build_count} 个调度器（应为 1）——"
            "会造成两个调度器同时运行、同一条延迟抓取被调度两次",
        )
        first = results[0]
        for scheduler in results[1:]:
            self.assertIs(
                first,
                scheduler,
                "并发调用拿到了不同的调度器实例（应为同一个）",
            )

    def test_serial_calls_reuse_the_same_scheduler(self):
        ops = _make_ops()
        first = ops.ensure_scheduler()
        second = ops.ensure_scheduler()
        self.assertIs(first, second)

    def test_scheduler_if_started_does_not_construct(self):
        ops = _make_ops()
        self.assertIsNone(ops.scheduler_if_started())
        self.assertIsNone(ops._scheduler, "scheduler_if_started 不应触发构造")

    def test_scheduler_if_started_returns_the_built_instance(self):
        ops = _make_ops()
        built = ops.ensure_scheduler()
        self.assertIs(built, ops.scheduler_if_started())


if __name__ == "__main__":
    unittest.main()
