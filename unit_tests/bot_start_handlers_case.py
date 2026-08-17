# coding=UTF-8
"""Bot.start_bot must register every handler without raising.

start_bot swallows all exceptions into a failure string, so a bad filter
silently leaves the bot with no listeners instead of crashing loudly.
"""
import asyncio
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


class BotStartHandlersCase(unittest.TestCase):
    @staticmethod
    def _start(registered: list):
        from module.adapters.bot.bot import Bot

        bot = Bot(gc=SimpleNamespace(config={}, get_config=lambda *args: False))
        bot_client = SimpleNamespace(
            start=AsyncMock(),
            set_bot_commands=AsyncMock(),
            get_me=AsyncMock(return_value=SimpleNamespace(username='trmd_bot', id=1)),
            add_handler=lambda handler, group=0: registered.append(group),
        )
        user_client = SimpleNamespace(
            get_me=AsyncMock(return_value=SimpleNamespace(id=42)),
            add_handler=lambda handler, group=0: registered.append(group),
            send_message=AsyncMock(),
        )
        result = asyncio.run(bot.start_bot(SimpleNamespace(), user_client, bot_client))
        return bot, result

    def test_start_bot_registers_handlers_and_reports_success(self):
        registered: list = []
        bot, result = self._start(registered)

        self.assertNotIn('启动失败', result)
        self.assertTrue(bot.is_bot_running)

    def test_start_bot_registers_guide_wizard_in_group_minus_two(self):
        """The wizard handler is registered last; a bad filter there kills the whole start."""
        registered: list = []
        self._start(registered)

        self.assertIn(-2, registered)


if __name__ == '__main__':
    unittest.main()
