# coding=UTF-8
import os
import sqlite3
import datetime

from typing import Optional, List, Dict, Any


class TransferStatus:
    PENDING = 'pending'
    RUNNING = 'running'
    PAUSED = 'paused'
    SKIPPED = 'skipped'
    SUCCESS = 'success'
    FAILURE = 'failure'


class TransferStore:
    FILE_NAME = 'transfer_tasks.sqlite3'

    def __init__(self, directory: str):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        self.path = os.path.join(directory, self.FILE_NAME)
        self._init_schema()

    @staticmethod
    def utc_now() -> str:
        return datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA foreign_keys=ON')
        return conn

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
                    include_comment INTEGER NOT NULL DEFAULT 0
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
                    phase TEXT NOT NULL DEFAULT 'pending',
                    download_current INTEGER NOT NULL DEFAULT 0,
                    download_total INTEGER NOT NULL DEFAULT 0,
                    upload_current INTEGER NOT NULL DEFAULT 0,
                    upload_total INTEGER NOT NULL DEFAULT 0,
                    source_folder TEXT,
                    archive_path TEXT,
                    archive_status TEXT,
                    archive_error TEXT,
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
                    'include_comment': 'INTEGER NOT NULL DEFAULT 0'
                }
            )
            self._ensure_columns(
                conn,
                'transfer_items',
                {
                    'source_chat_id': 'TEXT',
                    'file_name': 'TEXT',
                    'file_size': 'INTEGER',
                    'phase': "TEXT NOT NULL DEFAULT 'pending'",
                    'download_current': 'INTEGER NOT NULL DEFAULT 0',
                    'download_total': 'INTEGER NOT NULL DEFAULT 0',
                    'upload_current': 'INTEGER NOT NULL DEFAULT 0',
                    'upload_total': 'INTEGER NOT NULL DEFAULT 0',
                    'source_folder': 'TEXT',
                    'archive_path': 'TEXT',
                    'archive_status': 'TEXT',
                    'archive_error': 'TEXT'
                }
            )
            self._ensure_columns(
                conn,
                'live_transfer_watches',
                {
                    'target_link': 'TEXT',
                    'include_comment': 'INTEGER NOT NULL DEFAULT 0',
                    'status': f"TEXT NOT NULL DEFAULT '{TransferStatus.PENDING}'",
                    'error_message': 'TEXT'
                }
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

    def create_task(
            self,
            source_link: str,
            target_link: str = 'https://t.me/pikpak_bot',
            target_profile: str = 'pikpak',
            start_id: Optional[int] = None,
            end_id: Optional[int] = None,
            include_comment: bool = False
    ) -> int:
        now = self.utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO transfer_tasks (
                    source_link, target_link, target_profile, start_id, end_id,
                    include_comment, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    source_link, target_link, target_profile, start_id, end_id,
                    int(bool(include_comment)), TransferStatus.PENDING, now, now
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

    def list_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM transfer_tasks
                ORDER BY id DESC
                LIMIT ?
                ''',
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM transfer_tasks WHERE id = ?', (task_id,)).fetchone()
            return dict(row) if row else None

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
                else None if status in (TransferStatus.PENDING, TransferStatus.RUNNING)
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
            media_type: Optional[str] = None,
            file_name: Optional[str] = None,
            file_size: Optional[int] = None,
            local_path: Optional[str] = None,
            source_folder: Optional[str] = None,
            archive_path: Optional[str] = None,
            archive_status: Optional[str] = None,
            archive_error: Optional[str] = None,
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
                    self._update_item_with_connection(
                        conn=conn,
                        item_id=item_id,
                        status=status,
                        source_chat_id=source_chat_id,
                        media_type=media_type,
                        local_path=local_path,
                        file_name=file_name,
                        file_size=file_size,
                        source_folder=source_folder,
                        archive_path=archive_path,
                        archive_status=archive_status,
                        archive_error=archive_error,
                        phase=phase,
                        error_message=error_message,
                        now=now
                    )
                    return item_id
            cursor = conn.execute(
                '''
                INSERT INTO transfer_items (
                    task_id, source_chat_id, source_message_id, source_link, target_link,
                    media_type, file_name, file_size, local_path, source_folder,
                    archive_path, archive_status, archive_error, phase, status,
                    error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    task_id, source_chat_id, source_message_id, source_link, target_link,
                    media_type, file_name, file_size, local_path, source_folder,
                    archive_path, archive_status, archive_error, phase, status,
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
            file_name: Optional[str] = None,
            file_size: Optional[int] = None,
            phase: Optional[str] = None,
            source_folder: Optional[str] = None,
            archive_path: Optional[str] = None,
            archive_status: Optional[str] = None,
            archive_error: Optional[str] = None,
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
                file_name=file_name,
                file_size=file_size,
                source_folder=source_folder,
                archive_path=archive_path,
                archive_status=archive_status,
                archive_error=archive_error,
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
            file_name: Optional[str] = None,
            file_size: Optional[int] = None,
            source_folder: Optional[str] = None,
            archive_path: Optional[str] = None,
            archive_status: Optional[str] = None,
            archive_error: Optional[str] = None,
            phase: Optional[str] = None,
            error_message: Optional[str] = None
    ) -> None:
        fields = {'updated_at': now}
        optional_fields = {
            'status': status,
            'source_chat_id': source_chat_id,
            'media_type': media_type,
            'local_path': local_path,
            'file_name': file_name,
            'file_size': file_size,
            'source_folder': source_folder,
            'archive_path': archive_path,
            'archive_status': archive_status,
            'archive_error': archive_error,
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

    def update_item_progress(
            self,
            item_id: int,
            phase: Optional[str] = None,
            download_current: Optional[int] = None,
            download_total: Optional[int] = None,
            upload_current: Optional[int] = None,
            upload_total: Optional[int] = None
    ) -> None:
        fields = {'updated_at': self.utc_now()}
        values = {
            'phase': phase,
            'download_current': download_current,
            'download_total': download_total,
            'upload_current': upload_current,
            'upload_total': upload_total
        }
        for key, value in values.items():
            if value is not None:
                fields[key] = int(value) if key.endswith(('_current', '_total')) else value
        set_clause = ', '.join([f'{key} = :{key}' for key in fields])
        with self.connect() as conn:
            conn.execute(
                f'UPDATE transfer_items SET {set_clause} WHERE id = :item_id',
                {**fields, 'item_id': item_id}
            )

    def list_items(self, task_id: int) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM transfer_items
                WHERE task_id = ?
                ORDER BY id ASC
                ''',
                (task_id,)
            ).fetchall()
            return [dict(row) for row in rows]

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

    def add_event(self, task_id: int, message: str, level: str = 'info', item_id: Optional[int] = None) -> None:
        with self.connect() as conn:
            conn.execute(
                '''
                INSERT INTO transfer_events (task_id, item_id, level, message, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (task_id, item_id, level, message, self.utc_now())
            )

    def list_events(self, task_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM transfer_events
                WHERE task_id = ?
                ORDER BY id DESC
                LIMIT ?
                ''',
                (task_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    def task_payload(self, task_id: int) -> Optional[Dict[str, Any]]:
        task = self.get_task(task_id)
        if not task:
            return None
        return {
            'task': task,
            'items': self.list_items(task_id),
            'events': self.list_events(task_id)
        }

    def refresh_task_counts(
            self,
            task_id: int,
            expected_total: Optional[int] = None,
            assignment_completed: Optional[bool] = None
    ) -> None:
        task = self.get_task(task_id)
        if not task:
            return
        items = self.list_items(task_id)
        expected = expected_total if expected_total is not None else task.get('total_items')
        expected = int(expected or len(items))
        completed = len([item for item in items if item.get('status') in (TransferStatus.SUCCESS, TransferStatus.SKIPPED)])
        failed = len([item for item in items if item.get('status') == TransferStatus.FAILURE])
        terminal = completed + failed
        assigned = bool(task.get('assignment_completed'))
        if assignment_completed is not None:
            assigned = assignment_completed
        elif expected_total is not None:
            assigned = True

        status = TransferStatus.RUNNING
        finished = False
        if task.get('status') == TransferStatus.PAUSED:
            status = TransferStatus.PAUSED
        if expected > 0 and assigned and len(items) >= expected and terminal >= expected:
            status = TransferStatus.FAILURE if failed else TransferStatus.SUCCESS
            finished = True
        elif task.get('status') == TransferStatus.PENDING and not items:
            status = TransferStatus.PENDING

        self.update_task(
            task_id=task_id,
            status=status,
            total_items=expected,
            completed_items=completed,
            failed_items=failed,
            finished=finished,
            assignment_completed=assigned
        )

    def retry_failed_items(self, task_id: int) -> int:
        task = self.get_task(task_id)
        if not task:
            return 0
        now = self.utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                UPDATE transfer_items
                SET status = ?,
                    phase = 'pending',
                    download_current = 0,
                    upload_current = 0,
                    error_message = NULL,
                    updated_at = ?
                WHERE task_id = ?
                  AND status = ?
                ''',
                (TransferStatus.PENDING, now, task_id, TransferStatus.FAILURE)
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

    def list_download_success_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                '''
                SELECT * FROM download_success_records
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                ''',
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def _live_transfer_watch_row(row: sqlite3.Row) -> Dict[str, Any]:
        watch = dict(row)
        watch['include_comment'] = bool(watch.get('include_comment'))
        return watch

    def upsert_live_transfer_watch(
            self,
            watch_id: str,
            watch_type: str,
            source_link: str,
            target_link: Optional[str] = None,
            include_comment: bool = False,
            status: str = TransferStatus.PENDING,
            error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        now = self.utc_now()
        with self.connect() as conn:
            conn.execute(
                '''
                INSERT INTO live_transfer_watches (
                    id, type, source_link, target_link, include_comment,
                    status, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type = excluded.type,
                    source_link = excluded.source_link,
                    target_link = excluded.target_link,
                    include_comment = excluded.include_comment,
                    status = excluded.status,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                ''',
                (
                    watch_id, watch_type, source_link, target_link,
                    int(bool(include_comment)), status, error_message, now, now
                )
            )
        return self.get_live_transfer_watch(watch_id) or {
            'id': watch_id,
            'type': watch_type,
            'source_link': source_link,
            'target_link': target_link,
            'include_comment': bool(include_comment),
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
