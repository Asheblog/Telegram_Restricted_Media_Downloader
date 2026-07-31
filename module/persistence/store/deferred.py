# coding=UTF-8
import sqlite3
from typing import Optional, List, Dict, Any

from module.persistence.store.status import DeferredDiscussionCaptureStatus

class DeferredMixin:
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
