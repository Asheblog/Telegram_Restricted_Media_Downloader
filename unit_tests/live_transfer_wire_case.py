# coding=UTF-8
"""Seam tests for LiveTransferService extraction from the downloader facade."""
import asyncio
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


def _import_downloader():
    from module.downloader import TelegramRestrictedMediaDownloader
    return TelegramRestrictedMediaDownloader


class LiveTransferWireCase(unittest.TestCase):
    """Facade delegates listen/forward to LiveTransferService; Bot wiring uses host overrides."""

    def test_live_transfer_module_exports_service(self):
        from module.transfer.live_transfer import LiveTransferService

        host = SimpleNamespace()
        service = LiveTransferService(host=host)
        self.assertIs(service._host, host)

    def test_facade_lazy_wires_live_transfer_and_delegates_listen_download(self):
        TelegramRestrictedMediaDownloader = _import_downloader()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        calls = []

        async def fake_create_download_task(**kwargs):
            calls.append(kwargs)
            return {'status': 'ok'}

        downloader.create_download_task = fake_create_download_task
        downloader.watch_manager = SimpleNamespace(_download_chat_watch_id={})
        downloader._message_chain_context = lambda message, watch_id=None: ('trace', '-100', 7)
        downloader._log_system_chain = lambda **kwargs: None
        downloader.runtime_message_filter = lambda override=None: SimpleNamespace(
            should_pass=lambda message: True,
            get_reject_reason=lambda message: None,
        )

        message = SimpleNamespace(
            id=7,
            link='https://t.me/source/7',
            chat=SimpleNamespace(id=-100),
        )

        asyncio.run(downloader.listen_download(object(), message))

        self.assertTrue(hasattr(downloader, 'live_transfer'))
        from module.transfer.live_transfer import LiveTransferService
        self.assertIsInstance(downloader.live_transfer, LiveTransferService)
        self.assertEqual(1, len(calls))
        self.assertEqual('https://t.me/source/7', calls[0]['message_ids'])
        self.assertTrue(calls[0]['single_link'])

    def test_facade_forward_discussion_replies_uses_live_transfer(self):
        TelegramRestrictedMediaDownloader = _import_downloader()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        downloader.app = SimpleNamespace(client=SimpleNamespace(
            get_messages=AsyncMock(return_value=SimpleNamespace(empty=True, link=None)),
        ))
        downloader.gc = SimpleNamespace(get_deep_link_bot_whitelist=lambda: [])
        downloader.check_type = lambda message, media_types_override=None: False
        downloader.runtime_message_filter = lambda override=None: SimpleNamespace(
            should_pass=lambda message: False,
        )
        downloader._watch_media_types_override = lambda watch_id: None
        downloader._log_system_chain = lambda **kwargs: None

        class EmptyReplies:
            async def get_discussion_replies(self, chat_id, message_id):
                if False:
                    yield None

        downloader.app.client = EmptyReplies()
        # get_messages still needed
        downloader.app.client.get_messages = AsyncMock(
            return_value=SimpleNamespace(empty=True, link=None)
        )

        count = asyncio.run(downloader.forward_discussion_replies(
            client=object(),
            source_chat_id='source',
            source_message_id=1,
            target_chat_id='target',
            target_link='https://t.me/target',
            done_notice=False,
        ))
        self.assertEqual(0, count)
        self.assertIsInstance(
            downloader.live_transfer,
            __import__('module.transfer.live_transfer', fromlist=['LiveTransferService']).LiveTransferService,
        )

    def test_composition_root_registers_host_handler_overrides(self):
        import inspect
        from module.composition_root import TrmdCompositionRoot

        src = inspect.getsource(TrmdCompositionRoot.__init__)
        self.assertIn("'handle_forwarded_media': self.handle_forwarded_media", src)
        self.assertIn("'on_listen': self.on_listen", src)
        self.assertIn("'start': self.start", src)
        self.assertIn("'callback_data': self.callback_data", src)
        self.assertIn('LiveTransferService(host=self)', src)

    def test_bot_resolved_handler_prefers_host_overrides(self):
        """Regression: without overrides, /listen_* stayed on Bot.on_listen (meta discarded)."""
        from module.adapters.bot.bot import Bot

        host_on_listen = object()
        host_forwarded = object()
        bot = Bot(handler_overrides={
            'on_listen': host_on_listen,
            'handle_forwarded_media': host_forwarded,
        })
        self.assertIs(bot._resolved_handler('on_listen', bot.on_listen), host_on_listen)
        self.assertIs(
            bot._resolved_handler('handle_forwarded_media', bot.handle_forwarded_media),
            host_forwarded,
        )
        bare = Bot(handler_overrides={})
        default_on_listen = bare.on_listen
        default_forwarded = bare.handle_forwarded_media
        self.assertIs(bare._resolved_handler('on_listen', default_on_listen), default_on_listen)
        self.assertIs(
            bare._resolved_handler('handle_forwarded_media', default_forwarded),
            default_forwarded,
        )

    def test_host_on_listen_registers_watch_after_bot_meta(self):
        """Host on_listen must call Bot.on_listen then register a real chat handler."""
        import pyrogram
        from unittest.mock import patch
        from module.transfer.live_transfer import LiveTransferService

        registered = []
        bot_meta = {
            'command': '/listen_download',
            'links': ['https://t.me/source'],
            'include_comment': False,
        }

        async def bot_on_listen(client, message):
            return bot_meta

        chat = SimpleNamespace(id=-100123, is_forum=False)
        user = SimpleNamespace(
            get_chat=AsyncMock(return_value=chat),
            add_handler=lambda handler: registered.append(handler),
        )
        client = SimpleNamespace(
            send_message=AsyncMock(return_value=SimpleNamespace(id=1, text='✅')),
        )
        message = SimpleNamespace(
            id=9,
            from_user=SimpleNamespace(id=42),
            text='/listen_download https://t.me/source',
        )
        host = SimpleNamespace(
            bot=SimpleNamespace(on_listen=bot_on_listen),
            user=user,
            listen_download_chat={},
            listen_forward_chat={},
            listen_download=AsyncMock(),
            safe_edit_message=AsyncMock(
                return_value=SimpleNamespace(id=1, text='✅\nhttps://t.me/source')
            ),
        )
        service = LiveTransferService(host=host)

        # pyrogram stub's Dummy filters has no dynamic .chat; provide a minimal stand-in.
        pyrogram.filters.chat = lambda *args, **kwargs: SimpleNamespace(args=args, kwargs=kwargs)
        with patch(
            'module.transfer.live_transfer.MessageHandler',
            side_effect=lambda *args, **kwargs: SimpleNamespace(args=args, kwargs=kwargs),
        ):
            asyncio.run(service.on_listen(client, message))

        self.assertIn('https://t.me/source', host.listen_download_chat)
        self.assertEqual(1, len(registered))

    def test_host_on_listen_delegates_to_bot_parser(self):
        """Host path always starts with Bot.on_listen (wizard/validate); None stops registration."""
        from module.transfer.live_transfer import LiveTransferService

        called = []

        async def bot_on_listen(client, message):
            called.append(message.text)
            return None

        host = SimpleNamespace(
            bot=SimpleNamespace(on_listen=bot_on_listen),
            listen_download_chat={},
            listen_forward_chat={},
        )
        service = LiveTransferService(host=host)
        result = asyncio.run(
            service.on_listen(object(), SimpleNamespace(text='/listen_download'))
        )
        self.assertIsNone(result)
        self.assertEqual(['/listen_download'], called)

    def test_bot_dead_listen_stubs_removed(self):
        from module.adapters.bot.bot import Bot

        # Host owns listen_download / listen_forward / cancel_listen; Bot must not keep silent pass stubs.
        for name in ('listen_download', 'listen_forward', 'cancel_listen'):
            self.assertFalse(
                callable(getattr(Bot, name, None)) and name in Bot.__dict__,
                f'Bot still defines dead stub {name}',
            )

    def test_bot_handle_forwarded_media_requires_host_override(self):
        from module.adapters.bot.bot import Bot

        bot = Bot.__new__(Bot)
        bot._handler_overrides = {}
        with self.assertRaises(NotImplementedError):
            asyncio.run(Bot.handle_forwarded_media(bot, object(), object()))


if __name__ == '__main__':
    unittest.main()
