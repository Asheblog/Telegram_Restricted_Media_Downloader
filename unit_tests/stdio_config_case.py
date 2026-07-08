# coding=UTF-8
import unittest
import sys
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

sys.argv = [sys.argv[0]]
install_pyrogram_stub()

from module.stdio import StatisticalTable


def make_app(links):
    return SimpleNamespace(
        enable_proxy=False,
        links=links,
        download_type=['video', 'video_note']
    )


class ConfigTableCase(unittest.TestCase):
    def test_config_table_skips_missing_initial_links_in_webui_mode(self):
        with self.assertNoLogs('rich', level='WARNING'):
            StatisticalTable.print_config_table(make_app(None))

    def test_config_table_skips_blank_initial_links(self):
        with self.assertNoLogs('rich', level='WARNING'):
            StatisticalTable.print_config_table(make_app(''))

    def test_config_table_warns_when_configured_links_file_is_missing(self):
        with self.assertLogs('rich', level='WARNING') as logs:
            StatisticalTable.print_config_table(make_app('/definitely/missing/TRMD-links.txt'))

        self.assertIn('无法读取媒体链接文件', '\n'.join(logs.output))


if __name__ == '__main__':
    unittest.main()
