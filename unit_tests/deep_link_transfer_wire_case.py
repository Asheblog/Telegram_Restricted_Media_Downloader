# coding=UTF-8
import asyncio
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from unit_tests.pyrogram_stub import install_pyrogram_stub
install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.core.media_types import MEDIA_TYPES_DEFAULT, build_runtime_message_filter
from module.persistence.transfer_store import TransferStore
from module.transfer.deep_link import DeepLinkResolveError
from module.transfer.runner import WebTransferRunner
from module.transfer_store import TransferStatus
sys.argv = _ORIGINAL_ARGV


def _close_store(store):
    conn = getattr(getattr(store, '_tls', None), 'conn', None)
    if conn is not None:
        conn.close()
        store._tls.conn = None


def _make_host(store, resolver=None, forward=None):
    forward_calls = []

    async def default_forward(**kwargs):
        forward_calls.append(kwargs)
        return SimpleNamespace(id=100)

    host = SimpleNamespace(
        app=SimpleNamespace(client=object()),
        gc=SimpleNamespace(
            download_upload=True,
            message_filter={
                'enabled': True,
                'media_types': dict(MEDIA_TYPES_DEFAULT),
            },
            get_deep_link_bot_whitelist=lambda: ['a82bot'],
            get_deep_link_timeout_seconds=lambda: 60,
            get_deep_link_min_interval_seconds=lambda: 0,
            get_deep_link_settle_seconds=lambda: 0,
            get_deep_link_max_pages=lambda: 20,
            get_deep_link_page_click_interval_seconds=lambda: 0,
        ),
        transfer_store=store,
        forward_calls=forward_calls,
        create_web_transfer_fallback_download=AsyncMock(),
    )
    host.forward = forward or default_forward
    host.get_deep_link_resolver = lambda: resolver
    host.get_task_target_size_limit_error = lambda task, message: None
    host.get_message_media_target_limit_meta = lambda message, post_message_id=None: (
        {'file_name': 'video.mp4', 'file_size': 10}
        if getattr(message, 'video', None) else None
    )
    host.get_message_media_archive_filename = lambda message, post_message_id=None: (
        getattr(getattr(message, 'video', None), 'file_name', None)
    )
    host.is_pikpak_target = lambda target_link, target_profile=None: False
    host.forwarded_message_has_identity = lambda msg: getattr(msg, 'id', None) is not None
    host.refresh_transfer_task_counts = lambda task_id: store.refresh_task_counts(task_id)
    host.skip_empty_transfer_source_message = lambda **kwargs: None
    host.runtime_message_filter = lambda override=None: build_runtime_message_filter(
        host.gc.message_filter,
        override,
    )
    host.skip_transfer_item_for_media_type = (
        lambda task, message, source_link, origin_chat_id, reject_reason, range_message_id=None: (
            store.add_item(
                task_id=int(task['id']),
                source_chat_id=origin_chat_id,
                source_message_id=getattr(message, 'id', None),
                range_message_id=range_message_id,
                source_link=source_link,
                target_link=task.get('target_link'),
                media_type='filtered',
                phase='skipped',
                status=TransferStatus.SKIPPED,
                error_message=reject_reason,
            )
        )
    )
    host.fail_transfer_item = lambda task_id, item_id, message: store.update_item(
        item_id,
        phase='failure',
        status=TransferStatus.FAILURE,
        error_message=message,
    )
    return host


class DeepLinkTransferWireCase(unittest.TestCase):
    def test_resolve_disabled_does_not_call_resolver(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
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
                text='teaser',
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
            _close_store(store)

    def test_pikpak_target_skips_text_only_without_forward_or_ingest_wait(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/gokaidanbao',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
            )
            task = store.get_task(task_id)
            host = _make_host(store)
            host.is_pikpak_target = lambda target_link, target_profile=None: True
            host.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=False)
            runner = WebTransferRunner(host)
            text_msg = SimpleNamespace(
                id=2040,
                empty=False,
                text='求片 取一\n洛宝',
                caption=None,
                link='https://t.me/gokaidanbao/2040',
                chat=SimpleNamespace(id='gokaidanbao', username='gokaidanbao'),
                video=None,
                photo=None,
                document=None,
                audio=None,
                voice=None,
                animation=None,
                video_note=None,
            )

            asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=text_msg,
                origin_chat_id='gokaidanbao',
                target_chat_id='pikpak-chat',
                source_link='https://t.me/gokaidanbao/2040',
            ))

            self.assertEqual([], host.forward_calls)
            host.wait_for_pikpak_ingest_confirmation.assert_not_awaited()
            item = store.list_items(task_id)[0]
            self.assertEqual(TransferStatus.SKIPPED, item['status'])
            self.assertIn('PikPak 不支持无媒体消息', item['error_message'] or '')
            _close_store(store)

    def test_resolve_returns_media_forwards_resolved_and_records_event(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
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
                text='teaser',
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
            self.assertEqual('source/1 - teaser', item['source_folder'])
            events = store.list_events(task_id)
            self.assertTrue(
                any('resolved_via=' in (event.get('message') or '') for event in events),
                events,
            )

    def test_resolve_error_records_failure_without_channel_fallback(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
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

    def test_resolve_none_with_comments_awaits_without_skip_item(self):
        """开深链+评论区：主贴无链不转发封面、不记跳过项，交给评论区。"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/gokaidanbao',
                'https://t.me/pikpak_bot',
                resolve_deep_link=True,
                include_comment=True,
            )
            task = store.get_task(task_id)
            resolver = SimpleNamespace(resolve=AsyncMock(return_value=None))
            host = _make_host(store, resolver=resolver)
            runner = WebTransferRunner(host)
            channel_msg = SimpleNamespace(
                id=2509,
                empty=False,
                link='https://t.me/gokaidanbao/2509',
                chat=SimpleNamespace(id='gokaidanbao', username='gokaidanbao'),
                photo=SimpleNamespace(file_size=100_000),
                video=None,
                text='#一个人Yigeren33',
            )

            result = asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='gokaidanbao',
                target_chat_id='pikpak-chat',
                source_link='https://t.me/gokaidanbao/2509',
            ))

            self.assertFalse(result)
            self.assertEqual(0, len(host.forward_calls))
            host.create_web_transfer_fallback_download.assert_not_called()
            self.assertEqual([], store.list_items(task_id))
            events = store.list_events(task_id)
            self.assertTrue(
                any('交由评论区取片' in (e.get('message') or '') for e in events),
                events,
            )
            _close_store(store)

    def test_resolve_none_without_comments_marks_failure(self):
        """开深链但未开评论区：主贴无链标失败，不回退封面成功。"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/gokaidanbao',
                'https://t.me/pikpak_bot',
                resolve_deep_link=True,
                include_comment=False,
            )
            task = store.get_task(task_id)
            resolver = SimpleNamespace(resolve=AsyncMock(return_value=None))
            host = _make_host(store, resolver=resolver)
            runner = WebTransferRunner(host)
            channel_msg = SimpleNamespace(
                id=2509,
                empty=False,
                link='https://t.me/gokaidanbao/2509',
                chat=SimpleNamespace(id='gokaidanbao', username='gokaidanbao'),
                photo=SimpleNamespace(file_size=100_000),
                video=None,
                text='#一个人Yigeren33',
            )

            result = asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='gokaidanbao',
                target_chat_id='pikpak-chat',
                source_link='https://t.me/gokaidanbao/2509',
            ))

            self.assertFalse(result)
            self.assertEqual(0, len(host.forward_calls))
            items = store.list_items(task_id)
            self.assertEqual(1, len(items))
            self.assertEqual(TransferStatus.FAILURE, items[0]['status'])
            self.assertIn('未向资源 bot 取片', items[0]['error_message'] or '')
            _close_store(store)

    def test_resolve_success_forward_fallback_uses_resolved_message(self):
        from pyrogram.errors.exceptions.bad_request_400 import ChatForwardsRestricted

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
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
                text='teaser',
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

    def test_pikpak_deep_link_empty_forward_falls_back_to_download(self):
        """Regression: copy_message re-fetch yields MessageEmpty → forward returns None."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/gokaidanbao',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                resolve_deep_link=True,
            )
            task = store.get_task(task_id)
            resolved = SimpleNamespace(
                id=153990,
                empty=False,
                video=SimpleNamespace(file_size=10, file_name='clip.mp4'),
                chat=SimpleNamespace(id=7542243325, username='wenjianchucunbot'),
                link='https://t.me/c/2775073467/142125',
                _deep_link_meta={'bot': 'wenjianchucunbot', 'start_param': 'pack'},
            )
            resolver = SimpleNamespace(resolve=AsyncMock(return_value=resolved))

            async def empty_forward(**_kwargs):
                return None

            host = _make_host(store, resolver=resolver, forward=empty_forward)
            host.is_pikpak_target = lambda target_link, target_profile=None: True
            host.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)
            runner = WebTransferRunner(host)
            runner.create_web_transfer_fallback_download = AsyncMock()
            channel_msg = SimpleNamespace(
                id=2040,
                empty=False,
                link='https://t.me/gokaidanbao/2040',
                chat=SimpleNamespace(id='gokaidanbao', username='gokaidanbao'),
                video=None,
                text='求片',
            )

            result = asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='gokaidanbao',
                target_chat_id='pikpak-chat',
                source_link='https://t.me/gokaidanbao/2040',
            ))

            self.assertTrue(result)
            runner.create_web_transfer_fallback_download.assert_awaited_once()
            kwargs = runner.create_web_transfer_fallback_download.await_args.kwargs
            self.assertIs(resolved, kwargs['message'])
            self.assertEqual('https://t.me/gokaidanbao/2040', kwargs['source_link'])
            self.assertIsNotNone(kwargs.get('item_id'))
            host.wait_for_pikpak_ingest_confirmation.assert_not_awaited()
            events = store.list_events(task_id)
            self.assertTrue(
                any(
                    'Direct forward empty/invalid; fallback download' in (e.get('message') or '')
                    for e in events
                ),
                events,
            )
            item = store.get_item(int(kwargs['item_id']))
            self.assertEqual(TransferStatus.RUNNING, item['status'])
            self.assertNotIn(
                'Direct forward did not produce a target message',
                item.get('error_message') or '',
            )
            _close_store(store)

    def test_pikpak_deep_link_empty_forward_fails_when_download_upload_disabled(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
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

            async def empty_forward(**_kwargs):
                return None

            host = _make_host(store, resolver=resolver, forward=empty_forward)
            host.gc.download_upload = False
            host.is_pikpak_target = lambda target_link, target_profile=None: True
            runner = WebTransferRunner(host)
            runner.create_web_transfer_fallback_download = AsyncMock()
            channel_msg = SimpleNamespace(
                id=1,
                empty=False,
                link='https://t.me/source/1',
                chat=SimpleNamespace(id='source-chat', username='source'),
                video=None,
                text='teaser',
            )

            result = asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='source-chat',
                target_chat_id='pikpak-chat',
                source_link='https://t.me/source/1',
            ))

            self.assertFalse(result)
            runner.create_web_transfer_fallback_download.assert_not_called()
            item = store.list_items(task_id)[0]
            self.assertEqual(TransferStatus.FAILURE, item['status'])
            self.assertIn('Direct forward did not produce a target message', item['error_message'])
            _close_store(store)

    def test_resolve_pikpak_archive_keeps_channel_source_folder_not_bot(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/swag_vip',
                'https://t.me/mypikpakbot',
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
            archive_calls = []

            host = _make_host(store, resolver=resolver)
            host.is_pikpak_target = lambda *a, **k: True
            host.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)
            host.complete_forwarded_pikpak_item = lambda **kwargs: (
                archive_calls.append(kwargs) or True
            )
            host.get_message_media_target_limit_meta = lambda message, post_message_id=None: (
                {'file_name': 'video.mp4', 'file_size': 10}
                if getattr(message, 'video', None) else None
            )
            runner = WebTransferRunner(host)
            channel_msg = SimpleNamespace(
                id=1,
                empty=False,
                link='https://t.me/swag_vip/1',
                chat=SimpleNamespace(id='-1001', username='swag_vip'),
                video=None,
                text='teaser',
            )

            asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='-1001',
                target_chat_id='pikpak-chat',
                source_link='https://t.me/swag_vip/1',
            ))

            item = store.list_items(task_id)[0]
            self.assertEqual('swag_vip/1 - teaser', item['source_folder'])
            self.assertEqual(1, len(archive_calls))
            self.assertEqual(
                'swag_vip/1 - teaser',
                archive_calls[0].get('source_folder'),
                archive_calls[0],
            )


class DeepLinkMultiMediaWireCase(unittest.TestCase):
    def test_resolve_list_forwards_each_media_and_marks_source_complete(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/target',
                resolve_deep_link=True,
            )
            task = store.get_task(task_id)
            resolved = [
                SimpleNamespace(
                    id=101,
                    video=SimpleNamespace(file_size=10, file_name='a.mp4'),
                    chat=SimpleNamespace(id='bot-chat', username='a82bot'),
                    link=None,
                    _deep_link_meta={'bot': 'a82bot', 'start_param': 'pack'},
                ),
                SimpleNamespace(
                    id=102,
                    document=SimpleNamespace(file_size=11, file_name='b.bin'),
                    video=None,
                    chat=SimpleNamespace(id='bot-chat', username='a82bot'),
                    link=None,
                    _deep_link_meta={'bot': 'a82bot', 'start_param': 'pack'},
                ),
            ]
            resolver = SimpleNamespace(resolve=AsyncMock(return_value=resolved))
            host = _make_host(store, resolver=resolver)
            host.get_message_media_target_limit_meta = lambda message, post_message_id=None: (
                {'file_name': 'a.mp4', 'file_size': 10}
                if getattr(message, 'video', None)
                else (
                    {'file_name': 'b.bin', 'file_size': 11}
                    if getattr(message, 'document', None)
                    else None
                )
            )
            runner = WebTransferRunner(host)
            channel_msg = SimpleNamespace(
                id=1,
                empty=False,
                link='https://t.me/source/1',
                chat=SimpleNamespace(id='source-chat', username='source'),
                video=None,
                text='teaser',
            )

            asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=channel_msg,
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1',
            ))

            self.assertEqual(2, len(host.forward_calls))
            items = store.list_items(task_id)
            self.assertTrue(any(item['source_message_id'] == 1 for item in items))
            self.assertTrue(store.is_source_message_terminal(task_id, 1, 'source-chat'))

    def test_pause_mid_deep_link_batch_does_not_mark_source_complete(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/target',
                resolve_deep_link=True,
            )
            task = store.get_task(task_id)
            resolved = [
                SimpleNamespace(
                    id=101,
                    video=SimpleNamespace(file_size=10, file_name='a.mp4'),
                    chat=SimpleNamespace(id='bot-chat', username='a82bot'),
                    link=None,
                    _deep_link_meta={'bot': 'a82bot', 'start_param': 'pack'},
                ),
                SimpleNamespace(
                    id=102,
                    document=SimpleNamespace(file_size=11, file_name='b.bin'),
                    video=None,
                    chat=SimpleNamespace(id='bot-chat', username='a82bot'),
                    link=None,
                    _deep_link_meta={'bot': 'a82bot', 'start_param': 'pack'},
                ),
            ]
            resolver = SimpleNamespace(resolve=AsyncMock(return_value=resolved))
            host = _make_host(store, resolver=resolver)
            settle_calls = {'n': 0}

            async def settle(tid, *, before=None):
                settle_calls['n'] += 1
                # After first media forwarded, pause before the second.
                if settle_calls['n'] >= 2:
                    store.update_task(int(tid), status=TransferStatus.PAUSING)
                    store.update_task(int(tid), status=TransferStatus.PAUSED)
                    return True
                return False

            host.settle_web_task_pause_request = settle
            runner = WebTransferRunner(host)
            # Comment-sourced deep link (discussion reply message id).
            comment_msg = SimpleNamespace(
                id=142912,
                empty=False,
                link='https://t.me/c/2775073467/142912',
                chat=SimpleNamespace(id='discussion-chat', username=None),
                video=None,
                text='deep link comment',
            )

            asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=comment_msg,
                origin_chat_id='discussion-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/c/2775073467/142912',
            ))

            self.assertEqual(1, len(host.forward_calls))
            self.assertFalse(
                store.is_source_message_terminal(task_id, 142912, 'discussion-chat')
            )
            self.assertEqual(TransferStatus.PAUSED, store.get_task(task_id)['status'])


class DeepLinkArchiveFolderCase(unittest.TestCase):
    def test_archive_prefers_item_source_folder_over_bot_message_username(self):
        from module.pikpak_integration import PikpakIntegrationManager

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/swag_vip', 'https://t.me/mypikpakbot')
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='-1001',
                source_message_id=1,
                source_link='https://t.me/swag_vip/1',
                target_link='https://t.me/mypikpakbot',
                source_folder='swag_vip',
                status=TransferStatus.RUNNING,
            )
            archive_folders = []

            class FakeArchive:
                def archive_file(self, source_folder, **kwargs):
                    archive_folders.append(source_folder)
                    return SimpleNamespace(
                        ok=True,
                        status='moved',
                        archive_path=f'Telegram/{source_folder}/video.mp4',
                        message='',
                    )

                def ensure_source_folder(self, source_folder):
                    archive_folders.append(source_folder)
                    return SimpleNamespace(
                        ok=True,
                        status='folder_ready',
                        archive_path=f'Telegram/{source_folder}',
                        message='',
                    )

            manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: store,
                pikpak_archive_client_getter=lambda: FakeArchive(),
                diagnostic=SimpleNamespace(info=lambda m: None, warning=lambda m: None),
                gc_getter=lambda: None,
                refresh_counts=lambda tid: None,
            )
            bot_message = SimpleNamespace(
                id=99,
                video=SimpleNamespace(file_size=10, file_name='video.mp4'),
                chat=SimpleNamespace(id='bot-chat', username='a82bot'),
                link=None,
            )

            result = manager.archive_pikpak_item(
                target_profile='pikpak',
                item_id=item_id,
                task_id=task_id,
                message=bot_message,
                source_link='https://t.me/swag_vip/1',
                transferred_at=1.0,
            )

            self.assertTrue(result.ok)
            self.assertEqual(['swag_vip'], archive_folders)
            self.assertEqual('swag_vip', store.get_item(item_id)['source_folder'])

    def test_archive_prefers_source_link_over_bot_message_when_no_item_folder(self):
        from module.pikpak_integration import PikpakIntegrationManager

        archive_folders = []

        class FakeArchive:
            def archive_file(self, source_folder, **kwargs):
                archive_folders.append(source_folder)
                return SimpleNamespace(
                    ok=True,
                    status='moved',
                    archive_path=f'Telegram/{source_folder}/video.mp4',
                    message='',
                )

        manager = PikpakIntegrationManager(
            transfer_store_getter=lambda: None,
            pikpak_archive_client_getter=lambda: FakeArchive(),
            diagnostic=SimpleNamespace(info=lambda m: None, warning=lambda m: None),
            gc_getter=lambda: None,
            refresh_counts=lambda tid: None,
        )
        bot_message = SimpleNamespace(
            id=99,
            video=SimpleNamespace(file_size=10, file_name='video.mp4'),
            chat=SimpleNamespace(id='bot-chat', username='a82bot'),
            link=None,
        )

        result = manager.archive_pikpak_item(
            target_profile='pikpak',
            item_id=None,
            task_id=None,
            message=bot_message,
            source_link='https://t.me/swag_vip/1',
            transferred_at=1.0,
        )

        self.assertTrue(result.ok)
        self.assertEqual(['swag_vip/1'], archive_folders)

    def test_archive_recovers_parent_folder_for_discussion_item_without_folder(self):
        from module.pikpak_integration import PikpakIntegrationManager

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/mychannel/7',
                'https://t.me/mypikpakbot',
                target_profile='pikpak',
                include_comment=True,
                resolve_deep_link=True,
            )
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='discussion-chat',
                source_message_id=12,
                range_message_id=7,
                source_link='https://t.me/discussgrp/12',
                target_link='https://t.me/mypikpakbot',
                status=TransferStatus.RUNNING,
            )
            archive_folders = []

            class FakeArchive:
                def archive_file(self, source_folder, **kwargs):
                    archive_folders.append(source_folder)
                    return SimpleNamespace(
                        ok=True,
                        status='moved',
                        archive_path=f'Telegram/{source_folder}/video.mp4',
                        message='',
                    )

            manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: store,
                pikpak_archive_client_getter=lambda: FakeArchive(),
                diagnostic=SimpleNamespace(info=lambda m: None, warning=lambda m: None),
                gc_getter=lambda: None,
                refresh_counts=lambda tid: None,
            )
            bot_message = SimpleNamespace(
                id=99,
                video=SimpleNamespace(file_size=10, file_name='video.mp4'),
                chat=SimpleNamespace(id='bot-chat', username='a82bot'),
                link=None,
            )

            result = manager.archive_pikpak_item(
                target_profile='pikpak',
                item_id=item_id,
                task_id=task_id,
                message=bot_message,
                source_link='https://t.me/discussgrp/12',
                transferred_at=1.0,
            )

            self.assertTrue(result.ok)
            self.assertEqual(['mychannel/7'], archive_folders)
            self.assertEqual('mychannel/7', store.get_item(item_id)['source_folder'])
            _close_store(store)

    def test_archive_skips_text_only_message_without_creating_folder(self):
        from module.pikpak_integration import PikpakIntegrationManager

        folder_calls = []
        archive_calls = []

        class FakeArchive:
            def ensure_source_folder(self, source_folder):
                folder_calls.append(source_folder)
                return SimpleNamespace(
                    ok=True,
                    status='folder_ready',
                    archive_path=f'Telegram/{source_folder}',
                    message='',
                )

            def archive_file(self, **kwargs):
                archive_calls.append(kwargs)
                return SimpleNamespace(ok=True, status='moved', archive_path='x', message='')

        manager = PikpakIntegrationManager(
            transfer_store_getter=lambda: None,
            pikpak_archive_client_getter=lambda: FakeArchive(),
            diagnostic=SimpleNamespace(info=lambda m: None, warning=lambda m: None),
            gc_getter=lambda: None,
            refresh_counts=lambda tid: None,
        )
        text_message = SimpleNamespace(
            id=1969,
            text='求片 取一\n洛宝',
            caption=None,
            chat=SimpleNamespace(id=-1001, username='gokaidanbao'),
            link='https://t.me/gokaidanbao/1969',
        )

        result = manager.archive_pikpak_item(
            target_profile='pikpak',
            item_id=None,
            task_id=None,
            message=text_message,
            source_link='https://t.me/gokaidanbao/1969',
            source_folder='gokaidanbao/_未知作者/1969 - 求片 取一',
            transferred_at=1.0,
        )

        self.assertIsNone(result)
        self.assertEqual([], folder_calls)
        self.assertEqual([], archive_calls)

    def test_ingest_failure_recognizes_unsupported_file_reply(self):
        from module.pikpak_integration import PikpakIntegrationManager

        unsupported = SimpleNamespace(
            text='当前文件不支持，PikPak 正在努力支持中',
            caption=None,
        )
        self.assertTrue(PikpakIntegrationManager.is_pikpak_ingest_failure_message(unsupported))
        self.assertFalse(
            PikpakIntegrationManager.message_has_pikpak_ingestible_media(
                SimpleNamespace(id=1, text='求片 取一', video=None, photo=None, document=None)
            )
        )
        self.assertTrue(
            PikpakIntegrationManager.message_has_pikpak_ingestible_media(
                SimpleNamespace(id=2, video=SimpleNamespace(file_size=10), text=None)
            )
        )

    def test_wait_for_ingest_returns_false_immediately_on_unsupported_reply(self):
        from module.pikpak_integration import PikpakIntegrationManager

        class FakeClient:
            async def get_chat_history(self, chat_id, limit):
                yield SimpleNamespace(
                    id=101,
                    text='当前文件不支持，PikPak 正在努力支持中',
                    reply_to_message=SimpleNamespace(id=100),
                )

        sleep_calls = []

        async def fake_sleep(_seconds):
            sleep_calls.append(_seconds)

        manager = PikpakIntegrationManager(
            transfer_store_getter=lambda: None,
            pikpak_archive_client_getter=lambda: None,
            diagnostic=SimpleNamespace(info=lambda m: None, warning=lambda m: None),
            gc_getter=lambda: None,
            refresh_counts=lambda tid: None,
            app_getter=lambda: SimpleNamespace(client=FakeClient()),
        )

        async def run_case():
            with patch('module.adapters.pikpak.integration.asyncio.sleep', new=fake_sleep):
                return await manager.wait_for_pikpak_ingest_confirmation(
                    target_chat_id='pikpak',
                    forwarded_message=SimpleNamespace(id=100),
                    timeout_seconds=15,
                    poll_interval=3,
                )

        self.assertFalse(asyncio.run(run_case()))
        self.assertEqual([], sleep_calls)


class DeepLinkListenForwardFolderCase(unittest.TestCase):
    def test_pikpak_archive_after_forward_uses_explicit_channel_source_folder(self):
        from module.downloader import TelegramRestrictedMediaDownloader

        archive_calls = []
        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.archive_pikpak_item = lambda **kwargs: (
            archive_calls.append(kwargs) or SimpleNamespace(ok=True, status='moved', archive_path='x', message='')
        )
        downloader._log_system_chain = lambda **kwargs: None

        bot_message = SimpleNamespace(
            id=99,
            video=SimpleNamespace(file_size=10, file_name='video.mp4'),
            chat=SimpleNamespace(id='bot-chat', username='a82bot'),
            link=None,
            get_media_group=None,
        )

        asyncio.run(downloader._run_pikpak_archive_after_forward(
            message=bot_message,
            origin_chat_id='bot-chat',
            message_id=99,
            source_folder='swag_vip',
            source_link='https://t.me/swag_vip/1',
        ))

        self.assertEqual(1, len(archive_calls))
        self.assertEqual('swag_vip', archive_calls[0]['source_folder'])
        self.assertEqual('https://t.me/swag_vip/1', archive_calls[0]['source_link'])

    def test_pikpak_archive_after_forward_enriches_media_group_folder_with_caption(self):
        from module.downloader import TelegramRestrictedMediaDownloader

        archive_calls = []
        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.archive_pikpak_item = lambda **kwargs: (
            archive_calls.append(kwargs) or SimpleNamespace(ok=True, status='moved', archive_path='x', message='')
        )
        downloader._log_system_chain = lambda **kwargs: None

        members = []

        async def get_media_group():
            return members

        trigger = SimpleNamespace(
            id=93670,
            caption=None,
            text=None,
            web_page=None,
            photo=SimpleNamespace(file_size=10, file_unique_id='photoA'),
            chat=SimpleNamespace(id=-1001, username='chengdudiyi8', title=None),
            link='https://t.me/chengdudiyi8/93670',
            get_media_group=get_media_group,
        )
        captioned = SimpleNamespace(
            id=93671,
            caption='继父出差了妈妈自己在家',
            text=None,
            web_page=None,
            video=SimpleNamespace(file_size=20, file_name='b.mp4'),
            chat=SimpleNamespace(id=-1001, username='chengdudiyi8', title=None),
            link='https://t.me/chengdudiyi8/93671',
            get_media_group=get_media_group,
        )
        members.extend([trigger, captioned])

        async def _run_and_drain():
            await downloader._run_pikpak_archive_after_forward(
                message=trigger,
                origin_chat_id=-1001,
                message_id=93670,
                media_group=[93670, 93671],
                source_folder='chengdudiyi8/_未知作者/93670',
                source_link='https://t.me/chengdudiyi8/93670',
            )
            # Archive is fire-and-forget via create_task(to_thread); drain before assert.
            pending = [
                task for task in asyncio.all_tasks()
                if task is not asyncio.current_task()
            ]
            if pending:
                await asyncio.gather(*pending)

        asyncio.run(_run_and_drain())

        self.assertEqual(2, len(archive_calls))
        # ID-only may enrich once; existing `_未知作者` parent must stay (not flatten).
        expected = 'chengdudiyi8/_未知作者/93670 - 继父出差了妈妈自己在家'
        self.assertEqual(expected, archive_calls[0]['source_folder'])
        self.assertEqual(expected, archive_calls[1]['source_folder'])


class WebRangeAlbumArchiveCase(unittest.TestCase):
    def test_web_target_album_uses_min_id_even_when_caller_passes_member_range_id(self):
        """Range loop used to pass each member id as range_message_id, splitting folders."""
        from module.core.media_types import MEDIA_TYPES_DEFAULT, build_runtime_message_filter
        from module.transfer.runner import WebTransferRunner
        from module.transfer_store import TransferStore, TransferStatus

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/chengdudiyi8',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=73464,
                end_id=73465,
            )
            task = store.get_task(task_id)
            members = []

            async def get_media_group():
                return members

            photo = SimpleNamespace(
                id=73464,
                caption=(
                    '#示例\n'
                    '\n'
                    '【60分原创户外】拉着气质姐姐铁路旁裤里丝双洞齐插\n'
                ),
                text=None,
                web_page=None,
                photo=SimpleNamespace(file_id='p1', file_unique_id='pu1', file_size=10),
                video=None,
                document=None,
                audio=None,
                animation=None,
                voice=None,
                video_note=None,
                media_group_id='album-1',
                empty=False,
                chat=SimpleNamespace(id=-1001, username='chengdudiyi8', title=None),
                link='https://t.me/chengdudiyi8/73464',
                get_media_group=get_media_group,
            )
            video = SimpleNamespace(
                id=73465,
                caption=None,
                text=None,
                web_page=None,
                photo=None,
                video=SimpleNamespace(
                    file_name='5月13日.mp4',
                    file_id='v1',
                    mime_type='video/mp4',
                    file_size=20,
                ),
                document=None,
                audio=None,
                animation=None,
                voice=None,
                video_note=None,
                media_group_id='album-1',
                empty=False,
                chat=SimpleNamespace(id=-1001, username='chengdudiyi8', title=None),
                link='https://t.me/chengdudiyi8/73465',
                get_media_group=get_media_group,
            )
            members.extend([photo, video])

            host = SimpleNamespace(
                app=SimpleNamespace(client=object()),
                gc=SimpleNamespace(
                    message_filter={
                        'enabled': False,
                        'media_types': dict(MEDIA_TYPES_DEFAULT),
                    },
                    get_deep_link_bot_whitelist=lambda: [],
                    get_deep_link_timeout_seconds=lambda: 30,
                    get_deep_link_min_interval_seconds=lambda: 0,
                    get_deep_link_settle_seconds=lambda: 0,
                    get_deep_link_max_pages=lambda: 20,
                    get_deep_link_page_click_interval_seconds=lambda: 0,
                ),
                transfer_store=store,
                inherit_media_group_title=lambda group, propagate_to=None: None,
                # Non-PikPak path still writes source_folder on the item; enough to assert album id.
                is_pikpak_target=lambda *_a, **_k: False,
                get_task_target_size_limit_error=lambda *_a, **_k: None,
                get_message_media_target_limit_meta=lambda message, post_message_id=None: {
                    'file_name': getattr(getattr(message, 'video', None), 'file_name', None)
                    or 'photo.jpg',
                    'file_size': 10,
                },
                get_message_media_archive_filename=lambda message, post_message_id=None: None,
                refresh_transfer_task_counts=lambda tid: store.refresh_task_counts(tid),
                skip_empty_transfer_source_message=lambda **_k: None,
                skip_transfer_item_for_media_type=lambda **_k: None,
                skip_transfer_item_for_target_limit=lambda **_k: None,
                get_deep_link_resolver=lambda: None,
            )
            host.runtime_message_filter = lambda override=None: build_runtime_message_filter(
                host.gc.message_filter,
                override,
            )

            async def fake_forward(**_kwargs):
                return SimpleNamespace(id=900)

            host.forward = fake_forward
            runner = WebTransferRunner(host)

            asyncio.run(runner.transfer_message_to_web_target(
                task=task,
                message=video,
                origin_chat_id=-1001,
                target_chat_id='pikpak',
                source_link='https://t.me/chengdudiyi8/73465',
                range_message_id=73465,
            ))

            items = store.list_items(task_id)
            self.assertEqual(1, len(items))
            expected = (
                'chengdudiyi8/73464 - 【60分原创户外】拉着气质姐姐铁路旁裤里丝双洞齐插'
            )
            self.assertEqual(expected, items[0]['source_folder'])
            self.assertEqual(73465, items[0]['range_message_id'])
            self.assertEqual(73465, items[0]['source_message_id'])
            self.assertEqual(TransferStatus.SUCCESS, items[0]['status'])
            _close_store(store)

    def test_resolve_web_range_album_skips_secondary_ids_via_shared_folder(self):
        from module.transfer.runner import WebTransferRunner

        members = []

        async def get_media_group():
            return members

        photo = SimpleNamespace(
            id=10,
            caption='正文标题',
            text=None,
            web_page=None,
            photo=SimpleNamespace(file_id='p1'),
            video=None,
            document=None,
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            media_group_id='g',
            chat=SimpleNamespace(username='chan'),
            link='https://t.me/chan/10',
            get_media_group=get_media_group,
        )
        video = SimpleNamespace(
            id=11,
            caption=None,
            text=None,
            web_page=None,
            photo=None,
            video=SimpleNamespace(file_name='x.mp4', file_id='v1'),
            document=None,
            audio=None,
            animation=None,
            voice=None,
            video_note=None,
            media_group_id='g',
            chat=SimpleNamespace(username='chan'),
            link='https://t.me/chan/11',
            get_media_group=get_media_group,
        )
        members.extend([photo, video])
        host = SimpleNamespace(inherit_media_group_title=lambda group, propagate_to=None: None)
        runner = WebTransferRunner(host)
        got_members, shared_id, shared_folder = asyncio.run(
            runner._resolve_web_range_album(
                video,
                origin_chat_id=-1001,
                source_link='https://t.me/chan/11',
            )
        )
        self.assertEqual([photo, video], got_members)
        self.assertEqual(10, shared_id)
        self.assertEqual('chan/10 - 正文标题', shared_folder)


if __name__ == '__main__':
    unittest.main()
