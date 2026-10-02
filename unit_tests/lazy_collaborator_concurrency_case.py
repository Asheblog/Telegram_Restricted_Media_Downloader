# coding=UTF-8
"""`_lazy_collaborator` 的并发首次构造守卫。

## 为什么需要
`WebOperationsMixin` 有 15 个 `_ensure_*` 惰性协作者入口，原先是**裸的
"检查-创建-赋值"**（无锁）。首次构造可能同时来自 WebUI 的 HTTP 工作线程与主事件
循环（`start_web_ui` → `recover_web_runtime`），交错时会各建一个实例 ——
对无状态协作者只是浪费，对有状态的（如延迟抓取调度器，已单独加锁）会出实害。

现在骨架统一收进 `_lazy_collaborator` 并加锁，本用例用真线程验证"只构造一次"。

## 有效性说明
竞态窗口用"构造函数里 sleep"撑开 —— 不加这个停顿，`_build_*` 太快、GIL 不让线程
在该窗口交错，**未加锁的实现也会通过**（上一轮在调度器守卫上实测过这个陷阱）。
"""
import sys
import threading
import time
import unittest
from unittest.mock import patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


class LazyCollaboratorConcurrencyCase(unittest.TestCase):
    def _host(self):
        from module.web_operations import WebOperationsMixin

        class Host(WebOperationsMixin):
            pass

        host = Host()
        host.transfer_store = None
        host.web_operations = {}
        return host

    def test_concurrent_first_call_builds_exactly_one_collaborator(self):
        host = self._host()
        build_count = 0
        counter_lock = threading.Lock()
        original = host._build_stats_ops

        def slow_build():
            nonlocal build_count
            with counter_lock:
                build_count += 1
            # 撑开"已判定为 None、还没写回缓存"的窗口（否则测试无意义）。
            time.sleep(0.05)
            return original()

        thread_count = 16
        barrier = threading.Barrier(thread_count)
        results = []
        errors = []

        def worker():
            try:
                barrier.wait(timeout=10)
                results.append(host._ensure_stats_ops())
            except Exception as exc:  # noqa: BLE001 - 带回主线程断言
                errors.append(exc)

        with patch.object(host, "_build_stats_ops", side_effect=slow_build):
            threads = [threading.Thread(target=worker) for _ in range(thread_count)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=20)

        self.assertEqual([], errors, f"并发调用抛异常：{errors}")
        self.assertEqual(thread_count, len(results), "并非所有线程都返回了实例")
        self.assertEqual(
            1,
            build_count,
            f"并发首次调用构造了 {build_count} 个协作者（应为 1）—— "
            "_lazy_collaborator 的锁没有起作用",
        )
        first = results[0]
        for got in results[1:]:
            self.assertIs(first, got, "并发调用拿到了不同实例")

    def test_serial_calls_reuse_cache(self):
        host = self._host()
        self.assertIs(host._ensure_stats_ops(), host._ensure_stats_ops())

    def test_cache_lives_on_instance_dict_not_class(self):
        """缓存必须写在实例 `__dict__`：写类属性会让所有宿主共享一个协作者。"""
        host_a = self._host()
        host_b = self._host()
        self.assertIsNot(
            host_a._ensure_stats_ops(),
            host_b._ensure_stats_ops(),
            "两个宿主拿到了同一个协作者实例（缓存写到了类上）",
        )

    def test_class_attribute_does_not_shadow_the_lazy_build(self):
        """若子类在**类上**定义了同名属性，惰性构造不能被静默跳过。

        这是 `__dict__.get` 而非 `getattr` 的理由：用 getattr 会把类属性也读进来。
        """
        from module.web_operations import WebOperationsMixin

        sentinel = object()

        class Host(WebOperationsMixin):
            _stats_ops_impl = sentinel  # 类属性，不是本实例的缓存

        host = Host()
        host.transfer_store = None
        host.web_operations = {}
        self.assertIsNot(
            sentinel,
            host._ensure_stats_ops(),
            "惰性构造被类属性静默跳过（应只认实例 __dict__）",
        )


if __name__ == "__main__":
    unittest.main()
