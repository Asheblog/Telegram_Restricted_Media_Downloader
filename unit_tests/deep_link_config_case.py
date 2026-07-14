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


class DeepLinkConfigCase(unittest.TestCase):
    def test_template_defaults(self):
        self.assertEqual([], GlobalConfig.TEMPLATE['deep_link']['bot_whitelist'])
        self.assertEqual(60, GlobalConfig.TEMPLATE['deep_link']['timeout_seconds'])
        self.assertEqual(30, GlobalConfig.TEMPLATE['deep_link']['min_interval_seconds'])
        self.assertEqual(3, GlobalConfig.TEMPLATE['deep_link']['settle_seconds'])

    def test_getters(self):
        gc = GlobalConfig.__new__(GlobalConfig)
        gc.default_deep_link_nesting = deepcopy(GlobalConfig.TEMPLATE['deep_link'])
        gc.config = {'deep_link': {'bot_whitelist': ['@A82Bot', ''], 'timeout_seconds': 60}}
        self.assertEqual(['a82bot'], gc.get_deep_link_bot_whitelist())
        gc.config = {'deep_link': {'timeout_seconds': 0}}
        self.assertEqual(1, gc.get_deep_link_timeout_seconds())  # clamp min 1
        gc.config = {'deep_link': {'timeout_seconds': 9999}}
        self.assertEqual(600, gc.get_deep_link_timeout_seconds())  # clamp max 600
        gc.config = {'deep_link': {'min_interval_seconds': -1}}
        self.assertEqual(0, gc.get_deep_link_min_interval_seconds())
        gc.config = {'deep_link': {'min_interval_seconds': 9999}}
        self.assertEqual(600, gc.get_deep_link_min_interval_seconds())
        gc.config = {'deep_link': {'settle_seconds': -1}}
        self.assertEqual(0, gc.get_deep_link_settle_seconds())
        gc.config = {'deep_link': {'settle_seconds': 999}}
        self.assertEqual(60, gc.get_deep_link_settle_seconds())
        gc.config = {}
        self.assertEqual([], gc.get_deep_link_bot_whitelist())
        self.assertEqual(60, gc.get_deep_link_timeout_seconds())
        self.assertEqual(30, gc.get_deep_link_min_interval_seconds())
        self.assertEqual(3, gc.get_deep_link_settle_seconds())


if __name__ == '__main__':
    unittest.main()
