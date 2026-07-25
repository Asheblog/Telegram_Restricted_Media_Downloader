# coding=UTF-8
"""Keyword Blacklist must see album archive titles on the triggering update message."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.core.filter import MessageFilter
from module.downloader import TelegramRestrictedMediaDownloader


SPAM_CAPTION = '🥳🥳给大家推荐一个高质量的sm同城约炮圈里面汇聚全国上万名有需求的女m‼️🥳'


def _keyword_filter():
    return MessageFilter({
        'enabled': True,
        'media_types': {t: True for t in MessageFilter.MEDIA_TYPES},
        'keywords': {
            'enabled': True,
            'words': ['给大家推荐', '同城约炮', '同城'],
        },
    })


class KeywordAlbumInheritFilterCase(unittest.TestCase):
    def test_inherit_propagates_album_title_to_distinct_trigger_message(self):
        """get_media_group() returns new objects; trigger update must still get the title."""
        captioned = SimpleNamespace(
            id=5777,
            caption=SPAM_CAPTION,
            text=None,
            web_page=None,
            photo=SimpleNamespace(file_name=None),
        )
        sibling = SimpleNamespace(
            id=5780,
            caption=None,
            text=None,
            web_page=None,
            photo=SimpleNamespace(file_name=None),
        )
        # Distinct object with same id as sibling — mimics update message vs API fetch.
        trigger = SimpleNamespace(
            id=5780,
            caption=None,
            text=None,
            web_page=None,
            photo=SimpleNamespace(file_name=None),
        )

        TelegramRestrictedMediaDownloader.inherit_media_group_title(
            [captioned, sibling],
            propagate_to=trigger,
        )

        self.assertTrue(getattr(trigger, '_trmd_source_title', None))
        self.assertIn('同城约炮', trigger._trmd_source_title)

        f = _keyword_filter()
        self.assertFalse(f.should_pass(trigger))
        self.assertIn('命中过滤关键词', f.get_reject_reason(trigger) or '')


class KeywordListenForwardSourceFilterCase(unittest.TestCase):
    def test_listen_forward_skips_spam_album_before_deep_link_and_logs_filter_reject(self):
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        system_logs = []
        watch_events = []
        forward_calls = []

        members = []

        async def get_media_group():
            return members

        captioned = SimpleNamespace(
            id=5777,
            caption=SPAM_CAPTION,
            text=None,
            web_page=None,
            photo=SimpleNamespace(file_name=None, file_size=10),
            chat=SimpleNamespace(id=-1002162903654, username='jibahenyanga'),
            link='https://t.me/jibahenyanga/5777',
            media_group_id='album-1',
            get_media_group=get_media_group,
        )
        # API-fetched sibling — different object from the update handler message.
        fetched_sibling = SimpleNamespace(
            id=5780,
            caption=None,
            text=None,
            web_page=None,
            photo=SimpleNamespace(file_name=None, file_size=11),
            chat=SimpleNamespace(id=-1002162903654, username='jibahenyanga'),
            link='https://t.me/jibahenyanga/5780',
            media_group_id='album-1',
            get_media_group=get_media_group,
        )
        trigger = SimpleNamespace(
            id=5780,
            caption=None,
            text=None,
            web_page=None,
            photo=SimpleNamespace(file_name=None, file_size=11),
            chat=SimpleNamespace(id=-1002162903654, username='jibahenyanga'),
            link='https://t.me/jibahenyanga/5780',
            media_group_id='album-1',
            get_media_group=get_media_group,
        )
        members.extend([captioned, fetched_sibling])

        downloader.app = SimpleNamespace(client=object())
        downloader.gc = SimpleNamespace(
            message_filter={
                'enabled': True,
                'media_types': {t: True for t in MessageFilter.MEDIA_TYPES},
                'keywords': {
                    'enabled': True,
                    'words': ['给大家推荐', '同城约炮'],
                },
            },
            get_deep_link_bot_whitelist=lambda: ['some_bot'],
            get_deep_link_timeout_seconds=lambda: 60,
            get_deep_link_min_interval_seconds=lambda: 0,
            get_deep_link_settle_seconds=lambda: 0,
            get_deep_link_max_pages=lambda: 1,
            get_deep_link_page_click_interval_seconds=lambda: 0,
        )
        downloader.listen_forward_chat = {
            'https://t.me/jibahenyanga https://t.me/pikpak_bot --resolve-deep-link': object()
        }
        downloader.handle_media_groups = {}
        downloader.watch_manager = SimpleNamespace(
            forward_watch_id=lambda rule: f'forward:{rule}',
        )
        downloader._message_chain_context = lambda message, watch_id=None: (
            'trace-1', getattr(message.chat, 'id', None), message.id
        )
        downloader._log_system_chain = lambda **kwargs: system_logs.append(kwargs)
        downloader._record_watch_event = lambda *args, **kwargs: watch_events.append((args, kwargs))
        downloader._watch_media_types_override = lambda watch_id: None
        downloader.runtime_message_filter = lambda override=None: MessageFilter(
            downloader.gc.message_filter
        )
        downloader.inherit_media_group_title = (
            TelegramRestrictedMediaDownloader.inherit_media_group_title
        )

        async def fake_forward(**kwargs):
            forward_calls.append(kwargs)

        downloader.forward = fake_forward
        downloader._invoke = lambda name, **kwargs: fake_forward(**kwargs)

        resolve_called = {'n': 0}

        class FakeResolver:
            async def resolve(self, **kwargs):
                resolve_called['n'] += 1
                raise AssertionError('deep link resolve must not run after keyword reject')

        downloader.get_deep_link_resolver = lambda: FakeResolver()

        async def fake_parse_link(client, link):
            if 'jibahenyanga' in link:
                return {'chat_id': 'jibahenyanga'}
            if 'pikpak_bot' in link:
                return {'chat_id': 'pikpak_bot'}
            return {'chat_id': 'unknown'}

        with patch('module.transfer.live_transfer.parse_link', side_effect=fake_parse_link):
            asyncio.run(downloader.listen_forward(object(), trigger))

        self.assertEqual([], forward_calls)
        self.assertEqual(0, resolve_called['n'])
        reject_logs = [
            entry for entry in system_logs
            if entry.get('category') == 'filter' and entry.get('stage') == 'filter_reject'
        ]
        self.assertEqual(1, len(reject_logs))
        self.assertIn('命中过滤关键词', reject_logs[0].get('message') or '')


if __name__ == '__main__':
    unittest.main()
