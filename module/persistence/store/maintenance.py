# coding=UTF-8
import datetime
import os
import sqlite3

from module.persistence.store.constants import (
    CLEANUP_LOG_RETENTION_DAYS,
    DEFAULT_EVENT_PURGE_MIN_INTERVAL_SECONDS,
    DEFAULT_MAINTENANCE_MIN_INTERVAL_SECONDS,
    LIVE_WATCH_EVENTS_RETENTION_DAYS,
    SYSTEM_LOGS_RETENTION_DAYS,
    TRANSFER_EVENTS_RETENTION_DAYS,
)


class MaintenanceMixin:
    def maintain(
            self,
            min_interval_seconds: int = DEFAULT_MAINTENANCE_MIN_INTERVAL_SECONDS,
            force: bool = False
    ) -> bool:
        marker_path = f'{self.path}.maintenance'
        now = datetime.datetime.now(datetime.UTC).timestamp()
        if not force and now - self._last_maintenance_check < min_interval_seconds:
            return False
        self._last_maintenance_check = now
        if not force and os.path.exists(marker_path):
            try:
                if now - os.path.getmtime(marker_path) < min_interval_seconds:
                    return False
            except OSError:
                pass

        try:
            with self.connect(run_maintenance=False) as conn:
                conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                conn.execute('PRAGMA optimize')
                page_count = int(conn.execute('PRAGMA page_count').fetchone()[0])
                free_pages = int(conn.execute('PRAGMA freelist_count').fetchone()[0])
                should_vacuum = force or (
                    free_pages >= self.VACUUM_FREE_PAGE_THRESHOLD
                    and free_pages >= max(1, page_count // 10)
                )
            if should_vacuum:
                vacuum_conn = sqlite3.connect(self.path, timeout=30)
                try:
                    self._configure_connection(vacuum_conn)
                    vacuum_conn.execute('VACUUM')
                    vacuum_conn.execute('PRAGMA optimize')
                finally:
                    vacuum_conn.close()
        except sqlite3.Error:
            return False

        try:
            with open(marker_path, 'w', encoding='UTF-8') as marker:
                marker.write(self.utc_now())
        except OSError:
            pass
        self.purge_old_event_records(force=force)
        return True

    def purge_old_transfer_events(
            self,
            retention_days: int = TRANSFER_EVENTS_RETENTION_DAYS,
            cutoff_at: str | None = None
    ) -> int:
        cutoff = cutoff_at or self.retention_cutoff_iso(retention_days)
        with self.connect(run_maintenance=False) as conn:
            cursor = conn.execute(
                'DELETE FROM transfer_events WHERE created_at < ?',
                (cutoff,)
            )
            return int(cursor.rowcount or 0)

    def purge_old_live_watch_events(
            self,
            retention_days: int = LIVE_WATCH_EVENTS_RETENTION_DAYS,
            cutoff_at: str | None = None
    ) -> int:
        cutoff = cutoff_at or self.retention_cutoff_iso(retention_days)
        with self.connect(run_maintenance=False) as conn:
            cursor = conn.execute(
                'DELETE FROM live_watch_events WHERE created_at < ?',
                (cutoff,)
            )
            return int(cursor.rowcount or 0)

    def purge_old_cleanup_logs(
            self,
            retention_days: int = CLEANUP_LOG_RETENTION_DAYS,
            cutoff_at: str | None = None
    ) -> int:
        cutoff = cutoff_at or self.retention_cutoff_iso(retention_days)
        with self.connect(run_maintenance=False) as conn:
            cursor = conn.execute(
                'DELETE FROM cleanup_log WHERE created_at < ?',
                (cutoff,)
            )
            return int(cursor.rowcount or 0)

    def purge_old_system_logs(
            self,
            retention_days: int = SYSTEM_LOGS_RETENTION_DAYS,
            cutoff_at: str | None = None
    ) -> int:
        cutoff = cutoff_at or self.retention_cutoff_iso(retention_days)
        with self.connect(run_maintenance=False) as conn:
            cursor = conn.execute(
                'DELETE FROM system_logs WHERE created_at < ?',
                (cutoff,)
            )
            return int(cursor.rowcount or 0)

    def purge_old_event_records(
            self,
            force: bool = False,
            min_interval_seconds: int = DEFAULT_EVENT_PURGE_MIN_INTERVAL_SECONDS
    ) -> dict[str, int] | None:
        marker_path = f'{self.path}.event_purge'
        now = datetime.datetime.now(datetime.UTC).timestamp()
        if not force and os.path.exists(marker_path):
            try:
                if now - os.path.getmtime(marker_path) < min_interval_seconds:
                    return None
            except OSError:
                pass

        counts = {
            'transfer_events': self.purge_old_transfer_events(),
            'live_watch_events': self.purge_old_live_watch_events(),
            'cleanup_log': self.purge_old_cleanup_logs(),
            'system_logs': self.purge_old_system_logs(),
        }
        try:
            with open(marker_path, 'w', encoding='UTF-8') as marker:
                marker.write(self.utc_now())
        except OSError:
            pass
        return counts
