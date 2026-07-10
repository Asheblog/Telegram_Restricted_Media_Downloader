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
sys.argv = [sys.argv[0]]

from module.transfer_store import TransferStore, TransferStatus


def import_downloader_class():
    return __import__('module.downloader', fromlist=['TelegramRestrictedMediaDownloader']).TelegramRestrictedMediaDownloader


class WebTaskPauseDownloadCase(unittest.TestCase):
    def test_pause_web_task_cancels_active_transfer_downloads(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()

        async def run_case():
            with tempfile.TemporaryDirectory() as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
                store.update_task(task_id, status=TransferStatus.RUNNING)
                downloader = object.__new__(TelegramRestrictedMediaDownloader)
                downloader.transfer_store = store
                download_cancelled = asyncio.Event()
                keep_running = asyncio.Event()

                async def fake_resume_download(*args, **kwargs):
                    keep_running.set()
                    try:
                        await asyncio.Event().wait()
                    except asyncio.CancelledError:
                        download_cancelled.set()
                        raise

                download_task = asyncio.create_task(
                    fake_resume_download(message=SimpleNamespace(id=1), file_name=os.path.join(directory, 'video.mp4'))
                )
                await keep_running.wait()
                downloader._register_transfer_download_task({'task_id': task_id}, download_task)

                cancelled = downloader.cancel_task_downloads(task_id)
                await asyncio.gather(download_task, return_exceptions=True)

                self.assertEqual(1, cancelled)
                self.assertTrue(download_cancelled.is_set())
                self.assertEqual([], list(downloader._transfer_download_registry().get(task_id, [])))

        asyncio.run(run_case())

    def test_pause_web_task_invokes_download_cancellation(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            downloader = object.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = store
            downloader.web_task_manager = None
            downloader.discard_web_task_submission = lambda *args, **kwargs: None
            calls = []
            downloader.cancel_task_downloads = lambda tid: calls.append(tid) or 0

            self.assertTrue(
                TelegramRestrictedMediaDownloader.pause_web_task.__get__(
                    downloader,
                    TelegramRestrictedMediaDownloader
                )(task_id)
            )
            self.assertEqual([task_id], calls)

    def test_resume_download_stops_when_transfer_task_is_paused(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()

        async def run_case():
            with tempfile.TemporaryDirectory() as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
                store.update_task(task_id, status=TransferStatus.PAUSED)
                final_path = os.path.join(directory, 'video.mp4')
                cache_path = f'{final_path}.temp'
                with open(cache_path, 'wb') as file:
                    file.write(b'AAAABB')

                offsets = []

                class FakeClient:
                    async def stream_media(self, message, offset=0):
                        offsets.append(offset)
                        yield b'CCCC'
                        while True:
                            await asyncio.sleep(3600)

                downloader = object.__new__(TelegramRestrictedMediaDownloader)
                downloader.app = SimpleNamespace(client=FakeClient())
                downloader.should_continue_web_transfer_task = lambda tid: store.get_task(tid)['status'] != TransferStatus.PAUSED

                message = SimpleNamespace(chat=SimpleNamespace(id=1), id=1)
                with self.assertRaises(asyncio.CancelledError):
                    await downloader.resume_download(
                        message=message,
                        file_name=final_path,
                        chunk_size=4,
                        compare_size=8,
                        transfer_task_id=task_id
                    )

                self.assertEqual([], offsets)
                with open(cache_path, 'rb') as file:
                    self.assertEqual(b'AAAABB', file.read())

        asyncio.run(run_case())

    def test_runner_resumes_download_without_forward_for_partial_item(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()

        async def run_case():
            with tempfile.TemporaryDirectory() as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task(
                    'https://t.me/source',
                    'https://t.me/pikpak_bot',
                    start_id=1,
                    end_id=1
                )
                store.add_item(
                    task_id=task_id,
                    source_chat_id='source-chat',
                    source_message_id=1,
                    source_link='https://t.me/source/1',
                    target_link='https://t.me/pikpak_bot',
                    media_type='video',
                    file_name='video.mp4',
                    phase='downloading',
                    status=TransferStatus.RUNNING
                )
                store.update_task(task_id, status=TransferStatus.RUNNING)

                downloader = object.__new__(TelegramRestrictedMediaDownloader)
                downloader.transfer_store = store
                downloader.uploader = object()
                downloader.app = SimpleNamespace(client=SimpleNamespace())
                downloader.gc = SimpleNamespace(download_upload=True)
                downloader.forward_calls = []
                downloader.fallback_calls = []

                async def fake_forward(**kwargs):
                    downloader.forward_calls.append(kwargs)
                    return SimpleNamespace(id=101)

                async def fake_create_download_task(**kwargs):
                    downloader.fallback_calls.append(kwargs)
                    return {'status': 'success'}

                downloader.forward = fake_forward
                downloader.create_download_task = fake_create_download_task
                downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

                async def fake_parse_link(client, link):
                    if link == 'https://t.me/source':
                        return {'chat_id': 'source-chat'}
                    if link == 'https://t.me/pikpak_bot':
                        return {'chat_id': 'target-chat'}
                    return {'chat_id': 'unknown'}

                message = SimpleNamespace(id=1, link='https://t.me/source/1')
                downloader.get_web_transfer_range_message = AsyncMock(return_value=message)

                with patch('module.downloader.parse_link', side_effect=fake_parse_link), \
                        patch.object(downloader, 'wait_between_transfer_messages', new=AsyncMock()):
                    await downloader.process_web_transfer_task(task_id)

                self.assertEqual([], downloader.forward_calls)
                self.assertEqual(1, len(downloader.fallback_calls))

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
