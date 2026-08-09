# coding=UTF-8
"""PikPak archive target-name dedup: same post media must never overwrite.

Regression for the observed bug where several media files sharing one
``{message_id} - {shared_title}`` archive name were all rclone ``moveto``'d to the
same target path — the last move silently overwrote the earlier ones, leaving a
single file on PikPak while SQLite kept one item (with distinct size) per file.
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.pikpak_archive import RclonePikPakArchiveClient

NOW = 1786284000.0
TRANSFERRED_AT = NOW - 60


class _FakeCompleted:
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _lsjson_items(names_sizes):
    return [
        {
            'Name': name,
            'Path': name,
            'Size': size,
            'IsDir': False,
            'ModTime': '2026-08-09T13:59:00Z',
        }
        for name, size in names_sizes
    ]


class _FakeArchiveRunner:
    """Stateful rclone runner: My Telegram ingest vs archive target dir listings."""

    def __init__(self, ingest_files, target_dir_remote, initial_target=()):
        self.ingest_files = list(ingest_files)  # (name, size)
        self.target_dir_remote = target_dir_remote
        self.target_names = set(initial_target or ())
        self.calls = []
        self.moveto_calls = []

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        command = list(args)
        if len(command) >= 2 and command[1] == 'lsjson':
            remote = command[2]
            flags = command[3:]
            if '--recursive' in flags:
                # My Telegram ingest listing (recursive).
                return _FakeCompleted(
                    stdout=json.dumps(_lsjson_items(self.ingest_files)),
                )
            if remote == self.target_dir_remote:
                # Non-recursive target dir listing (dedup probe).
                return _FakeCompleted(
                    stdout=json.dumps(_lsjson_items(
                        [(name, 1) for name in sorted(self.target_names)]
                    )),
                )
            return _FakeCompleted(stdout='[]')
        if len(command) >= 2 and command[1] == 'mkdir':
            return _FakeCompleted()
        if len(command) >= 2 and command[1] == 'moveto':
            source = command[2]
            target = command[3]
            self.moveto_calls.append((source, target))
            target_name = target.rsplit('/', 1)[-1]
            self.target_names.add(target_name)
            source_name = source.rsplit('/', 1)[-1]
            self.ingest_files = [
                (name, size) for (name, size) in self.ingest_files if name != source_name
            ]
            return _FakeCompleted()
        raise AssertionError(f'unexpected rclone command: {command}')


def _make_client(runner):
    client = RclonePikPakArchiveClient(
        {
            'enable': True,
            'remote': 'pikpak',
            'source_directory': 'My Telegram',
            'root_directory': 'Telegram',
            'poll_seconds': 0,
            'poll_interval_seconds': 0,
            'match_window_seconds': 3600,
        },
        runner=runner,
        now=lambda: NOW,
    )
    return client


class UniqueArchiveTargetNameCase(unittest.TestCase):
    def test_free_name_returns_unchanged(self):
        from module.pikpak_archive import unique_archive_target_name

        self.assertEqual(
            '2509 - title.mp4',
            unique_archive_target_name([], '2509 - title.mp4'),
        )

    def test_occupied_name_gets_parenthesized_suffix(self):
        from module.pikpak_archive import unique_archive_target_name

        existing = ['2509 - title.mp4', '2509 - title (1).mp4', '2509 - title (3).mp4']
        self.assertEqual(
            '2509 - title (2).mp4',
            unique_archive_target_name(existing, '2509 - title.mp4'),
        )

    def test_sequential_same_post_media_get_increasing_suffixes(self):
        from module.pikpak_archive import unique_archive_target_name

        existing = []
        names = []
        for _ in range(5):
            name = unique_archive_target_name(existing, '2509 - title.mp4')
            names.append(name)
            existing.append(name)
        self.assertEqual(5, len(set(names)))
        self.assertEqual(
            [
                '2509 - title.mp4',
                '2509 - title (1).mp4',
                '2509 - title (2).mp4',
                '2509 - title (3).mp4',
                '2509 - title (4).mp4',
            ],
            names,
        )

    def test_explicit_parenthesized_name_kept_when_free(self):
        from module.pikpak_archive import unique_archive_target_name

        self.assertEqual(
            'clip (1).mp4',
            unique_archive_target_name(['clip.mp4'], 'clip (1).mp4'),
        )

    def test_explicit_parenthesized_name_rebased_when_occupied(self):
        from module.pikpak_archive import unique_archive_target_name

        existing = ['clip.mp4', 'clip (1).mp4', 'clip (2).mp4']
        self.assertEqual(
            'clip (3).mp4',
            unique_archive_target_name(existing, 'clip (1).mp4'),
        )

    def test_comparison_is_case_insensitive(self):
        from module.pikpak_archive import unique_archive_target_name

        existing = ['2509 - TITLE.MP4', '2509 - title (1).mp4']
        self.assertEqual(
            '2509 - title (2).mp4',
            unique_archive_target_name(existing, '2509 - title.mp4'),
        )

    def test_different_extension_does_not_collide(self):
        from module.pikpak_archive import unique_archive_target_name

        existing = ['2509 - title.mp4']
        self.assertEqual(
            '2509 - title.jpg',
            unique_archive_target_name(existing, '2509 - title.jpg'),
        )

    def test_ingest_suffix_matches_archived_bare_name(self):
        """PikPak's own ``name (1).ext`` ingest must be deduped against archives."""
        from module.pikpak_archive import unique_archive_target_name

        existing = ['clip.mp4', 'clip (1).mp4']
        self.assertEqual(
            'clip (2).mp4',
            unique_archive_target_name(existing, 'clip (1).mp4'),
        )


class ArchiveFileDedupCase(unittest.TestCase):
    def test_two_same_target_files_get_distinct_moveto_paths(self):
        """Red on the bug: both files used to moveto the exact same target path."""
        runner = _FakeArchiveRunner(
            ingest_files=[('bot_media_0.mp4', 100), ('bot_media_1.mp4', 200)],
            target_dir_remote='pikpak:Telegram/chan/2509 - title',
        )
        client = _make_client(runner)
        shared_name = '2509 - title.mp4'

        first = client.archive_file(
            source_folder='chan/2509 - title',
            file_name=shared_name,
            file_size=100,
            transferred_at=TRANSFERRED_AT,
            match_original_name=False,
        )
        second = client.archive_file(
            source_folder='chan/2509 - title',
            file_name=shared_name,
            file_size=200,
            transferred_at=TRANSFERRED_AT,
            match_original_name=False,
        )

        self.assertTrue(first.ok)
        self.assertTrue(second.ok)
        self.assertEqual(2, len(runner.moveto_calls))
        targets = [target for _, target in runner.moveto_calls]
        self.assertEqual(2, len(set(targets)), targets)
        self.assertIn(
            'pikpak:Telegram/chan/2509 - title/2509 - title.mp4',
            targets,
        )
        self.assertIn(
            'pikpak:Telegram/chan/2509 - title/2509 - title (1).mp4',
            targets,
        )

    def test_concurrent_same_target_archives_do_not_overwrite(self):
        """Both runs see the other's landed file via the target-dir listing."""
        runner = _FakeArchiveRunner(
            ingest_files=[('bot_media_0.mp4', 100), ('bot_media_1.mp4', 200)],
            target_dir_remote='pikpak:Telegram/chan/2509 - title',
        )
        client = _make_client(runner)
        shared_name = '2509 - title.mp4'

        first = client.archive_file(
            source_folder='chan/2509 - title',
            file_name=shared_name,
            file_size=100,
            transferred_at=TRANSFERRED_AT,
            match_original_name=False,
        )
        second = client.archive_file(
            source_folder='chan/2509 - title',
            file_name=shared_name,
            file_size=200,
            transferred_at=TRANSFERRED_AT,
            match_original_name=False,
        )

        self.assertTrue(first.ok)
        self.assertTrue(second.ok)
        self.assertEqual(
            'pikpak:Telegram/chan/2509 - title/2509 - title.mp4',
            runner.moveto_calls[0][1],
        )
        self.assertEqual(
            'pikpak:Telegram/chan/2509 - title/2509 - title (1).mp4',
            runner.moveto_calls[1][1],
        )

    def test_target_listing_and_moveto_hold_dedup_lock(self):
        """The dedup list→moveto decision must be atomic against concurrent archives."""
        runner = _FakeArchiveRunner(
            ingest_files=[('bot_media_0.mp4', 100)],
            target_dir_remote='pikpak:Telegram/chan/2509 - title',
        )
        client = _make_client(runner)
        lock_checks = []

        original_list = client._list_dir_file_names
        original_moveto = client.moveto

        def checked_list(remote_dir):
            lock_checks.append(('list', client._dedup_lock.locked()))
            return original_list(remote_dir)

        def checked_moveto(source_path, target_path):
            lock_checks.append(('moveto', client._dedup_lock.locked()))
            return original_moveto(source_path, target_path)

        client._list_dir_file_names = checked_list
        client.moveto = checked_moveto

        result = client.archive_file(
            source_folder='chan/2509 - title',
            file_name='2509 - title.mp4',
            file_size=100,
            transferred_at=TRANSFERRED_AT,
            match_original_name=False,
        )

        self.assertTrue(result.ok)
        self.assertTrue(lock_checks)
        for stage, held in lock_checks:
            self.assertTrue(held, f'{stage} ran outside the dedup lock')

    def test_bare_name_ignores_unrelated_existing_files(self):
        runner = _FakeArchiveRunner(
            ingest_files=[('bot_media_0.mp4', 100)],
            target_dir_remote='pikpak:Telegram/chan/2509 - title',
            initial_target=('other.mp4',),
        )
        client = _make_client(runner)
        result = client.archive_file(
            source_folder='chan/2509 - title',
            file_name='2509 - title.mp4',
            file_size=100,
            transferred_at=TRANSFERRED_AT,
            match_original_name=False,
        )

        self.assertTrue(result.ok)
        self.assertEqual(1, len(runner.moveto_calls))
        self.assertEqual(
            'pikpak:Telegram/chan/2509 - title/2509 - title.mp4',
            runner.moveto_calls[0][1],
        )


if __name__ == '__main__':
    unittest.main()
