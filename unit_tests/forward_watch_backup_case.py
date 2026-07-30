# coding=UTF-8
import unittest

from module.transfer.forward_watch_backup import (
    FORWARD_WATCH_BACKUP_KIND,
    FORWARD_WATCH_BACKUP_VERSION,
    build_forward_watch_export_payload,
    import_forward_watch_entries,
    normalize_forward_watch_entry,
    parse_forward_watch_import_payload,
)


class ForwardWatchBackupCase(unittest.TestCase):
    def test_normalize_forward_watch_entry(self):
        entry = normalize_forward_watch_entry({
            'source_link': 'https://t.me/source',
            'target_link': 'https://t.me/target',
            'include_comment': True,
            'resolve_deep_link': False,
            'comment_delay_minutes': 90,
        })
        self.assertEqual(entry['source_link'], 'https://t.me/source')
        self.assertTrue(entry['include_comment'])
        self.assertFalse(entry['resolve_deep_link'])
        self.assertEqual(90, entry['comment_delay_minutes'])

    def test_normalize_missing_comment_delay_inherits(self):
        entry = normalize_forward_watch_entry({
            'source_link': 'https://t.me/source',
            'target_link': 'https://t.me/target',
        })
        self.assertIsNone(entry['comment_delay_minutes'])

    def test_normalize_rejects_invalid_comment_delay(self):
        self.assertIsNone(normalize_forward_watch_entry({
            'source_link': 'https://t.me/source',
            'target_link': 'https://t.me/target',
            'comment_delay_minutes': 9999,
        }))

    def test_normalize_rejects_invalid_links(self):
        self.assertIsNone(normalize_forward_watch_entry({'source_link': 'http://bad', 'target_link': 'https://t.me/target'}))
        self.assertIsNone(normalize_forward_watch_entry({'source_link': 'https://t.me/source'}))

    def test_build_export_payload_deduplicates(self):
        payload = build_forward_watch_export_payload([
            {
                'source_link': 'https://t.me/a',
                'target_link': 'https://t.me/b',
                'include_comment': True,
            },
            {
                'source_link': 'https://t.me/a',
                'target_link': 'https://t.me/b',
                'include_comment': False,
            },
            {
                'source_link': 'https://t.me/c',
                'target_link': 'https://t.me/d',
            },
        ])
        self.assertEqual(FORWARD_WATCH_BACKUP_VERSION, payload['version'])
        self.assertEqual(FORWARD_WATCH_BACKUP_KIND, payload['kind'])
        self.assertEqual(2, len(payload['watches']))

    def test_parse_import_payload_accepts_export_and_array(self):
        export_payload = {
            'version': 1,
            'kind': FORWARD_WATCH_BACKUP_KIND,
            'watches': [{'source_link': 'https://t.me/a', 'target_link': 'https://t.me/b'}],
        }
        entries, errors = parse_forward_watch_import_payload(export_payload)
        self.assertEqual([], errors)
        self.assertEqual(1, len(entries))

        entries, errors = parse_forward_watch_import_payload(export_payload['watches'])
        self.assertEqual([], errors)
        self.assertEqual(1, len(entries))

    def test_parse_import_payload_rejects_invalid_kind(self):
        entries, errors = parse_forward_watch_import_payload({
            'version': 1,
            'kind': 'other',
            'watches': [],
        })
        self.assertEqual([], entries)
        self.assertEqual(['invalid_kind'], errors)

    def test_import_skips_existing_and_creates_missing(self):
        created = []

        def create_watch(payload):
            if payload['source_link'] == 'https://t.me/exists':
                raise ValueError('watch_already_exists')
            created.append(payload)
            return {'watches': [{'id': 'forward:test', **payload}]}

        result = import_forward_watch_entries([
            {
                'source_link': 'https://t.me/exists',
                'target_link': 'https://t.me/target',
            },
            {
                'source_link': 'https://t.me/new',
                'target_link': 'https://t.me/target',
            },
            {
                'source_link': 'bad',
                'target_link': 'https://t.me/target',
            },
        ], create_watch)

        self.assertEqual(1, result['created'])
        self.assertEqual(1, result['skipped'])
        self.assertEqual(1, result['failed'])
        self.assertEqual(1, len(created))


if __name__ == '__main__':
    unittest.main()
