# coding=UTF-8
"""Focused Protocol seams.

Each consumer imports only the smallest protocol it needs.  God protocols
(``IBotHost`` / ``IPikPakTarget``) were removed in favour of per-consumer seams.
"""
from typing import Optional, Protocol, runtime_checkable

import asyncio


@runtime_checkable
class IWatchOps(Protocol):
    def list_watches(self, tz_offset_minutes: int | None = None) -> list: ...
    def create_watch(self, payload: dict) -> dict: ...
    def update_watch(self, watch_id: str, payload: dict) -> dict: ...
    def delete_watch(self, watch_id: str) -> bool: ...
    def list_watch_events(
        self,
        watch_id: str,
        limit: int = 50,
        offset: int = 0,
        today_only: bool = False,
        tz_offset_minutes: int | None = None,
        status: str | None = None,
    ) -> Optional[dict]: ...


@runtime_checkable
class ITaskOps(Protocol):
    def delete_web_task(self, task_id: int) -> bool: ...
    def pause_web_task(self, task_id: int) -> bool: ...
    def resume_web_task(self, task_id: int) -> bool: ...
    def retry_failed_web_task(self, task_id: int) -> int: ...
    def submit_web_task(self, task_id: int) -> None: ...
    def detect_transfer_range(self, source_link: str) -> Optional[tuple]: ...


@runtime_checkable
class IMediaOps(Protocol):
    def scan_media_for_cleanup(
        self,
        task_id: int = None,
        items_limit: int = None,
        items_offset: int = 0,
        orphans_limit: int = None,
        orphans_offset: int = 0,
    ) -> dict: ...
    def cleanup_media_files(self, payload: dict) -> dict: ...
    def list_cleanup_logs(self) -> list: ...


@runtime_checkable
class IStatsOps(Protocol):
    def statistics(self, tz_offset_minutes: int | None = None) -> dict: ...
    def export_table(self, table_type: str) -> dict: ...
    def list_operations(self, limit: int = 50) -> list: ...


@runtime_checkable
class IUploadOps(Protocol):
    def create_upload(self, payload: dict) -> dict: ...
    def create_channel_download(self, payload: dict) -> dict: ...


@runtime_checkable
class IWebUiOperations(IWatchOps, ITaskOps, IMediaOps, IStatsOps, IUploadOps, Protocol):
    """Combined WebUI operations seam for typing convenience."""


@runtime_checkable
class IBotCallbackHost(Protocol):
    """Only the host surface actually consumed by CallbackHandler."""

    bot: object
    cd: object
    download_upload_window: object
    listen_download_chat: dict
    listen_forward_chat: dict
    web_watch_handler_clients: dict
    web_pending_watches: dict
    adding_keywords: list
    download_chat_filter: dict
    last_message: object
    last_client: object

    async def help(self) -> dict: ...
    async def table(self) -> dict: ...
    async def get_download_link_from_bot(self, client, message, with_upload=None) -> None: ...
    def build_download_upload_meta(self, *args, **kwargs) -> dict: ...
    def download_watch_id(self, link: str) -> str: ...
    def forward_watch_id(self, rule: str) -> str: ...
    def add_keyword_mode_handler(self, *args, **kwargs) -> None: ...
    async def download_chat(self, chat_id, callback_query) -> None: ...


@runtime_checkable
class IUploadContext(Protocol):
    """Focused upload dependencies: config, loop, progress, diagnostics, lifetime."""

    app: object
    loop: asyncio.AbstractEventLoop
    pb: object
    done_notice: object
    my_id: int
    is_running: bool
    is_bot_running: bool
    web_ui: Optional[object]
    wait_for_telegram_flood: object
    diagnostic: object


@runtime_checkable
class IDiagnosticPort(Protocol):
    def info(self, message: str, *args, **kwargs) -> None: ...
    def warning(self, message: str, *args, **kwargs) -> None: ...
    def error(self, message: str, *args, **kwargs) -> None: ...
    def debug(self, message: str, *args, **kwargs) -> None: ...
    def exception(self, message: str, *args, **kwargs) -> None: ...
    def console_log(self, *args, **kwargs) -> None: ...
    def console_print(self, *args, **kwargs) -> None: ...
