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
from pyrogram.errors.exceptions import FilePartMissing


class UploaderFloodWaitCase(unittest.TestCase):
    def test_progress_upload_records_completed_part_index_without_ahead_of_boundary(self):
        from module.stdio import ProgressBar

        class FakeProgress:
            def update(self, *args, **kwargs):
                pass

        class FakeUploadManager:
            def __init__(self):
                self.parts = []

            def update_file_part(self, file_part):
                self.parts.append(file_part)

        manager = FakeUploadManager()

        ProgressBar.upload(
            current=512 * 1024,
            total=1024 * 1024,
            progress=FakeProgress(),
            task_id=1,
            upload_manager=manager
        )

        self.assertEqual([0], manager.parts)

    def test_file_part_missing_forgets_reported_part_without_resetting_file_id(self):
        with tempfile.TemporaryDirectory() as directory:
            original_directory = UploadTask.DIRECTORY_NAME
            UploadTask.DIRECTORY_NAME = os.path.join(directory, 'upload-cache')
            file_path = os.path.join(directory, 'media.bin')
            try:
                with open(file_path, 'wb') as file:
                    file.write(b'a' * (4 * 512 * 1024))

                uploader = object.__new__(TelegramUploader)

                upload_task = UploadTask(
                    chat_id=None,
                    file_path=file_path,
                    file_id=111,
                    file_size=os.path.getsize(file_path),
                    file_part=[0, 1, 2, 3],
                    status=UploadStatus.PENDING
                )
                upload_task.chat_id = 'target-chat'

                cached_path = upload_task.upload_manager_path
                upload_task.rewind_after_missing_part(2)

                self.assertEqual(111, upload_task.file_id)
                self.assertEqual([0, 1, 3], upload_task.file_part)
                self.assertEqual(cached_path, upload_task.upload_manager_path)
                with open(upload_task.upload_manager_path, encoding='UTF-8') as file:
                    payload = __import__('json').load(file)
                self.assertEqual(111, payload['file_id'])
                self.assertEqual([0, 1, 3], payload['file_part'])
            finally:
                UploadTask.DIRECTORY_NAME = original_directory

    def test_create_upload_task_repairs_missing_part_before_resetting_file_id(self):
        with tempfile.TemporaryDirectory() as directory:
            original_directory = UploadTask.DIRECTORY_NAME
            UploadTask.DIRECTORY_NAME = os.path.join(directory, 'upload-cache')
            file_path = os.path.join(directory, 'media.bin')
            try:
                with open(file_path, 'wb') as file:
                    file.write(b'a' * (4 * 512 * 1024))

                class FakeClient:
                    def __init__(self):
                        self.ids = iter([201, 202])
                        self.me = SimpleNamespace(is_premium=True)

                    def rnd_id(self):
                        return next(self.ids)

                uploader = object.__new__(TelegramUploader)
                uploader.client = FakeClient()
                uploader.valid_link_cache = {}
                uploader.is_premium = True
                uploader.max_upload_retries = 3
                uploader.current_task_num = 0
                uploader.download_object = SimpleNamespace(gc={})
                attempts = []

                async def missing_once(upload_task):
                    attempts.append((upload_task.file_id, list(upload_task.file_part)))
                    if len(attempts) == 1:
                        raise FilePartMissing(2)
                    upload_task.status = UploadStatus.SUCCESS

                uploader._TelegramUploader__add_task = missing_once

                upload_task = UploadTask(
                    chat_id=None,
                    file_path=file_path,
                    file_id=200,
                    file_size=os.path.getsize(file_path),
                    file_part=[0, 1, 2, 3],
                    status=UploadStatus.PENDING
                )

                asyncio.run(uploader.create_upload_task(link='target-chat', upload_task=upload_task))

                self.assertEqual(UploadStatus.SUCCESS, upload_task.status)
                self.assertEqual([(200, [0, 1, 2, 3]), (200, [0, 1, 3])], attempts)
                self.assertIsNone(upload_task.error_msg)
            finally:
                UploadTask.DIRECTORY_NAME = original_directory

    def test_create_upload_task_aborts_after_repeated_file_part_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'media.bin')
            with open(file_path, 'wb') as file:
                file.write(b'a' * (2 * 512 * 1024))

            class FakeClient:
                def __init__(self):
                    self.ids = iter([200, 201, 202, 203, 204])
                    self.me = SimpleNamespace(is_premium=True)

                def rnd_id(self):
                    return next(self.ids)

            uploader = object.__new__(TelegramUploader)
            uploader.client = FakeClient()
            uploader.valid_link_cache = {}
            uploader.is_premium = True
            uploader.max_upload_retries = 3
            uploader.current_task_num = 0
            uploader.download_object = SimpleNamespace(gc={})

            async def always_missing(upload_task):
                raise FilePartMissing(1)

            uploader._TelegramUploader__add_task = always_missing

            upload_task = UploadTask(
                chat_id=None,
                file_path=file_path,
                file_id=200,
                file_size=os.path.getsize(file_path),
                file_part=[0, 1],
                status=UploadStatus.PENDING
            )

            asyncio.run(uploader.create_upload_task(link='target-chat', upload_task=upload_task))

            self.assertEqual(UploadStatus.FAILURE, upload_task.status)
            self.assertIn('FILE_PART_X_MISSING', upload_task.error_msg)

    def test_file_part_missing_completion_callback_does_not_emit_intermediate_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'media.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')

            status_updates = []
            uploader = object.__new__(TelegramUploader)
            uploader.current_task_num = 1
            uploader.event = SimpleNamespace(set=lambda: None)
            uploader.pb = SimpleNamespace(progress=SimpleNamespace(remove_task=lambda task_id: None))
            upload_task = UploadTask(
                chat_id=None,
                file_path=file_path,
                file_id=1,
                file_size=5,
                file_part=[],
                status=UploadStatus.UPLOADING,
                status_callback=lambda task: status_updates.append(task.status)
            )

            uploader.upload_complete_callback(
                upload_task=upload_task,
                task_id=1,
                _future=SimpleNamespace(result=lambda: (_ for _ in ()).throw(FilePartMissing(1)))
            )

            self.assertEqual(UploadStatus.UPLOADING, upload_task.status)
            self.assertEqual([], status_updates)

    def test_upload_complete_releases_local_storage_after_transfer_file_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            original_directory = UploadTask.DIRECTORY_NAME
            UploadTask.DIRECTORY_NAME = os.path.join(directory, 'upload-cache')
            file_path = os.path.join(directory, 'media.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')
            released = []
            try:
                uploader = object.__new__(TelegramUploader)
                uploader.current_task_num = 1
                uploader.event = SimpleNamespace(set=lambda: None)
                uploader.pb = SimpleNamespace(progress=SimpleNamespace(remove_task=lambda task_id: None))
                upload_task = UploadTask(
                    chat_id=None,
                    file_path=file_path,
                    file_id=1,
                    file_size=5,
                    file_part=[],
                    status=UploadStatus.UPLOADING,
                    with_delete=True,
                    transfer_meta={'local_storage_release': lambda: released.append(True)}
                )

                uploader.upload_complete_callback(
                    upload_task=upload_task,
                    task_id=1,
                    _future=SimpleNamespace(result=lambda: None)
                )

                self.assertEqual([True], released)
                self.assertIsNone(upload_task.transfer_meta['local_storage_release'])
                self.assertFalse(os.path.exists(file_path))
                self.assertEqual(UploadStatus.SUCCESS, upload_task.status)
            finally:
                UploadTask.DIRECTORY_NAME = original_directory

    def test_pikpak_upload_over_target_limit_fails_and_deletes_transfer_file(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'oversize.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')

            status_updates = []
            released = []
            window_releases = []
            uploader = object.__new__(TelegramUploader)
            uploader.valid_link_cache = {}
            uploader.is_premium = True
            uploader.max_upload_retries = 1
            uploader.current_task_num = 0

            upload_task = UploadTask(
                chat_id=None,
                file_path=file_path,
                file_id=1,
                file_size=4 * 1024 ** 3 + 1,
                file_part=[],
                status=UploadStatus.PENDING,
                with_delete=True,
                release_callback=lambda: window_releases.append(True),
                transfer_meta={'target_profile': 'pikpak', 'local_storage_release': lambda: released.append(True)},
                status_callback=lambda task: status_updates.append(task.status)
            )

            async def run_case():
                with patch('module.uploader.os.path.getsize', return_value=4 * 1024 ** 3 + 1):
                    await uploader.create_upload_task(link='target-chat', upload_task=upload_task)

            asyncio.run(run_case())

            self.assertEqual(UploadStatus.FAILURE, upload_task.status)
            self.assertIn('PikPak', upload_task.error_msg)
            self.assertFalse(os.path.exists(file_path))
            self.assertEqual([True], released)
            self.assertEqual([True], window_releases)
            self.assertIn(UploadStatus.FAILURE, status_updates)

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

    def test_upload_complete_callback_notifies_transfer_success_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'media.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')

            status_updates = []
            uploader = object.__new__(TelegramUploader)
            uploader.current_task_num = 1
            uploader.event = SimpleNamespace(set=lambda: None)
            uploader.pb = SimpleNamespace(progress=SimpleNamespace(remove_task=lambda task_id: None))
            upload_task = UploadTask(
                chat_id='target-chat',
                file_path=file_path,
                file_id=1,
                file_size=5,
                file_part=[],
                status=UploadStatus.UPLOADING,
                with_delete=False,
                status_callback=lambda task: status_updates.append(task.status)
            )

            uploader.upload_complete_callback(
                upload_task=upload_task,
                task_id=1,
                _future=SimpleNamespace(result=lambda: None)
            )

            self.assertEqual(UploadStatus.SUCCESS, upload_task.status)
            self.assertIn(UploadStatus.SUCCESS, status_updates)

    def test_download_upload_keeps_file_name_in_transfer_meta(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'title-name.mp4')
            with open(file_path, 'wb') as file:
                file.write(b'12345')

            captured = []

            class FakeClient:
                def rnd_id(self):
                    return 123

            async def fake_create_upload_task(link, upload_task):
                captured.append((link, upload_task))

            def fake_create_task(coroutine):
                asyncio.run(coroutine)
                return SimpleNamespace()

            uploader = object.__new__(TelegramUploader)
            uploader.client = FakeClient()
            uploader.create_upload_task = fake_create_upload_task

            with patch('module.uploader.asyncio.create_task', side_effect=fake_create_task):
                uploader.download_upload(
                    with_upload={
                        'link': 'https://t.me/pikpak_bot',
                        'target_profile': 'pikpak',
                        'source_link': 'https://t.me/source/1',
                        'source_folder': 'source',
                        'file_name': 'title-name.mp4'
                    },
                    file_path=file_path
                )

            self.assertEqual(1, len(captured))
            upload_task = captured[0][1]
            self.assertEqual('title-name.mp4', upload_task.file_name)
            self.assertEqual('title-name.mp4', upload_task.transfer_meta['file_name'])
            self.assertEqual('pikpak', upload_task.transfer_meta['target_profile'])


if __name__ == '__main__':
    unittest.main()
