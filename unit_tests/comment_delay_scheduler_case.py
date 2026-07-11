# coding=UTF-8
import asyncio
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.transfer.comment_delay import CommentDelayScheduler
from module.transfer_store import DeferredDiscussionCaptureStatus, TransferStore
sys.argv = _ORIGINAL_ARGV


class CommentDelaySchedulerCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = TransferStore(directory=self._tmpdir.name)
        self.executed = []

        async def executor(capture):
            self.executed.append(capture)
            return 3

        self.gc = SimpleNamespace(get_comment_delay_minutes=lambda: 20)
        self.scheduler = CommentDelayScheduler(
            store=self.store,
            delay_minutes_getter=self.gc.get_comment_delay_minutes,
            executor=executor,
            sleep_seconds=0.01,
            time_fn=time.time,
        )

    def tearDown(self):
        self.scheduler.stop()
        self._tmpdir.cleanup()

    def test_schedule_with_delay_persists_pending(self):
        async def run():
            result = await self.scheduler.schedule(
                watch_id='forward:a->b',
                source_chat_id='-1001',
                source_message_id=7,
                target_chat_id='-1002',
                target_link='https://t.me/b',
                client=None,
            )
            self.assertIsNotNone(result)
            self.assertEqual('pending', result['status'])
            self.assertEqual(0, len(self.executed))
            rows = self.store.list_deferred_discussion_captures(watch_id='forward:a->b')
            self.assertEqual(1, len(rows))
            self.assertGreater(rows[0]['due_at'], time.time())

        asyncio.run(run())

    def test_zero_delay_executes_immediately(self):
        self.scheduler.delay_minutes_getter = lambda: 0

        async def run():
            result = await self.scheduler.schedule(
                watch_id='forward:a->b',
                source_chat_id='-1001',
                source_message_id=8,
                target_chat_id='-1002',
                target_link='https://t.me/b',
                client=None,
            )
            self.assertIsNone(result)
            self.assertEqual(1, len(self.executed))
            self.assertEqual(8, self.executed[0]['source_message_id'])

        asyncio.run(run())

    def test_tick_claims_due_and_marks_done(self):
        row = self.store.schedule_deferred_discussion_capture(
            watch_id='forward:a->b',
            source_chat_id='-1001',
            source_message_id=9,
            target_chat_id='-1002',
            target_link='https://t.me/b',
            due_at=time.time() - 1,
        )

        async def run():
            await self.scheduler.tick_once()
            fetched = self.store.get_deferred_discussion_capture(row['id'])
            self.assertEqual(DeferredDiscussionCaptureStatus.DONE, fetched['status'])
            self.assertEqual(1, len(self.executed))

        asyncio.run(run())

    def test_run_now_and_cancel(self):
        row = self.store.schedule_deferred_discussion_capture(
            watch_id='forward:a->b',
            source_chat_id='-1001',
            source_message_id=10,
            target_chat_id='-1002',
            target_link='https://t.me/b',
            due_at=time.time() + 3600,
        )
        self.assertTrue(self.scheduler.cancel(row['id']))
        self.assertEqual(
            DeferredDiscussionCaptureStatus.CANCELLED,
            self.store.get_deferred_discussion_capture(row['id'])['status']
        )
        row2 = self.store.schedule_deferred_discussion_capture(
            watch_id='forward:a->b',
            source_chat_id='-1001',
            source_message_id=11,
            target_chat_id='-1002',
            target_link='https://t.me/b',
            due_at=time.time() + 3600,
        )

        async def run():
            ok = await self.scheduler.run_now(row2['id'])
            self.assertTrue(ok)
            fetched = self.store.get_deferred_discussion_capture(row2['id'])
            self.assertEqual(DeferredDiscussionCaptureStatus.DONE, fetched['status'])
            self.assertEqual(1, len(self.executed))

        asyncio.run(run())


if __name__ == '__main__':
    unittest.main()
