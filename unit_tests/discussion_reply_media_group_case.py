import asyncio
import sys
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.util import iter_discussion_reply_messages, iter_discussion_reply_forward_units
sys.argv = _ORIGINAL_ARGV


class DiscussionReplyMediaGroupCase(unittest.TestCase):
    def test_iter_discussion_reply_messages_expands_media_group(self):
        members = [
            SimpleNamespace(id=101, media_group_id=9001, video=object()),
            SimpleNamespace(id=102, media_group_id=9001, video=object()),
            SimpleNamespace(id=103, media_group_id=9001, video=object()),
        ]
        head = members[0]

        async def get_media_group():
            return members

        head.get_media_group = get_media_group

        single = SimpleNamespace(id=201, media_group_id=None, video=object())

        class FakeClient:
            async def get_discussion_message(self, chat_id, message_id):
                return SimpleNamespace(id=1, chat=SimpleNamespace(id='discussion-chat'))

            async def get_discussion_replies(self, chat_id, message_id):
                yield head
                yield single

        async def run():
            collected = []
            async for message in iter_discussion_reply_messages(
                    FakeClient(),
                    'channel',
                    1,
                    include_message=lambda msg: bool(getattr(msg, 'video', None))
            ):
                collected.append(message.id)
            return collected

        result = asyncio.run(run())
        self.assertEqual([101, 102, 103, 201], result)

    def test_iter_discussion_reply_forward_units_yields_group_once(self):
        members = [
            SimpleNamespace(id=301, media_group_id=9002, video=object()),
            SimpleNamespace(id=302, media_group_id=9002, video=object()),
        ]
        head = members[0]

        async def get_media_group():
            return members

        head.get_media_group = get_media_group

        class FakeClient:
            async def get_discussion_message(self, chat_id, message_id):
                return SimpleNamespace(id=1, chat=SimpleNamespace(id='discussion-chat'))

            async def get_discussion_replies(self, chat_id, message_id):
                yield head
                yield members[1]

        async def run():
            units = []
            async for anchor, group in iter_discussion_reply_forward_units(
                    FakeClient(),
                    'channel',
                    1,
                    include_message=lambda msg: bool(getattr(msg, 'video', None))
            ):
                units.append((
                    anchor.id,
                    None if group is None else [item.id for item in group]
                ))
            return units

        result = asyncio.run(run())
        self.assertEqual([(301, [301, 302])], result)

    def test_iter_discussion_reply_messages_groups_raw_replies_without_get_media_group(self):
        members = [
            SimpleNamespace(id=401, media_group_id=9101, video=object()),
            SimpleNamespace(id=402, media_group_id=9101, video=object()),
            SimpleNamespace(id=403, media_group_id=9101, video=object()),
        ]

        class FakeClient:
            async def get_discussion_message(self, chat_id, message_id):
                return SimpleNamespace(id=99, chat=SimpleNamespace(id='discussion-chat'))

            async def get_discussion_replies(self, chat_id, message_id):
                for member in members:
                    yield member

        async def run():
            collected = []
            async for message in iter_discussion_reply_messages(
                    FakeClient(),
                    'channel',
                    2888,
                    include_message=lambda msg: bool(getattr(msg, 'video', None))
            ):
                collected.append(message.id)
            return collected

        result = asyncio.run(run())
        self.assertEqual([401, 402, 403], result)


if __name__ == '__main__':
    unittest.main()
