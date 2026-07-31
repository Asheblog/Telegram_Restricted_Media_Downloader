# coding=UTF-8
import datetime  # noqa: F401 — re-export for tests that patch module.transfer_store.datetime
import os
import threading

from module.persistence.store.archive_jobs import ArchiveJobsMixin
from module.persistence.store.cleanup_logs import CleanupLogsMixin
from module.persistence.store.connection import ConnectionMixin
from module.persistence.store.deferred import DeferredMixin
from module.persistence.store.events import EventsMixin
from module.persistence.store.items import ItemsMixin
from module.persistence.store.maintenance import MaintenanceMixin
from module.persistence.store.schema import SchemaMixin
from module.persistence.store.constants import (
    CLEANUP_LOG_RETENTION_DAYS,
    DEFAULT_EVENT_PURGE_MIN_INTERVAL_SECONDS,
    DEFAULT_MAINTENANCE_MIN_INTERVAL_SECONDS,
    DEFAULT_RECONCILE_MIN_INTERVAL_SECONDS,
    LIVE_WATCH_EVENTS_RETENTION_DAYS,
    STALE_EMPTY_WATCH_INLINE_TIMEOUT_SECONDS,
    STALE_TRANSFER_ITEM_TIMEOUT_SECONDS,
    SYSTEM_LOGS_RETENTION_DAYS,
    TRANSFER_EVENTS_RETENTION_DAYS,
    VACUUM_FREE_PAGE_THRESHOLD,
)
from module.persistence.store.status import (
    DeferredDiscussionCaptureStatus,
    ExecutionMode,
    TransferStatus,
)
from module.persistence.store.system_logs import SystemLogsMixin
from module.persistence.store.tasks import TasksMixin
from module.persistence.store.watches import WatchesMixin

__all__ = [
    'TransferStore',
    'TransferStatus',
    'ExecutionMode',
    'DeferredDiscussionCaptureStatus',
]


class TransferStore(
    ConnectionMixin,
    SchemaMixin,
    MaintenanceMixin,
    TasksMixin,
    ItemsMixin,
    EventsMixin,
    WatchesMixin,
    DeferredMixin,
    ArchiveJobsMixin,
    SystemLogsMixin,
    CleanupLogsMixin,
):
    FILE_NAME = 'transfer_tasks.sqlite3'
    DEFAULT_MAINTENANCE_MIN_INTERVAL_SECONDS = DEFAULT_MAINTENANCE_MIN_INTERVAL_SECONDS
    DEFAULT_RECONCILE_MIN_INTERVAL_SECONDS = DEFAULT_RECONCILE_MIN_INTERVAL_SECONDS
    STALE_TRANSFER_ITEM_TIMEOUT_SECONDS = STALE_TRANSFER_ITEM_TIMEOUT_SECONDS
    STALE_EMPTY_WATCH_INLINE_TIMEOUT_SECONDS = STALE_EMPTY_WATCH_INLINE_TIMEOUT_SECONDS
    DEFAULT_EVENT_PURGE_MIN_INTERVAL_SECONDS = DEFAULT_EVENT_PURGE_MIN_INTERVAL_SECONDS
    TRANSFER_EVENTS_RETENTION_DAYS = TRANSFER_EVENTS_RETENTION_DAYS
    LIVE_WATCH_EVENTS_RETENTION_DAYS = LIVE_WATCH_EVENTS_RETENTION_DAYS
    CLEANUP_LOG_RETENTION_DAYS = CLEANUP_LOG_RETENTION_DAYS
    SYSTEM_LOGS_RETENTION_DAYS = SYSTEM_LOGS_RETENTION_DAYS
    VACUUM_FREE_PAGE_THRESHOLD = VACUUM_FREE_PAGE_THRESHOLD

    def __init__(self, directory: str):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        self.path = os.path.join(directory, self.FILE_NAME)
        self._last_maintenance_check = 0.0
        self._last_reconcile_check = 0.0
        self._schema_ready = False
        self._tls = threading.local()
        self._item_stale_timeout_seconds_getter = None
        self._stale_item_logger = None
        self._init_schema()
        self._schema_ready = True
        self.maintain()

