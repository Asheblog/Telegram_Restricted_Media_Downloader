# coding=UTF-8
import sys
import unittest
from copy import deepcopy

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.core.config import GlobalConfig
sys.argv = _ORIGINAL_ARGV


class ItemStaleTimeoutConfigCase(unittest.TestCase):
    def test_default_item_stale_timeout_minutes_is_5(self):
        self.assertEqual(5, GlobalConfig.TEMPLATE['transfer']['item_stale_timeout_minutes'])

    def test_getter_clamps_and_defaults(self):
        gc = GlobalConfig.__new__(GlobalConfig)
        gc.default_transfer_nesting = deepcopy(GlobalConfig.TEMPLATE['transfer'])
        gc.config = {'transfer': {'item_stale_timeout_minutes': 5}}
        self.assertEqual(5, GlobalConfig.get_item_stale_timeout_minutes(gc))
        gc.config = {'transfer': {'item_stale_timeout_minutes': 1}}
        self.assertEqual(1, GlobalConfig.get_item_stale_timeout_minutes(gc))
        gc.config = {'transfer': {'item_stale_timeout_minutes': 0}}
        self.assertEqual(1, GlobalConfig.get_item_stale_timeout_minutes(gc))
        gc.config = {'transfer': {'item_stale_timeout_minutes': -3}}
        self.assertEqual(1, GlobalConfig.get_item_stale_timeout_minutes(gc))
        gc.config = {'transfer': {'item_stale_timeout_minutes': 99999}}
        self.assertEqual(180, GlobalConfig.get_item_stale_timeout_minutes(gc))
        gc.config = {}
        self.assertEqual(5, GlobalConfig.get_item_stale_timeout_minutes(gc))


if __name__ == '__main__':
    unittest.main()
