# coding=UTF-8
import tempfile
import unittest
from pathlib import Path

from module.persistence.transfer_store import TransferStore
from module.utils.util import make_forward_watch_rule, parse_forward_watch_rule


class DeepLinkStoreCase(unittest.TestCase):
    def test_create_task_persists_flag(self):
        db = Path(tempfile.mkdtemp()) / 't.sqlite'
        store = TransferStore(str(db))
        tid = store.create_task(
            source_link='https://t.me/swag_vip',
            target_link='https://t.me/pikpak_bot',
            target_profile='pikpak',
            start_id=1,
            end_id=2,
            include_comment=False,
            resolve_deep_link=True,
        )
        task = store.get_task(tid)
        self.assertTrue(task['resolve_deep_link'])

    def test_watch_rule_flag(self):
        rule = make_forward_watch_rule('https://t.me/a', 'https://t.me/b', False, True)
        parsed = parse_forward_watch_rule(rule)
        self.assertTrue(parsed['resolve_deep_link'])
        self.assertFalse(parsed['include_comment'])


if __name__ == '__main__':
    unittest.main()
