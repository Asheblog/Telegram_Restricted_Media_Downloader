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
from module.transfer_store import DeferredDiscussionCaptureStatus, TransferStore, TransferStatus
from module.transfer.comment_delay import CommentDelayScheduler


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
from module.source_folders import archive_source_folder


def _downloader():
    """Lazy import so unit tests can patch names on module.downloader."""
    import module.downloader as downloader_module
    return downloader_module


class WebOperationsMixin:
    def _ensure_transfer_store(self) -> TransferStore:
        store = getattr(self, 'transfer_store', None)
        if store is not None:
            return store
        temp_directory = getattr(getattr(self, 'app', None), 'temp_directory', None)
        if not temp_directory:
            raise RuntimeError('temp_directory is required to create TransferStore')
        store = TransferStore(directory=temp_directory)
        self.transfer_store = store
        ctx = self.__dict__.get('ctx')
        if ctx is not None:
            ctx.transfer_store = store
        system_log = getattr(self, 'system_log', None)
        if system_log is not None:
            system_log.bind(store=store)
        return store

    def _ensure_comment_delay_scheduler(self) -> CommentDelayScheduler:
        scheduler = self.__dict__.get('comment_delay_scheduler')
        if scheduler is None:
            store = self._ensure_transfer_store()

            async def executor(capture: dict):
                client = (
                    capture.get('client')
                    or getattr(self, 'user', None)
                    or getattr(getattr(self, 'app', None), 'client', None)
                )
                resolve_deep_link = False
                archive_by_author = False
                watch_id = capture.get('watch_id')
                if watch_id and store is not None:
                    watch = store.get_live_transfer_watch(str(watch_id))
                    if watch:
                        resolve_deep_link = bool(watch.get('resolve_deep_link'))
                        archive_by_author = bool(watch.get('archive_by_author'))
                count = await self.forward_discussion_replies(
                    client=client,
                    source_chat_id=capture.get('source_chat_id'),
                    source_message_id=int(capture.get('source_message_id')),
                    target_chat_id=capture.get('target_chat_id'),
                    target_link=capture.get('target_link'),
                    watch_id=capture.get('watch_id'),
                    resolve_deep_link=resolve_deep_link,
                    archive_by_author=archive_by_author,
                )
                watch_id = capture.get('watch_id')
                if watch_id:
                    self._record_watch_event(
                        watch_id,
                        capture.get('source_chat_id'),
                        capture.get('source_message_id'),
                        capture.get('target_chat_id'),
                        capture.get('target_link'),
                        'success' if count else 'skipped',
                        f'延迟抓取评论区完成,匹配{count}条'
                    )
                return count

            def on_cancel(capture: dict):
                self._cancel_derived_tasks_for_deferred_capture(capture)

            scheduler = CommentDelayScheduler(
                store=store,
                delay_minutes_getter=lambda: self.gc.get_comment_delay_minutes(),
                executor=executor,
                on_cancel=on_cancel,
                has_active_derived=self._has_active_derived_tasks_for_deferred_capture,
            )
            self.comment_delay_scheduler = scheduler
        # Always (re)arm: first call may come from a WebUI worker thread without a
        # running loop; pass the app loop so start can attach via call_soon_threadsafe.
        scheduler.start(loop=getattr(self, 'loop', None))
        return scheduler

    def _has_active_derived_tasks_for_deferred_capture(self, capture: dict) -> bool:
        if not capture:
            return False
        watch_id = capture.get('watch_id')
        if not watch_id:
            return False
        store = self._ensure_transfer_store()
        started_at = str(capture.get('updated_at') or '')
        for task in store.list_tasks(limit=500, watch_id=watch_id):
            if task.get('status') not in (TransferStatus.PENDING, TransferStatus.RUNNING):
                continue
            created_at = str(task.get('created_at') or '')
            if started_at and created_at and created_at < started_at:
                continue
            return True
        return False

    def _cancel_derived_tasks_for_deferred_capture(self, capture: dict) -> None:
        """Best-effort cancel web transfer tasks spawned by a running deferred capture."""
        if not capture or capture.get('status') != DeferredDiscussionCaptureStatus.RUNNING:
            return
        watch_id = capture.get('watch_id')
        if not watch_id:
            return
        store = self._ensure_transfer_store()
        started_at = str(capture.get('updated_at') or '')
        for task in store.list_tasks(limit=500, watch_id=watch_id):
            if task.get('status') not in (TransferStatus.PENDING, TransferStatus.RUNNING):
                continue
            created_at = str(task.get('created_at') or '')
            if started_at and created_at and created_at < started_at:
                continue
            task_id = task.get('id')
            if task_id is None:
                continue
            try:
                self.delete_web_task(int(task_id))
            except Exception:
                log.exception('取消延迟评论区派生转存失败: task_id=%s', task_id)

    async def schedule_or_forward_discussion_replies(
            self,
            *,
            client,
            source_chat_id,
            source_message_id: int,
            target_chat_id,
            target_link: str,
            watch_id: Optional[str] = None,
            done_notice: Optional[bool] = True,
    ) -> Optional[dict]:
        scheduler = self._ensure_comment_delay_scheduler()
        scheduled = await scheduler.schedule(
            watch_id=watch_id or '',
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            target_chat_id=target_chat_id,
            target_link=target_link,
            client=client,
        )
        if scheduled is None:
            return None
        if watch_id:
            due_at = float(scheduled.get('due_at') or 0)
            delay_minutes = max(0, int(round((due_at - time.time()) / 60)))
            self._record_watch_event(
                watch_id,
                source_chat_id,
                source_message_id,
                target_chat_id,
                target_link,
                'success',
                f'已调度延迟抓取评论区,约{delay_minutes}分钟后执行'
            )
        return scheduled

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

    def should_start_next_web_transfer_item(self, task_id: int) -> bool:
        """Whether a new Transfer Item may start. False while pausing/paused."""
        if not self.transfer_store or not task_id:
            return False
        task = self.transfer_store.get_task(int(task_id))
        if not task:
            return False
        return task.get('status') not in (TransferStatus.PAUSING, TransferStatus.PAUSED)

    def has_active_transfer_io(self, task_id: int) -> bool:
        for download_task in self._transfer_download_registry().get(int(task_id), set()):
            if download_task is not None and not download_task.done():
                return True
        uploader = getattr(self, 'uploader', None)
        registry_getter = getattr(uploader, '_transfer_upload_registry', None) if uploader else None
        if callable(registry_getter):
            for upload_task in registry_getter().get(int(task_id), set()):
                if upload_task is not None and not upload_task.done():
                    return True
        return False

    async def settle_web_task_pause_request(self, task_id: int, *, before: str | None = None) -> bool:
        """Wait out in-flight IO while pausing, then finalize to paused. Return True to stop."""
        if not self.transfer_store or not task_id:
            return True
        while True:
            task = self.transfer_store.get_task(int(task_id))
            if not task:
                return True
            status = task.get('status')
            if status == TransferStatus.PAUSED:
                return True
            if status != TransferStatus.PAUSING:
                return False
            if self.has_active_transfer_io(int(task_id)):
                await asyncio.sleep(0.2)
                continue
            self.transfer_store.update_task(int(task_id), status=TransferStatus.PAUSED)
            message = 'Transfer task paused.'
            if before:
                message = f'Transfer task paused before item: {before}.'
            self.transfer_store.add_event(int(task_id), message, level='warning')
            return True

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
        task = self.transfer_store.get_task(task_id)
        if task.get('status') not in (TransferStatus.PENDING, TransferStatus.RUNNING):
            return False
        has_runner = (
            getattr(self, 'web_running_task_id', None) == task_id
            and getattr(self, 'web_running_task', None) is not None
            and not self.web_running_task.done()
        )
        if has_runner:
            self.transfer_store.update_task(task_id, status=TransferStatus.PAUSING)
            self.transfer_store.add_event(task_id, 'Transfer task pause requested.', level='warning')
            return True
        self.transfer_store.update_task(task_id, status=TransferStatus.PAUSED)
        self.transfer_store.add_event(task_id, 'Transfer task paused.', level='warning')
        self.discard_web_task_submission(task_id, cancel_running=True)
        return True

    def resume_web_task(self, task_id: int) -> bool:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.resume_web_task(task_id)
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        if not task:
            return False
        status = task.get('status')
        if status == TransferStatus.PAUSING:
            self.transfer_store.update_task(task_id, status=TransferStatus.RUNNING)
            self.transfer_store.add_event(task_id, 'Transfer task pause cancelled.')
            return True
        if status != TransferStatus.PAUSED:
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

    def export_forward_watches(self) -> dict:
        return self.watch_manager.export_forward_watches()

    def delete_watch(self, watch_id: str) -> bool:
        scheduler = self.__dict__.get('comment_delay_scheduler')
        if scheduler is not None:
            try:
                scheduler.cancel_for_watch(watch_id)
            except Exception:
                log.exception('删除监听时取消延迟评论区失败: %s', watch_id)
        return self.watch_manager.delete_watch(watch_id)

    def update_watch(self, watch_id: str, payload: dict) -> dict:
        return self.watch_manager.update_watch(watch_id, payload)

    def list_watch_events(
            self,
            watch_id: str,
            limit: int = 50,
            offset: int = 0,
            today_only: bool = False,
            tz_offset_minutes: int | None = None,
            status: str | None = None
    ):
        return self.watch_manager.list_watch_events(
            watch_id,
            limit=limit,
            offset=offset,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes,
            status=status
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
                or archive_source_folder(
                    fallback_link=item.get('source_link') or task.get('source_link'),
                    post_message_id=item.get('range_message_id') or item.get('source_message_id'),
                    archive_by_author=bool(task.get('archive_by_author')),
                )
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

    def statistics(self, tz_offset_minutes: int | None = None) -> dict:
        from module.statistics_payload import (
            DEFAULT_STATISTICS_WINDOW_DAYS,
            build_statistics_payload,
        )

        rows = self.transfer_store.aggregate_channel_download_stats(
            days=DEFAULT_STATISTICS_WINDOW_DAYS,
            tz_offset_minutes=tz_offset_minutes,
        )
        payload = build_statistics_payload(
            rows,
            window_days=DEFAULT_STATISTICS_WINDOW_DAYS,
        )
        payload['operations'] = list(self.web_operations.values())[-50:]
        return payload

    def export_table(self, table_type: str) -> dict:
        if table_type == 'channel':
            return self._export_channel_statistics_table()
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

    def _export_channel_statistics_table(self) -> dict:
        import csv
        import datetime
        import os
        import sys
        from module.statistics_payload import (
            DEFAULT_STATISTICS_WINDOW_DAYS,
            build_statistics_payload,
        )

        rows = self.transfer_store.aggregate_channel_download_stats(
            days=DEFAULT_STATISTICS_WINDOW_DAYS,
            tz_offset_minutes=None,
        )
        payload = build_statistics_payload(
            rows,
            window_days=DEFAULT_STATISTICS_WINDOW_DAYS,
        )
        if not payload['tables']['channel']['available']:
            return {
                'exported': False,
                'table_type': 'channel',
                'directory': 'DownloadRecordForm',
            }
        if is_docker():
            directory = '/app/form/ChannelForm'
            folder = 'form'
        else:
            directory = os.path.join(
                os.path.dirname(os.path.abspath(sys.argv[0])),
                'DownloadRecordForm',
                'ChannelForm',
            )
            folder = 'DownloadRecordForm'
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(
            directory,
            f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_频道下载统计表.csv',
        )
        with open(path, 'w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['频道', '成功', '失败', '跳过', '合计', '成功率'])
            for row in payload['channels']:
                writer.writerow([
                    row['channel'],
                    row['success'],
                    row['failure'],
                    row['skip'],
                    row['total'],
                    row['success_rate'],
                ])
        return {
            'exported': True,
            'table_type': 'channel',
            'directory': folder,
            'path': path,
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

    def _run_telegram_coro(self, coro, timeout: float | None = 300):
        """Run a coroutine on the Telegram loop from a worker thread.

        ``timeout=None`` waits indefinitely — required for long FloodWait-heavy
        archive author scans.
        """
        loop = getattr(self, 'loop', None)
        if loop is None:
            raise RuntimeError('Telegram event loop is unavailable.')
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=timeout)

    def _archive_author_service(self):
        from module.archive_author_tool import ArchiveAuthorReorganizeService
        from module.pikpak_archive import build_pikpak_archive_client

        client = getattr(self, 'pikpak_archive_client', None)
        manager = getattr(self, 'pikpak_manager', None)
        if client is None and manager is not None:
            getter = getattr(manager, '_pikpak_archive_client_getter', None)
            if callable(getter):
                try:
                    client = getter()
                except Exception:
                    client = None
            if client is None:
                existing = getattr(manager, '_pikpak_archive_client', None)
                if existing is not None:
                    client = existing
        if client is None:
            config = {}
            gc = getattr(self, 'gc', None)
            raw = getattr(gc, 'config', None) if gc is not None else None
            if isinstance(raw, dict):
                config = (
                    (raw.get('target_profiles') or {})
                    .get('pikpak', {})
                    .get('archive')
                    or {}
                )
            client = build_pikpak_archive_client(config if isinstance(config, dict) else {})
        app = getattr(self, 'app', None)
        telegram = getattr(self, 'user', None)
        if telegram is None and app is not None:
            telegram = getattr(app, 'client', None)
        store = None
        try:
            store = self._ensure_transfer_store()
        except Exception:
            store = getattr(self, 'transfer_store', None)
        return ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=telegram,
            transfer_store=store,
            run_coro=self._run_telegram_coro,
            on_log=self._archive_author_log,
        )

    def _archive_author_log(
            self,
            *,
            stage: str,
            message: str,
            level: str = 'info',
            source_message_id=None,
            details=None,
    ) -> None:
        system_log = getattr(self, 'system_log', None)
        if system_log is not None and hasattr(system_log, 'log'):
            try:
                system_log.log(
                    category='archive',
                    stage=stage,
                    message=message,
                    level=level,
                    source_message_id=source_message_id,
                    details=details,
                )
                return
            except Exception:
                pass
        diagnostic = getattr(self, 'diagnostic', None)
        if diagnostic is None:
            return
        line = f'[archive/{stage}] {message}'
        try:
            if level == 'error' and hasattr(diagnostic, 'error'):
                diagnostic.error(line)
            elif level == 'warning' and hasattr(diagnostic, 'warning'):
                diagnostic.warning(line)
            elif hasattr(diagnostic, 'info'):
                diagnostic.info(line)
        except Exception:
            pass

    def list_archive_author_channels(self) -> dict:
        service = self._archive_author_service()
        return {'channels': service.list_channels()}

    def _archive_author_job_store(self):
        from module.archive_author_jobs import ArchiveAuthorJobStore
        store = getattr(self, '_archive_author_jobs', None)
        if store is None:
            transfer_store = None
            try:
                transfer_store = self._ensure_transfer_store()
            except Exception:
                transfer_store = getattr(self, 'transfer_store', None)
            store = ArchiveAuthorJobStore(transfer_store=transfer_store)
            self._archive_author_jobs = store
        return store

    def _spawn_archive_author_runner(
            self,
            *,
            job_id: str,
            kind: str,
            channel_folder: str,
            execute_mode: str = 'all',
            resolve_scope: str = 'all',
            completed_keys: Optional[set] = None,
    ) -> None:
        import threading

        from module.archive_author_jobs import completed_keys_from_job

        jobs = self._archive_author_job_store()
        on_progress = jobs.progress_callback(job_id)
        on_checkpoint = jobs.checkpoint_callback(job_id)
        service = self._archive_author_service()
        mode = str(execute_mode or 'all').strip().lower() or 'all'
        scope = str(resolve_scope or 'all').strip().lower() or 'all'
        seed_keys = set(completed_keys or set())
        jobs.mark_runner_live(job_id)
        # Clear any previous stop request when (re)starting the runner.
        flag = jobs.attach_cancel_flag(job_id)
        flag.clear()

        def runner():
            try:
                if kind == 'scan':
                    result = service.scan(channel_folder, on_progress=on_progress)
                elif kind == 'resolve':
                    prior = jobs.latest_successful_scan_result(channel_folder)
                    paths = jobs.latest_directory_paths(channel_folder)
                    result = service.resolve_from_listing(
                        channel_folder,
                        directory_paths=paths or None,
                        prior_plan=prior,
                        on_progress=on_progress,
                        done_label=(
                            '未识别解析完成'
                            if scope in ('unresolved', 'review', 'needs_review', 'miss')
                            else '解析完成'
                        ),
                        require_telegram=True,
                        resolve_scope=scope,
                    )
                else:
                    # Reuse last successful scan/resolve plan — never rescan before move.
                    plan = jobs.latest_successful_scan_result(channel_folder)
                    from module.archive_reorganize import planned_count_for_execute_mode
                    executable = planned_count_for_execute_mode(plan, mode)
                    if not plan or executable <= 0:
                        raise RuntimeError(
                            '请先完成「扫描作者分布」或「重新解析作者」。'
                            '整理会复用计划并串行移动，不会再次全量扫描网盘。'
                        )
                    if not seed_keys:
                        seed_keys.update(completed_keys_from_job(jobs.get(job_id)))
                    result = service.execute_plan(
                        plan,
                        on_progress=on_progress,
                        execute_mode=mode,
                        completed_keys=seed_keys,
                        should_stop=lambda: jobs.should_stop(job_id),
                        on_checkpoint=on_checkpoint,
                    )
                if kind in ('scan', 'resolve'):
                    stats = result.get('resolve_stats') or {}
                    scope_note = ''
                    if kind == 'resolve' and (stats.get('preserved') or 0):
                        scope_note = (
                            f'保留已识别 {stats.get("preserved") or 0}，'
                            f'回查未识别 {stats.get("refetch") or 0}；'
                        )
                    done_message = (
                        f'{"扫描" if kind == "scan" else "解析"}完成：'
                        f'{scope_note}'
                        f'解析到作者 {result.get("resolved_author_count") or 0}/'
                        f'{result.get("message_id_count") or 0}'
                        f'（抓取 {stats.get("fetched") or 0}，'
                        f'相册 {stats.get("media_group_hits") or 0}，'
                        f'邻条 {stats.get("neighbor_hits") or 0}，'
                        f'标签精确 {stats.get("hashtag_exact_hits") or 0}，'
                        f'标签待确认 {stats.get("hashtag_substring_hits") or 0}），'
                        f'{result.get("author_count") or 0} 个作者目录，'
                        f'待移动 {result.get("move_count") or 0}，'
                        f'待确认 {result.get("confirm_count") or 0}，'
                        f'未识别 {result.get("review_count") or 0}，'
                        f'跳过 {result.get("skip_count") or 0}'
                    )
                    jobs.update(
                        job_id,
                        status='success',
                        phase='done',
                        result=result,
                        message=done_message,
                        percent=100,
                    )
                else:
                    if result.get('stopped'):
                        done_message = (
                            f'已停止：新移动 {result.get("moved_count") or 0}，'
                            f'已就位跳过 {result.get("skipped_already_count") or 0}，'
                            f'失败 {result.get("error_count") or 0}；重启或再次迁移可续跑'
                        )
                        jobs.update(
                            job_id,
                            status='stopped',
                            phase='stopped',
                            result=result,
                            message=done_message,
                        )
                    else:
                        done_message = (
                            f'整理完成：新移动 {result.get("moved_count") or 0}，'
                            f'已就位跳过 {result.get("skipped_already_count") or 0}，'
                            f'失败 {result.get("error_count") or 0}'
                        )
                        jobs.update(
                            job_id,
                            status='success',
                            phase='done',
                            result=result,
                            message=done_message,
                            percent=100,
                        )
                if kind in ('scan', 'resolve'):
                    system_log = getattr(self, 'system_log', None)
                    if system_log is not None and hasattr(system_log, 'log'):
                        try:
                            system_log.log(
                                category='archive',
                                stage=f'author_{kind}',
                                message=done_message,
                                level='info',
                                details={
                                    'channel_folder': channel_folder,
                                    'resolve_stats': result.get('resolve_stats'),
                                    'miss_samples': (result.get('miss_samples') or [])[:10],
                                },
                            )
                        except Exception:
                            pass
                elif kind == 'reorganize':
                    system_log = getattr(self, 'system_log', None)
                    if system_log is not None and hasattr(system_log, 'log'):
                        try:
                            system_log.log(
                                category='archive',
                                stage='author_reorganize',
                                message=done_message,
                                level=(
                                    'info'
                                    if not (result.get('error_count') or 0)
                                    and not result.get('stopped')
                                    else 'warning'
                                ),
                                details={
                                    'channel_folder': channel_folder,
                                    'moved_count': result.get('moved_count'),
                                    'error_count': result.get('error_count'),
                                    'skipped_already_count': result.get('skipped_already_count'),
                                    'execute_mode': result.get('execute_mode'),
                                    'stopped': bool(result.get('stopped')),
                                },
                            )
                        except Exception:
                            pass
            except Exception as error:
                message = str(error) or error.__class__.__name__
                jobs.update(
                    job_id,
                    status='failure',
                    phase='error',
                    error=message,
                    message=message,
                )
                diagnostic = getattr(self, 'diagnostic', None)
                if diagnostic is not None:
                    try:
                        diagnostic.exception(f'[ArchiveAuthor] {kind} failed: {message}')
                    except Exception:
                        pass
                system_log = getattr(self, 'system_log', None)
                if system_log is not None and hasattr(system_log, 'log'):
                    try:
                        system_log.log(
                            category='archive',
                            stage=f'author_{kind}',
                            message=message,
                            level='error',
                            details={'channel_folder': channel_folder},
                        )
                    except Exception:
                        pass
            finally:
                jobs.mark_runner_done(job_id)

        threading.Thread(target=runner, name=f'archive-author-{kind}', daemon=True).start()

    def _start_archive_author_job(
            self,
            *,
            kind: str,
            channel_folder: str,
            execute_mode: str = 'all',
            resolve_scope: str = 'all',
    ) -> dict:
        from module.archive_author_jobs import (
            completed_keys_from_job,
            public_job_view,
        )

        channel_folder = str(channel_folder or '').strip()
        if not channel_folder:
            raise ValueError('channel_folder is required')
        jobs = self._archive_author_job_store()
        existing = jobs.find_running(channel_folder=channel_folder)
        if existing:
            # Refresh reconnects to the same background job instead of starting another.
            return public_job_view(existing)

        mode = str(execute_mode or 'all').strip().lower() or 'all'
        if kind == 'reorganize':
            resumable = jobs.find_resumable_reorganize(channel_folder=channel_folder)
            if resumable:
                return self._resume_archive_author_reorganize_job(
                    resumable,
                    execute_mode=mode,
                )

        job = jobs.create(kind=kind, channel_folder=channel_folder)
        job_id = job['id']
        self._spawn_archive_author_runner(
            job_id=job_id,
            kind=kind,
            channel_folder=channel_folder,
            execute_mode=mode,
            resolve_scope=resolve_scope,
            completed_keys=completed_keys_from_job(job),
        )
        return public_job_view(jobs.get(job_id))

    def _resume_archive_author_reorganize_job(
            self,
            job: dict,
            *,
            execute_mode: str = 'all',
    ) -> dict:
        from module.archive_author_jobs import (
            completed_keys_from_job,
            public_job_view,
        )

        jobs = self._archive_author_job_store()
        job_id = str(job.get('id') or '')
        channel_folder = str(job.get('channel_folder') or '').strip()
        if not job_id or not channel_folder:
            raise ValueError('resumable reorganize job is invalid')
        if jobs.is_runner_live(job_id):
            return public_job_view(jobs.get(job_id))
        result = job.get('result') if isinstance(job.get('result'), dict) else {}
        mode = str(
            execute_mode
            or result.get('execute_mode')
            or 'all'
        ).strip().lower() or 'all'
        jobs.update(
            job_id,
            status='running',
            phase='moving',
            error=None,
            message='续跑整理中…',
        )
        self._spawn_archive_author_runner(
            job_id=job_id,
            kind='reorganize',
            channel_folder=channel_folder,
            execute_mode=mode,
            completed_keys=completed_keys_from_job(job),
        )
        return public_job_view(jobs.get(job_id))

    def resume_interrupted_archive_author_jobs(self) -> int:
        """Auto-resume orphaned reorganize jobs after process restart."""
        jobs = self._archive_author_job_store()
        resumed = 0
        for job in jobs.list_orphaned_reorganize():
            try:
                self._resume_archive_author_reorganize_job(
                    job,
                    execute_mode=str(
                        ((job.get('result') or {}) if isinstance(job.get('result'), dict) else {})
                        .get('execute_mode')
                        or 'all'
                    ),
                )
                resumed += 1
            except Exception as error:
                diagnostic = getattr(self, 'diagnostic', None)
                if diagnostic is not None:
                    try:
                        diagnostic.warning(
                            f'[ArchiveAuthor] resume interrupted job failed: {error}'
                        )
                    except Exception:
                        pass
        if resumed:
            diagnostic = getattr(self, 'diagnostic', None)
            if diagnostic is not None:
                try:
                    diagnostic.info(
                        f'Resumed {resumed} interrupted archive author reorganize job(s).'
                    )
                except Exception:
                    pass
        return resumed

    def stop_archive_author_job(self, job_id: str) -> dict:
        from module.archive_author_jobs import public_job_view

        jobs = self._archive_author_job_store()
        job = jobs.get(str(job_id or '').strip())
        if not job:
            raise ValueError('job not found')
        if str(job.get('kind') or '') != 'reorganize':
            raise ValueError('只有整理任务可以停止')
        if str(job.get('status') or '') != 'running':
            return public_job_view(job)
        if not jobs.request_stop(job['id']):
            raise RuntimeError('无法停止该任务')
        return public_job_view(jobs.get(job['id']))

    def scan_archive_author_reorganize(self, payload: dict) -> dict:
        channel_folder = str((payload or {}).get('channel_folder') or '').strip()
        return self._start_archive_author_job(kind='scan', channel_folder=channel_folder)

    def resolve_archive_author_reorganize(self, payload: dict) -> dict:
        channel_folder = str((payload or {}).get('channel_folder') or '').strip()
        scope = str(
            (payload or {}).get('scope')
            or (payload or {}).get('resolve_scope')
            or 'all'
        ).strip().lower() or 'all'
        return self._start_archive_author_job(
            kind='resolve',
            channel_folder=channel_folder,
            resolve_scope=scope,
        )

    def execute_archive_author_reorganize(self, payload: dict) -> dict:
        channel_folder = str((payload or {}).get('channel_folder') or '').strip()
        mode = str((payload or {}).get('mode') or 'all').strip().lower() or 'all'
        return self._start_archive_author_job(
            kind='reorganize',
            channel_folder=channel_folder,
            execute_mode=mode,
        )

    def list_archive_author_plan_moves(self, payload: dict | None = None) -> dict:
        from module.archive_author_jobs import list_job_plan_moves

        data = payload or {}
        job_id = str(data.get('job_id') or '').strip()
        channel_folder = str(data.get('channel_folder') or '').strip()
        bucket = str(data.get('bucket') or '').strip()
        offset = data.get('offset', 0)
        limit = data.get('limit', 50)
        jobs = self._archive_author_job_store()
        job = None
        if job_id:
            job = jobs.get(job_id)
        elif channel_folder:
            # Prefer latest successful scan/resolve for the channel.
            with jobs._lock:
                candidates = [
                    dict(item)
                    for item in jobs._jobs.values()
                    if item.get('channel_folder') == channel_folder
                    and item.get('kind') in ('scan', 'resolve')
                    and item.get('status') == 'success'
                    and isinstance(item.get('result'), dict)
                ]
            if candidates:
                candidates.sort(key=lambda item: float(item.get('updated_at') or 0), reverse=True)
                job = candidates[0]
            else:
                plan = jobs.latest_successful_scan_result(channel_folder)
                if plan:
                    job = {
                        'id': None,
                        'channel_folder': channel_folder,
                        'result': plan,
                    }
        if not job:
            raise ValueError('plan not found')
        return list_job_plan_moves(
            job,
            bucket=bucket,
            offset=offset,
            limit=limit,
        )

    def get_archive_author_job(self, job_id: str) -> dict:
        from module.archive_author_jobs import public_job_view

        job = self._archive_author_job_store().get(str(job_id or '').strip())
        if not job:
            raise ValueError('job not found')
        return public_job_view(job)

    def get_active_archive_author_job(self, channel_folder: str | None = None) -> dict:
        from module.archive_author_jobs import public_job_view

        jobs = self._archive_author_job_store()
        channel = str(channel_folder or '').strip() or None
        job = (
            jobs.find_running(channel_folder=channel)
            or jobs.find_resumable_reorganize(channel_folder=channel)
            or jobs.latest(channel_folder=channel)
        )
        # Cross-device resume: if the selected channel has no match, still surface
        # any live running / resumable job so mobile can attach to a desktop start.
        if channel and (not job or not job.get('id') or str(job.get('status') or '') != 'running'):
            global_running = (
                jobs.find_running(channel_folder=None)
                or jobs.find_resumable_reorganize(channel_folder=None)
            )
            if global_running and global_running.get('id'):
                job = global_running
        view = public_job_view(job)
        return view or {'id': None, 'status': None}

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

    def export_diagnostic_bundle(self, payload: dict | None = None) -> dict:
        """Build a secret-containing zip for local repro; returns path + filename."""
        import asyncio
        from pathlib import Path

        from module import GLOBAL_CONFIG_PATH, LOG_PATH, __version__
        from module.persistence.diagnostic_bundle import (
            DEFAULT_PROBE_LIMIT,
            build_diagnostic_bundle,
            clamp_probe_limit,
            probe_forward_items,
            select_probe_items,
        )

        payload = payload or {}
        if not bool(payload.get('acknowledge_secrets')):
            raise ValueError('acknowledge_secrets_required')

        store = self.transfer_store
        if not store:
            raise ValueError('transfer_store_unavailable')

        task_id = payload.get('task_id')
        if task_id not in (None, ''):
            task_id = int(task_id)
        else:
            task_id = None
        probe_limit = clamp_probe_limit(payload.get('probe_limit', DEFAULT_PROBE_LIMIT))
        run_probe = bool(payload.get('run_probe', True))
        target_chat = str(payload.get('target_chat_id') or 'pikpak_bot')

        probe_items = select_probe_items(store, task_id=task_id, limit=probe_limit)
        if task_id is None and probe_items:
            task_id = int(probe_items[0].get('task_id'))

        probe_results = {
            'probe_limit': probe_limit,
            'run_probe': run_probe,
            'items': probe_items,
            'results': [],
        }
        if run_probe and probe_items:
            client = getattr(getattr(self, 'app', None), 'client', None) or getattr(self, 'last_client', None)
            loop = getattr(self, 'loop', None)
            if client is None or loop is None:
                probe_results['error'] = 'telegram_client_unavailable'
            else:
                future = asyncio.run_coroutine_threadsafe(
                    probe_forward_items(
                        client,
                        probe_items,
                        target_chat_id=target_chat,
                        do_copy=True,
                        do_forward=True,
                    ),
                    loop,
                )
                try:
                    probe_results.update(future.result(timeout=180))
                except Exception as e:
                    probe_results['error'] = f'{type(e).__name__}: {e}'

        app = getattr(self, 'app', None)
        config_path = Path(getattr(app, 'config_path', '') or '')
        session_directory = Path(
            getattr(app, 'work_directory', None)
            or (getattr(app, 'config', {}) or {}).get('session_directory')
            or ''
        )
        temp_directory = Path(
            getattr(app, 'temp_directory', None)
            or (getattr(app, 'config', {}) or {}).get('temp_directory')
            or store.directory
        )
        export_root = Path(temp_directory) / 'diagnostic_exports'
        export_root.mkdir(parents=True, exist_ok=True)

        system_logs_text = self.export_system_logs(today_only=False)
        zip_path = build_diagnostic_bundle(
            work_dir=export_root,
            version=__version__,
            config_yaml_path=config_path if config_path.is_file() else None,
            global_config_path=Path(GLOBAL_CONFIG_PATH),
            session_directory=session_directory,
            transfer_db_path=Path(store.path),
            store=store,
            system_logs_text=system_logs_text,
            app_log_path=Path(LOG_PATH),
            probe_items=probe_items,
            probe_results=probe_results,
            task_id=task_id,
            probe_limit=probe_limit,
            extra_meta={
                'target_chat_id': target_chat,
                'run_probe': run_probe,
            },
        )
        return {
            'path': str(zip_path),
            'filename': zip_path.name,
            'task_id': task_id,
            'probe_item_count': len(probe_items),
            'contains_secrets': True,
        }

    def export_system_logs(
            self,
            category: str | None = None,
            level: str | None = None,
            trace_id: str | None = None,
            watch_id: str | None = None,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ) -> str:
        from module.persistence.system_log import build_system_logs_export_text
        if not self.transfer_store:
            return ''
        return build_system_logs_export_text(
            self.transfer_store,
            category=category,
            level=level,
            trace_id=trace_id,
            watch_id=watch_id,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes
        )

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
            allowed={'notice', 'export_table', 'upload', 'forward_type', 'target_profiles', 'message_filter', 'live_watch', 'deep_link'}
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

    def start_web_ui(self, with_auth_provider: bool = False, defer_runtime_recovery: bool = False) -> None:
        dl = _downloader()
        if dl.PARSE_ARGS.web is None:
            return
        os.makedirs(self.app.temp_directory or self.app.TEMP_DIRECTORY, exist_ok=True)
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
            diagnostic=getattr(self, 'diagnostic', None),
            deep_link_whitelist_getter=lambda: self.gc.get_deep_link_bot_whitelist(),
            setup_status_provider=self.get_setup_status,
            setup_api_saver=self.save_setup_api_credentials,
            setup_rclone_configurer=self.configure_setup_rclone,
            setup_rclone_skipper=self.skip_setup_rclone,
            setup_rclone_tester=self.test_setup_rclone,
            setup_ready_checker=self.is_setup_ready,
        )
        if with_auth_provider:
            from module.web_ui import AuthProvider
            self.web_ui_auth = AuthProvider()
            self.web_ui.set_auth_provider(self.web_ui_auth)
        self.web_ui.start(open_browser=True)
        if not defer_runtime_recovery:
            self.recover_web_runtime()
        console.log(f'WebUI已启动: {self.web_ui.url}', style='#B1DB74')

    def recover_web_runtime(self) -> None:
        """Resume pending web tasks / archives after Setup Ready."""
        if not self.transfer_store:
            return
        for task in self.transfer_store.list_tasks():
            status = task.get('status')
            task_id = int(task.get('id'))
            from module.transfer.watch_inline import is_watch_inline_task
            if is_watch_inline_task(task):
                continue
            if status == TransferStatus.PAUSING:
                has_active_item = any(
                    item.get('status') in (TransferStatus.PENDING, TransferStatus.RUNNING)
                    for item in self.transfer_store.list_items(task_id)
                )
                if has_active_item:
                    self.submit_web_task(task_id)
                else:
                    self.transfer_store.update_task(task_id, status=TransferStatus.PAUSED)
                    self.transfer_store.add_event(
                        task_id,
                        'Transfer task paused after restart with no in-flight item.',
                        level='warning',
                    )
                continue
            if status not in (TransferStatus.PENDING, TransferStatus.RUNNING, TransferStatus.FAILURE):
                continue
            self.submit_web_task(task_id)
        recovered_archives = 0
        progress_tracker = getattr(self, 'progress_tracker', None)
        if progress_tracker is not None:
            recovered_archives = progress_tracker.recover_pending_upload_archives()
        if recovered_archives:
            self.diagnostic.info(f'Recovered {recovered_archives} pending PikPak upload archive job(s).')
        if self.transfer_store:
            reconciled = self.transfer_store.reconcile_active_tasks(force=True)
            if reconciled:
                self.diagnostic.info(f'Reconciled {reconciled} stale transfer task(s).')
        try:
            self._ensure_comment_delay_scheduler()
        except Exception as e:
            log.debug(f'Comment delay scheduler start skipped: {e}')
        try:
            self.resume_interrupted_archive_author_jobs()
        except Exception as e:
            log.debug(f'Archive author reorganize resume skipped: {e}')

    def _archive_settings(self) -> dict:
        profiles = (self.gc.config or {}).get('target_profiles') or {}
        pikpak = profiles.get('pikpak') if isinstance(profiles, dict) else {}
        archive = (pikpak or {}).get('archive') if isinstance(pikpak, dict) else {}
        return archive if isinstance(archive, dict) else {}

    def _set_archive_settings(self, *, enable: Optional[bool] = None, remote: Optional[str] = None) -> None:
        config = deepcopy(self.gc.config)
        profiles = config.setdefault('target_profiles', {})
        if not isinstance(profiles, dict):
            profiles = {}
            config['target_profiles'] = profiles
        pikpak = profiles.setdefault('pikpak', {})
        if not isinstance(pikpak, dict):
            pikpak = {}
            profiles['pikpak'] = pikpak
        archive = pikpak.setdefault('archive', {})
        if not isinstance(archive, dict):
            archive = {}
            pikpak['archive'] = archive
        if enable is not None:
            archive['enable'] = bool(enable)
        if remote is not None:
            archive['remote'] = str(remote).strip().rstrip(':') or 'pikpak'
        self.gc.save_config(config)
        self.gc.target_profiles = config.get('target_profiles', self.gc.target_profiles)

    def is_setup_ready(self) -> bool:
        return bool(self.get_setup_status().get('ready'))

    def get_setup_status(self) -> dict:
        from module.adapters.webui.setup import has_telegram_api_credentials
        coordinator = getattr(self, 'setup_coordinator', None)
        if coordinator is None:
            from module.adapters.webui.setup import SetupCoordinator
            coordinator = SetupCoordinator()
            self.setup_coordinator = coordinator
        api_done = has_telegram_api_credentials(self.app.config)
        telegram_step = 'none'
        telegram_error = None
        telegram_done = False
        auth = getattr(self, 'web_ui_auth', None)
        if auth is not None:
            state = auth.get_state()
            telegram_step = state.get('step') or 'pending'
            telegram_error = state.get('error')
            telegram_done = telegram_step == 'done'
        client = getattr(self.app, 'client', None)
        if client is not None and getattr(client, 'is_connected', False) and getattr(client, 'me', None):
            telegram_done = True
            if telegram_step in ('none', 'pending'):
                telegram_step = 'done'
        archive = self._archive_settings()
        return coordinator.build_status(
            api_done=api_done,
            telegram_done=telegram_done,
            telegram_step=telegram_step,
            telegram_error=telegram_error,
            archive_enable=bool(archive.get('enable')),
            archive_remote=str(archive.get('remote') or 'pikpak'),
        )

    def save_setup_api_credentials(self, payload: dict) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        api_id = payload.get('api_id')
        api_hash = str(payload.get('api_hash') or '').strip()
        try:
            api_id_int = int(api_id)
        except (TypeError, ValueError):
            raise ValueError('api_id 必须是数字。')
        if api_id_int <= 0:
            raise ValueError('api_id 无效。')
        if len(api_hash) < 16:
            raise ValueError('api_hash 无效。')

        user_config = deepcopy(self.app.config)
        user_config['api_id'] = api_id_int
        user_config['api_hash'] = api_hash
        proxy_patch = payload.get('proxy')
        if isinstance(proxy_patch, dict):
            proxy = user_config.get('proxy') if isinstance(user_config.get('proxy'), dict) else {}
            if proxy_patch.get('enable_proxy') is not None:
                proxy['enable_proxy'] = bool(proxy_patch.get('enable_proxy'))
            for key in ('scheme', 'hostname', 'port', 'username', 'password'):
                if key in proxy_patch:
                    proxy[key] = proxy_patch.get(key)
            user_config['proxy'] = proxy
        from module.adapters.webui.setup import apply_web_safe_user_defaults
        user_config = apply_web_safe_user_defaults(user_config)
        user_config = UserConfig.normalize_runtime_numbers(user_config)
        self.app.save_config(user_config)
        self.app.config = user_config
        self.app.refresh_runtime_fields()
        # Signal main loop to build/rebuild client then authorize.
        event = getattr(self, '_api_credentials_event', None)
        if event is not None:
            loop = getattr(self, 'loop', None)
            if loop is not None and loop.is_running():
                loop.call_soon_threadsafe(event.set)
            else:
                event.set()
        coordinator = getattr(self, 'setup_coordinator', None)
        if coordinator is not None:
            coordinator.signal_api_ready()
        return self.get_setup_status()

    def configure_setup_rclone(self, payload: dict) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        coordinator = getattr(self, 'setup_coordinator', None)
        if coordinator is None:
            from module.adapters.webui.setup import SetupCoordinator
            coordinator = SetupCoordinator()
            self.setup_coordinator = coordinator
        remote = str(payload.get('remote') or 'pikpak').strip().rstrip(':') or 'pikpak'
        probe = coordinator.configure_pikpak_remote(
            remote=remote,
            username=str(payload.get('username') or ''),
            password=str(payload.get('password') or ''),
            overwrite=bool(payload.get('overwrite', True)),
        )
        self._set_archive_settings(enable=True, remote=remote)
        coordinator.dismiss_rclone()
        status = self.get_setup_status()
        status['rclone_probe'] = probe
        return status

    def skip_setup_rclone(self, payload: Optional[dict] = None) -> dict:
        raise ValueError('初始化必须配置 rclone（下载回退会直接上传到 My Telegram）。')

    def test_setup_rclone(self, payload: Optional[dict] = None) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        coordinator = getattr(self, 'setup_coordinator', None)
        if coordinator is None:
            from module.adapters.webui.setup import SetupCoordinator
            coordinator = SetupCoordinator()
            self.setup_coordinator = coordinator
        archive = self._archive_settings()
        remote = str(payload.get('remote') or archive.get('remote') or 'pikpak').strip().rstrip(':') or 'pikpak'
        probe = coordinator.probe_rclone(remote)
        if probe.get('ok'):
            self._set_archive_settings(enable=True, remote=remote)
            coordinator.dismiss_rclone()
        return {'probe': probe, 'status': self.get_setup_status()}
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
        selected = set(payload.get('download_type') or [])
        download_type = {
            dtype: dtype in selected
            for dtype in DownloadType()
        }
        # Form selection is full Media Type Override when provided; else inherit global allowlist.
        media_types_override = None
        if payload.get('download_type') is not None:
            from module.core.media_types import DOWNLOAD_MEDIA_TYPES, MEDIA_TYPES
            media_types_override = {t: False for t in MEDIA_TYPES}
            for dtype in DOWNLOAD_MEDIA_TYPES:
                media_types_override[dtype] = bool(download_type.get(dtype))
        keywords = payload.get('keywords') or []
        include_comment = bool(payload.get('include_comment'))
        filter_obj = Filter()
        runtime_filter = self.runtime_message_filter(media_types_override) if hasattr(
            self, 'runtime_message_filter'
        ) else Filter({'media_types': download_type})
        links = []

        def _media_ok(item) -> bool:
            if hasattr(runtime_filter, 'should_pass_media_type'):
                return runtime_filter.should_pass_media_type(item)
            return filter_obj.dtype(item, download_type)

        async for message in self.app.client.get_chat_history(chat_id=chat_id, reverse=True):
            if (
                    filter_obj.date_range(message, start_date, end_date)
                    and _media_ok(message)
                    and filter_obj.keyword_filter(message, keywords)
            ):
                links.append(message.link if getattr(message, 'link', None) else message)
                if include_comment:
                    try:
                        async for comment in iter_discussion_reply_messages(
                                client=self.app.client,
                                chat_id=chat_id,
                                message_id=message.id,
                                include_message=_media_ok,
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
        if not task:
            return False
        from module.transfer.watch_inline import is_watch_inline_task
        if is_watch_inline_task(task):
            return False
        return task.get('status') in (
            TransferStatus.PENDING,
            TransferStatus.RUNNING,
            TransferStatus.PAUSING,
            TransferStatus.FAILURE,
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


    def list_deferred_discussion_captures(self, watch_id: str) -> dict:
        store = self._ensure_transfer_store()
        captures = store.list_deferred_discussion_captures(watch_id=watch_id, limit=500)
        return {'captures': captures, 'total': len(captures)}

    def cancel_deferred_discussion_capture(self, watch_id: str, capture_id: int) -> bool:
        store = self._ensure_transfer_store()
        capture = store.get_deferred_discussion_capture(int(capture_id))
        if not capture or capture.get('watch_id') != watch_id:
            return False
        scheduler = self._ensure_comment_delay_scheduler()
        return scheduler.cancel(int(capture_id))

    def run_deferred_discussion_capture_now(self, watch_id: str, capture_id: int) -> bool:
        store = self._ensure_transfer_store()
        capture = store.get_deferred_discussion_capture(int(capture_id))
        if not capture or capture.get('watch_id') != watch_id:
            return False
        scheduler = self._ensure_comment_delay_scheduler()
        loop = getattr(self, 'loop', None)
        if loop is None:
            return False
        future = asyncio.run_coroutine_threadsafe(scheduler.run_now(int(capture_id)), loop)
        return bool(future.result(timeout=180))

    def retry_deferred_discussion_capture(self, watch_id: str, capture_id: int) -> bool:
        store = self._ensure_transfer_store()
        capture = store.get_deferred_discussion_capture(int(capture_id))
        if not capture or capture.get('watch_id') != watch_id:
            return False
        scheduler = self._ensure_comment_delay_scheduler()
        loop = getattr(self, 'loop', None)
        if loop is None:
            return False
        future = asyncio.run_coroutine_threadsafe(scheduler.retry(int(capture_id)), loop)
        return bool(future.result(timeout=180))


_WEB_UI_DELEGATE_METHODS = (
    'should_continue_web_transfer_task', 'cancel_task_uploads', 'pause_task_uploads', 'cancel_task_downloads', 'submit_web_task',
    'delete_web_task', 'pause_web_task', 'resume_web_task', 'retry_failed_web_task',
    'list_watches', 'create_watch', 'export_forward_watches', 'update_watch', 'delete_watch', 'list_watch_events',
    'list_deferred_discussion_captures', 'cancel_deferred_discussion_capture', 'run_deferred_discussion_capture_now',
    'retry_deferred_discussion_capture',
    'detect_transfer_range', 'statistics', 'export_table', 'create_upload',
    'create_channel_download', 'list_operations', 'scan_media_for_cleanup',
    'cleanup_media_files', 'list_cleanup_logs', 'list_system_logs', 'export_system_logs',
    'export_diagnostic_bundle',
    'list_archive_author_channels', 'scan_archive_author_reorganize',
    'resolve_archive_author_reorganize', 'execute_archive_author_reorganize',
    'list_archive_author_plan_moves',
    'get_archive_author_job',
    'get_active_archive_author_job',
    'stop_archive_author_job',
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
