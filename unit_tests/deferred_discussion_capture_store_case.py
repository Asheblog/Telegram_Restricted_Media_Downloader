# coding=UTF-8
import sys
import tempfile
import time
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.transfer_store import TransferStore
sys.argv = _ORIGINAL_ARGV


class DeferredDiscussionCaptureStoreCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = TransferStore(directory=self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _schedule(self, **overrides):
        payload = {
            'watch_id': 'forward:https://t.me/a->https://t.me/b',
            'source_chat_id': '-1001',
            'source_message_id': 42,
            'target_chat_id': '-1002',
            'target_link': 'https://t.me/b',
            'due_at': time.time() + 1200,
        }
        payload.update(overrides)
        return self.store.schedule_deferred_discussion_capture(**payload)

    def test_schedule_creates_pending_row(self):
        row = self._schedule()
        self.assertIsNotNone(row['id'])
        self.assertEqual('pending', row['status'])
        self.assertEqual(42, row['source_message_id'])
        self.assertEqual('-1001', str(row['source_chat_id']))

    def test_schedule_same_key_keeps_existing_pending(self):
        first = self._schedule(due_at=1000.0)
        second = self._schedule(due_at=2000.0)
        self.assertEqual(first['id'], second['id'])
        self.assertEqual(1000.0, float(second['due_at']))

    def test_claim_due_marks_running(self):
        self._schedule(due_at=time.time() - 1)
        claimed = self.store.claim_due_deferred_discussion_captures(now=time.time())
        self.assertEqual(1, len(claimed))
        self.assertEqual('running', claimed[0]['status'])
        again = self.store.claim_due_deferred_discussion_captures(now=time.time())
        self.assertEqual(0, len(again))

    def test_cancel_for_watch_only_pending(self):
        pending = self._schedule(source_message_id=1, due_at=time.time() + 60)
        due = self._schedule(source_message_id=2, due_at=time.time() - 1)
        claimed = self.store.claim_due_deferred_discussion_captures(now=time.time())
        self.assertEqual(1, len(claimed))
        cancelled = self.store.cancel_deferred_discussion_captures_for_watch(pending['watch_id'])
        self.assertEqual(1, cancelled)
        rows = self.store.list_deferred_discussion_captures(watch_id=pending['watch_id'])
        by_id = {row['id']: row for row in rows}
        self.assertEqual('cancelled', by_id[pending['id']]['status'])
        self.assertEqual('running', by_id[due['id']]['status'])

    def test_cancel_and_mark_done(self):
        row = self._schedule()
        self.assertTrue(self.store.cancel_deferred_discussion_capture(row['id']))
        fetched = self.store.get_deferred_discussion_capture(row['id'])
        self.assertEqual('cancelled', fetched['status'])
        row2 = self._schedule(source_message_id=99)
        self.assertTrue(self.store.mark_deferred_discussion_capture(row2['id'], 'done'))
        fetched2 = self.store.get_deferred_discussion_capture(row2['id'])
        self.assertEqual('done', fetched2['status'])


if __name__ == '__main__':
    unittest.main()
