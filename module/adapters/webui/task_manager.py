# coding=UTF-8
import asyncio
import threading
from typing import Callable, Optional, Set

from module.pikpak_integration import PikpakIntegrationManager
from module.source_folders import archive_source_folder
from module.transfer_store import TransferStore, TransferStatus


class WebUITaskManager:
    def __init__(
        self,
        transfer_store_getter,
        diagnostic,
        loop_getter,
        web_task_queue,
        web_submitted_task_ids: Set[int],
        web_running_task_getter,
        web_running_task_setter,
        web_running_task_id_getter,
        web_running_task_id_setter,
        web_operation_queue,
        web_operations: dict,
        watch_manager_getter=None,
        pikpak_manager_getter=None,
        progress_tracker_getter=None,
        listener_restart_callback=None,
        list_watches_getter=None,
        persisted_watches_getter=None,
        set_live_watch_status_getter=None,
        watch_payload_from_record_getter=None,
        is_web_transfer_task_schedulable_kwargs=None,
        archive_pikpak_item_getter=None,
        refresh_transfer_task_counts_getter=None,
        process_web_transfer_task_getter=None,
        retry_watch_inline_task_getter=None,
        process_web_task_queue_getter=None,
        cleanup_task_files_getter=None,
        cancel_task_uploads_getter=None,
        pause_task_uploads_getter=None,
        cancel_task_downloads_getter=None,
        should_continue_web_transfer_task_getter=None,
        uploader_getter=None,
    ):
        self._transfer_store = transfer_store_getter
        self.diagnostic = diagnostic
        self._loop = loop_getter
        self.web_task_queue = web_task_queue
        self.web_submitted_task_ids = web_submitted_task_ids
        self._get_web_running_task = web_running_task_getter
        self._set_web_running_task = web_running_task_setter
        self._get_web_running_task_id = web_running_task_id_getter
        self._set_web_running_task_id = web_running_task_id_setter
        self.web_operation_queue = web_operation_queue
        self.web_operations = web_operations
        self._watch_manager = watch_manager_getter
        self._pikpak_manager = pikpak_manager_getter
        self._progress_tracker = progress_tracker_getter
        self._listener_restart = listener_restart_callback
        self._list_watches = list_watches_getter
        self._persisted_watches = persisted_watches_getter
        self._set_live_watch_status = set_live_watch_status_getter
        self._watch_payload_from_record = watch_payload_from_record_getter
        self._is_schedulable_kwargs = is_web_transfer_task_schedulable_kwargs or {}
        self._archive_pikpak_item = archive_pikpak_item_getter
        self._refresh_transfer_task_counts = refresh_transfer_task_counts_getter
        self._process_web_transfer_task = process_web_transfer_task_getter
        self._retry_watch_inline_task = retry_watch_inline_task_getter
        self._process_web_task_queue = process_web_task_queue_getter
        self._cleanup_task_files = cleanup_task_files_getter
        self._cancel_task_uploads = cancel_task_uploads_getter
        self._pause_task_uploads = pause_task_uploads_getter
        self._cancel_task_downloads = cancel_task_downloads_getter
        self._should_continue_web_transfer_task = should_continue_web_transfer_task_getter
        self._uploader = uploader_getter
        self._transfer_download_tasks: dict = {}
        self.web_operation_counter: int = 0
        self._delete_wait_timeout_seconds: float = 10.0
        self._loop_callback_timeout_seconds: float = 15.0

    def _invoke_on_loop(self, callback: Callable[[], None]) -> None:
        """Schedule ``callback`` on the WebUI event loop, or run inline if unavailable."""
        loop = self.loop
        if loop and hasattr(loop, 'call_soon_threadsafe'):
            try:
                if asyncio.get_running_loop() is loop:
                    callback()
                    return
            except RuntimeError:
                pass
            if loop.is_running():
                loop.call_soon_threadsafe(callback)
                return
        callback()

    def _run_on_web_loop(
            self,
            callback: Callable[[], None],
            timeout: Optional[float] = None,
            raise_on_timeout: bool = True,
    ) -> bool:
        loop = self.loop
        try:
            if loop and asyncio.get_running_loop() is loop:
                callback()
                return True
        except RuntimeError:
            pass
        if not loop or not loop.is_running():
            callback()
            return True
        done = threading.Event()

        def wrapper() -> None:
            try:
                callback()
            finally:
                done.set()

        loop.call_soon_threadsafe(wrapper)
        if not done.wait(timeout=timeout or self._loop_callback_timeout_seconds):
            if raise_on_timeout:
                raise TimeoutError('Timed out waiting for WebUI task queue callback.')
            return False
        return True

    def _clear_running_transfer_task(self, task_id: int) -> None:
        def clear() -> None:
            if self.web_running_task_id != task_id:
                return
            running_task = self.web_running_task
            if running_task and running_task.done():
                self.finish_web_transfer_task(task_id, running_task)
                return
            if running_task and not running_task.done():
                try:
                    running_task.cancel()
                except Exception:
                    pass
            self.web_running_task = None
            self.web_running_task_id = None
            self.start_next_web_transfer_task()

        self._run_on_web_loop(clear, raise_on_timeout=False)

    def _kick_web_task_queue(self) -> None:
        def kick() -> None:
            if self.web_running_task and self.web_running_task.done():
                self.finish_web_transfer_task(self.web_running_task_id, self.web_running_task)
            self.start_next_web_transfer_task()

        self._invoke_on_loop(kick)

    @property
    def transfer_store(self):
        return self._transfer_store()

    @property
    def loop(self):
        return self._loop()

    @property
    def web_running_task(self):
        return self._get_web_running_task()

    @web_running_task.setter
    def web_running_task(self, value):
        self._set_web_running_task(value)

    @property
    def web_running_task_id(self):
        return self._get_web_running_task_id()

    @web_running_task_id.setter
    def web_running_task_id(self, value):
        self._set_web_running_task_id(value)

    @property
    def watch_manager(self):
        return self._watch_manager() if self._watch_manager else None

    def _is_task_id_in_web_queue(self, task_id: int) -> bool:
        queued_task_ids = []
        while True:
            try:
                queued_task_ids.append(int(self.web_task_queue.get_nowait()))
            except asyncio.QueueEmpty:
                break
            self.web_task_queue.task_done()
        for queued_task_id in queued_task_ids:
            self.web_task_queue.put_nowait(queued_task_id)
        return task_id in queued_task_ids

    def _is_task_actively_scheduled(self, task_id: int) -> bool:
        if (
                self.web_running_task_id == task_id
                and self.web_running_task
                and not self.web_running_task.done()
        ):
            return True
        return self._is_task_id_in_web_queue(task_id)

    def submit_web_task(self, task_id: int) -> None:
        if task_id in self.web_submitted_task_ids:
            if self._is_task_actively_scheduled(task_id):
                return
            self.web_submitted_task_ids.discard(task_id)
        self.web_submitted_task_ids.add(task_id)

        def enqueue_and_start() -> None:
            self.web_task_queue.put_nowait(task_id)
            self.start_next_web_transfer_task()

        self._invoke_on_loop(enqueue_and_start)

    def _enqueue_and_process_web_task(self, task_id: int) -> None:
        self.web_submitted_task_ids.discard(task_id)
        self.web_task_queue.put_nowait(task_id)
        self.start_next_web_transfer_task()

    def discard_web_task_submission(
            self,
            task_id: int,
            cancel_running: bool = True,
            wait: bool = False
    ) -> None:
        def cleanup() -> None:
            self.web_submitted_task_ids.discard(task_id)
            self.drop_web_task_from_queue(task_id)
            cancelled_running = False
            if cancel_running and self.web_running_task_id == task_id:
                running_task = self.web_running_task
                if running_task and not running_task.done():
                    running_task.cancel()
                    cancelled_running = True
                elif running_task and running_task.done():
                    self.finish_web_transfer_task(task_id, running_task)
                    return
                else:
                    self.web_running_task = None
                    self.web_running_task_id = None
            # Let the cancelled task's done_callback start the next runner so we
            # never overlap a dying process_task with a newly started one.
            if not cancelled_running:
                self.start_next_web_transfer_task()

        loop = self.loop
        try:
            if loop and asyncio.get_running_loop() is loop:
                cleanup()
                return
        except RuntimeError:
            pass
        if wait and loop and loop.is_running():
            synced = self._run_on_web_loop(cleanup, raise_on_timeout=False)
            if not synced and hasattr(loop, 'call_soon_threadsafe'):
                loop.call_soon_threadsafe(cleanup)
            return
        self._invoke_on_loop(cleanup)

    def drop_web_task_from_queue(self, task_id: int) -> None:
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

    def should_continue_web_transfer_task(self, task_id: int) -> bool:
        checker = self._should_continue_web_transfer_task
        if callable(checker):
            return bool(checker(task_id))
        if not self.transfer_store or not task_id:
            return False
        task = self.transfer_store.get_task(int(task_id))
        # PAUSING keeps in-flight work; only PAUSED aborts mid-item.
        return bool(task and task.get('status') != TransferStatus.PAUSED)

    def should_continue_web_transfer_item(self, item_id: int) -> bool:
        """False once reconcile/UI marked the item failed — abort in-flight IO cooperatively."""
        if not self.transfer_store or not item_id:
            return False
        item = self.transfer_store.get_item(int(item_id)) or {}
        return item.get('status') in (TransferStatus.PENDING, TransferStatus.RUNNING)

    def should_start_next_web_transfer_item(self, task_id: int) -> bool:
        """Whether a new Transfer Item may start. False while pausing/paused."""
        if not self.transfer_store or not task_id:
            return False
        task = self.transfer_store.get_task(int(task_id))
        if not task:
            return False
        return task.get('status') not in (TransferStatus.PAUSING, TransferStatus.PAUSED)

    def _transfer_download_registry(self) -> dict:
        return self._transfer_download_tasks

    def _register_transfer_download_task(
            self,
            with_upload: Optional[dict],
            download_task: asyncio.Task,
    ) -> None:
        if not isinstance(with_upload, dict):
            return
        raw_task_id = with_upload.get('task_id')
        if raw_task_id is None or download_task is None:
            return
        task_id = int(raw_task_id)
        self._transfer_download_registry().setdefault(task_id, set()).add(download_task)

    def _unregister_transfer_download_task(
            self,
            with_upload: Optional[dict],
            download_task: asyncio.Task,
    ) -> None:
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
        override = self._cancel_task_downloads
        if callable(override):
            return int(override(task_id) or 0)
        registry = self._transfer_download_registry()
        tasks = list(registry.pop(int(task_id), set()))
        cancelled = 0
        for download_task in tasks:
            if download_task and not download_task.done():
                download_task.cancel()
                cancelled += 1
        return cancelled

    def cancel_task_uploads(self, task_id: int) -> int:
        override = self._cancel_task_uploads
        if callable(override):
            return int(override(task_id) or 0)
        uploader = self._uploader() if callable(self._uploader) else None
        if uploader and hasattr(uploader, 'cancel_uploads_for_task'):
            return int(uploader.cancel_uploads_for_task(task_id) or 0)
        return 0

    def pause_task_uploads(self, task_id: int) -> int:
        override = self._pause_task_uploads
        if callable(override):
            return int(override(task_id) or 0)
        uploader = self._uploader() if callable(self._uploader) else None
        if uploader and hasattr(uploader, 'pause_uploads_for_task'):
            return int(uploader.pause_uploads_for_task(task_id) or 0)
        return 0

    def has_active_transfer_io(self, task_id: int) -> bool:
        for download_task in self._transfer_download_registry().get(int(task_id), set()):
            if download_task is not None and not download_task.done():
                return True
        uploader = self._uploader() if callable(self._uploader) else None
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

    def _has_active_web_transfer_runner(self, task_id: int) -> bool:
        return (
            self.web_running_task_id == task_id
            and self.web_running_task is not None
            and not self.web_running_task.done()
        )

    def _wait_for_running_transfer_task_stop(self, task_id: int) -> None:
        running_task_id = self.web_running_task_id
        running_task = self.web_running_task
        if running_task_id != task_id or not running_task or running_task.done():
            return
        if not self.loop or not self.loop.is_running():
            return

        async def _wait_for_stop() -> None:
            try:
                await asyncio.wait_for(running_task, timeout=self._delete_wait_timeout_seconds)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass

        try:
            future = asyncio.run_coroutine_threadsafe(_wait_for_stop(), self.loop)
            future.result(timeout=self._delete_wait_timeout_seconds + 2)
        except Exception:
            pass

    def delete_web_task(self, task_id: int) -> bool:
        if not self.transfer_store:
            return False
        if not self.transfer_store.get_task(task_id):
            return False
        self.discard_web_task_submission(task_id, cancel_running=True, wait=True)
        self.cancel_task_uploads(task_id)
        self.cancel_task_downloads(task_id)
        self._wait_for_running_transfer_task_stop(task_id)
        self._clear_running_transfer_task(task_id)
        if self._cleanup_task_files:
            cleanup_result = self._cleanup_task_files(task_id)
            if cleanup_result.get('failed'):
                self.submit_web_task(task_id)
                return False
        deleted = self.transfer_store.delete_task(task_id)
        if deleted:
            self._kick_web_task_queue()
        return deleted

    def pause_web_task(self, task_id: int) -> bool:
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        if not task:
            return False
        if task.get('status') not in (TransferStatus.PENDING, TransferStatus.RUNNING):
            return False
        if self._has_active_web_transfer_runner(task_id):
            self.transfer_store.update_task(task_id, status=TransferStatus.PAUSING)
            self.transfer_store.add_event(task_id, 'Transfer task pause requested.', level='warning')
            return True
        self.transfer_store.update_task(task_id, status=TransferStatus.PAUSED)
        self.transfer_store.add_event(task_id, 'Transfer task paused.', level='warning')
        self.discard_web_task_submission(task_id, cancel_running=True, wait=True)
        self._kick_web_task_queue()
        return True

    def resume_web_task(self, task_id: int) -> bool:
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

        def enqueue() -> None:
            self._enqueue_and_process_web_task(task_id)

        self._invoke_on_loop(enqueue)
        return True

    def retry_failed_web_task(self, task_id: int, submit_fn=None) -> int:
        if not self.transfer_store:
            return 0
        task = self.transfer_store.get_task(task_id)
        if not task:
            return 0
        from module.transfer.watch_inline import is_watch_inline_task
        watch_inline = is_watch_inline_task(task)
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
        if watch_inline:
            empty_failure = (
                task.get('status') == TransferStatus.FAILURE
                and not self.transfer_store.list_items(task_id)
            )
            if empty_failure:
                self.transfer_store.update_task(
                    task_id,
                    status=TransferStatus.RUNNING,
                    error_message='',
                    finished=False,
                    assignment_completed=True,
                )
                self.transfer_store.add_event(task_id, 'Watch inline empty failure retry requested.')
                self._schedule_watch_inline_retry(task_id)
                return 1
            if reset_items:
                self._schedule_watch_inline_retry(task_id)
            return reset_items
        if reset_items:
            if callable(submit_fn):
                submit_fn(task_id)
            else:
                self._invoke_on_loop(
                    lambda tid=task_id: self._enqueue_and_process_web_task(tid)
                )
        return reset_items

    def _schedule_watch_inline_retry(self, task_id: int) -> None:
        retry_runner = self._retry_watch_inline_task
        if not callable(retry_runner):
            return

        def launch() -> None:
            loop = self.loop
            if loop is None:
                return
            loop.create_task(retry_runner(task_id))

        self._invoke_on_loop(launch)

    def recover_pikpak_failed_item_before_retry(self, task: dict, item: dict) -> bool:
        if not PikpakIntegrationManager.is_pikpak_target(item.get('target_link') or task.get('target_link'), task.get('target_profile')):
            return False
        if not PikpakIntegrationManager.is_pikpak_archive_recoverable_item(item):
            return False
        if not item.get('file_name') and item.get('file_size') is None:
            return False
        item_id = int(item.get('id'))
        task_id = int(task.get('id'))
        result = self._archive_pikpak_item(
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
            transferred_at=PikpakIntegrationManager.transfer_item_archive_timestamp(item),
            match_original_name=PikpakIntegrationManager.transfer_item_archive_match_original_name(item)
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
        self._refresh_transfer_task_counts(task_id)
        return True

    def next_web_operation_id(self, operation_type: str) -> str:
        self.web_operation_counter += 1
        return f'{operation_type}-{self.web_operation_counter}'

    def submit_web_operation(self, operation_type: str, payload: dict) -> dict:
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
        self._invoke_on_loop(
            lambda: self.web_operation_queue.put_nowait(operation_id)
        )
        return operation

    def skip_missing_web_transfer_range_message(
            self,
            task: dict,
            origin_chat_id,
            source_link: str,
            message_id: int
    ) -> None:
        task_id = int(task.get('id'))
        message_link = f'{source_link.rstrip("/")}/{message_id}'
        item_id = self.transfer_store.add_item(
            task_id=task_id,
            source_chat_id=origin_chat_id,
            source_message_id=message_id,
            range_message_id=message_id,
            source_link=message_link,
            target_link=task.get('target_link'),
            phase='skipped',
            status=TransferStatus.SKIPPED,
            error_message=f'Source message not found: {message_id}.'
        )
        self.transfer_store.add_event(
            task_id,
            f'Source message not found, skipped: {message_id}.',
            level='warning',
            item_id=item_id
        )
        self._refresh_transfer_task_counts(task_id)

    def mark_pending_watch(self, payload: dict, status: str, error_message: str = None) -> None:
        self.watch_manager.mark_pending_watch(payload, status, error_message)

    def start_next_web_transfer_task(self) -> None:
        if self.web_running_task and not self.web_running_task.done():
            running_task_id = self.web_running_task_id
            if running_task_id and not self._should_keep_web_transfer_runner(running_task_id):
                try:
                    self.web_running_task.cancel()
                except Exception:
                    pass
                # Keep web_running_task until done_callback clears it and starts next.
                return
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
                loop = self.loop
                if loop is None:
                    self.web_task_queue.put_nowait(task_id)
                    return
                runner = loop.create_task(self._process_web_transfer_task(task_id))
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

    def _should_keep_web_transfer_runner(self, task_id: int) -> bool:
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        if not task:
            return False
        return task.get('status') in (
            TransferStatus.PENDING,
            TransferStatus.RUNNING,
            TransferStatus.PAUSING,
            TransferStatus.FAILURE,
        )

    def is_web_transfer_task_schedulable(self, task_id: int) -> bool:
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
        if task_id is not None:
            self.web_submitted_task_ids.discard(task_id)
        if self.web_running_task is completed_task:
            self.web_running_task = None
            self.web_running_task_id = None
        if not completed_task.cancelled():
            error = completed_task.exception()
            if error:
                import logging
                log = logging.getLogger(__name__)
                log.error(
                    f'WebUI转存任务执行失败:{task_id},原因:"{error}"',
                    exc_info=(type(error), error, error.__traceback__)
                )
        if not self.web_task_queue.empty():
            loop = self.loop
            if loop is not None:
                loop.create_task(self._process_web_task_queue())
