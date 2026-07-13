# coding=UTF-8
import datetime
import os
from typing import Any, Optional

from module.local_storage_guard import LocalStorageGuard
from module.transfer_store import TransferStatus, TransferStore

# Progress callbacks stop updating download/upload_speed_bps when transfer stalls.
# Exclude speeds whose item has not been touched within this window so the
# dashboard does not freeze on the last sampled rate.
SPEED_METRICS_STALE_SECONDS = 5


TASK_TERMINAL_STATUSES = {
    TransferStatus.SUCCESS,
    TransferStatus.FAILURE,
    TransferStatus.SKIPPED,
}

TASK_ACTIVE_STATUSES = {
    TransferStatus.PENDING,
    TransferStatus.RUNNING,
}

WATCH_DOWNLOAD_ACTIVE_STATUSES = {
    TransferStatus.PENDING,
    TransferStatus.RUNNING,
    TransferStatus.PAUSED,
}

WATCH_DOWNLOAD_COMPLETED_STATUSES = {
    TransferStatus.SUCCESS,
    TransferStatus.SKIPPED,
}

WATCH_DOWNLOAD_FAILED_STATUSES = {
    TransferStatus.FAILURE,
}


class WebUiViewModel:
    """Builds the single public data contract consumed by all WebUI clients."""

    def __init__(self, store: TransferStore):
        self.store = store

    def task_list(self, limit: int = 100) -> dict[str, Any]:
        from module.transfer_store import ExecutionMode

        tasks = self.store.list_tasks(
            limit=limit,
            exclude_execution_mode=ExecutionMode.WATCH_INLINE,
        )
        task_ids = [int(task['id']) for task in tasks]
        counts_by_task = self._status_counts_by_task(task_ids)
        active_items_by_task = self._active_items_by_task(task_ids)
        return {
            'tasks': [
                self.task_model(
                    task,
                    counts_by_task.get(int(task['id']), {}),
                    active_items_by_task.get(int(task['id']))
                )
                for task in tasks
            ]
        }

    def watch_download_tasks(self, watch_id: str, limit: int = 200) -> Optional[dict[str, Any]]:
        """返回某条监听触发的 watch_inline 下载/转存任务（含无 watch_id 的历史启发式归属）。"""
        from module.transfer.watch_inline import is_watch_inline_task, source_link_belongs_to_watch
        from module.transfer_store import ExecutionMode

        if not watch_id:
            return None
        watch = self.store.get_live_transfer_watch(watch_id)
        watch_source = (watch or {}).get('source_link') or ''
        # 也尝试从 watch_id 解析来源（pending 内存监听可能尚未落库）
        if not watch_source and watch_id.startswith('forward:'):
            rule = watch_id[len('forward:'):]
            if '->' in rule:
                watch_source = rule.split('->', 1)[0].strip()

        candidates = self.store.list_tasks(
            limit=max(limit * 3, 300),
            execution_mode=ExecutionMode.WATCH_INLINE,
        )
        matched = []
        for task in candidates:
            if not is_watch_inline_task(task):
                continue
            task_watch_id = task.get('watch_id') or None
            if task_watch_id == watch_id:
                matched.append(task)
            elif (
                not task_watch_id
                and watch_source
                and source_link_belongs_to_watch(task.get('source_link') or '', watch_source)
            ):
                matched.append(task)
            if len(matched) >= limit:
                break

        task_ids = [int(task['id']) for task in matched]
        counts_by_task = self._status_counts_by_task(task_ids)
        active_items_by_task = self._active_items_by_task(task_ids)
        models = [
            self.task_model(
                task,
                counts_by_task.get(int(task['id']), {}),
                active_items_by_task.get(int(task['id']))
            )
            for task in matched
        ]
        counts = {'active': 0, 'completed': 0, 'failed': 0}
        for model in models:
            bucket = self.watch_download_status_bucket(model.get('status'))
            counts[bucket] = counts.get(bucket, 0) + 1
        return {
            'watch_id': watch_id,
            'tasks': models,
            'counts': counts,
        }

    @staticmethod
    def watch_download_status_bucket(status: Optional[str]) -> str:
        value = str(status or TransferStatus.PENDING)
        if value in WATCH_DOWNLOAD_FAILED_STATUSES:
            return 'failed'
        if value in WATCH_DOWNLOAD_COMPLETED_STATUSES:
            return 'completed'
        if value in WATCH_DOWNLOAD_ACTIVE_STATUSES:
            return 'active'
        return 'active'

    def task_detail(
            self,
            task_id: int,
            item_limit: int = 200,
            item_offset: int = 0,
            item_status: Optional[str] = None,
            event_limit: int = 100,
            event_offset: int = 0
    ) -> Optional[dict[str, Any]]:
        task = self.store.get_task(task_id)
        if not task:
            return None
        counts = self._status_counts(task_id)
        item_count = self._item_count(task_id, item_status=item_status)
        event_count = self._event_count(task_id)
        items = self._list_items(task_id, item_limit, item_offset, item_status=item_status)
        events = self._list_events(task_id, event_limit, event_offset)
        return {
            'task': self.task_model(task, counts, self._active_item(task_id)),
            'summary': self.summary_model(task, counts),
            'items': [self.item_model(item) for item in items],
            'events': [self.event_model(event) for event in events],
            'page': {
                'item_count': item_count,
                'event_count': event_count,
                'items_limit': max(0, int(item_limit or 0)),
                'items_offset': max(0, int(item_offset or 0)),
                'item_status': item_status or '',
                'events_limit': max(0, int(event_limit or 0)),
                'events_offset': max(0, int(event_offset or 0)),
                'has_more_items': (max(0, item_offset) + len(items)) < item_count,
                'has_more_events': (max(0, event_offset) + len(events)) < event_count,
            }
        }

    def task_summary(self, task_id: int, recent_event_limit: int = 30) -> Optional[dict[str, Any]]:
        task = self.store.get_task(task_id)
        if not task:
            return None
        counts = self._status_counts(task_id)
        event_count = self._event_count(task_id)
        events = self._list_events(task_id, recent_event_limit, 0)
        return {
            'task': self.task_model(task, counts, self._active_item(task_id)),
            'summary': self.summary_model(task, counts),
            'recent_events': [self.event_model(event) for event in events],
            'page': {
                'item_count': self._item_count(task_id),
                'event_count': event_count,
                'events_limit': max(0, int(recent_event_limit or 0)),
                'events_offset': 0,
                'has_more_events': len(events) < event_count,
            }
        }

    @staticmethod
    def settings_model(settings: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        user = settings.get('user') or {}
        global_settings = settings.get('global') or {}
        message_filter = global_settings.get('message_filter') or {}
        return {
            'options': {
                'download_type': WebUiViewModel._option_list(schema.get('download_type') or []),
                'forward_type': WebUiViewModel._option_list(schema.get('forward_type') or []),
                'message_filter_media_types': WebUiViewModel._option_list(
                    ((schema.get('message_filter') or {}).get('media_types') or [])
                ),
            },
            'selections': {
                'user_download_type': list(user.get('download_type') or []),
                'forward_type': dict(global_settings.get('forward_type') or {}),
                'message_filter_media_types': dict(message_filter.get('media_types') or {}),
            }
        }

    @staticmethod
    def _option_list(values: list[str]) -> list[dict[str, str]]:
        return [{'value': str(value), 'label': str(value)} for value in values]

    def task_model(
            self,
            task: dict[str, Any],
            counts: dict[str, int] = None,
            active_item: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        counts = counts or {}
        summary = self.summary_model(task, counts)
        status = str(task.get('status') or TransferStatus.PENDING)
        task_id = int(task.get('id') or 0)
        active = self.active_transfer_model(active_item)
        range_progress = self.store.range_transfer_progress(task) or {}
        return {
            'id': task_id,
            'title': task.get('title') or f'#{task_id}',
            'source_link': task.get('source_link') or '',
            'target_link': task.get('target_link') or '',
            'target_profile': task.get('target_profile') or '',
            'start_id': task.get('start_id'),
            'end_id': task.get('end_id'),
            'include_comment': bool(task.get('include_comment')),
            'resolve_deep_link': bool(task.get('resolve_deep_link')),
            'execution_mode': task.get('execution_mode') or 'web_queue',
            'watch_id': task.get('watch_id') or None,
            'status': status,
            'total_items': summary['total'],
            'completed_items': summary['completed'],
            'failed_items': summary['failed'],
            'success_items': summary['success'],
            'skipped_items': summary['skipped'],
            'running_items': summary['running'],
            'pending_items': summary['pending'],
            'terminal_items': summary['terminal'],
            'progress_percent': summary['progress_percent'],
            'error_message': task.get('error_message') or '',
            'assignment_completed': bool(task.get('assignment_completed')),
            'created_at': task.get('created_at'),
            'updated_at': task.get('updated_at'),
            'started_at': task.get('started_at'),
            'finished_at': task.get('finished_at'),
            'can_pause': status in TASK_ACTIVE_STATUSES,
            'can_resume': status == TransferStatus.PAUSED,
            'can_retry': summary['failed'] > 0,
            'can_delete': status in TASK_TERMINAL_STATUSES or status == TransferStatus.PAUSED,
            **active,
            **range_progress,
        }

    @staticmethod
    def summary_model(task: dict[str, Any], counts: dict[str, int] = None) -> dict[str, int]:
        counts = counts or {}
        success = int(counts.get(TransferStatus.SUCCESS, 0))
        skipped = int(counts.get(TransferStatus.SKIPPED, 0))
        failed = int(counts.get(TransferStatus.FAILURE, 0))
        running = int(counts.get(TransferStatus.RUNNING, 0))
        pending = int(counts.get(TransferStatus.PENDING, 0))
        completed = success + skipped
        terminal = completed + failed
        item_count = sum(int(value) for value in counts.values())
        expected_total = int(task.get('total_items') or item_count or 0)
        total = max(expected_total, item_count)
        progress_percent = min(100, round((completed / total) * 100)) if total > 0 else 0
        return {
            'total': total,
            'completed': completed,
            'success': success,
            'skipped': skipped,
            'failed': failed,
            'running': running,
            'pending': pending,
            'terminal': terminal,
            'progress_percent': progress_percent,
        }

    @staticmethod
    def item_model(item: dict[str, Any]) -> dict[str, Any]:
        active = WebUiViewModel.active_transfer_model(item)
        return {
            'id': int(item.get('id') or 0),
            'task_id': int(item.get('task_id') or 0),
            'source_chat_id': item.get('source_chat_id'),
            'source_message_id': item.get('source_message_id'),
            'range_message_id': item.get('range_message_id'),
            'source_link': item.get('source_link') or '',
            'target_link': item.get('target_link') or '',
            'target_path': item.get('target_path') or item.get('archive_path') or '',
            'media_type': item.get('media_type') or '',
            'file_name': item.get('file_name') or '',
            'file_size': item.get('file_size'),
            'local_path': item.get('local_path') or '',
            'temp_path': item.get('temp_path') or '',
            'phase': item.get('phase') or TransferStatus.PENDING,
            'status': item.get('status') or TransferStatus.PENDING,
            'download_current': int(item.get('download_current') or 0),
            'download_total': int(item.get('download_total') or 0),
            'download_speed_bps': int(item.get('download_speed_bps') or 0),
            'upload_current': int(item.get('upload_current') or 0),
            'upload_total': int(item.get('upload_total') or 0),
            'upload_speed_bps': int(item.get('upload_speed_bps') or 0),
            'error_message': item.get('error_message') or '',
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at'),
            **active,
        }

    @staticmethod
    def active_transfer_model(item: Optional[dict[str, Any]]) -> dict[str, Any]:
        empty = {
            'active_item_id': None,
            'active_phase': '',
            'active_file_name': '',
            'active_progress_current': 0,
            'active_progress_total': 0,
            'active_progress_percent': 0,
            'active_speed_bps': 0,
            'download_current': 0,
            'download_total': 0,
            'download_speed_bps': 0,
            'upload_current': 0,
            'upload_total': 0,
            'upload_speed_bps': 0,
        }
        if not item:
            return empty
        phase = str(item.get('phase') or item.get('status') or '')
        download_current = int(item.get('download_current') or 0)
        download_total = int(item.get('download_total') or 0)
        download_speed = int(item.get('download_speed_bps') or 0)
        upload_current = int(item.get('upload_current') or 0)
        upload_total = int(item.get('upload_total') or 0)
        upload_speed = int(item.get('upload_speed_bps') or 0)
        if phase == 'uploading' or upload_current > 0:
            current = upload_current
            total = upload_total or int(item.get('file_size') or 0)
            speed = upload_speed
        else:
            current = download_current
            total = download_total or int(item.get('file_size') or 0)
            speed = download_speed
        percent = min(100, round((current / total) * 100)) if total > 0 else 0
        return {
            'active_item_id': int(item.get('id') or 0) or None,
            'active_phase': phase,
            'active_file_name': item.get('file_name') or '',
            'active_progress_current': current,
            'active_progress_total': total,
            'active_progress_percent': percent,
            'active_speed_bps': speed,
            'download_current': download_current,
            'download_total': download_total,
            'download_speed_bps': download_speed,
            'upload_current': upload_current,
            'upload_total': upload_total,
            'upload_speed_bps': upload_speed,
        }

    @staticmethod
    def event_model(event: dict[str, Any]) -> dict[str, Any]:
        return {
            'id': int(event.get('id') or 0),
            'task_id': int(event.get('task_id') or 0),
            'item_id': event.get('item_id'),
            'level': event.get('level') or 'info',
            'message': event.get('message') or '',
            'created_at': event.get('created_at'),
        }

    def _status_counts_by_task(self, task_ids: list[int]) -> dict[int, dict[str, int]]:
        if not task_ids:
            return {}
        placeholders = ','.join(['?'] * len(task_ids))
        with self.store.connect() as conn:
            rows = conn.execute(
                f'''
                SELECT task_id, status, COUNT(*) AS count
                FROM transfer_items
                WHERE task_id IN ({placeholders})
                GROUP BY task_id, status
                ''',
                tuple(task_ids)
            ).fetchall()
        result: dict[int, dict[str, int]] = {}
        for row in rows:
            task_id = int(row['task_id'])
            result.setdefault(task_id, {})[str(row['status'])] = int(row['count'])
        return result

    def _status_counts(self, task_id: int) -> dict[str, int]:
        return self._status_counts_by_task([int(task_id)]).get(int(task_id), {})

    def _active_item(self, task_id: int) -> Optional[dict[str, Any]]:
        return self._active_items_by_task([int(task_id)]).get(int(task_id))

    def _active_items_by_task(self, task_ids: list[int]) -> dict[int, dict[str, Any]]:
        if not task_ids:
            return {}
        placeholders = ','.join(['?'] * len(task_ids))
        with self.store.connect() as conn:
            rows = conn.execute(
                f'''
                SELECT *
                FROM transfer_items
                WHERE task_id IN ({placeholders})
                  AND status = ?
                ORDER BY updated_at DESC, id ASC
                ''',
                (*task_ids, TransferStatus.RUNNING)
            ).fetchall()
        result: dict[int, dict[str, Any]] = {}
        for row in rows:
            task_id = int(row['task_id'])
            result.setdefault(task_id, dict(row))
        return result

    @staticmethod
    def _item_status_filter(item_status: Optional[str]) -> tuple[str, ...]:
        if item_status == 'active':
            return tuple(TASK_ACTIVE_STATUSES)
        if item_status:
            return (item_status,)
        return ()

    def _item_count(self, task_id: int, item_status: Optional[str] = None) -> int:
        with self.store.connect() as conn:
            statuses = self._item_status_filter(item_status)
            if statuses:
                placeholders = ', '.join('?' for _ in statuses)
                return int(conn.execute(
                    f'SELECT COUNT(*) FROM transfer_items WHERE task_id = ? AND status IN ({placeholders})',
                    (task_id, *statuses)
                ).fetchone()[0])
            return int(conn.execute(
                'SELECT COUNT(*) FROM transfer_items WHERE task_id = ?',
                (task_id,)
            ).fetchone()[0])

    def _event_count(self, task_id: int) -> int:
        with self.store.connect() as conn:
            return int(conn.execute(
                'SELECT COUNT(*) FROM transfer_events WHERE task_id = ?',
                (task_id,)
            ).fetchone()[0])

    def _list_items(self, task_id: int, limit: int, offset: int, item_status: Optional[str] = None) -> list[dict[str, Any]]:
        limit = max(0, int(limit or 0))
        offset = max(0, int(offset or 0))
        if limit == 0:
            return []
        with self.store.connect() as conn:
            statuses = self._item_status_filter(item_status)
            if statuses:
                placeholders = ', '.join('?' for _ in statuses)
                rows = conn.execute(
                    f'''
                    SELECT * FROM transfer_items
                    WHERE task_id = ? AND status IN ({placeholders})
                    ORDER BY id ASC
                    LIMIT ? OFFSET ?
                    ''',
                    (task_id, *statuses, limit, offset)
                ).fetchall()
                return [dict(row) for row in rows]
            rows = conn.execute(
                '''
                SELECT * FROM transfer_items
                WHERE task_id = ?
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                ''',
                (task_id, limit, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    def transfer_speed_metrics(self) -> dict[str, int]:
        cutoff = (
            datetime.datetime.now(datetime.UTC)
            - datetime.timedelta(seconds=SPEED_METRICS_STALE_SECONDS)
        ).isoformat(timespec='seconds')
        with self.store.connect() as conn:
            row = conn.execute(
                '''
                SELECT COALESCE(SUM(download_speed_bps), 0) AS download_speed_bps,
                       COALESCE(SUM(upload_speed_bps), 0) AS upload_speed_bps
                FROM transfer_items
                WHERE status = ?
                  AND updated_at >= ?
                ''',
                (TransferStatus.RUNNING, cutoff)
            ).fetchone()
        return {
            'download_speed_bps': int(row['download_speed_bps'] or 0),
            'upload_speed_bps': int(row['upload_speed_bps'] or 0),
        }

    @staticmethod
    def disk_metrics(storage_paths: list[str]) -> dict[str, Any]:
        candidates = [
            str(path).strip()
            for path in (storage_paths or [])
            if str(path or '').strip()
        ]
        probe = candidates[0] if candidates else os.getcwd()
        return {
            'disk_free_bytes': LocalStorageGuard._disk_free_bytes(probe),
            'disk_path': probe,
        }

    def _list_events(self, task_id: int, limit: int, offset: int) -> list[dict[str, Any]]:
        limit = max(0, int(limit or 0))
        offset = max(0, int(offset or 0))
        if limit == 0:
            return []
        with self.store.connect() as conn:
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
