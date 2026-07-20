# coding=UTF-8
import os
import sqlite3
import datetime
import threading
import time

from typing import Optional, List, Dict, Any

from module.core.media_types import normalize_media_types, serialize_media_types


class TransferStatus:
    PENDING = 'pending'
    RUNNING = 'running'
    PAUSING = 'pausing'
    PAUSED = 'paused'
    SKIPPED = 'skipped'
    SUCCESS = 'success'
    FAILURE = 'failure'


class ExecutionMode:
    """Transfer Task 的执行归属：web 队列编排 vs 监听内联下载回退。"""
    WEB_QUEUE = 'web_queue'
    WATCH_INLINE = 'watch_inline'


class DeferredDiscussionCaptureStatus:
    PENDING = 'pending'
    RUNNING = 'running'
    DONE = 'done'
    CANCELLED = 'cancelled'
    FAILURE = 'failure'


class TransferStore:
    FILE_NAME = 'transfer_tasks.sqlite3'
    DEFAULT_MAINTENANCE_MIN_INTERVAL_SECONDS = 6 * 60 * 60
    DEFAULT_RECONCILE_MIN_INTERVAL_SECONDS = 60
    STALE_TRANSFER_ITEM_TIMEOUT_SECONDS = 30 * 60
    STALE_EMPTY_WATCH_INLINE_TIMEOUT_SECONDS = 10 * 60
    DEFAULT_EVENT_PURGE_MIN_INTERVAL_SECONDS = 7 * 24 * 60 * 60
    TRANSFER_EVENTS_RETENTION_DAYS = 90
    LIVE_WATCH_EVENTS_RETENTION_DAYS = 30
    CLEANUP_LOG_RETENTION_DAYS = 30
    SYSTEM_LOGS_RETENTION_DAYS = 2
    VACUUM_FREE_PAGE_THRESHOLD = 512

    def __init__(self, directory: str):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        self.path = os.path.join(directory, self.FILE_NAME)
        self._last_maintenance_check = 0.0
        self._last_reconcile_check = 0.0
        self._schema_ready = False
        self._tls = threading.local()
        self._init_schema()
        self._schema_ready = True
        self.maintain()

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

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                '''
                CREATE TABLE IF NOT EXISTS transfer_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_link TEXT NOT NULL,
                    target_link TEXT NOT NULL,
                    target_profile TEXT NOT NULL DEFAULT 'pikpak',
                    start_id INTEGER,
                    end_id INTEGER,
                    status TEXT NOT NULL,
                    total_items INTEGER NOT NULL DEFAULT 0,
                    completed_items INTEGER NOT NULL DEFAULT 0,
                    failed_items INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    assignment_completed INTEGER NOT NULL DEFAULT 0,
                    include_comment INTEGER NOT NULL DEFAULT 0,
                    resolve_deep_link INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS transfer_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL REFERENCES transfer_tasks(id) ON DELETE CASCADE,
                    source_chat_id TEXT,
                    source_message_id INTEGER,
                    source_link TEXT,
                    target_link TEXT NOT NULL,
                    media_type TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    local_path TEXT,
                    temp_path TEXT,
                    phase TEXT NOT NULL DEFAULT 'pending',
                    download_current INTEGER NOT NULL DEFAULT 0,
                    download_total INTEGER NOT NULL DEFAULT 0,
                    download_speed_bps INTEGER NOT NULL DEFAULT 0,
                    upload_current INTEGER NOT NULL DEFAULT 0,
                    upload_total INTEGER NOT NULL DEFAULT 0,
                    upload_speed_bps INTEGER NOT NULL DEFAULT 0,
                    source_folder TEXT,
                    archive_path TEXT,
                    archive_status TEXT,
                    archive_error TEXT,
                    archive_match_original_name INTEGER,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transfer_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL REFERENCES transfer_tasks(id) ON DELETE CASCADE,
                    item_id INTEGER REFERENCES transfer_items(id) ON DELETE SET NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS download_success_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_chat_id TEXT NOT NULL,
                    source_message_id INTEGER NOT NULL,
                    source_link TEXT,
                    media_type TEXT,
                    local_path TEXT NOT NULL,
                    file_size INTEGER,
                    file_name TEXT,
                    downloaded_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(source_chat_id, source_message_id)
                );

                CREATE TABLE IF NOT EXISTS live_transfer_watches (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    source_link TEXT NOT NULL,
                    target_link TEXT,
                    include_comment INTEGER NOT NULL DEFAULT 0,
                    resolve_deep_link INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                '''
            )
            self._ensure_columns(
                conn,
                'transfer_tasks',
                {
                    'assignment_completed': 'INTEGER NOT NULL DEFAULT 0',
                    'include_comment': 'INTEGER NOT NULL DEFAULT 0',
                    'resolve_deep_link': 'INTEGER NOT NULL DEFAULT 0',
                    'current_range_message_id': 'INTEGER',
                    'current_range_video_captured': 'INTEGER NOT NULL DEFAULT 0',
                    'current_range_video_index': 'INTEGER NOT NULL DEFAULT 0',
                    'execution_mode': "TEXT NOT NULL DEFAULT 'web_queue'",
                    'watch_id': 'TEXT',
                    'media_types': 'TEXT',
                    'archive_by_author': 'INTEGER NOT NULL DEFAULT 0',
                }
            )
            self._ensure_columns(
                conn,
                'transfer_items',
                {
                    'range_message_id': 'INTEGER',
                    'source_chat_id': 'TEXT',
                    'file_name': 'TEXT',
                    'file_size': 'INTEGER',
                    'temp_path': 'TEXT',
                    'phase': "TEXT NOT NULL DEFAULT 'pending'",
                    'download_current': 'INTEGER NOT NULL DEFAULT 0',
                    'download_total': 'INTEGER NOT NULL DEFAULT 0',
                    'download_speed_bps': 'INTEGER NOT NULL DEFAULT 0',
                    'upload_current': 'INTEGER NOT NULL DEFAULT 0',
                    'upload_total': 'INTEGER NOT NULL DEFAULT 0',
                    'upload_speed_bps': 'INTEGER NOT NULL DEFAULT 0',
                    'source_folder': 'TEXT',
                    'archive_path': 'TEXT',
                    'archive_status': 'TEXT',
                    'archive_error': 'TEXT',
                    'archive_match_original_name': 'INTEGER',
                    'local_file_deleted': 'INTEGER NOT NULL DEFAULT 0'
                }
            )
            conn.executescript(
                '''
                CREATE TABLE IF NOT EXISTS cleanup_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    source_task_id INTEGER,
                    source_item_id INTEGER,
                    reason TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS live_watch_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    watch_id TEXT NOT NULL,
                    source_chat_id TEXT,
                    source_message_id INTEGER,
                    target_chat_id TEXT,
                    target_link TEXT,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT,
                    category TEXT NOT NULL,
                    level TEXT NOT NULL DEFAULT 'info',
                    stage TEXT NOT NULL,
                    watch_id TEXT,
                    source_chat_id TEXT,
                    source_message_id INTEGER,
                    target_link TEXT,
                    message TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS deferred_discussion_captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    watch_id TEXT NOT NULL,
                    source_chat_id TEXT NOT NULL,
                    source_message_id INTEGER NOT NULL,
                    target_chat_id TEXT NOT NULL,
                    target_link TEXT NOT NULL,
                    due_at REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(watch_id, source_chat_id, source_message_id)
                );

                CREATE TABLE IF NOT EXISTS archive_author_jobs (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    channel_folder TEXT NOT NULL,
                    status TEXT NOT NULL,
                    phase TEXT,
                    current_count INTEGER NOT NULL DEFAULT 0,
                    total_count INTEGER NOT NULL DEFAULT 0,
                    percent INTEGER NOT NULL DEFAULT 0,
                    message TEXT,
                    error TEXT,
                    result_json TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                '''
            )
            self._ensure_columns(
                conn,
                'live_transfer_watches',
                {
                    'target_link': 'TEXT',
                    'include_comment': 'INTEGER NOT NULL DEFAULT 0',
                    'resolve_deep_link': 'INTEGER NOT NULL DEFAULT 0',
                    'status': f"TEXT NOT NULL DEFAULT '{TransferStatus.PENDING}'",
                    'error_message': 'TEXT',
                    'media_types': 'TEXT',
                    'archive_by_author': 'INTEGER NOT NULL DEFAULT 0',
                }
            )
            self._ensure_indexes(conn)

    @staticmethod
    def _ensure_indexes(conn: sqlite3.Connection) -> None:
        conn.executescript(
            '''
            CREATE INDEX IF NOT EXISTS idx_transfer_tasks_id_desc
                ON transfer_tasks(id DESC);
            CREATE INDEX IF NOT EXISTS idx_transfer_items_task_order
                ON transfer_items(task_id, id ASC);
            CREATE INDEX IF NOT EXISTS idx_transfer_items_task_message
                ON transfer_items(task_id, source_message_id, source_chat_id, id ASC);
            CREATE INDEX IF NOT EXISTS idx_transfer_items_task_status
                ON transfer_items(task_id, status);
            CREATE INDEX IF NOT EXISTS idx_transfer_items_task_status_msg
                ON transfer_items(task_id, status, source_message_id);
            CREATE INDEX IF NOT EXISTS idx_transfer_events_task_order
                ON transfer_events(task_id, id DESC);
            CREATE INDEX IF NOT EXISTS idx_download_records_updated_order
                ON download_success_records(updated_at DESC, id DESC);
            CREATE INDEX IF NOT EXISTS idx_live_transfer_watches_created_order
                ON live_transfer_watches(created_at ASC, id ASC);
            CREATE INDEX IF NOT EXISTS idx_live_watch_events_watch_order
                ON live_watch_events(watch_id, id DESC);
            CREATE INDEX IF NOT EXISTS idx_live_watch_events_watch_created
                ON live_watch_events(watch_id, created_at DESC, id DESC);
            CREATE INDEX IF NOT EXISTS idx_system_logs_created_order
                ON system_logs(created_at DESC, id DESC);
            CREATE INDEX IF NOT EXISTS idx_system_logs_trace_order
                ON system_logs(trace_id, id ASC);
            CREATE INDEX IF NOT EXISTS idx_system_logs_category_created
                ON system_logs(category, created_at DESC, id DESC);
            CREATE INDEX IF NOT EXISTS idx_deferred_discussion_due
                ON deferred_discussion_captures(status, due_at ASC, id ASC);
            CREATE INDEX IF NOT EXISTS idx_deferred_discussion_watch
                ON deferred_discussion_captures(watch_id, status, id DESC);
            CREATE INDEX IF NOT EXISTS idx_archive_author_jobs_status_updated
                ON archive_author_jobs(status, updated_at DESC);
            '''
        )

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

    @staticmethod
    def _ensure_columns(conn: sqlite3.Connection, table: str, columns: Dict[str, str]) -> None:
        existing = {
            str(row['name'])
            for row in conn.execute(f'PRAGMA table_info({table})').fetchall()
        }
        for column, ddl in columns.items():
            if column not in existing:
                conn.execute(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}')

    def create_task(
            self,
            source_link: str,
            target_link: str = 'https://t.me/pikpak_bot',
            target_profile: str = 'pikpak',
            start_id: Optional[int] = None,
            end_id: Optional[int] = None,
            include_comment: bool = False,
            resolve_deep_link: bool = False,
            archive_by_author: bool = False,
            execution_mode: str = ExecutionMode.WEB_QUEUE,
            watch_id: Optional[str] = None,
            media_types: Optional[dict] = None,
    ) -> int:
        now = self.utc_now()
        mode = execution_mode or ExecutionMode.WEB_QUEUE
        if mode not in (ExecutionMode.WEB_QUEUE, ExecutionMode.WATCH_INLINE):
            mode = ExecutionMode.WEB_QUEUE
        media_types_json = serialize_media_types(media_types)
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO transfer_tasks (
                    source_link, target_link, target_profile, start_id, end_id,
                    include_comment, resolve_deep_link, archive_by_author,
                    execution_mode, watch_id,
                    media_types, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    source_link, target_link, target_profile, start_id, end_id,
                    int(bool(include_comment)), int(bool(resolve_deep_link)),
                    int(bool(archive_by_author)),
                    mode, watch_id or None, media_types_json,
                    TransferStatus.PENDING, now, now
                )
            )
            task_id = int(cursor.lastrowid)
            conn.execute(
                '''
                INSERT INTO transfer_events (task_id, level, message, created_at)
                VALUES (?, ?, ?, ?)
                ''',
                (task_id, 'info', 'Transfer task created.', now)
            )
            return task_id

    @staticmethod
    def _task_row(row: sqlite3.Row) -> Dict[str, Any]:
        task = dict(row)
        task['resolve_deep_link'] = bool(task.get('resolve_deep_link'))
        task['archive_by_author'] = bool(task.get('archive_by_author'))
        task['assignment_completed'] = bool(task.get('assignment_completed'))
        task['execution_mode'] = task.get('execution_mode') or ExecutionMode.WEB_QUEUE
        task['watch_id'] = task.get('watch_id') or None
        task['media_types'] = normalize_media_types(task.get('media_types'))
        return task

    def list_tasks(
            self,
            limit: int = 100,
            *,
            execution_mode: Optional[str] = None,
            exclude_execution_mode: Optional[str] = None,
            watch_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if execution_mode:
            clauses.append('execution_mode = ?')
            params.append(execution_mode)
        if exclude_execution_mode:
            clauses.append("(COALESCE(execution_mode, 'web_queue') != ?)")
            params.append(exclude_execution_mode)
        if watch_id:
            clauses.append('watch_id = ?')
            params.append(watch_id)
        where_sql = ('WHERE ' + ' AND '.join(clauses)) if clauses else ''
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f'''
                SELECT * FROM transfer_tasks
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                ''',
                tuple(params)
            ).fetchall()
            return [self._task_row(row) for row in rows]

    def summarize_watch_inline_tasks_by_watch_id(self) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT watch_id, status, COUNT(*) AS count
                FROM transfer_tasks
                WHERE execution_mode = ?
                  AND watch_id IS NOT NULL
                  AND TRIM(watch_id) != ''
                GROUP BY watch_id, status
                ''',
                (ExecutionMode.WATCH_INLINE,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_watch_inline_tasks_without_watch_id(self, limit: int = 5000) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM transfer_tasks
                WHERE execution_mode = ?
                  AND (watch_id IS NULL OR TRIM(watch_id) = '')
                ORDER BY id DESC
                LIMIT ?
                ''',
                (ExecutionMode.WATCH_INLINE, limit),
            ).fetchall()
            return [self._task_row(row) for row in rows]

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM transfer_tasks WHERE id = ?', (task_id,)).fetchone()
            return self._task_row(row) if row else None

    def update_task(
            self,
            task_id: int,
            status: Optional[str] = None,
            total_items: Optional[int] = None,
            completed_items: Optional[int] = None,
            failed_items: Optional[int] = None,
            error_message: Optional[str] = None,
            started: bool = False,
            finished: bool = False,
            assignment_completed: Optional[bool] = None
    ) -> None:
        task = self.get_task(task_id)
        if not task:
            return
        now = self.utc_now()
        values = {
            'status': status if status is not None else task['status'],
            'total_items': total_items if total_items is not None else task['total_items'],
            'completed_items': completed_items if completed_items is not None else task['completed_items'],
            'failed_items': failed_items if failed_items is not None else task['failed_items'],
            'error_message': error_message if error_message is not None else task['error_message'],
            'updated_at': now,
            'started_at': now if started and not task['started_at'] else task['started_at'],
            'finished_at': (
                now
                if finished
                else None if status in (
                    TransferStatus.PENDING,
                    TransferStatus.RUNNING,
                    TransferStatus.PAUSING,
                )
                else task['finished_at']
            ),
            'assignment_completed': (
                int(assignment_completed)
                if assignment_completed is not None
                else int(task.get('assignment_completed') or 0)
            )
        }
        with self.connect() as conn:
            conn.execute(
                '''
                UPDATE transfer_tasks
                SET status = :status,
                    total_items = :total_items,
                    completed_items = :completed_items,
                    failed_items = :failed_items,
                    error_message = :error_message,
                    updated_at = :updated_at,
                    started_at = :started_at,
                    finished_at = :finished_at,
                    assignment_completed = :assignment_completed
                WHERE id = :task_id
                ''',
                {**values, 'task_id': task_id}
            )

    def add_item(
            self,
            task_id: int,
            source_message_id: Optional[int],
            source_link: Optional[str],
            target_link: str,
            source_chat_id: Optional[str] = None,
            range_message_id: Optional[int] = None,
            media_type: Optional[str] = None,
            file_name: Optional[str] = None,
            file_size: Optional[int] = None,
            local_path: Optional[str] = None,
            temp_path: Optional[str] = None,
            source_folder: Optional[str] = None,
            archive_path: Optional[str] = None,
            archive_status: Optional[str] = None,
            archive_error: Optional[str] = None,
            archive_match_original_name: Optional[bool] = None,
            phase: str = 'pending',
            status: str = TransferStatus.PENDING,
            error_message: Optional[str] = None
    ) -> int:
        now = self.utc_now()
        with self.connect() as conn:
            if source_message_id is not None:
                row = conn.execute(
                    '''
                    SELECT id FROM transfer_items
                    WHERE task_id = ?
                      AND source_message_id = ?
                      AND COALESCE(source_chat_id, '') = COALESCE(?, '')
                    ORDER BY id ASC
                    LIMIT 1
                    ''',
                    (task_id, source_message_id, str(source_chat_id) if source_chat_id is not None else None)
                ).fetchone()
                if row:
                    item_id = int(row['id'])
                    existing = conn.execute(
                        'SELECT status FROM transfer_items WHERE id = ?',
                        (item_id,),
                    ).fetchone()
                    existing_status = str((existing['status'] if existing else '') or '')
                    active_statuses = {TransferStatus.RUNNING, TransferStatus.PENDING}
                    done_statuses = {TransferStatus.SUCCESS, TransferStatus.SKIPPED}
                    # Never reopen a completed item via upsert — resume must pass item_id explicitly.
                    if existing_status in done_statuses and str(status or '') in active_statuses:
                        return item_id
                    self._update_item_with_connection(
                        conn=conn,
                        item_id=item_id,
                        status=status,
                        source_chat_id=source_chat_id,
                        range_message_id=range_message_id,
                        media_type=media_type,
                        local_path=local_path,
                        temp_path=temp_path,
                        file_name=file_name,
                        file_size=file_size,
                        source_folder=source_folder,
                        archive_path=archive_path,
                        archive_status=archive_status,
                        archive_error=archive_error,
                        archive_match_original_name=archive_match_original_name,
                        phase=phase,
                        error_message=error_message,
                        now=now
                    )
                    return item_id
            cursor = conn.execute(
                '''
                INSERT INTO transfer_items (
                    task_id, source_chat_id, source_message_id, range_message_id, source_link, target_link,
                    media_type, file_name, file_size, local_path, temp_path, source_folder,
                    archive_path, archive_status, archive_error, archive_match_original_name, phase, status,
                    error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    task_id, source_chat_id, source_message_id, range_message_id, source_link, target_link,
                    media_type, file_name, file_size, local_path, temp_path, source_folder,
                    archive_path, archive_status, archive_error,
                    self._normalize_optional_bool(archive_match_original_name), phase, status,
                    error_message, now, now
                )
            )
            return int(cursor.lastrowid)

    def update_item(
            self,
            item_id: int,
            status: Optional[str] = None,
            source_chat_id: Optional[str] = None,
            media_type: Optional[str] = None,
            local_path: Optional[str] = None,
            temp_path: Optional[str] = None,
            file_name: Optional[str] = None,
            file_size: Optional[int] = None,
            phase: Optional[str] = None,
            source_folder: Optional[str] = None,
            archive_path: Optional[str] = None,
            archive_status: Optional[str] = None,
            archive_error: Optional[str] = None,
            archive_match_original_name: Optional[bool] = None,
            range_message_id: Optional[int] = None,
            error_message: Optional[str] = None
    ) -> None:
        now = self.utc_now()
        with self.connect() as conn:
            self._update_item_with_connection(
                conn=conn,
                item_id=item_id,
                status=status,
                source_chat_id=source_chat_id,
                media_type=media_type,
                local_path=local_path,
                temp_path=temp_path,
                file_name=file_name,
                file_size=file_size,
                source_folder=source_folder,
                archive_path=archive_path,
                archive_status=archive_status,
                archive_error=archive_error,
                archive_match_original_name=archive_match_original_name,
                range_message_id=range_message_id,
                phase=phase,
                error_message=error_message,
                now=now
            )

    @staticmethod
    def _update_item_with_connection(
            conn: sqlite3.Connection,
            item_id: int,
            now: str,
            status: Optional[str] = None,
            source_chat_id: Optional[str] = None,
            media_type: Optional[str] = None,
            local_path: Optional[str] = None,
            temp_path: Optional[str] = None,
            file_name: Optional[str] = None,
            file_size: Optional[int] = None,
            source_folder: Optional[str] = None,
            archive_path: Optional[str] = None,
            archive_status: Optional[str] = None,
            archive_error: Optional[str] = None,
            archive_match_original_name: Optional[bool] = None,
            range_message_id: Optional[int] = None,
            phase: Optional[str] = None,
            error_message: Optional[str] = None
    ) -> None:
        fields = {'updated_at': now}
        optional_fields = {
            'status': status,
            'source_chat_id': source_chat_id,
            'range_message_id': range_message_id,
            'media_type': media_type,
            'local_path': local_path,
            'temp_path': temp_path,
            'file_name': file_name,
            'file_size': file_size,
            'source_folder': source_folder,
            'archive_path': archive_path,
            'archive_status': archive_status,
            'archive_error': archive_error,
            'archive_match_original_name': TransferStore._normalize_optional_bool(archive_match_original_name),
            'phase': phase,
            'error_message': error_message
        }
        for key, value in optional_fields.items():
            if value is not None:
                fields[key] = value
        set_clause = ', '.join([f'{key} = :{key}' for key in fields])
        conn.execute(
            f'UPDATE transfer_items SET {set_clause} WHERE id = :item_id',
            {**fields, 'item_id': item_id}
        )

    @staticmethod
    def _normalize_optional_bool(value: Optional[bool]) -> Optional[int]:
        if value is None:
            return None
        return 1 if bool(value) else 0

    def rewrite_source_folder_path(
            self,
            *,
            channel_folder: str,
            from_relative: str,
            to_relative: str,
    ) -> int:
        """Rewrite Transfer Item source_folder rows that match a channel-relative move."""
        channel = str(channel_folder or '').replace('\\', '/').strip('/')
        from_rel = str(from_relative or '').replace('\\', '/').strip('/')
        to_rel = str(to_relative or '').replace('\\', '/').strip('/')
        if not channel or not from_rel or not to_rel or from_rel == to_rel:
            return 0
        old_path = f'{channel}/{from_rel}'
        new_path = f'{channel}/{to_rel}'
        now = self.utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                UPDATE transfer_items
                SET source_folder = ?,
                    updated_at = ?
                WHERE REPLACE(TRIM(COALESCE(source_folder, '')), '\\', '/') = ?
                ''',
                (new_path, now, old_path),
            )
            return int(cursor.rowcount or 0)

    def update_item_progress(
            self,
            item_id: int,
            phase: Optional[str] = None,
            download_current: Optional[int] = None,
            download_total: Optional[int] = None,
            download_speed_bps: Optional[int] = None,
            upload_current: Optional[int] = None,
            upload_total: Optional[int] = None,
            upload_speed_bps: Optional[int] = None
    ) -> None:
        fields = {'updated_at': self.utc_now()}
        values = {
            'phase': phase,
            'download_current': download_current,
            'download_total': download_total,
            'download_speed_bps': download_speed_bps,
            'upload_current': upload_current,
            'upload_total': upload_total,
            'upload_speed_bps': upload_speed_bps
        }
        for key, value in values.items():
            if value is not None:
                fields[key] = int(value) if key.endswith(('_current', '_total', '_bps')) else value
        set_clause = ', '.join([f'{key} = :{key}' for key in fields])
        with self.connect() as conn:
            conn.execute(
                f'UPDATE transfer_items SET {set_clause} WHERE id = :item_id',
                {**fields, 'item_id': item_id}
            )

    def list_items(self, task_id: int, limit: int = 0, offset: int = 0) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            if limit > 0:
                rows = conn.execute(
                    '''
                    SELECT * FROM transfer_items
                    WHERE task_id = ?
                    ORDER BY id ASC
                    LIMIT ? OFFSET ?
                    ''',
                    (task_id, limit, offset)
                ).fetchall()
            else:
                rows = conn.execute(
                    '''
                    SELECT * FROM transfer_items
                    WHERE task_id = ?
                    ORDER BY id ASC
                    ''',
                    (task_id,)
                ).fetchall()
            return [dict(row) for row in rows]

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                'SELECT * FROM transfer_items WHERE id = ?',
                (item_id,)
            ).fetchone()
            if row is None:
                return None
            return dict(row)

    def completed_source_message_ids(self, task_id: int) -> set[int]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT source_message_id FROM transfer_items
                WHERE task_id = ?
                  AND source_message_id IS NOT NULL
                  AND status IN (?, ?)
                ''',
                (task_id, TransferStatus.SUCCESS, TransferStatus.SKIPPED)
            ).fetchall()
            return {int(row['source_message_id']) for row in rows}

    @staticmethod
    def _terminal_item_statuses() -> set[str]:
        return {
            TransferStatus.SUCCESS,
            TransferStatus.SKIPPED,
            TransferStatus.FAILURE,
        }

    @staticmethod
    def _resumable_item_phases() -> set[str]:
        return {'downloading', 'uploading'}

    def list_items_for_range_message(self, task_id: int, range_message_id: int) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT *
                FROM transfer_items
                WHERE task_id = ?
                  AND (
                    range_message_id = ?
                    OR (
                        range_message_id IS NULL
                        AND source_message_id = ?
                    )
                  )
                ORDER BY id ASC
                ''',
                (int(task_id), int(range_message_id), int(range_message_id))
            ).fetchall()
        return [dict(row) for row in rows]

    def is_range_message_complete(self, task_id: int, range_message_id: int) -> bool:
        items = self.list_items_for_range_message(task_id, range_message_id)
        if not items:
            return False
        terminal_statuses = self._terminal_item_statuses()
        return all(str(item.get('status') or '') in terminal_statuses for item in items)

    def suppress_duplicate_active_items_for_range(
            self,
            task_id: int,
            range_message_id: int,
            *,
            source_chat_id=None,
    ) -> int:
        """Skip zombie active items when the same source message already has a terminal success/skip.

        Resume used to spawn unbound downloads that left RUNNING siblings next to SUCCESS
        rows; those zombies kept the range incomplete and triggered remount downloads.
        """
        terminal_done = {TransferStatus.SUCCESS, TransferStatus.SKIPPED}
        active = {TransferStatus.RUNNING, TransferStatus.PENDING}
        suppressed = 0
        items = self.list_items_for_range_message(task_id, range_message_id)
        by_source: dict[tuple, list] = {}
        for item in items:
            source_message_id = item.get('source_message_id')
            if source_message_id is None:
                continue
            chat_id = str(item.get('source_chat_id') or '')
            if source_chat_id is not None and chat_id and chat_id != str(source_chat_id):
                continue
            key = (chat_id, int(source_message_id))
            by_source.setdefault(key, []).append(item)
        for siblings in by_source.values():
            if not any(str(item.get('status') or '') in terminal_done for item in siblings):
                continue
            for item in siblings:
                if str(item.get('status') or '') not in active:
                    continue
                item_id = int(item.get('id') or 0)
                if not item_id:
                    continue
                self.update_item(
                    item_id,
                    status=TransferStatus.SKIPPED,
                    phase='skipped',
                    error_message='Superseded by a completed item for the same source message.',
                )
                self.add_event(
                    int(task_id),
                    f'Suppressed duplicate active item #{item_id}.',
                    level='warning',
                    item_id=item_id,
                )
                suppressed += 1
        if suppressed:
            self.refresh_task_counts(int(task_id))
        return suppressed

    def is_source_message_terminal(
            self,
            task_id: int,
            source_message_id: int,
            source_chat_id=None
    ) -> bool:
        normalized_chat_id = str(source_chat_id) if source_chat_id is not None else None
        terminal_statuses = self._terminal_item_statuses()
        for item in self.list_items(int(task_id)):
            if int(item.get('source_message_id') or -1) != int(source_message_id):
                continue
            item_chat_id = item.get('source_chat_id')
            if normalized_chat_id is not None and str(item_chat_id or '') != normalized_chat_id:
                continue
            if str(item.get('status') or '') in terminal_statuses:
                return True
        return False

    def list_resumable_items_for_range_message(
            self,
            task_id: int,
            range_message_id: int
    ) -> List[Dict[str, Any]]:
        resumable_statuses = {TransferStatus.RUNNING, TransferStatus.PENDING}
        resumable_phases = self._resumable_item_phases()
        return [
            item
            for item in self.list_items_for_range_message(task_id, range_message_id)
            if str(item.get('status') or '') in resumable_statuses
            and str(item.get('phase') or '') in resumable_phases
        ]

    def add_event(self, task_id: int, message: str, level: str = 'info', item_id: Optional[int] = None) -> None:
        with self.connect() as conn:
            conn.execute(
                '''
                INSERT INTO transfer_events (task_id, item_id, level, message, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (task_id, item_id, level, message, self.utc_now())
            )

    def list_events(self, task_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM transfer_events
                WHERE task_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                ''',
                (task_id, limit, offset)
            ).fetchall()
            return [dict(row) for row in rows]

    def task_payload(
            self,
            task_id: int,
            item_limit: int = 200,
            item_offset: int = 0,
            event_limit: int = 100,
            event_offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            task = conn.execute('SELECT * FROM transfer_tasks WHERE id = ?', (task_id,)).fetchone()
            if not task:
                return None
            total_items = conn.execute(
                'SELECT COUNT(*) FROM transfer_items WHERE task_id = ?', (task_id,)
            ).fetchone()[0]
            total_events = conn.execute(
                'SELECT COUNT(*) FROM transfer_events WHERE task_id = ?', (task_id,)
            ).fetchone()[0]
            items = conn.execute(
                '''
                SELECT * FROM transfer_items
                WHERE task_id = ?
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                ''',
                (task_id, item_limit, item_offset)
            ).fetchall()
            events = conn.execute(
                '''
                SELECT * FROM transfer_events
                WHERE task_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                ''',
                (task_id, event_limit, event_offset)
            ).fetchall()
        return {
            'task': dict(task),
            'items': [dict(row) for row in items],
            'events': [dict(row) for row in events],
            'item_count': total_items,
            'event_count': total_events,
            'has_more_items': (item_offset + len(items)) < total_items,
            'has_more_events': (event_offset + len(events)) < total_events,
            'items_offset': item_offset,
            'events_offset': event_offset,
        }

    def task_summary(self, task_id: int, recent_event_limit: int = 30) -> Optional[Dict[str, Any]]:
        """轻量级任务摘要查询——仅返回任务信息和计数，不加载 items/events 数组。
        用于 WebUI 轮询更新时避免重复加载大量数据。"""
        with self.connect() as conn:
            task = conn.execute('SELECT * FROM transfer_tasks WHERE id = ?', (task_id,)).fetchone()
            if not task:
                return None
            total_items = conn.execute(
                'SELECT COUNT(*) FROM transfer_items WHERE task_id = ?', (task_id,)
            ).fetchone()[0]
            total_events = conn.execute(
                'SELECT COUNT(*) FROM transfer_events WHERE task_id = ?', (task_id,)
            ).fetchone()[0]
            recent_events = conn.execute(
                '''
                SELECT * FROM transfer_events
                WHERE task_id = ?
                ORDER BY id DESC
                LIMIT ?
                ''',
                (task_id, recent_event_limit)
            ).fetchall()
        return {
            'task': dict(task),
            'item_count': total_items,
            'event_count': total_events,
            'recent_events': [dict(row) for row in recent_events],
        }

    def count_items(self, task_id: int) -> int:
        with self.connect() as conn:
            return conn.execute(
                'SELECT COUNT(*) FROM transfer_items WHERE task_id = ?', (task_id,)
            ).fetchone()[0]

    def aggregate_channel_download_stats(
            self,
            days: int = 7,
            tz_offset_minutes: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Aggregate terminal transfer items by source channel for a local window."""
        cutoff = self.local_calendar_window_start_utc(
            days=days,
            tz_offset_minutes=tz_offset_minutes,
        )
        terminal = (
            TransferStatus.SUCCESS,
            TransferStatus.FAILURE,
            TransferStatus.SKIPPED,
        )
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT
                    CASE
                        WHEN source_folder IS NOT NULL AND TRIM(source_folder) != ''
                            THEN CASE
                                WHEN INSTR(REPLACE(TRIM(source_folder), '\\', '/'), '/') > 0
                                    THEN SUBSTR(
                                        REPLACE(TRIM(source_folder), '\\', '/'),
                                        1,
                                        INSTR(REPLACE(TRIM(source_folder), '\\', '/'), '/') - 1
                                    )
                                ELSE TRIM(source_folder)
                            END
                        WHEN source_chat_id IS NOT NULL AND TRIM(CAST(source_chat_id AS TEXT)) != ''
                            THEN TRIM(CAST(source_chat_id AS TEXT))
                        ELSE 'unknown'
                    END AS channel,
                    status,
                    COUNT(*) AS cnt
                FROM transfer_items
                WHERE updated_at >= ?
                  AND status IN (?, ?, ?)
                GROUP BY channel, status
                ''',
                (cutoff, *terminal),
            ).fetchall()

        aggregated: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            channel = str(row['channel'] or 'unknown')
            bucket = aggregated.setdefault(
                channel,
                {
                    'channel': channel,
                    'success': 0,
                    'failure': 0,
                    'skip': 0,
                    'total': 0,
                },
            )
            count = int(row['cnt'] or 0)
            status = str(row['status'] or '')
            if status == TransferStatus.SUCCESS:
                bucket['success'] += count
            elif status == TransferStatus.FAILURE:
                bucket['failure'] += count
            elif status == TransferStatus.SKIPPED:
                bucket['skip'] += count
            bucket['total'] = bucket['success'] + bucket['failure'] + bucket['skip']

        return sorted(
            aggregated.values(),
            key=lambda item: (-int(item['total']), str(item['channel'])),
        )

    def count_events(self, task_id: int) -> int:
        with self.connect() as conn:
            return conn.execute(
                'SELECT COUNT(*) FROM transfer_events WHERE task_id = ?', (task_id,)
            ).fetchone()[0]

    @staticmethod
    def _iso_before_now(seconds: int) -> str:
        cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=max(0, int(seconds)))
        return cutoff.isoformat(timespec='seconds')

    def refresh_task_counts(
            self,
            task_id: int,
            expected_total: Optional[int] = None,
            assignment_completed: Optional[bool] = None
    ) -> None:
        task = self.get_task(task_id)
        if not task:
            return
        expected = expected_total if expected_total is not None else task.get('total_items')
        with self.connect(run_maintenance=False) as conn:
            rows = conn.execute(
                '''
                SELECT status, COUNT(*) AS count
                FROM transfer_items
                WHERE task_id = ?
                GROUP BY status
                ''',
                (task_id,)
            ).fetchall()
        counts = {str(row['status']): int(row['count']) for row in rows}
        item_count = sum(counts.values())
        expected = int(expected or item_count)
        completed = counts.get(TransferStatus.SUCCESS, 0) + counts.get(TransferStatus.SKIPPED, 0)
        failed = counts.get(TransferStatus.FAILURE, 0)
        active = counts.get(TransferStatus.RUNNING, 0) + counts.get(TransferStatus.PENDING, 0)
        assigned = bool(task.get('assignment_completed'))
        if assignment_completed is not None:
            assigned = assignment_completed

        status = TransferStatus.RUNNING
        finished = False
        error_message = task.get('error_message')
        if task.get('status') == TransferStatus.PAUSED:
            status = TransferStatus.PAUSED
        elif task.get('status') == TransferStatus.PAUSING:
            status = TransferStatus.PAUSING
        elif task.get('status') == TransferStatus.PENDING:
            status = TransferStatus.PENDING

        can_finalize = False
        if assigned and active == 0:
            can_finalize = True
        elif (
                active == 0
                and item_count > 0
                and expected_total is not None
                and item_count >= expected
                and (completed + failed) >= item_count
        ):
            # Backward compatible: explicit expected_total refresh after all items terminal.
            can_finalize = True
            assigned = True

        if can_finalize:
            if item_count == 0:
                status = TransferStatus.FAILURE
                finished = True
                expected = 0
                if not error_message:
                    error_message = 'No transfer items were produced.'
            else:
                status = TransferStatus.FAILURE if failed > 0 else TransferStatus.SUCCESS
                finished = True
                expected = item_count
        elif status == TransferStatus.PENDING and item_count == 0:
            status = TransferStatus.PENDING

        self.update_task(
            task_id=task_id,
            status=status,
            total_items=expected,
            completed_items=completed,
            failed_items=failed,
            error_message=error_message,
            finished=finished,
            assignment_completed=assigned
        )

    def reconcile_active_tasks(
            self,
            *,
            min_interval_seconds: int = DEFAULT_RECONCILE_MIN_INTERVAL_SECONDS,
            force: bool = False,
            item_timeout_seconds: int = STALE_TRANSFER_ITEM_TIMEOUT_SECONDS,
            empty_watch_timeout_seconds: int = STALE_EMPTY_WATCH_INLINE_TIMEOUT_SECONDS,
    ) -> int:
        if getattr(self._tls, 'reconciling', False):
            return 0
        now = datetime.datetime.now(datetime.UTC).timestamp()
        if (
                not force
                and now - self._last_reconcile_check < max(1, int(min_interval_seconds))
        ):
            return 0
        self._last_reconcile_check = now
        self._tls.reconciling = True
        try:
            changed = 0
            changed += self._fail_stale_active_items(item_timeout_seconds)
            changed += self._fail_stale_empty_watch_inline_tasks(empty_watch_timeout_seconds)

            with self.connect(run_maintenance=False) as conn:
                rows = conn.execute(
                    '''
                    SELECT id
                    FROM transfer_tasks
                    WHERE status IN (?, ?, ?)
                    ''',
                    (
                        TransferStatus.PENDING,
                        TransferStatus.RUNNING,
                        TransferStatus.PAUSING,
                    )
                ).fetchall()
            for row in rows:
                task_id = int(row['id'])
                before = self.get_task(task_id)
                self.refresh_task_counts(task_id)
                after = self.get_task(task_id)
                if before and after and (
                        before.get('status') != after.get('status')
                        or bool(before.get('finished')) != bool(after.get('finished'))
                ):
                    changed += 1
            return changed
        finally:
            self._tls.reconciling = False

    def _fail_stale_active_items(self, timeout_seconds: int) -> int:
        cutoff = self._iso_before_now(timeout_seconds)
        timeout_label = max(1, int(timeout_seconds) // 60)
        with self.connect(run_maintenance=False) as conn:
            rows = conn.execute(
                '''
                SELECT id, task_id
                FROM transfer_items
                WHERE status IN (?, ?)
                  AND updated_at < ?
                ''',
                (TransferStatus.PENDING, TransferStatus.RUNNING, cutoff)
            ).fetchall()
        if not rows:
            return 0
        now = self.utc_now()
        message = f'Transfer item timed out after {timeout_label} minutes without progress.'
        affected_tasks: set[int] = set()
        with self.connect(run_maintenance=False) as conn:
            for row in rows:
                item_id = int(row['id'])
                task_id = int(row['task_id'])
                conn.execute(
                    '''
                    UPDATE transfer_items
                    SET status = ?,
                        phase = 'failure',
                        error_message = ?,
                        updated_at = ?
                    WHERE id = ?
                    ''',
                    (TransferStatus.FAILURE, message, now, item_id)
                )
                affected_tasks.add(task_id)
        for task_id in affected_tasks:
            self.add_event(task_id, message, level='warning')
            self.refresh_task_counts(task_id)
        return len(rows)

    def _fail_stale_empty_watch_inline_tasks(self, timeout_seconds: int) -> int:
        cutoff = self._iso_before_now(timeout_seconds)
        timeout_label = max(1, int(timeout_seconds) // 60)
        with self.connect(run_maintenance=False) as conn:
            rows = conn.execute(
                '''
                SELECT t.id
                FROM transfer_tasks AS t
                LEFT JOIN transfer_items AS i ON i.task_id = t.id
                WHERE t.execution_mode = ?
                  AND t.status IN (?, ?, ?)
                  AND COALESCE(t.assignment_completed, 0) = 1
                  AND COALESCE(t.updated_at, t.created_at) < ?
                GROUP BY t.id
                HAVING COUNT(i.id) = 0
                ''',
                (
                    ExecutionMode.WATCH_INLINE,
                    TransferStatus.PENDING,
                    TransferStatus.RUNNING,
                    TransferStatus.PAUSING,
                    cutoff,
                )
            ).fetchall()
        changed = 0
        message = (
            f'Watch inline download timed out after {timeout_label} minutes '
            f'without producing transfer items.'
        )
        for row in rows:
            task_id = int(row['id'])
            self.update_task(
                task_id,
                status=TransferStatus.FAILURE,
                total_items=0,
                completed_items=0,
                failed_items=0,
                error_message=message,
                finished=True,
            )
            self.add_event(task_id, message, level='warning')
            changed += 1
        return changed

    def update_task_range_runtime(
            self,
            task_id: int,
            *,
            current_range_message_id: Optional[int] = None,
            current_range_video_captured: Optional[int] = None,
            current_range_video_index: Optional[int] = None
    ) -> None:
        task = self.get_task(task_id)
        if not task:
            return
        fields: dict[str, Any] = {'updated_at': self.utc_now()}
        if current_range_message_id is not None:
            fields['current_range_message_id'] = int(current_range_message_id)
        if current_range_video_captured is not None:
            fields['current_range_video_captured'] = max(0, int(current_range_video_captured))
        if current_range_video_index is not None:
            fields['current_range_video_index'] = max(0, int(current_range_video_index))
        if len(fields) <= 1:
            return
        set_clause = ', '.join([f'{key} = :{key}' for key in fields])
        with self.connect() as conn:
            conn.execute(
                f'UPDATE transfer_tasks SET {set_clause} WHERE id = :task_id',
                {**fields, 'task_id': int(task_id)}
            )

    def range_transfer_progress(self, task: dict[str, Any]) -> Optional[dict[str, int]]:
        start_id = task.get('start_id')
        end_id = task.get('end_id')
        if start_id is None or end_id is None:
            return None
        start_id = int(start_id)
        end_id = int(end_id)
        if end_id < start_id:
            return None

        task_id = int(task.get('id') or 0)
        terminal_statuses = {
            TransferStatus.SUCCESS,
            TransferStatus.SKIPPED,
            TransferStatus.FAILURE,
        }
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT
                    COALESCE(
                        range_message_id,
                        CASE
                            WHEN source_message_id BETWEEN ? AND ? THEN source_message_id
                        END
                    ) AS range_id,
                    status,
                    COUNT(*) AS count
                FROM transfer_items
                WHERE task_id = ?
                GROUP BY range_id, status
                HAVING range_id IS NOT NULL
                ''',
                (start_id, end_id, task_id)
            ).fetchall()

        counts_by_range: dict[int, dict[str, int]] = {}
        for row in rows:
            range_id = int(row['range_id'])
            if not (start_id <= range_id <= end_id):
                continue
            counts_by_range.setdefault(range_id, {})[str(row['status'])] = int(row['count'])

        total_ids = end_id - start_id + 1
        completed_ids = 0
        current_id: Optional[int] = None
        video_total = 0
        video_done = 0
        video_index = 0

        for message_id in range(start_id, end_id + 1):
            status_counts = counts_by_range.get(message_id)
            if not status_counts:
                if completed_ids == message_id - start_id:
                    current_id = message_id
                break

            total_videos = sum(status_counts.values())
            done_videos = sum(status_counts.get(status, 0) for status in terminal_statuses)
            if done_videos >= total_videos:
                completed_ids += 1
                continue

            current_id = message_id
            video_total = total_videos
            video_done = done_videos
            active_videos = (
                status_counts.get(TransferStatus.RUNNING, 0)
                + status_counts.get(TransferStatus.PENDING, 0)
            )
            video_index = done_videos + (1 if active_videos else 0)
            break
        else:
            completed_ids = total_ids

        runtime_current_id = task.get('current_range_message_id')
        runtime_captured = int(task.get('current_range_video_captured') or 0)
        runtime_index = int(task.get('current_range_video_index') or 0)
        if runtime_current_id is not None:
            runtime_current_id = int(runtime_current_id)
            if current_id is None or runtime_current_id >= current_id:
                current_id = runtime_current_id
            if runtime_captured > video_total:
                video_total = runtime_captured
            if runtime_index > video_index:
                video_index = runtime_index

        progress_percent = min(100, round((completed_ids / total_ids) * 100)) if total_ids else 0
        return {
            'range_total_ids': total_ids,
            'range_completed_ids': completed_ids,
            'range_progress_percent': progress_percent,
            'current_range_message_id': current_id,
            'current_range_video_total': video_total,
            'current_range_video_done': video_done,
            'current_range_video_index': video_index,
            'current_range_video_captured': runtime_captured,
            'uses_range_progress': True,
        }

    def retry_failed_items(self, task_id: int) -> int:
        task = self.get_task(task_id)
        if not task:
            return 0
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT id FROM transfer_items
                WHERE task_id = ? AND status = ?
                ORDER BY id ASC
                ''',
                (task_id, TransferStatus.FAILURE)
            ).fetchall()
            failed_item_ids = [int(row['id']) for row in rows]
        return self.retry_failed_item_ids(task_id, failed_item_ids)

    def retry_failed_item_ids(self, task_id: int, item_ids: List[int]) -> int:
        task = self.get_task(task_id)
        if not task:
            return 0
        item_ids = [int(item_id) for item_id in item_ids]
        if not item_ids:
            return 0
        now = self.utc_now()
        placeholders = ','.join(['?'] * len(item_ids))
        with self.connect() as conn:
            cursor = conn.execute(
                f'''
                UPDATE transfer_items
                SET status = ?,
                    phase = 'pending',
                    download_current = 0,
                    upload_current = 0,
                    error_message = NULL,
                    updated_at = ?
                WHERE task_id = ?
                  AND status = ?
                  AND id IN ({placeholders})
                ''',
                (TransferStatus.PENDING, now, task_id, TransferStatus.FAILURE, *item_ids)
            )
            reset_items = int(cursor.rowcount)
        if reset_items:
            self.refresh_task_counts(task_id)
            self.update_task(
                task_id,
                status=TransferStatus.RUNNING,
                error_message='',
                finished=False
            )
            self.add_event(task_id, f'Retry failed items requested: {reset_items}.')
        return reset_items

    def delete_task(self, task_id: int) -> bool:
        with self.connect() as conn:
            cursor = conn.execute('DELETE FROM transfer_tasks WHERE id = ?', (task_id,))
            return cursor.rowcount > 0

    def upsert_download_success_record(
            self,
            source_chat_id: str,
            source_message_id: int,
            source_link: Optional[str],
            media_type: Optional[str],
            local_path: str,
            file_size: Optional[int],
            file_name: Optional[str]
    ) -> None:
        now = self.utc_now()
        with self.connect() as conn:
            conn.execute(
                '''
                INSERT INTO download_success_records (
                    source_chat_id, source_message_id, source_link, media_type,
                    local_path, file_size, file_name, downloaded_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_chat_id, source_message_id) DO UPDATE SET
                    source_link = excluded.source_link,
                    media_type = excluded.media_type,
                    local_path = excluded.local_path,
                    file_size = excluded.file_size,
                    file_name = excluded.file_name,
                    updated_at = excluded.updated_at
                ''',
                (
                    str(source_chat_id), int(source_message_id), source_link, media_type,
                    local_path, file_size, file_name, now, now
                )
            )

    def get_download_success_record(
            self,
            source_chat_id: str,
            source_message_id: int,
            expected_size: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                '''
                SELECT * FROM download_success_records
                WHERE source_chat_id = ? AND source_message_id = ?
                ''',
                (str(source_chat_id), int(source_message_id))
            ).fetchone()
        if not row:
            return None
        record = dict(row)
        local_path = record.get('local_path')
        if not local_path or not os.path.isfile(local_path):
            return None
        size_to_check = expected_size if expected_size is not None else record.get('file_size')
        if size_to_check is not None and os.path.getsize(local_path) != int(size_to_check):
            return None
        return record

    def count_download_success_records(self) -> int:
        with self.connect() as conn:
            row = conn.execute(
                'SELECT COUNT(*) AS total FROM download_success_records'
            ).fetchone()
            return int(row['total'] if row else 0)

    def list_download_success_records(
            self,
            limit: int = 100,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM download_success_records
                ORDER BY updated_at DESC, id DESC
                LIMIT ? OFFSET ?
                ''',
                (limit, offset)
            ).fetchall()
            return [dict(row) for row in rows]

    def clear_download_success_records(self) -> int:
        with self.connect() as conn:
            cursor = conn.execute('DELETE FROM download_success_records')
            conn.commit()
            return int(cursor.rowcount or 0)

    # --- cleanup_log ---

    def insert_cleanup_log(
            self,
            file_path: str,
            file_size: Optional[int] = None,
            source_task_id: Optional[int] = None,
            source_item_id: Optional[int] = None,
            reason: Optional[str] = None
    ) -> int:
        now = self.utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO cleanup_log (file_path, file_size, source_task_id, source_item_id, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (file_path, file_size, source_task_id, source_item_id, reason, now)
            )
            return cursor.lastrowid

    def list_cleanup_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM cleanup_log
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                ''',
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def mark_item_local_file_deleted(self, item_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                'UPDATE transfer_items SET local_file_deleted = 1 WHERE id = ?',
                (item_id,)
            )

    def list_cleanable_items(self, task_id: int = None) -> List[Dict[str, Any]]:
        """返回 local_path 非空、status 已终结（success/failure/skipped）且尚未标记删除的 item。

        可选 task_id 用于按任务筛选。"""
        with self.connect() as conn:
            if task_id:
                rows = conn.execute(
                    '''
                    SELECT ti.*, tt.source_link AS task_source_link, tt.target_link AS task_target_link
                    FROM transfer_items ti
                    JOIN transfer_tasks tt ON tt.id = ti.task_id
                    WHERE ti.task_id = ?
                      AND ti.local_path IS NOT NULL
                      AND ti.local_path != ''
                      AND ti.local_file_deleted = 0
                      AND ti.status IN (?, ?, ?)
                    ORDER BY ti.updated_at DESC
                    ''',
                    (int(task_id), TransferStatus.SUCCESS, TransferStatus.FAILURE, TransferStatus.SKIPPED)
                ).fetchall()
            else:
                rows = conn.execute(
                    '''
                    SELECT ti.*, tt.source_link AS task_source_link, tt.target_link AS task_target_link
                    FROM transfer_items ti
                    JOIN transfer_tasks tt ON tt.id = ti.task_id
                    WHERE ti.local_path IS NOT NULL
                      AND ti.local_path != ''
                      AND ti.local_file_deleted = 0
                      AND ti.status IN (?, ?, ?)
                    ORDER BY ti.updated_at DESC
                    ''',
                    (TransferStatus.SUCCESS, TransferStatus.FAILURE, TransferStatus.SKIPPED)
                ).fetchall()
            return [dict(row) for row in rows]

    def list_stale_active_items(self, task_id: int = None) -> List[Dict[str, Any]]:
        """返回挂在已终结任务上、但仍为 pending/running/paused 的残留 item。

        常见于 watch_inline 下载回退重复建 item 后留下的僵尸记录；本地文件可能仍占盘，
        媒体管理需要把它们当作可清理项。
        """
        active_statuses = (
            TransferStatus.PENDING,
            TransferStatus.RUNNING,
            TransferStatus.PAUSED,
        )
        terminal_task_statuses = (
            TransferStatus.SUCCESS,
            TransferStatus.FAILURE,
            TransferStatus.SKIPPED,
        )
        with self.connect() as conn:
            if task_id:
                rows = conn.execute(
                    '''
                    SELECT ti.*, tt.source_link AS task_source_link, tt.target_link AS task_target_link
                    FROM transfer_items ti
                    JOIN transfer_tasks tt ON tt.id = ti.task_id
                    WHERE ti.task_id = ?
                      AND ti.local_path IS NOT NULL
                      AND ti.local_path != ''
                      AND ti.local_file_deleted = 0
                      AND ti.status IN (?, ?, ?)
                      AND tt.status IN (?, ?, ?)
                    ORDER BY ti.updated_at DESC
                    ''',
                    (int(task_id), *active_statuses, *terminal_task_statuses)
                ).fetchall()
            else:
                rows = conn.execute(
                    '''
                    SELECT ti.*, tt.source_link AS task_source_link, tt.target_link AS task_target_link
                    FROM transfer_items ti
                    JOIN transfer_tasks tt ON tt.id = ti.task_id
                    WHERE ti.local_path IS NOT NULL
                      AND ti.local_path != ''
                      AND ti.local_file_deleted = 0
                      AND ti.status IN (?, ?, ?)
                      AND tt.status IN (?, ?, ?)
                    ORDER BY ti.updated_at DESC
                    ''',
                    (*active_statuses, *terminal_task_statuses)
                ).fetchall()
            return [dict(row) for row in rows]

    def list_ghost_items(self, task_id: int = None) -> List[Dict[str, Any]]:
        """返回已标记 local_file_deleted 但 local_path 仍非空的终结态 item（磁盘可能仍有残留）。"""
        with self.connect() as conn:
            if task_id:
                rows = conn.execute(
                    '''
                    SELECT ti.*, tt.source_link AS task_source_link, tt.target_link AS task_target_link
                    FROM transfer_items ti
                    JOIN transfer_tasks tt ON tt.id = ti.task_id
                    WHERE ti.task_id = ?
                      AND ti.local_path IS NOT NULL
                      AND ti.local_path != ''
                      AND ti.local_file_deleted = 1
                      AND ti.status IN (?, ?, ?)
                    ORDER BY ti.updated_at DESC
                    ''',
                    (int(task_id), TransferStatus.SUCCESS, TransferStatus.FAILURE, TransferStatus.SKIPPED)
                ).fetchall()
            else:
                rows = conn.execute(
                    '''
                    SELECT ti.*, tt.source_link AS task_source_link, tt.target_link AS task_target_link
                    FROM transfer_items ti
                    JOIN transfer_tasks tt ON tt.id = ti.task_id
                    WHERE ti.local_path IS NOT NULL
                      AND ti.local_path != ''
                      AND ti.local_file_deleted = 1
                      AND ti.status IN (?, ?, ?)
                    ORDER BY ti.updated_at DESC
                    ''',
                    (TransferStatus.SUCCESS, TransferStatus.FAILURE, TransferStatus.SKIPPED)
                ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def _live_transfer_watch_row(row: sqlite3.Row) -> Dict[str, Any]:
        watch = dict(row)
        watch['include_comment'] = bool(watch.get('include_comment'))
        watch['resolve_deep_link'] = bool(watch.get('resolve_deep_link'))
        watch['archive_by_author'] = bool(watch.get('archive_by_author'))
        watch['media_types'] = normalize_media_types(watch.get('media_types'))
        return watch

    def upsert_live_transfer_watch(
            self,
            watch_id: str,
            watch_type: str,
            source_link: str,
            target_link: Optional[str] = None,
            include_comment: bool = False,
            resolve_deep_link: bool = False,
            archive_by_author: bool = False,
            status: str = TransferStatus.PENDING,
            error_message: Optional[str] = None,
            media_types: Optional[dict] = None,
    ) -> Dict[str, Any]:
        now = self.utc_now()
        media_types_json = serialize_media_types(media_types)
        with self.connect() as conn:
            conn.execute(
                '''
                INSERT INTO live_transfer_watches (
                    id, type, source_link, target_link, include_comment, resolve_deep_link,
                    archive_by_author, media_types, status, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type = excluded.type,
                    source_link = excluded.source_link,
                    target_link = excluded.target_link,
                    include_comment = excluded.include_comment,
                    resolve_deep_link = excluded.resolve_deep_link,
                    archive_by_author = excluded.archive_by_author,
                    media_types = excluded.media_types,
                    status = excluded.status,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                ''',
                (
                    watch_id, watch_type, source_link, target_link,
                    int(bool(include_comment)), int(bool(resolve_deep_link)),
                    int(bool(archive_by_author)),
                    media_types_json, status, error_message, now, now
                )
            )
        return self.get_live_transfer_watch(watch_id) or {
            'id': watch_id,
            'type': watch_type,
            'source_link': source_link,
            'target_link': target_link,
            'include_comment': bool(include_comment),
            'resolve_deep_link': bool(resolve_deep_link),
            'archive_by_author': bool(archive_by_author),
            'media_types': normalize_media_types(media_types),
            'status': status,
            'error_message': error_message,
            'created_at': now,
            'updated_at': now
        }

    def list_live_transfer_watches(self, limit: int = 1000) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM live_transfer_watches
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                ''',
                (limit,)
            ).fetchall()
            return [self._live_transfer_watch_row(row) for row in rows]

    def get_live_transfer_watch(self, watch_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                'SELECT * FROM live_transfer_watches WHERE id = ?',
                (watch_id,)
            ).fetchone()
            return self._live_transfer_watch_row(row) if row else None

    def update_live_transfer_watch_status(
            self,
            watch_id: str,
            status: str,
            error_message: Optional[str] = None
    ) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                UPDATE live_transfer_watches
                SET status = ?,
                    error_message = ?,
                    updated_at = ?
                WHERE id = ?
                ''',
                (status, error_message, self.utc_now(), watch_id)
            )
            return cursor.rowcount > 0

    def delete_live_transfer_watch(self, watch_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute('DELETE FROM live_transfer_watches WHERE id = ?', (watch_id,))
            return cursor.rowcount > 0

    def add_live_watch_event(
            self,
            watch_id: str,
            source_chat_id: Optional[str],
            source_message_id: Optional[int],
            target_chat_id: Optional[str],
            target_link: Optional[str],
            status: str,
            message: str
    ) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO live_watch_events (
                    watch_id, source_chat_id, source_message_id,
                    target_chat_id, target_link, status, message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (watch_id, source_chat_id, source_message_id,
                 target_chat_id, target_link, status, message, self.utc_now())
            )
            return int(cursor.lastrowid)

    _LIVE_WATCH_EVENT_STATUS_FILTERS = {
        TransferStatus.SUCCESS,
        TransferStatus.SKIPPED,
        TransferStatus.FAILURE,
    }

    def _live_watch_event_where(
            self,
            watch_id: str,
            today_only: bool = False,
            tz_offset_minutes: int | None = None,
            status: str | None = None
    ) -> tuple[str, list[Any]]:
        where_sql = 'watch_id = ?'
        params: list[Any] = [watch_id]
        if today_only:
            start_at, end_at = self.local_today_utc_bounds(tz_offset_minutes)
            where_sql += ' AND created_at >= ? AND created_at < ?'
            params.extend([start_at, end_at])
        if status:
            if status == TransferStatus.FAILURE:
                where_sql += ' AND status NOT IN (?, ?)'
                params.extend([TransferStatus.SUCCESS, TransferStatus.SKIPPED])
            else:
                where_sql += ' AND status = ?'
                params.append(status)
        return where_sql, params

    def list_live_watch_events(
            self,
            watch_id: str,
            limit: int = 50,
            offset: int = 0,
            today_only: bool = False,
            tz_offset_minutes: int | None = None,
            status: str | None = None
    ) -> tuple:
        if status is not None and status not in self._LIVE_WATCH_EVENT_STATUS_FILTERS:
            raise ValueError('invalid_status')
        with self.connect() as conn:
            where_sql, params = self._live_watch_event_where(
                watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes,
                status=status
            )
            total = int(conn.execute(
                f'SELECT COUNT(*) FROM live_watch_events WHERE {where_sql}',
                params
            ).fetchone()[0])
            rows = conn.execute(
                f'''
                SELECT * FROM live_watch_events
                WHERE {where_sql}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                ''',
                [*params, limit, offset]
            ).fetchall()
            return [dict(row) for row in rows], total

    def count_live_watch_events_by_status(
            self,
            watch_id: str,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ) -> dict[str, int]:
        with self.connect() as conn:
            where_sql, params = self._live_watch_event_where(
                watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes
            )
            rows = conn.execute(
                f'''
                SELECT status, COUNT(*) AS cnt
                FROM live_watch_events
                WHERE {where_sql}
                GROUP BY status
                ''',
                params
            ).fetchall()
        success = 0
        skipped = 0
        failure = 0
        for row in rows:
            status = row['status'] if isinstance(row, sqlite3.Row) else row[0]
            count = int(row['cnt'] if isinstance(row, sqlite3.Row) else row[1])
            if status == TransferStatus.SUCCESS:
                success += count
            elif status == TransferStatus.SKIPPED:
                skipped += count
            else:
                failure += count
        return {
            'all': success + skipped + failure,
            'success': success,
            'skipped': skipped,
            'failure': failure,
        }

    def get_live_watch_event_count(
            self,
            watch_id: str,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ) -> int:
        with self.connect() as conn:
            where_sql, params = self._live_watch_event_where(
                watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes
            )
            return int(conn.execute(
                f'SELECT COUNT(*) FROM live_watch_events WHERE {where_sql}',
                params
            ).fetchone()[0])

    def delete_live_watch_events(self, watch_id: str) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                'DELETE FROM live_watch_events WHERE watch_id = ?',
                (watch_id,)
            )
            return int(cursor.rowcount)

    # --- system_logs ---

    def add_system_log(
            self,
            category: str,
            stage: str,
            message: str,
            level: str = 'info',
            trace_id: Optional[str] = None,
            watch_id: Optional[str] = None,
            source_chat_id: Optional[str] = None,
            source_message_id: Optional[int] = None,
            target_link: Optional[str] = None,
            details: Optional[dict | str] = None
    ) -> int:
        import json
        details_text = None
        if details is not None:
            details_text = details if isinstance(details, str) else json.dumps(details, ensure_ascii=False)
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO system_logs (
                    trace_id, category, level, stage, watch_id,
                    source_chat_id, source_message_id, target_link,
                    message, details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    trace_id, category, level, stage, watch_id,
                    source_chat_id, source_message_id, target_link,
                    message, details_text, self.utc_now()
                )
            )
            return int(cursor.lastrowid)

    # --- archive_author_jobs ---

    def upsert_archive_author_job(self, job: dict) -> None:
        import json
        result = job.get('result')
        result_json = None
        if result is not None:
            result_json = json.dumps(result, ensure_ascii=False)
        with self.connect() as conn:
            conn.execute(
                '''
                INSERT INTO archive_author_jobs (
                    id, kind, channel_folder, status, phase,
                    current_count, total_count, percent, message, error,
                    result_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kind = excluded.kind,
                    channel_folder = excluded.channel_folder,
                    status = excluded.status,
                    phase = excluded.phase,
                    current_count = excluded.current_count,
                    total_count = excluded.total_count,
                    percent = excluded.percent,
                    message = excluded.message,
                    error = excluded.error,
                    result_json = excluded.result_json,
                    updated_at = excluded.updated_at
                ''',
                (
                    job.get('id'),
                    job.get('kind'),
                    job.get('channel_folder'),
                    job.get('status'),
                    job.get('phase'),
                    int(job.get('current') or 0),
                    int(job.get('total') or 0),
                    int(job.get('percent') or 0),
                    job.get('message'),
                    job.get('error'),
                    result_json,
                    float(job.get('created_at') or time.time()),
                    float(job.get('updated_at') or time.time()),
                ),
            )

    def get_archive_author_job(self, job_id: str) -> Optional[dict]:
        import json
        with self.connect() as conn:
            row = conn.execute(
                'SELECT * FROM archive_author_jobs WHERE id = ?',
                (str(job_id),),
            ).fetchone()
        if not row:
            return None
        return self._archive_author_job_from_row(row, json)

    def list_archive_author_jobs(
            self,
            *,
            channel_folder: Optional[str] = None,
            status: Optional[str] = None,
            limit: int = 20,
    ) -> list[dict]:
        import json
        clauses = []
        params: list = []
        if channel_folder:
            clauses.append('channel_folder = ?')
            params.append(str(channel_folder))
        if status:
            clauses.append('status = ?')
            params.append(str(status))
        where = f'WHERE {" AND ".join(clauses)}' if clauses else ''
        params.append(max(int(limit or 20), 1))
        with self.connect() as conn:
            rows = conn.execute(
                f'''
                SELECT * FROM archive_author_jobs
                {where}
                ORDER BY updated_at DESC
                LIMIT ?
                ''',
                params,
            ).fetchall()
        return [self._archive_author_job_from_row(row, json) for row in rows]

    def mark_stale_archive_author_jobs(
            self,
            *,
            older_than_seconds: float = 0,
            message: str = '任务已中断（进程重启），请重新扫描。',
            kinds: Optional[tuple] = None,
    ) -> int:
        """Mark leftover running jobs as failure (e.g. after process restart).

        ``kinds`` limits which job kinds are marked stale. Reorganize jobs are
        typically excluded so they can resume from checkpoint after restart.
        """
        cutoff = time.time() - max(float(older_than_seconds or 0), 0)
        kind_list = None
        if kinds:
            kind_list = tuple(str(item) for item in kinds if str(item).strip())
        with self.connect() as conn:
            if kind_list:
                placeholders = ','.join('?' for _ in kind_list)
                cursor = conn.execute(
                    f'''
                    UPDATE archive_author_jobs
                    SET status = 'failure',
                        phase = 'error',
                        error = ?,
                        message = ?,
                        updated_at = ?
                    WHERE status = 'running'
                      AND updated_at <= ?
                      AND kind IN ({placeholders})
                    ''',
                    (message, message, time.time(), cutoff, *kind_list),
                )
            else:
                cursor = conn.execute(
                    '''
                    UPDATE archive_author_jobs
                    SET status = 'failure',
                        phase = 'error',
                        error = ?,
                        message = ?,
                        updated_at = ?
                    WHERE status = 'running'
                      AND updated_at <= ?
                    ''',
                    (message, message, time.time(), cutoff),
                )
            return int(cursor.rowcount or 0)

    @staticmethod
    def _archive_author_job_from_row(row, json_module) -> dict:
        result = None
        raw = row['result_json'] if 'result_json' in row.keys() else None
        if raw:
            try:
                result = json_module.loads(raw)
            except Exception:
                result = None
        return {
            'id': row['id'],
            'kind': row['kind'],
            'channel_folder': row['channel_folder'],
            'status': row['status'],
            'phase': row['phase'],
            'current': int(row['current_count'] or 0),
            'total': int(row['total_count'] or 0),
            'percent': int(row['percent'] or 0),
            'message': row['message'] or '',
            'error': row['error'],
            'result': result,
            'created_at': float(row['created_at'] or 0),
            'updated_at': float(row['updated_at'] or 0),
        }

    def list_system_logs(
            self,
            limit: int = 50,
            offset: int = 0,
            category: Optional[str] = None,
            level: Optional[str] = None,
            trace_id: Optional[str] = None,
            watch_id: Optional[str] = None,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ) -> tuple[list[Dict[str, Any]], int]:
        where_parts: list[str] = []
        params: list[Any] = []
        if category:
            where_parts.append('category = ?')
            params.append(category)
        if level:
            where_parts.append('level = ?')
            params.append(level)
        if trace_id:
            where_parts.append('trace_id = ?')
            params.append(trace_id)
        if watch_id:
            where_parts.append('watch_id = ?')
            params.append(watch_id)
        if today_only:
            start_at, end_at = self.local_today_utc_bounds(tz_offset_minutes)
            where_parts.append('created_at >= ? AND created_at < ?')
            params.extend([start_at, end_at])
        where_sql = ' AND '.join(where_parts) if where_parts else '1=1'
        with self.connect() as conn:
            total = int(conn.execute(
                f'SELECT COUNT(*) FROM system_logs WHERE {where_sql}',
                params
            ).fetchone()[0])
            rows = conn.execute(
                f'''
                SELECT * FROM system_logs
                WHERE {where_sql}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                ''',
                [*params, limit, offset]
            ).fetchall()
            return [dict(row) for row in rows], total

    # --- deferred_discussion_captures ---

    @staticmethod
    def _deferred_discussion_capture_row(row: sqlite3.Row) -> Dict[str, Any]:
        item = dict(row)
        item['source_message_id'] = int(item['source_message_id'])
        item['due_at'] = float(item['due_at'])
        item['source_chat_id'] = str(item['source_chat_id'])
        item['target_chat_id'] = str(item['target_chat_id'])
        return item

    def schedule_deferred_discussion_capture(
            self,
            watch_id: str,
            source_chat_id: str | int,
            source_message_id: int,
            target_chat_id: str | int,
            target_link: str,
            due_at: float,
    ) -> Dict[str, Any]:
        now = self.utc_now()
        source_chat = str(source_chat_id)
        target_chat = str(target_chat_id)
        message_id = int(source_message_id)
        with self.connect() as conn:
            existing = conn.execute(
                '''
                SELECT * FROM deferred_discussion_captures
                WHERE watch_id = ? AND source_chat_id = ? AND source_message_id = ?
                  AND status IN (?, ?)
                ''',
                (
                    watch_id, source_chat, message_id,
                    DeferredDiscussionCaptureStatus.PENDING,
                    DeferredDiscussionCaptureStatus.RUNNING,
                )
            ).fetchone()
            if existing:
                return self._deferred_discussion_capture_row(existing)
            conn.execute(
                '''
                INSERT INTO deferred_discussion_captures (
                    watch_id, source_chat_id, source_message_id,
                    target_chat_id, target_link, due_at, status,
                    error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                ON CONFLICT(watch_id, source_chat_id, source_message_id) DO UPDATE SET
                    target_chat_id = excluded.target_chat_id,
                    target_link = excluded.target_link,
                    due_at = excluded.due_at,
                    status = excluded.status,
                    error_message = NULL,
                    updated_at = excluded.updated_at
                WHERE deferred_discussion_captures.status NOT IN (?, ?)
                ''',
                (
                    watch_id, source_chat, message_id,
                    target_chat, target_link, float(due_at),
                    DeferredDiscussionCaptureStatus.PENDING,
                    now, now,
                    DeferredDiscussionCaptureStatus.PENDING,
                    DeferredDiscussionCaptureStatus.RUNNING,
                )
            )
            row = conn.execute(
                '''
                SELECT * FROM deferred_discussion_captures
                WHERE watch_id = ? AND source_chat_id = ? AND source_message_id = ?
                ''',
                (watch_id, source_chat, message_id)
            ).fetchone()
            return self._deferred_discussion_capture_row(row)

    def get_deferred_discussion_capture(self, capture_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                'SELECT * FROM deferred_discussion_captures WHERE id = ?',
                (int(capture_id),)
            ).fetchone()
            return self._deferred_discussion_capture_row(row) if row else None

    def list_deferred_discussion_captures(
            self,
            watch_id: Optional[str] = None,
            statuses: Optional[List[str]] = None,
            limit: int = 200,
            offset: int = 0,
    ) -> List[Dict[str, Any]]:
        where_parts: list[str] = []
        params: list[Any] = []
        if watch_id:
            where_parts.append('watch_id = ?')
            params.append(watch_id)
        if statuses:
            placeholders = ','.join('?' for _ in statuses)
            where_parts.append(f'status IN ({placeholders})')
            params.extend(statuses)
        where_sql = ' AND '.join(where_parts) if where_parts else '1=1'
        with self.connect() as conn:
            rows = conn.execute(
                f'''
                SELECT * FROM deferred_discussion_captures
                WHERE {where_sql}
                ORDER BY due_at ASC, id ASC
                LIMIT ? OFFSET ?
                ''',
                [*params, limit, offset]
            ).fetchall()
            return [self._deferred_discussion_capture_row(row) for row in rows]

    def claim_due_deferred_discussion_captures(self, now: float) -> List[Dict[str, Any]]:
        stamp = self.utc_now()
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT id FROM deferred_discussion_captures
                WHERE status = ? AND due_at <= ?
                ORDER BY due_at ASC, id ASC
                ''',
                (DeferredDiscussionCaptureStatus.PENDING, float(now))
            ).fetchall()
            claimed: List[Dict[str, Any]] = []
            for row in rows:
                capture_id = int(row['id'])
                cursor = conn.execute(
                    '''
                    UPDATE deferred_discussion_captures
                    SET status = ?, updated_at = ?
                    WHERE id = ? AND status = ?
                    ''',
                    (
                        DeferredDiscussionCaptureStatus.RUNNING,
                        stamp,
                        capture_id,
                        DeferredDiscussionCaptureStatus.PENDING,
                    )
                )
                if cursor.rowcount:
                    updated = conn.execute(
                        'SELECT * FROM deferred_discussion_captures WHERE id = ?',
                        (capture_id,)
                    ).fetchone()
                    if updated:
                        claimed.append(self._deferred_discussion_capture_row(updated))
            return claimed

    def mark_deferred_discussion_capture(
            self,
            capture_id: int,
            status: str,
            error_message: Optional[str] = None,
    ) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                UPDATE deferred_discussion_captures
                SET status = ?, error_message = ?, updated_at = ?
                WHERE id = ?
                ''',
                (status, error_message, self.utc_now(), int(capture_id))
            )
            return cursor.rowcount > 0

    def cancel_deferred_discussion_capture(self, capture_id: int) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                UPDATE deferred_discussion_captures
                SET status = ?, updated_at = ?
                WHERE id = ? AND status IN (?, ?)
                ''',
                (
                    DeferredDiscussionCaptureStatus.CANCELLED,
                    self.utc_now(),
                    int(capture_id),
                    DeferredDiscussionCaptureStatus.PENDING,
                    DeferredDiscussionCaptureStatus.RUNNING,
                )
            )
            return cursor.rowcount > 0

    def cancel_deferred_discussion_captures_for_watch(self, watch_id: str) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                UPDATE deferred_discussion_captures
                SET status = ?, updated_at = ?
                WHERE watch_id = ? AND status IN (?, ?)
                ''',
                (
                    DeferredDiscussionCaptureStatus.CANCELLED,
                    self.utc_now(),
                    watch_id,
                    DeferredDiscussionCaptureStatus.PENDING,
                    DeferredDiscussionCaptureStatus.RUNNING,
                )
            )
            return int(cursor.rowcount)

    def requeue_deferred_discussion_capture(
            self,
            capture_id: int,
            *,
            due_at: float,
    ) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                UPDATE deferred_discussion_captures
                SET status = ?, due_at = ?, error_message = NULL, updated_at = ?
                WHERE id = ? AND status IN (?, ?)
                ''',
                (
                    DeferredDiscussionCaptureStatus.PENDING,
                    float(due_at),
                    self.utc_now(),
                    int(capture_id),
                    DeferredDiscussionCaptureStatus.FAILURE,
                    DeferredDiscussionCaptureStatus.CANCELLED,
                )
            )
            return cursor.rowcount > 0

    def fail_running_deferred_discussion_captures(
            self,
            capture_ids: List[int],
            *,
            error_message: str,
    ) -> List[Dict[str, Any]]:
        """Mark specific running captures as failure. Returns pre-update snapshots."""
        ids = [int(capture_id) for capture_id in capture_ids]
        if not ids:
            return []
        snapshots: List[Dict[str, Any]] = []
        with self.connect() as conn:
            for capture_id in ids:
                row = conn.execute(
                    'SELECT * FROM deferred_discussion_captures WHERE id = ? AND status = ?',
                    (capture_id, DeferredDiscussionCaptureStatus.RUNNING),
                ).fetchone()
                if not row:
                    continue
                snapshots.append(self._deferred_discussion_capture_row(row))
                conn.execute(
                    '''
                    UPDATE deferred_discussion_captures
                    SET status = ?, error_message = ?, updated_at = ?
                    WHERE id = ? AND status = ?
                    ''',
                    (
                        DeferredDiscussionCaptureStatus.FAILURE,
                        error_message,
                        self.utc_now(),
                        capture_id,
                        DeferredDiscussionCaptureStatus.RUNNING,
                    ),
                )
        return snapshots

    def requeue_running_deferred_discussion_captures(
            self,
            capture_ids: List[int],
            *,
            due_at: float,
    ) -> List[Dict[str, Any]]:
        """Requeue specific running captures as pending. Returns pre-update snapshots."""
        ids = [int(capture_id) for capture_id in capture_ids]
        if not ids:
            return []
        snapshots: List[Dict[str, Any]] = []
        stamp = self.utc_now()
        with self.connect() as conn:
            for capture_id in ids:
                row = conn.execute(
                    'SELECT * FROM deferred_discussion_captures WHERE id = ? AND status = ?',
                    (capture_id, DeferredDiscussionCaptureStatus.RUNNING),
                ).fetchone()
                if not row:
                    continue
                snapshots.append(self._deferred_discussion_capture_row(row))
                conn.execute(
                    '''
                    UPDATE deferred_discussion_captures
                    SET status = ?, due_at = ?, error_message = NULL, updated_at = ?
                    WHERE id = ? AND status = ?
                    ''',
                    (
                        DeferredDiscussionCaptureStatus.PENDING,
                        float(due_at),
                        stamp,
                        capture_id,
                        DeferredDiscussionCaptureStatus.RUNNING,
                    ),
                )
        return snapshots
