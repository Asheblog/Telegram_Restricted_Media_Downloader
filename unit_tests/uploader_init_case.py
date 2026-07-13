# coding=UTF-8
import asyncio
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.uploader import TelegramUploader


class UploaderInitCase(unittest.TestCase):
    def test_init_defaults_is_premium_false_when_client_me_missing(self):
        loop = asyncio.new_event_loop()
        upload_context = SimpleNamespace(
            app=SimpleNamespace(
                client=SimpleNamespace(me=None),
                max_upload_task=1,
                max_upload_retries=1,
            ),
            loop=loop,
            pb=object(),
            my_id=12345,
            done_notice=lambda *args, **kwargs: None,
            is_running=False,
            is_bot_running=False,
            web_ui=None,
        )
        try:
            with patch('module.infra.uploader.asyncio.create_task', return_value=None):
                uploader = TelegramUploader(upload_context=upload_context)
            self.assertIs(uploader.is_premium, False)
        finally:
            loop.close()


if __name__ == '__main__':
    unittest.main()
