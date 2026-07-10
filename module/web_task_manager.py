# coding=UTF-8
import asyncio
from typing import Optional, Set

from module.pikpak_integration import PikpakIntegrationManager
from module.source_folders import source_folder_from_link
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
        process_web_task_queue_getter=None,
        cleanup_task_files_getter=None,
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
        self._process_web_task_queue = process_web_task_queue_getter
        self._cleanup_task_files = cleanup_task_files_getter
        self.web_operation_counter: int = 0

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

    def submit_web_task(self, task_id: int) -> None:
        if task_id in self.web_submitted_task_ids:
            return
        self.web_submitted_task_ids.add(task_id)
        try:
            if asyncio.get_running_loop() is self.loop:
                self.web_task_queue.put_nowait(task_id)
                return
        except RuntimeError:
            pass
        self.loop.call_soon_threadsafe(self.web_task_queue.put_nowait, task_id)

    def _enqueue_and_process_web_task(self, task_id: int) -> None:
        self.web_submitted_task_ids.discard(task_id)
        self.web_task_queue.put_nowait(task_id)
        self.start_next_web_transfer_task()

    def discard_web_task_submission(self, task_id: int, cancel_running: bool = True) -> None:
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
        if not self.transfer_store:
            return False
        if self._cleanup_task_files:
            cleanup_result = self._cleanup_task_files(task_id)
            if cleanup_result.get('failed'):
                return False
        deleted = self.transfer_store.delete_task(task_id)
        if deleted:
            self.discard_web_task_submission(task_id, cancel_running=True)
        return deleted

    def pause_web_task(self, task_id: int) -> bool:
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        if not task:
            return False
        if task.get('status') not in (TransferStatus.PENDING, TransferStatus.RUNNING):
            return False
        self.transfer_store.update_task(task_id, status=TransferStatus.PAUSED)
        self.transfer_store.add_event(task_id, 'Transfer task paused.', level='warning')
        self.discard_web_task_submission(task_id, cancel_running=True)
        return True

    def resume_web_task(self, task_id: int) -> bool:
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        if not task or task.get('status') != TransferStatus.PAUSED:
            return False
        self.transfer_store.update_task(task_id, status=TransferStatus.PENDING)
        self.transfer_store.add_event(task_id, 'Transfer task resumed.')
        self.loop.call_soon_threadsafe(
            lambda tid=task_id: self._enqueue_and_process_web_task(tid)
        )
        return True

    def retry_failed_web_task(self, task_id: int) -> int:
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
            self.loop.call_soon_threadsafe(
                lambda tid=task_id: self._enqueue_and_process_web_task(tid)
            )
        return reset_items

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
                or source_folder_from_link(item.get('source_link') or task.get('source_link'))
            ),
            file_name=item.get('file_name'),
            file_size=item.get('file_size'),
            transferred_at=PikpakIntegrationManager.transfer_item_archive_timestamp(item),
            match_original_name=PikpakIntegrationManager.transfer_item_archive_match_original_name(item)
        )
        if not bool(getattr(result, 'ok', False)):
            return False
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
        self.loop.call_soon_threadsafe(self.web_operation_queue.put_nowait, operation_id)
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
                runner = self.loop.create_task(self._process_web_transfer_task(task_id))
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
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        return bool(
            task
            and task.get('status') in (TransferStatus.PENDING, TransferStatus.RUNNING, TransferStatus.FAILURE)
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
            self.loop.create_task(self._process_web_task_queue())
