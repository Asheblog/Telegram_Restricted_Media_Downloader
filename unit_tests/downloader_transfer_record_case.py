# coding=UTF-8
import os
import sys
import asyncio
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.downloader import TelegramRestrictedMediaDownloader
from module.transfer_store import TransferStore
from module.local_storage_guard import LocalStorageGuard
from module.enums import UploadStatus
from module.task import DownloadTask


class DownloaderTransferRecordCase(unittest.TestCase):
    def test_download_upload_waits_for_local_storage_capacity_before_download(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as directory:
                calls = []
                releases = {}
                free_space = {'value': 200}
                downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
                downloader.transfer_store = None
                downloader.gc = SimpleNamespace(upload_delete=False)
                downloader.local_storage_guard = LocalStorageGuard(
                    free_space_provider=lambda _path: free_space['value'],
                    reserve_bytes_provider=lambda: 50
                )
                first_release = await downloader.local_storage_guard.acquire('existing', directory, 90)
                downloader.local_storage_guard.mark_materialized('existing')
                free_space['value'] = 10
                downloader.download_upload_window = SimpleNamespace(acquire=lambda: None)
                downloader.app = SimpleNamespace(
                    current_task_num=0,
                    max_download_task=1,
                    download_type=['video'],
                    client=SimpleNamespace(me=SimpleNamespace(is_premium=True)),
                    save_directory=directory,
                    get_file_type=lambda *args, **kwargs: 'video'
                )
                downloader.event = SimpleNamespace(wait=lambda: None, clear=lambda: None, set=lambda: None)
                downloader.pb = SimpleNamespace(progress=SimpleNamespace(add_task=lambda *args, **kwargs: 1))
                downloader.loop = asyncio.get_running_loop()
                downloader.queue = SimpleNamespace(put_nowait=lambda task: None, task_done=lambda: None)
                download_started = asyncio.Event()
                finish_download = asyncio.Event()
                downloader.get_media_meta = lambda message, dtype: {
                    'file_id': 1,
                    'temp_file_path': os.path.join(directory, 'media.mp4.temp'),
                    'sever_file_size': 60,
                    'file_name': 'media.mp4',
                    'save_directory': os.path.join(directory, 'media.mp4'),
                    'format_file_size': '60.00B'
                }
                async def resume_download(*args, **kwargs):
                    calls.append('download')
                    download_started.set()
                    await finish_download.wait()

                downloader.resume_download = resume_download
                downloader.transfer_download_progress = lambda *args, **kwargs: None
                async def acquire_window():
                    releases['window'] = lambda: None
                    return releases['window']
                downloader.download_upload_window.acquire = acquire_window

                message = SimpleNamespace(
                    id=1,
                    link='https://t.me/source/1',
                    chat=SimpleNamespace(id='source-chat'),
                    video=SimpleNamespace(file_size=60, file_name='media.mp4')
                )
                DownloadTask.LINK_INFO.clear()
                DownloadTask(
                    link='https://t.me/source/1',
                    link_type='single',
                    member_num=1,
                    complete_num=0,
                    file_name=set(),
                    error_msg={}
                )
                task = asyncio.create_task(downloader._TelegramRestrictedMediaDownloader__add_task(
                    chat_id='source-chat',
                    link_type='single',
                    link='https://t.me/source/1',
                    message=message,
                    retry={'id': -1, 'count': 0},
                    with_upload={'link': 'https://t.me/pikpak_bot'},
                    diy_download_type=['video']
                ))
                await asyncio.sleep(0)
                self.assertEqual([], calls)
                free_space['value'] = 200
                first_release()
                await asyncio.wait_for(task, timeout=1)
                await asyncio.wait_for(download_started.wait(), timeout=1)
                self.assertEqual(['download'], calls)
                for pending in list(asyncio.all_tasks()):
                    if pending is not asyncio.current_task() and pending.get_coro().__name__ == 'resume_download':
                        pending.cancel()
                        try:
                            await pending
                        except asyncio.CancelledError:
                            pass

        asyncio.run(run_case())

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

    def test_prepare_download_upload_meta_infers_pikpak_profile_from_target_link(self):
        async def run_case():
            downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
            downloader.gc = SimpleNamespace(upload_delete=False)
            downloader.download_upload_window = SimpleNamespace(acquire=lambda: (lambda: None))

            async def acquire():
                return lambda: None

            downloader.download_upload_window.acquire = acquire

            return await downloader.prepare_download_upload_meta({
                'link': 'https://t.me/pikpak_bot'
            })

        meta = __import__('asyncio').run(run_case())

        self.assertEqual('pikpak', meta['target_profile'])
        self.assertTrue(meta['with_delete'])
        self.assertFalse(meta['send_as_media_group'])
        self.assertIsNotNone(meta.get('failure_callback'))

    def test_download_upload_precheck_blocks_pikpak_file_before_download_when_profile_is_inferred(self):
        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.gc = SimpleNamespace(upload_delete=False)
        downloader.app = SimpleNamespace(client=SimpleNamespace(me=SimpleNamespace(is_premium=True)))

        meta = downloader.normalize_download_upload_meta({
            'link': 'https://t.me/pikpak_bot'
        })
        error = downloader.get_download_upload_size_limit_error(
            task_with_upload=meta,
            file_size=4 * 1024 ** 3 + 1
        )

        self.assertIn('PikPak', error)

    def test_download_upload_precheck_blocks_regular_target_over_telegram_limit(self):
        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.gc = SimpleNamespace(upload_delete=False)
        downloader.app = SimpleNamespace(client=SimpleNamespace(me=SimpleNamespace(is_premium=False)))

        meta = downloader.normalize_download_upload_meta({
            'link': 'https://t.me/target'
        })
        error = downloader.get_download_upload_size_limit_error(
            task_with_upload=meta,
            file_size=2 * 1024 ** 3 + 1
        )

        self.assertEqual('上传大小超过限制(普通用户2000MiB,会员用户4000MiB)', error)

    def test_add_task_skips_pikpak_oversize_before_download_starts(self):
        async def run_case():
            calls = []
            releases = []

            with tempfile.TemporaryDirectory() as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task(
                    source_link='https://t.me/source/1',
                    target_link='https://t.me/pikpak_bot',
                    target_profile='pikpak'
                )

                downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
                downloader.transfer_store = store
                downloader.gc = SimpleNamespace(upload_delete=False)
                downloader.app = SimpleNamespace(
                    current_task_num=0,
                    max_download_task=1,
                    download_type=['video'],
                    client=SimpleNamespace(me=SimpleNamespace(is_premium=True)),
                    save_directory=directory
                )
                downloader.event = SimpleNamespace(wait=lambda: None, clear=lambda: None)
                downloader.pb = SimpleNamespace(
                    progress=SimpleNamespace(add_task=lambda *args, **kwargs: calls.append('progress'))
                )

                async def prepare_download_upload_meta(with_upload):
                    return downloader.normalize_download_upload_meta(with_upload)

                downloader.prepare_download_upload_meta = prepare_download_upload_meta
                downloader.release_download_upload_window = lambda with_upload: releases.append(with_upload)
                downloader.resume_download = lambda *args, **kwargs: calls.append('download')
                downloader.get_media_meta = lambda message, dtype: {
                    'file_id': 1,
                    'temp_file_path': os.path.join(directory, 'large.mp4.temp'),
                    'sever_file_size': 4 * 1024 ** 3 + 1,
                    'file_name': 'large.mp4',
                    'save_directory': os.path.join(directory, 'large.mp4'),
                    'format_file_size': '4.00GB'
                }
                message = SimpleNamespace(
                    id=1,
                    link='https://t.me/source/1',
                    chat=SimpleNamespace(id='source-chat'),
                    video=SimpleNamespace(file_size=4 * 1024 ** 3 + 1, file_name='large.mp4')
                )
                with_upload = {
                    'link': 'https://t.me/pikpak_bot',
                    'task_id': task_id,
                    'source_link': 'https://t.me/source/1'
                }
                DownloadTask.LINK_INFO.clear()
                DownloadTask(
                    link='https://t.me/source/1',
                    link_type='single',
                    member_num=1,
                    complete_num=0,
                    file_name=set(),
                    error_msg={}
                )

                with patch('module.downloader.is_file_duplicate', return_value=False):
                    await downloader._TelegramRestrictedMediaDownloader__add_task(
                        chat_id='source-chat',
                        link_type='single',
                        link='https://t.me/source/1',
                        message=message,
                        retry={'id': -1, 'count': 0},
                        with_upload=with_upload,
                        diy_download_type=['video']
                    )
                return calls, releases, store.list_items(task_id), store.get_task(task_id), store.list_events(task_id)

        calls, releases, items, task, events = __import__('asyncio').run(run_case())

        self.assertEqual([], calls)
        self.assertEqual(1, len(releases))
        self.assertEqual(1, len(items))
        self.assertEqual('skipped', items[0]['phase'])
        self.assertEqual('skipped', items[0]['status'])
        self.assertIn('PikPak', items[0]['error_message'])
        self.assertEqual(1, task['completed_items'])
        self.assertEqual(0, task['failed_items'])
        self.assertTrue(any(event['level'] == 'warning' and 'PikPak' in event['message'] for event in events))


if __name__ == '__main__':
    unittest.main()
