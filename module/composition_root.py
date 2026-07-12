# coding=UTF-8
"""Composition root — wires app, bot, stores, managers, and transfer engine."""
import asyncio
from typing import Union, Optional, Set

from module import console, log
from module.filter import MessageFilter
from module.app import Application
from module.config import GlobalConfig
from module.async_window import DynamicAsyncWindow
from module.diagnostics import RichDiagnosticAdapter
from module.persistence.system_log import SystemLogTracer
from module.local_storage_guard import LocalStorageGuard
from module.media_manager import MediaManager
from module.web_task_manager import WebUITaskManager
from module.live_watch_manager import LiveWatchManager
from module.bot import Bot, CallbackData
from module.callback_handler import CallbackHandler
from module.pikpak_archive import build_pikpak_archive_client
from module.pikpak_integration import PikpakIntegrationManager
from module.transfer_progress import TransferProgressTracker
from module.transfer_store import TransferStore, TransferStatus
from module.stdio import ProgressBar
from module.transfer_engine import TransferEngine
from module.comp import TransferContext, TransferPorts
from module.transfer.runner import WebTransferRunner
from module.web_operations import WebOperationsFacade
from module.uploader import TelegramUploader
from module.web_ui import WebUiServer
from module.live_watch_applicator import LiveWatchApplicator


class TrmdCompositionRoot:
    def _local_attr(self, name, default=None):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return default

    def __getattr__(self, name):
        if name in ('bot', 'web_task_manager', '_te'):
            raise AttributeError(name)
        for mgr_name, init_fn in (
            ('watch_manager', '_ensure_watch_manager'),
            ('pikpak_manager', '_ensure_pikpak_manager'),
            ('progress_tracker', '_ensure_progress_tracker'),
        ):
            try:
                mgr = object.__getattribute__(self, mgr_name)
            except AttributeError:
                if init_fn is not None:
                    getattr(type(self), init_fn)(self)
                    try:
                        mgr = object.__getattribute__(self, mgr_name)
                    except AttributeError:
                        continue
                else:
                    continue
            if mgr_name == name and mgr is not None:
                return mgr
            try:
                return getattr(mgr, name)
            except AttributeError:
                continue
        try:
            bot = object.__getattribute__(self, 'bot')
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(bot, name)
    def __init__(self):
        self.gc = GlobalConfig()
        self.diagnostic = RichDiagnosticAdapter(console, log)
        self.system_log = SystemLogTracer(diagnostic=self.diagnostic)
        self.bot = Bot(
            handler_overrides={
                'start': self.start,
                'callback_data': self.callback_data,
            },
            gc=self.gc
        )
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.event: asyncio.Event = asyncio.Event()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.app: Application = Application()
        self.download_upload_window = DynamicAsyncWindow(
            limit_provider=lambda: self.gc.upload_pending_limit,
            minimum=1,
            maximum=5
        )
        self.local_storage_guard = LocalStorageGuard(
            reserve_bytes_provider=lambda: getattr(self.gc, 'local_storage_reserve_bytes', LocalStorageGuard.DEFAULT_RESERVE_BYTES)
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
        self.web_task_queue: asyncio.Queue = asyncio.Queue()
        self.web_submitted_task_ids: Set[int] = set()
        self.web_running_task: Optional[asyncio.Task] = None
        self.web_running_task_id: Optional[int] = None
        self._transfer_download_tasks: dict[int, set] = {}
        self.web_operation_queue: asyncio.Queue = asyncio.Queue()
        self.web_operations: dict = {}
        self.watch_manager = LiveWatchManager(
            transfer_store_getter=lambda: self.__dict__.get('transfer_store'),
            operation_submitter=self.submit_web_operation,
            user_getter=lambda: getattr(self, 'user', None),
            app_getter=lambda: self.app,
            diagnostic=self.diagnostic
        )
        self.bot.listen_download_chat = self.watch_manager.listen_download_chat
        self.bot.listen_forward_chat = self.watch_manager.listen_forward_chat
        self.web_pending_watches = self.watch_manager.web_pending_watches
        self.web_watch_handler_clients = self.watch_manager.web_watch_handler_clients
        self.pikpak_archive_client = None
        self.pikpak_manager = PikpakIntegrationManager(
            transfer_store_getter=lambda: self.__dict__.get('transfer_store'),
            pikpak_archive_client_getter=lambda: build_pikpak_archive_client(
                (getattr(self.gc, 'config', {}) or {}).get('target_profiles', {}).get('pikpak', {}).get('archive')
            ),
            diagnostic=self.diagnostic,
            gc_getter=lambda: self.gc,
            refresh_counts=self.refresh_transfer_task_counts,
            cleanup_item_file=lambda item_id: (
                self._ensure_media_manager().try_cleanup_item_file(item_id)
            ),
            app_getter=lambda: self.app,
        )
        self.progress_tracker = TransferProgressTracker(
            transfer_store_getter=lambda: self.__dict__.get('transfer_store'),
            diagnostic=self.diagnostic,
            app_getter=lambda: self.app,
            gc_getter=lambda: self.gc,
            loop_getter=lambda: getattr(self, 'loop', None),
            pb_getter=lambda: self.pb,
            release_storage=self.release_transfer_local_storage,
            release_window=self.release_download_upload_window,
            start_download_upload=self.start_download_upload,
            archive_pikpak_item=self.archive_pikpak_item,
            fail_transfer_item=self.fail_transfer_item,
            refresh_counts=self.refresh_transfer_task_counts,
            cleanup_local_file=lambda item_id: (
                self._ensure_media_manager().try_cleanup_item_file(item_id)
            ),
            system_log=self.system_log,
        )
        self.callback_handler = CallbackHandler(
            app_getter=lambda: self.app,
            gc_getter=lambda: self.gc,
            diagnostic=self.diagnostic,
            watch_manager_getter=lambda: getattr(self, 'watch_manager', None),
            transfer_store_getter=lambda: self.__dict__.get('transfer_store'),
            loop_getter=lambda: self.loop,
            user_getter=lambda: getattr(self, 'user', None),
            my_id_getter=lambda: self.my_id,
            host=self,
            downloader_ref=self,
        )
        self._transfer_runner = WebTransferRunner(host=self)
        self._watch_applicator = LiveWatchApplicator(host=self)
        self.web_task_manager = WebUITaskManager(
            transfer_store_getter=lambda: self.__dict__.get('transfer_store'),
            diagnostic=self.diagnostic,
            loop_getter=lambda: self.loop,
            web_task_queue=self.web_task_queue,
            web_submitted_task_ids=self.web_submitted_task_ids,
            web_running_task_getter=lambda: getattr(self, 'web_running_task', None),
            web_running_task_setter=lambda v: setattr(self, 'web_running_task', v),
            web_running_task_id_getter=lambda: getattr(self, 'web_running_task_id', None),
            web_running_task_id_setter=lambda v: setattr(self, 'web_running_task_id', v),
            web_operation_queue=self.web_operation_queue,
            web_operations=self.web_operations,
            watch_manager_getter=lambda: getattr(self, 'watch_manager', None),
            pikpak_manager_getter=lambda: getattr(self, 'pikpak_manager', None),
            progress_tracker_getter=lambda: getattr(self, 'progress_tracker', None),
            listener_restart_callback=getattr(self, 'restart_listener', None),
            list_watches_getter=lambda: getattr(self, 'list_watches', None),
            persisted_watches_getter=lambda: getattr(self, 'persisted_watches', None),
            set_live_watch_status_getter=lambda: getattr(self, 'set_live_watch_status', None),
            watch_payload_from_record_getter=lambda: getattr(self, 'watch_payload_from_record', None),
            archive_pikpak_item_getter=self.archive_pikpak_item,
            refresh_transfer_task_counts_getter=self.refresh_transfer_task_counts,
            process_web_transfer_task_getter=self.process_web_transfer_task,
            process_web_task_queue_getter=self.process_web_task_queue,
            cleanup_task_files_getter=lambda task_id: (
                self._ensure_media_manager().cleanup_task_files(task_id)
            ),
            cancel_task_uploads_getter=self.cancel_task_uploads,
            pause_task_uploads_getter=self.pause_task_uploads,
            cancel_task_downloads_getter=self.cancel_task_downloads,
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
        )
        self._te = TransferEngine(
            ctx=self.ctx,
            ports=TransferPorts.from_host(self),
            diagnostic=self.diagnostic,
        )
        self._web_operations_facade = WebOperationsFacade(self)

    @property
    def message_filter(self) -> MessageFilter:
        """共享消息过滤器实例，所有管线统一使用。

        每次访问时检查配置是否变更（通过 id 对比），确保 config reload 后使用最新配置。
        """
        current_mf = self.gc.message_filter
        if not hasattr(self, '_msg_filter') or self._msg_filter_config_id != id(current_mf):
            self._msg_filter = MessageFilter(current_mf)
            self._msg_filter_config_id = id(current_mf)
        return self._msg_filter

    @property
    def transfer_engine(self):
        try:
            return object.__getattribute__(self, '_te')
        except AttributeError:
            self._te = self._create_transfer_engine()
            return self._te

    def _create_transfer_engine(self):
        ctx = self._local_attr('ctx')
        if ctx is None:
            ctx = TransferContext(
                app=self._local_attr('app'),
                gc=self._local_attr('gc'),
                diagnostic=self._local_attr('diagnostic', RichDiagnosticAdapter(console, log)),
                loop=self._local_attr('loop'),
                my_id=self._local_attr('my_id', 0),
                download_upload_window=self._local_attr('download_upload_window'),
                local_storage_guard=self._local_attr('local_storage_guard'),
                transfer_store=self._local_attr('transfer_store'),
                progress_tracker=self._local_attr('progress_tracker'),
                pikpak_manager=self._local_attr('pikpak_manager'),
                watch_manager=self._local_attr('watch_manager'),
                web_task_manager=self._local_attr('web_task_manager'),
            )
        return TransferEngine(
            ctx=ctx,
            ports=TransferPorts.from_host(self),
            diagnostic=self._local_attr('diagnostic', RichDiagnosticAdapter(console, log)),
        )
    def _ensure_watch_manager(self):
        try:
            object.__getattribute__(self, 'watch_manager')
            return
        except AttributeError:
            pass
        try:
            diagnostic = object.__getattribute__(self, 'diagnostic')
        except AttributeError:
            diagnostic = RichDiagnosticAdapter(console, log)
        self.watch_manager = LiveWatchManager(
            transfer_store_getter=lambda: self.__dict__.get('transfer_store'),
            operation_submitter=getattr(self, 'submit_web_operation', lambda ot, p: {'id': f'{ot}-0', 'status': TransferStatus.PENDING}),
            user_getter=lambda: self.__dict__.get('user'),
            app_getter=lambda: self.__dict__.get('app'),
            diagnostic=diagnostic
        )

    def _ensure_pikpak_manager(self):
        try:
            object.__getattribute__(self, 'pikpak_manager')
            return
        except AttributeError:
            pass
        try:
            diagnostic = object.__getattribute__(self, 'diagnostic')
        except AttributeError:
            diagnostic = RichDiagnosticAdapter(console, log)
        self.pikpak_manager = PikpakIntegrationManager(
            transfer_store_getter=lambda: self.__dict__.get('transfer_store'),
            pikpak_archive_client_getter=lambda: build_pikpak_archive_client(
                (getattr(getattr(self, 'gc', None), 'config', {}) or {}).get('target_profiles', {}).get('pikpak', {}).get('archive')
            ),
            diagnostic=diagnostic,
            gc_getter=lambda: self.__dict__.get('gc'),
            refresh_counts=lambda tid: (
                self.__dict__.get('transfer_store').refresh_task_counts(tid)
                if self.__dict__.get('transfer_store') else None
            ),
            cleanup_item_file=lambda item_id: (
                self._ensure_media_manager().try_cleanup_item_file(item_id)
            ),
            app_getter=lambda: self.__dict__.get('app'),
        )

    def _ensure_progress_tracker(self):
        try:
            object.__getattribute__(self, 'progress_tracker')
            return
        except AttributeError:
            pass
        try:
            diagnostic = object.__getattribute__(self, 'diagnostic')
        except AttributeError:
            diagnostic = RichDiagnosticAdapter(console, log)
        self.progress_tracker = TransferProgressTracker(
            transfer_store_getter=lambda: self.__dict__.get('transfer_store'),
            diagnostic=diagnostic,
            app_getter=lambda: self.__dict__.get('app'),
            gc_getter=lambda: self.__dict__.get('gc'),
            loop_getter=lambda: self.__dict__.get('loop'),
            pb_getter=lambda: self.__dict__.get('pb'),
            release_storage=getattr(self, 'release_transfer_local_storage', lambda wu: None),
            release_window=getattr(self, 'release_download_upload_window', lambda wu: None),
            start_download_upload=getattr(self, 'start_download_upload', lambda **kw: False),
            archive_pikpak_item=getattr(self, 'archive_pikpak_item', lambda **kw: None),
            fail_transfer_item=getattr(self, 'fail_transfer_item', lambda *a: None),
            refresh_counts=lambda tid: (
                self.__dict__.get('transfer_store').refresh_task_counts(tid)
                if self.__dict__.get('transfer_store') else None
            ),
            cleanup_local_file=lambda item_id: (
                getattr(self.__dict__.get('media_manager'), 'try_cleanup_item_file', lambda i: False)(item_id)
            ),
        )
    def _ensure_transfer_runner(self) -> WebTransferRunner:
        runner = self.__dict__.get('_transfer_runner')
        if runner is None:
            runner = WebTransferRunner(host=self)
            self._transfer_runner = runner
        return runner


TelegramRestrictedMediaDownloader = TrmdCompositionRoot

__all__ = ['TrmdCompositionRoot', 'TelegramRestrictedMediaDownloader']