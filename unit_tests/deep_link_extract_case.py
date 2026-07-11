# coding=UTF-8
import unittest
from types import SimpleNamespace

from module.transfer.deep_link import (
    extract_deep_link_candidates,
    normalize_bot_username,
    pick_whitelisted_deep_link,
    parse_deep_link_url,
)


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


if __name__ == '__main__':
    unittest.main()
