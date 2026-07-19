# coding=UTF-8
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.archive_author_jobs import ArchiveAuthorJobStore, public_job_view
from module.archive_author_tool import ArchiveAuthorReorganizeService
from module.source_folders import UNKNOWN_AUTHOR_FOLDER


class FakeArchiveClient:
    def __init__(self):
        self.config = {
            'remote': 'pikpak',
            'root_directory': 'Telegram',
            'enable': True,
        }
        self.moved = []
        self.list_calls = []

    def list_archive_channel_folders(self):
        return ['chengdudiyi8']

    def list_directories(self, remote_path, *, recursive=False, timeout=None):
        self.list_calls.append((remote_path, recursive))
        path = str(remote_path or '').replace('\\', '/').strip('/')
        if recursive:
            raise AssertionError('author scan must not use recursive lsjson')
        if path.endswith('chengdudiyi8'):
            return [
                '92862 - title-a',
                '92850 - title-b',
                UNKNOWN_AUTHOR_FOLDER,
                '我的羞涩女儿',
            ]
        if path.endswith(UNKNOWN_AUTHOR_FOLDER):
            return ['99999 - unknown']
        if path.endswith('我的羞涩女儿'):
            return ['92840 - nested']
        return []

    def move_directory(self, source, target):
        self.moved.append((source, target))

    def ensure_directory(self, remote_path):
        return remote_path


class ArchiveAuthorProgressCase(unittest.TestCase):
    def test_scan_reports_progress_phases(self):
        events = []

        def on_progress(**kwargs):
            events.append(kwargs)

        client = FakeArchiveClient()
        service = ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=None,
        )
        # Avoid multi-second pacing sleeps in unit tests.
        service._pace = lambda _seconds: None
        plan = service.scan('chengdudiyi8', on_progress=on_progress)
        self.assertGreaterEqual(plan['move_count'], 2)
        phases = [item['phase'] for item in events]
        self.assertIn('listing', phases)
        self.assertIn('planning', phases)
        self.assertIn('done', phases)
        self.assertTrue(any(item.get('message') for item in events))
        self.assertTrue(client.list_calls)
        self.assertTrue(all(not recursive for _path, recursive in client.list_calls))
        from_paths = {item['from_relative'] for item in plan['moves']}
        self.assertIn('92862 - title-a', from_paths)
        self.assertIn(f'{UNKNOWN_AUTHOR_FOLDER}/99999 - unknown', from_paths)
        self.assertIn('我的羞涩女儿/92840 - nested', from_paths)

    def test_resolve_reuses_directory_paths_without_rclone_listing(self):
        from types import SimpleNamespace
        import asyncio

        client = FakeArchiveClient()

        class FakeTelegram:
            def __init__(self):
                self.calls = []

            async def get_messages(self, chat_id=None, message_ids=None, *args, **kwargs):
                ids = message_ids
                if ids is None and args:
                    ids = args[0]
                if not isinstance(ids, list):
                    ids = [ids]
                self.calls.extend(int(x) for x in ids)
                mid = int(ids[0])
                marker = '\u6d77\u89d2\u793e\u533a\u4f5c\u8005\uff1a#我的羞涩女儿'
                return [SimpleNamespace(id=mid, caption=marker, text=None)]

        telegram = FakeTelegram()

        def run_coro(coro, timeout=None):
            return asyncio.run(coro)

        service = ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=telegram,
            run_coro=run_coro,
        )
        service._pace = lambda _seconds: None
        listed = service.scan('chengdudiyi8')
        self.assertTrue(listed.get('directory_paths'))
        list_calls = len(client.list_calls)
        replanned = service.resolve_from_listing(
            'chengdudiyi8',
            directory_paths=listed['directory_paths'],
        )
        self.assertEqual(list_calls, len(client.list_calls))
        self.assertTrue(telegram.calls)
        move_authors = {
            item['author']
            for item in replanned['moves']
            if item['action'] == 'move'
        }
        self.assertIn('我的羞涩女儿', move_authors)

    def test_directory_paths_reconstructed_from_prior_moves(self):
        from module.archive_author_tool import directory_paths_from_plan

        paths = directory_paths_from_plan({
            'channel_folder': 'chengdudiyi8',
            'moves': [
                {'from_relative': '92862 - a'},
                {'from_relative': f'{UNKNOWN_AUTHOR_FOLDER}/99999 - b'},
            ],
        })
        self.assertEqual(
            [
                'chengdudiyi8/92862 - a',
                f'chengdudiyi8/{UNKNOWN_AUTHOR_FOLDER}/99999 - b',
            ],
            paths,
        )


    def test_latest_successful_scan_result_returns_full_plan(self):
        store = ArchiveAuthorJobStore()
        job = store.create(kind='scan', channel_folder='chengdudiyi8')
        store.update(
            job['id'],
            status='success',
            result={'move_count': 3, 'moves': [{'action': 'move'}] * 3},
        )
        plan = store.latest_successful_scan_result('chengdudiyi8')
        self.assertEqual(3, plan['move_count'])
        self.assertEqual(3, len(plan['moves']))

    def test_job_store_tracks_percent_and_truncates_moves(self):
        store = ArchiveAuthorJobStore()
        job = store.create(kind='scan', channel_folder='chengdudiyi8')
        store.update(job['id'], phase='resolving', current=50, total=200, message='halfway')
        view = store.get(job['id'])
        self.assertEqual(25, view['percent'])
        store.update(
            job['id'],
            status='success',
            result={
                'moves': [{'action': 'move', 'from_relative': str(i)} for i in range(250)],
                'move_count': 250,
            },
        )
        public = public_job_view(store.get(job['id']))
        self.assertTrue(public['result']['moves_truncated'])
        self.assertEqual(200, len(public['result']['moves']))
        self.assertEqual(250, public['result']['moves_total'])

    def test_job_store_persists_and_finds_running(self):
        import tempfile
        from module.transfer_store import TransferStore

        directory = tempfile.mkdtemp()
        try:
            transfer_store = TransferStore(directory=directory)
            jobs = ArchiveAuthorJobStore(transfer_store=transfer_store)
            created = jobs.create(kind='scan', channel_folder='chengdudiyi8')
            jobs.update(created['id'], phase='resolving', current=10, total=100, message='go')
            # Force immediate persist path via update already; ensure DB row exists.
            jobs._persist(jobs.get(created['id']), force=True)
            found = jobs.find_running(channel_folder='chengdudiyi8')
            self.assertIsNotNone(found)
            self.assertEqual(created['id'], found['id'])
            reloaded = ArchiveAuthorJobStore(transfer_store=transfer_store)
            stale = reloaded.get(created['id'])
            self.assertEqual('failure', stale['status'])
        finally:
            try:
                import shutil
                shutil.rmtree(directory, ignore_errors=True)
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()
