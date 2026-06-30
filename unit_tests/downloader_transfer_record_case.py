# coding=UTF-8
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.downloader import TelegramRestrictedMediaDownloader
from module.transfer_store import TransferStore
from module.enums import UploadStatus
from module.task import DownloadTask


class DownloaderTransferRecordCase(unittest.TestCase):
    def test_reuse_download_success_record_only_when_record_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            media_path = os.path.join(directory, 'media.bin')
            with open(media_path, 'wb') as file:
                file.write(b'12345')

            downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = TransferStore(directory=directory)
            uploaded = []

            class FakeUploader:
                def download_upload(self, with_upload, file_path):
                    uploaded.append((with_upload, file_path))

            downloader.uploader = FakeUploader()
            downloader.release_download_upload_window = lambda with_upload: None
            downloader.transfer_store.upsert_download_success_record(
                source_chat_id='source',
                source_message_id=7,
                source_link='https://t.me/source/7',
                media_type='document',
                local_path=media_path,
                file_size=5,
                file_name='media.bin'
            )
            task_id = downloader.transfer_store.create_task(
                source_link='https://t.me/source/7',
                target_link='https://t.me/pikpak_bot'
            )
            item_id = downloader.transfer_store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=7,
                source_link='https://t.me/source/7',
                target_link='https://t.me/pikpak_bot'
            )
            with_upload = {
                'task_id': task_id,
                'item_id': item_id,
                'source_chat_id': 'source',
                'message_id': 7
            }
            message = SimpleNamespace(id=7, get_media_group=lambda: (_ for _ in ()).throw(ValueError()))

            self.assertEqual(
                media_path,
                downloader.try_reuse_transfer_download_record(with_upload, message, expected_size=5)
            )
            self.assertEqual(media_path, uploaded[-1][1])

            os.remove(media_path)
            self.assertIsNone(
                downloader.try_reuse_transfer_download_record(with_upload, message, expected_size=5)
            )

    def test_transfer_item_uses_message_chat_id_for_download_success_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = TransferStore(directory=directory)
            downloader.refresh_transfer_task_counts = lambda task_id: None
            task_id = downloader.transfer_store.create_task(
                source_link='https://t.me/source/7',
                target_link='https://t.me/pikpak_bot'
            )
            message = SimpleNamespace(
                id=7,
                link='https://t.me/source/7',
                chat=SimpleNamespace(id=-100123)
            )
            meta = downloader.create_transfer_item_for_download(
                task_with_upload={'task_id': task_id, 'link': 'https://t.me/pikpak_bot'},
                chat_id='source',
                link='https://t.me/source/7',
                message=message,
                media_type='document',
                file_name='media.bin',
                final_path=os.path.join(directory, 'media.bin'),
                file_size=5
            )

            self.assertEqual('-100123', meta['source_chat_id'])
            item = downloader.transfer_store.list_items(task_id)[0]
            self.assertEqual('-100123', item['source_chat_id'])

    def test_transfer_meta_without_web_task_still_gets_download_record_identity(self):
        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.transfer_store = None
        message = SimpleNamespace(
            id=9,
            link='https://t.me/source/9',
            chat=SimpleNamespace(id=-100999)
        )

        meta = downloader.create_transfer_item_for_download(
            task_with_upload={'link': 'https://t.me/target'},
            chat_id='source',
            link='https://t.me/source/9',
            message=message,
            media_type='video',
            file_name='video.mp4',
            final_path='/tmp/video.mp4',
            file_size=9
        )

        self.assertEqual('-100999', meta['source_chat_id'])
        self.assertEqual(9, meta['message_id'])
        self.assertEqual('video', meta['media_type'])

    def test_transfer_download_meta_includes_source_folder_and_final_path(self):
        with tempfile.TemporaryDirectory() as directory:
            downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = TransferStore(directory=directory)
            downloader.app = SimpleNamespace(save_directory=directory)
            downloader.refresh_transfer_task_counts = lambda task_id: None
            task_id = downloader.transfer_store.create_task(
                source_link='https://t.me/ctuxas/7',
                target_link='https://t.me/pikpak_bot'
            )
            message = SimpleNamespace(
                id=7,
                link='https://t.me/ctuxas/7',
                chat=SimpleNamespace(id=-100123, username='ctuxas')
            )

            meta = downloader.create_transfer_item_for_download(
                task_with_upload={'task_id': task_id, 'link': 'https://t.me/pikpak_bot'},
                chat_id='ctuxas',
                link='https://t.me/ctuxas/7',
                message=message,
                media_type='video',
                file_name='video.mp4',
                final_path=os.path.join(directory, 'video.mp4'),
                file_size=9
            )

            self.assertEqual('ctuxas', meta['source_folder'])
            item = downloader.transfer_store.list_items(task_id)[0]
            self.assertEqual('ctuxas', item['source_folder'])
            self.assertEqual(os.path.join(directory, 'ctuxas', 'video.mp4'), item['local_path'])

    def test_bot_progress_is_updated_for_download_upload_lifecycle(self):
        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.transfer_store = None
        downloader._scheduled_bot_progress_updates = []
        downloader.schedule_bot_transfer_progress_update = (
            lambda progress, text, force=False: downloader._scheduled_bot_progress_updates.append(text)
        )
        bot_progress = {
            'source_link': 'https://t.me/source/7',
            'target_link': 'https://t.me/pikpak_bot',
            'source_message_id': 7,
            'file_name': 'media.bin',
            'min_interval': 0
        }
        with_upload = {
            'bot_progress': bot_progress,
            'file_name': 'media.bin'
        }
        downloader.pb = SimpleNamespace(download=lambda *args, **kwargs: None)

        downloader.transfer_download_progress(
            current=5,
            total=10,
            progress=SimpleNamespace(update=lambda *args, **kwargs: None),
            task_id=1,
            with_upload=with_upload
        )
        upload_task = SimpleNamespace(
            file_name='media.bin',
            file_size=10,
            status=UploadStatus.SENT,
            error_msg=None,
            transfer_meta={
                'bot_progress': bot_progress,
                'file_name': 'media.bin'
            }
        )
        downloader.on_transfer_upload_progress(upload_task, current=7, total=10)
        downloader.on_transfer_upload_status(upload_task)

        joined = '\n'.join(downloader._scheduled_bot_progress_updates)
        self.assertIn('📥 下载中 50.0%', joined)
        self.assertIn('📤 上传中 70.0%', joined)
        self.assertIn('✅ 已发送到目标', joined)

    def test_bot_progress_reports_upload_failure_even_without_transfer_store(self):
        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.transfer_store = None
        downloader._scheduled_bot_progress_updates = []
        downloader.schedule_bot_transfer_progress_update = (
            lambda progress, text, force=False: downloader._scheduled_bot_progress_updates.append(text)
        )
        upload_task = SimpleNamespace(
            file_name='media.bin',
            file_size=10,
            status=UploadStatus.FAILURE,
            error_msg='target rejected file',
            transfer_meta={
                'bot_progress': {
                    'source_link': 'https://t.me/source/7',
                    'target_link': 'https://t.me/pikpak_bot',
                    'source_message_id': 7,
                    'file_name': 'media.bin',
                    'min_interval': 0
                },
                'file_name': 'media.bin'
            }
        )

        downloader.on_transfer_upload_status(upload_task)

        self.assertIn('❌ 上传失败', downloader._scheduled_bot_progress_updates[-1])
        self.assertIn('target rejected file', downloader._scheduled_bot_progress_updates[-1])

    def test_download_complete_initializes_uploader_for_download_upload_task(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_directory = os.path.join(directory, 'temp')
            save_directory = os.path.join(directory, 'downloads')
            os.makedirs(temp_directory, exist_ok=True)
            os.makedirs(save_directory, exist_ok=True)
            temp_file_path = os.path.join(temp_directory, 'media.bin.temp')
            final_path = os.path.join(save_directory, 'media.bin')
            with open(temp_file_path, 'wb') as file:
                file.write(b'12345')

            uploaded = []
            link = 'https://t.me/source/7'
            DownloadTask.LINK_INFO.clear()
            DownloadTask.COMPLETE_LINK.clear()
            DownloadTask(
                link=link,
                link_type='single',
                member_num=2,
                complete_num=0,
                file_name=set(),
                error_msg={}
            )

            class FakeUploader:
                def __init__(self, download_object):
                    self.download_object = download_object

                def download_upload(self, with_upload, file_path):
                    uploaded.append((with_upload, file_path))

            downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = None
            downloader.uploader = None
            downloader.app = SimpleNamespace(
                current_task_num=1,
                max_download_retries=1,
                get_file_type=lambda *args, **kwargs: 'document'
            )
            downloader.event = SimpleNamespace(set=lambda: None)
            downloader.queue = SimpleNamespace(task_done=lambda: None)
            downloader.pb = SimpleNamespace(progress=SimpleNamespace(remove_task=lambda task_id: None))
            downloader.get_final_save_directory = lambda message, with_upload=None: save_directory
            downloader.get_final_file_path = lambda message, file_name, with_upload=None: os.path.join(save_directory, file_name)
            downloader.record_transfer_download_success = lambda with_upload, message, file_path: None
            downloader.release_download_upload_window = lambda with_upload: None
            downloader.create_uploader = lambda: FakeUploader(downloader)
            message = SimpleNamespace(id=7, get_media_group=lambda: (_ for _ in ()).throw(ValueError()))
            with_upload = {
                'link': 'https://t.me/pikpak_bot',
                'with_delete': True,
                'target_profile': 'pikpak'
            }

            downloader.download_complete_callback(
                sever_file_size=5,
                temp_file_path=temp_file_path,
                link=link,
                message=message,
                file_name='media.bin',
                retry_count=0,
                file_id=7,
                format_file_size='5.00B',
                task_id=1,
                with_upload=with_upload,
                diy_download_type=None,
                _future=final_path
            )

            self.assertEqual(1, len(uploaded))
            self.assertEqual(final_path, uploaded[0][1])
            self.assertEqual(7, uploaded[0][0]['message_id'])

    def test_start_download_upload_creates_missing_uploader(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = os.path.join(directory, 'media.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')

            uploaded = []

            class FakeUploader:
                def download_upload(self, with_upload, file_path):
                    uploaded.append((with_upload, file_path))

            downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
            downloader.uploader = None
            downloader.create_uploader = lambda: FakeUploader()
            downloader.release_download_upload_window = lambda with_upload: None
            message = SimpleNamespace(id=9, get_media_group=lambda: (_ for _ in ()).throw(ValueError()))
            with_upload = {'link': 'https://t.me/pikpak_bot'}

            self.assertTrue(downloader.start_download_upload(with_upload, message, file_path))

            self.assertIsNotNone(downloader.uploader)
            self.assertEqual(file_path, uploaded[0][1])
            self.assertEqual(9, uploaded[0][0]['message_id'])

    def test_pikpak_download_upload_meta_uses_profile_defaults_even_when_media_group_requested(self):
        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.gc = SimpleNamespace(upload_delete=False)

        meta = downloader.build_download_upload_meta(
            target_link='https://t.me/pikpak_bot',
            source_link='https://t.me/source/7',
            source_folder='source',
            send_as_media_group=True
        )

        self.assertEqual('pikpak', meta['target_profile'])
        self.assertTrue(meta['with_delete'])
        self.assertTrue(meta['send_as_media_group'])
        self.assertIs(meta['status_callback'].__self__, downloader)
        self.assertIs(meta['on_file_ready'].__self__, downloader)


if __name__ == '__main__':
    unittest.main()
