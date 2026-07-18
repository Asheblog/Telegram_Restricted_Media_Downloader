# coding=UTF-8
import asyncio
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from unit_tests.pyrogram_stub import install_pyrogram_stub
install_pyrogram_stub()

from module.persistence.transfer_store import TransferStore
from module.transfer.runner import WebTransferRunner


def _import_downloader_class():
    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0]]
        from module.downloader import TelegramRestrictedMediaDownloader
        return TelegramRestrictedMediaDownloader
    finally:
        sys.argv = original_argv


def _close_store(store):
    conn = getattr(getattr(store, '_tls', None), 'conn', None)
    if conn is not None:
        conn.close()
        store._tls.conn = None


def _text_comment(msg_id: int, text: str, chat_id='discussion-chat'):
    return SimpleNamespace(
        id=msg_id,
        text=text,
        caption=None,
        entities=None,
        caption_entities=None,
        reply_markup=None,
        video=None,
        photo=None,
        document=None,
        animation=None,
        audio=None,
        voice=None,
        video_note=None,
        media_group_id=None,
        link=f'https://t.me/c/{chat_id}/{msg_id}',
        chat=SimpleNamespace(id=chat_id, username=None),
        empty=False,
    )


def _deep_link_comment(msg_id: int, bot='a82bot', param='pack1', chat_id='discussion-chat'):
    msg = _text_comment(msg_id, f'click https://t.me/{bot}?start={param}', chat_id=chat_id)
    msg.entities = [
        SimpleNamespace(
            url=f'https://t.me/{bot}?start={param}',
            type='text_link',
            offset=6,
            length=5,
        )
    ]
    return msg


class DiscussionDeepLinkFilterListenCase(unittest.TestCase):
    def test_resolve_mode_skips_bare_text_forwards_only_resolved_deep_link(self):
        TelegramRestrictedMediaDownloader = _import_downloader_class()

        bare = _text_comment(11, '酷溜')
        deep = _deep_link_comment(12, 'a82bot', 'pack1')
        resolved = SimpleNamespace(
            id=99,
            video=SimpleNamespace(file_size=10, file_name='a.mp4'),
            document=None,
            animation=None,
            photo=None,
            chat=SimpleNamespace(id='bot-chat', username='a82bot'),
            media_group_id=None,
            _deep_link_meta={'bot': 'a82bot', 'start_param': 'pack1'},
        )

        class FakeClient:
            async def get_discussion_message(self, chat_id, message_id):
                raise ValueError('use source thread')

            async def get_discussion_replies(self, chat_id, message_id):
                yield bare
                yield deep

        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.app = SimpleNamespace(client=FakeClient())
        downloader.gc = SimpleNamespace(
            get_deep_link_bot_whitelist=lambda: ['a82bot'],
            get_deep_link_timeout_seconds=lambda: 60,
            get_deep_link_min_interval_seconds=lambda: 0,
            get_deep_link_settle_seconds=lambda: 0,
            get_deep_link_max_pages=lambda: 20,
            get_deep_link_page_click_interval_seconds=lambda: 0,
            forward_type={'text': True, 'video': True},
        )
        downloader.check_type = lambda message: bool(
            getattr(message, 'text', None) or getattr(message, 'video', None)
        )
        downloader._log_system_chain = lambda **kwargs: None
        forward_calls = []

        async def fake_forward(**kwargs):
            forward_calls.append(kwargs)
            return SimpleNamespace(id=100)

        downloader.forward = fake_forward
        downloader.get_deep_link_resolver = lambda: SimpleNamespace(
            resolve=AsyncMock(return_value=[resolved]),
        )

        count = asyncio.run(downloader.forward_discussion_replies(
            client=SimpleNamespace(),
            source_chat_id='source-chat',
            source_message_id=5,
            target_chat_id='target-chat',
            target_link='https://t.me/mypikpakbot',
            done_notice=False,
            resolve_deep_link=True,
        ))

        self.assertEqual(1, count)
        self.assertEqual(1, len(forward_calls))
        self.assertIs(resolved, forward_calls[0]['message'])
        self.assertNotEqual(bare, forward_calls[0]['message'])

    def test_without_resolve_mode_still_forwards_check_type_text(self):
        TelegramRestrictedMediaDownloader = _import_downloader_class()

        bare = _text_comment(11, '酷溜')

        class FakeClient:
            async def get_discussion_message(self, chat_id, message_id):
                raise ValueError('use source thread')

            async def get_discussion_replies(self, chat_id, message_id):
                yield bare

        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.app = SimpleNamespace(client=FakeClient())
        downloader.gc = SimpleNamespace(
            get_deep_link_bot_whitelist=lambda: ['a82bot'],
            forward_type={'text': True},
        )
        downloader.check_type = lambda message: bool(getattr(message, 'text', None))
        downloader._log_system_chain = lambda **kwargs: None
        forward_calls = []

        async def fake_forward(**kwargs):
            forward_calls.append(kwargs)
            return SimpleNamespace(id=100)

        downloader.forward = fake_forward

        count = asyncio.run(downloader.forward_discussion_replies(
            client=SimpleNamespace(),
            source_chat_id='source-chat',
            source_message_id=5,
            target_chat_id='target-chat',
            target_link='https://t.me/mypikpakbot',
            done_notice=False,
            resolve_deep_link=False,
        ))

        self.assertEqual(1, count)
        self.assertEqual(1, len(forward_calls))
        self.assertIs(bare, forward_calls[0]['message'])


class DiscussionDeepLinkFilterWebCase(unittest.TestCase):
    def test_resolve_mode_skips_bare_text_comments(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/mypikpakbot',
                include_comment=True,
                resolve_deep_link=True,
            )
            task = store.get_task(task_id)
            bare = _text_comment(11, '酷溜')
            deep = _deep_link_comment(12, 'a82bot', 'pack1')

            class FakeClient:
                async def get_discussion_message(self, chat_id, message_id):
                    raise ValueError('use source thread')

                async def get_discussion_replies(self, chat_id, message_id):
                    yield bare
                    yield deep

            transfer_calls = []

            async def fake_transfer(**kwargs):
                transfer_calls.append(kwargs)
                return False

            async def no_wait():
                return None

            host = SimpleNamespace(
                app=SimpleNamespace(client=FakeClient()),
                gc=SimpleNamespace(
                    get_deep_link_bot_whitelist=lambda: ['a82bot'],
                    forward_type={'text': True, 'video': True},
                ),
                transfer_store=store,
                check_type=lambda message: bool(
                    getattr(message, 'text', None) or getattr(message, 'video', None)
                ),
                find_resumable_transfer_item=lambda *a, **k: None,
                transfer_message_to_web_target=fake_transfer,
                wait_between_transfer_messages=no_wait,
            )
            runner = WebTransferRunner(host)

            reply_count, _ = asyncio.run(runner.transfer_web_discussion_replies_to_target(
                task=task,
                source_chat_id='source-chat',
                source_message_id=1,
                target_chat_id='target-chat',
                expected_total=1,
            ))

            self.assertEqual(1, reply_count)
            self.assertEqual(1, len(transfer_calls))
            self.assertIs(deep, transfer_calls[0]['message'])
            self.assertNotIn(bare, [c['message'] for c in transfer_calls])
            _close_store(store)

    def test_resume_discussion_download_keeps_parent_post_source_folder(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/mychannel/7',
                'https://t.me/mypikpakbot',
                include_comment=True,
                resolve_deep_link=True,
                target_profile='pikpak',
            )
            task = store.get_task(task_id)
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='discussion-chat',
                source_message_id=12,
                range_message_id=7,
                source_link='https://t.me/discussgrp/12',
                target_link='https://t.me/mypikpakbot',
                source_folder='mychannel/_未知作者/7 - parent title',
                phase='downloading',
                status='running',
            )
            created_downloads = []

            def build_meta(**kwargs):
                return {
                    'link': kwargs.get('task', task).get('target_link'),
                    'source_link': kwargs.get('source_link'),
                    'source_folder': kwargs.get('source_folder') or 'discussgrp/_未知作者/7',
                    'range_message_id': kwargs.get('range_message_id'),
                }

            async def create_download_task(**kwargs):
                created_downloads.append(kwargs)
                return {'status': 'success'}

            host = SimpleNamespace(
                build_transfer_upload_meta=build_meta,
                create_download_task=create_download_task,
            )
            runner = WebTransferRunner(host)

            asyncio.run(runner.resume_transfer_item_download(
                task=task,
                item=store.get_item(item_id),
                range_message_id=7,
            ))

            self.assertEqual(1, len(created_downloads))
            self.assertEqual(
                'mychannel/_未知作者/7 - parent title',
                created_downloads[0]['with_upload']['source_folder'],
            )
            _close_store(store)


if __name__ == '__main__':
    unittest.main()
