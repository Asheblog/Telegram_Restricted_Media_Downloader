# coding=UTF-8
import base64
import http.client
import json
import os
import tempfile
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.transfer_store import TransferStatus, TransferStore
from module.web_ui import WebUiServer


class TransferStoreWebUiCase(unittest.TestCase):
    def test_download_success_record_is_reused_only_when_file_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            media_path = os.path.join(directory, 'media.bin')
            with open(media_path, 'wb') as file:
                file.write(b'12345')

            store = TransferStore(directory=directory)
            store.upsert_download_success_record(
                source_chat_id='-100123',
                source_message_id=42,
                source_link='https://t.me/c/123/42',
                media_type='document',
                local_path=media_path,
                file_size=5,
                file_name='media.bin'
            )

            record = store.get_download_success_record('-100123', 42, expected_size=5)
            self.assertIsNotNone(record)
            self.assertEqual(media_path, record['local_path'])

            os.remove(media_path)
            self.assertIsNone(store.get_download_success_record('-100123', 42, expected_size=5))

    def test_task_progress_counts_delete_and_download_records_are_public_behaviors(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            item_id = store.add_item(
                task_id=task_id,
                source_message_id=1,
                source_link='https://t.me/source/1',
                target_link='https://t.me/pikpak_bot',
                source_chat_id='source',
                media_type='document',
                file_name='demo.bin',
                file_size=10
            )

            store.update_item_progress(item_id, phase='downloading', download_current=4, download_total=10)
            payload = store.task_payload(task_id)
            self.assertEqual('downloading', payload['items'][0]['phase'])
            self.assertEqual(4, payload['items'][0]['download_current'])
            self.assertEqual(10, payload['items'][0]['download_total'])

            store.update_item(item_id, status=TransferStatus.SUCCESS)
            store.refresh_task_counts(task_id, expected_total=1)
            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.SUCCESS, task['status'])
            self.assertEqual(1, task['completed_items'])

            store.delete_task(task_id)
            self.assertIsNone(store.get_task(task_id))

    def test_webui_exposes_delete_settings_and_download_records_without_secret_leaks(self):
        with tempfile.TemporaryDirectory() as directory:
            media_path = os.path.join(directory, 'media.bin')
            with open(media_path, 'wb') as file:
                file.write(b'12345')
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.upsert_download_success_record(
                source_chat_id='source',
                source_message_id=1,
                source_link='https://t.me/source/1',
                media_type='document',
                local_path=media_path,
                file_size=5,
                file_name='media.bin'
            )
            settings = {
                'user': {'api_hash': 'real-secret', 'download_type': ['video']},
                'global': {'notice': True}
            }

            def get_settings():
                return settings

            def update_settings(payload):
                settings['global']['notice'] = bool(payload['global']['notice'])
                return get_settings()

            server = WebUiServer(
                store=store,
                settings_provider=get_settings,
                settings_updater=update_settings,
                username='admin',
                password='pass'
            )
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request('GET', '/api/settings', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertNotIn('real-secret', json.dumps(body, ensure_ascii=False))

                conn.request(
                    'PATCH',
                    '/api/settings',
                    body=json.dumps({'global': {'notice': False}}),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertFalse(body['settings']['global']['notice'])

                conn.request('GET', '/api/download-records', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertEqual(1, len(body['records']))

                conn.request('DELETE', f'/api/tasks/{task_id}', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['deleted'])
                self.assertIsNone(store.get_task(task_id))
                self.assertEqual(1, len(store.list_download_success_records()))
            finally:
                server.stop()

    def test_webui_api_errors_include_stable_error_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            server = WebUiServer(store=store, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request('GET', '/api/tasks/not-a-number', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(400, response.status)
                self.assertEqual('invalid_task_id', body['error_code'])

                conn.request(
                    'POST',
                    '/api/tasks',
                    body=json.dumps({'target_link': 'https://t.me/pikpak_bot'}),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(400, response.status)
                self.assertEqual('source_link_required', body['error_code'])

                conn.request(
                    'POST',
                    '/api/tasks',
                    body=json.dumps({
                        'source_link': 'https://t.me/source',
                        'target_link': 'https://t.me/pikpak_bot',
                        'start_id': 9,
                        'end_id': 3
                    }),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(400, response.status)
                self.assertEqual('range_end_before_start', body['error_code'])
            finally:
                server.stop()


if __name__ == '__main__':
    unittest.main()
