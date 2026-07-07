# coding=UTF-8
from typing import Any, Optional

from module.transfer_store import TransferStatus, TransferStore


TASK_TERMINAL_STATUSES = {
    TransferStatus.SUCCESS,
    TransferStatus.FAILURE,
    TransferStatus.SKIPPED,
}

TASK_ACTIVE_STATUSES = {
    TransferStatus.PENDING,
    TransferStatus.RUNNING,
}


class WebUiViewModel:
    """Builds the single public data contract consumed by all WebUI clients."""

    def __init__(self, store: TransferStore):
        self.store = store

    def task_list(self, limit: int = 100) -> dict[str, Any]:
        tasks = self.store.list_tasks(limit=limit)
        counts_by_task = self._status_counts_by_task([int(task['id']) for task in tasks])
        return {
            'tasks': [
                self.task_model(task, counts_by_task.get(int(task['id']), {}))
                for task in tasks
            ]
        }

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
            'task': self.task_model(task, counts),
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
            'task': self.task_model(task, counts),
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

    def task_model(self, task: dict[str, Any], counts: dict[str, int] = None) -> dict[str, Any]:
        counts = counts or {}
        summary = self.summary_model(task, counts)
        status = str(task.get('status') or TransferStatus.PENDING)
        task_id = int(task.get('id') or 0)
        return {
            'id': task_id,
            'title': task.get('title') or f'#{task_id}',
            'source_link': task.get('source_link') or '',
            'target_link': task.get('target_link') or '',
            'target_profile': task.get('target_profile') or '',
            'start_id': task.get('start_id'),
            'end_id': task.get('end_id'),
            'include_comment': bool(task.get('include_comment')),
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
        return {
            'id': int(item.get('id') or 0),
            'task_id': int(item.get('task_id') or 0),
            'source_chat_id': item.get('source_chat_id'),
            'source_message_id': item.get('source_message_id'),
            'source_link': item.get('source_link') or '',
            'target_link': item.get('target_link') or '',
            'target_path': item.get('target_path') or item.get('archive_path') or '',
            'media_type': item.get('media_type') or '',
            'file_name': item.get('file_name') or '',
            'file_size': item.get('file_size'),
            'local_path': item.get('local_path') or '',
            'phase': item.get('phase') or TransferStatus.PENDING,
            'status': item.get('status') or TransferStatus.PENDING,
            'download_current': int(item.get('download_current') or 0),
            'download_total': int(item.get('download_total') or 0),
            'upload_current': int(item.get('upload_current') or 0),
            'upload_total': int(item.get('upload_total') or 0),
            'error_message': item.get('error_message') or '',
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at'),
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

    def _item_count(self, task_id: int, item_status: Optional[str] = None) -> int:
        with self.store.connect() as conn:
            if item_status:
                return int(conn.execute(
                    'SELECT COUNT(*) FROM transfer_items WHERE task_id = ? AND status = ?',
                    (task_id, item_status)
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
            if item_status:
                rows = conn.execute(
                    '''
                    SELECT * FROM transfer_items
                    WHERE task_id = ? AND status = ?
                    ORDER BY id ASC
                    LIMIT ? OFFSET ?
                    ''',
                    (task_id, item_status, limit, offset)
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
