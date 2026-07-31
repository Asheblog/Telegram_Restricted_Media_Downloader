# coding=UTF-8
import asyncio
import sys
import tempfile
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


class TransferItemContinueCase(unittest.TestCase):
    def test_should_continue_web_transfer_item_false_after_failure(self):
        from module.adapters.webui.task_manager import WebUITaskManager
        from module.persistence.transfer_store import TransferStore, TransferStatus
        from module.web_operations import WebOperationsMixin

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            item_id = store.add_item(
                task_id=task_id,
                source_message_id=1,
                source_link='https://t.me/source/1',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.RUNNING,
                phase='downloading',
            )
            manager = WebUITaskManager(
                transfer_store_getter=lambda: store,
                diagnostic=SimpleNamespace(),
                loop_getter=lambda: None,
                web_task_queue=asyncio.Queue(),
                web_submitted_task_ids=set(),
                web_running_task_getter=lambda: None,
                web_running_task_setter=lambda _value: None,
                web_running_task_id_getter=lambda: None,
                web_running_task_id_setter=lambda _value: None,
                web_operation_queue=asyncio.Queue(),
                web_operations={},
            )
            host = SimpleNamespace(transfer_store=store, web_task_manager=manager)
            self.assertTrue(WebOperationsMixin.should_continue_web_transfer_item(host, item_id))

            store.update_item(
                item_id,
                status=TransferStatus.FAILURE,
                phase='failure',
                error_message='stale',
            )
            self.assertFalse(WebOperationsMixin.should_continue_web_transfer_item(host, item_id))


if __name__ == '__main__':
    unittest.main()
