# coding=UTF-8
import sqlite3
from typing import Optional, List, Dict, Any

from module.persistence.store.status import TransferStatus

class ItemsMixin:
    def set_item_stale_timeout_seconds_getter(self, getter) -> None:
        self._item_stale_timeout_seconds_getter = getter

    def set_stale_item_logger(self, logger) -> None:
        """Optional logger(item_id, task_id, message) for system-log / diagnostics."""
        self._stale_item_logger = logger

    def resolve_item_stale_timeout_seconds(self) -> int:
        getter = self._item_stale_timeout_seconds_getter
        if callable(getter):
            try:
                value = int(getter())
            except (TypeError, ValueError):
                value = self.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS
            return max(60, value)
        return int(self.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS)

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
            'archive_match_original_name': ItemsMixin._normalize_optional_bool(archive_match_original_name),
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

    def ensure_range_message_accounted(
            self,
            task_id: int,
            range_message_id: int,
            *,
            origin_chat_id,
            task: dict,
            reason: str = '范围内消息无可转存内容，已跳过',
    ) -> Optional[int]:
        """Create a skipped placeholder when a range message produced no transfer items.

        Channel ID ranges often include bot posts or plain text that never enter the
        transfer pipeline; without a terminal item the range progress bar stalls below
        100% even after assignment completes.
        """
        items = self.list_items_for_range_message(task_id, int(range_message_id))
        if items:
            active_statuses = {TransferStatus.RUNNING, TransferStatus.PENDING}
            if any(str(item.get('status') or '') in active_statuses for item in items):
                return None
            if self.is_range_message_complete(task_id, int(range_message_id)):
                return None
            return None
        source_prefix = str(task.get('source_link') or '').rstrip('/')
        message_link = f'{source_prefix}/{int(range_message_id)}'
        item_id = self.add_item(
            task_id=int(task_id),
            source_chat_id=origin_chat_id,
            source_message_id=int(range_message_id),
            range_message_id=int(range_message_id),
            source_link=message_link,
            target_link=task.get('target_link'),
            media_type='empty',
            phase='skipped',
            status=TransferStatus.SKIPPED,
            error_message=reason,
        )
        self.add_event(
            int(task_id),
            reason,
            level='warning',
            item_id=item_id,
        )
        self.refresh_task_counts(int(task_id))
        return item_id

    def finalize_range_message_assignment(
            self,
            task_id: int,
            start_id: int,
            end_id: int,
            *,
            origin_chat_id,
            task: dict,
    ) -> int:
        """Ensure every ID in [start_id, end_id] has a terminal item before range finalize."""
        ensured = 0
        for message_id in range(int(start_id), int(end_id) + 1):
            if self.ensure_range_message_accounted(
                    task_id,
                    message_id,
                    origin_chat_id=origin_chat_id,
                    task=task,
            ) is not None:
                ensured += 1
        return ensured

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

    def count_items(self, task_id: int) -> int:
        with self.connect() as conn:
            return conn.execute(
                'SELECT COUNT(*) FROM transfer_items WHERE task_id = ?', (task_id,)
            ).fetchone()[0]

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
