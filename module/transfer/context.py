# coding=UTF-8
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, Dict

from module.ports import IDiagnosticPort


def _noop(*_a, **_kw):
    return None


def _noop_str(*_a, **_kw):
    return ''


def _noop_false(*_a, **_kw):
    return False


def _noop_dict(*_a, **_kw):
    return {}


def _identity_wu(wu):
    return wu


@dataclass
class TransferPathPorts:
    """Local path resolution for download destinations."""
    env_save_directory: Callable = field(default=_noop_str)
    get_final_save_directory: Callable = field(default=_noop_str)
    get_final_file_path: Callable = field(default=_noop_str)


@dataclass
class TransferProgressPorts:
    """Transfer item progress / bot status callbacks used by TransferEngine."""
    record_transfer_download_success: Callable = field(default=lambda **kw: None)
    on_transfer_file_ready: Callable = field(default=_noop)
    on_transfer_item_skipped: Callable = field(default=_noop)
    on_transfer_item_failed: Callable = field(default=_noop)
    on_transfer_upload_progress: Callable = field(default=_noop)
    on_transfer_upload_status: Callable = field(default=_noop)
    build_bot_transfer_progress_text: Callable = field(default=_noop_str)
    schedule_bot_transfer_progress_update: Callable = field(default=_noop)


@dataclass
class TransferTargetPorts:
    """Target profile / upload-meta helpers (incl. PikPak detection)."""
    infer_target_profile: Callable = field(default=lambda *a, **kw: None)
    is_pikpak_target: Callable = field(default=_noop_false)
    normalize_download_upload_meta: Callable = field(default=_identity_wu)
    build_transfer_upload_meta: Callable = field(default=_noop_dict)


@dataclass
class TransferStoragePorts:
    """Local disk budget + download/upload concurrency window release."""
    release_download_upload_window: Callable = field(default=_noop)
    release_transfer_local_storage: Callable = field(default=_noop)
    mark_transfer_local_storage_materialized: Callable = field(default=_noop)


@dataclass
class TransferRuntimePorts:
    """Host runtime state still required by the download-complete path."""
    ensure_uploader: Callable = field(default=lambda: None)
    bot_task_link: Callable = field(default=lambda: set())
    queue: Callable = field(default=lambda: None)
    pb_progress: Callable = field(default=lambda: None)
    event: Callable = field(default=lambda: None)
    create_download_task: Callable = field(default=_noop_dict)
    detect_transfer_range_async: Callable = field(default=lambda *a, **kw: None)


@dataclass
class TransferPorts:
    """Host callbacks for TransferEngine — duty-clustered seams (not a flat bag)."""
    paths: TransferPathPorts = field(default_factory=TransferPathPorts)
    progress: TransferProgressPorts = field(default_factory=TransferProgressPorts)
    target: TransferTargetPorts = field(default_factory=TransferTargetPorts)
    storage: TransferStoragePorts = field(default_factory=TransferStoragePorts)
    runtime: TransferRuntimePorts = field(default_factory=TransferRuntimePorts)

    @classmethod
    def from_host(cls, host: Any) -> 'TransferPorts':
        """Build clustered ports from composition root; missing attrs fall back to no-ops."""
        def _attr(name: str, default):
            return getattr(host, name, default)

        return cls(
            paths=TransferPathPorts(
                env_save_directory=_attr('env_save_directory', _noop_str),
                get_final_save_directory=_attr('get_final_save_directory', _noop_str),
                get_final_file_path=_attr('get_final_file_path', _noop_str),
            ),
            progress=TransferProgressPorts(
                record_transfer_download_success=_attr(
                    'record_transfer_download_success', lambda **kw: None
                ),
                on_transfer_file_ready=_attr('on_transfer_file_ready', _noop),
                on_transfer_item_skipped=_attr('on_transfer_item_skipped', _noop),
                on_transfer_item_failed=_attr('on_transfer_item_failed', _noop),
                on_transfer_upload_progress=_attr('on_transfer_upload_progress', _noop),
                on_transfer_upload_status=_attr('on_transfer_upload_status', _noop),
                build_bot_transfer_progress_text=_attr(
                    'build_bot_transfer_progress_text', _noop_str
                ),
                schedule_bot_transfer_progress_update=_attr(
                    'schedule_bot_transfer_progress_update', _noop
                ),
            ),
            target=TransferTargetPorts(
                infer_target_profile=_attr('infer_target_profile', lambda *a, **kw: None),
                is_pikpak_target=_attr('is_pikpak_target', _noop_false),
                normalize_download_upload_meta=_attr(
                    'normalize_download_upload_meta', _identity_wu
                ),
                build_transfer_upload_meta=_attr('build_transfer_upload_meta', _noop_dict),
            ),
            storage=TransferStoragePorts(
                release_download_upload_window=_attr(
                    'release_download_upload_window', _noop
                ),
                release_transfer_local_storage=_attr(
                    'release_transfer_local_storage', _noop
                ),
                mark_transfer_local_storage_materialized=_attr(
                    'mark_transfer_local_storage_materialized', _noop
                ),
            ),
            runtime=TransferRuntimePorts(
                ensure_uploader=_attr('ensure_uploader', lambda: None),
                bot_task_link=lambda: getattr(host, 'bot_task_link', set()),
                queue=lambda: getattr(host, 'queue', None),
                pb_progress=lambda: getattr(getattr(host, 'pb', None), 'progress', None),
                event=lambda: getattr(host, 'event', None),
                create_download_task=_attr('create_download_task', _noop_dict),
                detect_transfer_range_async=_attr(
                    'detect_transfer_range_async', lambda *a, **kw: None
                ),
            ),
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
