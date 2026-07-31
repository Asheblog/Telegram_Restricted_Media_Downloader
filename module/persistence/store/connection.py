# coding=UTF-8
import datetime
import sqlite3

class ConnectionMixin:
    @staticmethod
    def utc_now() -> str:
        return datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')

    @staticmethod
    def local_today_utc_bounds(tz_offset_minutes: int | None = None) -> tuple[str, str]:
        utc_now = datetime.datetime.now(datetime.UTC)
        if tz_offset_minutes is None:
            local_now = utc_now.astimezone()
            local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
            local_end = local_start + datetime.timedelta(days=1)
            return (
                local_start.astimezone(datetime.UTC).isoformat(timespec='seconds'),
                local_end.astimezone(datetime.UTC).isoformat(timespec='seconds')
            )
        # JavaScript Date.getTimezoneOffset(): UTC - local, in minutes.
        local_now = utc_now - datetime.timedelta(minutes=tz_offset_minutes)
        local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        local_end = local_start + datetime.timedelta(days=1)
        start_utc = (local_start + datetime.timedelta(minutes=tz_offset_minutes)).replace(tzinfo=datetime.UTC)
        end_utc = (local_end + datetime.timedelta(minutes=tz_offset_minutes)).replace(tzinfo=datetime.UTC)
        return (
            start_utc.isoformat(timespec='seconds'),
            end_utc.isoformat(timespec='seconds')
        )

    @staticmethod
    def retention_cutoff_iso(
            retention_days: int,
            now: datetime.datetime | None = None
    ) -> str:
        reference = now or datetime.datetime.now(datetime.UTC)
        cutoff = reference - datetime.timedelta(days=max(0, retention_days))
        return cutoff.isoformat(timespec='seconds')

    @classmethod
    def local_calendar_window_start_utc(
            cls,
            days: int,
            tz_offset_minutes: int | None = None,
    ) -> str:
        """UTC ISO start of a local calendar window that includes today.

        ``days=7`` means today plus the previous 6 local calendar days.
        """
        window_days = max(1, int(days))
        today_start, _ = cls.local_today_utc_bounds(tz_offset_minutes)
        start_dt = datetime.datetime.fromisoformat(today_start)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=datetime.UTC)
        window_start = start_dt - datetime.timedelta(days=window_days - 1)
        return window_start.astimezone(datetime.UTC).isoformat(timespec='seconds')

    def _get_conn(self) -> sqlite3.Connection:
        """返回当前线程缓存的数据库连接，首次调用时创建并配置。"""
        conn = getattr(self._tls, 'conn', None)
        if conn is None:
            conn = sqlite3.connect(self.path, timeout=30)
            conn.row_factory = sqlite3.Row
            self._configure_connection(conn)
            self._tls.conn = conn
        return conn

    def connect(self, run_maintenance: bool = True) -> sqlite3.Connection:
        if run_maintenance and self._schema_ready:
            self.maintain()
            if not getattr(self._tls, 'reconciling', False):
                self.reconcile_active_tasks()
        return self._get_conn()

    @staticmethod
    def _configure_connection(conn: sqlite3.Connection) -> None:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA temp_store=MEMORY')
        conn.execute('PRAGMA busy_timeout=30000')

    @staticmethod
    def _iso_before_now(seconds: int) -> str:
        cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=max(0, int(seconds)))
        return cutoff.isoformat(timespec='seconds')

    def close(self) -> None:
        """Close the thread-local SQLite connection so temp dirs can be removed on Windows."""
        conn = getattr(self._tls, 'conn', None)
        if conn is None:
            return
        try:
            conn.close()
        finally:
            self._tls.conn = None
