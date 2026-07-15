# coding=UTF-8
import asyncio
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.adapters.webui.task_manager import WebUITaskManager
from module.adapters.webui.view_model import WebUiViewModel
from module.transfer.runner import WebTransferRunner
from module.transfer_store import TransferStore, TransferStatus


def import_downloader_class():
    return __import__('module.downloader', fromlist=['TelegramRestrictedMediaDownloader']).TelegramRestrictedMediaDownloader


class WebTaskDeferredPauseCase(unittest.TestCase):
    def test_pause_without_runner_goes_paused_immediately(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            downloader = object.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = store
            downloader.web_task_manager = None
            downloader.web_running_task_id = None
            downloader.web_running_task = None
            discarded = []
            downloader.discard_web_task_submission = (
                lambda tid, cancel_running=False, wait=False: discarded.append((tid, cancel_running))
            )

            self.assertTrue(
                TelegramRestrictedMediaDownloader.pause_web_task.__get__(
                    downloader,
                    TelegramRestrictedMediaDownloader,
                )(task_id)
            )
            self.assertEqual(TransferStatus.PAUSED, store.get_task(task_id)['status'])
            self.assertEqual([(task_id, True)], discarded)

    def test_pause_with_active_runner_sets_pausing_without_cancel(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.RUNNING)
            running = SimpleNamespace(done=lambda: False, cancel=lambda: None)
            cancel_calls = []
            pause_upload_calls = []
            discarded = []

            manager = WebUITaskManager(
                transfer_store_getter=lambda: store,
                diagnostic=SimpleNamespace(),
                loop_getter=lambda: None,
                web_task_queue=asyncio.Queue(),
                web_submitted_task_ids={task_id},
                web_running_task_getter=lambda: running,
                web_running_task_setter=lambda value: None,
                web_running_task_id_getter=lambda: task_id,
                web_running_task_id_setter=lambda value: None,
                web_operation_queue=asyncio.Queue(),
                web_operations={},
                cancel_task_downloads_getter=lambda tid: cancel_calls.append(tid) or 0,
                pause_task_uploads_getter=lambda tid: pause_upload_calls.append(tid) or 0,
            )
            manager.discard_web_task_submission = (
                lambda tid, cancel_running=False, wait=False: discarded.append((tid, cancel_running))
            )

            self.assertTrue(manager.pause_web_task(task_id))
            self.assertEqual(TransferStatus.PAUSING, store.get_task(task_id)['status'])
            self.assertEqual([], cancel_calls)
            self.assertEqual([], pause_upload_calls)
            self.assertEqual([], discarded)
            events = [event['message'] for event in store.list_events(task_id)]
            self.assertIn('Transfer task pause requested.', events)

    def test_should_continue_while_pausing(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.PAUSING)
            manager = WebUITaskManager(
                transfer_store_getter=lambda: store,
                diagnostic=SimpleNamespace(),
                loop_getter=lambda: None,
                web_task_queue=asyncio.Queue(),
                web_submitted_task_ids=set(),
                web_running_task_getter=lambda: None,
                web_running_task_setter=lambda value: None,
                web_running_task_id_getter=lambda: None,
                web_running_task_id_setter=lambda value: None,
                web_operation_queue=asyncio.Queue(),
                web_operations={},
            )
            self.assertTrue(manager.should_continue_web_transfer_task(task_id))
            store.update_task(task_id, status=TransferStatus.PAUSED)
            self.assertFalse(manager.should_continue_web_transfer_task(task_id))

    def test_cancel_pause_returns_to_running(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.PAUSING)
            manager = WebUITaskManager(
                transfer_store_getter=lambda: store,
                diagnostic=SimpleNamespace(),
                loop_getter=lambda: None,
                web_task_queue=asyncio.Queue(),
                web_submitted_task_ids=set(),
                web_running_task_getter=lambda: None,
                web_running_task_setter=lambda value: None,
                web_running_task_id_getter=lambda: None,
                web_running_task_id_setter=lambda value: None,
                web_operation_queue=asyncio.Queue(),
                web_operations={},
            )
            self.assertTrue(manager.resume_web_task(task_id))
            self.assertEqual(TransferStatus.RUNNING, store.get_task(task_id)['status'])

    def test_view_model_capabilities_for_pausing(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.PAUSING)
            task = WebUiViewModel(store).task_model(store.get_task(task_id))
            self.assertFalse(task['can_pause'])
            self.assertTrue(task['can_resume'])
            self.assertFalse(task['can_delete'])
            self.assertEqual(TransferStatus.PAUSING, task['status'])

    def test_honor_pause_request_finalizes_pausing(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.PAUSING)
            host = SimpleNamespace(transfer_store=store, web_task_manager=None)
            runner = WebTransferRunner(host)
            self.assertTrue(runner.honor_web_task_pause_request(task_id, before='7'))
            self.assertEqual(TransferStatus.PAUSED, store.get_task(task_id)['status'])
            messages = [event['message'] for event in store.list_events(task_id)]
            self.assertIn('Transfer task paused before message: 7.', messages)

    def test_refresh_task_counts_preserves_pausing(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.PAUSING)
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            self.assertEqual(TransferStatus.PAUSING, store.get_task(task_id)['status'])

    def test_recover_pausing_without_active_item_converges_to_paused(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.PAUSING)
            downloader = object.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = store
            downloader.diagnostic = SimpleNamespace(info=lambda *args, **kwargs: None)
            submitted = []
            downloader.submit_web_task = lambda tid: submitted.append(tid)
            downloader._ensure_comment_delay_scheduler = lambda: None
            downloader.progress_tracker = None

            TelegramRestrictedMediaDownloader.recover_web_runtime.__get__(
                downloader,
                TelegramRestrictedMediaDownloader,
            )()
            self.assertEqual(TransferStatus.PAUSED, store.get_task(task_id)['status'])
            self.assertEqual([], submitted)

    def test_runner_stops_before_next_message_when_pausing(self):
        async def run_case():
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task(
                    'https://t.me/source',
                    'https://t.me/pikpak_bot',
                    start_id=1,
                    end_id=2,
                )
                store.update_task(task_id, status=TransferStatus.RUNNING)
                transferred = []

                async def fake_transfer(**kwargs):
                    transferred.append(kwargs.get('range_message_id'))
                    store.update_task(task_id, status=TransferStatus.PAUSING)
                    return False

                host = SimpleNamespace(
                    transfer_store=store,
                    web_task_manager=None,
                    uploader=object(),
                    app=SimpleNamespace(client=SimpleNamespace()),
                    parse_web_transfer_link=AsyncMock(
                        side_effect=[
                            {'chat_id': 'source-chat'},
                            {'chat_id': 'target-chat'},
                        ]
                    ),
                    find_resumable_transfer_item=lambda *args, **kwargs: None,
                    wait_between_transfer_messages=AsyncMock(),
                    get_web_transfer_range_message=AsyncMock(
                        side_effect=lambda chat_id, message_id, task_id=None: SimpleNamespace(id=message_id)
                    ),
                    transfer_message_to_web_target=fake_transfer,
                    skip_missing_web_transfer_range_message=lambda **kwargs: None,
                    transfer_web_discussion_replies_to_target=AsyncMock(return_value=(0, 0)),
                )
                runner = WebTransferRunner(host)
                with patch.object(runner, 'resume_orphan_resumable_items', new=AsyncMock()):
                    await runner.process_task(task_id)

                self.assertEqual([1], transferred)
                self.assertEqual(TransferStatus.PAUSED, store.get_task(task_id)['status'])

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
