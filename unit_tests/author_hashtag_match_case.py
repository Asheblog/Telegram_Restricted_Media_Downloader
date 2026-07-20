# coding=UTF-8
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.author_hashtag_match import (
    extract_hashtags_from_text,
    match_author_from_hashtags,
    normalize_author_label,
)


class AuthorHashtagMatchCase(unittest.TestCase):
    def test_extract_hashtags_preserves_order_and_dedupes(self):
        tags = extract_hashtags_from_text(
            '#海角社区 #会喷水的亲姐姐 【55分原创】发现暧昧 #会喷水的亲姐姐'
        )
        self.assertEqual(['海角社区', '会喷水的亲姐姐'], tags)

    def test_topic_tags_alone_do_not_match(self):
        match = match_author_from_hashtags(
            ['人妻', '熟女', '视频'],
            known_authors=['喷水的姐姐'],
        )
        self.assertIsNone(match.author)
        self.assertEqual('none', match.method)

    def test_exact_hashtag_hits_known_author(self):
        match = match_author_from_hashtags(
            ['海角社区', '喷水的姐姐', '人妻'],
            known_authors=['喷水的姐姐', '小兽先生'],
            extra_deny=['海角社区'],
        )
        self.assertEqual('喷水的姐姐', match.author)
        self.assertEqual('medium', match.confidence)
        self.assertEqual('hashtag_exact', match.method)

    def test_substring_hashtag_needs_confirm(self):
        match = match_author_from_hashtags(
            ['海角社区', '会喷水的亲姐姐', '人妻'],
            known_authors=['喷水的姐姐'],
            extra_deny=['海角社区'],
        )
        self.assertEqual('喷水的姐姐', match.author)
        self.assertEqual('low', match.confidence)
        self.assertEqual('hashtag_substring', match.method)

    def test_unique_non_denied_tag_becomes_confirm_candidate(self):
        match = match_author_from_hashtags(
            ['海角社区', '想双飞老婆姐姐'],
            known_authors=['喷水的姐姐'],
        )
        self.assertEqual('想双飞老婆姐姐', match.author)
        self.assertEqual('low', match.confidence)
        self.assertEqual('hashtag_candidate', match.method)

    def test_ambiguous_non_denied_tags_stay_unmatched(self):
        match = match_author_from_hashtags(
            ['想双飞老婆姐姐', '另一个作者名'],
            known_authors=['喷水的姐姐'],
        )
        self.assertIsNone(match.author)
        self.assertEqual('none', match.method)

    def test_denied_site_name_never_matches_as_known_author(self):
        match = match_author_from_hashtags(
            ['海角社区', '翘臀巨乳小妈'],
            known_authors=['海角社区', '翘臀巨乳小妈'],
        )
        self.assertEqual('翘臀巨乳小妈', match.author)
        self.assertEqual('hashtag_exact', match.method)

        only_site = match_author_from_hashtags(
            ['海角社区'],
            known_authors=['海角社区'],
        )
        self.assertIsNone(only_site.author)

    def test_normalize_strips_punctuation(self):
        self.assertEqual(
            normalize_author_label('#喷水的姐姐，'),
            normalize_author_label('喷水的姐姐'),
        )


if __name__ == '__main__':
    unittest.main()
