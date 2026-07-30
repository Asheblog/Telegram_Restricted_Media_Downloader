# coding=UTF-8
"""Per-watch comment delay override: store, scheduler, normalize."""
import asyncio
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.transfer.comment_delay import (
    CommentDelayScheduler,
    normalize_optional_comment_delay_minutes,
)
from module.transfer_store import TransferStore
sys.argv = _ORIGINAL_ARGV


class NormalizeCommentDelayCase(unittest.TestCase):
    def test_empty_means_inherit(self):
        self.assertIsNone(normalize_optional_comment_delay_minutes(None))
        self.assertIsNone(normalize_optional_comment_delay_minutes(''))
        self.assertIsNone(normalize_optional_comment_delay_minutes('  '))

    def test_valid_override(self):
        self.assertEqual(0, normalize_optional_comment_delay_minutes(0))
        self.assertEqual(120, normalize_optional_comment_delay_minutes('120'))
        self.assertEqual(1440, normalize_optional_comment_delay_minutes(1440))

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            normalize_optional_comment_delay_minutes(-1)
        with self.assertRaises(ValueError):
            normalize_optional_comment_delay_minutes(1441)
        with self.assertRaises(ValueError):
            normalize_optional_comment_delay_minutes('abc')


class WatchCommentDelayStoreCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.store = TransferStore(directory=self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_persist_null_inherits_and_override_round_trip(self):
        plain = self.store.upsert_live_transfer_watch(
            watch_id='forward:a->b',
            watch_type='forward',
            source_link='https://t.me/a',
            target_link='https://t.me/b',
            include_comment=True,
        )
        self.assertIsNone(plain.get('comment_delay_minutes'))

        overridden = self.store.upsert_live_transfer_watch(
            watch_id='forward:a->b',
            watch_type='forward',
            source_link='https://t.me/a',
            target_link='https://t.me/b',
            include_comment=True,
            comment_delay_minutes=120,
        )
        self.assertEqual(120, overridden['comment_delay_minutes'])
        loaded = self.store.get_live_transfer_watch('forward:a->b')
        self.assertEqual(120, loaded['comment_delay_minutes'])

        cleared = self.store.upsert_live_transfer_watch(
            watch_id='forward:a->b',
            watch_type='forward',
            source_link='https://t.me/a',
            target_link='https://t.me/b',
            include_comment=True,
            comment_delay_minutes=None,
        )
        self.assertIsNone(cleared['comment_delay_minutes'])


class WatchCommentDelaySchedulerCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.store = TransferStore(directory=self._tmpdir.name)
        self.executed = []
        self.fixed_now = 1_700_000_000.0

        async def executor(capture):
            self.executed.append(capture)
            return 1

        self.scheduler = CommentDelayScheduler(
            store=self.store,
            delay_minutes_getter=lambda: 20,
            executor=executor,
            sleep_seconds=0.01,
            time_fn=lambda: self.fixed_now,
        )

    def tearDown(self):
        self.scheduler.stop()
        self._tmpdir.cleanup()

    def test_schedule_inherits_global_when_watch_has_no_override(self):
        self.store.upsert_live_transfer_watch(
            watch_id='forward:a->b',
            watch_type='forward',
            source_link='https://t.me/a',
            target_link='https://t.me/b',
            include_comment=True,
        )

        async def run():
            result = await self.scheduler.schedule(
                watch_id='forward:a->b',
                source_chat_id='-1001',
                source_message_id=1,
                target_chat_id='-1002',
                target_link='https://t.me/b',
            )
            self.assertIsNotNone(result)
            self.assertEqual(self.fixed_now + 20 * 60, result['due_at'])
            self.assertEqual(0, len(self.executed))

        asyncio.run(run())

    def test_schedule_uses_watch_override(self):
        self.store.upsert_live_transfer_watch(
            watch_id='forward:slow',
            watch_type='forward',
            source_link='https://t.me/slow',
            target_link='https://t.me/b',
            include_comment=True,
            comment_delay_minutes=120,
        )

        async def run():
            result = await self.scheduler.schedule(
                watch_id='forward:slow',
                source_chat_id='-1001',
                source_message_id=2,
                target_chat_id='-1002',
                target_link='https://t.me/b',
            )
            self.assertIsNotNone(result)
            self.assertEqual(self.fixed_now + 120 * 60, result['due_at'])

        asyncio.run(run())

    def test_watch_override_zero_executes_immediately(self):
        self.store.upsert_live_transfer_watch(
            watch_id='forward:now',
            watch_type='forward',
            source_link='https://t.me/now',
            target_link='https://t.me/b',
            include_comment=True,
            comment_delay_minutes=0,
        )

        async def run():
            result = await self.scheduler.schedule(
                watch_id='forward:now',
                source_chat_id='-1001',
                source_message_id=3,
                target_chat_id='-1002',
                target_link='https://t.me/b',
            )
            self.assertIsNone(result)
            self.assertEqual(1, len(self.executed))

        asyncio.run(run())


if __name__ == '__main__':
    unittest.main()
