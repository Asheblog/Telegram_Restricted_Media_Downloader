# coding=UTF-8
import sys
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub
install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.transfer.deep_link import (
    classify_pagination_button,
    is_last_page_status_text,
    pick_pagination_click_target,
)
sys.argv = _ORIGINAL_ARGV


def _btn(text, data=b'data'):
    return SimpleNamespace(text=text, callback_data=data, url=None)


def _msg_with_keyboard(rows):
    return SimpleNamespace(
        id=42,
        chat=SimpleNamespace(id=100),
        reply_markup=SimpleNamespace(inline_keyboard=rows),
        video=None,
        document=None,
        animation=None,
        photo=None,
        outgoing=False,
    )


class DeepLinkPaginationCase(unittest.TestCase):
    def test_classify_next_prev_status_group(self):
        self.assertEqual('next', classify_pagination_button('下一页 ▶️'))
        self.assertEqual('next', classify_pagination_button('Next'))
        self.assertEqual('prev', classify_pagination_button('◀️ 上一页'))
        self.assertEqual('prev', classify_pagination_button('Previous'))
        self.assertEqual('status', classify_pagination_button('📋 1-2/2'))
        self.assertEqual('group', classify_pagination_button('❄️1'))
        self.assertEqual('group', classify_pagination_button('✅2'))
        self.assertEqual('group', classify_pagination_button('3'))
        self.assertEqual('other', classify_pagination_button('打开频道'))

    def test_is_last_page_status(self):
        self.assertTrue(is_last_page_status_text('📋 2/2'))
        self.assertTrue(is_last_page_status_text('📋 1-2/2'))
        self.assertFalse(is_last_page_status_text('📋 1/2'))
        self.assertFalse(is_last_page_status_text('📋 1-1/3'))

    def test_pick_prefers_unclicked_group_over_next(self):
        msg = _msg_with_keyboard([
            [_btn('◀️ 上一页', b'prev'), _btn('📋 1-2/2', b'status'), _btn('下一页 ▶️', b'next')],
            [_btn('❄️1', b'g1'), _btn('✅2', b'g2')],
        ])
        target = pick_pagination_click_target([msg], clicked_callback_data=set())
        self.assertIsNotNone(target)
        self.assertEqual('group', target.kind)
        self.assertEqual(b'g1', target.callback_data)

        target2 = pick_pagination_click_target([msg], clicked_callback_data={b'g1'})
        self.assertEqual(b'g2', target2.callback_data)

    def test_pick_next_when_groups_exhausted_and_not_last_page(self):
        msg = _msg_with_keyboard([
            [_btn('◀️ 上一页', b'prev'), _btn('📋 1/2', b'status'), _btn('下一页 ▶️', b'next')],
            [_btn('❄️1', b'g1'), _btn('✅2', b'g2')],
        ])
        target = pick_pagination_click_target(
            [msg], clicked_callback_data={b'g1', b'g2'},
        )
        self.assertEqual('next', target.kind)
        self.assertEqual(b'next', target.callback_data)

    def test_pick_none_on_last_page_when_groups_done(self):
        msg = _msg_with_keyboard([
            [_btn('◀️ 上一页', b'prev'), _btn('📋 1-2/2', b'status'), _btn('下一页 ▶️', b'next')],
            [_btn('❄️1', b'g1'), _btn('✅2', b'g2')],
        ])
        target = pick_pagination_click_target(
            [msg], clicked_callback_data={b'g1', b'g2'},
        )
        self.assertIsNone(target)

    def test_pick_skips_already_clicked_callback_data(self):
        msg = _msg_with_keyboard([[_btn('下一页 ▶️', b'next1')]])
        target = pick_pagination_click_target([msg], clicked_callback_data={b'next1'})
        self.assertIsNone(target)

    def test_pick_ignores_url_only_buttons(self):
        msg = _msg_with_keyboard([[
            SimpleNamespace(text='打开', callback_data=None, url='https://t.me/x'),
        ]])
        self.assertIsNone(pick_pagination_click_target([msg], set()))


if __name__ == '__main__':
    unittest.main()
