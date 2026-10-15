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

    def test_refresh_keeps_running_when_item_count_exceeds_range_expected_before_assignment_done(self):
        """Deep-link comments can create more items than range message count mid-scan."""
        from module.persistence.transfer_store import TransferStore, TransferStatus

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                start_id=1,
                end_id=10,
            )
            store.update_task(task_id, status=TransferStatus.RUNNING, started=True)
            for message_id in range(1, 12):
                store.add_item(
                    task_id=task_id,
                    source_message_id=message_id,
                    range_message_id=min(message_id, 5),
                    source_link=f'https://t.me/source/{message_id}',
                    target_link='https://t.me/pikpak_bot',
                    status=TransferStatus.SUCCESS,
                )
            store.add_item(
                task_id=task_id,
                source_message_id=99,
                range_message_id=5,
                source_link='https://t.me/source/99',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.FAILURE,
                error_message='deep link failed',
            )

            store.refresh_task_counts(task_id, expected_total=10, assignment_completed=False)

            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.RUNNING, task['status'])
            self.assertIsNone(task['finished_at'])
            self.assertFalse(bool(task['assignment_completed']))
            self.assertEqual(1, task['failed_items'])
            self.assertEqual(11, task['completed_items'])

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

    def test_default_stale_item_timeout_is_five_minutes(self):
        from module.persistence.transfer_store import TransferStore

        self.assertEqual(5 * 60, TransferStore.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS)

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
            self.assertIn('5分钟无进展', item.get('error_message') or '')
            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.FAILURE, task['status'])
            self.assertIsNotNone(task['finished_at'])

    def test_reconcile_uses_item_timeout_getter_minutes(self):
        from module.persistence.transfer_store import TransferStore, TransferStatus

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            store.set_item_stale_timeout_seconds_getter(lambda: 2 * 60)
            task_id = store.create_task('https://t.me/source/2', 'https://t.me/pikpak_bot')
            store.update_task(
                task_id,
                status=TransferStatus.RUNNING,
                total_items=1,
                assignment_completed=True,
                started=True,
            )
            item_id = store.add_item(
                task_id=task_id,
                source_message_id=2,
                source_link='https://t.me/source/2',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.RUNNING,
                phase='forwarding',
            )
            stale_at = self._stale_iso(seconds=2 * 60 + 30)
            with store.connect(run_maintenance=False) as conn:
                conn.execute(
                    'UPDATE transfer_items SET updated_at = ? WHERE id = ?',
                    (stale_at, item_id),
                )

            changed = store.reconcile_active_tasks(force=True)

            self.assertGreaterEqual(changed, 1)
            item = store.get_item(item_id)
            self.assertEqual(TransferStatus.FAILURE, item['status'])
            self.assertIn('2分钟无进展', item.get('error_message') or '')

    def _running_task_with_item(self, store, *, message_id: int = 1, status=None):
        from module.persistence.transfer_store import TransferStatus

        task_id = store.create_task(
            f'https://t.me/source/{message_id}', 'https://t.me/pikpak_bot'
        )
        store.update_task(
            task_id,
            status=TransferStatus.RUNNING,
            total_items=1,
            assignment_completed=True,
            started=True,
        )
        item_id = store.add_item(
            task_id=task_id,
            source_message_id=message_id,
            source_link=f'https://t.me/source/{message_id}',
            target_link='https://t.me/pikpak_bot',
            status=status or TransferStatus.RUNNING,
            phase='uploading',
        )
        return task_id, item_id

    def _age_item(self, store, item_id: int, *, seconds: int) -> None:
        with store.connect(run_maintenance=False) as conn:
            conn.execute(
                'UPDATE transfer_items SET updated_at = ? WHERE id = ?',
                (self._stale_iso(seconds=seconds), item_id),
            )

    def test_reconcile_keeps_leased_item_past_normal_timeout(self):
        from module.persistence.transfer_store import TransferStatus, TransferStore

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id, item_id = self._running_task_with_item(store)
            store.lease_items([item_id])
            self._age_item(
                store, item_id, seconds=store.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS + 120
            )

            store.reconcile_active_tasks(force=True)

            self.assertEqual(TransferStatus.RUNNING, store.get_item(item_id)['status'])
            self.assertEqual(TransferStatus.RUNNING, store.get_task(task_id)['status'])

    def test_reconcile_fails_leased_item_after_leased_timeout(self):
        from module.persistence.transfer_store import TransferStatus, TransferStore

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id, item_id = self._running_task_with_item(store)
            store.lease_items([item_id])
            self._age_item(
                store, item_id, seconds=store.LEASED_TRANSFER_ITEM_TIMEOUT_SECONDS + 120
            )

            changed = store.reconcile_active_tasks(force=True)

            self.assertGreaterEqual(changed, 1)
            item = store.get_item(item_id)
            self.assertEqual(TransferStatus.FAILURE, item['status'])
            self.assertIn('1440分钟无进展', item.get('error_message') or '')
            self.assertEqual(TransferStatus.FAILURE, store.get_task(task_id)['status'])
            self.assertNotIn(item_id, store._leased_item_ids)

    def test_reconcile_prunes_lease_of_finished_item(self):
        from module.persistence.transfer_store import TransferStatus, TransferStore

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            _task_id, item_id = self._running_task_with_item(store)
            store.lease_items([item_id])
            store.update_item(item_id, status=TransferStatus.SUCCESS, phase='sent')
            store.reconcile_active_tasks(force=True)

            store.update_item(item_id, status=TransferStatus.RUNNING, phase='uploading')
            self._age_item(
                store, item_id, seconds=store.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS + 120
            )
            store.reconcile_active_tasks(force=True)

            item = store.get_item(item_id)
            self.assertEqual(TransferStatus.FAILURE, item['status'])
            self.assertIn('5分钟无进展', item.get('error_message') or '')

    def test_retry_failed_item_ids_leases_reset_items(self):
        from module.persistence.transfer_store import TransferStatus, TransferStore

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id, item_id = self._running_task_with_item(
                store, status=TransferStatus.FAILURE
            )

            self.assertEqual(1, store.retry_failed_item_ids(task_id, [item_id]))
            self._age_item(
                store, item_id, seconds=store.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS + 120
            )
            store.reconcile_active_tasks(force=True)

            self.assertEqual(TransferStatus.PENDING, store.get_item(item_id)['status'])

    def _download_message(self, message_id: int):
        from types import SimpleNamespace

        return SimpleNamespace(
            id=message_id,
            link=f'https://t.me/source/{message_id}',
            chat=SimpleNamespace(id=-1001),
        )

    def test_engine_create_item_for_download_leases_new_item(self):
        from module.persistence.transfer_store import TransferStatus, TransferStore
        from module.transfer.context import TransferContext
        from module.transfer.engine import TransferEngine

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/5', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.RUNNING, started=True)
            engine = TransferEngine(TransferContext(transfer_store=store))

            meta = engine.create_transfer_item_for_download(
                task_with_upload={'task_id': task_id, 'link': 'https://t.me/pikpak_bot'},
                chat_id=-1001,
                link='https://t.me/source/5',
                message=self._download_message(5),
                media_type='video',
                file_name='a.mp4',
                final_path=f'{directory}/a.mp4',
                file_size=10,
            )
            item_id = int(meta['item_id'])
            self._age_item(
                store, item_id, seconds=store.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS + 120
            )
            store.reconcile_active_tasks(force=True)

            self.assertEqual(TransferStatus.RUNNING, store.get_item(item_id)['status'])

    def test_engine_create_item_for_download_leases_reused_item(self):
        from module.persistence.transfer_store import TransferStatus, TransferStore
        from module.transfer.context import TransferContext
        from module.transfer.engine import TransferEngine

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id, item_id = self._running_task_with_item(
                store, message_id=6, status=TransferStatus.PENDING
            )
            engine = TransferEngine(TransferContext(transfer_store=store))

            engine.create_transfer_item_for_download(
                task_with_upload={
                    'task_id': task_id,
                    'link': 'https://t.me/pikpak_bot',
                    'item_id': item_id,
                },
                chat_id=-1001,
                link='https://t.me/source/6',
                message=self._download_message(6),
                media_type='video',
                file_name='a.mp4',
                final_path=f'{directory}/a.mp4',
                file_size=10,
            )
            self._age_item(
                store, item_id, seconds=store.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS + 120
            )
            store.reconcile_active_tasks(force=True)

            self.assertEqual(TransferStatus.RUNNING, store.get_item(item_id)['status'])

    def _progress_tracker(self, store):
        from types import SimpleNamespace

        from module.transfer.progress import TransferProgressTracker

        return TransferProgressTracker(
            transfer_store_getter=lambda: store,
            diagnostic=SimpleNamespace(),
            app_getter=lambda: None,
            gc_getter=lambda: None,
            loop_getter=lambda: None,
            pb_getter=lambda: None,
            release_storage=lambda *a: None,
            release_window=lambda *a: None,
            start_download_upload=lambda **kw: False,
            archive_pikpak_item=lambda *a: None,
            fail_transfer_item=lambda *a: None,
            refresh_counts=store.refresh_task_counts,
        )

    def test_progress_file_ready_leases_new_item(self):
        import os

        from module.persistence.transfer_store import TransferStatus, TransferStore

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/7', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.RUNNING, started=True)
            file_path = os.path.join(directory, 'media.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')

            item_id = self._progress_tracker(store).on_transfer_file_ready(
                file_path,
                {
                    'task_id': task_id,
                    'message_id': 7,
                    'source_link': 'https://t.me/source/7',
                    'link': 'https://t.me/pikpak_bot',
                },
            )
            self._age_item(
                store, item_id, seconds=store.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS + 120
            )
            store.reconcile_active_tasks(force=True)

            self.assertEqual(TransferStatus.RUNNING, store.get_item(item_id)['status'])

    def test_progress_file_ready_leases_reused_item(self):
        import os

        from module.persistence.transfer_store import TransferStatus, TransferStore

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id, item_id = self._running_task_with_item(store, message_id=8)
            file_path = os.path.join(directory, 'media.bin')
            with open(file_path, 'wb') as file:
                file.write(b'12345')

            returned_id = self._progress_tracker(store).on_transfer_file_ready(
                file_path,
                {
                    'task_id': task_id,
                    'item_id': item_id,
                    'link': 'https://t.me/pikpak_bot',
                },
            )
            self.assertEqual(item_id, returned_id)
            self._age_item(
                store, item_id, seconds=store.STALE_TRANSFER_ITEM_TIMEOUT_SECONDS + 120
            )
            store.reconcile_active_tasks(force=True)

            self.assertEqual(TransferStatus.RUNNING, store.get_item(item_id)['status'])

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
