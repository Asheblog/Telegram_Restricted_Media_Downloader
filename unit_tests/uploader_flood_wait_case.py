# coding=UTF-8
import asyncio
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.enums import UploadStatus
from module.task import UploadTask
from module.uploader import TelegramUploader
from pyrogram.errors import FloodWait


class UploaderFloodWaitCase(unittest.TestCase):
    def test_send_media_waits_and_retries_flood_wait_without_marking_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'media.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')

            invoke_attempts = []
            status_updates = []

            class FakeClient:
                async def resolve_peer(self, chat_id):
                    return chat_id

                def rnd_id(self):
                    return 123

                async def invoke(self, payload, *args, **kwargs):
                    invoke_attempts.append(payload)
                    if len(invoke_attempts) == 1:
                        raise FloodWait(7)
                    return object()

            uploader = object.__new__(TelegramUploader)
            uploader.client = FakeClient()
            uploader.valid_link_cache = {}
            upload_task = UploadTask(
                chat_id='target-chat',
                file_path=file_path,
                file_id=1,
                file_size=5,
                file_part=[],
                status=UploadStatus.SUCCESS,
                status_callback=lambda task: status_updates.append(task.status)
            )

            async def run_case():
                async def parse_text_entities(*args, **kwargs):
                    return {}

                with patch('module.uploader.asyncio.sleep') as sleep_mock, \
                        patch('module.uploader.random.uniform', return_value=0), \
                        patch('module.uploader.utils.parse_text_entities', side_effect=parse_text_entities):
                    await uploader.send_media(SimpleNamespace(), upload_task)
                    sleep_mock.assert_awaited_once_with(7)

            asyncio.run(run_case())

            self.assertEqual(2, len(invoke_attempts))
            self.assertEqual(UploadStatus.SENT, upload_task.status)
            self.assertNotIn(UploadStatus.FAILURE, status_updates)


if __name__ == '__main__':
    unittest.main()
