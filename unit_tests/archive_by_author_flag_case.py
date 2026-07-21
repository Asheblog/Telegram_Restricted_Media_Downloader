# coding=UTF-8
import sys
import tempfile
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


class ArchiveByAuthorFlagCase(unittest.TestCase):
    def test_forward_rule_round_trip_archive_by_author(self):
        from module.util import make_forward_watch_rule, parse_forward_watch_rule

        rule = make_forward_watch_rule(
            'https://t.me/a',
            'https://t.me/b',
            include_comment=True,
            resolve_deep_link=False,
            archive_by_author=True,
        )
        self.assertIn('--archive-by-author', rule)
        parsed = parse_forward_watch_rule(rule)
        self.assertTrue(parsed['archive_by_author'])
        self.assertTrue(parsed['include_comment'])
        self.assertFalse(parsed['resolve_deep_link'])

    def test_archive_default_flat_opt_in_nests_author(self):
        from module.source_folders import UNKNOWN_AUTHOR_FOLDER, archive_source_folder

        caption = '标题一行\n作者：#示例作者\n正文'
        message = SimpleNamespace(
            id=100,
            caption=caption,
            text=None,
            web_page=None,
            video=None,
            document=None,
            chat=SimpleNamespace(username='demochan'),
            link='https://t.me/demochan/100',
        )
        self.assertEqual(
            'demochan/100 - 标题一行',
            archive_source_folder(message),
        )
        self.assertEqual(
            'demochan/示例作者/100 - 标题一行',
            archive_source_folder(message, archive_by_author=True),
        )
        self.assertEqual(
            f'demochan/{UNKNOWN_AUTHOR_FOLDER}/101 - #tag #only',
            archive_source_folder(
                SimpleNamespace(
                    id=101,
                    caption='#tag #only',
                    text=None,
                    web_page=None,
                    video=None,
                    document=None,
                    chat=SimpleNamespace(username='demochan'),
                    link='https://t.me/demochan/101',
                ),
                archive_by_author=True,
            ),
        )

    def test_archive_pikpak_item_honours_explicit_flag_without_task(self):
        from module.pikpak_integration import PikpakIntegrationManager

        archive_folders = []

        class FakeArchive:
            def archive_file(self, source_folder, **kwargs):
                archive_folders.append(source_folder)
                return SimpleNamespace(
                    ok=True,
                    status='moved',
                    archive_path=f'Telegram/{source_folder}/video.mp4',
                    message='',
                )

        manager = PikpakIntegrationManager(
            transfer_store_getter=lambda: None,
            pikpak_archive_client_getter=lambda: FakeArchive(),
            diagnostic=SimpleNamespace(info=lambda m: None, warning=lambda m: None),
            gc_getter=lambda: None,
            refresh_counts=lambda tid: None,
        )
        message = SimpleNamespace(
            id=100,
            caption='标题一行\n作者：#示例作者\n正文',
            text=None,
            web_page=None,
            video=SimpleNamespace(file_size=10, file_name='video.mp4'),
            document=None,
            chat=SimpleNamespace(username='demochan'),
            link='https://t.me/demochan/100',
        )

        # Listen-forward archive passes the watch flag explicitly (task_id=None).
        result = manager.archive_pikpak_item(
            target_profile='pikpak',
            item_id=None,
            task_id=None,
            message=message,
            source_link='https://t.me/demochan/100',
            source_folder='demochan/100 - 标题一行',
            transferred_at=1.0,
            archive_by_author=True,
        )
        self.assertTrue(result.ok)
        self.assertEqual(['demochan/示例作者/100 - 标题一行'], archive_folders)

    def test_task_and_watch_persist_archive_by_author(self):
        from module.persistence.transfer_store import TransferStore

        directory = tempfile.mkdtemp()
        store = TransferStore(directory)
        try:
            task_id = store.create_task(
                source_link='https://t.me/demochan',
                archive_by_author=True,
            )
            task = store.get_task(task_id)
            self.assertTrue(task['archive_by_author'])

            watch = store.upsert_live_transfer_watch(
                watch_id='forward:https://t.me/a https://t.me/b --archive-by-author',
                watch_type='forward',
                source_link='https://t.me/a',
                target_link='https://t.me/b',
                archive_by_author=True,
            )
            loaded = store.get_live_transfer_watch(watch['id'])
            self.assertTrue(loaded['archive_by_author'])

            plain_id = store.create_task(source_link='https://t.me/other')
            plain = store.get_task(plain_id)
            self.assertFalse(plain['archive_by_author'])
        finally:
            conn = getattr(getattr(store, '_tls', None), 'conn', None)
            if conn is not None:
                conn.close()
                store._tls.conn = None


if __name__ == '__main__':
    unittest.main()
