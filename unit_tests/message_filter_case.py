# coding=UTF-8
"""MessageFilter 单元测试"""

import unittest
import datetime
from unittest.mock import MagicMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.filter import MessageFilter


def make_message(**kwargs):
    """创建模拟的 pyrogram Message 对象。"""
    msg = MagicMock()
    msg.date = kwargs.get('date', datetime.datetime(2024, 6, 15, 12, 0, 0))
    msg.text = kwargs.get('text', None)
    msg.caption = kwargs.get('caption', None)
    for media_type in MessageFilter.MEDIA_TYPES:
        setattr(msg, media_type, kwargs.get(media_type, None))
    return msg


class MessageFilterTestCase(unittest.TestCase):

    # ── 总开关 ──

    def test_disabled_filter_passes_everything(self):
        f = MessageFilter({'enabled': False})
        msg = make_message()
        self.assertTrue(f.should_pass(msg))

    def test_default_config_passes_everything(self):
        f = MessageFilter({})
        msg = make_message(video=True)
        self.assertTrue(f.should_pass(msg))

    # ── 媒体类型过滤 ──

    def test_media_type_passes_when_type_enabled(self):
        f = MessageFilter({'media_types': {'video': True, 'photo': False, 'audio': False,
                                           'document': False, 'voice': False, 'text': False,
                                           'animation': False, 'video_note': False}})
        msg = make_message(video=True)
        self.assertTrue(f.should_pass(msg))

    def test_media_type_blocks_when_type_disabled(self):
        f = MessageFilter({'media_types': {'video': False, 'photo': True, 'audio': False,
                                           'document': False, 'voice': False, 'text': False,
                                           'animation': False, 'video_note': False}})
        msg = make_message(video=True)
        self.assertFalse(f.should_pass(msg))

    def test_text_message_passes_when_text_enabled(self):
        f = MessageFilter({'media_types': {'video': False, 'photo': False, 'audio': False,
                                           'document': False, 'voice': False, 'text': True,
                                           'animation': False, 'video_note': False}})
        msg = make_message(text="hello")
        self.assertTrue(f.should_pass(msg))

    def test_message_without_any_media_blocked(self):
        f = MessageFilter({'media_types': {'video': True, 'photo': True, 'audio': False,
                                           'document': False, 'voice': False, 'text': False,
                                           'animation': False, 'video_note': False}})
        msg = make_message()  # no media attributes
        self.assertFalse(f.should_pass(msg))

    # ── 日期范围过滤 ──

    def test_date_range_disabled_passes(self):
        f = MessageFilter({'date_range': {'enabled': False, 'start_date': None, 'end_date': None}})
        msg = make_message(date=datetime.datetime(2024, 1, 1))
        self.assertTrue(f.should_pass(msg))

    def test_date_range_start_only(self):
        start_ts = datetime.datetime(2024, 6, 1).timestamp()
        f = MessageFilter({'date_range': {'enabled': True, 'start_date': start_ts, 'end_date': None}})
        msg_before = make_message(date=datetime.datetime(2024, 5, 1))
        msg_after = make_message(date=datetime.datetime(2024, 7, 1))
        self.assertFalse(f.should_pass(msg_before))
        self.assertTrue(f.should_pass(msg_after))

    def test_date_range_end_only(self):
        end_ts = datetime.datetime(2024, 6, 1).timestamp()
        f = MessageFilter({'date_range': {'enabled': True, 'start_date': None, 'end_date': end_ts}})
        msg_before = make_message(date=datetime.datetime(2024, 5, 1))
        msg_after = make_message(date=datetime.datetime(2024, 7, 1))
        self.assertTrue(f.should_pass(msg_before))
        self.assertFalse(f.should_pass(msg_after))

    def test_date_range_both(self):
        start_ts = datetime.datetime(2024, 1, 1).timestamp()
        end_ts = datetime.datetime(2024, 6, 1).timestamp()
        f = MessageFilter({'date_range': {'enabled': True, 'start_date': start_ts, 'end_date': end_ts}})
        msg_in = make_message(date=datetime.datetime(2024, 3, 15))
        msg_out = make_message(date=datetime.datetime(2024, 7, 1))
        self.assertTrue(f.should_pass(msg_in))
        self.assertFalse(f.should_pass(msg_out))

    # ── 关键词过滤 ──

    def test_keywords_disabled_passes(self):
        f = MessageFilter({'keywords': {'enabled': False, 'words': ['test']}})
        msg = make_message(text="hello world")
        self.assertTrue(f.should_pass(msg))

    def test_keywords_empty_list_passes(self):
        f = MessageFilter({'keywords': {'enabled': True, 'words': []}})
        msg = make_message(text="hello world")
        self.assertTrue(f.should_pass(msg))

    def test_keywords_match_in_text(self):
        f = MessageFilter({'keywords': {'enabled': True, 'words': ['电影', 'music']}})
        msg = make_message(text="好看的电影推荐")
        self.assertTrue(f.should_pass(msg))

    def test_keywords_match_in_caption(self):
        f = MessageFilter({'keywords': {'enabled': True, 'words': ['music']}})
        msg = make_message(caption="best music album")
        self.assertTrue(f.should_pass(msg))

    def test_keywords_case_insensitive(self):
        f = MessageFilter({'keywords': {'enabled': True, 'words': ['MUSIC']}})
        msg = make_message(text="Music is great")
        self.assertTrue(f.should_pass(msg))

    def test_keywords_no_match(self):
        f = MessageFilter({'keywords': {'enabled': True, 'words': ['电影']}})
        msg = make_message(text="today's weather")
        self.assertFalse(f.should_pass(msg))

    # ── AND 组合逻辑 ──

    def test_all_filters_must_pass(self):
        start_ts = datetime.datetime(2024, 1, 1).timestamp()
        f = MessageFilter({
            'media_types': {'video': True, 'photo': False, 'audio': False,
                            'document': False, 'voice': False, 'text': False,
                            'animation': False, 'video_note': False},
            'date_range': {'enabled': True, 'start_date': start_ts, 'end_date': None},
            'keywords': {'enabled': True, 'words': ['电影']}
        })
        # 全部满足：type=video, date ok, keyword match
        msg_pass = make_message(
            video=True,
            date=datetime.datetime(2024, 6, 15),
            caption="好看的电影"
        )
        self.assertTrue(f.should_pass(msg_pass))

        # type不满足
        msg_fail_type = make_message(
            photo=True,
            date=datetime.datetime(2024, 6, 15),
            caption="好看的电影"
        )
        self.assertFalse(f.should_pass(msg_fail_type))

        # 关键词不满足
        msg_fail_kw = make_message(
            video=True,
            date=datetime.datetime(2024, 6, 15),
            text="今天天气不错"
        )
        self.assertFalse(f.should_pass(msg_fail_kw))

    # ── 兼容静态方法 ──

    def test_static_date_range(self):
        msg = make_message(date=datetime.datetime(2024, 6, 15))
        start = datetime.datetime(2024, 1, 1).timestamp()
        end = datetime.datetime(2024, 12, 31).timestamp()
        self.assertTrue(MessageFilter.date_range(msg, start, end))
        self.assertFalse(MessageFilter.date_range(msg, end, None))

    def test_static_dtype(self):
        msg = make_message(video=True)
        self.assertTrue(MessageFilter.dtype(msg, {'video': True, 'photo': False}))
        self.assertFalse(MessageFilter.dtype(msg, {'video': False, 'photo': True}))

    def test_static_keyword_filter(self):
        msg = make_message(text="hello world")
        self.assertTrue(MessageFilter.keyword_filter(msg, ['hello']))
        self.assertFalse(MessageFilter.keyword_filter(msg, ['goodbye']))
        self.assertTrue(MessageFilter.keyword_filter(msg, None))
        self.assertTrue(MessageFilter.keyword_filter(msg, []))


if __name__ == '__main__':
    unittest.main()
