# coding=UTF-8
import sqlite3
from typing import Dict

from module.persistence.store.status import TransferStatus

class SchemaMixin:
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
                    'comment_delay_minutes': 'INTEGER',
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

    @staticmethod
    def _ensure_columns(conn: sqlite3.Connection, table: str, columns: Dict[str, str]) -> None:
        existing = {
            str(row['name'])
            for row in conn.execute(f'PRAGMA table_info({table})').fetchall()
        }
        for column, ddl in columns.items():
            if column not in existing:
                conn.execute(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}')
