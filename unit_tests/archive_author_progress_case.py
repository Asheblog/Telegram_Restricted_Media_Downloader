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
        self.assertGreaterEqual(len(plan['moves']), 2)
        self.assertGreaterEqual(
            int(plan.get('review_count') or 0) + int(plan.get('move_count') or 0),
            2,
        )
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

    def test_post_author_from_media_group_sibling_caption(self):
        from types import SimpleNamespace
        from module.source_folders import post_author_from_messages

        marker = '\u6d77\u89d2\u793e\u533a\u4f5c\u8005\uff1a#橙色晚空'
        head = SimpleNamespace(id=73464, caption=None, text=None, media_group_id=99)
        sibling = SimpleNamespace(id=73465, caption=marker, text=None, media_group_id=99)
        self.assertEqual('橙色晚空', post_author_from_messages([head, sibling]))

    def test_resolve_logs_miss_samples_via_callback(self):
        from types import SimpleNamespace
        import asyncio

        client = FakeArchiveClient()
        events = []

        class FakeTelegram:
            async def get_messages(self, chat_id=None, message_ids=None, *args, **kwargs):
                ids = message_ids if message_ids is not None else (args[0] if args else None)
                if not isinstance(ids, list):
                    ids = [ids]
                mid = int(ids[0])
                return [SimpleNamespace(
                    id=mid,
                    caption='只有标题没有作者行',
                    text=None,
                    empty=False,
                    media_group_id=None,
                )]

        service = ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=FakeTelegram(),
            run_coro=lambda coro, timeout=None: asyncio.run(coro),
            on_log=lambda **kwargs: events.append(kwargs),
        )
        service._pace = lambda _seconds: None
        plan = service.resolve_from_listing(
            'chengdudiyi8',
            directory_paths=['chengdudiyi8/73464 - demo'],
        )
        self.assertEqual(0, plan.get('resolved_author_count') or 0)
        self.assertTrue(plan.get('miss_samples'))
        self.assertTrue(any(item.get('stage') == 'author_resolve' for item in events))
        self.assertTrue(any(item.get('level') == 'warning' for item in events))

    def test_resolve_uses_media_group_when_primary_has_no_caption(self):
        from types import SimpleNamespace
        import asyncio

        client = FakeArchiveClient()
        marker = '\u6d77\u89d2\u793e\u533a\u4f5c\u8005\uff1a#橙色晚空'

        class FakeTelegram:
            async def get_messages(self, chat_id=None, message_ids=None, *args, **kwargs):
                ids = message_ids if message_ids is not None else (args[0] if args else None)
                if not isinstance(ids, list):
                    ids = [ids]
                mid = int(ids[0])
                msg = SimpleNamespace(
                    id=mid,
                    caption=None,
                    text=None,
                    empty=False,
                    media_group_id=42,
                )

                async def get_media_group():
                    return [
                        msg,
                        SimpleNamespace(
                            id=mid + 1,
                            caption=marker,
                            text=None,
                            media_group_id=42,
                        ),
                    ]

                msg.get_media_group = get_media_group
                return [msg]

        service = ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=FakeTelegram(),
            run_coro=lambda coro, timeout=None: asyncio.run(coro),
        )
        service._pace = lambda _seconds: None
        plan = service.resolve_from_listing(
            'chengdudiyi8',
            directory_paths=['chengdudiyi8/73464 - demo'],
        )
        authors = {item['author'] for item in plan['moves']}
        self.assertIn('橙色晚空', authors)
        self.assertGreaterEqual(plan.get('resolved_author_count') or 0, 1)



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

    def test_job_store_tracks_percent_and_omits_moves_in_public_view(self):
        store = ArchiveAuthorJobStore()
        job = store.create(kind='scan', channel_folder='chengdudiyi8')
        store.update(job['id'], phase='resolving', current=50, total=200, message='halfway')
        view = store.get(job['id'])
        self.assertEqual(25, view['percent'])
        store.update(
            job['id'],
            status='success',
            result={
                'moves': [
                    {'action': 'move', 'from_relative': str(i), 'author': 'A'}
                    for i in range(250)
                ],
                'move_count': 250,
            },
        )
        public = public_job_view(store.get(job['id']))
        self.assertTrue(public['result']['moves_omitted'])
        self.assertEqual([], public['result']['moves'])
        self.assertEqual(250, public['result']['moves_total'])
        self.assertEqual(250, public['result']['summary']['move'])

        from module.archive_author_jobs import list_job_plan_moves
        page = list_job_plan_moves(store.get(job['id']), bucket='move', offset=0, limit=20)
        self.assertEqual(250, page['total'])
        self.assertEqual(20, len(page['items']))

    def test_resolve_hashtag_matches_known_author_folder(self):
        from types import SimpleNamespace
        import asyncio

        client = FakeArchiveClient()

        class FakeTelegram:
            async def get_messages(self, chat_id=None, message_ids=None, *args, **kwargs):
                ids = message_ids if message_ids is not None else (args[0] if args else None)
                if not isinstance(ids, list):
                    ids = [ids]
                mid = int(ids[0])
                if mid == 99:
                    return [SimpleNamespace(
                        id=99,
                        caption='标题 作者：#喷水的姐姐',
                        text=None,
                        empty=False,
                        media_group_id=None,
                        get_media_group=None,
                    )]
                if mid == 100:
                    return [SimpleNamespace(
                        id=100,
                        caption='#海角社区 #会喷水的亲姐姐 【55分原创】正文',
                        text=None,
                        empty=False,
                        media_group_id=None,
                        get_media_group=None,
                    )]
                return [SimpleNamespace(id=mid, caption=None, text=None, empty=True)]

        service = ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=FakeTelegram(),
            run_coro=lambda coro, timeout=None: asyncio.run(coro),
        )
        service._pace = lambda _seconds: None
        plan = service.resolve_from_listing(
            'chengdudiyi8',
            directory_paths=[
                'chengdudiyi8/喷水的姐姐/99 - signed',
                'chengdudiyi8/100 - only tags',
            ],
        )
        by_id = {item['message_id']: item for item in plan['moves']}
        self.assertEqual('skip_already', by_id[99]['action'])
        self.assertEqual('needs_confirm', by_id[100]['action'])
        self.assertEqual('喷水的姐姐', by_id[100]['author'])
        self.assertEqual('hashtag_substring', by_id[100]['resolution_method'])
        self.assertEqual(1, plan.get('confirm_count'))
        self.assertEqual(1, (plan.get('resolve_stats') or {}).get('hashtag_substring_hits'))

    def test_resolve_hashtag_from_media_group_sibling_caption(self):
        """Album caption often sits on a sibling — hashtags must still be collected."""
        from types import SimpleNamespace
        import asyncio

        client = FakeArchiveClient()

        class FakeTelegram:
            async def get_messages(self, chat_id=None, message_ids=None, *args, **kwargs):
                ids = message_ids if message_ids is not None else (args[0] if args else None)
                if not isinstance(ids, list):
                    ids = [ids]
                mid = int(ids[0])
                if mid == 200:
                    # Known author seed via explicit signature.
                    return [SimpleNamespace(
                        id=200,
                        caption='作者：#喷水的姐姐',
                        text=None,
                        empty=False,
                        media_group_id=None,
                        get_media_group=None,
                    )]
                if mid == 201:
                    # Primary album member has no caption; tags live on sibling.
                    primary = SimpleNamespace(
                        id=201,
                        caption=None,
                        text=None,
                        empty=False,
                        media_group_id=77,
                    )

                    async def get_media_group():
                        return [
                            primary,
                            SimpleNamespace(
                                id=202,
                                caption='#海角社区 #会喷水的亲姐姐 【55分原创】正文',
                                text=None,
                                empty=False,
                                media_group_id=77,
                                get_media_group=None,
                            ),
                        ]

                    primary.get_media_group = get_media_group
                    return [primary]
                return [SimpleNamespace(id=mid, caption=None, text=None, empty=True)]

        service = ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=FakeTelegram(),
            run_coro=lambda coro, timeout=None: asyncio.run(coro),
        )
        service._pace = lambda _seconds: None
        plan = service.resolve_from_listing(
            'chengdudiyi8',
            directory_paths=[
                'chengdudiyi8/喷水的姐姐/200 - signed',
                'chengdudiyi8/201 - album tags only',
            ],
        )
        by_id = {item['message_id']: item for item in plan['moves']}
        self.assertEqual('needs_confirm', by_id[201]['action'])
        self.assertEqual('喷水的姐姐', by_id[201]['author'])
        self.assertEqual('hashtag_substring', by_id[201]['resolution_method'])
        self.assertEqual(1, (plan.get('resolve_stats') or {}).get('hashtag_substring_hits'))

    def test_resolve_unresolved_scope_skips_already_recognized(self):
        from types import SimpleNamespace
        import asyncio

        client = FakeArchiveClient()
        fetched = []

        class FakeTelegram:
            async def get_messages(self, chat_id=None, message_ids=None, *args, **kwargs):
                ids = message_ids if message_ids is not None else (args[0] if args else None)
                if not isinstance(ids, list):
                    ids = [ids]
                mid = int(ids[0])
                fetched.append(mid)
                if mid == 301:
                    return [SimpleNamespace(
                        id=301,
                        caption='#海角社区 #会喷水的亲姐姐 正文',
                        text=None,
                        empty=False,
                        media_group_id=None,
                        get_media_group=None,
                    )]
                return [SimpleNamespace(id=mid, caption=None, text=None, empty=True)]

        prior = {
            'channel_folder': 'chengdudiyi8',
            'directory_paths': [
                'chengdudiyi8/300 - known',
                'chengdudiyi8/301 - unknown',
            ],
            'moves': [
                {
                    'message_id': 300,
                    'from_relative': '300 - known',
                    'to_relative': '喷水的姐姐/300 - known',
                    'author': '喷水的姐姐',
                    'action': 'move',
                    'confidence': 'high',
                    'resolution_method': 'signature',
                },
                {
                    'message_id': 301,
                    'from_relative': '301 - unknown',
                    'to_relative': '_未知作者/301 - unknown',
                    'author': '_未知作者',
                    'action': 'needs_review',
                    'confidence': 'none',
                    'resolution_method': 'none',
                },
            ],
        }
        service = ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=FakeTelegram(),
            run_coro=lambda coro, timeout=None: asyncio.run(coro),
        )
        service._pace = lambda _seconds: None
        plan = service.resolve_from_listing(
            'chengdudiyi8',
            directory_paths=prior['directory_paths'],
            prior_plan=prior,
            resolve_scope='unresolved',
        )
        self.assertIn(301, fetched)
        self.assertNotIn(300, fetched)
        self.assertEqual(1, (plan.get('resolve_stats') or {}).get('preserved'))
        self.assertEqual(1, (plan.get('resolve_stats') or {}).get('refetch'))
        by_id = {item['message_id']: item for item in plan['moves']}
        self.assertEqual('喷水的姐姐', by_id[300]['author'])
        self.assertEqual('needs_confirm', by_id[301]['action'])
        self.assertEqual('喷水的姐姐', by_id[301]['author'])

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
            jobs.mark_runner_live(created['id'])
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

    def test_reorganize_job_survives_restart_for_resume(self):
        import tempfile
        from module.transfer_store import TransferStore

        directory = tempfile.mkdtemp()
        try:
            transfer_store = TransferStore(directory=directory)
            jobs = ArchiveAuthorJobStore(transfer_store=transfer_store)
            created = jobs.create(kind='reorganize', channel_folder='chengdudiyi8')
            jobs.update(
                created['id'],
                phase='moving',
                current=126,
                total=3241,
                message='moving',
                result={
                    'checkpoint': True,
                    'completed_from_relatives': ['1 - a', '2 - b'],
                    'execute_mode': 'all',
                },
            )
            jobs._persist(jobs.get(created['id']), force=True)
            reloaded = ArchiveAuthorJobStore(transfer_store=transfer_store)
            row = reloaded.get(created['id'])
            self.assertEqual('running', row['status'])
            resumable = reloaded.find_resumable_reorganize(channel_folder='chengdudiyi8')
            self.assertIsNotNone(resumable)
            self.assertEqual(created['id'], resumable['id'])
            from module.archive_author_jobs import completed_keys_from_job
            self.assertEqual({'1 - a', '2 - b'}, completed_keys_from_job(resumable))
        finally:
            try:
                import shutil
                shutil.rmtree(directory, ignore_errors=True)
            except Exception:
                pass

    def test_execute_plan_skips_already_moved_and_honors_stop(self):
        class StatefulClient(FakeArchiveClient):
            def __init__(self):
                super().__init__()
                self.dirs = {
                    'Telegram/chengdudiyi8': {'100 - a', '101 - b', '102 - c'},
                    'Telegram/chengdudiyi8/作者甲': set(),
                }

            def list_directories(self, remote_path, *, recursive=False, timeout=None):
                path = str(remote_path or '').replace('\\', '/').strip('/')
                return sorted(self.dirs.get(path, set()))

            def ensure_directory(self, remote_path):
                path = str(remote_path or '').replace('\\', '/').strip('/')
                self.dirs.setdefault(path, set())
                return path

            def move_directory(self, source, target):
                source = str(source or '').replace('\\', '/').strip('/')
                target = str(target or '').replace('\\', '/').strip('/')
                parent_s, _, leaf_s = source.rpartition('/')
                parent_t, _, leaf_t = target.rpartition('/')
                if leaf_s not in self.dirs.get(parent_s, set()):
                    raise RuntimeError('source missing')
                self.dirs[parent_s].discard(leaf_s)
                self.dirs.setdefault(parent_t, set()).add(leaf_t)
                self.moved.append((source, target))

        client = StatefulClient()
        # Pretend first item already moved.
        client.dirs['Telegram/chengdudiyi8'].discard('100 - a')
        client.dirs['Telegram/chengdudiyi8/作者甲'].add('100 - a')
        service = ArchiveAuthorReorganizeService(archive_client=client)
        service._pace = lambda _seconds: None
        checkpoints = []

        def should_stop():
            return len(client.moved) >= 1

        def on_checkpoint(**kwargs):
            checkpoints.append(kwargs)

        plan = {
            'channel_folder': 'chengdudiyi8',
            'channel_remote_root': 'Telegram/chengdudiyi8',
            'moves': [
                {
                    'message_id': 100,
                    'from_relative': '100 - a',
                    'to_relative': '作者甲/100 - a',
                    'author': '作者甲',
                    'action': 'move',
                },
                {
                    'message_id': 101,
                    'from_relative': '101 - b',
                    'to_relative': '作者甲/101 - b',
                    'author': '作者甲',
                    'action': 'move',
                },
                {
                    'message_id': 102,
                    'from_relative': '102 - c',
                    'to_relative': '作者甲/102 - c',
                    'author': '作者甲',
                    'action': 'move',
                },
            ],
        }
        result = service.execute_plan(
            plan,
            execute_mode='all',
            should_stop=should_stop,
            on_checkpoint=on_checkpoint,
        )
        self.assertTrue(result.get('stopped'))
        self.assertEqual(1, result.get('skipped_already_count'))
        self.assertEqual(1, result.get('moved_count'))
        self.assertIn('100 - a', result.get('completed_from_relatives') or [])
        self.assertIn('101 - b', result.get('completed_from_relatives') or [])
        self.assertNotIn('102 - c', result.get('completed_from_relatives') or [])
        self.assertTrue(checkpoints)

    def test_execute_plan_resumes_from_completed_keys(self):
        class StatefulClient(FakeArchiveClient):
            def __init__(self):
                super().__init__()
                self.dirs = {
                    'Telegram/chengdudiyi8': {'200 - x', '201 - y'},
                    'Telegram/chengdudiyi8/作者乙': set(),
                }

            def list_directories(self, remote_path, *, recursive=False, timeout=None):
                path = str(remote_path or '').replace('\\', '/').strip('/')
                return sorted(self.dirs.get(path, set()))

            def ensure_directory(self, remote_path):
                path = str(remote_path or '').replace('\\', '/').strip('/')
                self.dirs.setdefault(path, set())
                return path

            def move_directory(self, source, target):
                source = str(source or '').replace('\\', '/').strip('/')
                target = str(target or '').replace('\\', '/').strip('/')
                parent_s, _, leaf_s = source.rpartition('/')
                parent_t, _, leaf_t = target.rpartition('/')
                self.dirs[parent_s].discard(leaf_s)
                self.dirs.setdefault(parent_t, set()).add(leaf_t)
                self.moved.append((source, target))

        client = StatefulClient()
        service = ArchiveAuthorReorganizeService(archive_client=client)
        service._pace = lambda _seconds: None
        plan = {
            'channel_folder': 'chengdudiyi8',
            'channel_remote_root': 'Telegram/chengdudiyi8',
            'moves': [
                {
                    'message_id': 200,
                    'from_relative': '200 - x',
                    'to_relative': '作者乙/200 - x',
                    'author': '作者乙',
                    'action': 'move',
                },
                {
                    'message_id': 201,
                    'from_relative': '201 - y',
                    'to_relative': '作者乙/201 - y',
                    'author': '作者乙',
                    'action': 'move',
                },
            ],
        }
        result = service.execute_plan(
            plan,
            completed_keys={'200 - x'},
        )
        self.assertFalse(result.get('stopped'))
        self.assertEqual(1, result.get('moved_count'))
        self.assertEqual(1, result.get('skipped_already_count'))
        self.assertEqual(
            [('Telegram/chengdudiyi8/201 - y', 'Telegram/chengdudiyi8/作者乙/201 - y')],
            client.moved,
        )

    def test_pace_defaults_are_faster_but_serial(self):
        from module.archive_author_tool import (
            RCLONE_LIST_PAUSE_SECONDS,
            RCLONE_MOVE_PAUSE_SECONDS,
        )
        self.assertLessEqual(RCLONE_MOVE_PAUSE_SECONDS, 1.0)
        self.assertGreaterEqual(RCLONE_MOVE_PAUSE_SECONDS, 0.5)
        self.assertLessEqual(RCLONE_LIST_PAUSE_SECONDS, 1.0)
