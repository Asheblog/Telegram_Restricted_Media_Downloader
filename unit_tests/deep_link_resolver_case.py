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
from module.transfer.deep_link import (
    DeepLinkResolveError,
    DeepLinkResolver,
    text_has_session_failure,
)
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
    def test_message_has_resolvable_media_skips_empty(self):
        self.assertFalse(DeepLinkResolver.message_has_resolvable_media(None))
        self.assertFalse(
            DeepLinkResolver.message_has_resolvable_media(
                SimpleNamespace(empty=True, photo=object(), video=None, document=None, animation=None)
            )
        )
        self.assertTrue(
            DeepLinkResolver.message_has_resolvable_media(
                SimpleNamespace(empty=False, photo=object(), video=None, document=None, animation=None)
            )
        )

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
            resolver = DeepLinkResolver(
                timeout_seconds=0.3, poll_interval=0.05, settle_seconds=0, min_interval_seconds=0,
            )
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

            self.assertEqual([video_msg], result)
            self.assertEqual(
                {'bot': 'a82bot', 'start_param': 'v_abc'},
                getattr(result[0], '_deep_link_meta'),
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
            resolver = DeepLinkResolver(
                timeout_seconds=0.3, poll_interval=0.05, settle_seconds=0, min_interval_seconds=0,
            )
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
            resolver = DeepLinkResolver(
                timeout_seconds=2.0, poll_interval=0.05, settle_seconds=0, min_interval_seconds=0,
            )
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
            resolver = DeepLinkResolver(
                timeout_seconds=0.3, poll_interval=0.05, settle_seconds=0, min_interval_seconds=0,
            )

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
            resolver = DeepLinkResolver(
                timeout_seconds=0.3, poll_interval=0.05, settle_seconds=0, min_interval_seconds=0,
            )
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
            resolver = DeepLinkResolver(
                timeout_seconds=0.3, poll_interval=0.05, settle_seconds=0, min_interval_seconds=0,
            )
            real_sleep = asyncio.sleep

            async def yield_sleep(seconds):
                await real_sleep(0)

            t0 = time.time()
            with patch('module.transfer.deep_link.asyncio.sleep', new=yield_sleep):
                with self.assertRaises(DeepLinkResolveError) as ctx:
                    await asyncio.wait_for(
                        resolver.resolve(
                            client, _source_message_with_deep_link(), whitelist=['a82bot'],
                        ),
                        timeout=2.0,
                    )
            self.assertLess(time.time() - t0, 1.5)
            self.assertIn('限流', str(ctx.exception))

        asyncio.run(run_case())

    def test_resolve_continues_after_pagination_click_fail_until_media(self):
        """Click fail with zero media must not abort; keep polling until media or deadline."""
        async def run_case():
            t0_abs = {'v': None}
            clicks = {'n': 0}

            async def get_chat_history(bot_username, limit=10):
                now = time.time()
                if t0_abs['v'] is None:
                    t0_abs['v'] = now
                elapsed = now - t0_abs['v']
                menu = SimpleNamespace(
                    id=2,
                    video=None,
                    document=None,
                    animation=None,
                    photo=None,
                    outgoing=False,
                    date=t0_abs['v'],
                    chat=SimpleNamespace(id='bot'),
                    reply_markup=SimpleNamespace(inline_keyboard=[[
                        SimpleNamespace(text='下一页', callback_data=b'n1', url=None),
                    ]]),
                )

                async def boom(*_a, **_k):
                    clicks['n'] += 1
                    raise RuntimeError('QUERY_ID_INVALID')

                menu.click = boom
                msgs = [menu]
                if elapsed >= 0.35:
                    msgs.append(SimpleNamespace(
                        id=99,
                        video=object(),
                        document=None,
                        animation=None,
                        photo=None,
                        outgoing=False,
                        date=now,
                        chat=SimpleNamespace(id='bot'),
                        reply_markup=None,
                    ))
                for msg in msgs:
                    yield msg

            client = SimpleNamespace(
                resolve_peer=AsyncMock(return_value=object()),
                invoke=AsyncMock(),
                get_chat_history=get_chat_history,
                rnd_id=lambda: 1,
            )
            resolver = DeepLinkResolver(
                timeout_seconds=2.0,
                poll_interval=0.08,
                settle_seconds=0,
                min_interval_seconds=0,
                page_click_interval_seconds=0.02,
            )
            t0 = time.time()
            result = await resolver.resolve(
                client, _source_message_with_deep_link(), whitelist=['a82bot'],
            )
            self.assertEqual(1, len(result))
            self.assertTrue(getattr(result[0], 'video', None))
            self.assertGreaterEqual(clicks['n'], 1)
            self.assertGreaterEqual(time.time() - t0, 0.3)

        asyncio.run(run_case())

    def test_resolve_waits_full_timeout_after_click_fail_with_no_media(self):
        async def run_case():
            started = time.time()

            async def get_chat_history(bot_username, limit=10):
                menu = SimpleNamespace(
                    id=2,
                    video=None,
                    document=None,
                    animation=None,
                    photo=None,
                    outgoing=False,
                    date=started,
                    chat=SimpleNamespace(id='bot'),
                    reply_markup=SimpleNamespace(inline_keyboard=[[
                        SimpleNamespace(text='1', callback_data=b'g1', url=None),
                    ]]),
                )

                async def boom(*_a, **_k):
                    raise RuntimeError('btn invalid')

                menu.click = boom
                yield menu

            client = SimpleNamespace(
                resolve_peer=AsyncMock(return_value=object()),
                invoke=AsyncMock(),
                get_chat_history=get_chat_history,
                rnd_id=lambda: 1,
            )
            resolver = DeepLinkResolver(
                timeout_seconds=0.5,
                poll_interval=0.08,
                settle_seconds=0,
                min_interval_seconds=0,
                page_click_interval_seconds=0.02,
            )
            t0 = time.time()
            with self.assertRaises(DeepLinkResolveError) as ctx:
                await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            elapsed = time.time() - t0
            self.assertGreaterEqual(elapsed, 0.45)
            self.assertIn('未在超时内返回媒体', str(ctx.exception))

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
            resolver = DeepLinkResolver(
                timeout_seconds=0.25, poll_interval=0.05, settle_seconds=0, min_interval_seconds=0,
            )
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
            self.assertEqual(1, len(result))
            self.assertTrue(getattr(result[0], 'video', None))

        asyncio.run(run_case())

    def test_resolve_collects_multiple_media_from_same_poll(self):
        async def run_case():
            started = time.time()
            first = SimpleNamespace(
                id=1,
                video=object(),
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
            )
            second = SimpleNamespace(
                id=2,
                video=None,
                document=object(),
                animation=None,
                photo=None,
                outgoing=False,
                date=started + 0.1,
                chat=SimpleNamespace(id='bot'),
            )
            client = _make_history_client([[second, first]])
            resolver = DeepLinkResolver(
                timeout_seconds=0.5,
                poll_interval=0.05,
                settle_seconds=0,
                min_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock()):
                result = await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            self.assertEqual([first, second], result)

        asyncio.run(run_case())

    def test_resolve_accepts_photo_media(self):
        async def run_case():
            started = time.time()
            photo_msg = SimpleNamespace(
                id=9,
                video=None,
                document=None,
                animation=None,
                photo=object(),
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
            )
            client = _make_history_client([[photo_msg]])
            resolver = DeepLinkResolver(
                timeout_seconds=0.5, poll_interval=0.05, settle_seconds=0, min_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock()):
                result = await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            self.assertEqual([photo_msg], result)

        asyncio.run(run_case())

    def test_resolve_clicks_next_page_and_collects_more_media(self):
        async def run_case():
            started = time.time()
            page1 = SimpleNamespace(
                id=1,
                video=object(),
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=None,
            )
            pager = SimpleNamespace(
                id=2,
                video=None,
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=SimpleNamespace(inline_keyboard=[[
                    SimpleNamespace(text='下一页 ▶️', callback_data=b'next1', url=None),
                ]]),
                click=AsyncMock(),
            )
            page2 = SimpleNamespace(
                id=3,
                video=None,
                document=object(),
                animation=None,
                photo=None,
                outgoing=False,
                date=started + 0.2,
                chat=SimpleNamespace(id='bot'),
                reply_markup=None,
            )
            # poll0: page1+pager; after click poll1+: page1+pager(no next)+page2
            pager_done = SimpleNamespace(
                id=2,
                video=None,
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=SimpleNamespace(inline_keyboard=[[
                    SimpleNamespace(text='📋 2/2', callback_data=b'status', url=None),
                ]]),
            )
            client = _make_history_client([
                [pager, page1],
                [page2, pager_done, page1],
            ])
            resolver = DeepLinkResolver(
                timeout_seconds=2.0,
                poll_interval=0.02,
                settle_seconds=0,
                min_interval_seconds=0,
                max_pages=5,
                page_click_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock()):
                result = await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            self.assertEqual([page1, page2], result)
            pager.click.assert_awaited()

        asyncio.run(run_case())

    def test_resolve_zero_media_then_pagination_succeeds(self):
        async def run_case():
            started = time.time()
            pager = SimpleNamespace(
                id=1,
                video=None,
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=SimpleNamespace(inline_keyboard=[[
                    SimpleNamespace(text='❄️1', callback_data=b'g1', url=None),
                ]]),
                click=AsyncMock(),
            )
            media = SimpleNamespace(
                id=2,
                video=object(),
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started + 0.1,
                chat=SimpleNamespace(id='bot'),
                reply_markup=None,
            )
            pager_done = SimpleNamespace(
                id=1,
                video=None,
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=SimpleNamespace(inline_keyboard=[[
                    SimpleNamespace(text='✅1', callback_data=b'g1', url=None),
                ]]),
            )
            client = _make_history_client([[pager], [media, pager_done]])
            resolver = DeepLinkResolver(
                timeout_seconds=2.0,
                poll_interval=0.02,
                settle_seconds=0,
                min_interval_seconds=0,
                page_click_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock()):
                result = await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            self.assertEqual([media], result)
            pager.click.assert_awaited()

        asyncio.run(run_case())

    def test_resolve_pagination_click_failure_keeps_partial_media(self):
        async def run_case():
            started = time.time()
            page1 = SimpleNamespace(
                id=1,
                video=object(),
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=None,
            )
            pager = SimpleNamespace(
                id=2,
                video=None,
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=SimpleNamespace(inline_keyboard=[[
                    SimpleNamespace(text='下一页 ▶️', callback_data=b'next1', url=None),
                ]]),
                click=AsyncMock(side_effect=TimeoutError('bot slow')),
            )
            client = _make_history_client([[pager, page1]])
            resolver = DeepLinkResolver(
                timeout_seconds=1.0,
                poll_interval=0.02,
                settle_seconds=0,
                min_interval_seconds=0,
                page_click_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock()):
                result = await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            self.assertEqual([page1], result)

        asyncio.run(run_case())

    def test_resolve_dedupes_same_file_unique_id_across_message_ids(self):
        async def run_case():
            started = time.time()
            media_a = SimpleNamespace(
                id=10,
                video=SimpleNamespace(file_unique_id='uid-same', file_id='fid-a', file_name='a.mp4'),
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=None,
            )
            media_dup = SimpleNamespace(
                id=11,
                video=SimpleNamespace(file_unique_id='uid-same', file_id='fid-b', file_name='a.mp4'),
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started + 0.1,
                chat=SimpleNamespace(id='bot'),
                reply_markup=None,
            )
            client = _make_history_client([[media_a, media_dup]])
            resolver = DeepLinkResolver(
                timeout_seconds=0.5, poll_interval=0.02, settle_seconds=0, min_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock()):
                result = await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            self.assertEqual([media_a], result)

        asyncio.run(run_case())

    def test_resolve_stops_pagination_when_click_yields_no_new_unique_media(self):
        async def run_case():
            started = time.time()
            page1 = SimpleNamespace(
                id=1,
                video=SimpleNamespace(file_unique_id='uid-1', file_id='f1'),
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=None,
            )
            pager = SimpleNamespace(
                id=2,
                video=None,
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=SimpleNamespace(inline_keyboard=[[
                    SimpleNamespace(text='下一页 ▶️', callback_data=b'next1', url=None),
                ]]),
                click=AsyncMock(),
            )
            # After click: same content under new message id + another next button.
            page1_resend = SimpleNamespace(
                id=3,
                video=SimpleNamespace(file_unique_id='uid-1', file_id='f1b'),
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started + 0.2,
                chat=SimpleNamespace(id='bot'),
                reply_markup=None,
            )
            pager2 = SimpleNamespace(
                id=4,
                video=None,
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started + 0.2,
                chat=SimpleNamespace(id='bot'),
                reply_markup=SimpleNamespace(inline_keyboard=[[
                    SimpleNamespace(text='下一页 ▶️', callback_data=b'next2', url=None),
                ]]),
                click=AsyncMock(),
            )
            client = _make_history_client([
                [pager, page1],
                [page1_resend, pager2, pager, page1],
            ])
            resolver = DeepLinkResolver(
                timeout_seconds=2.0,
                poll_interval=0.02,
                settle_seconds=0,
                min_interval_seconds=0,
                max_pages=5,
                page_click_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock()):
                result = await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            self.assertEqual([page1], result)
            pager.click.assert_awaited()
            pager2.click.assert_not_awaited()

        asyncio.run(run_case())

    def test_resolve_should_continue_false_returns_partial_media(self):
        async def run_case():
            started = time.time()
            page1 = SimpleNamespace(
                id=1,
                video=SimpleNamespace(file_unique_id='uid-1', file_id='f1'),
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=None,
            )
            pager = SimpleNamespace(
                id=2,
                video=None,
                document=None,
                animation=None,
                photo=None,
                outgoing=False,
                date=started,
                chat=SimpleNamespace(id='bot'),
                reply_markup=SimpleNamespace(inline_keyboard=[[
                    SimpleNamespace(text='下一页 ▶️', callback_data=b'next1', url=None),
                ]]),
                click=AsyncMock(),
            )
            client = _make_history_client([[pager, page1]])
            resolver = DeepLinkResolver(
                timeout_seconds=2.0,
                poll_interval=0.02,
                settle_seconds=0,
                min_interval_seconds=0,
                max_pages=5,
                page_click_interval_seconds=0,
            )
            calls = {'n': 0}

            def should_continue():
                calls['n'] += 1
                # Allow first wave polls + outer checks; stop before pagination click.
                return calls['n'] < 3

            with patch.object(resolver, 'start_bot', new=AsyncMock()):
                result = await resolver.resolve(
                    client,
                    _source_message_with_deep_link(),
                    whitelist=['a82bot'],
                    should_continue=should_continue,
                )
            self.assertEqual([page1], result)
            pager.click.assert_not_awaited()

        asyncio.run(run_case())

    def test_text_has_session_failure_markers(self):
        self.assertTrue(text_has_session_failure('会话已超时关闭。'))
        self.assertTrue(text_has_session_failure('提示：会话超时，请重新打开'))
        self.assertTrue(text_has_session_failure('会话已关闭'))
        self.assertFalse(text_has_session_failure('#MYMPET'))
        self.assertFalse(text_has_session_failure(''))
        self.assertFalse(text_has_session_failure(None))

    def test_resolve_session_failure_retries_then_succeeds(self):
        async def run_case():
            starts = {'n': 0}
            started = time.time()

            async def start_bot(client, bot_username, start_param, deadline=None):
                starts['n'] += 1

            async def get_chat_history(bot_username, limit=10):
                if starts['n'] <= 1:
                    yield SimpleNamespace(
                        id=10,
                        video=None,
                        document=None,
                        animation=None,
                        photo=object(),
                        outgoing=False,
                        date=started,
                        text=None,
                        caption='#preview',
                        chat=SimpleNamespace(id='bot'),
                    )
                    yield SimpleNamespace(
                        id=11,
                        video=None,
                        document=None,
                        animation=None,
                        photo=None,
                        outgoing=False,
                        date=started,
                        text='会话已超时关闭。',
                        caption=None,
                        chat=SimpleNamespace(id='bot'),
                    )
                    return
                yield SimpleNamespace(
                    id=20,
                    video=object(),
                    document=None,
                    animation=None,
                    photo=None,
                    outgoing=False,
                    date=time.time(),
                    text=None,
                    caption=None,
                    chat=SimpleNamespace(id='bot'),
                )

            client = SimpleNamespace(
                resolve_peer=AsyncMock(return_value=object()),
                invoke=AsyncMock(),
                get_chat_history=get_chat_history,
                rnd_id=lambda: 1,
            )
            resolver = DeepLinkResolver(
                timeout_seconds=0.8,
                poll_interval=0.05,
                settle_seconds=0.15,
                min_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock(side_effect=start_bot)):
                result = await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            self.assertEqual(2, starts['n'])
            self.assertEqual(1, len(result))
            self.assertTrue(getattr(result[0], 'video', None))
            self.assertFalse(getattr(result[0], 'photo', None))

        asyncio.run(run_case())

    def test_resolve_session_failure_exhausts_retries(self):
        async def run_case():
            starts = {'n': 0}
            started = time.time()

            async def start_bot(client, bot_username, start_param, deadline=None):
                starts['n'] += 1

            async def get_chat_history(bot_username, limit=10):
                yield SimpleNamespace(
                    id=starts['n'] * 10,
                    video=None,
                    document=None,
                    animation=None,
                    photo=object(),
                    outgoing=False,
                    date=started,
                    text=None,
                    caption=None,
                    chat=SimpleNamespace(id='bot'),
                )
                yield SimpleNamespace(
                    id=starts['n'] * 10 + 1,
                    video=None,
                    document=None,
                    animation=None,
                    photo=None,
                    outgoing=False,
                    date=started,
                    text='会话已超时关闭。',
                    caption=None,
                    chat=SimpleNamespace(id='bot'),
                )

            client = SimpleNamespace(
                resolve_peer=AsyncMock(return_value=object()),
                invoke=AsyncMock(),
                get_chat_history=get_chat_history,
                rnd_id=lambda: 1,
            )
            resolver = DeepLinkResolver(
                timeout_seconds=0.4,
                poll_interval=0.05,
                settle_seconds=0.1,
                min_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock(side_effect=start_bot)):
                with self.assertRaises(DeepLinkResolveError) as ctx:
                    await resolver.resolve(
                        client, _source_message_with_deep_link(), whitelist=['a82bot'],
                    )
            self.assertEqual(3, starts['n'])
            self.assertIn('会话超时', str(ctx.exception))
            self.assertIn('已尝试 3 次仍失败', str(ctx.exception))

        asyncio.run(run_case())

    def test_resolve_session_failure_interrupted_reports_attempts_used(self):
        async def run_case():
            starts = {'n': 0}
            started = time.time()

            async def start_bot(client, bot_username, start_param, deadline=None):
                starts['n'] += 1

            async def get_chat_history(bot_username, limit=10):
                yield SimpleNamespace(
                    id=starts['n'] * 10,
                    video=None,
                    document=None,
                    animation=None,
                    photo=object(),
                    outgoing=False,
                    date=started,
                    text=None,
                    caption=None,
                    chat=SimpleNamespace(id='bot'),
                )
                yield SimpleNamespace(
                    id=starts['n'] * 10 + 1,
                    video=None,
                    document=None,
                    animation=None,
                    photo=None,
                    outgoing=False,
                    date=started,
                    text='会话已超时关闭。',
                    caption=None,
                    chat=SimpleNamespace(id='bot'),
                )

            client = SimpleNamespace(
                resolve_peer=AsyncMock(return_value=object()),
                invoke=AsyncMock(),
                get_chat_history=get_chat_history,
                rnd_id=lambda: 1,
            )
            resolver = DeepLinkResolver(
                timeout_seconds=0.4,
                poll_interval=0.05,
                settle_seconds=0.1,
                min_interval_seconds=0,
            )
            continue_calls = {'n': 0}

            def should_continue():
                continue_calls['n'] += 1
                # 首波：outer + _collect_wave 各 1 次；第 3 次为 resolve 重试门闩。
                return continue_calls['n'] < 3

            with patch.object(resolver, 'start_bot', new=AsyncMock(side_effect=start_bot)):
                with self.assertRaises(DeepLinkResolveError) as ctx:
                    await resolver.resolve(
                        client,
                        _source_message_with_deep_link(),
                        whitelist=['a82bot'],
                        should_continue=should_continue,
                    )
            self.assertEqual(1, starts['n'])
            self.assertIn('已尝试 1 次后中断', str(ctx.exception))

        asyncio.run(run_case())

    def test_resolve_photo_without_session_failure_still_succeeds(self):
        async def run_case():
            started = time.time()
            photo_msg = SimpleNamespace(
                id=1,
                video=None,
                document=None,
                animation=None,
                photo=object(),
                outgoing=False,
                date=started,
                text=None,
                caption='#ok',
                chat=SimpleNamespace(id='bot'),
            )
            client = _make_history_client([[photo_msg]])
            resolver = DeepLinkResolver(
                timeout_seconds=0.3,
                poll_interval=0.05,
                settle_seconds=0,
                min_interval_seconds=0,
            )
            with patch.object(resolver, 'start_bot', new=AsyncMock()) as start_bot:
                result = await resolver.resolve(
                    client, _source_message_with_deep_link(), whitelist=['a82bot'],
                )
            start_bot.assert_awaited_once()
            self.assertEqual([photo_msg], result)

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
