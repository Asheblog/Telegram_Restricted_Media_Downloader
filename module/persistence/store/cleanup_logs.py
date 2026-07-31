# coding=UTF-8
from typing import Optional, List, Dict, Any

class CleanupLogsMixin:
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
