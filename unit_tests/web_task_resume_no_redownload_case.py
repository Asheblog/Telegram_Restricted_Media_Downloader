# coding=UTF-8
import asyncio
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.persistence.transfer_store import TransferStatus, TransferStore
from module.transfer.context import TransferContext
from module.transfer.engine import TransferEngine
from module.transfer.runner import WebTransferRunner


def _engine_with_store(store: TransferStore) -> TransferEngine:
    return TransferEngine(TransferContext(transfer_store=store))


class WebTaskResumeNoRedownloadCase(unittest.TestCase):
    def test_create_transfer_item_reuses_existing_item_id(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                start_id=190,
                end_id=190,
            )
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='-1001',
                source_message_id=190,
                source_link='https://t.me/c/1/190',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='a.mp4',
                phase='uploading',
                status=TransferStatus.RUNNING,
            )
            engine = _engine_with_store(store)
            message = SimpleNamespace(
                id=190,
                link='https://t.me/c/1/190',
                chat=SimpleNamespace(id=-1001),
            )
            meta = engine.create_transfer_item_for_download(
                task_with_upload={
                    'task_id': task_id,
                    'link': 'https://t.me/pikpak_bot',
                    'item_id': item_id,
                    'target_profile': 'pikpak',
                },
                chat_id=-1001,
                link='https://t.me/c/1/190',
                message=message,
                media_type='video',
                file_name='a.mp4',
                final_path=f'{directory}/a.mp4',
                file_size=10,
            )
            self.assertEqual(item_id, meta['item_id'])
            self.assertEqual(1, len(store.list_items(task_id)))
            item = store.get_item(item_id)
            self.assertEqual(TransferStatus.RUNNING, item['status'])
            self.assertEqual('downloading', item['phase'])

    def test_create_transfer_item_skips_terminal_existing_item(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                start_id=190,
                end_id=190,
            )
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='-1001',
                source_message_id=190,
                source_link='https://t.me/c/1/190',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='a.mp4',
                phase='sent',
                status=TransferStatus.SUCCESS,
                archive_status='already_archived',
            )
            engine = _engine_with_store(store)
            message = SimpleNamespace(
                id=190,
                link='https://t.me/c/1/190',
                chat=SimpleNamespace(id=-1001),
            )
            meta = engine.create_transfer_item_for_download(
                task_with_upload={
                    'task_id': task_id,
                    'link': 'https://t.me/pikpak_bot',
                    'item_id': item_id,
                    'target_profile': 'pikpak',
                },
                chat_id=-1001,
                link='https://t.me/c/1/190',
                message=message,
                media_type='video',
                file_name='a.mp4',
                final_path=f'{directory}/a.mp4',
                file_size=10,
            )
            self.assertEqual(item_id, meta.get('item_id'))
            self.assertTrue(meta.get('_skip_download'))
            item = store.get_item(item_id)
            self.assertEqual(TransferStatus.SUCCESS, item['status'])
            self.assertEqual('sent', item['phase'])

    def test_resume_transfer_item_download_binds_existing_item_id(self):
        async def run_case():
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task(
                    'https://t.me/source',
                    'https://t.me/pikpak_bot',
                    start_id=190,
                    end_id=190,
                )
                item_id = store.add_item(
                    task_id=task_id,
                    source_chat_id='-1001',
                    source_message_id=190,
                    range_message_id=190,
                    source_link='https://t.me/c/1/190',
                    target_link='https://t.me/pikpak_bot',
                    media_type='video',
                    file_name='a.mp4',
                    phase='uploading',
                    status=TransferStatus.RUNNING,
                )
                task = store.get_task(task_id)
                captured = {}

                async def fake_create_download_task(**kwargs):
                    captured['with_upload'] = kwargs.get('with_upload')
                    return {'status': 'downloading'}

                host = SimpleNamespace(
                    transfer_store=store,
                    build_transfer_upload_meta=lambda **kwargs: {
                        'task_id': task_id,
                        'link': 'https://t.me/pikpak_bot',
                        'target_profile': 'pikpak',
                        'source_link': kwargs.get('source_link'),
                        'range_message_id': kwargs.get('range_message_id'),
                        'source_folder': kwargs.get('source_folder'),
                    },
                    create_download_task=fake_create_download_task,
                    transfer_single_link=lambda link: link,
                )
                runner = WebTransferRunner(host)
                await runner.resume_transfer_item_download(
                    task=task,
                    item=store.get_item(item_id),
                    range_message_id=190,
                )
                self.assertEqual(item_id, captured['with_upload']['item_id'])

        asyncio.run(run_case())

    def test_process_task_does_not_stack_second_fallback_after_resume(self):
        async def run_case():
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task(
                    'https://t.me/source',
                    'https://t.me/pikpak_bot',
                    start_id=190,
                    end_id=190,
                )
                store.update_task(task_id, status=TransferStatus.RUNNING)
                item_id = store.add_item(
                    task_id=task_id,
                    source_chat_id='source-chat',
                    source_message_id=190,
                    range_message_id=190,
                    source_link='https://t.me/source/190',
                    target_link='https://t.me/pikpak_bot',
                    media_type='video',
                    file_name='a.mp4',
                    phase='downloading',
                    status=TransferStatus.RUNNING,
                )
                fallback_calls = []

                host = SimpleNamespace(
                    transfer_store=store,
                    web_task_manager=None,
                    uploader=object(),
                    app=SimpleNamespace(client=SimpleNamespace()),
                    parse_web_transfer_link=AsyncMock(
                        side_effect=[
                            {'chat_id': 'source-chat'},
                            {'chat_id': 'target-chat'},
                        ]
                    ),
                    find_resumable_transfer_item=lambda *args, **kwargs: store.get_item(item_id),
                    wait_between_transfer_messages=AsyncMock(),
                    get_web_transfer_range_message=AsyncMock(
                        return_value=SimpleNamespace(id=190, link='https://t.me/source/190')
                    ),
                    transfer_message_to_web_target=AsyncMock(return_value=False),
                    skip_missing_web_transfer_range_message=lambda **kwargs: None,
                    transfer_web_discussion_replies_to_target=AsyncMock(return_value=(0, 0)),
                    create_download_task=AsyncMock(return_value={'status': 'downloading'}),
                    build_transfer_upload_meta=lambda **kwargs: {
                        'task_id': task_id,
                        'link': 'https://t.me/pikpak_bot',
                        'source_link': kwargs.get('source_link'),
                        'range_message_id': kwargs.get('range_message_id'),
                    },
                    transfer_single_link=lambda link: link,
                )
                runner = WebTransferRunner(host)

                async def counting_fallback(**kwargs):
                    fallback_calls.append(kwargs)
                    return None

                runner.create_web_transfer_fallback_download = counting_fallback
                with patch.object(runner, 'resume_orphan_resumable_items', new=AsyncMock()):
                    await runner.process_task(task_id)

                # One resume for the interrupted item — not resume + another stacked fallback.
                self.assertEqual(1, len(fallback_calls))
                bound = fallback_calls[0].get('item_id')
                if bound is None:
                    bound = (fallback_calls[0].get('with_upload') or {}).get('item_id')
                self.assertEqual(item_id, bound)

        asyncio.run(run_case())

    def test_process_task_skips_message_when_source_already_terminal(self):
        async def run_case():
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task(
                    'https://t.me/source',
                    'https://t.me/pikpak_bot',
                    start_id=190,
                    end_id=190,
                )
                store.update_task(task_id, status=TransferStatus.RUNNING)
                store.add_item(
                    task_id=task_id,
                    source_chat_id='source-chat',
                    source_message_id=190,
                    range_message_id=190,
                    source_link='https://t.me/source/190',
                    target_link='https://t.me/pikpak_bot',
                    media_type='video',
                    file_name='a.mp4',
                    phase='sent',
                    status=TransferStatus.SUCCESS,
                    archive_status='already_archived',
                )
                # Insert zombie active sibling via SQL — add_item upserts same source_message_id.
                with store.connect() as conn:
                    conn.execute(
                        '''
                        INSERT INTO transfer_items (
                            task_id, source_chat_id, source_message_id, range_message_id,
                            source_link, target_link, media_type, file_name, phase, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            task_id, 'source-chat', 190, 190,
                            'https://t.me/source/190', 'https://t.me/pikpak_bot',
                            'video', 'a.mp4', 'downloading', TransferStatus.RUNNING,
                            store.utc_now(), store.utc_now(),
                        ),
                    )
                fallback_calls = []

                host = SimpleNamespace(
                    transfer_store=store,
                    web_task_manager=None,
                    uploader=object(),
                    app=SimpleNamespace(client=SimpleNamespace()),
                    parse_web_transfer_link=AsyncMock(
                        side_effect=[
                            {'chat_id': 'source-chat'},
                            {'chat_id': 'target-chat'},
                        ]
                    ),
                    find_resumable_transfer_item=_engine_with_store(store).find_resumable_transfer_item,
                    wait_between_transfer_messages=AsyncMock(),
                    get_web_transfer_range_message=AsyncMock(
                        return_value=SimpleNamespace(id=190, link='https://t.me/source/190')
                    ),
                    transfer_message_to_web_target=AsyncMock(return_value=True),
                    skip_missing_web_transfer_range_message=lambda **kwargs: None,
                    transfer_web_discussion_replies_to_target=AsyncMock(return_value=(0, 0)),
                )
                runner = WebTransferRunner(host)
                runner.create_web_transfer_fallback_download = AsyncMock(
                    side_effect=lambda **kwargs: fallback_calls.append(kwargs)
                )
                with patch.object(runner, 'resume_orphan_resumable_items', new=AsyncMock()):
                    await runner.process_task(task_id)

                self.assertEqual([], fallback_calls)
                self.assertEqual(0, host.transfer_message_to_web_target.await_count)
                zombies = [
                    item for item in store.list_items(task_id)
                    if item['status'] == TransferStatus.RUNNING
                ]
                self.assertEqual([], zombies)

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
