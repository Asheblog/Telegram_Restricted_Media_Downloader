# coding=UTF-8
import asyncio
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from unit_tests.pyrogram_stub import install_pyrogram_stub
install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.transfer.deep_link import DeepLinkResolveError, DeepLinkResolver
sys.argv = _ORIGINAL_ARGV


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
                start_bot.assert_awaited_once()
                self.assertEqual(
                    (client, 'a82bot', 'v_abc'),
                    start_bot.await_args.args,
                )
                self.assertIn('deadline', start_bot.await_args.kwargs)

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
            resolver = DeepLinkResolver(timeout_seconds=2.0, poll_interval=0.05)
            source = _source_message_with_deep_link()

            order = []
            first_hold = asyncio.Event()
            second_may_enter = asyncio.Event()

            async def slow_start_bot(client, bot_username, start_param, deadline=None):
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

    def test_start_bot_waits_and_retries_flood_wait(self):
        async def run_case():
            from pyrogram.errors import FloodWait

            client = SimpleNamespace(
                resolve_peer=AsyncMock(return_value=object()),
                invoke=AsyncMock(side_effect=[FloodWait(3), None]),
                rnd_id=lambda: 1,
            )
            resolver = DeepLinkResolver(timeout_seconds=0.3, poll_interval=0.05)

            with patch('module.transfer.deep_link.asyncio.sleep', new=AsyncMock()) as sleep_mock:
                await resolver.start_bot(client, 'a82bot', 'v_abc')

            self.assertEqual(2, client.invoke.await_count)
            sleep_mock.assert_awaited_once_with(3)

        asyncio.run(run_case())

    def test_resolve_enforces_min_interval_between_start_bot_calls(self):
        async def run_case():
            resolver = DeepLinkResolver(min_interval_seconds=2.0)
            sleeps = []

            async def record_sleep(seconds):
                sleeps.append(seconds)

            with patch('module.transfer.deep_link.asyncio.sleep', new=AsyncMock(side_effect=record_sleep)), \
                    patch('module.transfer.deep_link.time.time', return_value=100.5):
                resolver._last_start_bot_at = 0.0
                await resolver._wait_min_interval()
                self.assertEqual([], sleeps)
                resolver._last_start_bot_at = 100.0
                await resolver._wait_min_interval()

            self.assertEqual([1.5], sleeps)

        asyncio.run(run_case())

    def test_resolve_times_out_when_chat_history_hangs(self):
        async def run_case():
            async def hung_history(bot_username, limit=10):
                await asyncio.Event().wait()
                if False:
                    yield None

            client = SimpleNamespace(
                resolve_peer=AsyncMock(return_value=object()),
                invoke=AsyncMock(),
                get_chat_history=hung_history,
                rnd_id=lambda: 1,
            )
            resolver = DeepLinkResolver(timeout_seconds=0.3, poll_interval=0.05)
            t0 = time.time()
            with self.assertRaises(DeepLinkResolveError):
                await asyncio.wait_for(
                    resolver.resolve(
                        client, _source_message_with_deep_link(), whitelist=['a82bot'],
                    ),
                    timeout=2.0,
                )
            self.assertLess(time.time() - t0, 1.5)

        asyncio.run(run_case())

    def test_resolve_times_out_when_flood_wait_exceeds_budget(self):
        async def run_case():
            from pyrogram.errors import FloodWait

            client = SimpleNamespace(
                resolve_peer=AsyncMock(return_value=object()),
                invoke=AsyncMock(side_effect=FloodWait(30)),
                get_chat_history=AsyncMock(),
                rnd_id=lambda: 1,
            )
            resolver = DeepLinkResolver(timeout_seconds=0.3, poll_interval=0.05)
            real_sleep = asyncio.sleep

            async def yield_sleep(seconds):
                await real_sleep(0)

            t0 = time.time()
            with patch('module.transfer.deep_link.asyncio.sleep', new=yield_sleep):
                with self.assertRaises(DeepLinkResolveError):
                    await asyncio.wait_for(
                        resolver.resolve(
                            client, _source_message_with_deep_link(), whitelist=['a82bot'],
                        ),
                        timeout=2.0,
                    )
            self.assertLess(time.time() - t0, 1.5)

        asyncio.run(run_case())

    def test_resolve_releases_lock_after_hung_history_timeout(self):
        async def run_case():
            entered = asyncio.Event()
            hang = True

            async def history(bot_username, limit=10):
                if hang:
                    entered.set()
                    await asyncio.Event().wait()
                    if False:
                        yield None
                    return
                started = time.time()
                yield SimpleNamespace(
                    video=object(),
                    document=None,
                    animation=None,
                    outgoing=False,
                    date=started,
                )

            client = SimpleNamespace(
                resolve_peer=AsyncMock(return_value=object()),
                invoke=AsyncMock(),
                get_chat_history=history,
                rnd_id=lambda: 1,
            )
            resolver = DeepLinkResolver(timeout_seconds=0.25, poll_interval=0.05, min_interval_seconds=0)
            first = asyncio.create_task(
                resolver.resolve(client, _source_message_with_deep_link(), whitelist=['a82bot']),
            )
            await entered.wait()
            with self.assertRaises(DeepLinkResolveError):
                await asyncio.wait_for(first, timeout=2.0)
            hang = False
            result = await asyncio.wait_for(
                resolver.resolve(client, _source_message_with_deep_link(), whitelist=['a82bot']),
                timeout=1.5,
            )
            self.assertTrue(getattr(result, 'video', None))

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
