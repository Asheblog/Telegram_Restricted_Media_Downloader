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


class DownloaderTransferRecordCase(unittest.TestCase):
    def test_reuse_download_success_record_only_when_record_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            media_path = os.path.join(directory, 'media.bin')
            with open(media_path, 'wb') as file:
                file.write(b'12345')

            downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
            downloader.transfer_store = TransferStore(directory=directory)
            downloader.uploader = None
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


if __name__ == '__main__':
    unittest.main()
