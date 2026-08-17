# coding=UTF-8
"""Composition root — explicit wiring for app, bot, stores, managers, and engines."""

import asyncio
from typing import Optional, Set, Union

from module import console, log
from module.adapters.bot.bot import Bot, CallbackData
from module.adapters.bot.callback_handler import CallbackHandler
from module.adapters.pikpak.archive import build_pikpak_archive_client
from module.adapters.pikpak.integration import PikpakIntegrationManager
from module.adapters.webui.operations import WebOperationsFacade
from module.adapters.webui.server import WebUiServer
from module.adapters.webui.setup import SetupCoordinator
from module.adapters.webui.task_manager import WebUITaskManager
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
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
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
        self.watch_manager = LiveWatchManager(
            transfer_store_getter=self._transfer_store,
            operation_submitter=self.submit_web_operation,
            user_getter=self._runtime_user,
            app_getter=self._app,
            diagnostic=self.diagnostic,
        )
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
        self.pikpak_manager = PikpakIntegrationManager(
            transfer_store_getter=self._transfer_store,
            pikpak_archive_client_getter=self._pikpak_archive_client,
            diagnostic=self.diagnostic,
            gc_getter=self._gc,
            refresh_counts=self.refresh_transfer_task_counts,
            cleanup_item_file=self._cleanup_item_file,
            app_getter=self._app,
            system_log=self.system_log,
            schedule_deferred_archive=self._schedule_deferred_archive,
        )
        self.progress_tracker = TransferProgressTracker(
            transfer_store_getter=self._transfer_store,
            diagnostic=self.diagnostic,
            app_getter=self._app,
            gc_getter=self._gc,
            loop_getter=self._loop,
            pb_getter=self._pb,
            release_storage=self.release_transfer_local_storage,
            release_window=self.release_download_upload_window,
            start_download_upload=self.start_download_upload,
            archive_pikpak_item=self.archive_pikpak_item,
            fail_transfer_item=self.fail_transfer_item,
            refresh_counts=self.refresh_transfer_task_counts,
            cleanup_local_file=self._cleanup_item_file,
            system_log=self.system_log,
        )
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
    # Explicit late-bound dependencies (single source of truth; no __getattr__ magic)
    # ------------------------------------------------------------------
    def _app(self):
        return getattr(self, "app", None)

    def _gc(self):
        return getattr(self, "gc", None)

    def _loop(self):
        return getattr(self, "loop", None)

    def _pb(self):
        return getattr(self, "pb", None)

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
            self.watch_manager = LiveWatchManager(
                listen_download_chat=getattr(self, "listen_download_chat", {}),
                listen_forward_chat=getattr(self, "listen_forward_chat", {}),
                web_pending_watches=getattr(self, "web_pending_watches", {}),
                web_watch_handler_clients=getattr(
                    self, "web_watch_handler_clients", {}
                ),
                transfer_store_getter=self._transfer_store,
                operation_submitter=getattr(
                    self,
                    "submit_web_operation",
                    lambda ot, p: {
                        "id": f"{ot}-0",
                        "status": TransferStatus.PENDING,
                    },
                ),
                user_getter=self._runtime_user,
                app_getter=self._app,
                diagnostic=getattr(
                    self, "diagnostic", RichDiagnosticAdapter(console, log)
                ),
            )
        return self.watch_manager

    def _pikpak_manager(self):
        return getattr(self, "pikpak_manager", None)

    def _require_pikpak_manager(self):
        if getattr(self, "pikpak_manager", None) is None:
            self.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=self._transfer_store,
                pikpak_archive_client_getter=self._pikpak_archive_client,
                diagnostic=getattr(
                    self, "diagnostic", RichDiagnosticAdapter(console, log)
                ),
                gc_getter=self._gc,
                refresh_counts=lambda task_id: (
                    self.transfer_store.refresh_task_counts(task_id)
                    if self.transfer_store is not None
                    else None
                ),
                cleanup_item_file=self._cleanup_item_file,
                app_getter=self._app,
                system_log=getattr(self, "system_log", None),
                schedule_deferred_archive=self._schedule_deferred_archive,
            )
        return self.pikpak_manager

    def _require_progress_tracker(self):
        if getattr(self, "progress_tracker", None) is None:
            self.progress_tracker = TransferProgressTracker(
                transfer_store_getter=self._transfer_store,
                diagnostic=getattr(
                    self, "diagnostic", RichDiagnosticAdapter(console, log)
                ),
                app_getter=self._app,
                gc_getter=self._gc,
                loop_getter=self._loop,
                pb_getter=self._pb,
                release_storage=getattr(
                    self, "release_transfer_local_storage", lambda wu: None
                ),
                release_window=getattr(
                    self, "release_download_upload_window", lambda wu: None
                ),
                start_download_upload=getattr(
                    self, "start_download_upload", lambda **kw: False
                ),
                archive_pikpak_item=getattr(
                    self, "archive_pikpak_item", lambda **kw: None
                ),
                fail_transfer_item=getattr(
                    self, "fail_transfer_item", lambda *a: None
                ),
                refresh_counts=lambda task_id: (
                    self.transfer_store.refresh_task_counts(task_id)
                    if self.transfer_store is not None
                    else None
                ),
                cleanup_local_file=self._cleanup_item_file,
                system_log=getattr(self, "system_log", None),
            )
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
