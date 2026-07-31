# coding=UTF-8
import asyncio
import sys
import tempfile
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub
install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.adapters.webui.task_manager import WebUITaskManager
from module.persistence.transfer_store import TransferStore, TransferStatus
sys.argv = _ORIGINAL_ARGV


class WebTaskQueueSerialCase(unittest.TestCase):
    def test_resume_second_task_stays_pending_while_first_runs(self):
        async def run_case():
            loop = asyncio.get_running_loop()
            queue = asyncio.Queue()
            submitted = set()
            state = SimpleNamespace(running=None, running_id=None)
            started = []
            hold = asyncio.Event()

            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
                store = TransferStore(directory=directory)
                first_id = store.create_task('https://t.me/a/1', 'https://t.me/pikpak_bot')
                second_id = store.create_task('https://t.me/b/1', 'https://t.me/pikpak_bot')
                store.update_task(first_id, status=TransferStatus.PAUSED)
                store.update_task(second_id, status=TransferStatus.PAUSED)

                async def fake_process(task_id):
                    started.append(task_id)
                    store.update_task(task_id, status=TransferStatus.RUNNING)
                    await hold.wait()

                async def process_queue():
                    manager.start_next_web_transfer_task()

                manager = WebUITaskManager(
                    transfer_store_getter=lambda: store,
                    diagnostic=SimpleNamespace(),
                    loop_getter=lambda: loop,
                    web_task_queue=queue,
                    web_submitted_task_ids=submitted,
                    web_running_task_getter=lambda: state.running,
                    web_running_task_setter=lambda v: setattr(state, 'running', v),
                    web_running_task_id_getter=lambda: state.running_id,
                    web_running_task_id_setter=lambda v: setattr(state, 'running_id', v),
                    web_operation_queue=asyncio.Queue(),
                    web_operations={},
                    process_web_transfer_task_getter=fake_process,
                    process_web_task_queue_getter=process_queue,
                )

                self.assertTrue(manager.resume_web_task(first_id))
                await asyncio.sleep(0)
                self.assertEqual([first_id], started)
                self.assertEqual(TransferStatus.RUNNING, store.get_task(first_id)['status'])

                self.assertTrue(manager.resume_web_task(second_id))
                await asyncio.sleep(0)
                self.assertEqual([first_id], started)
                self.assertEqual(TransferStatus.PENDING, store.get_task(second_id)['status'])

                # Background item refresh must not promote queued pending → running.
                store.add_item(
                    task_id=second_id,
                    source_chat_id=1,
                    source_message_id=1,
                    source_link='https://t.me/b/1',
                    target_link='https://t.me/pikpak_bot',
                    status=TransferStatus.SUCCESS,
                )
                store.refresh_task_counts(second_id, expected_total=10, assignment_completed=False)
                self.assertEqual(TransferStatus.PENDING, store.get_task(second_id)['status'])

                hold.set()
                for _ in range(30):
                    await asyncio.sleep(0)
                    if len(started) >= 2:
                        break
                if state.running and not state.running.done():
                    await asyncio.wait_for(state.running, timeout=1)
                self.assertEqual([first_id, second_id], started)
                self.assertEqual(TransferStatus.RUNNING, store.get_task(second_id)['status'])

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
