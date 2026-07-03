# coding=UTF-8
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, Dict, Union

from module.ports import IDiagnosticPort


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
