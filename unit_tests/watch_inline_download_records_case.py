# coding=UTF-8
"""Watch Inline Transfer Task 的 watch_id 归属与 WebUI 下载记录列表。"""
import sys
import tempfile
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


class WatchInlineDownloadRecordsCase(unittest.TestCase):
    def test_create_task_persists_watch_id(self):
        from module.transfer_store import TransferStore, ExecutionMode

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/c/4209310295/5433',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
                watch_id='forward:https://t.me/c/4209310295->https://t.me/pikpak_bot',
            )
            task = store.get_task(task_id)
            self.assertEqual(
                'forward:https://t.me/c/4209310295->https://t.me/pikpak_bot',
                task['watch_id'],
            )

    def test_ensure_download_fallback_persists_watch_id(self):
        from module.transfer_store import TransferStore, ExecutionMode
        from module.transfer.watch_inline import ensure_download_fallback_transfer_task

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            watch_id = 'forward:https://t.me/ctuxas->https://t.me/pikpak_bot'
            task_id = ensure_download_fallback_transfer_task(
                store=store,
                source_link='https://t.me/ctuxas/99',
                target_link='https://t.me/pikpak_bot',
                target_profile='pikpak',
                watch_id=watch_id,
            )
            task = store.get_task(task_id)
            self.assertEqual(ExecutionMode.WATCH_INLINE, task['execution_mode'])
            self.assertEqual(watch_id, task['watch_id'])

    def test_task_list_excludes_watch_inline_tasks(self):
        from module.transfer_store import TransferStore, ExecutionMode
        from module.adapters.webui.view_model import WebUiViewModel

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            store.create_task(
                'https://t.me/web/1',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WEB_QUEUE,
            )
            store.create_task(
                'https://t.me/watch/2',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
                watch_id='forward:a->b',
            )
            payload = WebUiViewModel(store).task_list()
            ids_links = [t['source_link'] for t in payload['tasks']]
            self.assertEqual(['https://t.me/web/1'], ids_links)

    def test_watch_download_tasks_matches_watch_id_and_legacy_heuristic(self):
        from module.transfer_store import TransferStore, ExecutionMode, TransferStatus
        from module.adapters.webui.view_model import WebUiViewModel

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            watch_id = 'forward:https://t.me/ctuxas->https://t.me/pikpak_bot'
            store.upsert_live_transfer_watch(
                watch_id=watch_id,
                watch_type='forward',
                source_link='https://t.me/ctuxas',
                target_link='https://t.me/pikpak_bot',
                status='running',
            )
            linked = store.create_task(
                'https://t.me/ctuxas/10',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
                watch_id=watch_id,
            )
            legacy = store.create_task(
                'https://t.me/ctuxas/11',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
            )
            other = store.create_task(
                'https://t.me/other/12',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
                watch_id='forward:other->pikpak',
            )
            store.update_task(linked, status=TransferStatus.RUNNING, started=True)
            store.update_task(legacy, status=TransferStatus.SUCCESS, finished=True)
            store.update_task(other, status=TransferStatus.FAILURE, finished=True)

            payload = WebUiViewModel(store).watch_download_tasks(watch_id)
            ids = sorted(t['id'] for t in payload['tasks'])
            self.assertEqual(sorted([linked, legacy]), ids)
            self.assertEqual(1, payload['counts']['active'])
            self.assertEqual(1, payload['counts']['completed'])
            self.assertEqual(0, payload['counts']['failed'])

    def test_watch_download_tasks_expose_display_file_name_and_active_progress(self):
        from module.transfer_store import TransferStore, ExecutionMode, TransferStatus
        from module.adapters.webui.view_model import WebUiViewModel

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            watch_id = 'forward:https://t.me/c/4209310295->https://t.me/pikpak_bot'
            store.upsert_live_transfer_watch(
                watch_id=watch_id,
                watch_type='forward',
                source_link='https://t.me/c/4209310295',
                target_link='https://t.me/pikpak_bot',
                status='running',
            )
            active_id = store.create_task(
                'https://t.me/c/4209310295/5638',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                execution_mode=ExecutionMode.WATCH_INLINE,
                watch_id=watch_id,
            )
            done_id = store.create_task(
                'https://t.me/c/4209310295/5637',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                execution_mode=ExecutionMode.WATCH_INLINE,
                watch_id=watch_id,
            )
            store.update_task(active_id, status=TransferStatus.RUNNING, total_items=1, started=True)
            store.update_task(done_id, status=TransferStatus.SUCCESS, total_items=1, finished=True)
            store.add_item(
                task_id=active_id,
                source_chat_id='4209310295',
                source_message_id=5638,
                source_link='https://t.me/c/4209310295/5638',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='clip.mp4',
                file_size=1000,
                phase='downloading',
                status=TransferStatus.RUNNING,
            )
            active_item_id = store.list_items(active_id)[0]['id']
            store.update_item_progress(
                item_id=active_item_id,
                phase='downloading',
                download_current=420,
                download_total=1000,
                download_speed_bps=2048,
                upload_current=0,
                upload_total=1000,
                upload_speed_bps=0,
            )
            store.add_item(
                task_id=done_id,
                source_chat_id='4209310295',
                source_message_id=5637,
                source_link='https://t.me/c/4209310295/5637',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='done.mp4',
                file_size=500,
                phase='uploaded',
                status=TransferStatus.SUCCESS,
            )

            payload = WebUiViewModel(store).watch_download_tasks(watch_id)
            by_id = {task['id']: task for task in payload['tasks']}

            self.assertEqual('clip.mp4', by_id[active_id]['display_file_name'])
            self.assertEqual('clip.mp4', by_id[active_id]['active_file_name'])
            self.assertEqual(42, by_id[active_id]['active_progress_percent'])
            self.assertEqual(2048, by_id[active_id]['active_speed_bps'])
            self.assertEqual('done.mp4', by_id[done_id]['display_file_name'])

    def test_source_link_belongs_to_watch(self):
        from module.transfer.watch_inline import source_link_belongs_to_watch

        self.assertTrue(source_link_belongs_to_watch(
            'https://t.me/ctuxas/99', 'https://t.me/ctuxas'
        ))
        self.assertTrue(source_link_belongs_to_watch(
            'https://t.me/c/4209310295/5433', 'https://t.me/c/4209310295'
        ))
        self.assertFalse(source_link_belongs_to_watch(
            'https://t.me/ctuxas2/1', 'https://t.me/ctuxas'
        ))


if __name__ == '__main__':
    unittest.main()
