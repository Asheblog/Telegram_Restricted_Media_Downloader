# coding=UTF-8
import unittest

from module.enums import UploadStatus
from module.statistics_payload import build_statistics_payload


class _FakeApp:
    def __init__(self):
        self.success_video = {'a'}
        self.failure_video = set()
        self.skip_video = set()
        self.success_photo = {'b', 'c'}
        self.failure_photo = {'d'}
        self.skip_photo = set()
        self.success_document = set()
        self.failure_document = set()
        self.skip_document = set()
        self.success_audio = set()
        self.failure_audio = set()
        self.skip_audio = set()
        self.success_voice = set()
        self.failure_voice = set()
        self.skip_voice = set()
        self.success_animation = set()
        self.failure_animation = set()
        self.skip_animation = set()
        self.success_video_note = set()
        self.failure_video_note = set()
        self.skip_video_note = set()


class _FakeUploadTask:
    def __init__(self, status, chat_id='-1001', file_path='/tmp/demo.mp4', file_size=1024):
        self.status = status
        self.chat_id = chat_id
        self.file_path = file_path
        self.file_name = 'demo.mp4'
        self.file_size = file_size
        self.error_msg = ''
        self.with_delete = False


class StatisticsPayloadCase(unittest.TestCase):
    def test_build_statistics_payload_aggregates_links_counts_and_uploads(self):
        link_info = {
            'https://t.me/demo/1': {
                'complete_num': 2,
                'member_num': 2,
                'file_name': {'a.mp4', 'b.mp4'},
                'error_msg': {},
            },
            'https://t.me/demo/2': {
                'complete_num': 1,
                'member_num': 4,
                'file_name': {'c.mp4'},
                'error_msg': {},
            },
            'https://t.me/demo/3': {
                'complete_num': 0,
                'member_num': 2,
                'file_name': set(),
                'error_msg': {'all_member': 'FloodWait'},
            },
        }
        upload_tasks = {
            _FakeUploadTask(UploadStatus.SUCCESS),
            _FakeUploadTask(UploadStatus.FAILURE),
        }
        list(upload_tasks)[1].error_msg = 'timeout'

        payload = build_statistics_payload(link_info, _FakeApp(), upload_tasks)

        self.assertTrue(payload['tables']['link']['available'])
        self.assertTrue(payload['tables']['count']['available'])
        self.assertTrue(payload['tables']['upload']['available'])
        self.assertEqual(3, payload['summary']['links'])
        self.assertEqual(4, payload['summary']['downloads_total'])
        self.assertEqual(75.0, payload['summary']['success_rate'])
        self.assertEqual(1, payload['summary']['failure_count'])
        self.assertEqual(2, payload['summary']['upload_tasks'])
        self.assertEqual(1, payload['summary']['upload_completed'])
        self.assertEqual('complete', payload['links'][0]['status'])
        self.assertEqual('progress', payload['links'][1]['status'])
        self.assertEqual('error', payload['links'][2]['status'])
        self.assertEqual(1, payload['link_completion']['complete'])
        self.assertEqual(1, payload['link_completion']['progress'])
        self.assertEqual(1, payload['link_completion']['error'])
        self.assertEqual(7, len(payload['count_by_type']))
        self.assertEqual(2, len(payload['upload_rows']))


if __name__ == '__main__':
    unittest.main()
