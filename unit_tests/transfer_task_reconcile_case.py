# coding=UTF-8
import datetime
import sys
import tempfile
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


class TransferTaskReconcileCase(unittest.TestCase):
    def _stale_iso(self, *, seconds: int) -> str:
        return (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=seconds)
        ).isoformat(timespec='seconds')

    def test_refresh_finalizes_assigned_task_when_expected_exceeds_actual_items(self):
        from module.persistence.transfer_store import TransferStore, TransferStatus

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source', 'https://t.me/pikpak_bot')
            store.update_task(
                task_id,
                status=TransferStatus.RUNNING,
                total_items=4000,
                assignment_completed=True,
                started=True,
            )
            for message_id in range(1, 4):
                store.add_item(
                    task_id=task_id,
                    source_message_id=message_id,
                    source_link=f'https://t.me/source/{message_id}',
                    target_link='https://t.me/pikpak_bot',
                    status=TransferStatus.SUCCESS,
                )
            store.add_item(
                task_id=task_id,
                source_message_id=4,
                source_link='https://t.me/source/4',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.FAILURE,
                error_message='timeout',
            )

            store.refresh_task_counts(task_id)

            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.FAILURE, task['status'])
            self.assertIsNotNone(task['finished_at'])
            self.assertEqual(4, task['total_items'])
            self.assertEqual(3, task['completed_items'])
            self.assertEqual(1, task['failed_items'])

    def test_refresh_marks_assigned_empty_task_as_failure(self):
        from module.persistence.transfer_store import TransferStore, TransferStatus

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(
                task_id,
                status=TransferStatus.RUNNING,
                total_items=1,
                assignment_completed=True,
                started=True,
            )

            store.refresh_task_counts(task_id)

            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.FAILURE, task['status'])
            self.assertIsNotNone(task['finished_at'])
            self.assertEqual(0, task['total_items'])

    def test_reconcile_fails_stale_active_items_and_finalizes_task(self):
        from module.persistence.transfer_store import TransferStore, TransferStatus

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.update_task(
                task_id,
                status=TransferStatus.RUNNING,
                total_items=1,
                assignment_completed=True,
                started=True,
            )
            item_id = store.add_item(
                task_id=task_id,
                source_message_id=1,
                source_link='https://t.me/source/1',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.RUNNING,
                phase='downloading',
            )
            stale_at = self._stale_iso(seconds=store.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS + 120)
            with store.connect() as conn:
                conn.execute(
                    'UPDATE transfer_items SET updated_at = ? WHERE id = ?',
                    (stale_at, item_id),
                )

            changed = store.reconcile_active_tasks(force=True)

            self.assertGreaterEqual(changed, 1)
            item = store.get_item(item_id)
            self.assertEqual(TransferStatus.FAILURE, item['status'])
            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.FAILURE, task['status'])
            self.assertIsNotNone(task['finished_at'])

    def test_reconcile_fails_stale_empty_watch_inline_task(self):
        from module.persistence.transfer_store import ExecutionMode, TransferStore, TransferStatus

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source/681',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
                watch_id='forward:https://t.me/source->https://t.me/pikpak_bot',
            )
            store.update_task(
                task_id,
                status=TransferStatus.RUNNING,
                total_items=1,
                assignment_completed=True,
                started=True,
            )
            stale_at = self._stale_iso(
                seconds=store.STALE_EMPTY_WATCH_INLINE_TIMEOUT_SECONDS + 120
            )
            with store.connect() as conn:
                conn.execute(
                    'UPDATE transfer_tasks SET updated_at = ?, started_at = ? WHERE id = ?',
                    (stale_at, stale_at, task_id),
                )

            changed = store.reconcile_active_tasks(force=True)

            self.assertGreaterEqual(changed, 1)
            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.FAILURE, task['status'])
            self.assertIsNotNone(task['finished_at'])
            self.assertIn('timed out', (task.get('error_message') or '').lower())

    def test_watch_download_running_task_can_delete(self):
        from module.adapters.webui.view_model import WebUiViewModel
        from module.persistence.transfer_store import ExecutionMode, TransferStore, TransferStatus

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            watch_id = 'forward:https://t.me/source->https://t.me/pikpak_bot'
            task_id = store.create_task(
                'https://t.me/source/681',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
                watch_id=watch_id,
            )
            store.update_task(
                task_id,
                status=TransferStatus.RUNNING,
                total_items=1,
                assignment_completed=True,
                started=True,
            )
            store.add_item(
                task_id=task_id,
                source_message_id=681,
                source_link='https://t.me/source/681',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.RUNNING,
                phase='downloading',
            )

            payload = WebUiViewModel(store).watch_download_tasks(watch_id)
            model = next(task for task in payload['tasks'] if task['id'] == task_id)
            self.assertTrue(model['can_delete'])
            self.assertFalse(model['can_retry'])

    def test_watch_download_failed_task_can_retry(self):
        from module.adapters.webui.view_model import WebUiViewModel
        from module.persistence.transfer_store import ExecutionMode, TransferStore, TransferStatus

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            watch_id = 'forward:https://t.me/source->https://t.me/pikpak_bot'
            task_id = store.create_task(
                'https://t.me/source/681',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
                watch_id=watch_id,
            )
            store.update_task(
                task_id,
                status=TransferStatus.RUNNING,
                total_items=1,
                assignment_completed=True,
                started=True,
            )
            store.add_item(
                task_id=task_id,
                source_message_id=681,
                source_link='https://t.me/source/681',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.FAILURE,
                error_message='download failed',
            )
            store.refresh_task_counts(task_id)

            payload = WebUiViewModel(store).watch_download_tasks(watch_id)
            model = next(task for task in payload['tasks'] if task['id'] == task_id)
            self.assertTrue(model['can_delete'])
            self.assertTrue(model['can_retry'])


if __name__ == '__main__':
    unittest.main()
