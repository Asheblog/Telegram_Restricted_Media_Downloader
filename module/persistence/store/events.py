# coding=UTF-8
from typing import Optional, List, Dict, Any

class EventsMixin:
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

    def count_events(self, task_id: int) -> int:
        with self.connect() as conn:
            return conn.execute(
                'SELECT COUNT(*) FROM transfer_events WHERE task_id = ?', (task_id,)
            ).fetchone()[0]
