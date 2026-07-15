# coding=UTF-8
"""PikPak download fallback: rclone copyto My Telegram, then reuse archive."""
import asyncio
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.enums import UploadStatus
from module.pikpak_archive import (
    DisabledPikPakArchiveClient,
    PikPakArchiveResult,
    RclonePikPakArchiveClient,
)


class _FakeCompleted:
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class PikpakRcloneIngestCase(unittest.TestCase):
    def test_upload_to_ingest_copyto_my_telegram(self):
        calls = []

        def runner(args, **kwargs):
            calls.append(args)
            return _FakeCompleted()

        client = RclonePikPakArchiveClient(
            {
                'enable': True,
                'remote': 'pikpak',
                'source_directory': 'My Telegram',
            },
            runner=runner,
        )
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as handle:
            handle.write(b'hello')
            local_path = handle.name
        try:
            result = client.upload_to_ingest(local_path, '123 - title.mp4')
        finally:
            os.unlink(local_path)

        self.assertTrue(result.ok)
        self.assertEqual('uploaded', result.status)
        self.assertEqual('My Telegram/123 - title.mp4', result.archive_path)
        copyto = [c for c in calls if len(c) >= 2 and c[1] == 'copyto']
        self.assertEqual(1, len(copyto))
        self.assertEqual(local_path, copyto[0][2])
        self.assertEqual('pikpak:My Telegram/123 - title.mp4', copyto[0][3])

    def test_upload_to_ingest_requires_remote(self):
        client = DisabledPikPakArchiveClient()
        result = client.upload_to_ingest('/tmp/a.mp4', 'a.mp4')
        self.assertFalse(result.ok)
        self.assertEqual('disabled', result.status)

    def test_download_upload_pikpak_uses_rclone_not_telegram_send(self):
        from module.infra.uploader import TelegramUploader
        from module.task import UploadTask

        statuses = []
        cleaned = []

        class FakeArchive:
            def upload_to_ingest(self, local_path, file_name=None):
                return PikPakArchiveResult(
                    True,
                    'uploaded',
                    archive_path=f'My Telegram/{file_name or os.path.basename(local_path)}',
                )

        class FakeUploader(TelegramUploader):
            def __init__(self):
                self.loop = asyncio.new_event_loop()
                self.client = SimpleNamespace(rnd_id=lambda: 1)
                self.upload_context = SimpleNamespace(
                    pikpak_manager=SimpleNamespace(
                        get_pikpak_archive_client=lambda: FakeArchive()
                    ),
                    transfer_store=None,
                    is_running=True,
                    is_bot_running=False,
                    web_ui=None,
                    diagnostic=SimpleNamespace(
                        info=lambda *a, **k: None,
                        warning=lambda *a, **k: None,
                        error=lambda *a, **k: None,
                        console_log=lambda *a, **k: None,
                        exception=lambda *a, **k: None,
                    ),
                )
                self.valid_link_cache = {}
                self.current_task_num = 0
                self.max_upload_task = 1
                self.max_upload_retries = 1
                self.upload_queue = asyncio.Queue()
                self.event = asyncio.Event()
                self.pb = SimpleNamespace()
                self.app = SimpleNamespace()
                self.is_premium = False

            async def create_upload_task(self, *args, **kwargs):
                raise AssertionError('Telegram create_upload_task must not run for pikpak ingest')

        uploader = FakeUploader()
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as handle:
            handle.write(b'data')
            local_path = handle.name
        try:
            releases = []

            def status_callback(task):
                statuses.append(task.status)
                if task.status == UploadStatus.SENT:
                    cleaned.append(task.file_path)

            with_upload = {
                'link': 'https://t.me/pikpak_bot',
                'target_profile': 'pikpak',
                'with_delete': True,
                'source_link': 'https://t.me/ctuxas/1',
                'source_folder': 'ctuxas/1 - title',
                'file_name': '1 - title.mp4',
                'task_id': 7,
                'item_id': 9,
                'status_callback': status_callback,
                '_window_release': lambda: releases.append('window'),
                '_local_storage_release': lambda: releases.append('storage'),
                'on_file_ready': lambda path, wu: 9,
            }

            async def run():
                uploader.download_upload(with_upload, local_path)
                await asyncio.sleep(0.05)
                # drain pending rclone task
                pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                if pending:
                    await asyncio.wait(pending, timeout=2)

            uploader.loop.run_until_complete(run())
        finally:
            uploader.loop.close()
            if os.path.exists(local_path):
                os.unlink(local_path)

        self.assertIn(UploadStatus.SENT, statuses)
        self.assertIn(UploadStatus.SUCCESS, statuses)
        self.assertIn('window', releases)
        self.assertIn('storage', releases)
        self.assertTrue(cleaned)


if __name__ == '__main__':
    unittest.main()
