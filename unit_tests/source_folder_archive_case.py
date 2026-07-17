# coding=UTF-8
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


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

    def test_archive_source_folder_nests_post_id_and_caption(self):
        from module.source_folders import archive_source_folder

        message = SimpleNamespace(
            id=3404,
            caption='正文标题第一行\n第二行',
            text=None,
            web_page=None,
            video=None,
            document=None,
            chat=SimpleNamespace(id=-1001, username='gokaidanbao', title='x'),
            link='https://t.me/gokaidanbao/3404',
        )

        self.assertEqual(
            'gokaidanbao/3404 - 正文标题第一行',
            archive_source_folder(message),
        )

    def test_archive_source_folder_limits_each_segment_for_linux_filesystems(self):
        from module.source_folders import archive_source_folder, join_local_source_folder

        message = SimpleNamespace(
            id=270,
            caption='很长的中文标题' * 30,
            text=None,
            web_page=None,
            video=None,
            document=None,
            chat=SimpleNamespace(id=-1001, username='long_titles', title='x'),
            link='https://t.me/long_titles/270',
        )

        source_folder = archive_source_folder(message)
        post_segment = source_folder.split('/')[-1]

        self.assertTrue(post_segment.startswith('270 - '))
        self.assertLessEqual(len(post_segment.encode('utf-8')), 230)

        legacy_source_folder = f'long_titles/270 - {"很长的中文标题" * 30}'
        local_path = join_local_source_folder('downloads', legacy_source_folder)
        self.assertTrue(os.path.basename(local_path).startswith('270 - '))
        self.assertLessEqual(len(os.path.basename(local_path).encode('utf-8')), 230)

    def test_archive_prefers_bracket_title_over_leading_hashtags(self):
        from module.source_folders import archive_source_folder, extract_message_body_title

        caption = (
            '#示例 #清纯 #姐姐 #舔逼\n'
            '\n'
            '【60分原创户外】拉着气质姐姐铁路旁裤里丝双洞齐插，晚上又到树林母狗调教\n'
            '#白皮肤 #灰丝加高跟 #露出\n'
            '作者：@会喷水的辛姐姐\n'
        )
        message = SimpleNamespace(
            id=73466,
            caption=caption,
            text=None,
            web_page=None,
            video=SimpleNamespace(file_name='5月13日.mp4', file_id='v1', mime_type='video/mp4'),
            document=None,
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            chat=SimpleNamespace(username='chengdudiyi8'),
            link='https://t.me/chengdudiyi8/73466',
        )

        self.assertEqual(
            '【60分原创户外】拉着气质姐姐铁路旁裤里丝双洞齐插，晚上又到树林母狗调教',
            extract_message_body_title(message),
        )
        self.assertEqual(
            'chengdudiyi8/73466 - 【60分原创户外】拉着气质姐姐铁路旁裤里丝双洞齐插，晚上又到树林母狗调教',
            archive_source_folder(message),
        )

    def test_archive_skips_date_only_and_post_content_label(self):
        from module.source_folders import extract_message_body_title

        message = SimpleNamespace(
            id=73465,
            caption=(
                '帖子内容\n'
                '27. 我姐喝多了，超级狂野，边回答我妈边给我吃鸡巴\n'
                '#示例社区 #乱伦\n'
            ),
            text=None,
            web_page=None,
            video=SimpleNamespace(file_name='5月13日(1).mp4', file_id='v1', mime_type='video/mp4'),
            document=None,
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
        )

        self.assertEqual(
            '27. 我姐喝多了，超级狂野，边回答我妈边给我吃鸡巴',
            extract_message_body_title(message),
        )

    def test_media_group_picks_best_title_not_first_weak_caption(self):
        from module.source_folders import resolve_forward_archive_source_folder

        weak = SimpleNamespace(
            id=73465,
            caption='5月13日',
            text=None,
            web_page=None,
            video=SimpleNamespace(file_name='5月13日.mp4', file_id='v1', mime_type='video/mp4'),
            document=None,
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            chat=SimpleNamespace(username='chengdudiyi8'),
            link='https://t.me/chengdudiyi8/73465',
        )
        strong = SimpleNamespace(
            id=73466,
            caption='#示例 #清纯\n\n【60分原创户外】拉着气质姐姐铁路旁裤里丝双洞齐插\n',
            text=None,
            web_page=None,
            video=SimpleNamespace(file_name='clip.mp4', file_id='v2', mime_type='video/mp4'),
            document=None,
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            chat=SimpleNamespace(username='chengdudiyi8'),
            link='https://t.me/chengdudiyi8/73466',
        )

        self.assertEqual(
            'chengdudiyi8/73465 - 【60分原创户外】拉着气质姐姐铁路旁裤里丝双洞齐插',
            resolve_forward_archive_source_folder(
                source_folder='chengdudiyi8/73465',
                messages=[weak, strong],
                post_message_id=73465,
                fallback_link='https://t.me/chengdudiyi8/73465',
            ),
        )

    def test_media_group_photo_and_video_share_min_id_and_best_title(self):
        from module.source_folders import archive_source_folder_for_messages

        photo = SimpleNamespace(
            id=73464,
            caption=(
                '#示例社区 #乱伦 #姐弟 #野战\n'
                '\n'
                '【60分原创户外】拉着气质姐姐铁路旁裤里丝双洞齐插，晚上又到树林母狗调教\n'
            ),
            text=None,
            web_page=None,
            photo=SimpleNamespace(file_id='p1', file_unique_id='pu1'),
            video=None,
            document=None,
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            media_group_id='album-1',
            chat=SimpleNamespace(username='chengdudiyi8'),
            link='https://t.me/chengdudiyi8/73464',
        )
        video = SimpleNamespace(
            id=73465,
            caption=None,
            text=None,
            web_page=None,
            photo=None,
            video=SimpleNamespace(
                file_name='5月13日.mp4',
                file_id='v1',
                mime_type='video/mp4',
            ),
            document=None,
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            media_group_id='album-1',
            chat=SimpleNamespace(username='chengdudiyi8'),
            link='https://t.me/chengdudiyi8/73465',
        )

        shared = archive_source_folder_for_messages(
            [video, photo],
            fallback_link='https://t.me/chengdudiyi8/73465',
        )
        self.assertEqual(
            'chengdudiyi8/73464 - 【60分原创户外】拉着气质姐姐铁路旁裤里丝双洞齐插，晚上又到树林母狗调教',
            shared,
        )
        # Video-only resolution must not invent a separate date folder when group is known.
        self.assertEqual(
            shared,
            archive_source_folder_for_messages([video, photo]),
        )

    def test_resolve_forward_upgrades_title_but_keeps_existing_post_id(self):
        from module.source_folders import resolve_forward_archive_source_folder

        video = SimpleNamespace(
            id=73469,
            caption=None,
            text=None,
            web_page=None,
            video=SimpleNamespace(file_name='更好的标题正文.mp4', file_id='v1', mime_type='video/mp4'),
            document=None,
            photo=None,
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            chat=SimpleNamespace(username='chengdudiyi8'),
            link='https://t.me/chengdudiyi8/73469',
        )

        self.assertEqual(
            'chengdudiyi8/73464 - 更好的标题正文',
            resolve_forward_archive_source_folder(
                source_folder='chengdudiyi8/73464 - 5月13日',
                messages=[video],
                post_message_id=73469,
                fallback_link='https://t.me/chengdudiyi8/73469',
            ),
        )

    def test_archive_source_folder_falls_back_to_media_file_name_stem(self):
        from module.source_folders import archive_source_folder, post_title_from_message

        message = SimpleNamespace(
            id=88,
            caption=None,
            text=None,
            web_page=None,
            video=None,
            document=SimpleNamespace(
                file_name='#fhheese35 #tag__推特高颜值示例正文.jpg',
                file_id='d1',
                mime_type='image/jpeg',
            ),
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            chat=SimpleNamespace(id=-1001, username='demochan', title='x'),
            link='https://t.me/demochan/88',
        )

        self.assertEqual('#fhheese35 #tag__推特高颜值示例正文', post_title_from_message(message))
        self.assertEqual(
            'demochan/88 - #fhheese35 #tag__推特高颜值示例正文',
            archive_source_folder(message),
        )

    def test_archive_source_folder_strips_leading_id_from_file_name_stem(self):
        from module.source_folders import archive_source_folder

        message = SimpleNamespace(
            id=198,
            caption=None,
            text=None,
            web_page=None,
            document=None,
            video=SimpleNamespace(
                file_name='198_会所技女技师按摩放松.mp4',
                file_id='v1',
                mime_type='video/mp4',
            ),
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            chat=SimpleNamespace(username='ctuxas'),
            link='https://t.me/ctuxas/198',
        )

        self.assertEqual(
            'ctuxas/198 - 会所技女技师按摩放松',
            archive_source_folder(message),
        )

    def test_get_message_media_archive_filename_uses_post_message_id_and_file_name(self):
        from module.adapters.pikpak.integration import PikpakIntegrationManager

        bot_media = SimpleNamespace(
            id=9999,
            caption=None,
            text=None,
            web_page=None,
            video=SimpleNamespace(
                file_name='会所技女技师按摩放松.mp4',
                file_id='v1',
                mime_type='video/mp4',
                file_size=10,
            ),
            document=None,
            photo=None,
            audio=None,
            voice=None,
            animation=None,
            video_note=None,
            sticker=None,
        )

        self.assertEqual(
            '198 - 会所技女技师按摩放松.mp4',
            PikpakIntegrationManager.get_message_media_archive_filename(
                bot_media,
                post_message_id=198,
            ),
        )

    def test_archive_source_folder_from_link_uses_message_id_without_title(self):
        from module.source_folders import archive_source_folder

        self.assertEqual(
            'swag_vip/730',
            archive_source_folder(fallback_link='https://t.me/swag_vip/730'),
        )

    def test_resolve_forward_archive_source_folder_enriches_id_only_path(self):
        from module.source_folders import resolve_forward_archive_source_folder

        trigger = SimpleNamespace(
            id=93670,
            caption=None,
            text=None,
            web_page=None,
            chat=SimpleNamespace(id=-1001, username='chengdudiyi8', title=None),
            link='https://t.me/chengdudiyi8/93670',
            _trmd_source_title='继父出差了妈妈自己在家',
        )

        self.assertEqual(
            'chengdudiyi8/93670 - 继父出差了妈妈自己在家',
            resolve_forward_archive_source_folder(
                source_folder='chengdudiyi8/93670',
                messages=[trigger],
                post_message_id=93670,
                fallback_chat_id=-1001,
                fallback_link='https://t.me/chengdudiyi8/93670',
            ),
        )

    def test_resolve_forward_archive_source_folder_keeps_explicit_channel_folder(self):
        from module.source_folders import resolve_forward_archive_source_folder

        bot_message = SimpleNamespace(
            id=99,
            caption=None,
            text=None,
            web_page=None,
            chat=SimpleNamespace(id='bot-chat', username='a82bot', title=None),
            link=None,
        )

        self.assertEqual(
            'swag_vip',
            resolve_forward_archive_source_folder(
                source_folder='swag_vip',
                messages=[bot_message],
                post_message_id=99,
                fallback_chat_id='bot-chat',
                fallback_link='https://t.me/swag_vip/1',
            ),
        )

    def test_archive_source_folder_for_comment_uses_parent_post(self):
        from module.source_folders import archive_source_folder

        parent = SimpleNamespace(
            id=100,
            caption='主贴资源合集',
            text=None,
            web_page=None,
            chat=SimpleNamespace(username='gokaidanbao'),
            link='https://t.me/gokaidanbao/100',
        )
        comment = SimpleNamespace(
            id=999,
            caption=None,
            text=None,
            chat=SimpleNamespace(id=-200, username='discussion_group'),
        )

        self.assertEqual(
            'gokaidanbao/100 - 主贴资源合集',
            archive_source_folder(
                comment,
                post_message=parent,
                post_message_id=100,
                fallback_chat_id=-1001,
            ),
        )

    def test_rclone_archive_supports_nested_source_folder(self):
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
            source_folder='gokaidanbao/3404 - title',
            file_name='video.mp4',
            file_size=5,
            transferred_at=1782439200.0
        )

        self.assertTrue(result.ok)
        self.assertEqual('Telegram/gokaidanbao/3404 - title/video.mp4', result.archive_path)
        self.assertIn(['rclone', 'mkdir', 'pikpak:Telegram/gokaidanbao/3404 - title'], calls)

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

    def test_rclone_archive_moves_unique_name_match_when_pikpak_size_differs(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        calls = []
        pikpak_name = (
            '6_意大利古典四级_拳王的私生活_#剧情_#意大利四级_#古典四级_'
            '#复古_#大屌_#女友_#颜射_#打屁股_拳王在拳场得意，情场更得意..._'
            '身体保养超好，性能力极强，很多女人投.mp4'
        )
        target_name = (
            '6 - 意大利古典四级- 拳王的私生活 #剧情 #意大利四级 #古典四级 '
            '#复古 #大屌 #女友 #颜射 #打屁股 拳王在拳场得意，情场更得意... '
            '身体保养超好，性能力极强，很多女人投.mp4'
        )

        def fake_runner(args, **kwargs):
            calls.append(args)
            if args[:2] == ['rclone', 'lsjson']:
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps([
                        {
                            'Name': pikpak_name,
                            'Size': 1200000000,
                            'Path': pikpak_name,
                            'IsDir': False,
                            'ModTime': '2026-07-09T05:48:00Z'
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
            source_folder='xxxshare123',
            file_name=target_name,
            file_size=1390000000,
            transferred_at=1783576080.0,
            match_original_name=True
        )

        self.assertTrue(result.ok)
        self.assertEqual(f'Telegram/xxxshare123/{target_name}', result.archive_path)
        self.assertIn(
            [
                'rclone',
                'moveto',
                f'pikpak:My Telegram/{pikpak_name}',
                f'pikpak:Telegram/xxxshare123/{target_name}'
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

    def test_archive_disabled_with_remote_still_allows_ingest(self):
        from module.pikpak_archive import build_pikpak_archive_client

        calls = []

        def runner(args, **kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        client = build_pikpak_archive_client({
            'enable': False,
            'remote': 'pikpak',
            'source_directory': 'My Telegram',
        })
        client.runner = runner
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as handle:
            handle.write(b'hello')
            local_path = handle.name
        try:
            archive = client.archive_file('ctuxas', 'video.mp4', 5)
            ingest = client.upload_to_ingest(local_path, '123 - title.mp4')
        finally:
            os.unlink(local_path)

        self.assertFalse(archive.ok)
        self.assertEqual('disabled', archive.status)
        self.assertTrue(ingest.ok)
        self.assertEqual('uploaded', ingest.status)
        self.assertTrue(any(c[1] == 'copyto' for c in calls))

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

    def test_resolve_poll_seconds_scales_with_large_file_size(self):
        from module.pikpak_archive import RclonePikPakArchiveClient

        client = RclonePikPakArchiveClient({
            'enable': True,
            'remote': 'pikpak',
            'poll_seconds': 60,
            'poll_cap_seconds': 1800,
            'match_window_seconds': 3600
        })

        self.assertEqual(60, client.resolve_poll_seconds(None))
        self.assertEqual(60, client.resolve_poll_seconds(87 * 1024))
        self.assertEqual(1800, client.resolve_poll_seconds(1536 * 1024 ** 2))

    def test_pikpak_upload_archive_retries_not_found_within_match_window(self):
        import asyncio
        import time
        from module.transfer.progress import TransferProgressTracker

        archive_calls = []

        class FakeLoop:
            def is_running(self):
                return True

            def create_task(self, coro):
                asyncio.run(coro)
                return None

        tracker = TransferProgressTracker(
            transfer_store_getter=lambda: None,
            diagnostic=SimpleNamespace(info=lambda m: None, warning=lambda m: None),
            app_getter=lambda: None,
            gc_getter=lambda: SimpleNamespace(config={
                'target_profiles': {
                    'pikpak': {
                        'archive': {
                            'enable': True,
                            'remote': 'pikpak',
                            'archive_retry_interval_seconds': 0,
                            'match_window_seconds': 3600
                        }
                    }
                }
            }),
            loop_getter=lambda: FakeLoop(),
            pb_getter=lambda: None,
            release_storage=lambda *a: None,
            release_window=lambda *a: None,
            start_download_upload=lambda **kw: False,
            archive_pikpak_item=lambda **kw: (
                archive_calls.append(kw) or SimpleNamespace(ok=False, status='not_found', message='missing')
            ),
            fail_transfer_item=lambda *a: None,
            refresh_counts=lambda *a: None,
        )

        transferred_at = time.time()
        tracker._run_upload_archive_now(
            task_id=None,
            item_id=None,
            target_profile='pikpak',
            source_link='https://t.me/ctuxas/1',
            source_folder='ctuxas',
            file_name='video.mp4',
            file_size=5,
            transferred_at=transferred_at,
            match_original_name=False,
            pending_key=None
        )

        self.assertEqual(1, len(archive_calls))

    def test_pikpak_upload_archive_schedules_retry_when_not_found(self):
        import time
        from module.transfer.progress import TransferProgressTracker

        scheduled = []

        tracker = TransferProgressTracker(
            transfer_store_getter=lambda: None,
            diagnostic=SimpleNamespace(info=lambda m: None, warning=lambda m: None),
            app_getter=lambda: None,
            gc_getter=lambda: SimpleNamespace(config={
                'target_profiles': {
                    'pikpak': {
                        'archive': {
                            'enable': True,
                            'remote': 'pikpak',
                            'archive_retry_interval_seconds': 300,
                            'match_window_seconds': 3600
                        }
                    }
                }
            }),
            loop_getter=lambda: None,
            pb_getter=lambda: None,
            release_storage=lambda *a: None,
            release_window=lambda *a: None,
            start_download_upload=lambda **kw: False,
            archive_pikpak_item=lambda **kw: SimpleNamespace(
                ok=False,
                status='not_found',
                message='missing'
            ),
            fail_transfer_item=lambda *a: None,
            refresh_counts=lambda *a: None,
        )
        tracker._schedule_deferred_upload_archive = lambda **kwargs: scheduled.append(kwargs) or True

        transferred_at = time.time()
        tracker._run_upload_archive_now(
            task_id=1,
            item_id=2,
            target_profile='pikpak',
            source_link='https://t.me/ctuxas/1',
            source_folder='ctuxas',
            file_name='video.mp4',
            file_size=5,
            transferred_at=transferred_at,
            match_original_name=False,
            pending_key=None
        )

        self.assertEqual(1, len(scheduled))
        self.assertEqual(300, scheduled[0]['delay_seconds'])
        self.assertTrue(scheduled[0]['reset_archive_status'])

    def test_watch_download_fallback_archive_retries_without_task_id(self):
        """监听下载回退没有 transfer task_id 时，not_found 仍应在匹配窗口内重试。"""
        import time
        from module.transfer.progress import TransferProgressTracker

        scheduled = []
        warnings = []

        tracker = TransferProgressTracker(
            transfer_store_getter=lambda: None,
            diagnostic=SimpleNamespace(
                info=lambda m: None,
                warning=lambda m: warnings.append(m)
            ),
            app_getter=lambda: None,
            gc_getter=lambda: SimpleNamespace(config={
                'target_profiles': {
                    'pikpak': {
                        'archive': {
                            'enable': True,
                            'remote': 'pikpak',
                            'archive_retry_interval_seconds': 300,
                            'match_window_seconds': 3600
                        }
                    }
                }
            }),
            loop_getter=lambda: None,
            pb_getter=lambda: None,
            release_storage=lambda *a: None,
            release_window=lambda *a: None,
            start_download_upload=lambda **kw: False,
            archive_pikpak_item=lambda **kw: SimpleNamespace(
                ok=False,
                status='not_found',
                message='missing'
            ),
            fail_transfer_item=lambda *a: None,
            refresh_counts=lambda *a: None,
        )
        tracker._schedule_deferred_upload_archive = lambda **kwargs: scheduled.append(kwargs) or True

        tracker._run_upload_archive_now(
            task_id=None,
            item_id=None,
            target_profile='pikpak',
            source_link='https://t.me/c/4209310295/5433',
            source_folder='4209310295',
            file_name='video.mp4',
            file_size=5,
            transferred_at=time.time(),
            match_original_name=False,
            pending_key=None
        )

        self.assertEqual(
            1,
            len(scheduled),
            'watch download-fallback archive not_found must retry without task_id'
        )
        self.assertEqual(300, scheduled[0]['delay_seconds'])

    def test_deferred_upload_archive_emits_system_log_on_result(self):
        """下载转存的延迟 rclone 归档结果应写入 system_logs（归档分类）。"""
        import time
        from module.transfer.progress import TransferProgressTracker

        system_logs = []

        tracker = TransferProgressTracker(
            transfer_store_getter=lambda: None,
            diagnostic=SimpleNamespace(info=lambda m: None, warning=lambda m: None),
            app_getter=lambda: None,
            gc_getter=lambda: SimpleNamespace(config={
                'target_profiles': {
                    'pikpak': {
                        'archive': {
                            'enable': True,
                            'remote': 'pikpak',
                            'archive_retry_interval_seconds': 0,
                            'match_window_seconds': 3600
                        }
                    }
                }
            }),
            loop_getter=lambda: None,
            pb_getter=lambda: None,
            release_storage=lambda *a: None,
            release_window=lambda *a: None,
            start_download_upload=lambda **kw: False,
            archive_pikpak_item=lambda **kw: SimpleNamespace(
                ok=True,
                status='success',
                message='',
                archive_path='Telegram/4209310295/video.mp4',
                file_name='video.mp4'
            ),
            fail_transfer_item=lambda *a: None,
            refresh_counts=lambda *a: None,
        )
        tracker._log_system_chain = lambda **kwargs: system_logs.append(kwargs)

        tracker._run_upload_archive_now(
            task_id=None,
            item_id=None,
            target_profile='pikpak',
            source_link='https://t.me/c/4209310295/5433',
            source_folder='4209310295',
            file_name='video.mp4',
            file_size=5,
            transferred_at=time.time(),
            match_original_name=False,
            pending_key=None
        )

        archive_logs = [log for log in system_logs if log.get('category') == 'archive']
        self.assertEqual(
            1,
            len(archive_logs),
            'deferred upload archive must emit archive category system log'
        )
        self.assertEqual('archive_success', archive_logs[0].get('stage'))

    def test_create_task_persists_watch_inline_execution_mode(self):
        from module.transfer_store import TransferStore, ExecutionMode

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/c/4209310295/5433',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
            )
            task = store.get_task(task_id)
            self.assertEqual(ExecutionMode.WATCH_INLINE, task['execution_mode'])

    def test_watch_inline_task_is_not_web_queue_schedulable(self):
        from module.transfer_store import TransferStore, TransferStatus, ExecutionMode
        from module.adapters.webui.task_manager import WebUITaskManager

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/c/4209310295/5433',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
            )
            store.update_task(task_id, status=TransferStatus.RUNNING, started=True)

            manager = object.__new__(WebUITaskManager)
            manager._transfer_store = lambda: store
            self.assertFalse(manager.is_web_transfer_task_schedulable(task_id))

    def test_ensure_download_fallback_transfer_task_marks_single_item_assignment(self):
        from module.transfer_store import TransferStore, ExecutionMode, TransferStatus
        from module.transfer.watch_inline import ensure_download_fallback_transfer_task

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = ensure_download_fallback_transfer_task(
                store=store,
                source_link='https://t.me/c/4209310295/5433',
                target_link='https://t.me/pikpak_bot',
                target_profile='pikpak',
            )
            task = store.get_task(task_id)
            self.assertEqual(ExecutionMode.WATCH_INLINE, task['execution_mode'])
            self.assertEqual(TransferStatus.RUNNING, task['status'])
            self.assertEqual(1, task['total_items'])
            self.assertTrue(bool(task.get('assignment_completed')))


if __name__ == '__main__':
    unittest.main()
