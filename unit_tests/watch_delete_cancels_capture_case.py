# coding=UTF-8
"""监听删除必须联动取消延迟评论区抓取（H1 回归守卫）。

## 这个 bug 是怎么来的
`WebOperationsMixin` 抽出 `WatchOperations` 时，`comment_delay_scheduler_getter`
被写成读 `self.__dict__.get('comment_delay_scheduler')` —— 而调度器实例其实由
`DeferredDiscussionOperations._scheduler` 持有，**宿主上没有这个名字**。
于是 getter 恒为 None：`delete_watch()` 里"取消该监听的延迟抓取"整段被跳过，
另外三个入口（cancel/run_now/retry）会对 None 调方法直接 AttributeError。

全量测试当时是绿的 —— 因为**没有任何用例覆盖"删监听 × 延迟抓取"这个交叉点**。
本文件补上它：这类"跨协作者的接线断了"只能靠交叉用例发现。
"""
import sys
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


class _FakeScheduler:
    def __init__(self):
        self.cancelled_watches = []
        self.cancel_ids = []

    def cancel_for_watch(self, watch_id):
        self.cancelled_watches.append(watch_id)

    def cancel(self, capture_id):
        self.cancel_ids.append(capture_id)
        return True

    async def run_now(self, capture_id):
        return True

    async def retry(self, capture_id):
        return True


class _FakeWatchManager:
    def __init__(self):
        self.deleted = []

    def delete_watch(self, watch_id):
        self.deleted.append(watch_id)
        return True


class WatchDeleteCancelsDeferredCaptureCase(unittest.TestCase):
    def _ops(self, scheduler):
        """构造 WatchOperations，getter 分别指向"已启动的调度器"与空 store。"""
        from module.webops.watch_operations import WatchOperations

        manager = _FakeWatchManager()
        return (
            WatchOperations(
                watch_manager_getter=lambda: manager,
                comment_delay_scheduler_getter=lambda: scheduler,
                transfer_store_getter=lambda: None,
                loop_getter=lambda: None,
            ),
            manager,
        )

    def test_delete_watch_cancels_deferred_capture_for_that_watch(self):
        scheduler = _FakeScheduler()
        ops, manager = self._ops(scheduler)

        self.assertTrue(ops.delete_watch("watch-7"))
        self.assertEqual(["watch-7"], manager.deleted, "监听本身没有被删除")
        self.assertEqual(
            ["watch-7"],
            scheduler.cancelled_watches,
            "删除监听时没有取消它的延迟评论区抓取（会留下孤儿定时任务）",
        )

    def test_delete_watch_still_succeeds_without_started_scheduler(self):
        """调度器尚未启动（getter 返回 None）时，删除仍须成功。"""
        ops, manager = self._ops(None)

        self.assertTrue(ops.delete_watch("watch-8"))
        self.assertEqual(["watch-8"], manager.deleted)

    def test_delete_watch_survives_scheduler_cancel_failure(self):
        """取消失败不应阻断删除（原实现的 try/except 语义）。"""

        class _Exploding(_FakeScheduler):
            def cancel_for_watch(self, watch_id):
                raise RuntimeError("scheduler exploded")

        ops, manager = self._ops(_Exploding())

        self.assertTrue(ops.delete_watch("watch-9"))
        self.assertEqual(["watch-9"], manager.deleted)


class WatchOpsSchedulerWiringCase(unittest.TestCase):
    """守卫：宿主侧 `_ensure_watch_ops` 给的 getter 必须能拿到**同一个**调度器实例。

    这是 H1 的直接复现路径 —— 之前 getter 读了一个没人写的属性名，恒为 None。
    """

    def test_getter_resolves_to_started_scheduler_instance(self):
        from module.web_operations import WebOperationsMixin

        class Host(WebOperationsMixin):
            pass

        host = Host()
        host.watch_manager = _FakeWatchManager()
        deferred = host._ensure_deferred_discussion_ops()
        scheduler = _FakeScheduler()
        # 模拟"调度器已启动"：DeferredDiscussionOperations 持有实例。
        deferred._scheduler = scheduler

        resolved = host._ensure_watch_ops()._comment_delay_scheduler()
        self.assertIs(
            resolved,
            scheduler,
            "宿主给的 comment_delay_scheduler getter 没有解析到已启动的调度器实例"
            "（H1：删监听时取消延迟抓取会静默失效）",
        )

    def test_getter_does_not_start_scheduler_as_a_side_effect(self):
        """取调度器不应触发启动 —— 删监听不该顺带挂线程/循环。"""
        from module.web_operations import WebOperationsMixin

        class Host(WebOperationsMixin):
            pass

        host = Host()
        host.watch_manager = _FakeWatchManager()
        deferred = host._ensure_deferred_discussion_ops()
        self.assertIsNone(deferred._scheduler, "前置条件：调度器尚未启动")

        host._ensure_watch_ops()._comment_delay_scheduler()

        self.assertIsNone(
            deferred._scheduler,
            "取调度器时把调度器启动了（副作用）；应只取已启动实例",
        )


if __name__ == "__main__":
    unittest.main()
