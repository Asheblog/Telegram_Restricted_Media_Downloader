# coding=UTF-8
import asyncio
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from module.transfer.deep_link import DeepLinkResolveError, DeepLinkResolver


def _source_message_with_deep_link(bot='a82bot', param='v_abc'):
    return SimpleNamespace(
        reply_markup=SimpleNamespace(inline_keyboard=[[
            SimpleNamespace(url=f'https://t.me/{bot}?start={param}'),
        ]]),
        text=None,
        caption=None,
        entities=None,
        caption_entities=None,
    )


def _make_history_client(messages_by_poll):
    """messages_by_poll: list of lists; each poll yields one list of messages."""
    poll_idx = {'i': 0}

    async def get_chat_history(bot_username, limit=10):
        idx = poll_idx['i']
        poll_idx['i'] = idx + 1
        batch = messages_by_poll[min(idx, len(messages_by_poll) - 1)]
        for msg in batch:
            yield msg

    client = SimpleNamespace()
    client.resolve_peer = AsyncMock(return_value=object())
    client.invoke = AsyncMock()
    client.get_chat_history = get_chat_history
    return client


class DeepLinkResolverCase(unittest.TestCase):
    def test_resolve_success_returns_video_message_with_meta(self):
        async def run_case():
            started = time.time()
            video_msg = SimpleNamespace(
                video=object(),
                document=None,
                animation=None,
                outgoing=False,
                date=started,
            )
            client = _make_history_client([[video_msg]])
            resolver = DeepLinkResolver(timeout_seconds=0.3, poll_interval=0.05)
            source = _source_message_with_deep_link('a82bot', 'v_abc')

            with patch.object(resolver, 'start_bot', new=AsyncMock()) as start_bot:
                result = await resolver.resolve(
                    client, source, whitelist=['a82bot'],
                )
                start_bot.assert_awaited_once_with(client, 'a82bot', 'v_abc')

            self.assertIs(result, video_msg)
            self.assertEqual(
                {'bot': 'a82bot', 'start_param': 'v_abc'},
                getattr(result, '_deep_link_meta'),
            )

        asyncio.run(run_case())

    def test_resolve_timeout_on_text_only_raises(self):
        async def run_case():
            started = time.time()
            text_msg = SimpleNamespace(
                video=None,
                document=None,
                animation=None,
                outgoing=False,
                date=started,
                text='hello',
            )
            client = _make_history_client([[text_msg]])
            resolver = DeepLinkResolver(timeout_seconds=0.3, poll_interval=0.05)
            source = _source_message_with_deep_link()

            with patch.object(resolver, 'start_bot', new=AsyncMock()):
                with self.assertRaises(DeepLinkResolveError):
                    await resolver.resolve(client, source, whitelist=['a82bot'])

        asyncio.run(run_case())

    def test_resolve_serial_lock_blocks_second_start_bot(self):
        async def run_case():
            started = time.time()
            video_msg = SimpleNamespace(
                video=object(),
                document=None,
                animation=None,
                outgoing=False,
                date=started,
            )
            client = _make_history_client([[video_msg]])
            resolver = DeepLinkResolver(timeout_seconds=0.5, poll_interval=0.05)
            source = _source_message_with_deep_link()

            order = []
            first_hold = asyncio.Event()
            second_may_enter = asyncio.Event()

            async def slow_start_bot(client, bot_username, start_param):
                order.append(('start', bot_username))
                first_hold.set()
                await second_may_enter.wait()
                await asyncio.sleep(0.05)
                order.append(('start_done', bot_username))

            with patch.object(resolver, 'start_bot', new=AsyncMock(side_effect=slow_start_bot)):
                t1 = asyncio.create_task(
                    resolver.resolve(client, source, whitelist=['a82bot']),
                )
                await first_hold.wait()

                t2 = asyncio.create_task(
                    resolver.resolve(client, source, whitelist=['a82bot']),
                )
                # Give t2 a chance to race ahead if lock were broken.
                await asyncio.sleep(0.08)
                self.assertEqual([('start', 'a82bot')], order)

                second_may_enter.set()
                await asyncio.gather(t1, t2)

            self.assertEqual(
                [('start', 'a82bot'), ('start_done', 'a82bot'),
                 ('start', 'a82bot'), ('start_done', 'a82bot')],
                order,
            )

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
