# coding=UTF-8
import os
import sqlite3
import datetime

from typing import Optional, List, Dict, Any


class TransferStatus:
    PENDING = 'pending'
    RUNNING = 'running'
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
                    finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS transfer_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL REFERENCES transfer_tasks(id) ON DELETE CASCADE,
                    source_message_id INTEGER,
                    source_link TEXT,
                    target_link TEXT NOT NULL,
                    media_type TEXT,
                    local_path TEXT,
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
                '''
            )

    def create_task(
            self,
            source_link: str,
            target_link: str = 'https://t.me/pikpak_bot',
            target_profile: str = 'pikpak',
            start_id: Optional[int] = None,
            end_id: Optional[int] = None
    ) -> int:
        now = self.utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO transfer_tasks (
                    source_link, target_link, target_profile, start_id, end_id,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (source_link, target_link, target_profile, start_id, end_id, TransferStatus.PENDING, now, now)
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
            finished: bool = False
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
            'finished_at': now if finished else task['finished_at']
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
                    finished_at = :finished_at
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
            media_type: Optional[str] = None,
            local_path: Optional[str] = None,
            status: str = TransferStatus.PENDING,
            error_message: Optional[str] = None
    ) -> int:
        now = self.utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO transfer_items (
                    task_id, source_message_id, source_link, target_link,
                    media_type, local_path, status, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (task_id, source_message_id, source_link, target_link, media_type, local_path, status, error_message, now, now)
            )
            return int(cursor.lastrowid)

    def update_item(
            self,
            item_id: int,
            status: Optional[str] = None,
            media_type: Optional[str] = None,
            local_path: Optional[str] = None,
            error_message: Optional[str] = None
    ) -> None:
        now = self.utc_now()
        fields = {'updated_at': now}
        if status is not None:
            fields['status'] = status
        if media_type is not None:
            fields['media_type'] = media_type
        if local_path is not None:
            fields['local_path'] = local_path
        if error_message is not None:
            fields['error_message'] = error_message
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
