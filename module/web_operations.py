# coding=UTF-8
"""Web UI operations facade — IWebUiOperations / IWatchOps / ITaskOps seam."""
import os
import asyncio
import random
import time
from copy import deepcopy
from functools import partial
from typing import Optional, Union, Callable

import pyrogram
from pyrogram.errors import FloodWait, FloodPremiumWait
from pyrogram.errors.exceptions.bad_request_400 import MsgIdInvalid

from module import console, log
from module.filter import Filter
from module.config import GlobalConfig, UserConfig
from module.media_manager import MediaManager
from module.live_watch_applicator import LiveWatchApplicator
from module.enums import DownloadType, UploadStatus, KeyWord
from module.language import _t
from module.task import DownloadTask, UploadTask
from module.transfer_store import TransferStore, TransferStatus


ORPHAN_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60
from module.uploader import TelegramUploader
from module.web_ui import (
    get_web_host_from_env,
    get_web_password_from_env,
    get_web_port_from_env,
    get_web_username_from_env,
    merge_allowed_settings,
)
from module.util import is_docker, make_forward_watch_rule, iter_discussion_reply_messages
from module.pikpak_integration import PikpakIntegrationManager
from module.source_folders import source_folder_from_link


def _downloader():
    """Lazy import so unit tests can patch names on module.downloader."""
    import module.downloader as downloader_module
    return downloader_module


class WebOperationsMixin:
    def _web_ui_operations(self) -> 'WebOperationsFacade':
        facade = self.__dict__.get('_web_operations_facade')
        if facade is None:
            facade = WebOperationsFacade(self)
            self._web_operations_facade = facade
        return facade

    def should_continue_web_transfer_task(self, task_id: int) -> bool:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.should_continue_web_transfer_task(task_id)
        if not self.transfer_store or not task_id:
            return False
        task = self.transfer_store.get_task(int(task_id))
        return bool(task and task.get('status') != TransferStatus.PAUSED)
    def cancel_task_uploads(self, task_id: int) -> int:
        uploader = getattr(self, 'uploader', None)
        if uploader and hasattr(uploader, 'cancel_uploads_for_task'):
            return int(uploader.cancel_uploads_for_task(task_id) or 0)
        return 0

    def pause_task_uploads(self, task_id: int) -> int:
        uploader = getattr(self, 'uploader', None)
        if uploader and hasattr(uploader, 'pause_uploads_for_task'):
            return int(uploader.pause_uploads_for_task(task_id) or 0)
        return 0

    def _transfer_download_registry(self) -> dict:
        return self.__dict__.setdefault('_transfer_download_tasks', {})

    def _register_transfer_download_task(self, with_upload: Optional[dict], download_task: asyncio.Task) -> None:
        if not isinstance(with_upload, dict):
            return
        raw_task_id = with_upload.get('task_id')
        if raw_task_id is None or download_task is None:
            return
        task_id = int(raw_task_id)
        self._transfer_download_registry().setdefault(task_id, set()).add(download_task)

    def _unregister_transfer_download_task(self, with_upload: Optional[dict], download_task: asyncio.Task) -> None:
        if not isinstance(with_upload, dict):
            return
        raw_task_id = with_upload.get('task_id')
        if raw_task_id is None:
            return
        task_id = int(raw_task_id)
        registry = self._transfer_download_registry()
        tasks = registry.get(task_id)
        if not tasks:
            return
        tasks.discard(download_task)
        if not tasks:
            registry.pop(task_id, None)

    def cancel_task_downloads(self, task_id: int) -> int:
        registry = self._transfer_download_registry()
        tasks = list(registry.pop(int(task_id), set()))
        cancelled = 0
        for download_task in tasks:
            if download_task and not download_task.done():
                download_task.cancel()
                cancelled += 1
        return cancelled

    def submit_web_task(self, task_id: int) -> None:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.submit_web_task(task_id)
        if task_id in self.web_submitted_task_ids:
            return
        self.web_submitted_task_ids.add(task_id)

        def enqueue_and_start() -> None:
            self.web_task_queue.put_nowait(task_id)
            self.start_next_web_transfer_task()

        try:
            if asyncio.get_running_loop() is self.loop:
                enqueue_and_start()
                return
        except RuntimeError:
            pass
        self.loop.call_soon_threadsafe(enqueue_and_start)

    def _enqueue_and_process_web_task(self, task_id: int) -> None:
        self.web_submitted_task_ids.discard(task_id)
        self.web_task_queue.put_nowait(task_id)
        self.start_next_web_transfer_task()

    def _schedule_web_task_resubmission(self, task_id: int) -> None:
        loop = self.__dict__.get('loop')
        if loop and hasattr(loop, 'call_soon_threadsafe'):
            loop.call_soon_threadsafe(
                lambda tid=task_id: self._enqueue_and_process_web_task(tid)
            )
            return
        try:
            self.submit_web_task(task_id)
        except AttributeError:
            pass

    def discard_web_task_submission(self, task_id: int, cancel_running: bool = True) -> None:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.discard_web_task_submission(task_id, cancel_running)

        def cleanup() -> None:
            self.web_submitted_task_ids.discard(task_id)
            self.drop_web_task_from_queue(task_id)
            if (
                    cancel_running
                    and self.web_running_task_id == task_id
                    and self.web_running_task
                    and not self.web_running_task.done()
            ):
                self.web_running_task.cancel()

        try:
            if asyncio.get_running_loop() is self.loop:
                cleanup()
                return
        except RuntimeError:
            pass
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(cleanup)
        else:
            cleanup()

    def drop_web_task_from_queue(self, task_id: int) -> None:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.drop_web_task_from_queue(task_id)
        kept_task_ids = []
        while True:
            try:
                queued_task_id = self.web_task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if queued_task_id != task_id:
                kept_task_ids.append(queued_task_id)
            self.web_task_queue.task_done()
        for queued_task_id in kept_task_ids:
            self.web_task_queue.put_nowait(queued_task_id)

    def delete_web_task(self, task_id: int) -> bool:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.delete_web_task(task_id)
        if not self.transfer_store or not self.transfer_store.get_task(task_id):
            return False
        self.discard_web_task_submission(task_id, cancel_running=True)
        self.cancel_task_uploads(task_id)
        self.cancel_task_downloads(task_id)
        running_task = self.web_running_task
        if self.web_running_task_id == task_id and running_task and not running_task.done():
            if self.loop.is_running():
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        asyncio.wait_for(running_task, timeout=10.0),
                        self.loop
                    )
                    future.result(timeout=12)
                except Exception:
                    pass
            else:
                running_task.cancel()
        cleanup_result = self._ensure_media_manager().cleanup_task_files(task_id)
        if cleanup_result.get('failed'):
            return False
        return self.transfer_store.delete_task(task_id)

    def pause_web_task(self, task_id: int) -> bool:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.pause_web_task(task_id)
        if not self.transfer_store or not self.transfer_store.get_task(task_id):
            return False
        self.transfer_store.update_task(task_id, status=TransferStatus.PAUSED)
        self.transfer_store.add_event(task_id, 'Transfer task paused.', level='warning')
        self.cancel_task_downloads(task_id)
        self.pause_task_uploads(task_id)
        self.discard_web_task_submission(task_id, cancel_running=True)
        return True

    def resume_web_task(self, task_id: int) -> bool:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.resume_web_task(task_id)
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        if not task or task.get('status') != TransferStatus.PAUSED:
            return False
        self.transfer_store.update_task(task_id, status=TransferStatus.PENDING)
        self.transfer_store.add_event(task_id, 'Transfer task resumed.')
        self._schedule_web_task_resubmission(task_id)
        return True

    def retry_failed_web_task(self, task_id: int) -> int:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.retry_failed_web_task(task_id)
        if not self.transfer_store:
            return 0
        task = self.transfer_store.get_task(task_id)
        if not task:
            return 0
        failed_items = [
            item for item in self.transfer_store.list_items(task_id)
            if PikpakIntegrationManager.is_pikpak_archive_recoverable_item(item)
            or item.get('status') == TransferStatus.FAILURE
        ]
        retry_item_ids = [
            int(item['id'])
            for item in failed_items
            if not self.recover_pikpak_failed_item_before_retry(task, item)
        ]
        reset_items = self.transfer_store.retry_failed_item_ids(task_id, retry_item_ids)
        if reset_items:
            self._schedule_web_task_resubmission(task_id)
        return reset_items

    def list_watches(self, tz_offset_minutes: int | None = None) -> list:
        return self.watch_manager.list_watches(tz_offset_minutes=tz_offset_minutes)

    def create_watch(self, payload: dict) -> dict:
        return self.watch_manager.create_watch(payload)

    def delete_watch(self, watch_id: str) -> bool:
        return self.watch_manager.delete_watch(watch_id)

    def update_watch(self, watch_id: str, payload: dict) -> dict:
        return self.watch_manager.update_watch(watch_id, payload)

    def list_watch_events(
            self,
            watch_id: str,
            limit: int = 50,
            offset: int = 0,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ):
        return self.watch_manager.list_watch_events(
            watch_id,
            limit=limit,
            offset=offset,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes
        )

    def recover_pikpak_failed_item_before_retry(self, task: dict, item: dict) -> bool:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.recover_pikpak_failed_item_before_retry(task, item)
        if not self.is_pikpak_target(item.get('target_link') or task.get('target_link'), task.get('target_profile')):
            return False
        if not PikpakIntegrationManager.is_pikpak_archive_recoverable_item(item):
            return False
        if not item.get('file_name') and item.get('file_size') is None:
            return False
        item_id = int(item.get('id'))
        task_id = int(task.get('id'))
        result = self.archive_pikpak_item(
            target_profile='pikpak',
            item_id=item_id,
            task_id=task_id,
            message=None,
            source_link=item.get('source_link') or task.get('source_link'),
            source_folder=(
                item.get('source_folder')
                or source_folder_from_link(item.get('source_link') or task.get('source_link'))
            ),
            file_name=item.get('file_name'),
            file_size=item.get('file_size'),
            transferred_at=self.transfer_item_archive_timestamp(item),
            match_original_name=self.transfer_item_archive_match_original_name(item)
        )
        if not bool(getattr(result, 'ok', False)):
            return False
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
        self.transfer_store.update_item(
            item_id,
            phase=phase,
            status=TransferStatus.SUCCESS,
            error_message=''
        )
        self.transfer_store.add_event(
            task_id,
            f'PikPak ingest confirmation recovered before retry: {item.get("source_link") or task.get("source_link")}',
            item_id=item_id
        )
        self.refresh_transfer_task_counts(task_id)
        return True

    def next_web_operation_id(self, operation_type: str) -> str:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.next_web_operation_id(operation_type)
        self.web_operation_counter += 1
        return f'{operation_type}-{self.web_operation_counter}'

    def submit_web_operation(self, operation_type: str, payload: dict) -> dict:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.submit_web_operation(operation_type, payload)
        operation_id = self.next_web_operation_id(operation_type)
        operation = {
            'id': operation_id,
            'type': operation_type,
            'status': TransferStatus.PENDING,
            'payload': payload,
            'error_message': None,
            'created_at': TransferStore.utc_now(),
            'updated_at': TransferStore.utc_now()
        }
        self.web_operations[operation_id] = operation
        self.loop.call_soon_threadsafe(self.web_operation_queue.put_nowait, operation_id)
        return operation

    def detect_transfer_range(self, source_link: str) -> Optional[dict]:
        return self.transfer_engine.detect_transfer_range(source_link)

    async def detect_transfer_range_async(self, source_link: str) -> Optional[dict]:
        origin_meta = await _downloader().parse_link(client=self.app.client, link=source_link)
        chat_id = origin_meta.get('chat_id')
        if not chat_id:
            raise ValueError('Invalid source link.')
        detected = await self.detect_transfer_range_fast(chat_id)
        if detected:
            return detected
        return await self.detect_transfer_range_by_history_scan(chat_id)

    async def detect_transfer_range_by_history_scan(self, chat_id) -> Optional[dict]:
        oldest = None
        newest = None
        async for message in self.iter_transfer_range_history(chat_id=chat_id):
            newest = newest or message
            oldest = message
        if not newest or not oldest:
            return None
        return {
            'start_id': int(getattr(oldest, 'id')),
            'end_id': int(getattr(newest, 'id'))
        }

    async def detect_transfer_range_fast(self, chat_id) -> Optional[dict]:
        client = self.app.client
        history_count = getattr(client, 'get_chat_history_count', None)
        if not callable(history_count):
            return None
        try:
            newest = await self.get_first_transfer_range_history_message(chat_id=chat_id, limit=1)
            if not newest:
                return None
            count = int(await history_count(chat_id))
            if count <= 1:
                oldest = newest
            else:
                oldest = await self.get_first_transfer_range_history_message(
                    chat_id=chat_id,
                    limit=1,
                    offset=count - 1
                )
            if not oldest:
                return None
            start_id = int(getattr(oldest, 'id'))
            end_id = int(getattr(newest, 'id'))
            if start_id > end_id:
                return None
            if count > 1 and start_id == end_id:
                return None
        except (FloodWait, FloodPremiumWait) as e:
            await self.wait_for_telegram_flood(e, action='detect transfer range')
            return None
        except Exception:
            return None
        return {
            'start_id': start_id,
            'end_id': end_id
        }

    async def get_first_transfer_range_history_message(self, chat_id, limit: int = 1, **kwargs):
        async for message in self.app.client.get_chat_history(
                chat_id=chat_id,
                limit=limit,
                **kwargs
        ):
            return message
        return None

    async def iter_transfer_range_history(self, chat_id, limit: int = 100):
        offset_id = 0
        while True:
            last_message_id = None
            try:
                async for message in self.app.client.get_chat_history(
                        chat_id=chat_id,
                        limit=limit,
                        offset_id=offset_id
                ):
                    last_message_id = getattr(message, 'id', None)
                    yield message
            except (FloodWait, FloodPremiumWait) as e:
                await self.wait_for_telegram_flood(e, action='detect transfer range')
                continue
            if last_message_id is None:
                return
            next_offset_id = int(last_message_id)
            if next_offset_id <= 0 or next_offset_id == offset_id:
                return
            offset_id = next_offset_id

    def statistics(self) -> dict:
        from module.statistics_payload import build_statistics_payload

        payload = build_statistics_payload(
            link_info=DownloadTask.LINK_INFO,
            app=self.app,
            upload_tasks=UploadTask.TASKS,
        )
        payload['operations'] = list(self.web_operations.values())[-50:]
        return payload

    def export_table(self, table_type: str) -> dict:
        if table_type == 'link':
            exported = self.app.print_link_table(
                link_info=DownloadTask.LINK_INFO,
                export=True,
                only_export=True
            )
            folder = 'form' if is_docker() else 'DownloadRecordForm'
        elif table_type == 'count':
            exported = self.app.print_count_table(export=True, only_export=True)
            folder = 'form' if is_docker() else 'DownloadRecordForm'
        else:
            exported = self.app.print_upload_table(
                upload_tasks=UploadTask.TASKS,
                export=True,
                only_export=True
            )
            folder = 'form' if is_docker() else 'UploadRecordForm'
        return {
            'exported': bool(exported),
            'table_type': table_type,
            'directory': folder
        }

    def create_upload(self, payload: dict) -> dict:
        operation = self.submit_web_operation('upload', payload)
        return {'accepted': True, 'operation_id': operation['id']}

    def create_channel_download(self, payload: dict) -> dict:
        operation = self.submit_web_operation('channel_download', payload)
        return {'accepted': True, 'operation_id': operation['id']}

    def list_operations(self, limit: int = 50) -> list:
        """列出 WebUI 下载/上传操作记录（最近 N 条）。"""
        ops = [op for op in self.web_operations.values()
               if op.get('type') in ('channel_download', 'upload')]
        ops.sort(key=lambda o: o.get('created_at', ''), reverse=True)
        return ops[:limit]

    # --- 媒体管理 (Media Manager) ---

    def _ensure_media_manager(self) -> MediaManager:
        app = self.__dict__.get('app')
        store = self.__dict__.get('transfer_store')
        fallback_directory = getattr(store, 'directory', '') if store else ''
        save_directory = getattr(app, 'save_directory', None) or fallback_directory
        temp_directory = getattr(app, 'temp_directory', None) or fallback_directory
        media_manager = self.__dict__.get('media_manager')
        if media_manager is not None:
            current_roots = {
                media_manager._save_directory,
                media_manager._temp_directory,
                media_manager._store_directory,
            }
            next_roots = {
                os.path.abspath(save_directory) if save_directory else '',
                os.path.abspath(temp_directory) if temp_directory else '',
                os.path.abspath(getattr(store, 'directory', '') or '') if store else '',
            }
            if current_roots == next_roots:
                return media_manager
        self.media_manager = MediaManager(
            transfer_store=store,
            save_directory=save_directory,
            temp_directory=temp_directory,
            diagnostic=getattr(self, 'diagnostic', None)
        )
        return self.media_manager

    def scan_media_for_cleanup(
            self,
            task_id: int = None,
            items_limit: int = None,
            items_offset: int = 0,
            orphans_limit: int = None,
            orphans_offset: int = 0,
    ) -> dict:
        """扫描可清理的媒体文件。"""
        mm = self._ensure_media_manager()
        return mm.scan_all(
            task_id=task_id,
            items_limit=items_limit,
            items_offset=items_offset,
            orphans_limit=orphans_limit,
            orphans_offset=orphans_offset,
        )

    def cleanup_media_files(self, payload: dict) -> dict:
        """执行媒体文件清理。

        payload: {'item_ids': [...], 'file_paths': [...]}
        """
        mm = self._ensure_media_manager()
        item_ids = payload.get('item_ids') or []
        file_paths = payload.get('file_paths') or []

        result = {
            'item_result': None,
            'orphan_result': None,
            'total_deleted_count': 0,
            'total_deleted_size': 0,
        }

        if item_ids:
            item_result = mm.cleanup_by_item_ids([int(i) for i in item_ids])
            result['item_result'] = item_result
            result['total_deleted_count'] += item_result['total_deleted_count']
            result['total_deleted_size'] += item_result['total_deleted_size']

        if file_paths:
            orphan_result = mm.cleanup_orphan_files(file_paths)
            result['orphan_result'] = orphan_result
            result['total_deleted_count'] += orphan_result['total_deleted_count']
            result['total_deleted_size'] += orphan_result['total_deleted_size']

        return result

    def maybe_run_scheduled_media_cleanup(self) -> None:
        if not self.transfer_store:
            return
        now = time.time()
        last_run = getattr(self, '_last_orphan_cleanup_at', 0.0)
        if now - last_run < ORPHAN_CLEANUP_INTERVAL_SECONDS:
            return
        self._last_orphan_cleanup_at = now
        try:
            result = self._ensure_media_manager().auto_cleanup_orphan_files()
            deleted_count = int(result.get('total_deleted_count') or 0)
            if deleted_count:
                diagnostic = getattr(self, 'diagnostic', None)
                message = f'Auto orphan cleanup removed {deleted_count} file(s).'
                if diagnostic is not None:
                    diagnostic.info(message)
                else:
                    log.info(message)
        except Exception as error:
            log.warning(f'Scheduled orphan cleanup failed: {error}')

    def list_cleanup_logs(self) -> list:
        if not self.transfer_store:
            return []
        return self.transfer_store.list_cleanup_logs()

    def list_system_logs(
            self,
            limit: int = 50,
            offset: int = 0,
            category: str | None = None,
            level: str | None = None,
            trace_id: str | None = None,
            watch_id: str | None = None,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ) -> dict:
        if not self.transfer_store:
            return {'logs': [], 'total': 0, 'limit': limit, 'offset': offset}
        logs, total = self.transfer_store.list_system_logs(
            limit=limit,
            offset=offset,
            category=category,
            level=level,
            trace_id=trace_id,
            watch_id=watch_id,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes
        )
        return {
            'logs': logs,
            'total': total,
            'limit': limit,
            'offset': offset,
            'retention_days': self.transfer_store.SYSTEM_LOGS_RETENTION_DAYS
        }

    def get_web_settings(self) -> dict:
        return {
            'user': {
                'config_path': self.app.config_path,
                'api_id': self.app.config.get('api_id'),
                'api_hash': self.app.config.get('api_hash'),
                'bot_token': self.app.config.get('bot_token'),
                'session_directory': self.app.config.get('session_directory'),
                'save_directory': self.app.config.get('save_directory'),
                'temp_directory': self.app.config.get('temp_directory'),
                'max_tasks': self.app.config.get('max_tasks'),
                'max_retries': self.app.config.get('max_retries'),
                'download_type': self.app.config.get('download_type'),
                'is_shutdown': self.app.config.get('is_shutdown'),
                'proxy': self.app.config.get('proxy')
            },
            'global': self.gc.config
        }

    def update_web_settings(self, payload: dict) -> dict:
        user_config = merge_allowed_settings(
            target=deepcopy(self.app.config),
            patch=payload.get('user', {}) if isinstance(payload, dict) else {},
            allowed={
                'api_id', 'api_hash', 'bot_token', 'session_directory', 'save_directory',
                'temp_directory', 'max_tasks', 'max_retries', 'download_type', 'is_shutdown',
                'proxy'
            }
        )
        global_config = merge_allowed_settings(
            target=deepcopy(self.gc.config),
            patch=payload.get('global', {}) if isinstance(payload, dict) else {},
            allowed={'notice', 'export_table', 'upload', 'forward_type', 'target_profiles', 'message_filter'}
        )
        user_config = UserConfig.normalize_runtime_numbers(user_config)
        self.app.save_config(user_config)
        self.app.config = user_config
        self.app.download_type = user_config.get('download_type')
        self.app.is_shutdown = user_config.get('is_shutdown')
        self.app.max_download_task = user_config['max_tasks']['download']
        self.app.max_upload_task = user_config['max_tasks']['upload']
        self.app.max_download_retries = user_config['max_retries']['download']
        self.app.max_upload_retries = user_config['max_retries']['upload']
        self.app.save_directory = user_config.get('save_directory')
        dl = _downloader()
        self.app.temp_directory = dl.PARSE_ARGS.temp or (user_config.get('temp_directory') or self.app.TEMP_DIRECTORY)
        self.app.work_directory = dl.PARSE_ARGS.session or (
                user_config.get('session_directory') or self.app.WORK_DIRECTORY)
        self.gc.save_config(global_config)
        self.download_upload_window.notify_limit_changed()
        if getattr(self, 'local_storage_guard', None):
            self.local_storage_guard.notify_limit_changed()
        return self.get_web_settings()

    def start_web_ui(self, with_auth_provider: bool = False) -> None:
        dl = _downloader()
        if dl.PARSE_ARGS.web is None:
            return
        self.transfer_store = dl.TransferStore(directory=self.app.temp_directory)
        system_log = getattr(self, 'system_log', None)
        if system_log is not None:
            system_log.bind(store=self.transfer_store)
        ctx = self.__dict__.get('ctx')
        if ctx is not None:
            ctx.transfer_store = self.transfer_store
        self.web_ui = dl.WebUiServer(
            store=self.transfer_store,
            task_submitter=self.submit_web_task,
            settings_provider=self.get_web_settings,
            settings_updater=self.update_web_settings,
            operations=self._web_ui_operations(),
            host=get_web_host_from_env(),
            port=get_web_port_from_env(),
            username=get_web_username_from_env(),
            password=get_web_password_from_env(),
            diagnostic=getattr(self, 'diagnostic', None)
        )
        if with_auth_provider:
            from module.web_ui import AuthProvider
            self.web_ui_auth = AuthProvider()
            self.web_ui.set_auth_provider(self.web_ui_auth)
        self.web_ui.start(open_browser=True)
        for task in self.transfer_store.list_tasks():
            if task.get('status') in (TransferStatus.PENDING, TransferStatus.RUNNING, TransferStatus.FAILURE):
                self.submit_web_task(int(task.get('id')))
        recovered_archives = 0
        progress_tracker = getattr(self, 'progress_tracker', None)
        if progress_tracker is not None:
            recovered_archives = progress_tracker.recover_pending_upload_archives()
        if recovered_archives:
            self.diagnostic.info(f'Recovered {recovered_archives} pending PikPak upload archive job(s).')
        console.log(f'WebUI已启动: {self.web_ui.url}', style='#B1DB74')
    async def process_web_operation(self, operation_id: str) -> None:
        operation = self.web_operations.get(operation_id)
        if not operation:
            return
        operation['status'] = TransferStatus.RUNNING
        operation['updated_at'] = TransferStore.utc_now()
        try:
            operation_type = operation.get('type')
            payload = operation.get('payload') or {}
            if operation_type == 'watch':
                await self.apply_web_watch(payload)
            elif operation_type == 'upload':
                await self.apply_web_upload(payload)
            elif operation_type == 'channel_download':
                await self.apply_web_channel_download(payload)
            else:
                raise ValueError(f'Unsupported WebUI operation: {operation_type}')
            operation['status'] = TransferStatus.SUCCESS
        except Exception as e:
            operation['status'] = TransferStatus.FAILURE
            operation['error_message'] = str(e)
            payload = operation.get('payload') or {}
            if operation.get('type') == 'watch':
                self.mark_pending_watch(payload, TransferStatus.FAILURE, str(e))
            log.exception(f'WebUI操作失败:{operation_id},{_t(KeyWord.REASON)}:"{e}"')
        finally:
            operation['updated_at'] = TransferStore.utc_now()

    async def restore_live_transfer_watches(self) -> None:
        for watch in self.persisted_watches():
            watch_id = watch.get('id')
            if not watch_id:
                continue
            if watch.get('type') == 'download' and watch.get('source_link') in self.listen_download_chat:
                continue
            if watch.get('type') == 'forward':
                rule = make_forward_watch_rule(
                    watch.get('source_link'),
                    watch.get('target_link'),
                    bool(watch.get('include_comment'))
                )
                if rule in self.listen_forward_chat:
                    continue
            self.web_pending_watches[watch_id] = {
                **watch,
                'status': TransferStatus.PENDING,
                'error_message': None
            }
            self.set_live_watch_status(watch_id, TransferStatus.PENDING)
            try:
                await self.apply_web_watch(self.watch_payload_from_record(watch))
            except Exception as e:
                self.mark_pending_watch(self.watch_payload_from_record(watch), TransferStatus.FAILURE, str(e))
                log.exception(f'恢复WebUI实时监听失败:{watch_id},{_t(KeyWord.REASON)}:"{e}"')

    def _ensure_watch_applicator(self) -> LiveWatchApplicator:
        applicator = self.__dict__.get('_watch_applicator')
        if applicator is None:
            applicator = LiveWatchApplicator(host=self)
            self._watch_applicator = applicator
        return applicator

    async def apply_web_watch(self, payload: dict) -> None:
        return await self._ensure_watch_applicator().apply_watch(payload)

    def remove_web_watch(self, watch_id: str) -> bool:
        return self._ensure_watch_applicator().remove_watch(watch_id)

    async def apply_web_upload(self, payload: dict) -> None:
        if not self.uploader:
            self.uploader = TelegramUploader(upload_context=self)
        upload_path = payload.get('path')
        target_link = payload.get('target_link')
        recursive = bool(payload.get('recursive'))
        if os.path.isdir(upload_path):
            if recursive:
                upload_files = [
                    os.path.join(root, filename)
                    for root, _dirs, files in os.walk(upload_path)
                    for filename in files
                ]
            else:
                upload_files = [
                    os.path.join(upload_path, filename)
                    for filename in os.listdir(upload_path)
                    if os.path.isfile(os.path.join(upload_path, filename))
                ]
        else:
            upload_files = [upload_path]
        if not upload_files:
            raise ValueError('Upload path contains no files.')
        for file_path in upload_files:
            file_size = os.path.getsize(file_path)
            upload_task = UploadTask(
                chat_id=None,
                file_path=file_path,
                file_id=self.app.client.rnd_id(),
                file_size=file_size,
                file_part=[],
                status=UploadStatus.PENDING,
                with_delete=self.gc.upload_delete
            )
            await self.uploader.create_upload_task(link=target_link, upload_task=upload_task)

    async def apply_web_channel_download(self, payload: dict) -> None:
        chat_link = payload.get('chat_link')
        meta = await _downloader().parse_link(client=self.app.client, link=chat_link)
        chat_id = meta.get('chat_id')
        date_range = payload.get('date_range') or {}
        start_date = date_range.get('start_date')
        end_date = date_range.get('end_date')
        download_type = {
            dtype: dtype in set(payload.get('download_type') or [])
            for dtype in DownloadType()
        }
        keywords = payload.get('keywords') or []
        include_comment = bool(payload.get('include_comment'))
        filter_obj = Filter()
        links = []
        async for message in self.app.client.get_chat_history(chat_id=chat_id, reverse=True):
            if (
                    filter_obj.date_range(message, start_date, end_date)
                    and filter_obj.dtype(message, download_type)
                    and filter_obj.keyword_filter(message, keywords)
            ):
                links.append(message.link if getattr(message, 'link', None) else message)
                if include_comment:
                    try:
                        async for comment in iter_discussion_reply_messages(
                                client=self.app.client,
                                chat_id=chat_id,
                                message_id=message.id,
                                include_message=lambda item: filter_obj.dtype(item, download_type)
                        ):
                            links.append(comment.link if getattr(comment, 'link', None) else comment)
                    except (ValueError, AttributeError, MsgIdInvalid):
                        pass
        for link in links:
            await self.create_download_task(
                message_ids=link,
                single_link=True,
                diy_download_type=[_ for _ in DownloadType()]
            )

    async def process_web_task_queue(self) -> None:
        self.start_next_web_transfer_task()
        while not self.web_task_queue.empty():
            if self.web_running_task and not self.web_running_task.done():
                break
            self.start_next_web_transfer_task()
            if self.web_running_task and not self.web_running_task.done():
                break
        while not self.web_operation_queue.empty():
            operation_id = await self.web_operation_queue.get()
            try:
                await self.process_web_operation(operation_id)
            finally:
                self.web_operation_queue.task_done()

    def start_next_web_transfer_task(self) -> None:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.start_next_web_transfer_task()
        if self.web_running_task and not self.web_running_task.done():
            return
        if self.web_running_task and self.web_running_task.done():
            self.finish_web_transfer_task(self.web_running_task_id, self.web_running_task)
        while not self.web_task_queue.empty():
            try:
                task_id = int(self.web_task_queue.get_nowait())
            except asyncio.QueueEmpty:
                return
            try:
                if not self.is_web_transfer_task_schedulable(task_id):
                    self.web_submitted_task_ids.discard(task_id)
                    continue
                runner = self.loop.create_task(self.process_web_transfer_task(task_id))
                self.web_running_task = runner
                self.web_running_task_id = task_id
                runner.add_done_callback(
                    lambda completed_task, completed_task_id=task_id: self.finish_web_transfer_task(
                        completed_task_id,
                        completed_task
                    )
                )
                return
            finally:
                self.web_task_queue.task_done()

    def is_web_transfer_task_schedulable(self, task_id: int) -> bool:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.is_web_transfer_task_schedulable(task_id)
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        return bool(
            task
            and task.get('status') in (TransferStatus.PENDING, TransferStatus.RUNNING, TransferStatus.FAILURE)
        )

    def finish_web_transfer_task(self, task_id: Optional[int], completed_task: asyncio.Task) -> None:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.finish_web_transfer_task(task_id, completed_task)
        if task_id is not None:
            self.web_submitted_task_ids.discard(task_id)
        if self.web_running_task is completed_task:
            self.web_running_task = None
            self.web_running_task_id = None
        if not completed_task.cancelled():
            error = completed_task.exception()
            if error:
                log.error(
                    f'WebUI转存任务执行失败:{task_id},{_t(KeyWord.REASON)}:"{error}"',
                    exc_info=(type(error), error, error.__traceback__)
                )
        if not self.web_task_queue.empty():
            self.loop.create_task(self.process_web_task_queue())


_WEB_UI_DELEGATE_METHODS = (
    'should_continue_web_transfer_task', 'cancel_task_uploads', 'pause_task_uploads', 'cancel_task_downloads', 'submit_web_task',
    'delete_web_task', 'pause_web_task', 'resume_web_task', 'retry_failed_web_task',
    'list_watches', 'create_watch', 'update_watch', 'delete_watch', 'list_watch_events',
    'detect_transfer_range', 'statistics', 'export_table', 'create_upload',
    'create_channel_download', 'list_operations', 'scan_media_for_cleanup',
    'cleanup_media_files', 'list_cleanup_logs', 'list_system_logs',
)


class WebOperationsFacade:
    """Standalone IWebUiOperations adapter; delegates to host mixin methods."""

    def __init__(self, host):
        self._host = host


def _bind_web_delegate(name: str):
    def delegate(self, *args, **kwargs):
        return getattr(self._host, name)(*args, **kwargs)
    delegate.__name__ = name
    return delegate


for _method_name in _WEB_UI_DELEGATE_METHODS:
    setattr(WebOperationsFacade, _method_name, _bind_web_delegate(_method_name))
