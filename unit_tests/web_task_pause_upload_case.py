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

from module.enums import UploadStatus
from module.task import UploadTask
from module.transfer_store import TransferStore, TransferStatus
from module.uploader import TelegramUploader


def import_downloader_class():
    return __import__('module.downloader', fromlist=['TelegramRestrictedMediaDownloader']).TelegramRestrictedMediaDownloader


class WebTaskPauseUploadCase(unittest.TestCase):
    def test_pause_web_task_invokes_upload_pause(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            downloader = object.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = store
            downloader.web_task_manager = None
            downloader.discard_web_task_submission = lambda *args, **kwargs: None
            download_calls = []
            upload_calls = []
            downloader.cancel_task_downloads = lambda tid: download_calls.append(tid) or 0
            downloader.pause_task_uploads = lambda tid: upload_calls.append(tid) or 0

            self.assertTrue(
                TelegramRestrictedMediaDownloader.pause_web_task.__get__(
                    downloader,
                    TelegramRestrictedMediaDownloader
                )(task_id)
            )
            self.assertEqual([task_id], download_calls)
            self.assertEqual([task_id], upload_calls)

    def test_pause_uploads_for_task_drops_queue_without_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'queued.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')
            uploader = object.__new__(TelegramUploader)
            loop = asyncio.new_event_loop()
            uploader.upload_queue = asyncio.Queue()
            uploader.loop = loop
            uploader.upload_context = SimpleNamespace(
                should_continue_web_transfer_task=lambda task_id: False,
                transfer_store=None,
                diagnostic=SimpleNamespace(
                    info=lambda *args, **kwargs: None,
                    warning=lambda *args, **kwargs: None,
                    error=lambda *args, **kwargs: None,
                    console_log=lambda *args, **kwargs: None,
                ),
            )
            uploader.notify_transfer_status = lambda upload_task: None

            paused_task = UploadTask(
                chat_id=1,
                file_path=file_path,
                file_id=1,
                file_size=5,
                file_part=[],
                status=UploadStatus.PENDING,
                transfer_meta={'task_id': 7},
            )
            other_task = UploadTask(
                chat_id=1,
                file_path=file_path,
                file_id=2,
                file_size=5,
                file_part=[],
                status=UploadStatus.PENDING,
                transfer_meta={'task_id': 9},
            )
            uploader.upload_queue.put_nowait((None, paused_task))
            uploader.upload_queue.put_nowait((None, other_task))

            paused = uploader.pause_uploads_for_task(7)

            self.assertEqual(1, paused)
            self.assertEqual(UploadStatus.PENDING, paused_task.status)
            self.assertEqual(UploadStatus.PENDING, other_task.status)
            self.assertEqual(1, uploader.upload_queue.qsize())
            remaining_media, remaining_task = uploader.upload_queue.get_nowait()
            self.assertEqual(9, remaining_task.transfer_meta['task_id'])

    def test_resume_upload_stops_when_transfer_task_is_paused(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'video.mp4')
            with open(file_path, 'wb') as file:
                file.write(b'0' * (1024 * 1024 + 1))

            uploader = object.__new__(TelegramUploader)
            uploader.loop = asyncio.new_event_loop()
            uploader.PART_UPLOAD_DELAY = 0
            uploader.upload_context = SimpleNamespace(
                should_continue_web_transfer_task=lambda task_id: False,
                diagnostic=SimpleNamespace(
                    info=lambda *args, **kwargs: None,
                    warning=lambda *args, **kwargs: None,
                    error=lambda *args, **kwargs: None,
                    console_log=lambda *args, **kwargs: None,
                ),
            )
            uploader.upload_file_part = AsyncMock()
            uploader.notify_transfer_progress = lambda *args, **kwargs: None

            upload_task = UploadTask(
                chat_id=1,
                file_path=file_path,
                file_id=1,
                file_size=len(b'0' * (1024 * 1024 + 1)),
                file_part=[],
                status=UploadStatus.UPLOADING,
                transfer_meta={'task_id': 3},
            )

            async def run_case():
                with self.assertRaises(asyncio.CancelledError):
                    await uploader.resume_upload(upload_task)

            asyncio.run(run_case())
            uploader.upload_file_part.assert_not_awaited()

    def test_pause_uploads_for_task_cancels_active_resume_upload_task(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'video.mp4')
            with open(file_path, 'wb') as file:
                file.write(b'0' * (1024 * 1024 + 1))

            uploader = object.__new__(TelegramUploader)
            loop = asyncio.new_event_loop()
            uploader.upload_queue = asyncio.Queue()
            uploader.loop = loop
            uploader.PART_UPLOAD_DELAY = 0
            uploader.upload_context = SimpleNamespace(
                should_continue_web_transfer_task=lambda task_id: True,
                transfer_store=None,
                diagnostic=SimpleNamespace(
                    info=lambda *args, **kwargs: None,
                    warning=lambda *args, **kwargs: None,
                    error=lambda *args, **kwargs: None,
                    console_log=lambda *args, **kwargs: None,
                ),
            )
            uploader.notify_transfer_progress = lambda *args, **kwargs: None
            upload_cancelled = asyncio.Event()

            async def fake_upload_file_part(upload_task, file_part):
                upload_cancelled.set()
                await asyncio.Event().wait()

            uploader.upload_file_part = fake_upload_file_part

            upload_task = UploadTask(
                chat_id=1,
                file_path=file_path,
                file_id=1,
                file_size=len(b'0' * (1024 * 1024 + 1)),
                file_part=[],
                status=UploadStatus.UPLOADING,
                transfer_meta={'task_id': 5},
            )

            async def run_case():
                resume_task = loop.create_task(uploader.resume_upload(upload_task))
                uploader._register_transfer_upload_task(upload_task, resume_task)
                await upload_cancelled.wait()
                paused = uploader.pause_uploads_for_task(5)
                await asyncio.gather(resume_task, return_exceptions=True)
                return paused

            paused = loop.run_until_complete(run_case())
            self.assertGreaterEqual(paused, 1)
            self.assertEqual(UploadStatus.UPLOADING, upload_task.status)
            self.assertEqual([], list(uploader._transfer_upload_registry().get(5, [])))


if __name__ == '__main__':
    unittest.main()
