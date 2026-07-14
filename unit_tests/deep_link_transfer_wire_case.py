# coding=UTF-8
import asyncio
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from unit_tests.pyrogram_stub import install_pyrogram_stub
install_pyrogram_stub()

from module.core.media_types import MEDIA_TYPES_DEFAULT, build_runtime_message_filter
from module.persistence.transfer_store import TransferStore
from module.transfer.deep_link import DeepLinkResolveError
from module.transfer.runner import WebTransferRunner
from module.transfer_store import TransferStatus


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
            host.get_message_media_target_limit_meta = lambda message: (
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
            host.get_message_media_target_limit_meta = lambda message: (
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


if __name__ == '__main__':
    unittest.main()
