# coding=UTF-8
import sys
import time
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.adapters.bot.guide_wizard import (
    BotGuideWizard,
    GuideWizardSession,
    WizardCommand,
    WizardStep,
    WIZARD_TIMEOUT_SECONDS,
    build_forward_command,
    build_listen_download_command,
    build_listen_forward_command,
    build_range_download_command,
    channels_match,
    extract_post_id,
    initial_step,
    normalize_telegram_link,
    to_channel_root,
)
from module.core.enums import BotCallbackText


class BotGuideWizardCase(unittest.TestCase):
    def test_normalize_telegram_link_accepts_common_formats(self):
        self.assertEqual(
            normalize_telegram_link('t.me/demo/42'),
            'https://t.me/demo/42',
        )
        self.assertEqual(
            normalize_telegram_link('https://t.me/demo/42?single'),
            'https://t.me/demo/42',
        )
        self.assertEqual(
            normalize_telegram_link('https://t.me/c/1234567890/99'),
            'https://t.me/c/1234567890/99',
        )
        self.assertIsNone(normalize_telegram_link('https://example.com/demo'))

    def test_to_channel_root_from_public_channel_and_message(self):
        self.assertEqual(to_channel_root('https://t.me/demo'), 'https://t.me/demo')
        self.assertEqual(to_channel_root('https://t.me/demo/42'), 'https://t.me/demo')

    def test_to_channel_root_from_private_channel(self):
        self.assertEqual(
            to_channel_root('https://t.me/c/1234567890/42'),
            'https://t.me/c/1234567890',
        )

    def test_extract_post_id_and_channel_match(self):
        self.assertEqual(extract_post_id('https://t.me/demo/10'), 10)
        self.assertEqual(extract_post_id('https://t.me/c/1234567890/88'), 88)
        self.assertTrue(channels_match('https://t.me/demo', 'https://t.me/demo/99'))
        self.assertFalse(channels_match('https://t.me/demo', 'https://t.me/other/99'))

    def test_build_commands(self):
        self.assertEqual(
            build_range_download_command('https://t.me/demo', 1, 100),
            '/download https://t.me/demo 1 100',
        )
        self.assertEqual(
            build_forward_command('https://t.me/a', 'https://t.me/b', 2, 20, include_comment=True),
            '/forward https://t.me/a https://t.me/b 2 20 --include-comment',
        )
        self.assertEqual(
            build_listen_download_command(['https://t.me/a', 'https://t.me/b']),
            '/listen_download https://t.me/a https://t.me/b',
        )
        self.assertEqual(
            build_listen_forward_command('https://t.me/a', 'https://t.me/b'),
            '/listen_forward https://t.me/a https://t.me/b',
        )

    def test_initial_step_for_listen_download(self):
        self.assertEqual(initial_step(WizardCommand.LISTEN_DOWNLOAD), WizardStep.LISTEN_CHANNEL)
        self.assertEqual(initial_step(WizardCommand.DOWNLOAD), WizardStep.SOURCE_CHANNEL)

    def test_can_start_blocks_active_download_chat_setup(self):
        class _Bot:
            pass

        wizard = BotGuideWizard(_Bot())
        previous = BotCallbackText.DOWNLOAD_CHAT_ID
        try:
            BotCallbackText.DOWNLOAD_CHAT_ID = '12345'
            ok, reason = wizard.can_start(1)
            self.assertFalse(ok)
            self.assertIn('频道下载', reason)
        finally:
            BotCallbackText.DOWNLOAD_CHAT_ID = previous

    def test_session_expires_after_timeout(self):
        class _Bot:
            pass

        wizard = BotGuideWizard(_Bot())
        wizard._sessions[9] = GuideWizardSession(
            user_id=9,
            command=WizardCommand.DOWNLOAD,
            step=WizardStep.SOURCE_CHANNEL,
            updated_at=time.time() - WIZARD_TIMEOUT_SECONDS - 1,
        )
        self.assertFalse(wizard.has_active_session(9))


if __name__ == '__main__':
    unittest.main()
