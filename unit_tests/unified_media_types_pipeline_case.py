# coding=UTF-8
import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.core.filter import MessageFilter
from module.core.media_types import MEDIA_TYPES_DEFAULT, resolve_allowed_media_types
from module.persistence.transfer_store import TransferStatus, TransferStore
from module.transfer.runner import WebTransferRunner


def make_message(**kwargs):
    msg = MagicMock()
    msg.id = kwargs.get('id', 1)
    msg.empty = False
    msg.date = kwargs.get('date')
    msg.text = kwargs.get('text', None)
    msg.caption = kwargs.get('caption', None)
    msg.chat = SimpleNamespace(id=kwargs.get('chat_id', -1001))
    msg.link = kwargs.get('link', 'https://t.me/c/1/1')
    for media_type in MessageFilter.MEDIA_TYPES:
        setattr(msg, media_type, kwargs.get(media_type, None))
    return msg


class TransferStoreMediaTypesCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.store = TransferStore(self.tmp.name)

    def tearDown(self):
        conn = getattr(getattr(self.store, '_tls', None), 'conn', None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            self.store._tls.conn = None
        self.tmp.cleanup()

    def test_create_task_inherits_null_media_types(self):
        task_id = self.store.create_task('https://t.me/demo', media_types=None)
        task = self.store.get_task(task_id)
        self.assertIsNone(task.get('media_types'))

    def test_create_task_stores_override(self):
        override = {**MEDIA_TYPES_DEFAULT, 'photo': False, 'video': True}
        task_id = self.store.create_task('https://t.me/demo', media_types=override)
        task = self.store.get_task(task_id)
        self.assertFalse(task['media_types']['photo'])
        self.assertTrue(task['media_types']['video'])

    def test_watch_media_types_roundtrip(self):
        override = {**MEDIA_TYPES_DEFAULT, 'document': False}
        watch = self.store.upsert_live_transfer_watch(
            watch_id='forward:demo',
            watch_type='forward',
            source_link='https://t.me/src',
            target_link='https://t.me/dst',
            media_types=override,
        )
        self.assertFalse(watch['media_types']['document'])
        loaded = self.store.get_live_transfer_watch('forward:demo')
        self.assertFalse(loaded['media_types']['document'])


class WebTransferMediaFilterCase(unittest.TestCase):
    def test_skips_disallowed_photo_for_task_override(self):
        skipped = []

        class Host:
            app = SimpleNamespace(client=object())
            gc = SimpleNamespace(
                message_filter={
                    'enabled': True,
                    'media_types': dict(MEDIA_TYPES_DEFAULT),
                },
                download_upload=True,
            )
            transfer_store = SimpleNamespace(
                add_item=lambda **kw: 1,
                add_event=lambda *a, **k: None,
                is_source_message_terminal=lambda *a, **k: False,
            )

            def runtime_message_filter(self, override=None):
                allowed = resolve_allowed_media_types(
                    self.gc.message_filter.get('media_types'),
                    override,
                )
                return MessageFilter({
                    'enabled': True,
                    'media_types': allowed,
                })

            def skip_transfer_item_for_media_type(self, **kwargs):
                skipped.append(kwargs)
                return 1

            def get_task_target_size_limit_error(self, task, message):
                return None

            async def forward(self, **kwargs):
                raise AssertionError('forward should not be called for filtered media')

            def skip_empty_transfer_source_message(self, **kwargs):
                return None

            def get_deep_link_resolver(self):
                raise AssertionError('should not resolve')

        host = Host()
        runner = WebTransferRunner(host)
        task = {
            'id': 7,
            'target_link': 'https://t.me/pikpak_bot',
            'target_profile': 'pikpak',
            'resolve_deep_link': False,
            'media_types': {**MEDIA_TYPES_DEFAULT, 'photo': False},
        }
        photo = make_message(photo=object(), id=42)

        used_fallback = asyncio.run(
            runner.transfer_message_to_web_target(
                task=task,
                message=photo,
                origin_chat_id=-1001,
                target_chat_id=123,
                source_link='https://t.me/c/1/42',
                range_message_id=42,
            )
        )
        self.assertFalse(used_fallback)
        self.assertEqual(len(skipped), 1)
        self.assertIn('媒体类型', skipped[0]['reject_reason'])


if __name__ == '__main__':
    unittest.main()
