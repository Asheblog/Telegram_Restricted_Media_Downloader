# coding=UTF-8
"""真实集成基线：一次真正的端到端装配与落盘。

## 为什么需要这个文件
仓库里 700+ 个单元用例大量使用 ``object.__new__(TelegramRestrictedMediaDownloader)``
+ ``SimpleNamespace`` 打桩，**从不执行真实的组合根接线**。后果（已实测）：
- 把 ``WebUiServer`` / ``TransferStore`` 直接 patch 成假对象，测的是替身行为；
- 组合根里 50 个 getter / 199 个 kwarg 的接线错误在单测里无法暴露；
- 因此任何结构性重构（例如拆上帝对象）都没有安全网。

本文件提供一条**真实**链路的最小基线：真构造门面 → 真起 HTTP 服务 →
走真实首启向导 API → 真实提交转存任务 → 真实落 SQLite → 用独立只读连接读回。
只有"Telegram 登录"与"rclone 探测"被替代（它们需要外部服务）。

## 覆盖到的真实接线（此前无任何测试覆盖）
- ``TelegramRestrictedMediaDownloader()`` 完整构造（composition_root 装配）
- ``module.bootstrap.initialize()`` 的幂等副作用
- ``start_web_ui()`` → ``WebUiServer`` 构造（23 个实参）+ 真实端口绑定
- ``WebUiServer._operation()`` 字符串派发 → ``WebOperationsFacade`` → 宿主 mixin
- setup 向导状态机（``SetupCoordinator.build_status`` + ``is_setup_ready``）
- ``TransferStore`` 真实建库、建表、写入、跨连接读取
"""
import asyncio
import datetime
import http.client
import json
import os
import pathlib
import shutil
import socket
import sys
import tempfile
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

# ── 沙箱：必须在 import 任何 module.* 之前完成 ──
# UserConfig 的 config.yaml 路径在**类定义与实例化时**由 sys.argv[0] 推导
# （module/core/config.py: DIRECTORY_NAME / config_path）。pytest 的 argv[0] 指向
# venv 的 Scripts 目录，若不隔离，向导保存的 API 凭证会写到仓库外/仓库根。
# 因此先把 argv[0] 指到沙箱，再导入门面，测试结束再还原。
_ORIGINAL_ARGV = list(sys.argv)
_ORIGINAL_CWD = os.getcwd()
_SANDBOX = pathlib.Path(tempfile.mkdtemp(prefix="trmd-integration-"))
_WORKDIR = _SANDBOX / "work"
for _sub in ("work", "temp", "sessions", "appdata", "downloads"):
    (_SANDBOX / _sub).mkdir(parents=True, exist_ok=True)
os.chdir(_WORKDIR)
sys.argv = [str(_SANDBOX / "trmd-test-entry.py")]

os.environ["XDG_CONFIG_HOME"] = str(_SANDBOX / "appdata")
os.environ["APPDATA"] = str(_SANDBOX / "appdata")

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()

from module.downloader import TelegramRestrictedMediaDownloader  # noqa: E402
from module.persistence.transfer_store import TransferStatus, TransferStore  # noqa: E402
from module.utils.parser import PARSE_ARGS  # noqa: E402

sys.argv = _ORIGINAL_ARGV

_WEB_PORT = PARSE_ARGS.web
if not _WEB_PORT:
    # 未带 --web 时显式给一个空端口，供 start_web_ui 绑定。
    with socket.socket() as _probe:
        _probe.bind(("127.0.0.1", 0))
        _WEB_PORT = _probe.getsockname()[1]
    PARSE_ARGS.web = _WEB_PORT
os.environ["TRMD_WEB_HOST"] = "127.0.0.1"
os.environ["TRMD_WEB_PORT"] = str(_WEB_PORT)

# UserConfig.DIRECTORY_NAME 是**类属性**，在进程内首次 import module.core.config 时
# 就由当时的 sys.argv[0] 固化。跑完整套件时它往往已被别的测试模块导入并指向
# pytest 目录，因此仅靠 chdir/argv 无法隔离 config.yaml。这里改用真实的
# `--config` 契约（UserConfig.__init__ 会优先采用 PARSE_ARGS.config）显式指向沙箱。
_SANDBOX_CONFIG = _WORKDIR / "config.yaml"
PARSE_ARGS.config = str(_SANDBOX_CONFIG)


class _Http:
    """每次请求独立连接的极简客户端（连接复用在该服务器上不可靠）。"""

    def __init__(self, port):
        self.port = port

    def request(self, method, path, payload=None, headers=None):
        body = None
        hdrs = dict(headers or {})
        if payload is not None:
            body = json.dumps(payload)
            hdrs.setdefault("Content-Type", "application/json")
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.request(method, path, body=body, headers=hdrs)
            response = conn.getresponse()
            raw = response.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except ValueError:
                parsed = {"_raw": raw}
            return response.status, parsed
        finally:
            conn.close()


class CompositionRootIntegrationCase(unittest.TestCase):
    """一条真实链路：构造 → 起服务 → 向导 → 提交任务 → 落盘。"""

    @classmethod
    def setUpClass(cls):
        cls._cwd_dir = tempfile.mkdtemp(prefix="trmd-integration-work-")
        os.chdir(cls._cwd_dir)
        # 组合根的 self.loop 需要"当前线程的 event loop"。这里**显式**提供一个：
        # 既贴近生产（main.py 在无 loop 的进程里由组合根自建），又避免
        # asyncio 的"隐式兜底"产生 DeprecationWarning（在 -W error 下会变成失败）。
        cls._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls._loop)
        # 真实构造门面；open_browser 不弹浏览器。
        with patch("module.adapters.webui.server.webbrowser.open", return_value=True):
            cls.downloader = TelegramRestrictedMediaDownloader()
            cls.downloader.start_web_ui(with_auth_provider=True)
        cls.http = _Http(cls.downloader.web_ui.port)
        cls.temp_directory = cls.downloader.app.temp_directory

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.downloader.web_ui is not None:
                cls.downloader.web_ui.stop()
        finally:
            if cls.downloader.transfer_store is not None:
                cls.downloader.transfer_store.close()
            # 还原本类设置的进程级 asyncio 状态，避免影响同进程的其它测试模块。
            # 注意：不删除 _WORKDIR —— PARSE_ARGS.config 指向其中的 config.yaml，
            # 本文件后续的测试类仍要用（删掉会让它们构造失败）。
            asyncio.set_event_loop(None)
            cls._loop.close()
            os.chdir(_ORIGINAL_CWD)

    # ── 1. 真实装配 ──

    def test_01_real_composition_wired_every_collaborator(self):
        dl = self.downloader
        self.assertIsNotNone(dl.gc, "GlobalConfig 未接线")
        self.assertIsNotNone(dl.app, "Application 未接线")
        self.assertIsNotNone(dl.bot, "Bot 未接线")
        self.assertIsNotNone(dl.watch_manager, "LiveWatchManager 未接线")
        self.assertIsNotNone(dl.pikpak_manager, "PikpakIntegrationManager 未接线")
        self.assertIsNotNone(dl.progress_tracker, "TransferProgressTracker 未接线")
        self.assertIsNotNone(dl.web_task_manager, "WebUITaskManager 未接线")
        self.assertIsNotNone(dl.web_ui, "WebUiServer 未启动")
        self.assertIsNotNone(dl.transfer_store, "TransferStore 未创建")
        # 门面暴露的引擎必须与组合根共用同一个 ctx（否则 transfer_store 会是 None）。
        engine = dl.transfer_engine
        self.assertIs(engine.ctx, dl.ctx, "TransferEngine 使用了另一个 ctx")
        self.assertIs(
            engine.transfer_store,
            dl.transfer_store,
            "TransferEngine.transfer_store 与宿主的 store 不是同一个实例",
        )

    def test_02_real_http_server_answers_before_setup(self):
        status, body = self.http.request("GET", "/api/auth/status")
        self.assertEqual(200, status)
        # with_auth_provider=True 时真实 AuthProvider 初始为 pending（等 Telegram 登录）。
        self.assertEqual("pending", body.get("step"))

        status, body = self.http.request("GET", "/api/setup/status")
        self.assertEqual(200, status)
        self.assertFalse(body.get("ready"), "全新安装不应是 ready")
        self.assertTrue(body.get("wizard_active"), "全新安装应触发首启向导")
        self.assertEqual("api", body.get("current_step"))

    def test_03_setup_gate_blocks_business_api_before_ready(self):
        """未就绪时业务 API 必须被挡住——这是真实门禁，不是 mock 行为。"""
        status, body = self.http.request(
            "POST",
            "/api/tasks",
            {
                "source_link": "https://t.me/example_channel",
                "target_link": "https://t.me/pikpak_bot",
                "start_id": 1,
                "end_id": 2,
            },
        )
        self.assertEqual(409, status, f"应被 setup 门禁拦截，实际 {status}: {body}")
        self.assertEqual("setup_required", body.get("error_code"))

    def test_03b_config_is_confined_to_the_sandbox(self):
        """隔离自检：应用读写的 config.yaml 必须在沙箱里，不能碰仓库。"""
        self.assertEqual(
            str(_SANDBOX_CONFIG.resolve()),
            str(pathlib.Path(self.downloader.app.config_path).resolve()),
            "app.config_path 未指向沙箱 —— 测试会写坏仓库的 config.yaml",
        )
        repo_config = (pathlib.Path(_ORIGINAL_CWD) / "config.yaml").resolve()
        self.assertFalse(
            str(repo_config).startswith(str(_SANDBOX)),
            "自检逻辑错误：仓库路径不应在沙箱内",
        )
        # 仓库里的 config.yaml 必须仍是"无凭证"状态（未被测试写入）。
        if repo_config.exists():
            text = repo_config.read_text(encoding="utf-8")
            self.assertNotIn(
                "123456", text,
                "仓库根 config.yaml 被测试污染（写入了测试 api_id）",
            )

    def test_04_setup_wizard_via_real_api_reaches_ready(self):
        # 1) 保存 API 凭证（真实写 config.yaml 并 refresh_runtime_fields）
        status, body = self.http.request(
            "POST",
            "/api/setup/api",
            {"api_id": 123456, "api_hash": "0123456789abcdef0123456789abcdef"},
        )
        self.assertEqual(200, status, body)

        status, body = self.http.request("GET", "/api/setup/status")
        self.assertTrue(body["steps"]["api"]["done"], "API 凭证未生效")
        self.assertEqual("telegram", body.get("current_step"))

        # 2) Telegram 登录需要外部服务；用真实 AuthProvider 的公开 set_done 推进状态。
        auth = self.downloader.web_ui_auth
        self.assertIsNotNone(auth, "auth provider 未接线")
        auth.set_done("integration-user")

        status, body = self.http.request("GET", "/api/setup/status")
        self.assertEqual(200, status)
        self.assertTrue(body["steps"]["telegram"]["done"])
        self.assertTrue(body.get("ready"), f"API+Telegram 就绪后 ready 应为真: {body}")
        # 就绪后向导不会立刻关：全新安装还要求 rclone 探测通过（外部二进制，
        # 测试环境不可用），因此 current_step 应是 rclone。这是设计如此，不是缺陷。
        self.assertEqual("rclone", body.get("current_step"), body)
        self.assertTrue(
            body["steps"]["rclone"]["prompt"], "应提示配置 rclone"
        )

    def test_05_submit_transfer_task_persists_to_sqlite(self):
        # 区间转存要求"频道链接"，不能是消息链接（这是真实校验，曾被 mock 掩盖）。
        source_link = "https://t.me/example_channel"
        status, body = self.http.request(
            "POST",
            "/api/tasks",
            {
                "source_link": source_link,
                "target_link": "https://t.me/pikpak_bot",
                "start_id": 42,
                "end_id": 44,
            },
        )
        self.assertEqual(201, status, f"就绪后提交任务应成功，实际 {status}: {body}")
        self.assertIn("task_id", body)

        # 真实 store（服务端那份）里必须能查到
        store = self.downloader.transfer_store
        self.assertEqual(1, len(store.list_tasks()), "任务未落库")
        task = store.list_tasks()[0]
        self.assertEqual(source_link, task.get("source_link"))
        self.assertEqual(42, task.get("start_id"))
        self.assertEqual(44, task.get("end_id"))

        # 独立打开一个新的连接读同一个目录 —— 证明真的写进了磁盘，而不是内存假象
        recheck = TransferStore(directory=self.temp_directory)
        try:
            rows = recheck.list_tasks()
            self.assertEqual(1, len(rows), "独立连接读不到任务：没有真正落盘")
            self.assertEqual(source_link, rows[0].get("source_link"))

            # ── item 级别的真实落库 ──
            # item 由执行期（runner）在遍历来源消息时创建，而执行需要真实 Telegram 会话，
            # 集成环境无法覆盖。这里改为对**服务端同一个 store 实例**写入 item 并回读，
            # 覆盖的仍是真实 SQLite 表结构 / 状态字段 / 跨连接可见性，
            # 而不是用 mock 假装成功。
            item_id = self.downloader.transfer_store.add_item(
                task_id=int(body["task_id"]),
                source_chat_id=-1001234567890,
                source_message_id=42,
                source_link=f"{source_link}/42",
                target_link="https://t.me/pikpak_bot",
            )
            item = recheck.get_item(int(item_id))
            self.assertIsNotNone(item, "独立连接读不到 item：item 未真正落盘")
            self.assertEqual(
                TransferStatus.PENDING,
                item.get("status"),
                f"新建 item 的初始状态应为 PENDING，实际 {item.get('status')!r}",
            )
            self.assertEqual(42, item.get("source_message_id"))
            self.assertEqual(
                int(body["task_id"]), int(item.get("task_id"))
            )
            # 以权威来源（item 表）断言，而不是冗余计数列：
            # add_item 本身不刷新 transfer_tasks.total_items（由 refresh_task_counts 维护），
            # 因此断言 total_items 会误判为缺陷。
            items = recheck.list_items(int(body["task_id"]))
            self.assertEqual(1, len(items), "独立连接的 item 列表里查不到该 item")
        finally:
            recheck.close()

    def test_06_business_api_reachable_after_ready(self):
        """反向确认门禁不是"什么都拦"：就绪后只读业务接口应正常。"""
        status, body = self.http.request("GET", "/api/tasks")
        self.assertEqual(200, status, f"就绪后 /api/tasks 应可用: {status} {body}")
        self.assertIn("tasks", body)


class _FakeMessage:
    """足够真实 runner 遍历的最小消息替身（只提供被读取的字段）。"""

    def __init__(self, message_id, chat_id, has_video=True):
        self.id = message_id
        self.chat = SimpleNamespace(id=chat_id)
        self.text = None
        self.caption = "integration caption"
        self.date = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        self.web_page = None
        self.video = SimpleNamespace(
            file_id="fake-file-id",
            file_unique_id="fake-unique-id",
            file_name="clip.mp4",
            file_size=1024,
            mime_type="video/mp4",
            duration=1,
            width=2,
            height=2,
        ) if has_video else None
        self.photo = None
        self.document = None


class TransferChainIntegrationCase(unittest.TestCase):
    """驱动**真实** WebTransferRunner.process_task 直到 item 落库。

    与上一个类不同，这里不满足于"手工 add_item"：由真实 runner 执行任务，
    真实判定媒体类型并创建 Transfer Item，再用独立连接读回。
    只有两处面向 Telegram 的取数被替换（integration 环境无会话）：
    - ``parse_web_transfer_link``（解析链接 -> chat_id）
    - ``get_web_transfer_range_message``（按 id 取消息）
    其余全部走真实代码：process_task 的状态机、range 遍历、
    runtime_message_filter 判定、skip_transfer_item_for_media_type 落库、
    refresh_task_counts 聚合。
    """

    @classmethod
    def setUpClass(cls):
        cls._cwd_dir = tempfile.mkdtemp(prefix="trmd-chain-work-")
        os.chdir(cls._cwd_dir)
        cls._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls._loop)
        with patch("module.adapters.webui.server.webbrowser.open", return_value=True):
            cls.downloader = TelegramRestrictedMediaDownloader()
            cls.downloader.start_web_ui(with_auth_provider=True)
        cls.store = cls.downloader.transfer_store
        cls.temp_directory = cls.downloader.app.temp_directory
        cls.origin_chat_id = -1009999

        # 只允许 photo：让视频消息被判定为"媒体类型不匹配" -> 走 skip 分支落 item。
        # 注意 message_filter 属于**全局配置**（GlobalConfig，~/.config/TRMD/.CONFIG.yaml），
        # 不是用户 config.yaml；写错位置会导致过滤不生效（实测过）。
        gc = cls.downloader.gc
        gc_config = deepcopy(gc.config)
        gc_config["message_filter"] = {
            "enabled": True,
            "media_types": {"photo": True, "video": False},
        }
        gc.save_config(gc_config)

        async def _parse(client, link):
            return {"chat_id": cls.origin_chat_id}

        async def _range_message(chat_id, message_id, task_id):
            return _FakeMessage(message_id, cls.origin_chat_id)

        cls.downloader.parse_web_transfer_link = _parse
        cls.downloader.get_web_transfer_range_message = _range_message
        # ensure_uploader 会真的构造 uploader（需要 client），这里给一个惰性替身，
        # 本用例的 skip 分支不触碰上传。
        cls.downloader.ensure_uploader = lambda: SimpleNamespace()

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.downloader.web_ui is not None:
                cls.downloader.web_ui.stop()
        finally:
            if cls.downloader.transfer_store is not None:
                cls.downloader.transfer_store.close()
            asyncio.set_event_loop(None)
            cls._loop.close()
            os.chdir(_ORIGINAL_CWD)

    def test_real_runner_creates_skipped_item_for_disallowed_media(self):
        source_link = "https://t.me/example_channel"
        task_id = self.store.create_task(
            source_link, "https://t.me/pikpak_bot", start_id=42, end_id=42
        )
        runner = self.downloader._transfer_runner
        asyncio.run(runner.process_task(int(task_id)))

        # 真实 runner 应当已经创建了 item（媒体类型不允许 -> SKIPPED）
        items = self.store.list_items(int(task_id))
        self.assertEqual(1, len(items), f"真实 runner 未创建 item: {items}")
        item = items[0]
        self.assertEqual(TransferStatus.SKIPPED, item.get("status"))
        self.assertEqual("filtered", item.get("media_type"))
        self.assertEqual(42, item.get("source_message_id"))
        # store 以 TEXT 存 source_chat_id，比较时统一成字符串。
        self.assertEqual(str(self.origin_chat_id), str(item.get("source_chat_id")))

        # 冗余计数列应已被 refresh_task_counts 刷新
        task = self.store.get_task(int(task_id))
        self.assertEqual(1, int(task.get("total_items") or 0))

        # 跨连接可见 —— 真的落盘
        recheck = TransferStore(directory=self.temp_directory)
        try:
            rows = recheck.list_items(int(task_id))
            self.assertEqual(1, len(rows), "独立连接读不到 runner 创建的 item")
            self.assertEqual(TransferStatus.SKIPPED, rows[0].get("status"))
        finally:
            recheck.close()


if __name__ == "__main__":
    unittest.main()
