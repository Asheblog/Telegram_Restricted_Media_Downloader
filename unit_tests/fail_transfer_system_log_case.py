# coding=UTF-8
"""fail_transfer_item must persist failure reasons into system_logs."""
import tempfile
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.persistence.system_log import SystemLogTracer
from module.pikpak_integration import PikpakIntegrationManager
from module.transfer_store import TransferStatus, TransferStore


class FailTransferSystemLogCase(unittest.TestCase):
    def test_fail_transfer_item_writes_system_log_error(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/swag_vip/554',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=554,
                end_id=554,
            )
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='6492177719',
                source_message_id=554,
                source_link='https://t.me/swag_vip/554',
                target_link='https://t.me/pikpak_bot',
                media_type='forward',
                file_name='clip.mp4',
                file_size=1024,
                phase='forwarded',
                status=TransferStatus.RUNNING,
            )
            tracer = SystemLogTracer(store=store, diagnostic=SimpleNamespace())
            manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: store,
                pikpak_archive_client_getter=lambda: None,
                diagnostic=SimpleNamespace(warning=lambda m: None),
                gc_getter=lambda: SimpleNamespace(config={}),
                refresh_counts=lambda tid: store.refresh_task_counts(tid),
                system_log=tracer,
            )

            error = 'PikPak ingest confirmation timeout or failure: https://t.me/swag_vip/554'
            manager.fail_transfer_item(task_id, item_id, error)

            item = store.get_item(item_id)
            self.assertEqual(TransferStatus.FAILURE, item['status'])
            self.assertEqual(error, item['error_message'])

            logs, total = store.list_system_logs(category='transfer', level='error', limit=10)
            self.assertEqual(1, total)
            entry = logs[0]
            self.assertEqual('item_failure', entry['stage'])
            self.assertEqual(error, entry['message'])
            self.assertEqual('6492177719', entry['source_chat_id'])
            self.assertEqual(554, entry['source_message_id'])
            self.assertEqual('https://t.me/pikpak_bot', entry['target_link'])
            self.assertIn(str(task_id), entry.get('details') or '')
            self.assertIn(str(item_id), entry.get('details') or '')


if __name__ == '__main__':
    unittest.main()
