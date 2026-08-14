# coding=UTF-8
import sqlite3
from typing import Any, Dict, List, Optional

from module.core.archive_title_source import normalize_archive_title_source
from module.core.media_types import normalize_media_types, serialize_media_types
from module.persistence.store.status import TransferStatus


class WatchesMixin:
    _LIVE_WATCH_EVENT_STATUS_FILTERS = {
        TransferStatus.SUCCESS,
        TransferStatus.SKIPPED,
        TransferStatus.FAILURE,
    }

    @staticmethod
    def _live_transfer_watch_row(row: sqlite3.Row) -> Dict[str, Any]:
        watch = dict(row)
        watch['include_comment'] = bool(watch.get('include_comment'))
        watch['resolve_deep_link'] = bool(watch.get('resolve_deep_link'))
        watch['archive_by_author'] = bool(watch.get('archive_by_author'))
        watch['archive_title_source'] = normalize_archive_title_source(
            watch.get('archive_title_source')
        )
        delay = watch.get('comment_delay_minutes')
        watch['comment_delay_minutes'] = int(delay) if delay is not None else None
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
            archive_title_source: str = 'auto',
            comment_delay_minutes: Optional[int] = None,
            status: str = TransferStatus.PENDING,
            error_message: Optional[str] = None,
            media_types: Optional[dict] = None,
    ) -> Dict[str, Any]:
        now = self.utc_now()
        media_types_json = serialize_media_types(media_types)
        delay_value = None if comment_delay_minutes is None else int(comment_delay_minutes)
        with self.connect() as conn:
            conn.execute(
                '''
                INSERT INTO live_transfer_watches (
                    id, type, source_link, target_link, include_comment, resolve_deep_link,
                    archive_by_author, archive_title_source, comment_delay_minutes, media_types, status, error_message,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type = excluded.type,
                    source_link = excluded.source_link,
                    target_link = excluded.target_link,
                    include_comment = excluded.include_comment,
                    resolve_deep_link = excluded.resolve_deep_link,
                    archive_by_author = excluded.archive_by_author,
                    archive_title_source = excluded.archive_title_source,
                    comment_delay_minutes = excluded.comment_delay_minutes,
                    media_types = excluded.media_types,
                    status = excluded.status,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                ''',
                (
                    watch_id, watch_type, source_link, target_link,
                    int(bool(include_comment)), int(bool(resolve_deep_link)),
                    int(bool(archive_by_author)),
                    normalize_archive_title_source(archive_title_source),
                    delay_value,
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
            'archive_title_source': normalize_archive_title_source(archive_title_source),
            'comment_delay_minutes': delay_value,
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
