# coding=UTF-8
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.archive_reorganize import (
    AuthorHint,
    filter_plan_moves,
    plan_author_reorganize,
    rewrite_transfer_source_folder,
)
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
        self.assertEqual(1, plan.author_count)
        self.assertEqual(2, plan.move_count)
        self.assertEqual(1, plan.review_count)
        self.assertEqual(2, plan.executable_count)
        self.assertEqual(
            {
                '92862 - 湿逼是真的奇妙': '我的羞涩女儿/92862 - 湿逼是真的奇妙',
                '92850 - 我也忘了': '我的羞涩女儿/92850 - 我也忘了',
            },
            {item.from_relative: item.to_relative for item in plan.moves if item.action == 'move'},
        )
        review = next(item for item in plan.moves if item.action == 'needs_review')
        self.assertEqual(UNKNOWN_AUTHOR_FOLDER, review.author)
        self.assertEqual(f'{UNKNOWN_AUTHOR_FOLDER}/99999 - 无作者行', review.to_relative)

    def test_plan_hashtag_substring_is_needs_confirm(self):
        plan = plan_author_reorganize(
            channel_folder='chengdudiyi8',
            directory_paths=['chengdudiyi8/100 - title'],
            author_by_message_id={
                100: AuthorHint(
                    name='喷水的姐姐',
                    confidence='low',
                    method='hashtag_substring',
                    matched_tag='会喷水的亲姐姐',
                ),
            },
        )
        self.assertEqual(1, plan.confirm_count)
        self.assertEqual(0, plan.move_count)
        self.assertEqual(1, plan.executable_count)
        self.assertEqual('needs_confirm', plan.moves[0].action)
        self.assertEqual('会喷水的亲姐姐', plan.moves[0].matched_tag)

    def test_plan_hashtag_candidate_is_needs_confirm(self):
        plan = plan_author_reorganize(
            channel_folder='chengdudiyi8',
            directory_paths=['chengdudiyi8/200 - title'],
            author_by_message_id={
                200: AuthorHint(
                    name='想双飞老婆姐姐',
                    confidence='low',
                    method='hashtag_candidate',
                    matched_tag='想双飞老婆姐姐',
                ),
            },
        )
        self.assertEqual(1, plan.confirm_count)
        self.assertEqual('needs_confirm', plan.moves[0].action)
        self.assertEqual('想双飞老婆姐姐', plan.moves[0].author)

    def test_filter_plan_moves_pages_executable_bucket(self):
        plan = plan_author_reorganize(
            channel_folder='ch',
            directory_paths=[
                'ch/1 - a',
                'ch/2 - b',
                'ch/3 - c',
            ],
            author_by_message_id={
                1: AuthorHint(name='A', confidence='high', method='signature'),
                2: AuthorHint(name='A', confidence='low', method='hashtag_substring'),
                3: None,
            },
        )
        page = filter_plan_moves(plan.to_dict()['moves'], bucket='executable', offset=0, limit=10)
        self.assertEqual(2, page['total'])
        self.assertEqual({'move', 'needs_confirm'}, {item['action'] for item in page['items']})

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
