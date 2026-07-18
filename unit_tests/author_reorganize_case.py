# coding=UTF-8
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.archive_reorganize import plan_author_reorganize, rewrite_transfer_source_folder
from module.source_folders import UNKNOWN_AUTHOR_FOLDER


class AuthorReorganizePlanCase(unittest.TestCase):
    def test_plan_moves_flat_posts_under_authors(self):
        plan = plan_author_reorganize(
            channel_folder='chengdudiyi8',
            directory_paths=[
                'chengdudiyi8/92862 - 湿逼是真的奇妙',
                'chengdudiyi8/92850 - 我也忘了',
                'chengdudiyi8/99999 - 无作者行',
            ],
            author_by_message_id={
                92862: '我的羞涩女儿',
                92850: '我的羞涩女儿',
                99999: None,
            },
        )
        self.assertEqual(2, plan.author_count)  # 我的羞涩女儿 + _未知作者
        self.assertEqual(3, plan.move_count)
        self.assertEqual(
            {
                '92862 - 湿逼是真的奇妙': '我的羞涩女儿/92862 - 湿逼是真的奇妙',
                '92850 - 我也忘了': '我的羞涩女儿/92850 - 我也忘了',
                '99999 - 无作者行': f'{UNKNOWN_AUTHOR_FOLDER}/99999 - 无作者行',
            },
            {item.from_relative: item.to_relative for item in plan.moves if item.action == 'move'},
        )

    def test_plan_skips_already_nested_matching_author(self):
        plan = plan_author_reorganize(
            channel_folder='chengdudiyi8',
            directory_paths=['chengdudiyi8/我的羞涩女儿/92862 - title'],
            author_by_message_id={92862: '我的羞涩女儿'},
        )
        self.assertEqual(0, plan.move_count)
        self.assertEqual(1, plan.skip_count)
        self.assertEqual('skip_already', plan.moves[0].action)

    def test_rewrite_transfer_source_folder_updates_matching_item(self):
        updated = rewrite_transfer_source_folder(
            'chengdudiyi8/92862 - title',
            channel_folder='chengdudiyi8',
            from_relative='92862 - title',
            to_relative='我的羞涩女儿/92862 - title',
        )
        self.assertEqual('chengdudiyi8/我的羞涩女儿/92862 - title', updated)
        self.assertIsNone(
            rewrite_transfer_source_folder(
                'other/92862 - title',
                channel_folder='chengdudiyi8',
                from_relative='92862 - title',
                to_relative='我的羞涩女儿/92862 - title',
            )
        )


if __name__ == '__main__':
    unittest.main()
