# coding=UTF-8
"""Composition root — explicit wiring for app, bot, stores, managers, and engines."""

import asyncio
from typing import Optional, Set, Union

from module import console, log
from module.adapters.bot.bot import Bot, CallbackData
from module.adapters.bot.callback_handler import CallbackHandler
from module.adapters.pikpak.archive import build_pikpak_archive_client
from module.adapters.pikpak.integration import PikpakIntegrationManager
from module.webops.operations import WebOperationsFacade
from module.adapters.webui.server import WebUiServer
from module.webops.setup_coordinator import SetupCoordinator
from module.webops.task_manager import WebUITaskManager
from module.bootstrap import initialize
from module.core.app import Application
from module.core.config import GlobalConfig
from module.core.filter import MessageFilter
from module.infra.async_window import DynamicAsyncWindow
from module.infra.client import TelegramRestrictedMediaDownloaderClient
from module.infra.uploader import TelegramUploader
from module.persistence.local_storage_guard import LocalStorageGuard
from module.persistence.media_manager import MediaManager
from module.persistence.system_log import SystemLogTracer
from module.persistence.transfer_store import TransferStatus, TransferStore
from module.transfer.context import (
    TransferContext,
    TransferPathPorts,
    TransferPorts,
    TransferProgressPorts,
    TransferRuntimePorts,
    TransferStoragePorts,
    TransferTargetPorts,
)
from module.transfer.engine import TransferEngine
from module.transfer.live_transfer import LiveTransferService
from module.transfer.live_watch import LiveWatchManager
from module.transfer.progress import TransferProgressTracker
from module.transfer.runner import WebTransferRunner
from module.transfer.watch_applicator import LiveWatchApplicator
from module.utils.diagnostics import RichDiagnosticAdapter
from module.utils.stdio import ProgressBar


class TrmdCompositionRoot:
    def __init__(self):
        initialize()
        self.gc = GlobalConfig()
        self.diagnostic = RichDiagnosticAdapter(console, log)
        self.system_log = SystemLogTracer(diagnostic=self.diagnostic)
        self.bot = Bot(
            handler_overrides={
                "start": self.start,
                "callback_data": self.callback_data,
                "handle_forwarded_media": self.handle_forwarded_media,
                "on_listen": self.on_listen,
            },
            gc=self.gc,
        )
        self.loop: asyncio.AbstractEventLoop = self._resolve_event_loop()
        self.event: asyncio.Event = asyncio.Event()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.app: Application = Application(
            client_factory=TelegramRestrictedMediaDownloaderClient
        )
        self.download_upload_window = DynamicAsyncWindow(
            limit_provider=self.gc.upload_pending_limit, minimum=1, maximum=5
        )
        self.local_storage_guard = LocalStorageGuard(
            reserve_bytes_provider=self._local_storage_reserve_bytes
        )
        self.media_manager: Union[MediaManager, None] = None
        self.is_running: bool = False
        self.running_log: Set[bool] = set()
        self.running_log.add(self.is_running)
        self.pb: ProgressBar = ProgressBar()
        self.uploader: Union[TelegramUploader, None] = None
        self.cd: Union[CallbackData, None] = None
        self.my_id: int = 0
        self.transfer_store: Union[TransferStore, None] = None
        self.web_ui: Union[WebUiServer, None] = None
        self.web_ui_auth = None
        self.setup_coordinator = SetupCoordinator()
        self._api_credentials_event: asyncio.Event = asyncio.Event()
        if self.app.has_telegram_api_credentials():
            self._api_credentials_event.set()
        self.web_task_queue: asyncio.Queue = asyncio.Queue()
        self.web_submitted_task_ids: Set[int] = set()
        self.web_running_task: Optional[asyncio.Task] = None
        self.web_running_task_id: Optional[int] = None
        self._transfer_download_tasks: dict[int, set] = {}
        self.web_operation_queue: asyncio.Queue = asyncio.Queue()
        self.web_operations: dict = {}
        self.watch_manager = self._new_watch_manager()
        # Host + Bot must share watch_manager dicts. Missing host aliases crash after
        # WebUI login when restore_live_transfer_watches reads self.listen_forward_chat.
        self.listen_download_chat = self.watch_manager.listen_download_chat
        self.listen_forward_chat = self.watch_manager.listen_forward_chat
        self.bot.listen_download_chat = self.watch_manager.listen_download_chat
        self.bot.listen_forward_chat = self.watch_manager.listen_forward_chat
        self.bot.downloader = self
        # Album dedupe state lives on Bot; live_transfer mutates it through the host.
        self.handle_media_groups = self.bot.handle_media_groups
        self.web_pending_watches = self.watch_manager.web_pending_watches
        self.web_watch_handler_clients = self.watch_manager.web_watch_handler_clients
        self.pikpak_archive_client = None
        self.pikpak_manager = self._new_pikpak_manager()
        self.progress_tracker = self._new_progress_tracker()
        self.callback_handler = CallbackHandler(
            app_getter=self._app,
            gc_getter=self._gc,
            diagnostic=self.diagnostic,
            watch_manager_getter=self._watch_manager,
            transfer_store_getter=self._transfer_store,
            loop_getter=self._loop,
            user_getter=self._runtime_user,
            my_id_getter=self._my_id,
            host=self,
            downloader_ref=self,
        )
        self._transfer_runner = WebTransferRunner(host=self)
        self.live_transfer = LiveTransferService(host=self)
        self._watch_applicator = LiveWatchApplicator(host=self)
        self.web_task_manager = WebUITaskManager(
            transfer_store_getter=self._transfer_store,
            diagnostic=self.diagnostic,
            loop_getter=self._loop,
            web_task_queue=self.web_task_queue,
            web_submitted_task_ids=self.web_submitted_task_ids,
            web_running_task_getter=self._web_running_task,
            web_running_task_setter=self._set_web_running_task,
            web_running_task_id_getter=self._web_running_task_id,
            web_running_task_id_setter=self._set_web_running_task_id,
            web_operation_queue=self.web_operation_queue,
            web_operations=self.web_operations,
            watch_manager_getter=self._watch_manager,
            pikpak_manager_getter=self._pikpak_manager,
            progress_tracker_getter=self._progress_tracker,
            listener_restart_callback=None,
            list_watches_getter=self.list_watches,
            persisted_watches_getter=self.watch_manager.persisted_watches,
            set_live_watch_status_getter=self.watch_manager.set_live_watch_status,
            watch_payload_from_record_getter=self.watch_manager.watch_payload_from_record,
            archive_pikpak_item_getter=self.archive_pikpak_item,
            refresh_transfer_task_counts_getter=self.refresh_transfer_task_counts,
            process_web_transfer_task_getter=self.process_web_transfer_task,
            retry_watch_inline_task_getter=self.retry_watch_inline_task,
            process_web_task_queue_getter=self.process_web_task_queue,
            cleanup_task_files_getter=self._cleanup_task_files,
            uploader_getter=self._uploader,
            should_continue_web_transfer_task_getter=None,
        )
        self.ctx = TransferContext(
            app=self.app,
            gc=self.gc,
            diagnostic=self.diagnostic,
            loop=self.loop,
            my_id=self.my_id,
            download_upload_window=self.download_upload_window,
            local_storage_guard=self.local_storage_guard,
            transfer_store=self.transfer_store,
            progress_tracker=self.progress_tracker,
            pikpak_manager=self.pikpak_manager,
            watch_manager=self.watch_manager,
            web_task_manager=self.web_task_manager,
        )
        self._transfer_ports = self._build_transfer_ports()
        self._te = TransferEngine(
            ctx=self.ctx,
            ports=self._transfer_ports,
            diagnostic=self.diagnostic,
        )
        self._web_operations_facade = WebOperationsFacade(self)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_event_loop() -> asyncio.AbstractEventLoop:
        """取一个可用的 event loop，且不依赖进程级"当前 loop"状态。

        原先直接 ``asyncio.get_event_loop()``：该 API 在 3.12+ 已废弃，并且在
        "本线程曾被 set_event_loop 过、当前 loop 为 None"的进程里会抛
        ``RuntimeError: There is no current event loop``（实测：组合根在完整测试
        套件中构造即失败，单独构造却成功）。这里按"运行中 → 已设置 → 新建"取，
        三种情况都不抛；生产入口没有显式设过 loop，因此得到的仍是新建的 loop。
        """
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            # 不在协程里：本线程已设置过 loop 就复用，否则显式新建并注册。
            try:
                existing = asyncio.get_event_loop_policy().get_event_loop()
            except RuntimeError:
                existing = None
            if existing is not None:
                return existing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    # ------------------------------------------------------------------
    # Explicit late-bound dependencies (single source of truth; no __getattr__ magic)
    #
    # 这四个 getter（`_app` / `_gc` / `_loop` / `_pb`）**一律不兜底**：
    # 直接 `self.x`，初始化顺序写错会立刻 AttributeError，而不是让下游拿到
    # 静默的 None（那会把"顺序错误"伪装成"能力缺失"）。
    #
    # 这个结论是实测出来的，不是猜的。做法：逐个把兜底换成直接属性访问、
    # 跑全量、记录失败用例，再决定是收紧还是补测试（结果见下表）。
    #
    # | getter  | 收紧后失败数 | 处理 |
    # | ------- | ------------ | ---- |
    # | `_app`  | 0 | 直接收紧 |
    # | `_pb`   | 0 | 直接收紧 |
    # | `_gc`   | 5 | 先用探针定位真实调用路径（见下），给那 5 个宿主补 `gc` 后收紧 |
    # | `_loop` | 1 | 核对后确认走的是生产降级分支，改为用例显式声明 `loop = None` 后收紧 |
    #
    # `_gc` 那次值得记一笔：失败只告诉你"测试红了"，不告诉你"谁在用 gc"。
    # 实际调用链是 `PikpakIntegrationManager.get_task_target_size_limit_error`
    # → `target_profile_limit(gc, ...)`，而后者对 gc 的唯一要求是"能取到 config"，
    # 所以补 `SimpleNamespace(config={})`（语义 = 未配置目标档案）就够。
    #
    # `_loop` 那次也值得记：那个用例并不是"测试遗留"，它走的正是生产分支 ——
    # `schedule_deferred_archive` 在 `loop is None or not loop.is_running()` 时
    # 改为立即归档。所以正确处理是把"没有 loop"**显式写出来**，而不是继续
    # 依赖 getter 的隐式 None。
    # ------------------------------------------------------------------
    def _app(self):
        return self.app

    def _gc(self):
        return self.gc

    def _loop(self):
        return self.loop

    def _pb(self):
        return self.pb

    def _my_id(self):
        return getattr(self, "my_id", 0)

    def _transfer_store(self):
        return getattr(self, "transfer_store", None)

    def _runtime_user(self):
        return getattr(self, "user", None)

    def _watch_manager(self):
        return getattr(self, "watch_manager", None)

    def _require_watch_manager(self):
        if getattr(self, "watch_manager", None) is None:
            self.watch_manager = self._new_watch_manager()
        return self.watch_manager

    # ------------------------------------------------------------------
    # Collaborator factories —— 接线只写一次
    # ------------------------------------------------------------------
    # 构造期（__init__）与按需兜底（_require_* / 半构造宿主）此前各写了一份
    # LiveWatchManager / PikpakIntegrationManager / TransferProgressTracker 的
    # 构造实参，改一个依赖要记得改两处，且两边默认值不同（一处用真实方法、
    # 一处用 lambda 兜底），审计时记为"重复构造"。现在统一走下面三个工厂：
    # 主路径与兜底路径读同一份定义，差异只剩"属性还没赋值时怎么退化"。
    def _new_watch_manager(self) -> LiveWatchManager:
        return LiveWatchManager(
            listen_download_chat=getattr(self, "listen_download_chat", {}),
            listen_forward_chat=getattr(self, "listen_forward_chat", {}),
            web_pending_watches=getattr(self, "web_pending_watches", {}),
            web_watch_handler_clients=getattr(self, "web_watch_handler_clients", {}),
            transfer_store_getter=self._transfer_store,
            operation_submitter=getattr(
                self,
                "submit_web_operation",
                lambda operation_type, payload: {
                    "id": f"{operation_type}-0",
                    "status": TransferStatus.PENDING,
                },
            ),
            user_getter=self._runtime_user,
            app_getter=self._app,
            diagnostic=getattr(
                self, "diagnostic", RichDiagnosticAdapter(console, log)
            ),
        )

    def _new_pikpak_manager(self) -> PikpakIntegrationManager:
        return PikpakIntegrationManager(
            transfer_store_getter=self._transfer_store,
            pikpak_archive_client_getter=self._pikpak_archive_client,
            diagnostic=getattr(
                self, "diagnostic", RichDiagnosticAdapter(console, log)
            ),
            gc_getter=self._gc,
            refresh_counts=getattr(self, "refresh_transfer_task_counts", None)
            or (
                lambda task_id: (
                    self.transfer_store.refresh_task_counts(task_id)
                    if getattr(self, "transfer_store", None) is not None
                    else None
                )
            ),
            cleanup_item_file=self._cleanup_item_file,
            app_getter=self._app,
            system_log=getattr(self, "system_log", None),
            schedule_deferred_archive=self._schedule_deferred_archive,
        )

    def _new_progress_tracker(self) -> TransferProgressTracker:
        return TransferProgressTracker(
            transfer_store_getter=self._transfer_store,
            diagnostic=getattr(
                self, "diagnostic", RichDiagnosticAdapter(console, log)
            ),
            app_getter=self._app,
            gc_getter=self._gc,
            loop_getter=self._loop,
            pb_getter=self._pb,
            release_storage=getattr(
                self, "release_transfer_local_storage", lambda with_upload: None
            ),
            release_window=getattr(
                self, "release_download_upload_window", lambda with_upload: None
            ),
            start_download_upload=getattr(
                self, "start_download_upload", lambda **kwargs: False
            ),
            archive_pikpak_item=getattr(
                self, "archive_pikpak_item", lambda **kwargs: None
            ),
            fail_transfer_item=getattr(
                self, "fail_transfer_item", lambda *args: None
            ),
            refresh_counts=getattr(self, "refresh_transfer_task_counts", None)
            or (
                lambda task_id: (
                    self.transfer_store.refresh_task_counts(task_id)
                    if getattr(self, "transfer_store", None) is not None
                    else None
                )
            ),
            cleanup_local_file=self._cleanup_item_file,
            system_log=getattr(self, "system_log", None),
        )

    def _pikpak_manager(self):
        return getattr(self, "pikpak_manager", None)

    def _require_pikpak_manager(self):
        if getattr(self, "pikpak_manager", None) is None:
            self.pikpak_manager = self._new_pikpak_manager()
        return self.pikpak_manager

    def _require_progress_tracker(self):
        if getattr(self, "progress_tracker", None) is None:
            self.progress_tracker = self._new_progress_tracker()
        return self.progress_tracker

    def on_transfer_file_ready(self, *args, **kwargs):
        return self._require_progress_tracker().on_transfer_file_ready(*args, **kwargs)

    def on_transfer_item_skipped(self, *args, **kwargs):
        return self._require_progress_tracker().on_transfer_item_skipped(*args, **kwargs)

    def on_transfer_item_failed(self, *args, **kwargs):
        return self._require_progress_tracker().on_transfer_item_failed(*args, **kwargs)

    def on_transfer_upload_progress(self, *args, **kwargs):
        return self._require_progress_tracker().on_transfer_upload_progress(*args, **kwargs)

    def on_transfer_upload_status(self, *args, **kwargs):
        return self._require_progress_tracker().on_transfer_upload_status(*args, **kwargs)

    def build_bot_transfer_progress_text(self, *args, **kwargs):
        return self._require_progress_tracker().build_bot_transfer_progress_text(*args, **kwargs)

    def schedule_bot_transfer_progress_update(self, *args, **kwargs):
        return self._require_progress_tracker().schedule_bot_transfer_progress_update(*args, **kwargs)

    def record_transfer_download_success(self, *args, **kwargs):
        return self._require_progress_tracker().record_transfer_download_success(*args, **kwargs)

    def try_reuse_transfer_download_record(self, *args, **kwargs):
        return self._require_progress_tracker().try_reuse_transfer_download_record(*args, **kwargs)

    def transfer_download_progress(self, *args, **kwargs):
        return self._require_progress_tracker().transfer_download_progress(*args, **kwargs)

    def transfer_percent(self, *args, **kwargs):
        return self._require_progress_tracker().transfer_percent(*args, **kwargs)

    def transfer_size_text(self, *args, **kwargs):
        return self._require_progress_tracker().transfer_size_text(*args, **kwargs)

    def notify_bot_transfer_download_progress(self, *args, **kwargs):
        return self._require_progress_tracker().notify_bot_transfer_download_progress(*args, **kwargs)

    def notify_bot_transfer_downloaded(self, *args, **kwargs):
        return self._require_progress_tracker().notify_bot_transfer_downloaded(*args, **kwargs)

    def notify_bot_transfer_upload_progress(self, *args, **kwargs):
        return self._require_progress_tracker().notify_bot_transfer_upload_progress(*args, **kwargs)

    def notify_bot_transfer_upload_status(self, *args, **kwargs):
        return self._require_progress_tracker().notify_bot_transfer_upload_status(*args, **kwargs)

    def recover_pending_upload_archives(self, *args, **kwargs):
        return self._require_progress_tracker().recover_pending_upload_archives(*args, **kwargs)

    def _progress_tracker(self):
        return getattr(self, "progress_tracker", None)

    def _uploader(self):
        return getattr(self, "uploader", None)

    def _web_running_task(self):
        return self.web_running_task

    def _set_web_running_task(self, value):
        self.web_running_task = value

    def _web_running_task_id(self):
        return self.web_running_task_id

    def _set_web_running_task_id(self, value):
        self.web_running_task_id = value

    def _local_storage_reserve_bytes(self):
        return getattr(
            getattr(self, "gc", None),
            "local_storage_reserve_bytes",
            LocalStorageGuard.DEFAULT_RESERVE_BYTES,
        )

    def _pikpak_archive_client(self):
        return build_pikpak_archive_client(
            (getattr(getattr(self, "gc", None), "config", {}) or {})
            .get("target_profiles", {})
            .get("pikpak", {})
            .get("archive")
        )

    def _schedule_deferred_archive(self, **kwargs):
        if self.progress_tracker is None:
            return None
        return self.progress_tracker._schedule_deferred_upload_archive(**kwargs)

    def _cleanup_item_file(self, item_id):
        return self._ensure_media_manager().try_cleanup_item_file(item_id)

    def _cleanup_task_files(self, task_id):
        return self._ensure_media_manager().cleanup_task_files(task_id)

    def _bot_task_link(self):
        return self.bot.bot_task_link

    def _queue(self):
        return self.queue

    def _pb_progress(self):
        return self.pb.progress

    def _event(self):
        return self.event

    def _ensure_uploader(self):
        return self.ensure_uploader()

    def _build_transfer_ports(self) -> TransferPorts:
        progress = self.progress_tracker
        return TransferPorts(
            paths=TransferPathPorts(
                env_save_directory=self.env_save_directory,
                get_final_save_directory=self.get_final_save_directory,
                get_final_file_path=self.get_final_file_path,
            ),
            progress=TransferProgressPorts(
                record_transfer_download_success=progress.record_transfer_download_success,
                on_transfer_file_ready=progress.on_transfer_file_ready,
                on_transfer_item_skipped=progress.on_transfer_item_skipped,
                on_transfer_item_failed=progress.on_transfer_item_failed,
                on_transfer_upload_progress=progress.on_transfer_upload_progress,
                on_transfer_upload_status=progress.on_transfer_upload_status,
                build_bot_transfer_progress_text=progress.build_bot_transfer_progress_text,
                schedule_bot_transfer_progress_update=progress.schedule_bot_transfer_progress_update,
            ),
            target=TransferTargetPorts(
                infer_target_profile=self.infer_target_profile,
                is_pikpak_target=self.is_pikpak_target,
                normalize_download_upload_meta=self.normalize_download_upload_meta,
                build_transfer_upload_meta=self.build_transfer_upload_meta,
            ),
            storage=TransferStoragePorts(
                release_download_upload_window=self.release_download_upload_window,
                release_transfer_local_storage=self.release_transfer_local_storage,
                mark_transfer_local_storage_materialized=self.mark_transfer_local_storage_materialized,
            ),
            runtime=TransferRuntimePorts(
                ensure_uploader=self._ensure_uploader,
                bot_task_link=self._bot_task_link,
                queue=self._queue,
                pb_progress=self._pb_progress,
                event=self._event,
                create_download_task=self.create_download_task,
                detect_transfer_range_async=self.detect_transfer_range_async,
            ),
        )

    @property
    def message_filter(self) -> MessageFilter:
        """共享消息过滤器实例，所有管线统一使用。

        每次访问时检查配置是否变更（通过 id 对比），确保 config reload 后使用最新配置。
        """
        current_mf = self.gc.message_filter
        if not hasattr(self, "_msg_filter") or self._msg_filter_config_id != id(
            current_mf
        ):
            self._msg_filter = MessageFilter(current_mf)
            self._msg_filter_config_id = id(current_mf)
        return self._msg_filter

    @property
    def transfer_engine(self) -> TransferEngine:
        engine = getattr(self, "_te", None)
        if engine is None:
            engine = self._create_standalone_transfer_engine()
            self._te = engine
        return engine

    def _create_standalone_transfer_engine(self) -> TransferEngine:
        """Explicit fallback for bare/partially-constructed hosts (tests and recovery)."""

        def _noop(*_args, **_kwargs):
            return None

        def _noop_false(*_args, **_kwargs):
            return False

        def _noop_dict(*_args, **_kwargs):
            return {}

        def _noop_str(*_args, **_kwargs):
            return ""

        progress = self._require_progress_tracker()
        return TransferEngine(
            ctx=TransferContext(
                app=getattr(self, "app", None),
                gc=getattr(self, "gc", None),
                diagnostic=getattr(
                    self, "diagnostic", RichDiagnosticAdapter(console, log)
                ),
                loop=getattr(self, "loop", None),
                my_id=getattr(self, "my_id", 0),
                download_upload_window=getattr(
                    self, "download_upload_window", None
                ),
                local_storage_guard=getattr(self, "local_storage_guard", None),
                transfer_store=getattr(self, "transfer_store", None),
                progress_tracker=progress,
                pikpak_manager=getattr(self, "pikpak_manager", None),
                watch_manager=getattr(self, "watch_manager", None),
                web_task_manager=getattr(self, "web_task_manager", None),
            ),
            ports=TransferPorts(
                paths=TransferPathPorts(
                    env_save_directory=getattr(
                        self, "env_save_directory", _noop_str
                    ),
                    get_final_save_directory=getattr(
                        self, "get_final_save_directory", _noop_str
                    ),
                    get_final_file_path=getattr(
                        self, "get_final_file_path", _noop_str
                    ),
                ),
                progress=TransferProgressPorts(
                    record_transfer_download_success=getattr(
                        progress, "record_transfer_download_success", _noop
                    ),
                    on_transfer_file_ready=getattr(
                        progress, "on_transfer_file_ready", _noop
                    ),
                    on_transfer_item_skipped=getattr(
                        progress, "on_transfer_item_skipped", _noop
                    ),
                    on_transfer_item_failed=getattr(
                        progress, "on_transfer_item_failed", _noop
                    ),
                    on_transfer_upload_progress=getattr(
                        progress, "on_transfer_upload_progress", _noop
                    ),
                    on_transfer_upload_status=getattr(
                        progress, "on_transfer_upload_status", _noop
                    ),
                    build_bot_transfer_progress_text=getattr(
                        progress, "build_bot_transfer_progress_text", _noop_str
                    ),
                    schedule_bot_transfer_progress_update=getattr(
                        progress,
                        "schedule_bot_transfer_progress_update",
                        _noop,
                    ),
                ),
                target=TransferTargetPorts(
                    infer_target_profile=getattr(
                        self, "infer_target_profile", lambda *a, **kw: None
                    ),
                    is_pikpak_target=getattr(
                        self, "is_pikpak_target", _noop_false
                    ),
                    normalize_download_upload_meta=getattr(
                        self,
                        "normalize_download_upload_meta",
                        lambda wu: wu,
                    ),
                    build_transfer_upload_meta=getattr(
                        self, "build_transfer_upload_meta", _noop_dict
                    ),
                ),
                storage=TransferStoragePorts(
                    release_download_upload_window=getattr(
                        self, "release_download_upload_window", _noop
                    ),
                    release_transfer_local_storage=getattr(
                        self, "release_transfer_local_storage", _noop
                    ),
                    mark_transfer_local_storage_materialized=getattr(
                        self,
                        "mark_transfer_local_storage_materialized",
                        _noop,
                    ),
                ),
                runtime=TransferRuntimePorts(
                    ensure_uploader=getattr(self, "ensure_uploader", lambda: None),
                    bot_task_link=lambda: getattr(
                        getattr(self, "bot", None), "bot_task_link", set()
                    ),
                    queue=lambda: getattr(self, "queue", None),
                    pb_progress=lambda: getattr(
                        getattr(self, "pb", None), "progress", None
                    ),
                    event=lambda: getattr(self, "event", None),
                    create_download_task=getattr(
                        self, "create_download_task", _noop_dict
                    ),
                    detect_transfer_range_async=getattr(
                        self, "detect_transfer_range_async", lambda *a, **kw: None
                    ),
                ),
            ),
            diagnostic=getattr(
                self, "diagnostic", RichDiagnosticAdapter(console, log)
            ),
        )

    def _ensure_transfer_runner(self) -> WebTransferRunner:
        runner = getattr(self, "_transfer_runner", None)
        if runner is None:
            runner = WebTransferRunner(host=self)
            self._transfer_runner = runner
        return runner


TelegramRestrictedMediaDownloader = TrmdCompositionRoot

__all__ = ["TrmdCompositionRoot", "TelegramRestrictedMediaDownloader"]
