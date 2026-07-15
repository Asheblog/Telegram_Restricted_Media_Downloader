# coding=UTF-8
import asyncio
import sys
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.bot import Bot
from module.enums import BotButton, BotCommandText


def _button_rows(markup):
    if hasattr(markup, 'args') and markup.args:
        return markup.args[0]
    return getattr(markup, 'inline_keyboard', [])


def _button_text(button):
    if hasattr(button, 'args') and button.args:
        return button.args[0]
    return getattr(button, 'text', '')


def _button_url(button):
    if hasattr(button, 'kwargs'):
        return button.kwargs.get('url')
    return getattr(button, 'url', None)


class BotHelpCase(unittest.TestCase):
    def test_help_describes_webui_fork_and_quick_start(self):
        meta = asyncio.run(Bot.help())
        text = meta['text']

        self.assertIn('WebUI Fork', text)
        self.assertIn('上游作者: Gentlesprite', text)
        self.assertIn('魔改作者: Asheblog', text)
        self.assertIn('WebUI 入口', text)
        self.assertIn('Docker 默认访问', text)
        self.assertIn('本 Fork 亮点', text)
        self.assertIn('深链取片', text)
        self.assertIn('WebUI 能力', text)
        self.assertIn('/cleanup', text)
        self.assertIn('快速部署', text)
        self.assertNotIn('订阅频道', text)
        self.assertNotIn('视频教程', text)

    def test_help_buttons_point_to_fork_readme(self):
        meta = asyncio.run(Bot.help())
        buttons = [button for row in _button_rows(meta['keyboard']) for button in row]
        button_texts = [_button_text(button) for button in buttons]
        button_urls = [_button_url(button) for button in buttons if _button_url(button)]

        self.assertIn(BotButton.GITHUB, button_texts)
        self.assertIn(BotButton.QUICK_START, button_texts)
        self.assertIn(
            'https://github.com/Asheblog/Telegram_Restricted_Media_Downloader',
            button_urls
        )
        self.assertIn(
            'https://github.com/Asheblog/Telegram_Restricted_Media_Downloader#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B',
            button_urls
        )
        self.assertFalse(any('RestrictedMediaDownloader' in url for url in button_urls))
        self.assertFalse(any('youtube.com' in url for url in button_urls))

    def test_cleanup_is_registered_as_bot_command(self):
        command_names = [
            command.args[0] if hasattr(command, 'args') and command.args else getattr(command, 'command', '')
            for command in Bot.COMMANDS
        ]

        self.assertIn(BotCommandText.CLEANUP[0], command_names)

