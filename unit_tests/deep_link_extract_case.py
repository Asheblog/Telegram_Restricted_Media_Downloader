# coding=UTF-8
import sys
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub
install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.transfer.deep_link import (
    extract_deep_link_candidates,
    messages_after_deep_link_resolve,
    normalize_bot_username,
    pick_whitelisted_deep_link,
    parse_deep_link_url,
)
sys.argv = _ORIGINAL_ARGV


class DeepLinkExtractCase(unittest.TestCase):
    def test_normalize_strips_at_and_lower(self):
        self.assertEqual('a82bot', normalize_bot_username('@A82Bot'))

    def test_parse_tme_and_tg_urls(self):
        self.assertEqual(
            ('a82bot', 'v_db7c66a8e8'),
            parse_deep_link_url('https://t.me/a82bot?start=v_db7c66a8e8'),
        )
        self.assertEqual(
            ('a82bot', 'v_abc'),
            parse_deep_link_url('tg://resolve?domain=a82bot&start=v_abc'),
        )
        self.assertIsNone(parse_deep_link_url('https://t.me/a82bot'))

    def test_button_before_text(self):
        msg = SimpleNamespace(
            reply_markup=SimpleNamespace(inline_keyboard=[[
                SimpleNamespace(url='https://t.me/otherbot?start=skip'),
                SimpleNamespace(url='https://t.me/a82bot?start=from_btn'),
            ]]),
            text='see https://t.me/a82bot?start=from_text',
            caption=None,
            entities=None,
            caption_entities=None,
        )
        cands = extract_deep_link_candidates(msg)
        # Buttons first (order preserved), then text; whitelist pick skips non-listed bots.
        self.assertEqual([('otherbot', 'skip'), ('a82bot', 'from_btn'), ('a82bot', 'from_text')], cands)
        picked = pick_whitelisted_deep_link(cands, ['a82bot'])
        self.assertEqual(('a82bot', 'from_btn'), picked)

    def test_non_whitelist_returns_none(self):
        cands = [('otherbot', 'x')]
        self.assertIsNone(pick_whitelisted_deep_link(cands, ['a82bot']))

    def test_messages_after_resolve_skips_source_when_no_deep_link(self):
        source = SimpleNamespace(id=2509, photo=object())
        self.assertIsNone(messages_after_deep_link_resolve(
            resolve_enabled=True,
            source_message=source,
            resolved_list=None,
        ))

    def test_messages_after_resolve_uses_bot_media_when_present(self):
        source = SimpleNamespace(id=2509)
        bot_msg = SimpleNamespace(id=99)
        self.assertEqual(
            [bot_msg],
            messages_after_deep_link_resolve(
                resolve_enabled=True,
                source_message=source,
                resolved_list=[bot_msg],
            ),
        )

    def test_messages_after_resolve_keeps_source_when_disabled(self):
        source = SimpleNamespace(id=2509)
        self.assertEqual(
            [source],
            messages_after_deep_link_resolve(
                resolve_enabled=False,
                source_message=source,
                resolved_list=None,
            ),
        )


if __name__ == '__main__':
    unittest.main()
