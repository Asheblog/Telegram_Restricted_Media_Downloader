# coding=UTF-8
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.app import Application, DownloadFileName
from module.downloader import TelegramRestrictedMediaDownloader
from module.enums import DownloadType


class AppFilenameCase(unittest.TestCase):
    def test_photo_temp_path_prefers_forward_article_title(self):
        app = Application.__new__(Application)
        app.temp_directory = tempfile.mkdtemp()
        message = SimpleNamespace(
            id=12,
            caption='合集标题: 第1集/开场\n1080P',
            chat=SimpleNamespace(id=-1007),
            photo=SimpleNamespace(file_id='photo-file-id', file_unique_id='AQADenglishId')
        )

        with patch('module.app.get_extension', return_value='jpg'):
            path = app.get_temp_file_path(message, DownloadType.PHOTO)

        self.assertEqual(
            os.path.join(app.temp_directory, '-1007', '12 - 合集标题_ 第1集_开场.jpg'),
            path
        )

    def test_video_filename_prefers_text_title_over_random_media_id(self):
        message = SimpleNamespace(
            id=13,
            text='第02话｜真正的标题',
            video=SimpleNamespace(
                file_id='video-file-id',
                file_unique_id='BAADrandomEnglish',
                file_name='video_2026-06-28_12-00-00.mp4',
                mime_type='video/mp4'
            )
        )

        with patch('module.app.get_extension', return_value='mp4'):
            file_name = DownloadFileName(message, DownloadType.VIDEO).get_video_filename()

        self.assertEqual('13 - 第02话｜真正的标题.mp4', file_name)

    def test_document_keeps_compressed_original_name(self):
        message = SimpleNamespace(
            id=14,
            caption='文章标题',
            document=SimpleNamespace(
                file_id='doc-file-id',
                file_unique_id='BQADrandomEnglish',
                file_name='archive.part1.rar',
                mime_type='application/x-rar-compressed'
            )
        )

        file_name = DownloadFileName(message, DownloadType.DOCUMENT).get_document_filename()

        self.assertEqual('archive.part1.rar', file_name)

    def test_media_group_members_inherit_first_caption_title_for_download_name(self):
        app = Application.__new__(Application)
        app.temp_directory = tempfile.mkdtemp()
        app.save_directory = tempfile.mkdtemp()
        first = SimpleNamespace(
            id=21,
            caption='相册文章标题',
            chat=SimpleNamespace(id=-1008),
            photo=SimpleNamespace(file_id='photo-file-id-1', file_unique_id='firstId', file_size=10)
        )
        second = SimpleNamespace(
            id=22,
            caption=None,
            chat=SimpleNamespace(id=-1008),
            photo=SimpleNamespace(file_id='photo-file-id-2', file_unique_id='secondEnglishId', file_size=11)
        )
        TelegramRestrictedMediaDownloader.inherit_media_group_title([first, second])
        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.app = app
        downloader.env_save_directory = lambda message: app.save_directory

        with patch('module.app.get_extension', return_value='jpg'):
            meta = downloader.get_media_meta(second, DownloadType.PHOTO)

        self.assertEqual('22 - 相册文章标题.jpg', meta['file_name'])


if __name__ == '__main__':
    unittest.main()
