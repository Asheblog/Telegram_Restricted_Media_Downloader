# coding=UTF-8
"""WebOps 解耦回归守卫：拆 operation_applicator / watch_operations 时断掉的两条接线。

## 两个回归（均由独立源码复核确认）

**R1 — Channel Download 媒体白名单 override 丢失（引入于 6e0d564，接线漂移于 e95af69）**
`apply_web_channel_download` 的表单 `download_type` 是「整表覆盖」语义：
给了就整表替换全局 `message_filter.media_types`（date/keywords 仍用会话参数），
没给就继承全局。拆分后 `operation_applicator.py` 算出了 `media_types_override`，
却调用零参 `self._runtime_message_filter()`；`operations.py` 的组装 lambda 也写死
零参（丢弃 override）。于是**表单勾选被静默忽略**，主贴与评论区都退回全局白名单。

**R2 — 延迟评论区抓取三个主动入口拿不到调度器（引入于 dde1ac3）**
`WatchOperations.cancel/run_now/retry` 用的是「只窥视、不启动」的
`scheduler_if_started()`；调度器尚未启动时它返回 `None` → `AttributeError`。
旧实现按需 `_ensure_comment_delay_scheduler()`（创建 + 启动）。
删除监听必须保留「不因删除而启动调度器」的语义（deferred_discussion.py 的注释、
ADR0007、LiveWatchManager.delete_watch 已有 store 层取消保障），因此要区分两条
getter：删除用 peek，主动操作用 ensure。

## 隔离策略：整个场景在子进程里跑
`module.core.config.UserConfig.PATH` / `PARSE_ARGS.config` / `APPDATA` 都是
**进程级、import 期固化**的。本用例早期版本在父进程 import 阶段改
`PARSE_ARGS.config` 和 cwd，污染了同进程后续的 integration 用例
（`test_03b_config_is_confined_to_the_sandbox` 实测失败）。
现在改为：父进程只负责写场景脚本并 `subprocess.run`；场景脚本在**自己的进程**里
设 argv/env/cwd、import module、构造真实门面（沿用 `composition_window_case.py`
的既有范式）。父进程的 argv/cwd/APPDATA/XDG_CONFIG_HOME/PARSE_ARGS/事件循环
一律不动，`SANDBOX` 由 `TemporaryDirectory` 显式清理。
Telegram 外部 client 用 fake；store / MessageFilter / 调度器都是真的。
run_now/retry 走 `run_coroutine_threadsafe`，因此场景里显式跑一个后台事件循环，
绝不阻塞自己的线程，收尾显式关 store / loop / 线程。
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_PREAMBLE = r'''
import asyncio
import datetime
import os
import pathlib
import sys
import tempfile
import threading
import time
from types import SimpleNamespace

sys.path.insert(0, os.environ["TRMD_REPO_ROOT"])
_sandbox = pathlib.Path(os.environ["TRMD_SANDBOX"])
_work = _sandbox / "work"
for _sub in ("work", "temp", "sessions", "appdata", "downloads"):
    (_sandbox / _sub).mkdir(parents=True, exist_ok=True)
os.chdir(_work)
sys.argv = [
    str(_sandbox / "trmd-test-entry.py"),
    "-c", str(_work / "config.yaml"),
    "-w", "0",
]
os.environ["XDG_CONFIG_HOME"] = str(_sandbox / "appdata")
os.environ["APPDATA"] = str(_sandbox / "appdata")

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.core.filter import Filter
from module.core.media_types import MEDIA_TYPES, MEDIA_TYPES_DEFAULT
from module.downloader import TelegramRestrictedMediaDownloader
from module.persistence.transfer_store import (
    DeferredDiscussionCaptureStatus,
    TransferStore,
)
from module.utils.flag_support import make_forward_watch_rule

_EPOCH = datetime.datetime(2024, 6, 15, 12, 0, 0)


def _message(message_id, *, link=None, date=None, text=None, **media):
    payload = {"id": message_id, "link": link or "https://t.me/c/1/%s" % message_id}
    payload["date"] = date or _EPOCH
    payload["text"] = text
    payload["caption"] = None
    payload["media_group_id"] = None
    for media_type in MEDIA_TYPES:
        if media_type == "text":
            # MEDIA_TYPES 含 'text'，它不是媒体附件对象；别把消息正文覆写成 None。
            continue
        payload[media_type] = media.get(media_type)
    return SimpleNamespace(**payload)


def _media_only(**allowed):
    return {t: bool(allowed.get(t, False)) for t in MEDIA_TYPES}


class _FakeTelegramClient:
    """只替代外部 Telegram：历史遍历与讨论区取回是异步生成器。"""

    def __init__(self, messages, comments=None):
        self._messages = list(messages)
        self._comments = dict(comments or {})

    async def get_chat_history(self, chat_id=None, reverse=False):
        for message in self._messages:
            yield message

    async def get_discussion_message(self, chat_id, message_id):
        raise AttributeError("no discussion link in fake client")

    async def get_discussion_replies(self, chat_id, message_id):
        for comment in self._comments.get(int(message_id), []):
            yield comment


def _build_facade():
    """真实组合根 + 真实 MessageFilter；只把 Telegram client 换成 fake。"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        facade = TelegramRestrictedMediaDownloader()
    finally:
        asyncio.set_event_loop(None)
        loop.close()
    return facade


class _ChannelDownloadScene:
    """R1 场景：表单 download_type 整表覆盖 / 未传继承 / 评论区共享同一过滤器。"""

    def __init__(self, tmpdir):
        self.facade = _build_facade()
        self.facade.transfer_store = TransferStore(directory=tmpdir)
        self.created_links = []

        async def _create_download_task(**kwargs):
            self.created_links.append(kwargs.get("message_ids"))
            return {"status": "ok"}

        # 必须在首次 _ensure_operation_applicator() 之前覆盖，组装时才拿得到替身。
        self.facade.create_download_task = _create_download_task

    def close(self):
        store = self.facade.transfer_store
        if store is not None:
            store.close()

    def set_global_media(self, allowed):
        self.facade.gc.message_filter["media_types"] = dict(allowed)

    def apply(self, payload, messages, comments=None):
        self.facade.app.client = _FakeTelegramClient(messages, comments)
        payload = {"chat_link": "https://t.me/regression_channel", **payload}
        asyncio.run(self.facade.apply_web_channel_download(payload))
        return list(self.created_links)

    def apply_through_operation_queue(self, payload, messages):
        """走真实入口：process_web_operation → operation_applicator → channel_download。"""
        self.facade.app.client = _FakeTelegramClient(messages)
        operation_id = "channel_download-regression-1"
        self.facade.web_operations[operation_id] = {
            "id": operation_id,
            "type": "channel_download",
            "status": "pending",
            "created_at": "2026-10-03T00:00:00+00:00",
            "updated_at": "2026-10-03T00:00:00+00:00",
            "payload": {"chat_link": "https://t.me/regression_channel", **payload},
        }
        asyncio.run(self.facade.process_web_operation(operation_id))
        return self.facade.web_operations[operation_id]


class _DeferredCaptureScene:
    """R2 场景：cancel/run_now/retry 必须 ensure 调度器；delete 只窥视已启动实例。"""

    def __init__(self, tmpdir):
        self.facade = _build_facade()
        self.store = TransferStore(directory=tmpdir)
        self.facade.transfer_store = self.store
        self.executed = []

        async def _forward_discussion_replies(**kwargs):
            self.executed.append(kwargs)
            return 1

        # DeferredDiscussionOperations 在调用时经实例解析该方法，组装前/后覆盖都生效。
        self.facade.forward_discussion_replies = _forward_discussion_replies
        # 后台事件循环：run_now/retry 经 run_coroutine_threadsafe 提交，不能占用测试线程。
        self.loop_thread_ready = threading.Event()
        self.background_loop = asyncio.new_event_loop()

        def _run_loop():
            asyncio.set_event_loop(self.background_loop)
            self.loop_thread_ready.set()
            self.background_loop.run_forever()

        self.loop_thread = threading.Thread(target=_run_loop, daemon=True)
        self.loop_thread.start()
        assert self.loop_thread_ready.wait(timeout=10), "后台事件循环线程未就绪"
        self.facade.loop = self.background_loop

    def close(self):
        """收尾一律在后台 loop 线程内完成，且不吞异常。

        dev 模式（PYTHONDEVMODE=1）暴露的真实缺陷：在主线程直接调
        ``scheduler.stop()`` 会对后台 loop 持有的 Task 做跨线程 ``cancel()``，
        抛 ``RuntimeError: Non-thread-safe operation invoked on an event loop
        other than the current one``；close 提前中断后后台线程的 sqlite 连接没关，
        ``TemporaryDirectory`` 在 Windows 上删不掉 transfer_tasks.sqlite3。
        正确顺序：loop 线程内 stop 调度器 → 等被取消的 tick/inflight 任务收尾 →
        关该线程的 store 连接；随后停 loop、join 线程；最后关主线程连接。
        """
        deferred = self.facade._ensure_deferred_discussion_ops()
        scheduler = deferred.scheduler_if_started()
        shutdown_error = None
        if self.background_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._shutdown_in_loop_thread(scheduler), self.background_loop
            )
            try:
                future.result(timeout=30)
            except BaseException as exc:  # noqa: BLE001 - 记录后仍要释放资源
                shutdown_error = exc

        self.background_loop.call_soon_threadsafe(self.background_loop.stop)
        self.loop_thread.join(timeout=30)
        if self.loop_thread.is_alive():
            raise AssertionError("后台事件循环线程未能在 30s 内停止")

        # store 的连接是线程局部的：后台 loop 线程与主线程各关一次。
        self.store.close()
        self.background_loop.close()
        if shutdown_error is not None:
            raise shutdown_error

    async def _shutdown_in_loop_thread(self, scheduler):
        """必须整体跑在后台 loop 线程里：Task.cancel/await 都不是线程安全的。"""
        tick_task = scheduler._task if scheduler is not None else None
        inflight = list(scheduler._inflight.values()) if scheduler is not None else []
        if scheduler is not None:
            scheduler.stop()
        for task in [tick_task, *inflight]:
            if task is None or task.done():
                continue
            try:
                await task
            except asyncio.CancelledError:
                pass
        # 让被取消任务的 finally / 派生回调在关连接前跑完。
        await asyncio.sleep(0)
        self.store.close()

    def schedule_capture(self, watch_id="forward:regression", due_in=3600):
        self.store.upsert_live_transfer_watch(
            watch_id=watch_id,
            watch_type="forward",
            source_link="https://t.me/source",
            target_link="https://t.me/target",
            include_comment=True,
        )
        return self.store.schedule_deferred_discussion_capture(
            watch_id=watch_id,
            source_chat_id="-1001",
            source_message_id=42,
            target_chat_id="-1002",
            target_link="https://t.me/target",
            due_at=time.time() + due_in,
        )

    def started_scheduler(self):
        return self.facade._ensure_deferred_discussion_ops().scheduler_if_started()


# ────────────────────────── R1 scenarios ──────────────────────────

def scenario_form_selection_replaces_global_allowlist(tmpdir):
    scene = _ChannelDownloadScene(tmpdir)
    try:
        scene.set_global_media(_media_only(video=True, photo=True, text=True))
        links = scene.apply(
            {"download_type": ["photo"]},
            [_message(1, photo=object()), _message(2, video=object())],
        )
        assert links == ["https://t.me/c/1/1"], (
            "表单 download_type 没有整表覆盖全局白名单（override 被丢弃）: %r" % (links,)
        )
    finally:
        scene.close()


def scenario_operation_queue_entrypoint_honors_override(tmpdir):
    scene = _ChannelDownloadScene(tmpdir)
    try:
        scene.set_global_media(_media_only(video=True, photo=True, text=True))
        operation = scene.apply_through_operation_queue(
            {"download_type": ["photo"]},
            [_message(11, photo=object()), _message(12, video=object())],
        )
        assert operation["status"] == "success", operation.get("error_message")
        assert scene.created_links == ["https://t.me/c/1/11"], scene.created_links
    finally:
        scene.close()


def scenario_missing_form_selection_inherits_global_allowlist(tmpdir):
    scene = _ChannelDownloadScene(tmpdir)
    try:
        scene.set_global_media(_media_only(photo=True, text=True))
        links = scene.apply(
            {},
            [_message(3, photo=object()), _message(4, video=object())],
        )
        assert links == ["https://t.me/c/1/3"], links
    finally:
        scene.close()


def scenario_comments_share_the_same_override_filter(tmpdir):
    scene = _ChannelDownloadScene(tmpdir)
    try:
        scene.set_global_media(dict(MEDIA_TYPES_DEFAULT))
        links = scene.apply(
            {"download_type": ["photo"], "include_comment": True},
            [_message(5, photo=object())],
            {5: [_message(51, video=object()), _message(52, photo=object())]},
        )
        assert links == ["https://t.me/c/1/5", "https://t.me/c/1/52"], (
            "评论区没有共享主贴的 override 过滤器（video 被放行）: %r" % (links,)
        )
    finally:
        scene.close()


def scenario_date_range_and_keywords_still_apply(tmpdir):
    scene = _ChannelDownloadScene(tmpdir)
    try:
        scene.set_global_media(dict(MEDIA_TYPES_DEFAULT))
        links = scene.apply(
            {
                "download_type": ["photo"],
                "keywords": ["keep"],
                "date_range": {
                    "start_date": datetime.datetime(2024, 6, 1).timestamp(),
                    "end_date": datetime.datetime(2024, 6, 30).timestamp(),
                },
            },
            [
                _message(6, photo=object(), text="keep this", date=_EPOCH),
                _message(7, photo=object(), text="drop this", date=_EPOCH),
                _message(
                    8, photo=object(), text="keep but old",
                    date=datetime.datetime(2020, 1, 1, 0, 0, 0),
                ),
            ],
        )
        assert links == ["https://t.me/c/1/6"], links
    finally:
        scene.close()


# ────────────────────────── R2 scenarios ──────────────────────────

def scenario_watch_operations_requires_ensure_getter(tmpdir):
    from module.webops.watch_operations import WatchOperations

    try:
        WatchOperations(
            watch_manager_getter=lambda: None,
            comment_delay_scheduler_getter=lambda: None,
            transfer_store_getter=lambda: None,
            loop_getter=lambda: None,
        )
    except TypeError:
        return
    raise AssertionError(
        "ensure_comment_delay_scheduler_getter 必须是必填参数（不许缺省退回 peek）"
    )


def scenario_cancel_before_scheduler_started_ensures_and_cancels(tmpdir):
    scene = _DeferredCaptureScene(tmpdir)
    try:
        capture = scene.schedule_capture()
        assert scene.started_scheduler() is None, "前置条件：调度器尚未启动"
        ok = scene.facade.cancel_deferred_discussion_capture(
            capture["watch_id"], capture["id"]
        )
        assert ok, "调度器未启动时取消延迟抓取失败（getter 返回 None → AttributeError）"
        fetched = scene.store.get_deferred_discussion_capture(capture["id"])
        assert fetched["status"] == DeferredDiscussionCaptureStatus.CANCELLED, fetched
        assert scene.started_scheduler() is not None, (
            "主动操作应 ensure 出调度器实例（旧行为：按需创建并启动）"
        )
    finally:
        scene.close()


def scenario_run_now_before_scheduler_started_executes_capture(tmpdir):
    scene = _DeferredCaptureScene(tmpdir)
    try:
        capture = scene.schedule_capture()
        assert scene.started_scheduler() is None, "前置条件：调度器尚未启动"
        ok = scene.facade.run_deferred_discussion_capture_now(
            capture["watch_id"], capture["id"]
        )
        assert ok, "调度器未启动时立即执行失败（getter 返回 None → AttributeError）"
        fetched = scene.store.get_deferred_discussion_capture(capture["id"])
        assert fetched["status"] == DeferredDiscussionCaptureStatus.DONE, fetched
        assert len(scene.executed) == 1, "立即执行没有真正跑 executor"
    finally:
        scene.close()


def scenario_retry_before_scheduler_started_requeues_and_executes(tmpdir):
    scene = _DeferredCaptureScene(tmpdir)
    try:
        capture = scene.schedule_capture()
        scene.store.cancel_deferred_discussion_capture(capture["id"])
        assert scene.started_scheduler() is None, "前置条件：调度器尚未启动"
        ok = scene.facade.retry_deferred_discussion_capture(
            capture["watch_id"], capture["id"]
        )
        assert ok, "调度器未启动时重试失败（getter 返回 None → AttributeError）"
        fetched = scene.store.get_deferred_discussion_capture(capture["id"])
        assert fetched["status"] == DeferredDiscussionCaptureStatus.DONE, fetched
        assert len(scene.executed) == 1, "重试没有真正跑 executor"
    finally:
        scene.close()


def scenario_active_entrypoints_reuse_the_same_started_scheduler_instance(tmpdir):
    scene = _DeferredCaptureScene(tmpdir)
    try:
        capture = scene.schedule_capture()
        scene.facade.cancel_deferred_discussion_capture(
            capture["watch_id"], capture["id"]
        )
        started = scene.started_scheduler()
        assert started is not None
        assert started is scene.facade._ensure_comment_delay_scheduler(), (
            "主动入口拿到的不是宿主持有的同一个调度器实例"
        )
        assert started is scene.facade._ensure_watch_ops()._comment_delay_scheduler(), (
            "peek getter 没有解析到宿主持有的已启动实例"
        )
    finally:
        scene.close()


def scenario_foreign_capture_rejected_without_starting_or_executing(tmpdir):
    scene = _DeferredCaptureScene(tmpdir)
    try:
        capture = scene.schedule_capture(watch_id="forward:owner")
        assert scene.started_scheduler() is None, "前置条件：调度器尚未启动"
        assert not scene.facade.cancel_deferred_discussion_capture(
            "forward:other", capture["id"]
        )
        assert not scene.facade.run_deferred_discussion_capture_now(
            "forward:other", capture["id"]
        )
        assert not scene.facade.retry_deferred_discussion_capture(
            "forward:other", capture["id"]
        )
        assert scene.executed == [], "非归属 capture 不得执行 executor"
        fetched = scene.store.get_deferred_discussion_capture(capture["id"])
        assert fetched["status"] == DeferredDiscussionCaptureStatus.PENDING, fetched
        assert scene.started_scheduler() is None, "非归属 capture 不得触发调度器启动"
    finally:
        scene.close()


def scenario_delete_watch_does_not_start_scheduler_but_cancels_pending(tmpdir):
    scene = _DeferredCaptureScene(tmpdir)
    try:
        rule = make_forward_watch_rule(
            "https://t.me/source", "https://t.me/target", True, False, False
        )
        watch_id = "forward:%s" % rule
        capture = scene.schedule_capture(watch_id=watch_id)
        assert scene.started_scheduler() is None, "前置条件：调度器尚未启动"
        assert scene.facade.delete_watch(watch_id)
        fetched = scene.store.get_deferred_discussion_capture(capture["id"])
        assert fetched["status"] == DeferredDiscussionCaptureStatus.CANCELLED, fetched
        assert scene.started_scheduler() is None, (
            "删除监听不得因取消延迟抓取而启动调度器（deferred_discussion 的既有语义）"
        )
    finally:
        scene.close()


SCENARIOS = {
    "form_selection_replaces_global_allowlist": scenario_form_selection_replaces_global_allowlist,
    "operation_queue_entrypoint_honors_override": scenario_operation_queue_entrypoint_honors_override,
    "missing_form_selection_inherits_global_allowlist": scenario_missing_form_selection_inherits_global_allowlist,
    "comments_share_the_same_override_filter": scenario_comments_share_the_same_override_filter,
    "date_range_and_keywords_still_apply": scenario_date_range_and_keywords_still_apply,
    "watch_operations_requires_ensure_getter": scenario_watch_operations_requires_ensure_getter,
    "cancel_before_scheduler_started_ensures_and_cancels": scenario_cancel_before_scheduler_started_ensures_and_cancels,
    "run_now_before_scheduler_started_executes_capture": scenario_run_now_before_scheduler_started_executes_capture,
    "retry_before_scheduler_started_requeues_and_executes": scenario_retry_before_scheduler_started_requeues_and_executes,
    "active_entrypoints_reuse_the_same_started_scheduler_instance": scenario_active_entrypoints_reuse_the_same_started_scheduler_instance,
    "foreign_capture_rejected_without_starting_or_executing": scenario_foreign_capture_rejected_without_starting_or_executing,
    "delete_watch_does_not_start_scheduler_but_cancels_pending": scenario_delete_watch_does_not_start_scheduler_but_cancels_pending,
}


def main() -> int:
    name = os.environ["TRMD_WEB_OPS_SCENARIO"]
    scenario = SCENARIOS[name]
    with tempfile.TemporaryDirectory(prefix="trmd-webops-scene-") as tmpdir:
        scenario(tmpdir)
    print("SCENARIO_OK %s" % name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


class WebOpsExtractionRegressionCase(unittest.TestCase):
    """父进程只跑子进程场景：不动 argv/cwd/env/PARSE_ARGS/事件循环。"""

    def _run_scenario(self, name: str) -> subprocess.CompletedProcess:
        # SANDBOX 显式由 TemporaryDirectory 创建与清理，绝不复用真实用户配置目录。
        with tempfile.TemporaryDirectory(prefix="trmd-webops-regression-") as sandbox:
            script_path = os.path.join(sandbox, "scenario.py")
            with open(script_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(_PREAMBLE)
            env = os.environ.copy()
            env["TRMD_REPO_ROOT"] = ROOT
            env["TRMD_SANDBOX"] = sandbox
            env["TRMD_WEB_OPS_SCENARIO"] = name
            env["PYTHONIOENCODING"] = "utf-8"
            # 沙箱内不留真实用户的 APPDATA / XDG_CONFIG_HOME，交给场景脚本重设。
            env.pop("APPDATA", None)
            env.pop("XDG_CONFIG_HOME", None)
            return subprocess.run(
                [
                    sys.executable,
                    # 子进程内把两类收尾警告升级为错误/显式报告，父进程据此把关。
                    "-W", "error::RuntimeWarning",
                    "-W", "error::ResourceWarning",
                    script_path,
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                cwd=ROOT,
                timeout=180,
            )

    def _assert_scenario_ok(self, name: str) -> None:
        result = self._run_scenario(name)
        self.assertEqual(
            0,
            result.returncode,
            f"场景 {name} 失败：\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        # exit code 0 也可能带 unraisable 警告（例如解释器 gc 阶段才销毁的连接），
        # 因此必须额外检查 stderr，不能只看返回码。
        for marker in ("RuntimeWarning", "ResourceWarning"):
            self.assertNotIn(
                marker,
                result.stderr,
                f"场景 {name} 收尾泄漏了 {marker}（子进程严格门禁）：\n"
                f"stdout={result.stdout}\nstderr={result.stderr}",
            )
        self.assertIn(f"SCENARIO_OK {name}", result.stdout)

    def test_form_selection_replaces_global_allowlist(self):
        self._assert_scenario_ok("form_selection_replaces_global_allowlist")

    def test_operation_queue_entrypoint_honors_override(self):
        self._assert_scenario_ok("operation_queue_entrypoint_honors_override")

    def test_missing_form_selection_inherits_global_allowlist(self):
        self._assert_scenario_ok("missing_form_selection_inherits_global_allowlist")

    def test_comments_share_the_same_override_filter(self):
        self._assert_scenario_ok("comments_share_the_same_override_filter")

    def test_date_range_and_keywords_still_apply(self):
        self._assert_scenario_ok("date_range_and_keywords_still_apply")

    def test_watch_operations_requires_ensure_getter(self):
        self._assert_scenario_ok("watch_operations_requires_ensure_getter")

    def test_cancel_before_scheduler_started_ensures_and_cancels(self):
        self._assert_scenario_ok("cancel_before_scheduler_started_ensures_and_cancels")

    def test_run_now_before_scheduler_started_executes_capture(self):
        self._assert_scenario_ok("run_now_before_scheduler_started_executes_capture")

    def test_retry_before_scheduler_started_requeues_and_executes(self):
        self._assert_scenario_ok("retry_before_scheduler_started_requeues_and_executes")

    def test_active_entrypoints_reuse_the_same_started_scheduler_instance(self):
        self._assert_scenario_ok(
            "active_entrypoints_reuse_the_same_started_scheduler_instance"
        )

    def test_foreign_capture_rejected_without_starting_or_executing(self):
        self._assert_scenario_ok(
            "foreign_capture_rejected_without_starting_or_executing"
        )

    def test_delete_watch_does_not_start_scheduler_but_cancels_pending(self):
        self._assert_scenario_ok(
            "delete_watch_does_not_start_scheduler_but_cancels_pending"
        )


if __name__ == "__main__":
    unittest.main()
