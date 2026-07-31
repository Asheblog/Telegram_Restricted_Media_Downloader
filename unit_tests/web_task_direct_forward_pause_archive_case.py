# coding=UTF-8
"""Direct PikPak forward must not block pause on synchronous archive."""
import asyncio
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.adapters.pikpak.integration import PikpakIntegrationManager
from module.adapters.webui.task_manager import WebUITaskManager
from module.transfer_store import TransferStore, TransferStatus


def import_downloader_class():
    return __import__('module.downloader', fromlist=['TelegramRestrictedMediaDownloader']).TelegramRestrictedMediaDownloader


class WebTaskDirectForwardPauseArchiveCase(unittest.TestCase):
    def test_complete_forwarded_schedules_archive_without_blocking(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source/1',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
            )
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='source-chat',
                source_message_id=1,
                source_link='https://t.me/source/1',
                target_link='https://t.me/pikpak_bot',
                media_type='forward',
                file_name='video.mp4',
                file_size=5,
                source_folder='source',
                archive_status='pending',
                phase='forwarded',
                status=TransferStatus.RUNNING,
            )
            scheduled = []
            archive_started = []

            class BlockingArchiveClient:
                enabled = True

                def archive_file(self, **kwargs):
                    archive_started.append(time.time())
                    time.sleep(30)
                    return SimpleNamespace(ok=True, status='success', archive_path='Telegram/source/video.mp4')

            manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: store,
                pikpak_archive_client_getter=lambda: BlockingArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: SimpleNamespace(config={
                    'target_profiles': {
                        'pikpak': {'archive': {'enable': True, 'remote': 'pikpak'}}
                    }
                }),
                refresh_counts=lambda tid: store.refresh_task_counts(tid),
                schedule_deferred_archive=lambda **kwargs: scheduled.append(kwargs) or True,
            )
            task = store.get_task(task_id)
            started = time.perf_counter()
            ok = manager.complete_forwarded_pikpak_item(
                task=task,
                item_id=item_id,
                task_id=task_id,
                message=SimpleNamespace(
                    id=1,
                    video=SimpleNamespace(file_size=5, file_name='video.mp4'),
                ),
                source_link='https://t.me/source/1',
                transferred_at=time.time(),
                source_folder='source',
            )
            elapsed = time.perf_counter() - started

            self.assertTrue(ok)
            self.assertLess(elapsed, 1.0)
            self.assertEqual([], archive_started)
            self.assertEqual(1, len(scheduled))
            self.assertEqual(0, scheduled[0].get('delay_seconds'))
            item = store.get_item(item_id)
            self.assertEqual(TransferStatus.SUCCESS, item['status'])
            self.assertEqual('pending', item['archive_status'])
            events = [event['message'] for event in store.list_events(task_id)]
            self.assertTrue(any('archive scheduled' in message for message in events))

    def test_pausing_direct_forward_settles_without_waiting_for_archive(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()

        async def run_case():
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task(
                    'https://t.me/source',
                    'https://t.me/pikpak_bot',
                    target_profile='pikpak',
                    start_id=1,
                    end_id=1,
                )
                store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
                store.update_task(task_id, status=TransferStatus.RUNNING)
                task = store.get_task(task_id)
                scheduled = []

                class BlockingArchiveClient:
                    enabled = True

                    def archive_file(self, **kwargs):
                        time.sleep(30)
                        return SimpleNamespace(
                            ok=True, status='success', archive_path='Telegram/source/video.mp4'
                        )

                downloader = object.__new__(TelegramRestrictedMediaDownloader)
                downloader.transfer_store = store
                downloader.app = SimpleNamespace(client=object())
                downloader.gc = SimpleNamespace(
                    config={
                        'target_profiles': {
                            'pikpak': {'archive': {'enable': True, 'remote': 'pikpak'}}
                        }
                    }
                )
                downloader.forward = AsyncMock(return_value=SimpleNamespace(id=100))

                async def fake_ingest(**_kwargs):
                    # User clicks pause while waiting for PikPak bot confirmation.
                    store.update_task(task_id, status=TransferStatus.PAUSING)
                    return True

                downloader.wait_for_pikpak_ingest_confirmation = fake_ingest
                downloader.web_task_manager = WebUITaskManager(
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
                    uploader_getter=lambda: None,
                )
                downloader.pikpak_manager = PikpakIntegrationManager(
                    transfer_store_getter=lambda: store,
                    pikpak_archive_client_getter=lambda: BlockingArchiveClient(),
                    diagnostic=SimpleNamespace(
                        warning=lambda m: None, info=lambda m: None, status=lambda m: None
                    ),
                    gc_getter=lambda: downloader.gc,
                    refresh_counts=lambda tid: store.refresh_task_counts(tid),
                    schedule_deferred_archive=lambda **kwargs: scheduled.append(kwargs) or True,
                )

                started = time.perf_counter()
                await downloader.transfer_message_to_web_target(
                    task=task,
                    message=SimpleNamespace(
                        id=1,
                        link='https://t.me/source/1',
                        chat=SimpleNamespace(id='source-chat', username='source'),
                        video=SimpleNamespace(file_size=5, file_name='video.mp4'),
                    ),
                    origin_chat_id='source-chat',
                    target_chat_id='target-chat',
                    source_link='https://t.me/source/1',
                )
                transfer_elapsed = time.perf_counter() - started
                self.assertLess(transfer_elapsed, 1.0)
                self.assertEqual(1, len(scheduled))
                self.assertEqual(TransferStatus.PAUSING, store.get_task(task_id)['status'])

                settle_started = time.perf_counter()
                self.assertTrue(await downloader.settle_web_task_pause_request(task_id, before='2'))
                settle_elapsed = time.perf_counter() - settle_started
                self.assertLess(settle_elapsed, 1.0)
                self.assertEqual(TransferStatus.PAUSED, store.get_task(task_id)['status'])
                item = store.list_items(task_id)[0]
                self.assertEqual(TransferStatus.SUCCESS, item['status'])
                self.assertEqual('pending', item['archive_status'])

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
