# coding=UTF-8
import sys
import tempfile
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub
install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.persistence.transfer_store import TransferStore, TransferStatus
sys.argv = _ORIGINAL_ARGV


class TransferStorePendingRefreshCase(unittest.TestCase):
    def test_refresh_keeps_pending_queued_task_status(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.RUNNING)
            store.add_item(
                task_id=task_id,
                source_chat_id=1,
                source_message_id=1,
                source_link='https://t.me/source/1',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.SUCCESS,
            )
            store.update_task(task_id, status=TransferStatus.PENDING)

            store.refresh_task_counts(task_id, expected_total=10, assignment_completed=False)

            self.assertEqual(TransferStatus.PENDING, store.get_task(task_id)['status'])


if __name__ == '__main__':
    unittest.main()
