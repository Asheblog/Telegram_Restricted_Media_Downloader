# coding=UTF-8
import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()


class SourceFolderArchiveCase(unittest.TestCase):
    def test_source_folder_uses_public_channel_username_from_link(self):
        from module.source_folders import source_folder_from_link

        self.assertEqual('ctuxas', source_folder_from_link('https://t.me/ctuxas'))
        self.assertEqual('ctuxas', source_folder_from_link('https://t.me/ctuxas/123?single'))

    def test_source_folder_sanitizes_message_chat_title_for_private_links(self):
        from module.source_folders import source_folder_from_message

        message = SimpleNamespace(
            chat=SimpleNamespace(id=-100123, username=None, title='bad:/name*?'),
            link='https://t.me/c/123/456'
        )

        self.assertEqual('bad__name__', source_folder_from_message(message))

    def test_rclone_archive_creates_folder_and_moves_unique_candidate(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if args[:2] == ['rclone', 'lsjson']:
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps([
                        {
                            'Name': 'video.mp4',
                            'Size': 5,
                            'Path': 'video.mp4',
                            'IsDir': False,
                            'ModTime': '2026-06-26T02:00:00Z'
                        }
                    ]),
                    stderr=''
                )
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        client = RclonePikPakArchiveClient(
            {
                'enable': True,
                'remote': 'pikpak',
                'source_directory': 'My Telegram',
                'root_directory': 'Telegram',
                'poll_seconds': 0,
                'poll_interval_seconds': 0,
                'match_window_seconds': 3600
            },
            runner=fake_runner,
            now=lambda: 1782442800.0
        )

        result = client.archive_file(
            source_folder='ctuxas',
            file_name='video.mp4',
            file_size=5,
            transferred_at=1782439200.0
        )

        self.assertTrue(result.ok)
        self.assertEqual('Telegram/ctuxas/video.mp4', result.archive_path)
        self.assertIn(['rclone', 'mkdir', 'pikpak:Telegram/ctuxas'], calls)
        self.assertIn(['rclone', 'lsjson', 'pikpak:My Telegram', '--recursive', '--files-only'], calls)
        self.assertIn(
            ['rclone', 'moveto', 'pikpak:My Telegram/video.mp4', 'pikpak:Telegram/ctuxas/video.mp4'],
            calls
        )

    def test_rclone_archive_can_prepare_source_folder_without_file_metadata(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        client = RclonePikPakArchiveClient(
            {'enable': True, 'remote': 'pikpak', 'root_directory': 'Telegram'},
            runner=fake_runner
        )

        result = client.ensure_source_folder('ctuxas')

        self.assertTrue(result.ok)
        self.assertEqual('folder_ready', result.status)
        self.assertEqual('Telegram/ctuxas', result.archive_path)
        self.assertEqual([['rclone', 'mkdir', 'pikpak:Telegram/ctuxas']], calls)

    def test_rclone_archive_does_not_move_ambiguous_candidates(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if args[:2] == ['rclone', 'lsjson']:
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps([
                        {'Name': 'video.mp4', 'Size': 5, 'Path': 'video.mp4', 'IsDir': False},
                        {'Name': 'video.mp4', 'Size': 5, 'Path': 'copy/video.mp4', 'IsDir': False}
                    ]),
                    stderr=''
                )
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        client = RclonePikPakArchiveClient(
            {'enable': True, 'remote': 'pikpak', 'root_directory': 'Telegram'},
            runner=fake_runner
        )

        result = client.archive_file('ctuxas', 'video.mp4', 5)

        self.assertFalse(result.ok)
        self.assertEqual('ambiguous', result.status)
        self.assertFalse(any(args[1] == 'moveto' for args in calls))

    def test_rclone_archive_can_match_photo_without_file_name_by_size_and_time(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if args[:2] == ['rclone', 'lsjson']:
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps([
                        {
                            'Name': 'photo_2026-06-26.jpg',
                            'Size': 7,
                            'Path': 'photo_2026-06-26.jpg',
                            'IsDir': False,
                            'ModTime': '2026-06-26T02:00:00Z'
                        }
                    ]),
                    stderr=''
                )
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        client = RclonePikPakArchiveClient(
            {
                'enable': True,
                'remote': 'pikpak',
                'source_directory': 'My Telegram',
                'root_directory': 'Telegram',
                'poll_seconds': 0,
                'match_window_seconds': 3600
            },
            runner=fake_runner
        )

        result = client.archive_file(
            source_folder='ctuxas',
            file_name=None,
            file_size=7,
            transferred_at=1782439200.0
        )

        self.assertTrue(result.ok)
        self.assertEqual('Telegram/ctuxas/photo_2026-06-26.jpg', result.archive_path)
        self.assertIn(['rclone', 'lsjson', 'pikpak:My Telegram', '--recursive', '--files-only'], calls)

    def test_rclone_archive_can_rename_tmp_ingest_file_to_desired_name(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if args[:2] == ['rclone', 'lsjson']:
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps([
                        {
                            'Name': 'tmpa0kqz48b.mp4',
                            'Size': 177200000,
                            'Path': 'tmpa0kqz48b.mp4',
                            'IsDir': False,
                            'ModTime': '2026-06-28T14:17:00Z'
                        }
                    ]),
                    stderr=''
                )
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        client = RclonePikPakArchiveClient(
            {
                'enable': True,
                'remote': 'pikpak',
                'source_directory': 'My Telegram',
                'root_directory': 'Telegram',
                'poll_seconds': 0,
                'match_window_seconds': 3600
            },
            runner=fake_runner
        )

        result = client.archive_file(
            source_folder='chengdudiyi8',
            file_name='123 - 文章标题.mp4',
            file_size=177200000,
            transferred_at=1782656220.0,
            match_original_name=False
        )

        self.assertTrue(result.ok)
        self.assertEqual('Telegram/chengdudiyi8/123 - 文章标题.mp4', result.archive_path)
        self.assertIn(
            [
                'rclone',
                'moveto',
                'pikpak:My Telegram/tmpa0kqz48b.mp4',
                'pikpak:Telegram/chengdudiyi8/123 - 文章标题.mp4'
            ],
            calls
        )

    def test_rclone_archive_matches_original_name_by_default(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if args[:2] == ['rclone', 'lsjson']:
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps([
                        {
                            'Name': 'tmpa0kqz48b.mp4',
                            'Size': 177200000,
                            'Path': 'tmpa0kqz48b.mp4',
                            'IsDir': False,
                            'ModTime': '2026-06-28T14:17:00Z'
                        },
                        {
                            'Name': 'video.mp4',
                            'Size': 177200000,
                            'Path': 'video.mp4',
                            'IsDir': False,
                            'ModTime': '2026-06-28T14:17:00Z'
                        }
                    ]),
                    stderr=''
                )
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        client = RclonePikPakArchiveClient(
            {
                'enable': True,
                'remote': 'pikpak',
                'source_directory': 'My Telegram',
                'root_directory': 'Telegram',
                'poll_seconds': 0,
                'match_window_seconds': 3600
            },
            runner=fake_runner
        )

        result = client.archive_file(
            source_folder='ctuxas',
            file_name='video.mp4',
            file_size=177200000,
            transferred_at=1782656220.0
        )

        self.assertTrue(result.ok)
        self.assertEqual('Telegram/ctuxas/video.mp4', result.archive_path)
        self.assertIn(
            [
                'rclone',
                'moveto',
                'pikpak:My Telegram/video.mp4',
                'pikpak:Telegram/ctuxas/video.mp4'
            ],
            calls
        )

    def test_rclone_archive_matches_pikpak_separator_normalized_name(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if args[:2] == ['rclone', 'lsjson']:
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps([
                        {
                            'Name': '198_会所技女技师按摩放松.mp4',
                            'Size': 1001700000,
                            'Path': '198_会所技女技师按摩放松.mp4',
                            'IsDir': False,
                            'ModTime': '2026-07-01T10:44:00Z'
                        }
                    ]),
                    stderr=''
                )
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        client = RclonePikPakArchiveClient(
            {
                'enable': True,
                'remote': 'pikpak',
                'source_directory': 'My Telegram',
                'root_directory': 'Telegram',
                'poll_seconds': 0,
                'match_window_seconds': 3600
            },
            runner=fake_runner
        )

        result = client.archive_file(
            source_folder='ctuxas',
            file_name='198 - 会所技女技师按摩放松.mp4',
            file_size=1001700000,
            transferred_at=1782902640.0,
            match_original_name=True
        )

        self.assertTrue(result.ok)
        self.assertEqual('Telegram/ctuxas/198 - 会所技女技师按摩放松.mp4', result.archive_path)
        self.assertIn(
            [
                'rclone',
                'moveto',
                'pikpak:My Telegram/198_会所技女技师按摩放松.mp4',
                'pikpak:Telegram/ctuxas/198 - 会所技女技师按摩放松.mp4'
            ],
            calls
        )

    def test_rclone_archive_treats_existing_target_file_as_already_archived(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            if args[:2] == ['rclone', 'lsjson'] and args[2] == 'pikpak:My Telegram':
                return SimpleNamespace(returncode=0, stdout=json.dumps([]), stderr='')
            if args[:2] == ['rclone', 'lsjson'] and args[2] == 'pikpak:Telegram/ctuxas':
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps([
                        {
                            'Name': 'video.mp4',
                            'Size': 5,
                            'Path': 'video.mp4',
                            'IsDir': False,
                            'ModTime': '2026-06-26T02:00:00Z'
                        }
                    ]),
                    stderr=''
                )
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        client = RclonePikPakArchiveClient(
            {
                'enable': True,
                'remote': 'pikpak',
                'source_directory': 'My Telegram',
                'root_directory': 'Telegram',
                'poll_seconds': 0,
                'match_window_seconds': 3600
            },
            runner=fake_runner
        )

        result = client.archive_file('ctuxas', 'video.mp4', 5)

        self.assertTrue(result.ok)
        self.assertEqual('already_archived', result.status)
        self.assertEqual('Telegram/ctuxas/video.mp4', result.archive_path)
        self.assertFalse(any(args[1] == 'moveto' for args in calls))

    def test_disabled_archive_is_noop(self):
        from module.pikpak_archive import build_pikpak_archive_client

        client = build_pikpak_archive_client({'enable': False})

        result = client.archive_file('ctuxas', 'video.mp4', 5)

        self.assertFalse(result.ok)
        self.assertEqual('disabled', result.status)

    def test_transfer_items_persist_archive_fields(self):
        from module.transfer_store import TransferStatus, TransferStore

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/ctuxas/1', 'https://t.me/pikpak_bot')
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='ctuxas',
                source_message_id=1,
                source_link='https://t.me/ctuxas/1',
                target_link='https://t.me/pikpak_bot',
                source_folder='ctuxas',
                archive_status='pending',
                archive_match_original_name=False,
                status=TransferStatus.RUNNING
            )

            store.update_item(
                item_id,
                archive_status='success',
                archive_path='Telegram/ctuxas/video.mp4',
                archive_match_original_name=True
            )

            item = store.list_items(task_id)[0]
            self.assertEqual('ctuxas', item['source_folder'])
            self.assertEqual('success', item['archive_status'])
            self.assertEqual('Telegram/ctuxas/video.mp4', item['archive_path'])
            self.assertEqual(1, item['archive_match_original_name'])

    def test_webui_settings_accept_pikpak_archive_config(self):
        from module.web_ui import merge_allowed_settings

        settings = merge_allowed_settings(
            target={'target_profiles': {'pikpak': {'max_file_size': 1}}},
            patch={
                'target_profiles': {
                    'pikpak': {
                        'archive': {
                            'enable': True,
                            'remote': 'pikpak',
                            'root_directory': 'Telegram'
                        }
                    }
                }
            },
            allowed={'target_profiles'}
        )

        self.assertTrue(settings['target_profiles']['pikpak']['archive']['enable'])
        self.assertEqual('pikpak', settings['target_profiles']['pikpak']['archive']['remote'])


if __name__ == '__main__':
    unittest.main()
