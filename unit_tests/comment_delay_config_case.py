# coding=UTF-8
import sys
import tempfile
import unittest
from copy import deepcopy

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.core.config import GlobalConfig
sys.argv = _ORIGINAL_ARGV


class CommentDelayConfigCase(unittest.TestCase):
    def test_default_comment_delay_minutes_is_20(self):
        self.assertEqual(20, GlobalConfig.TEMPLATE['live_watch']['comment_delay_minutes'])

    def test_getter_clamps_and_defaults(self):
        gc = GlobalConfig.__new__(GlobalConfig)
        gc.default_live_watch_nesting = deepcopy(GlobalConfig.TEMPLATE['live_watch'])
        gc.config = {'live_watch': {'comment_delay_minutes': 20}}
        self.assertEqual(20, GlobalConfig.get_comment_delay_minutes(gc))
        gc.config = {'live_watch': {'comment_delay_minutes': 0}}
        self.assertEqual(0, GlobalConfig.get_comment_delay_minutes(gc))
        gc.config = {'live_watch': {'comment_delay_minutes': -5}}
        self.assertEqual(0, GlobalConfig.get_comment_delay_minutes(gc))
        gc.config = {'live_watch': {'comment_delay_minutes': 99999}}
        self.assertEqual(1440, GlobalConfig.get_comment_delay_minutes(gc))
        gc.config = {}
        self.assertEqual(20, GlobalConfig.get_comment_delay_minutes(gc))


if __name__ == '__main__':
    unittest.main()
