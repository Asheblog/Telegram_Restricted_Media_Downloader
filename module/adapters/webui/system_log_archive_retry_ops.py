# coding=UTF-8
"""Manual archive retry from system logs — deep module for WebUI orchestration."""
from __future__ import annotations

import threading
from typing import Any

from module.persistence.system_log import (
    archive_retry_inflight_key,
    resolve_archive_retry_meta,
)
from module.domain.archive_naming.source_folders import archive_source_folder, normalize_archive_title_source
from module.persistence.transfer_store import TransferStatus


class SystemLogArchiveRetryOps:
    """Owns manual archive-not_found retry; reads runtime deps from ``host``."""

    def __init__(self, host):
        self._host = host
        self._lock = threading.Lock()
        self._inflight: set[str] = set()

    def retry_archive_from_system_log(self, log_id: int) -> dict[str, Any]:
        """Manually re-run PikPak archive for an archive_not_found system log.

        Ignores the automatic match/retry window. Raises:
        - LookupError: log missing
        - ValueError: not retryable / missing metadata
        - RuntimeError: already in progress, or archive still failed
        """
        host = self._host
        store = getattr(host, 'transfer_store', None)
        if not store or not hasattr(store, 'get_system_log'):
            raise LookupError('log_not_found')
        entry = store.get_system_log(int(log_id))
        if not entry:
            raise LookupError('log_not_found')
        meta = resolve_archive_retry_meta(entry)
        if not meta:
            raise ValueError('not_retryable')
        key = archive_retry_inflight_key(meta)
        if not key:
            raise ValueError('missing_metadata')

        with self._lock:
            if key in self._inflight:
                raise RuntimeError('retry_in_progress')
            self._inflight.add(key)

        try:
            task_id = meta.get('task_id')
            item_id = meta.get('item_id')
            item = None
            task = None
            source_folder = meta.get('source_folder')
            file_name = meta.get('file_name')
            file_size = meta.get('file_size')
            match_original_name = meta.get('match_original_name')
            source_link = meta.get('source_link')

            if task_id is not None and item_id is not None:
                item = store.get_item(int(item_id))
                task = store.get_task(int(task_id))
                if not item or not task or int(item.get('task_id') or 0) != int(task_id):
                    raise ValueError('missing_metadata')
                source_folder = (
                    item.get('source_folder')
                    or source_folder
                    or archive_source_folder(
                        fallback_link=item.get('source_link') or task.get('source_link') or source_link,
                        post_message_id=item.get('range_message_id') or item.get('source_message_id'),
                        archive_by_author=bool(task.get('archive_by_author')),
                        archive_title_source=normalize_archive_title_source(
                            task.get('archive_title_source')
                        ),
                    )
                )
                file_name = item.get('file_name') or file_name
                file_size = item.get('file_size') if item.get('file_size') is not None else file_size
                if match_original_name is None:
                    match_original_name = host.transfer_item_archive_match_original_name(item)
                source_link = item.get('source_link') or task.get('source_link') or source_link

            if not source_folder or not file_name:
                raise ValueError('missing_metadata')

            result = host.archive_pikpak_item(
                target_profile='pikpak',
                item_id=int(item_id) if item_id is not None else None,
                task_id=int(task_id) if task_id is not None else None,
                message=None,
                source_link=source_link,
                source_folder=source_folder,
                file_name=file_name,
                file_size=file_size,
                transferred_at=None,
                match_original_name=bool(match_original_name) if match_original_name is not None else True,
            )
            status = getattr(result, 'status', 'error') if result is not None else 'error'
            ok = bool(result is not None and getattr(result, 'ok', False))
            archive_path = getattr(result, 'archive_path', None) if result is not None else None
            archive_message = getattr(result, 'message', '') if result is not None else 'archive unavailable'

            tracer = getattr(host, 'system_log', None)
            if tracer is not None and hasattr(tracer, 'log'):
                tracer.log(
                    category='archive',
                    stage='archive_success' if ok else f'archive_{status}',
                    message=(
                        f'rclone 归档成功(手动重试): {archive_path or source_link or file_name}'
                        if ok else
                        f'rclone 归档失败({status}): {archive_message or ""}'
                    ),
                    level='info' if ok else 'warning',
                    source_chat_id=meta.get('source_chat_id') or entry.get('source_chat_id'),
                    source_message_id=meta.get('source_message_id') or entry.get('source_message_id'),
                    target_link=source_link or entry.get('target_link'),
                    details={
                        'archive_path': archive_path,
                        'source_folder': source_folder,
                        'file_name': file_name,
                        'task_id': task_id,
                        'item_id': item_id,
                        'manual_retry_of': int(log_id),
                        'match_original_name': match_original_name,
                    },
                )

            if not ok:
                raise RuntimeError(archive_message or f'archive_{status}')

            if item is not None and task is not None and item.get('status') == TransferStatus.FAILURE:
                error_message = str(item.get('error_message') or '')
                existing_phase = item.get('phase')
                if existing_phase in ('forwarded', 'sent'):
                    phase = existing_phase
                elif existing_phase == 'failure':
                    phase = (
                        'forwarded'
                        if item.get('media_type') == 'forward' or 'PikPak archive' in error_message
                        else 'sent'
                    )
                else:
                    phase = 'forwarded' if item.get('media_type') == 'forward' else 'sent'
                store.update_item(
                    int(item_id),
                    phase=phase,
                    status=TransferStatus.SUCCESS,
                    error_message='',
                    archive_error=None,
                )
                store.add_event(
                    int(task_id),
                    f'PikPak archive recovered by manual system-log retry: {source_link or file_name}',
                    item_id=int(item_id),
                )
                host.refresh_transfer_task_counts(int(task_id))
            elif item is not None:
                store.update_item(
                    int(item_id),
                    archive_error=None,
                    error_message=(
                        ''
                        if 'PikPak archive' in str(item.get('error_message') or '')
                        else item.get('error_message')
                    ),
                )

            return {
                'ok': True,
                'status': status,
                'archive_path': archive_path,
                'log_id': int(log_id),
                'file_name': file_name,
                'source_folder': source_folder,
            }
        finally:
            with self._lock:
                self._inflight.discard(key)
