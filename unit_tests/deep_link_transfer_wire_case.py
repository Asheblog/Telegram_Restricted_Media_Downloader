# coding=UTF-8
import asyncio
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from module.persistence.transfer_store import TransferStore
from module.transfer.deep_link import DeepLinkResolveError
from module.transfer.runner import WebTransferRunner
from module.transfer_store import TransferStatus


def _make_host(store, resolver=None, forward=None):
    forward_calls = []

    async def default_forward(**kwargs):
        forward_calls.append(kwargs)
        return SimpleNamespace(id=100)

    host = SimpleNamespace(
        app=SimpleNamespace(client=object()),
        gc=SimpleNamespace(
            download_upload=True,
            get_deep_link_bot_whitelist=lambda: ['a82bot'],
            get_deep_link_timeout_seconds=lambda: 60,
        ),
        transfer_store=store,
        forward_calls=forward_calls,
        create_web_transfer_fallback_download=AsyncMock(),
    )
    host.forward = forward or default_forward
    host.get_deep_link_resolver = lambda: resolver
    host.get_task_target_size_limit_error = lambda task, message: None
    host.get_message_media_target_limit_meta = lambda message: (
        {'file_name': 'video.mp4', 'file_size': 10}
        if getattr(message, 'video', None) else None
    )
    host.get_message_media_archive_filename = lambda message: (
        getattr(getattr(message, 'video', None), 'file_name', None)
    )
    host.is_pikpak_target = lambda target_link, target_profile=None: False
    host.forwarded_message_has_identity = lambda msg: getattr(msg, 'id', None) is not None
    host.refresh_transfer_task_counts = lambda task_id: store.refresh_task_counts(task_id)
    host.skip_empty_transfer_source_message = lambda **kwargs: None
    host.fail_transfer_item = lambda task_id, item_id, message: store.update_item(
        item_id,
        phase='failure',
        status=TransferStatus.FAILURE,
        error_message=message,
    )
    return host


class DeepLinkTransferWireCase(unittest.TestCase):
    def test_resolve_disabled_does_not_call_resolver(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/target',
                resolve_deep_link=False,
            )
            task = store.get_task(task_id)
            resolver = SimpleNamespace(resolve=AsyncMock())
            host = _make_host(store, resolver=resolver)
            runner = WebTransferRunner(host)
            channel_msg = SimpleNamespace(
                id=1,
                empty=False,
                link='https://t.me/source/1',
                chat=SimpleNamespace(id='source-chat', username='source'),
                video=None,
            )

            asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1',
            ))

            resolver.resolve.assert_not_called()
            self.assertEqual(1, len(host.forward_calls))
            self.assertIs(channel_msg, host.forward_calls[0]['message'])

    def test_resolve_returns_media_forwards_resolved_and_records_event(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/target',
                resolve_deep_link=True,
            )
            task = store.get_task(task_id)
            resolved = SimpleNamespace(
                id=99,
                video=SimpleNamespace(file_size=10, file_name='video.mp4'),
                chat=SimpleNamespace(id='bot-chat', username='a82bot'),
                link=None,
                _deep_link_meta={'bot': 'a82bot', 'start_param': 'v_abc'},
            )
            resolver = SimpleNamespace(resolve=AsyncMock(return_value=resolved))
            host = _make_host(store, resolver=resolver)
            runner = WebTransferRunner(host)
            channel_msg = SimpleNamespace(
                id=1,
                empty=False,
                link='https://t.me/source/1',
                chat=SimpleNamespace(id='source-chat', username='source'),
                video=None,
            )

            asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1',
            ))

            resolver.resolve.assert_awaited_once()
            self.assertEqual(1, len(host.forward_calls))
            self.assertIs(resolved, host.forward_calls[0]['message'])
            item = store.list_items(task_id)[0]
            self.assertEqual('source-chat', item['source_chat_id'])
            self.assertEqual(1, item['source_message_id'])
            self.assertEqual('source', item['source_folder'])
            events = store.list_events(task_id)
            self.assertTrue(
                any('resolved_via=' in (event.get('message') or '') for event in events),
                events,
            )

    def test_resolve_error_records_failure_without_channel_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/target',
                resolve_deep_link=True,
            )
            task = store.get_task(task_id)
            resolver = SimpleNamespace(
                resolve=AsyncMock(side_effect=DeepLinkResolveError('timeout')),
            )
            host = _make_host(store, resolver=resolver)
            runner = WebTransferRunner(host)
            channel_msg = SimpleNamespace(
                id=1,
                empty=False,
                link='https://t.me/source/1',
                chat=SimpleNamespace(id='source-chat', username='source'),
                video=SimpleNamespace(file_size=10, file_name='preview.mp4'),
            )

            result = asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1',
            ))

            self.assertFalse(result)
            self.assertEqual(0, len(host.forward_calls))
            host.create_web_transfer_fallback_download.assert_not_called()
            item = store.list_items(task_id)[0]
            self.assertEqual(TransferStatus.FAILURE, item['status'])
            self.assertEqual('failed', item['phase'])
            self.assertEqual('deep_link', item['media_type'])
            self.assertEqual('source-chat', item['source_chat_id'])
            self.assertEqual(1, item['source_message_id'])
            self.assertIn('timeout', item['error_message'])

    def test_resolve_success_forward_fallback_uses_resolved_message(self):
        from pyrogram.errors import ChatForwardsRestricted

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/target',
                resolve_deep_link=True,
            )
            task = store.get_task(task_id)
            resolved = SimpleNamespace(
                id=99,
                video=SimpleNamespace(file_size=10, file_name='video.mp4'),
                chat=SimpleNamespace(id='bot-chat', username='a82bot'),
                link=None,
                _deep_link_meta={'bot': 'a82bot', 'start_param': 'v_abc'},
            )
            resolver = SimpleNamespace(resolve=AsyncMock(return_value=resolved))

            async def restricted_forward(**kwargs):
                raise ChatForwardsRestricted('restricted')

            host = _make_host(store, resolver=resolver, forward=restricted_forward)
            runner = WebTransferRunner(host)
            runner.create_web_transfer_fallback_download = AsyncMock()
            channel_msg = SimpleNamespace(
                id=1,
                empty=False,
                link='https://t.me/source/1',
                chat=SimpleNamespace(id='source-chat', username='source'),
                video=None,
            )

            result = asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1',
            ))

            self.assertTrue(result)
            runner.create_web_transfer_fallback_download.assert_awaited_once()
            kwargs = runner.create_web_transfer_fallback_download.await_args.kwargs
            self.assertIs(resolved, kwargs['message'])
            self.assertEqual('https://t.me/source/1', kwargs['source_link'])


if __name__ == '__main__':
    unittest.main()
