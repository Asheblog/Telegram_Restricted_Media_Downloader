# coding=UTF-8
from typing import Optional, List, Dict, Any

class SystemLogsMixin:
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

    def get_system_log(self, log_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                'SELECT * FROM system_logs WHERE id = ?',
                (int(log_id),),
            ).fetchone()
            return dict(row) if row else None

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
