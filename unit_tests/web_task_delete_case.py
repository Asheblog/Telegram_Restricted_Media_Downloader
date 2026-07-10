# coding=UTF-8
import asyncio
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

import sys


def import_with_clean_argv(importer):
    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0]]
        return importer()
    finally:
        sys.argv = original_argv


from module.transfer_store import TransferStore, TransferStatus

UploadStatus = import_with_clean_argv(lambda: __import__('module.enums', fromlist=['UploadStatus']).UploadStatus)
UploadTask = import_with_clean_argv(lambda: __import__('module.task', fromlist=['UploadTask']).UploadTask)
TelegramUploader = import_with_clean_argv(lambda: __import__('module.uploader', fromlist=['TelegramUploader']).TelegramUploader)


def import_downloader_class():
    return import_with_clean_argv(lambda: __import__('module.downloader', fromlist=['TelegramRestrictedMediaDownloader']).TelegramRestrictedMediaDownloader)


class WebTaskDeleteCase(unittest.TestCase):
    def test_should_continue_web_transfer_task_false_when_task_deleted(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            downloader = object.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = store
            self.assertTrue(downloader.should_continue_web_transfer_task(task_id))
            store.delete_task(task_id)
            self.assertFalse(downloader.should_continue_web_transfer_task(task_id))

    def test_should_continue_web_transfer_task_false_when_paused(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.PAUSED)
            downloader = object.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = store
            self.assertFalse(downloader.should_continue_web_transfer_task(task_id))

    def test_process_web_transfer_task_stops_when_task_deleted_mid_run(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()

        async def run_case():
            with tempfile.TemporaryDirectory() as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task(
                    'https://t.me/source/1',
                    'https://t.me/pikpak_bot',
                    start_id=1,
                    end_id=3,
                )
                store.update_task(task_id, status=TransferStatus.RUNNING)
                downloader = object.__new__(TelegramRestrictedMediaDownloader)
                downloader.transfer_store = store
                downloader.loop = asyncio.get_running_loop()
                downloader.app = SimpleNamespace(client=SimpleNamespace(name='test'))
                downloader.uploader = SimpleNamespace()
                processed_message_ids = []

                async def fake_transfer_message_to_web_target(**kwargs):
                    processed_message_ids.append(kwargs['message'].id)
                    if len(processed_message_ids) == 1:
                        store.delete_task(task_id)
                    return False

                downloader.transfer_message_to_web_target = fake_transfer_message_to_web_target
                downloader.wait_between_transfer_messages = AsyncMock()
                downloader.get_web_transfer_range_message = AsyncMock(
                    side_effect=lambda chat_id, message_id, tid: SimpleNamespace(id=message_id)
                )
                downloader.skip_missing_web_transfer_range_message = lambda **kwargs: None
                downloader.transfer_web_discussion_replies_to_target = AsyncMock(return_value=(0, 0))
                downloader.refresh_transfer_task_counts = lambda tid: None

                with patch('module.downloader.parse_link', new=AsyncMock(return_value={'chat_id': 1})):
                    await downloader.process_web_transfer_task(task_id)

                self.assertEqual([1], processed_message_ids)

        asyncio.run(run_case())

    def test_delete_web_task_cancels_running_worker_before_file_cleanup(self):
        MediaManager = import_with_clean_argv(
            lambda: __import__('module.media_manager', fromlist=['MediaManager']).MediaManager
        )

        TelegramRestrictedMediaDownloader = import_downloader_class()

        async def run_case():
            with tempfile.TemporaryDirectory() as directory:
                final_path = os.path.join(directory, 'delete-me.bin')
                with open(final_path, 'wb') as file:
                    file.write(b'12345')
                store = TransferStore(directory=directory)
                task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
                store.add_item(
                    task_id=task_id,
                    source_chat_id='source',
                    source_message_id=1,
                    source_link='https://t.me/source/1',
                    target_link='https://t.me/pikpak_bot',
                    file_name='delete-me.bin',
                    local_path=final_path,
                    temp_path=f'{final_path}.cache',
                    phase='downloading',
                    status='running',
                )
                store.update_task(task_id, status=TransferStatus.RUNNING)

                downloader = object.__new__(TelegramRestrictedMediaDownloader)
                downloader.transfer_store = store
                downloader.media_manager = MediaManager(store, save_directory=directory, temp_directory=directory)
                downloader.web_submitted_task_ids = set()
                downloader.web_task_queue = asyncio.Queue()
                downloader.web_running_task = None
                downloader.web_running_task_id = None
                downloader.loop = asyncio.get_running_loop()
                downloader.uploader = None
                worker_cancelled = asyncio.Event()

                async def fake_process_web_transfer_task(running_id):
                    try:
                        await asyncio.sleep(3600)
                    except asyncio.CancelledError:
                        worker_cancelled.set()
                        raise

                downloader.process_web_transfer_task = fake_process_web_transfer_task
                downloader.web_task_manager = None
                downloader.web_running_task = asyncio.create_task(fake_process_web_transfer_task(task_id))
                downloader.web_running_task_id = task_id

                cleanup_started = False
                original_cleanup = downloader.media_manager.cleanup_task_files

                def fake_cleanup(task_id_to_clean):
                    nonlocal cleanup_started
                    cleanup_started = True
                    self.assertTrue(worker_cancelled.is_set())
                    return original_cleanup(task_id_to_clean)

                with patch.object(downloader, '_ensure_media_manager', return_value=downloader.media_manager):
                    with patch.object(downloader.media_manager, 'cleanup_task_files', side_effect=fake_cleanup) as cleanup_mock:
                        deleted = await asyncio.get_running_loop().run_in_executor(
                            None,
                            downloader.delete_web_task,
                            task_id,
                        )
                        self.assertTrue(deleted)

                cleanup_mock.assert_called_once_with(task_id)
                self.assertTrue(cleanup_started)
                self.assertTrue(worker_cancelled.is_set())
                self.assertIsNone(store.get_task(task_id))
                self.assertFalse(os.path.exists(final_path))

                if downloader.web_running_task and not downloader.web_running_task.done():
                    downloader.web_running_task.cancel()
                    await asyncio.gather(downloader.web_running_task, return_exceptions=True)

        asyncio.run(run_case())

    def test_should_continue_web_transfer_task_no_recursion_with_task_manager(self):
        from module.web_task_manager import WebUITaskManager

        TelegramRestrictedMediaDownloader = import_downloader_class()
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            downloader = object.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = store
            downloader.web_task_manager = WebUITaskManager(
                transfer_store_getter=lambda: store,
                diagnostic=SimpleNamespace(),
                loop_getter=lambda: asyncio.new_event_loop(),
                web_task_queue=asyncio.Queue(),
                web_submitted_task_ids=set(),
                web_running_task_getter=lambda: None,
                web_running_task_setter=lambda _value: None,
                web_running_task_id_getter=lambda: None,
                web_running_task_id_setter=lambda _value: None,
                web_operation_queue=asyncio.Queue(),
                web_operations={},
                should_continue_web_transfer_task_getter=None,
            )
            self.assertTrue(downloader.should_continue_web_transfer_task(task_id))
            store.update_task(task_id, status=TransferStatus.PAUSED)
            self.assertFalse(downloader.should_continue_web_transfer_task(task_id))

    def test_cancel_uploads_for_task_drops_queue_and_marks_active_uploads(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'queued.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')
            uploader = object.__new__(TelegramUploader)
            uploader.upload_queue = asyncio.Queue()
            uploader.loop = asyncio.get_event_loop()
            uploader.upload_context = SimpleNamespace(
                should_continue_web_transfer_task=lambda task_id: False,
                diagnostic=SimpleNamespace(
                    info=lambda *args, **kwargs: None,
                    warning=lambda *args, **kwargs: None,
                    error=lambda *args, **kwargs: None,
                    console_log=lambda *args, **kwargs: None,
                ),
            )
            uploader.notify_transfer_status = lambda upload_task: None

            queued_task = UploadTask(
                chat_id=1,
                file_path=file_path,
                file_id=1,
                file_size=5,
                file_part=[],
                status=UploadStatus.PENDING,
                transfer_meta={'task_id': 7},
            )
            active_task = UploadTask(
                chat_id=1,
                file_path=file_path,
                file_id=2,
                file_size=5,
                file_part=[],
                status=UploadStatus.UPLOADING,
                transfer_meta={'task_id': 7},
            )
            other_task = UploadTask(
                chat_id=1,
                file_path=file_path,
                file_id=3,
                file_size=5,
                file_part=[],
                status=UploadStatus.PENDING,
                transfer_meta={'task_id': 9},
            )
            uploader.upload_queue.put_nowait((None, queued_task))
            uploader.upload_queue.put_nowait((None, other_task))

            cancelled = uploader.cancel_uploads_for_task(7)

            self.assertEqual(2, cancelled)
            self.assertEqual(UploadStatus.FAILURE, queued_task.status)
            self.assertEqual(UploadStatus.FAILURE, active_task.status)
            self.assertEqual(UploadStatus.PENDING, other_task.status)
            self.assertEqual(1, uploader.upload_queue.qsize())
            remaining_media, remaining_task = uploader.upload_queue.get_nowait()
            self.assertEqual(9, remaining_task.transfer_meta['task_id'])


if __name__ == '__main__':
    unittest.main()
