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

    def test_cancel_running_invokes_callback_and_stops_inflight(self):
        cancelled_ids = []
        started = asyncio.Event()
        release = asyncio.Event()

        async def slow_executor(capture):
            started.set()
            await release.wait()
            self.executed.append(capture)

        self.scheduler = CommentDelayScheduler(
            store=self.store,
            delay_minutes_getter=self.gc.get_comment_delay_minutes,
            executor=slow_executor,
            sleep_seconds=0.01,
            time_fn=time.time,
            on_cancel=lambda capture: cancelled_ids.append(int(capture['id'])),
            running_timeout_seconds=1800,
        )
        row = self.store.schedule_deferred_discussion_capture(
            watch_id='forward:a->b',
            source_chat_id='-1001',
            source_message_id=12,
            target_chat_id='-1002',
            target_link='https://t.me/b',
            due_at=time.time() - 1,
        )

        async def run():
            tick = asyncio.create_task(self.scheduler.tick_once())
            await asyncio.wait_for(started.wait(), timeout=1)
            self.assertTrue(self.scheduler.cancel(row['id']))
            release.set()
            await tick
            fetched = self.store.get_deferred_discussion_capture(row['id'])
            self.assertEqual(DeferredDiscussionCaptureStatus.CANCELLED, fetched['status'])
            self.assertEqual([row['id']], cancelled_ids)
            self.assertEqual(0, len(self.executed))

        asyncio.run(run())

    def test_retry_requeues_cancelled_and_runs(self):
        row = self.store.schedule_deferred_discussion_capture(
            watch_id='forward:a->b',
            source_chat_id='-1001',
            source_message_id=13,
            target_chat_id='-1002',
            target_link='https://t.me/b',
            due_at=time.time() + 3600,
        )
        self.scheduler.cancel(row['id'])

        async def run():
            ok = await self.scheduler.retry(row['id'])
            self.assertTrue(ok)
            fetched = self.store.get_deferred_discussion_capture(row['id'])
            self.assertEqual(DeferredDiscussionCaptureStatus.DONE, fetched['status'])
            self.assertEqual(1, len(self.executed))

        asyncio.run(run())

    def test_tick_fails_stale_running(self):
        row = self.store.schedule_deferred_discussion_capture(
            watch_id='forward:a->b',
            source_chat_id='-1001',
            source_message_id=14,
            target_chat_id='-1002',
            target_link='https://t.me/b',
            due_at=time.time() - 1,
        )
        self.store.claim_due_deferred_discussion_captures(now=time.time())
        with self.store.connect() as conn:
            conn.execute(
                'UPDATE deferred_discussion_captures SET updated_at = ? WHERE id = ?',
                ('2020-01-01T00:00:00+00:00', row['id']),
            )
        self.scheduler.running_timeout_seconds = 60

        async def run():
            await self.scheduler.tick_once()
            fetched = self.store.get_deferred_discussion_capture(row['id'])
            self.assertEqual(DeferredDiscussionCaptureStatus.FAILURE, fetched['status'])
            self.assertEqual(0, len(self.executed))

        asyncio.run(run())


if __name__ == '__main__':
    unittest.main()
