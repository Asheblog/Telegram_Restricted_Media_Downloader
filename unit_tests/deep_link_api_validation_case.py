# coding=UTF-8
import sys
import tempfile
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]

from module.adapters.webui.server import WebUiApiError, WebUiServer
from module.persistence.transfer_store import TransferStore

sys.argv = _ORIGINAL_ARGV


class DeepLinkApiValidationCase(unittest.TestCase):
    def test_create_task_requires_whitelist_when_resolve_enabled(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            server = WebUiServer(
                store=store,
                deep_link_whitelist_getter=lambda: [],
            )
            with self.assertRaises(WebUiApiError) as ctx:
                server.create_task({
                    'source_link': 'https://t.me/source/1',
                    'target_link': 'https://t.me/pikpak_bot',
                    'resolve_deep_link': True,
                })
            self.assertEqual('deep_link_whitelist_required', ctx.exception.error_code)
            self.assertIn('系统设置', ctx.exception.message)
            self.assertIn('白名单', ctx.exception.message)

    def test_create_task_allows_resolve_false_with_empty_whitelist(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            server = WebUiServer(
                store=store,
                deep_link_whitelist_getter=lambda: [],
            )
            result = server.create_task({
                'source_link': 'https://t.me/source/1',
                'target_link': 'https://t.me/pikpak_bot',
                'resolve_deep_link': False,
            })
            self.assertIn('task_id', result)
            task = store.get_task(result['task_id'])
            self.assertFalse(task['resolve_deep_link'])


if __name__ == '__main__':
    unittest.main()
