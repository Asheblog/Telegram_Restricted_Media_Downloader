# coding=UTF-8
import unittest

from module.statistics_payload import (
    OTHER_CHANNEL_LABEL,
    build_statistics_payload,
)


class StatisticsPayloadCase(unittest.TestCase):
    def test_build_statistics_payload_aggregates_channels_and_kpis(self):
        rows = [
            {'channel': 'alpha', 'success': 8, 'failure': 1, 'skip': 1, 'total': 10},
            {'channel': 'beta', 'success': 3, 'failure': 2, 'skip': 0, 'total': 5},
        ]

        payload = build_statistics_payload(rows, chart_limit=12, window_days=7)

        self.assertTrue(payload['tables']['channel']['available'])
        self.assertEqual(2, payload['tables']['channel']['rows'])
        self.assertEqual(2, payload['summary']['channels'])
        self.assertEqual(15, payload['summary']['downloads_total'])
        self.assertEqual(73.3, payload['summary']['success_rate'])
        self.assertEqual(3, payload['summary']['failure_count'])
        self.assertEqual(1, payload['summary']['skip_count'])
        self.assertEqual(4, payload['summary']['issue_count'])
        self.assertEqual(7, payload['summary']['window_days'])
        self.assertEqual(2, len(payload['channels']))
        self.assertEqual('alpha', payload['channels'][0]['channel'])
        self.assertEqual(80.0, payload['channels'][0]['success_rate'])
        self.assertEqual(2, len(payload['count_by_channel']))
        self.assertEqual(payload['channels'], payload['count_by_channel'])

    def test_build_statistics_payload_collapses_chart_overflow_into_other(self):
        rows = [
            {
                'channel': f'ch-{index}',
                'success': 20 - index,
                'failure': 1,
                'skip': 0,
                'total': 21 - index,
            }
            for index in range(15)
        ]

        payload = build_statistics_payload(rows, chart_limit=12)

        chart = payload['chart_by_channel']
        self.assertEqual(13, len(chart))
        self.assertEqual(OTHER_CHANNEL_LABEL, chart[-1]['channel'])
        self.assertTrue(chart[-1]['is_other'])
        overflow = rows[12:]
        self.assertEqual(sum(row['success'] for row in overflow), chart[-1]['success'])
        self.assertEqual(sum(row['failure'] for row in overflow), chart[-1]['failure'])
        self.assertEqual(sum(row['skip'] for row in overflow), chart[-1]['skip'])
        self.assertEqual(15, len(payload['channels']))

    def test_build_statistics_payload_empty(self):
        payload = build_statistics_payload([])

        self.assertFalse(payload['tables']['channel']['available'])
        self.assertEqual(0, payload['summary']['channels'])
        self.assertEqual(0, payload['summary']['downloads_total'])
        self.assertEqual(0.0, payload['summary']['success_rate'])
        self.assertEqual([], payload['channels'])
        self.assertEqual([], payload['chart_by_channel'])


if __name__ == '__main__':
    unittest.main()
