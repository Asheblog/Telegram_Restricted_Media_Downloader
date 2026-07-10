# coding=UTF-8
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, Dict

from module.ports import IDiagnosticPort


@dataclass
class TransferPorts:
    """Host callbacks for TransferEngine — one seam replacing 30+ getter lambdas."""
    env_save_directory: Callable = field(default=lambda *a, **kw: '')
    get_final_save_directory: Callable = field(default=lambda *a, **kw: '')
    get_final_file_path: Callable = field(default=lambda *a, **kw: '')
    infer_target_profile: Callable = field(default=lambda *a, **kw: None)
    normalize_download_upload_meta: Callable = field(default=lambda wu: wu)
    is_pikpak_target: Callable = field(default=lambda *a, **kw: False)
    build_transfer_upload_meta: Callable = field(default=lambda *a, **kw: {})
    notify_bot_transfer_download_progress: Callable = field(default=lambda *a, **kw: None)
    notify_bot_transfer_downloaded: Callable = field(default=lambda *a, **kw: None)
    record_transfer_download_success: Callable = field(default=lambda **kw: None)
    try_reuse_transfer_download_record: Callable = field(default=lambda *a, **kw: False)
    on_transfer_file_ready: Callable = field(default=lambda *a, **kw: None)
    on_transfer_item_skipped: Callable = field(default=lambda *a, **kw: None)
    on_transfer_item_failed: Callable = field(default=lambda *a, **kw: None)
    on_transfer_upload_progress: Callable = field(default=lambda *a, **kw: None)
    on_transfer_upload_status: Callable = field(default=lambda *a, **kw: None)
    notify_bot_transfer_upload_progress: Callable = field(default=lambda *a, **kw: None)
    notify_bot_transfer_upload_status: Callable = field(default=lambda *a, **kw: None)
    release_download_upload_window: Callable = field(default=lambda wu: None)
    release_transfer_local_storage: Callable = field(default=lambda wu: None)
    mark_transfer_local_storage_materialized: Callable = field(default=lambda wu: None)
    transfer_send_interval: Callable = field(default=lambda: 1.0)
    ensure_uploader: Callable = field(default=lambda: None)
    build_bot_transfer_progress_text: Callable = field(default=lambda *a, **kw: '')
    schedule_bot_transfer_progress_update: Callable = field(default=lambda *a, **kw: None)
    bot_task_link: Callable = field(default=lambda: set())
    queue: Callable = field(default=lambda: None)
    pb_progress: Callable = field(default=lambda: None)
    event: Callable = field(default=lambda: None)
    create_download_task: Callable = field(default=lambda **kw: {})
    detect_transfer_range_async: Callable = field(default=lambda *a, **kw: None)

    @classmethod
    def from_host(cls, host: Any) -> 'TransferPorts':
        """Build ports from composition root; missing attrs fall back to no-ops."""
        def _attr(name: str, default):
            return getattr(host, name, default)

        return cls(
            env_save_directory=_attr('env_save_directory', lambda *a, **kw: ''),
            get_final_save_directory=_attr('get_final_save_directory', lambda *a, **kw: ''),
            get_final_file_path=_attr('get_final_file_path', lambda *a, **kw: ''),
            infer_target_profile=_attr('infer_target_profile', lambda *a, **kw: None),
            normalize_download_upload_meta=_attr('normalize_download_upload_meta', lambda wu: wu),
            is_pikpak_target=_attr('is_pikpak_target', lambda *a, **kw: False),
            build_transfer_upload_meta=_attr('build_transfer_upload_meta', lambda *a, **kw: {}),
            notify_bot_transfer_download_progress=_attr(
                'notify_bot_transfer_download_progress', lambda *a, **kw: None
            ),
            notify_bot_transfer_downloaded=_attr('notify_bot_transfer_downloaded', lambda *a, **kw: None),
            record_transfer_download_success=_attr('record_transfer_download_success', lambda **kw: None),
            try_reuse_transfer_download_record=_attr(
                'try_reuse_transfer_download_record', lambda *a, **kw: False
            ),
            on_transfer_file_ready=_attr('on_transfer_file_ready', lambda *a, **kw: None),
            on_transfer_item_skipped=_attr('on_transfer_item_skipped', lambda *a, **kw: None),
            on_transfer_item_failed=_attr('on_transfer_item_failed', lambda *a, **kw: None),
            on_transfer_upload_progress=_attr('on_transfer_upload_progress', lambda *a, **kw: None),
            on_transfer_upload_status=_attr('on_transfer_upload_status', lambda *a, **kw: None),
            notify_bot_transfer_upload_progress=_attr(
                'notify_bot_transfer_upload_progress', lambda *a, **kw: None
            ),
            notify_bot_transfer_upload_status=_attr(
                'notify_bot_transfer_upload_status', lambda *a, **kw: None
            ),
            release_download_upload_window=_attr('release_download_upload_window', lambda wu: None),
            release_transfer_local_storage=_attr('release_transfer_local_storage', lambda wu: None),
            mark_transfer_local_storage_materialized=_attr(
                'mark_transfer_local_storage_materialized', lambda wu: None
            ),
            transfer_send_interval=_attr('transfer_send_interval', lambda: 1.0),
            ensure_uploader=_attr('ensure_uploader', lambda: None),
            build_bot_transfer_progress_text=_attr('build_bot_transfer_progress_text', lambda *a, **kw: ''),
            schedule_bot_transfer_progress_update=_attr(
                'schedule_bot_transfer_progress_update', lambda *a, **kw: None
            ),
            bot_task_link=lambda: getattr(host, 'bot_task_link', set()),
            queue=lambda: getattr(host, 'queue', None),
            pb_progress=lambda: getattr(getattr(host, 'pb', None), 'progress', None),
            event=lambda: getattr(host, 'event', None),
            create_download_task=_attr('create_download_task', lambda **kw: {}),
            detect_transfer_range_async=_attr('detect_transfer_range_async', lambda *a, **kw: None),
        )


@dataclass
class TransferContext:
    """Holds shared services for transfer operations.
    Replaces 50+ individual getter lambdas with a single structured context.
    """
    app: Any = None
    gc: Any = None
    diagnostic: IDiagnosticPort = None
    loop: Optional[asyncio.AbstractEventLoop] = None
    my_id: int = 0

    uploader: Optional[Any] = None
    progress_tracker: Optional[Any] = None
    pikpak_manager: Optional[Any] = None
    watch_manager: Optional[Any] = None
    web_task_manager: Optional[Any] = None
    transfer_store: Optional[Any] = None
    local_storage_guard: Optional[Any] = None
    download_upload_window: Optional[Any] = None

    uploader_getter: Optional[Callable[[], Any]] = None
    progress_tracker_getter: Optional[Callable[[], Any]] = None
    pikpak_manager_getter: Optional[Callable[[], Any]] = None
    watch_manager_getter: Optional[Callable[[], Any]] = None
    web_task_manager_getter: Optional[Callable[[], Any]] = None
    transfer_store_getter: Optional[Callable[[], Any]] = None

    downloader_callbacks: Dict[str, Callable] = field(default_factory=dict)

    def build(self) -> 'TransferContext':
        for name in ('uploader', 'progress_tracker', 'pikpak_manager',
                      'watch_manager', 'web_task_manager', 'transfer_store'):
            getter = getattr(self, f'{name}_getter', None)
            if getter is not None and getattr(self, name, None) is None:
                try:
                    setattr(self, name, getter())
                except Exception:
                    pass
        return self

    def resolve(self, name: str, default=None):
        cb = self.downloader_callbacks.get(name)
        return cb if cb is not None else default
