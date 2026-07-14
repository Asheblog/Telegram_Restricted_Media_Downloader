# coding=UTF-8
import datetime
import unittest
from unittest.mock import MagicMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.core.filter import MessageFilter
from module.core.media_types import (
    MEDIA_TYPES_DEFAULT,
    media_types_to_download_type_list,
    message_matches_media_types,
    normalize_media_types,
    resolve_allowed_media_types,
    serialize_media_types,
)


def make_message(**kwargs):
    msg = MagicMock()
    msg.date = kwargs.get('date', datetime.datetime(2024, 6, 15, 12, 0, 0))
    msg.text = kwargs.get('text', None)
    msg.caption = kwargs.get('caption', None)
    for media_type in MessageFilter.MEDIA_TYPES:
        setattr(msg, media_type, kwargs.get(media_type, None))
    return msg


class MediaTypesHelperTestCase(unittest.TestCase):
    def test_normalize_none_means_inherit(self):
        self.assertIsNone(normalize_media_types(None))
        self.assertIsNone(normalize_media_types(''))
        self.assertIsNone(normalize_media_types('null'))

    def test_normalize_dict_is_complete_allowlist(self):
        raw = {'video': True, 'photo': False}
        got = normalize_media_types(raw)
        self.assertTrue(got['video'])
        self.assertFalse(got['photo'])
        self.assertFalse(got['document'])
        self.assertIn('text', got)

    def test_resolve_override_replaces_global(self):
        global_types = {**MEDIA_TYPES_DEFAULT, 'photo': True, 'video': True}
        override = {'video': True, 'photo': False}
        got = resolve_allowed_media_types(global_types, override)
        self.assertTrue(got['video'])
        self.assertFalse(got['photo'])
        self.assertFalse(got['document'])

    def test_resolve_inherits_global_when_override_unset(self):
        global_types = {**MEDIA_TYPES_DEFAULT, 'photo': False}
        got = resolve_allowed_media_types(global_types, None)
        self.assertFalse(got['photo'])
        self.assertTrue(got['video'])

    def test_serialize_roundtrip(self):
        payload = {'video': True, 'photo': False}
        text = serialize_media_types(payload)
        self.assertIsInstance(text, str)
        self.assertEqual(normalize_media_types(text)['video'], True)
        self.assertIsNone(serialize_media_types(None))

    def test_download_type_list_excludes_text(self):
        allow = {**MEDIA_TYPES_DEFAULT, 'text': True, 'voice': False}
        got = media_types_to_download_type_list(allow)
        self.assertIn('video', got)
        self.assertNotIn('text', got)
        self.assertNotIn('voice', got)

    def test_message_matches_uses_allowlist(self):
        allow = {**MEDIA_TYPES_DEFAULT, 'photo': False, 'video': True}
        self.assertTrue(message_matches_media_types(make_message(video=object()), allow))
        self.assertFalse(message_matches_media_types(make_message(photo=object()), allow))


class MessageFilterMediaAlwaysOnTestCase(unittest.TestCase):
    def test_disabled_filter_still_blocks_disallowed_media(self):
        f = MessageFilter({
            'enabled': False,
            'media_types': {
                'video': True, 'photo': False, 'audio': False, 'document': False,
                'voice': False, 'text': False, 'animation': False, 'video_note': False,
            },
        })
        self.assertTrue(f.should_pass(make_message(video=object())))
        self.assertFalse(f.should_pass(make_message(photo=object())))

    def test_disabled_filter_skips_date_and_keywords(self):
        start_ts = datetime.datetime(2024, 6, 1).timestamp()
        f = MessageFilter({
            'enabled': False,
            'media_types': dict(MEDIA_TYPES_DEFAULT),
            'date_range': {'enabled': True, 'start_date': start_ts, 'end_date': None},
            'keywords': {'enabled': True, 'words': ['blocked']},
        })
        msg = make_message(
            video=object(),
            date=datetime.datetime(2024, 1, 1),
            text='blocked movie',
        )
        self.assertTrue(f.should_pass(msg))


if __name__ == '__main__':
    unittest.main()
