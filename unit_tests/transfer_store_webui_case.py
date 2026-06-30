# coding=UTF-8
import base64
import asyncio
import http.client
import inspect
import json
import os
import sys
import tempfile
import time
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

import module as trmd_module
from module.transfer_store import TransferStatus, TransferStore
from module.web_ui import WebUiServer


def import_with_clean_argv(importer):
    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0]]
        return importer()
    finally:
        sys.argv = original_argv


class FakeWebUiOperations:
    def __init__(self):
        self.watches = {}
        self.created_uploads = []
        self.created_channel_downloads = []
        self.exported_tables = []
        self.transfer_range = None
        self.transfer_range_error = None
        self.detected_transfer_ranges = []

    def list_watches(self):
        return list(self.watches.values())

    def create_watch(self, payload):
        watch_type = payload.get('type')
        if watch_type == 'download':
            created = []
            for source_link in payload.get('source_links') or []:
                if self._has_forward_source(source_link):
                    raise ValueError('watch_source_conflict')
                watch_id = f'download:{source_link}'
                self.watches[watch_id] = {
                    'id': watch_id,
                    'type': 'download',
                    'source_link': source_link,
                    'target_link': None
                }
                created.append(self.watches[watch_id])
            return {'watches': created}
        if watch_type == 'forward':
            source_link = payload.get('source_link')
            target_link = payload.get('target_link')
            if self._has_download_source(source_link):
                raise ValueError('watch_source_conflict')
            watch_id = f'forward:{source_link}->{target_link}'
            self.watches[watch_id] = {
                'id': watch_id,
                'type': 'forward',
                'source_link': source_link,
                'target_link': target_link,
                'include_comment': bool(payload.get('include_comment'))
            }
            return {'watches': [self.watches[watch_id]]}
        raise ValueError('Unsupported watch type.')

    def _has_download_source(self, source_link):
        return any(
            watch['type'] == 'download' and watch['source_link'] == source_link
            for watch in self.watches.values()
        )

    def _has_forward_source(self, source_link):
        return any(
            watch['type'] == 'forward' and watch['source_link'] == source_link
            for watch in self.watches.values()
        )

    def delete_watch(self, watch_id):
        return self.watches.pop(watch_id, None) is not None

    def create_upload(self, payload):
        self.created_uploads.append(payload)
        return {'accepted': True, 'upload_id': len(self.created_uploads)}

    def create_channel_download(self, payload):
        self.created_channel_downloads.append(payload)
        return {'accepted': True, 'task_id': len(self.created_channel_downloads)}

    def detect_transfer_range(self, source_link):
        self.detected_transfer_ranges.append(source_link)
        if self.transfer_range_error:
            raise self.transfer_range_error
        return self.transfer_range

    def statistics(self):
        return {
            'tables': {
                'link': {'available': True, 'rows': 2},
                'count': {'available': True, 'rows': 1},
                'upload': {'available': False, 'rows': 0}
            }
        }

    def export_table(self, table_type):
        self.exported_tables.append(table_type)
        return {'exported': True, 'table_type': table_type, 'directory': 'form'}


class TaskDeletingOperations:
    def __init__(self, store):
        self.store = store
        self.deleted_task_ids = []

    def delete_web_task(self, task_id):
        self.deleted_task_ids.append(task_id)
        return self.store.delete_task(task_id)


class FakeTelegramClient:
    def __init__(self):
        self.added_handlers = []
        self.removed_handlers = []

    async def get_chat(self, _link):
        return SimpleNamespace(id=12345, is_forum=False)

    def add_handler(self, handler):
        self.added_handlers.append(handler)

    def remove_handler(self, handler):
        self.removed_handlers.append(handler)


def import_downloader_class():
    def importer():
        from module.downloader import TelegramRestrictedMediaDownloader
        return TelegramRestrictedMediaDownloader

    return import_with_clean_argv(importer)


class TransferStoreWebUiCase(unittest.TestCase):
    def test_log_cleanup_removes_rotated_files_older_than_three_days(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = os.path.join(directory, 'TRMD_LOG.log')
            old_log = f'{log_path}.2026-06-20'
            fresh_log = f'{log_path}.2026-06-26'
            active_log = log_path
            for path in (old_log, fresh_log, active_log):
                with open(path, 'w', encoding='UTF-8') as file:
                    file.write('log')
            now = time.time()
            old_mtime = now - 5 * 24 * 60 * 60
            fresh_mtime = now - 24 * 60 * 60
            os.utime(old_log, (old_mtime, old_mtime))
            os.utime(fresh_log, (fresh_mtime, fresh_mtime))
            os.utime(active_log, (old_mtime, old_mtime))

            removed = trmd_module.cleanup_old_log_files(log_path=log_path, retention_days=3, now=now)

            self.assertEqual(1, removed)
            self.assertFalse(os.path.exists(old_log))
            self.assertTrue(os.path.exists(fresh_log))
            self.assertTrue(os.path.exists(active_log))

    def test_transfer_store_maintenance_vacuums_and_marks_last_run(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1')
            for index in range(200):
                store.add_event(task_id, f'large event {index} ' + ('x' * 4000))
            store.delete_task(task_id)

            with store.connect() as conn:
                free_pages_before = int(conn.execute('PRAGMA freelist_count').fetchone()[0])

            self.assertGreater(free_pages_before, 0)
            self.assertTrue(store.maintain(force=True))

            with store.connect() as conn:
                free_pages_after = int(conn.execute('PRAGMA freelist_count').fetchone()[0])
            self.assertEqual(0, free_pages_after)
            self.assertTrue(os.path.exists(f'{store.path}.maintenance'))

    def test_transfer_store_runs_maintenance_periodically_from_connections(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            marker_path = f'{store.path}.maintenance'
            old_mtime = time.time() - 7 * 60 * 60
            os.utime(marker_path, (old_mtime, old_mtime))
            store._last_maintenance_check = old_mtime

            with store.connect():
                pass

            self.assertGreater(os.path.getmtime(marker_path), old_mtime)

    def test_transfer_store_read_paths_use_covering_indexes(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1')
            for message_id in range(1, 6):
                store.add_item(
                    task_id=task_id,
                    source_chat_id='123',
                    source_message_id=message_id,
                    source_link=f'https://t.me/source/{message_id}',
                    target_link='https://t.me/pikpak_bot',
                    status=TransferStatus.SUCCESS if message_id % 2 else TransferStatus.FAILURE
                )
                store.add_event(task_id, f'event {message_id}')
            store.upsert_download_success_record(
                source_chat_id='123',
                source_message_id=1,
                source_link='https://t.me/source/1',
                media_type='document',
                local_path=__file__,
                file_size=os.path.getsize(__file__),
                file_name='transfer_store_webui_case.py'
            )

            with store.connect() as conn:
                plans = {
                    'items': conn.execute(
                        '''
                        EXPLAIN QUERY PLAN
                        SELECT * FROM transfer_items
                        WHERE task_id = ?
                        ORDER BY id ASC
                        ''',
                        (task_id,)
                    ).fetchall(),
                    'events': conn.execute(
                        '''
                        EXPLAIN QUERY PLAN
                        SELECT * FROM transfer_events
                        WHERE task_id = ?
                        ORDER BY id DESC
                        LIMIT ?
                        ''',
                        (task_id, 100)
                    ).fetchall(),
                    'record_list': conn.execute(
                        '''
                        EXPLAIN QUERY PLAN
                        SELECT * FROM download_success_records
                        ORDER BY updated_at DESC, id DESC
                        LIMIT ?
                        ''',
                        (100,)
                    ).fetchall(),
                    'count': conn.execute(
                        '''
                        EXPLAIN QUERY PLAN
                        SELECT status, COUNT(*) AS count
                        FROM transfer_items
                        WHERE task_id = ?
                        GROUP BY status
                        ''',
                        (task_id,)
                    ).fetchall()
                }

            flattened = {
                name: ' '.join(str(row['detail']).upper() for row in rows)
                for name, rows in plans.items()
            }
            self.assertIn('IDX_TRANSFER_ITEMS_TASK_ORDER', flattened['items'])
            self.assertIn('IDX_TRANSFER_EVENTS_TASK_ORDER', flattened['events'])
            self.assertIn('IDX_DOWNLOAD_RECORDS_UPDATED_ORDER', flattened['record_list'])
            self.assertIn('IDX_TRANSFER_ITEMS_TASK_STATUS', flattened['count'])

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

    def test_default_download_concurrency_and_pikpak_size_limit_are_system_defaults(self):
        config_module = import_with_clean_argv(
            lambda: __import__('module.config', fromlist=['GlobalConfig', 'UserConfig'])
        )
        GlobalConfig = config_module.GlobalConfig
        UserConfig = config_module.UserConfig
        from module.web_ui import merge_allowed_settings

        self.assertEqual(1, UserConfig.TEMPLATE['max_tasks']['download'])
        self.assertEqual(
            4 * 1024 ** 3,
            GlobalConfig.TEMPLATE['target_profiles']['pikpak']['max_file_size']
        )
        archive = GlobalConfig.TEMPLATE['target_profiles']['pikpak']['archive']
        self.assertTrue(archive['enable'])
        self.assertEqual('pikpak', archive['remote'])
        self.assertEqual('My Telegram', archive['source_directory'])
        self.assertEqual('Telegram', archive['root_directory'])

        settings = merge_allowed_settings(
            target=deepcopy(GlobalConfig.TEMPLATE),
            patch={'target_profiles': {'pikpak': {'max_file_size': 1024}}},
            allowed={'target_profiles'}
        )
        self.assertEqual(1024, settings['target_profiles']['pikpak']['max_file_size'])
        self.assertTrue(settings['target_profiles']['pikpak']['archive']['enable'])
        self.assertEqual(
            4 * 1024 ** 3,
            GlobalConfig.TEMPLATE['target_profiles']['pikpak']['max_file_size']
        )

    def test_global_target_profile_archive_config_is_completed_recursively(self):
        GlobalConfig = import_with_clean_argv(
            lambda: __import__('module.config', fromlist=['GlobalConfig'])
        ).GlobalConfig

        config = {
            'notice': True,
            'file_log_level': 'INFO',
            'console_log_level': 'INFO',
            'export_table': {'link': False, 'count': False, 'upload': False},
            'upload': {'download_upload': True, 'delete': False, 'pending_limit': 3},
            'target_profiles': {
                'pikpak': {
                    'max_file_size': 1024,
                    'archive': {
                        'enable': True
                    }
                }
            },
            'forward_type': {
                'video': True,
                'photo': True,
                'audio': True,
                'document': True,
                'voice': True,
                'text': True,
                'animation': True,
                'video_note': True
            }
        }

        GlobalConfig.process_target_profiles(GlobalConfig, config)

        archive = config['target_profiles']['pikpak']['archive']
        self.assertTrue(archive['enable'])
        self.assertEqual('pikpak', archive['remote'])
        self.assertEqual('My Telegram', archive['source_directory'])
        self.assertEqual('Telegram', archive['root_directory'])
        self.assertEqual(60, archive['poll_seconds'])
        self.assertEqual(5, archive['poll_interval_seconds'])
        self.assertEqual(3600, archive['match_window_seconds'])

    def test_transfer_task_persists_discussion_reply_inclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                include_comment=True
            )

            task = store.get_task(task_id)
            self.assertEqual(1, task['include_comment'])
            self.assertEqual(1, store.list_tasks()[0]['include_comment'])

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

                conn.request(
                    'POST',
                    '/api/tasks',
                    body=json.dumps({
                        'source_link': 'https://t.me/source',
                        'target_link': 'https://t.me/pikpak_bot',
                        'start_id': 1
                    }),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(400, response.status)
                self.assertEqual('range_ids_required', body['error_code'])
            finally:
                server.stop()

    def test_webui_task_api_detects_transfer_range_when_chat_link_has_no_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            submitted = []
            operations = FakeWebUiOperations()
            operations.transfer_range = {'start_id': 1, 'end_id': 9}
            server = WebUiServer(
                store=store,
                task_submitter=submitted.append,
                operations=operations,
                username='admin',
                password='pass'
            )
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request(
                    'POST',
                    '/api/tasks',
                    body=json.dumps({
                        'source_link': 'https://t.me/source',
                        'target_link': 'https://t.me/pikpak_bot'
                    }),
                    headers=headers
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))

                self.assertEqual(201, response.status)
                task = store.get_task(body['task_id'])
                self.assertEqual(1, task['start_id'])
                self.assertEqual(9, task['end_id'])
                self.assertEqual([body['task_id']], submitted)
                self.assertEqual(['https://t.me/source'], operations.detected_transfer_ranges)
            finally:
                server.stop()

    def test_webui_task_api_keeps_message_link_without_auto_range(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            operations.transfer_range = {'start_id': 1, 'end_id': 9}
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request(
                    'POST',
                    '/api/tasks',
                    body=json.dumps({
                        'source_link': 'https://t.me/source/123',
                        'target_link': 'https://t.me/pikpak_bot'
                    }),
                    headers=headers
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))

                self.assertEqual(201, response.status)
                task = store.get_task(body['task_id'])
                self.assertIsNone(task['start_id'])
                self.assertIsNone(task['end_id'])
                self.assertEqual([], operations.detected_transfer_ranges)
            finally:
                server.stop()

    def test_webui_task_api_reports_empty_detected_transfer_range(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            operations.transfer_range = None
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request(
                    'POST',
                    '/api/tasks',
                    body=json.dumps({
                        'source_link': 'https://t.me/source',
                        'target_link': 'https://t.me/pikpak_bot'
                    }),
                    headers=headers
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))

                self.assertEqual(400, response.status)
                self.assertEqual('transfer_range_empty', body['error_code'])
                self.assertEqual([], store.list_tasks())
            finally:
                server.stop()

    def test_webui_task_retry_failed_resets_failed_items_and_resubmits_task(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                start_id=1,
                end_id=2
            )
            failed_item_id = store.add_item(
                task_id=task_id,
                source_message_id=1,
                source_link='https://t.me/source/1',
                target_link='https://t.me/pikpak_bot',
                phase='failure',
                status=TransferStatus.FAILURE,
                error_message='PikPak ingest confirmation timeout or failure'
            )
            success_item_id = store.add_item(
                task_id=task_id,
                source_message_id=2,
                source_link='https://t.me/source/2',
                target_link='https://t.me/pikpak_bot',
                phase='forwarded',
                status=TransferStatus.SUCCESS
            )
            store.refresh_task_counts(task_id, expected_total=2, assignment_completed=True)
            submitted = []
            server = WebUiServer(
                store=store,
                task_submitter=submitted.append,
                username='admin',
                password='pass'
            )
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request('POST', f'/api/tasks/{task_id}/retry-failed', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))

                self.assertEqual(202, response.status)
                self.assertEqual(1, body['reset_items'])
                self.assertEqual([task_id], submitted)
                items = {item['id']: item for item in store.list_items(task_id)}
                self.assertEqual(TransferStatus.PENDING, items[failed_item_id]['status'])
                self.assertEqual('pending', items[failed_item_id]['phase'])
                self.assertIsNone(items[failed_item_id]['error_message'])
                self.assertEqual(TransferStatus.SUCCESS, items[success_item_id]['status'])
                task = store.get_task(task_id)
                self.assertEqual(TransferStatus.RUNNING, task['status'])
                self.assertEqual(1, task['completed_items'])
                self.assertEqual(0, task['failed_items'])
            finally:
                server.stop()

    def test_downloader_retry_failed_recovers_pikpak_timeout_before_resubmitting(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/chengdudiyi8',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=73962,
                end_id=73962
            )
            failed_item_id = store.add_item(
                task_id=task_id,
                source_message_id=73962,
                source_link='https://t.me/chengdudiyi8/73962',
                target_link='https://t.me/pikpak_bot',
                media_type='forward',
                file_name='73962 - 作者_ #海角社区 #示例标签.mp4',
                file_size=5,
                source_folder='chengdudiyi8',
                archive_status='pending',
                archive_match_original_name=False,
                phase='failure',
                status=TransferStatus.FAILURE,
                error_message='PikPak ingest confirmation timeout or failure: https://t.me/chengdudiyi8/73962'
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=True)
            archive_calls = []
            submitted = []

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(
                        ok=True,
                        status='success',
                        archive_path='Telegram/chengdudiyi8/73962 - 作者_ #海角社区 #示例标签.mp4'
                    )

            downloader.transfer_store = store
            downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()
            downloader.submit_web_task = lambda submitted_task_id: submitted.append(submitted_task_id)

            reset_items = downloader.retry_failed_web_task(task_id)

            self.assertEqual(0, reset_items)
            self.assertEqual([], submitted)
            self.assertEqual(1, len(archive_calls))
            self.assertEqual('chengdudiyi8', archive_calls[0]['source_folder'])
            self.assertEqual('73962 - 作者_ #海角社区 #示例标签.mp4', archive_calls[0]['file_name'])
            self.assertFalse(archive_calls[0]['match_original_name'])
            item = store.list_items(task_id)[0]
            self.assertEqual(failed_item_id, item['id'])
            self.assertEqual(TransferStatus.SUCCESS, item['status'])
            self.assertEqual('forwarded', item['phase'])
            self.assertEqual('success', item['archive_status'])
            self.assertEqual(0, item['archive_match_original_name'])
            self.assertEqual('', item['error_message'])
            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.SUCCESS, task['status'])
            self.assertEqual(1, task['completed_items'])
            self.assertEqual(0, task['failed_items'])
            events = store.list_events(task_id)
            self.assertTrue(any('recovered before retry' in event['message'] for event in events))

    def test_downloader_retry_failed_recovers_pikpak_archive_failure_before_resubmitting(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/ctuxas',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=1
            )
            item_id = store.add_item(
                task_id=task_id,
                source_message_id=1,
                source_link='https://t.me/ctuxas/1',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='1 - 标题.mp4',
                file_size=5,
                source_folder='ctuxas',
                archive_status='not_found',
                archive_match_original_name=True,
                phase='failure',
                status=TransferStatus.FAILURE,
                error_message='PikPak archive not_found: No PikPak file matched 1 - 标题.mp4.'
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=True)
            archive_calls = []
            submitted = []

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(
                        ok=True,
                        status='success',
                        archive_path='Telegram/ctuxas/1 - 标题.mp4'
                    )

            downloader.transfer_store = store
            downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()
            downloader.submit_web_task = lambda submitted_task_id: submitted.append(submitted_task_id)

            reset_items = downloader.retry_failed_web_task(task_id)

            self.assertEqual(0, reset_items)
            self.assertEqual([], submitted)
            self.assertEqual(1, len(archive_calls))
            self.assertEqual('1 - 标题.mp4', archive_calls[0]['file_name'])
            self.assertTrue(archive_calls[0]['match_original_name'])
            item = store.list_items(task_id)[0]
            self.assertEqual(item_id, item['id'])
            self.assertEqual(TransferStatus.SUCCESS, item['status'])
            self.assertEqual('forwarded', item['phase'])
            self.assertEqual('success', item['archive_status'])
            self.assertEqual(1, item['archive_match_original_name'])
            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.SUCCESS, task['status'])
            self.assertEqual(1, task['completed_items'])
            self.assertEqual(0, task['failed_items'])

    def test_downloader_retry_failed_resubmits_items_that_cannot_be_recovered(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/chengdudiyi8',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=2
            )
            recovered_item_id = store.add_item(
                task_id=task_id,
                source_message_id=1,
                source_link='https://t.me/chengdudiyi8/1',
                target_link='https://t.me/pikpak_bot',
                media_type='forward',
                file_name='done.mp4',
                file_size=5,
                source_folder='chengdudiyi8',
                phase='failure',
                status=TransferStatus.FAILURE,
                error_message='PikPak ingest confirmation timeout or failure: https://t.me/chengdudiyi8/1'
            )
            retry_item_id = store.add_item(
                task_id=task_id,
                source_message_id=2,
                source_link='https://t.me/chengdudiyi8/2',
                target_link='https://t.me/pikpak_bot',
                media_type='forward',
                file_name='missing.mp4',
                file_size=7,
                source_folder='chengdudiyi8',
                phase='failure',
                status=TransferStatus.FAILURE,
                error_message='PikPak ingest confirmation timeout or failure: https://t.me/chengdudiyi8/2'
            )
            store.refresh_task_counts(task_id, expected_total=2, assignment_completed=True)
            archive_calls = []
            submitted = []

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    if kwargs.get('file_name') == 'done.mp4':
                        return SimpleNamespace(ok=True, status='success', archive_path='Telegram/chengdudiyi8/done.mp4')
                    return SimpleNamespace(ok=False, status='not_found', message='not indexed yet')

            downloader.transfer_store = store
            downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()
            downloader.submit_web_task = lambda submitted_task_id: submitted.append(submitted_task_id)

            reset_items = downloader.retry_failed_web_task(task_id)

            self.assertEqual(1, reset_items)
            self.assertEqual([task_id], submitted)
            self.assertEqual(2, len(archive_calls))
            items = {item['id']: item for item in store.list_items(task_id)}
            self.assertEqual(TransferStatus.SUCCESS, items[recovered_item_id]['status'])
            self.assertEqual('success', items[recovered_item_id]['archive_status'])
            self.assertEqual(TransferStatus.PENDING, items[retry_item_id]['status'])
            self.assertEqual('pending', items[retry_item_id]['phase'])
            self.assertIsNone(items[retry_item_id]['error_message'])
            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.RUNNING, task['status'])
            self.assertEqual(1, task['completed_items'])
            self.assertEqual(0, task['failed_items'])

    def test_webui_task_pause_blocks_scheduling_and_resume_resubmits(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source', 'https://t.me/pikpak_bot')
            downloader.transfer_store = store
            downloader.web_submitted_task_ids = set()
            submitted = []
            downloader.submit_web_task = lambda submitted_task_id: submitted.append(submitted_task_id)
            downloader.discard_web_task_submission = lambda discarded_task_id, cancel_running=False: submitted.append(
                f'discard:{discarded_task_id}:{cancel_running}'
            )

            self.assertTrue(downloader.pause_web_task(task_id))
            self.assertEqual(TransferStatus.PAUSED, store.get_task(task_id)['status'])
            store.refresh_task_counts(task_id)
            self.assertEqual(TransferStatus.PAUSED, store.get_task(task_id)['status'])
            self.assertFalse(downloader.is_web_transfer_task_schedulable(task_id))
            self.assertEqual([f'discard:{task_id}:False'], submitted)

            self.assertTrue(downloader.resume_web_task(task_id))
            self.assertEqual(TransferStatus.PENDING, store.get_task(task_id)['status'])
            self.assertEqual([f'discard:{task_id}:False', task_id], submitted)

    def test_webui_task_pause_and_resume_api_use_operations(self):
        class TaskControlOperations:
            def __init__(self, store):
                self.store = store
                self.calls = []

            def pause_web_task(self, task_id):
                self.calls.append(('pause', task_id))
                self.store.update_task(task_id, status=TransferStatus.PAUSED)
                return True

            def resume_web_task(self, task_id):
                self.calls.append(('resume', task_id))
                self.store.update_task(task_id, status=TransferStatus.PENDING)
                return True

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source', 'https://t.me/pikpak_bot')
            operations = TaskControlOperations(store)
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request('POST', f'/api/tasks/{task_id}/pause', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(202, response.status)
                self.assertEqual('pause', body['action'])
                self.assertEqual(TransferStatus.PAUSED, store.get_task(task_id)['status'])

                conn.request('POST', f'/api/tasks/{task_id}/resume', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(202, response.status)
                self.assertEqual('resume', body['action'])
                self.assertEqual(TransferStatus.PENDING, store.get_task(task_id)['status'])
                self.assertEqual([('pause', task_id), ('resume', task_id)], operations.calls)
            finally:
                server.stop()

    def test_webui_exposes_live_transfer_watch_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request(
                    'POST',
                    '/api/watches',
                    body=json.dumps({'type': 'download', 'source_links': ['https://t.me/source']}),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(201, response.status)
                self.assertEqual('download', body['watches'][0]['type'])

                conn.request('GET', '/api/watches', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertEqual(1, len(body['watches']))

                watch_id = body['watches'][0]['id']
                conn.request('DELETE', f'/api/watches/{watch_id}', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['deleted'])
            finally:
                server.stop()

    def test_webui_rejects_conflicting_live_transfer_watch_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request(
                    'POST',
                    '/api/watches',
                    body=json.dumps({'type': 'download', 'source_links': ['https://t.me/source']}),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                response.read()
                self.assertEqual(201, response.status)

                conn.request(
                    'POST',
                    '/api/watches',
                    body=json.dumps({
                        'type': 'forward',
                        'source_link': 'https://t.me/source',
                        'target_link': 'https://t.me/target'
                    }),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(409, response.status)
                self.assertEqual('watch_source_conflict', body['error_code'])
            finally:
                server.stop()

    def test_webui_exposes_statistics_and_table_export_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request('GET', '/api/statistics', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['tables']['link']['available'])
                self.assertFalse(body['tables']['upload']['available'])

                conn.request(
                    'POST',
                    '/api/tables/export',
                    body=json.dumps({'table_type': 'link'}),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['exported'])
                self.assertEqual('link', body['table_type'])
                self.assertEqual(['link'], operations.exported_tables)
            finally:
                server.stop()

    def test_webui_exposes_upload_channel_download_and_forward_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            media_path = os.path.join(directory, 'media.bin')
            with open(media_path, 'wb') as file:
                file.write(b'12345')
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request(
                    'POST',
                    '/api/uploads',
                    body=json.dumps({
                        'path': media_path,
                        'target_link': 'https://t.me/target',
                        'recursive': False
                    }),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(202, response.status)
                self.assertTrue(body['accepted'])
                self.assertEqual(media_path, operations.created_uploads[0]['path'])

                conn.request(
                    'POST',
                    '/api/channel-downloads',
                    body=json.dumps({
                        'chat_link': 'https://t.me/source',
                        'download_type': ['video', 'photo'],
                        'keywords': ['demo'],
                        'include_comment': True
                    }),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(202, response.status)
                self.assertTrue(body['accepted'])
                self.assertEqual(['video', 'photo'], operations.created_channel_downloads[0]['download_type'])
            finally:
                server.stop()

    def test_webui_task_api_accepts_discussion_reply_inclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            server = WebUiServer(store=store, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request(
                    'POST',
                    '/api/tasks',
                    body=json.dumps({
                        'source_link': 'https://t.me/source',
                        'target_link': 'https://t.me/pikpak_bot',
                        'start_id': 1,
                        'end_id': 2,
                        'include_comment': True
                    }),
                    headers=headers
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(201, response.status)
                self.assertEqual(1, store.get_task(body['task_id'])['include_comment'])
            finally:
                server.stop()

    def test_webui_forward_watch_accepts_discussion_reply_inclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request(
                    'POST',
                    '/api/watches',
                    body=json.dumps({
                        'type': 'forward',
                        'source_link': 'https://t.me/source',
                        'target_link': 'https://t.me/target',
                        'include_comment': True
                    }),
                    headers=headers
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(201, response.status)
                self.assertTrue(body['watches'][0]['include_comment'])
                self.assertTrue(operations.watches['forward:https://t.me/source->https://t.me/target']['include_comment'])
            finally:
                server.stop()

    def test_webui_no_longer_exposes_separate_forward_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request(
                    'POST',
                    '/api/forwards',
                    body=json.dumps({
                        'source_link': 'https://t.me/source',
                        'target_link': 'https://t.me/target',
                        'start_id': 1,
                        'end_id': 3
                    }),
                    headers=headers
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(404, response.status)
                self.assertEqual('not_found', body['error_code'])
            finally:
                server.stop()

    def test_webui_transfer_tries_native_forward_before_restricted_fallback_download(self):
        from pyrogram.errors.exceptions.bad_request_400 import ChatForwardsRestricted

        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=2
            )
            messages = [
                SimpleNamespace(id=1, link='https://t.me/source/1'),
                SimpleNamespace(id=2, link='https://t.me/source/2')
            ]

            class FakeClient:
                def __init__(self, items):
                    self.items = {item.id: item for item in items}

                async def get_messages(self, chat_id, message_ids):
                    return self.items.get(message_ids)

            downloader.transfer_store = store
            downloader.uploader = object()
            downloader.app = SimpleNamespace(client=FakeClient(messages))
            downloader.gc = SimpleNamespace(download_upload=True, upload_delete=False)
            downloader.forward_calls = []
            downloader.download_calls = []

            async def fake_forward(**kwargs):
                downloader.forward_calls.append(kwargs)
                if kwargs['message_id'] == 2:
                    raise ChatForwardsRestricted()
                return SimpleNamespace(id=100)

            async def fake_create_download_task(**kwargs):
                downloader.download_calls.append(kwargs)
                return {'status': 'success'}

            downloader.forward = fake_forward
            downloader.create_download_task = fake_create_download_task
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

            async def fake_parse_link(client, link):
                if link == 'https://t.me/source':
                    return {'chat_id': 'source-chat'}
                if link == 'https://t.me/pikpak_bot':
                    return {'chat_id': 'target-chat'}
                return {'chat_id': 'unknown'}

            with patch('module.downloader.parse_link', side_effect=fake_parse_link):
                asyncio.run(downloader.process_web_transfer_task(task_id))

            self.assertEqual([1, 2], [call['message_id'] for call in downloader.forward_calls])
            self.assertTrue(all(call['ignore_type_filter'] for call in downloader.forward_calls))
            self.assertEqual(1, len(downloader.download_calls))
            fallback = downloader.download_calls[0]
            self.assertEqual('https://t.me/source/2?single', fallback['message_ids'])
            self.assertEqual('https://t.me/pikpak_bot', fallback['with_upload']['link'])
            self.assertTrue(fallback['with_upload']['with_delete'])
            self.assertFalse(fallback['with_upload']['send_as_media_group'])
            self.assertEqual('source', fallback['with_upload']['source_folder'])
            task = store.get_task(task_id)
            self.assertEqual(2, task['total_items'])

    def test_webui_transfer_includes_discussion_replies_when_enabled(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=1,
                include_comment=True
            )
            source_message = SimpleNamespace(id=1, link='https://t.me/source/1')
            reply_message = SimpleNamespace(
                id=10,
                link='https://t.me/discuss/10',
                chat=SimpleNamespace(id='discussion-chat'),
                video=SimpleNamespace(file_size=10, file_name='reply.mp4')
            )

            class FakeClient:
                async def get_messages(self, chat_id, message_ids):
                    return source_message if message_ids == 1 else None

                async def get_discussion_replies(self, chat_id, message_id):
                    if chat_id == 'source-chat' and message_id == 1:
                        yield reply_message

            downloader.transfer_store = store
            downloader.uploader = object()
            downloader.app = SimpleNamespace(client=FakeClient())
            downloader.gc = SimpleNamespace(
                download_upload=True,
                upload_delete=False,
                forward_type={'video': True, 'photo': False, 'text': False}
            )
            downloader.forward_calls = []

            async def fake_forward(**kwargs):
                downloader.forward_calls.append(kwargs)
                return SimpleNamespace(id=100 + kwargs['message_id'])

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

            async def fake_parse_link(client, link):
                if link == 'https://t.me/source':
                    return {'chat_id': 'source-chat'}
                if link == 'https://t.me/pikpak_bot':
                    return {'chat_id': 'target-chat'}
                return {'chat_id': 'unknown'}

            with patch('module.downloader.parse_link', side_effect=fake_parse_link), \
                    patch.object(downloader, 'wait_between_transfer_messages', new=AsyncMock()):
                asyncio.run(downloader.process_web_transfer_task(task_id))

            self.assertEqual([1, 10], [call['message_id'] for call in downloader.forward_calls])
            self.assertEqual('discussion-chat', downloader.forward_calls[1]['origin_chat_id'])
            task = store.get_task(task_id)
            self.assertEqual(2, task['total_items'])
            self.assertEqual(2, task['completed_items'])
            self.assertEqual(TransferStatus.SUCCESS, task['status'])

    def test_webui_discussion_reply_without_link_fallback_uses_message_object(self):
        from pyrogram.errors.exceptions.bad_request_400 import MediaCaptionTooLong

        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source/1',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                include_comment=True
            )
            reply_message = SimpleNamespace(
                id=10,
                link=None,
                chat=SimpleNamespace(id='discussion-chat'),
                video=SimpleNamespace(file_size=10, file_name='reply.mp4')
            )

            class FakeClient:
                async def get_discussion_replies(self, chat_id, message_id):
                    yield reply_message

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=FakeClient())
            downloader.gc = SimpleNamespace(
                download_upload=True,
                upload_delete=False,
                forward_type={'video': True}
            )
            downloader.download_calls = []

            async def fake_forward(**kwargs):
                raise MediaCaptionTooLong()

            async def fake_create_download_task(**kwargs):
                downloader.download_calls.append(kwargs)
                return {'status': 'downloading'}

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)
            downloader.create_download_task = fake_create_download_task

            reply_count, fallback_count = asyncio.run(downloader.transfer_web_discussion_replies_to_target(
                task=store.get_task(task_id),
                source_chat_id='source-chat',
                source_message_id=1,
                target_chat_id='target-chat',
                expected_total=1
            ))

            self.assertEqual(1, reply_count)
            self.assertEqual(1, fallback_count)
            self.assertIs(reply_message, downloader.download_calls[0]['message_ids'])

    def test_direct_forward_updates_task_progress_before_assignment_completes(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=2
            )
            store.refresh_task_counts(task_id, expected_total=2, assignment_completed=False)
            task = store.get_task(task_id)

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())
            downloader.forward_calls = []

            async def fake_forward(**kwargs):
                downloader.forward_calls.append(kwargs)
                return SimpleNamespace(id=100 + kwargs['message_id'])

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

            asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(id=1, link='https://t.me/source/1'),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1'
            ))

            task = store.get_task(task_id)
            self.assertEqual(2, task['total_items'])
            self.assertEqual(1, task['completed_items'])
            self.assertEqual(0, task['failed_items'])
            self.assertEqual(0, task['assignment_completed'])
            self.assertEqual(TransferStatus.RUNNING, task['status'])

    def test_direct_pikpak_forward_archive_failure_records_failure(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/ctuxas',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=1
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            task = store.get_task(task_id)
            archive_calls = []

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())
            downloader.gc = SimpleNamespace(
                config={
                    'target_profiles': {
                        'pikpak': {
                            'archive': {
                                'enable': True,
                                'remote': 'pikpak',
                                'root_directory': 'Telegram'
                            }
                        }
                    }
                }
            )

            async def fake_forward(**kwargs):
                return SimpleNamespace(id=100)

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(ok=False, status='not_found', message='not indexed yet')

            downloader.forward = fake_forward
            downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

            asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(
                    id=1,
                    link='https://t.me/ctuxas/1',
                    chat=SimpleNamespace(id=-100123, username='ctuxas'),
                    video=SimpleNamespace(file_size=5, file_name='video.mp4')
                ),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/ctuxas/1'
            ))

            self.assertEqual('ctuxas', archive_calls[0]['source_folder'])
            self.assertEqual('video.mp4', archive_calls[0]['file_name'])
            self.assertTrue(archive_calls[0]['match_original_name'])
            item = store.list_items(task_id)[0]
            self.assertEqual(TransferStatus.FAILURE, item['status'])
            self.assertEqual('failure', item['phase'])
            self.assertEqual('not_found', item['archive_status'])
            self.assertIn('PikPak archive not_found', item['error_message'])
            self.assertEqual(0, store.get_task(task_id)['completed_items'])
            events = store.list_events(task_id)
            self.assertTrue(any(event['level'] == 'warning' and 'PikPak archive' in event['message'] for event in events))

    def test_direct_pikpak_forward_archives_with_message_title_filename(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/chengdudiyi8/73962',
                'https://t.me/pikpak_bot',
                target_profile='pikpak'
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            task = store.get_task(task_id)
            archive_calls = []

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())

            async def fake_forward(**kwargs):
                return SimpleNamespace(id=100)

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(
                        ok=True,
                        status='success',
                        archive_path='Telegram/chengdudiyi8/73962 - 作者_ #海角社区 #示例标签.mp4'
                    )

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)
            downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()

            asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(
                    id=73962,
                    link='https://t.me/chengdudiyi8/73962',
                    caption='作者： #海角社区 #示例标签\n主题：【合集】 示例标题',
                    chat=SimpleNamespace(id='source-chat', username='chengdudiyi8'),
                    video=SimpleNamespace(
                        file_size=177200000,
                        file_name=None,
                        file_id='video-file-id',
                        mime_type='video/mp4'
                    )
                ),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/chengdudiyi8/73962'
            ))

            self.assertEqual(1, len(archive_calls))
            self.assertEqual('chengdudiyi8', archive_calls[0]['source_folder'])
            self.assertEqual(
                '73962 - 作者_ #海角社区 #示例标签.mp4',
                archive_calls[0]['file_name']
            )
            self.assertFalse(archive_calls[0]['match_original_name'])
            item = store.list_items(task_id)[0]
            self.assertEqual('73962 - 作者_ #海角社区 #示例标签.mp4', item['file_name'])
            self.assertEqual(TransferStatus.SUCCESS, item['status'])

    def test_direct_pikpak_forward_without_ingest_confirmation_records_failure(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=1
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            task = store.get_task(task_id)

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())
            downloader.forward_calls = []

            async def fake_forward(**kwargs):
                downloader.forward_calls.append(kwargs)
                return SimpleNamespace(id=100)

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=False)

            used_fallback = asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(id=1, link='https://t.me/source/1'),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1'
            ))

            self.assertFalse(used_fallback)
            items = store.list_items(task_id)
            self.assertEqual(1, len(items))
            self.assertEqual(TransferStatus.FAILURE, items[0]['status'])
            self.assertIn('PikPak ingest confirmation', items[0]['error_message'])
            self.assertEqual(0, store.get_task(task_id)['completed_items'])
            self.assertEqual(set(), store.completed_source_message_ids(task_id))

    def test_direct_pikpak_forward_without_target_message_records_failure(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=1
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            task = store.get_task(task_id)

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())

            async def fake_forward(**_kwargs):
                return None

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

            asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(
                    id=1,
                    link='https://t.me/source/1',
                    video=SimpleNamespace(file_size=5, file_name='video.mp4')
                ),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1'
            ))

            downloader.wait_for_pikpak_ingest_confirmation.assert_not_awaited()
            items = store.list_items(task_id)
            self.assertEqual(1, len(items))
            self.assertEqual(TransferStatus.FAILURE, items[0]['status'])
            self.assertIn('Direct forward did not produce a target message', items[0]['error_message'])
            self.assertEqual(0, store.get_task(task_id)['completed_items'])

    def test_webui_transfer_skips_empty_source_message_without_forwarding(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=74097,
                end_id=74097
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            task = store.get_task(task_id)

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())
            downloader.forward = AsyncMock(return_value=SimpleNamespace(id=100))
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

            used_fallback = asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(id=74097, empty=True),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/74097'
            ))

            self.assertFalse(used_fallback)
            downloader.forward.assert_not_awaited()
            downloader.wait_for_pikpak_ingest_confirmation.assert_not_awaited()
            items = store.list_items(task_id)
            self.assertEqual(1, len(items))
            self.assertEqual(TransferStatus.SKIPPED, items[0]['status'])
            self.assertEqual('skipped', items[0]['phase'])
            self.assertIn('Telegram API returned an empty source message', items[0]['error_message'])
            task = store.get_task(task_id)
            self.assertEqual(1, task['completed_items'])
            self.assertEqual(0, task['failed_items'])
            self.assertEqual({74097}, store.completed_source_message_ids(task_id))

    def test_direct_pikpak_forward_timeout_recovers_when_archive_finds_ingested_file(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/chengdudiyi8',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=73962,
                end_id=73962
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            task = store.get_task(task_id)
            archive_calls = []

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())

            async def fake_forward(**kwargs):
                return SimpleNamespace(id=100)

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(ok=True, status='success', archive_path='Telegram/chengdudiyi8/video.mp4')

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=False)
            downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()

            used_fallback = asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(
                    id=73962,
                    link='https://t.me/chengdudiyi8/73962',
                    chat=SimpleNamespace(id='source-chat', username='chengdudiyi8'),
                    video=SimpleNamespace(file_size=5, file_name='video.mp4')
                ),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/chengdudiyi8/73962'
            ))

            self.assertFalse(used_fallback)
            self.assertEqual(1, len(archive_calls))
            self.assertEqual('chengdudiyi8', archive_calls[0]['source_folder'])
            self.assertEqual('video.mp4', archive_calls[0]['file_name'])
            items = store.list_items(task_id)
            self.assertEqual(1, len(items))
            self.assertEqual(TransferStatus.SUCCESS, items[0]['status'])
            self.assertEqual('success', items[0]['archive_status'])
            self.assertEqual('', items[0]['error_message'])
            self.assertEqual(1, store.get_task(task_id)['completed_items'])
            self.assertEqual(0, store.get_task(task_id)['failed_items'])
            self.assertEqual({73962}, store.completed_source_message_ids(task_id))
            events = store.list_events(task_id)
            self.assertTrue(any('recovered by archive' in event['message'] for event in events))

    def test_webui_pikpak_confirmation_failure_continues_range_assignment(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=2
            )
            messages = [
                SimpleNamespace(id=1, link='https://t.me/source/1'),
                SimpleNamespace(id=2, link='https://t.me/source/2')
            ]

            class FakeClient:
                def __init__(self, items):
                    self.items = {item.id: item for item in items}

                async def get_messages(self, chat_id, message_ids):
                    return self.items.get(message_ids)

            downloader.transfer_store = store
            downloader.uploader = object()
            downloader.app = SimpleNamespace(client=FakeClient(messages))
            downloader.gc = SimpleNamespace(download_upload=True, upload_delete=False)
            downloader.forward_calls = []

            async def fake_forward(**kwargs):
                downloader.forward_calls.append(kwargs)
                return SimpleNamespace(id=100 + kwargs['message_id'])

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(side_effect=[False, True])

            async def fake_parse_link(client, link):
                if link == 'https://t.me/source':
                    return {'chat_id': 'source-chat'}
                if link == 'https://t.me/pikpak_bot':
                    return {'chat_id': 'target-chat'}
                return {'chat_id': 'unknown'}

            with patch('module.downloader.parse_link', side_effect=fake_parse_link), \
                    patch.object(downloader, 'wait_between_transfer_messages', new=AsyncMock()):
                asyncio.run(downloader.process_web_transfer_task(task_id))

            self.assertEqual([1, 2], [call['message_id'] for call in downloader.forward_calls])
            items = store.list_items(task_id)
            self.assertEqual(2, len(items))
            by_message_id = {item['source_message_id']: item for item in items}
            self.assertEqual(TransferStatus.FAILURE, by_message_id[1]['status'])
            self.assertEqual(TransferStatus.SUCCESS, by_message_id[2]['status'])
            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.FAILURE, task['status'])
            self.assertEqual(1, task['completed_items'])
            self.assertEqual(1, task['failed_items'])
            self.assertIsNone(task['error_message'])
            events = store.list_events(task_id)
            self.assertFalse(any('Transfer task failed' in event['message'] for event in events))

    def test_direct_pikpak_forward_with_ingest_confirmation_records_success(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=1
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            task = store.get_task(task_id)
            archive_calls = []

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())
            downloader.gc = SimpleNamespace(
                config={
                    'target_profiles': {
                        'pikpak': {
                            'archive': {
                                'enable': True,
                                'remote': 'pikpak',
                                'root_directory': 'Telegram'
                            }
                        }
                    }
                }
            )

            async def fake_forward(**_kwargs):
                return SimpleNamespace(id=100)

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(ok=True, status='success', archive_path='Telegram/source/video.mp4')

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)
            downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()

            asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(
                    id=1,
                    link='https://t.me/source/1',
                    chat=SimpleNamespace(id='source-chat'),
                    video=SimpleNamespace(file_size=5, file_name='video.mp4')
                ),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1'
            ))

            items = store.list_items(task_id)
            self.assertEqual(1, len(items))
            self.assertEqual(TransferStatus.SUCCESS, items[0]['status'])
            self.assertEqual(1, store.get_task(task_id)['completed_items'])
            self.assertEqual(1, len(archive_calls))

    def test_direct_non_pikpak_forward_does_not_wait_for_ingest_confirmation(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/target',
                target_profile='telegram',
                start_id=1,
                end_id=1
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            task = store.get_task(task_id)

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())

            async def fake_forward(**_kwargs):
                return SimpleNamespace(id=100)

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=False)

            asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(id=1, link='https://t.me/source/1'),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1'
            ))

            downloader.wait_for_pikpak_ingest_confirmation.assert_not_awaited()
            items = store.list_items(task_id)
            self.assertEqual(1, len(items))
            self.assertEqual(TransferStatus.SUCCESS, items[0]['status'])

    def test_pikpak_ingest_confirmation_ignores_success_before_forwarded_message(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        class FakeClient:
            def __init__(self):
                self.calls = 0

            async def get_chat_history(self, chat_id, limit):
                self.calls += 1
                messages = (
                    [SimpleNamespace(id=99, text='保存成功')]
                    if self.calls == 1
                    else [SimpleNamespace(id=101, text='保存成功')]
                )
                for message in messages:
                    yield message

        downloader.app = SimpleNamespace(client=FakeClient())

        async def run_case():
            with patch('module.downloader.asyncio.sleep', new=AsyncMock()):
                return await downloader.wait_for_pikpak_ingest_confirmation(
                    target_chat_id='target-chat',
                    forwarded_message=SimpleNamespace(id=100),
                    timeout_seconds=1,
                    poll_interval=0
                )

        self.assertTrue(asyncio.run(run_case()))
        self.assertEqual(2, downloader.app.client.calls)

    def test_pikpak_ingest_confirmation_requires_forwarded_message_identity(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        downloader.app = SimpleNamespace(client=object())

        self.assertFalse(asyncio.run(downloader.wait_for_pikpak_ingest_confirmation(
            target_chat_id='target-chat',
            forwarded_message=None,
            timeout_seconds=1,
            poll_interval=0
        )))

    def test_pikpak_ingest_confirmation_default_timeout_is_short(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        signature = inspect.signature(TelegramRestrictedMediaDownloader.wait_for_pikpak_ingest_confirmation)
        self.assertEqual(15, signature.parameters['timeout_seconds'].default)

    def test_direct_pikpak_forward_without_media_metadata_prepares_source_folder(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/ctuxas',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=1
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)
            task = store.get_task(task_id)
            archive_calls = []

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())
            folder_calls = []

            async def fake_forward(**kwargs):
                return SimpleNamespace(id=100)

            class FakeArchiveClient:
                def ensure_source_folder(self, source_folder):
                    folder_calls.append(source_folder)
                    return SimpleNamespace(ok=True, status='folder_ready', archive_path=f'Telegram/{source_folder}')

                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(ok=False, status='missing_metadata', message='metadata missing')

            downloader.forward = fake_forward
            downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

            asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(
                    id=1,
                    link='https://t.me/ctuxas/1',
                    chat=SimpleNamespace(id=-100123, username='ctuxas')
                ),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/ctuxas/1'
            ))

            self.assertEqual([], archive_calls)
            self.assertEqual(['ctuxas'], folder_calls)
            item = store.list_items(task_id)[0]
            self.assertEqual(TransferStatus.SUCCESS, item['status'])
            self.assertIsNone(item['archive_status'])
            events = store.list_events(task_id)
            self.assertFalse(any('PikPak archive missing_metadata' in event['message'] for event in events))

    def test_pikpak_upload_status_archives_without_transfer_store(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        archive_calls = []

        class FakeArchiveClient:
            def archive_file(self, **kwargs):
                archive_calls.append(kwargs)
                return SimpleNamespace(ok=True, status='success', archive_path='Telegram/ctuxas/video.mp4')

        downloader.transfer_store = None
        downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()

        upload_task = SimpleNamespace(
            status='sent',
            file_name='video.mp4',
            file_size=5,
            transfer_meta={
                'target_profile': 'pikpak',
                'source_link': 'https://t.me/ctuxas/1',
                'source_folder': 'ctuxas'
            }
        )

        downloader.on_transfer_upload_status(upload_task)

        self.assertEqual(1, len(archive_calls))
        self.assertEqual('ctuxas', archive_calls[0]['source_folder'])
        self.assertEqual('video.mp4', archive_calls[0]['file_name'])
        self.assertEqual(5, archive_calls[0]['file_size'])
        self.assertTrue(archive_calls[0]['match_original_name'])

    def test_pikpak_upload_archive_failure_records_transfer_failure(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/ctuxas/1',
                'https://t.me/pikpak_bot',
                target_profile='pikpak'
            )
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='source-chat',
                source_message_id=1,
                source_link='https://t.me/ctuxas/1',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='video.mp4',
                file_size=5,
                source_folder='ctuxas',
                archive_status='pending',
                archive_match_original_name=True,
                phase='uploading',
                status=TransferStatus.RUNNING
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=True)
            archive_calls = []

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(ok=False, status='not_found', message='not indexed yet')

            downloader.transfer_store = store
            downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()

            upload_task = SimpleNamespace(
                status='sent',
                file_name='video.mp4',
                file_size=5,
                transfer_meta={
                    'task_id': task_id,
                    'item_id': item_id,
                    'target_profile': 'pikpak',
                    'source_link': 'https://t.me/ctuxas/1',
                    'source_folder': 'ctuxas'
                }
            )

            downloader.on_transfer_upload_status(upload_task)

            self.assertEqual(1, len(archive_calls))
            self.assertTrue(archive_calls[0]['match_original_name'])
            item = store.list_items(task_id)[0]
            self.assertEqual(TransferStatus.FAILURE, item['status'])
            self.assertEqual('failure', item['phase'])
            self.assertEqual('not_found', item['archive_status'])
            self.assertIn('PikPak archive not_found', item['error_message'])
            task = store.get_task(task_id)
            self.assertEqual(0, task['completed_items'])
            self.assertEqual(1, task['failed_items'])

    def test_common_download_upload_meta_enables_pikpak_archive_callbacks_for_listen_forward(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        downloader.gc = SimpleNamespace(upload_delete=False)

        meta = downloader.build_download_upload_meta(
            target_link='https://t.me/pikpak_bot',
            source_link='https://t.me/ctuxas/1',
            source_folder='ctuxas'
        )

        self.assertEqual('pikpak', meta['target_profile'])
        self.assertEqual('ctuxas', meta['source_folder'])
        self.assertTrue(meta['with_delete'])
        self.assertFalse(meta['send_as_media_group'])
        self.assertIs(meta['status_callback'].__self__, downloader)
        self.assertIs(meta['status_callback'].__func__, downloader.on_transfer_upload_status.__func__)
        self.assertIs(meta['on_file_ready'].__self__, downloader)
        self.assertIs(meta['on_file_ready'].__func__, downloader.on_transfer_file_ready.__func__)

    def test_pikpak_transfer_over_target_limit_fails_before_forward_or_download(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source/1',
                'https://t.me/pikpak_bot',
                target_profile='pikpak'
            )
            task = store.get_task(task_id)
            message = SimpleNamespace(
                id=1,
                link='https://t.me/source/1',
                video=SimpleNamespace(file_size=4 * 1024 ** 3 + 1, file_name='large.mp4')
            )

            downloader.transfer_store = store
            downloader.app = SimpleNamespace(client=object())
            downloader.forward_calls = []
            downloader.download_calls = []
            downloader.gc = SimpleNamespace(download_upload=True)

            async def fake_forward(**kwargs):
                downloader.forward_calls.append(kwargs)

            async def fake_create_download_task(**kwargs):
                downloader.download_calls.append(kwargs)
                return {'status': 'success'}

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)
            downloader.create_download_task = fake_create_download_task

            used_fallback = asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=message,
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1'
            ))

            self.assertFalse(used_fallback)
            self.assertEqual([], downloader.forward_calls)
            self.assertEqual([], downloader.download_calls)
            items = store.list_items(task_id)
            self.assertEqual(1, len(items))
            self.assertEqual(TransferStatus.FAILURE, items[0]['status'])
            self.assertIn('PikPak', items[0]['error_message'])
            events = store.list_events(task_id)
            self.assertTrue(any('PikPak' in event['message'] for event in events))

    def test_webui_transfer_resumes_running_range_without_repeating_completed_items(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=2
            )
            store.add_item(
                task_id=task_id,
                source_chat_id='source-chat',
                source_message_id=1,
                source_link='https://t.me/source/1',
                target_link='https://t.me/pikpak_bot',
                media_type='forward',
                phase='forwarded',
                status=TransferStatus.SUCCESS
            )
            store.refresh_task_counts(task_id, expected_total=2, assignment_completed=False)
            store.update_task(task_id, status=TransferStatus.RUNNING)
            messages = [
                SimpleNamespace(id=1, link='https://t.me/source/1'),
                SimpleNamespace(id=2, link='https://t.me/source/2')
            ]

            class FakeClient:
                def __init__(self, items):
                    self.items = {item.id: item for item in items}

                async def get_messages(self, chat_id, message_ids):
                    return self.items.get(message_ids)

            downloader.transfer_store = store
            downloader.uploader = object()
            downloader.app = SimpleNamespace(client=FakeClient(messages))
            downloader.gc = SimpleNamespace(download_upload=True, upload_delete=False)
            downloader.forward_calls = []

            async def fake_forward(**kwargs):
                downloader.forward_calls.append(kwargs)
                return SimpleNamespace(id=100 + kwargs['message_id'])

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

            async def fake_parse_link(client, link):
                if link == 'https://t.me/source':
                    return {'chat_id': 'source-chat'}
                if link == 'https://t.me/pikpak_bot':
                    return {'chat_id': 'target-chat'}
                return {'chat_id': 'unknown'}

            with patch('module.downloader.parse_link', side_effect=fake_parse_link), \
                    patch.object(downloader, 'wait_between_transfer_messages', new=AsyncMock()):
                asyncio.run(downloader.process_web_transfer_task(task_id))

            self.assertEqual([2], [call['message_id'] for call in downloader.forward_calls])
            task = store.get_task(task_id)
            self.assertEqual(2, task['total_items'])
            self.assertEqual(2, task['completed_items'])
            self.assertEqual(TransferStatus.SUCCESS, task['status'])

    def test_webui_transfer_skips_missing_range_messages_and_continues(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=3
            )
            messages = [
                SimpleNamespace(id=1, link='https://t.me/source/1'),
                SimpleNamespace(id=3, link='https://t.me/source/3')
            ]

            class FakeClient:
                def __init__(self, items):
                    self.items = {item.id: item for item in items}

                async def get_messages(self, chat_id, message_ids):
                    return self.items.get(message_ids)

            downloader.transfer_store = store
            downloader.uploader = object()
            downloader.app = SimpleNamespace(client=FakeClient(messages))
            downloader.gc = SimpleNamespace(download_upload=True, upload_delete=False)
            downloader.forward_calls = []

            async def fake_forward(**kwargs):
                downloader.forward_calls.append(kwargs)
                return SimpleNamespace(id=100 + kwargs['message_id'])

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)

            async def fake_parse_link(client, link):
                if link == 'https://t.me/source':
                    return {'chat_id': 'source-chat'}
                if link == 'https://t.me/pikpak_bot':
                    return {'chat_id': 'target-chat'}
                return {'chat_id': 'unknown'}

            with patch('module.downloader.parse_link', side_effect=fake_parse_link), \
                    patch.object(downloader, 'wait_between_transfer_messages', new=AsyncMock()):
                asyncio.run(downloader.process_web_transfer_task(task_id))

            self.assertEqual([1, 3], [call['message_id'] for call in downloader.forward_calls])
            items = store.list_items(task_id)
            skipped = [item for item in items if item['source_message_id'] == 2]
            self.assertEqual(1, len(skipped))
            self.assertEqual(TransferStatus.SKIPPED, skipped[0]['status'])
            self.assertIn('not found', skipped[0]['error_message'])
            events = store.list_events(task_id)
            self.assertTrue(any(event['level'] == 'warning' and '2' in event['message'] for event in events))
            task = store.get_task(task_id)
            self.assertEqual(3, task['total_items'])
            self.assertEqual(3, task['completed_items'])
            self.assertEqual(TransferStatus.SUCCESS, task['status'])

    def test_downloader_detects_transfer_range_from_accessible_chat_history(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        class FakeClient:
            def __init__(self):
                self.pages = [
                    [SimpleNamespace(id=99)],
                    [SimpleNamespace(id=3)],
                    []
                ]
                self.calls = []

            async def get_chat_history(self, chat_id, limit=0, offset_id=0, **_kwargs):
                self.calls.append({'chat_id': chat_id, 'limit': limit, 'offset_id': offset_id})
                page = self.pages.pop(0)
                for message in page:
                    yield message

        client = FakeClient()
        downloader.app = SimpleNamespace(client=client)

        async def fake_parse_link(client, link):
            return {'chat_id': 'source-chat'}

        with patch('module.downloader.parse_link', side_effect=fake_parse_link):
            detected = asyncio.run(downloader.detect_transfer_range_async('https://t.me/source'))

        self.assertEqual({'start_id': 3, 'end_id': 99}, detected)
        self.assertEqual(
            [
                {'chat_id': 'source-chat', 'limit': 100, 'offset_id': 0},
                {'chat_id': 'source-chat', 'limit': 100, 'offset_id': 99},
                {'chat_id': 'source-chat', 'limit': 100, 'offset_id': 3}
            ],
            client.calls
        )

    def test_downloader_detects_transfer_range_uses_count_offset_fast_path(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        class FakeClient:
            def __init__(self):
                self.calls = []
                self.count_calls = []

            async def get_chat_history_count(self, chat_id):
                self.count_calls.append(chat_id)
                return 5000

            async def get_chat_history(self, chat_id, limit=0, offset=0, offset_id=0, **_kwargs):
                self.calls.append({
                    'chat_id': chat_id,
                    'limit': limit,
                    'offset': offset,
                    'offset_id': offset_id
                })
                if offset == 0:
                    yield SimpleNamespace(id=9999)
                    return
                if offset == 4999:
                    yield SimpleNamespace(id=42)
                    return
                raise AssertionError(f'unexpected history offset: {offset}')

        client = FakeClient()
        downloader.app = SimpleNamespace(client=client)

        async def fake_parse_link(client, link):
            return {'chat_id': 'source-chat'}

        with patch('module.downloader.parse_link', side_effect=fake_parse_link):
            detected = asyncio.run(downloader.detect_transfer_range_async('https://t.me/source'))

        self.assertEqual({'start_id': 42, 'end_id': 9999}, detected)
        self.assertEqual(['source-chat'], client.count_calls)
        self.assertEqual(
            [
                {'chat_id': 'source-chat', 'limit': 1, 'offset': 0, 'offset_id': 0},
                {'chat_id': 'source-chat', 'limit': 1, 'offset': 4999, 'offset_id': 0}
            ],
            client.calls
        )

    def test_downloader_detects_transfer_range_falls_back_when_fast_count_fails(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        class FakeClient:
            def __init__(self):
                self.pages = [
                    [SimpleNamespace(id=99)],
                    [SimpleNamespace(id=3)],
                    []
                ]
                self.calls = []
                self.count_calls = []

            async def get_chat_history_count(self, chat_id):
                self.count_calls.append(chat_id)
                raise RuntimeError('count unavailable')

            async def get_chat_history(self, chat_id, limit=0, offset=0, offset_id=0, **_kwargs):
                self.calls.append({
                    'chat_id': chat_id,
                    'limit': limit,
                    'offset': offset,
                    'offset_id': offset_id
                })
                if offset == 0 and offset_id == 0 and limit == 1:
                    yield SimpleNamespace(id=99)
                    return
                page = self.pages.pop(0)
                for message in page:
                    yield message

        client = FakeClient()
        downloader.app = SimpleNamespace(client=client)

        async def fake_parse_link(client, link):
            return {'chat_id': 'source-chat'}

        with patch('module.downloader.parse_link', side_effect=fake_parse_link):
            detected = asyncio.run(downloader.detect_transfer_range_async('https://t.me/source'))

        self.assertEqual({'start_id': 3, 'end_id': 99}, detected)
        self.assertEqual(['source-chat'], client.count_calls)
        self.assertEqual(
            [
                {'chat_id': 'source-chat', 'limit': 1, 'offset': 0, 'offset_id': 0},
                {'chat_id': 'source-chat', 'limit': 100, 'offset': 0, 'offset_id': 0},
                {'chat_id': 'source-chat', 'limit': 100, 'offset': 0, 'offset_id': 99},
                {'chat_id': 'source-chat', 'limit': 100, 'offset': 0, 'offset_id': 3}
            ],
            client.calls
        )

    def test_downloader_detects_transfer_range_falls_back_when_fast_tail_matches_newest(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        class FakeClient:
            def __init__(self):
                self.pages = [
                    [SimpleNamespace(id=99)],
                    [SimpleNamespace(id=3)],
                    []
                ]
                self.calls = []

            async def get_chat_history_count(self, _chat_id):
                return 5000

            async def get_chat_history(self, chat_id, limit=0, offset=0, offset_id=0, **_kwargs):
                self.calls.append({
                    'chat_id': chat_id,
                    'limit': limit,
                    'offset': offset,
                    'offset_id': offset_id
                })
                if offset == 0 and offset_id == 0 and limit == 1:
                    yield SimpleNamespace(id=99)
                    return
                if offset == 4999 and limit == 1:
                    yield SimpleNamespace(id=99)
                    return
                page = self.pages.pop(0)
                for message in page:
                    yield message

        client = FakeClient()
        downloader.app = SimpleNamespace(client=client)

        async def fake_parse_link(client, link):
            return {'chat_id': 'source-chat'}

        with patch('module.downloader.parse_link', side_effect=fake_parse_link):
            detected = asyncio.run(downloader.detect_transfer_range_async('https://t.me/source'))

        self.assertEqual({'start_id': 3, 'end_id': 99}, detected)
        self.assertEqual(
            [
                {'chat_id': 'source-chat', 'limit': 1, 'offset': 0, 'offset_id': 0},
                {'chat_id': 'source-chat', 'limit': 1, 'offset': 4999, 'offset_id': 0},
                {'chat_id': 'source-chat', 'limit': 100, 'offset': 0, 'offset_id': 0},
                {'chat_id': 'source-chat', 'limit': 100, 'offset': 0, 'offset_id': 99},
                {'chat_id': 'source-chat', 'limit': 100, 'offset': 0, 'offset_id': 3}
            ],
            client.calls
        )

    def test_downloader_detects_transfer_range_start_from_actual_history_tail(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        class FakeClient:
            def __init__(self):
                self.pages = [
                    [SimpleNamespace(id=99), SimpleNamespace(id=98)],
                    [SimpleNamespace(id=51), SimpleNamespace(id=50)],
                    []
                ]
                self.calls = []

            async def get_chat_history(self, chat_id, limit=0, offset_id=0, **_kwargs):
                self.calls.append({'chat_id': chat_id, 'limit': limit, 'offset_id': offset_id})
                page = self.pages.pop(0)
                for message in page:
                    yield message

        client = FakeClient()
        downloader.app = SimpleNamespace(client=client)

        async def fake_parse_link(client, link):
            return {'chat_id': 'source-chat'}

        with patch('module.downloader.parse_link', side_effect=fake_parse_link):
            detected = asyncio.run(downloader.detect_transfer_range_async('https://t.me/source'))

        self.assertEqual({'start_id': 50, 'end_id': 99}, detected)
        self.assertEqual(
            [
                {'chat_id': 'source-chat', 'limit': 100, 'offset_id': 0},
                {'chat_id': 'source-chat', 'limit': 100, 'offset_id': 98},
                {'chat_id': 'source-chat', 'limit': 100, 'offset_id': 50}
            ],
            client.calls
        )

    def test_forward_waits_and_retries_copy_message_flood_wait(self):
        from pyrogram.errors import FloodWait

        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        copy_attempts = []

        class FakeClient:
            name = 'test-client'

            async def copy_message(self, **kwargs):
                copy_attempts.append(kwargs)
                if len(copy_attempts) == 1:
                    raise FloodWait(9)
                return SimpleNamespace(id=100)

        downloader.app = SimpleNamespace(client=FakeClient())
        downloader.transfer_store = None

        async def run_case():
            with patch('module.downloader.asyncio.sleep') as sleep_mock, \
                    patch('module.downloader.random.uniform', return_value=0):
                await downloader.forward(
                    client=downloader.app.client,
                    message=SimpleNamespace(id=1),
                    message_id=1,
                    origin_chat_id='source-chat',
                    target_chat_id='target-chat',
                    target_link='https://t.me/pikpak_bot',
                    done_notice=False,
                    ignore_type_filter=True
                )
                sleep_mock.assert_awaited_once_with(9)

        asyncio.run(run_case())

        self.assertEqual(2, len(copy_attempts))

    def test_forward_uses_forward_messages_when_copy_returns_empty_result(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        class FakeClient:
            name = 'test-client'

            def __init__(self):
                self.copy_calls = []
                self.forward_calls = []

            async def copy_message(self, **kwargs):
                self.copy_calls.append(kwargs)
                return None

            async def forward_messages(self, **kwargs):
                self.forward_calls.append(kwargs)
                return SimpleNamespace(id=101)

        client = FakeClient()
        downloader.app = SimpleNamespace(client=client)
        downloader.transfer_store = None

        result = asyncio.run(downloader.forward(
            client=client,
            message=SimpleNamespace(id=1, link='https://t.me/source/1'),
            message_id=1,
            origin_chat_id='source-chat',
            target_chat_id='target-chat',
            target_link='https://t.me/pikpak_bot',
            done_notice=False,
            ignore_type_filter=True
        ))

        self.assertEqual(101, result.id)
        self.assertEqual(1, len(client.copy_calls))
        self.assertEqual(1, len(client.forward_calls))
        self.assertEqual('target-chat', client.forward_calls[0]['chat_id'])
        self.assertEqual('source-chat', client.forward_calls[0]['from_chat_id'])
        self.assertEqual(1, client.forward_calls[0]['message_ids'])

    def test_forward_logs_pikpak_archive_failure_without_transfer_store(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        class FakeClient:
            async def copy_message(self, **_kwargs):
                return SimpleNamespace(id=100)

        class FakeArchiveClient:
            def archive_file(self, **_kwargs):
                return SimpleNamespace(ok=False, status='not_found', message='not indexed yet')

        downloader.app = SimpleNamespace(client=FakeClient())
        downloader.transfer_store = None
        downloader.get_pikpak_archive_client = lambda: FakeArchiveClient()

        with self.assertLogs('rich', level='WARNING') as logs:
            result = asyncio.run(downloader.forward(
                client=downloader.app.client,
                message=SimpleNamespace(
                    id=1,
                    link='https://t.me/source/1',
                    chat=SimpleNamespace(id='source-chat'),
                    video=SimpleNamespace(file_size=5, file_name='video.mp4')
                ),
                message_id=1,
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                target_link='https://t.me/pikpak_bot',
                done_notice=False,
                ignore_type_filter=True
            ))

        self.assertEqual(100, result.id)
        self.assertTrue(any('PikPak archive not_found' in message for message in logs.output))

    def test_webui_start_requeues_running_tasks_after_container_restart(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        downloader.app = SimpleNamespace(temp_directory='tmp', save_directory='downloads')
        submitted_task_ids = []
        downloader.submit_web_task = lambda task_id: submitted_task_ids.append(task_id)
        fake_store = SimpleNamespace(
            list_tasks=lambda: [
                {'id': 1, 'status': TransferStatus.SUCCESS},
                {'id': 2, 'status': TransferStatus.RUNNING},
                {'id': 3, 'status': TransferStatus.PENDING},
                {'id': 4, 'status': TransferStatus.FAILURE}
            ]
        )
        fake_web_ui = SimpleNamespace(
            start=lambda open_browser: None,
            url='http://127.0.0.1:8080'
        )

        with patch('module.downloader.PARSE_ARGS', SimpleNamespace(web=8080)), \
                patch('module.downloader.TransferStore', return_value=fake_store), \
                patch('module.downloader.WebUiServer', return_value=fake_web_ui):
            downloader.start_web_ui()

        self.assertEqual([2, 3, 4], submitted_task_ids)

    def test_webui_delete_task_uses_operations_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            operations = TaskDeletingOperations(store)
            server = WebUiServer(store=store, operations=operations)
            server.start(open_browser=False)
            try:
                conn = http.client.HTTPConnection(server.host, server.port)
                conn.request('DELETE', f'/api/tasks/{task_id}')
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['deleted'])
                self.assertEqual([task_id], operations.deleted_task_ids)
                self.assertIsNone(store.get_task(task_id))
            finally:
                server.stop()

    def test_deleting_running_web_task_cancels_and_schedules_next_task(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()

        async def run_case():
            downloader = object.__new__(TelegramRestrictedMediaDownloader)
            downloader.loop = asyncio.get_running_loop()
            downloader.web_task_queue = asyncio.Queue()
            downloader.web_submitted_task_ids = set()
            downloader.web_operation_queue = asyncio.Queue()
            downloader.web_running_task = None
            downloader.web_running_task_id = None
            started_task_ids = []
            cancelled_task_ids = []

            with tempfile.TemporaryDirectory() as directory:
                store = TransferStore(directory=directory)
                running_task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
                next_task_id = store.create_task('https://t.me/source/2', 'https://t.me/pikpak_bot')
                downloader.transfer_store = store

                async def fake_process_web_transfer_task(task_id):
                    started_task_ids.append(task_id)
                    try:
                        await asyncio.sleep(60)
                    except asyncio.CancelledError:
                        cancelled_task_ids.append(task_id)
                        raise

                downloader.process_web_transfer_task = fake_process_web_transfer_task
                downloader.submit_web_task(running_task_id)
                await asyncio.wait_for(downloader.process_web_task_queue(), timeout=0.2)
                await asyncio.sleep(0)

                self.assertEqual([running_task_id], started_task_ids)
                self.assertEqual(running_task_id, downloader.web_running_task_id)
                self.assertIn(running_task_id, downloader.web_submitted_task_ids)

                self.assertTrue(downloader.delete_web_task(running_task_id))
                downloader.submit_web_task(next_task_id)
                for _ in range(10):
                    await asyncio.sleep(0)
                    await downloader.process_web_task_queue()
                    if started_task_ids[-1] == next_task_id:
                        break

                self.assertEqual([running_task_id, next_task_id], started_task_ids)
                self.assertEqual([running_task_id], cancelled_task_ids)
                self.assertNotIn(running_task_id, downloader.web_submitted_task_ids)
                self.assertEqual(next_task_id, downloader.web_running_task_id)

                if downloader.web_running_task:
                    downloader.web_running_task.cancel()
                    await asyncio.gather(downloader.web_running_task, return_exceptions=True)

        asyncio.run(run_case())

    def test_webui_transfer_falls_back_when_direct_copy_caption_is_too_long(self):
        from pyrogram.errors.exceptions.bad_request_400 import MediaCaptionTooLong

        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source/1',
                'https://t.me/pikpak_bot',
                target_profile='pikpak'
            )
            message = SimpleNamespace(id=1, link='https://t.me/source/1', caption='x' * 5000)

            downloader.transfer_store = store
            downloader.uploader = object()
            downloader.app = SimpleNamespace(client=object())
            downloader.gc = SimpleNamespace(download_upload=True, upload_delete=False)
            downloader.forward_calls = []
            downloader.download_calls = []

            async def fake_forward(**kwargs):
                downloader.forward_calls.append(kwargs)
                raise MediaCaptionTooLong()

            async def fake_create_download_task(**kwargs):
                downloader.download_calls.append(kwargs)
                return {'status': 'success'}

            downloader.forward = fake_forward
            downloader.create_download_task = fake_create_download_task

            used_fallback = asyncio.run(downloader.transfer_message_to_web_target(
                task=store.get_task(task_id),
                message=message,
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/source/1'
            ))

            self.assertTrue(used_fallback)
            self.assertEqual(1, len(downloader.forward_calls))
            self.assertEqual(1, len(downloader.download_calls))
            fallback = downloader.download_calls[0]
            self.assertEqual('https://t.me/source/1?single', fallback['message_ids'])
            self.assertEqual('https://t.me/pikpak_bot', fallback['with_upload']['link'])
            self.assertTrue(fallback['with_upload']['with_delete'])
            self.assertFalse(fallback['with_upload']['send_as_media_group'])
            events = store.list_events(task_id)
            self.assertFalse(any('Transfer task failed' in event['message'] for event in events))

    def test_bot_forward_and_listen_forward_parse_discussion_reply_flag(self):
        Bot = import_with_clean_argv(
            lambda: __import__('module.bot', fromlist=['Bot'])
        ).Bot

        bot = object.__new__(Bot)
        bot.listen_download_chat = {}
        bot.listen_forward_chat = {}
        bot.check_download_range = AsyncMock(return_value=True)

        class FakeClient:
            async def send_message(self, *args, **kwargs):
                return SimpleNamespace(id=1, text=kwargs.get('text', ''))

        client = FakeClient()
        message = SimpleNamespace(
            id=1,
            text='/forward https://t.me/source https://t.me/target 1 2 --include-comment',
            from_user=SimpleNamespace(id=123)
        )

        forward_meta = asyncio.run(Bot.get_forward_link_from_bot(bot, client, message))
        self.assertTrue(forward_meta['include_comment'])

        message.text = '/listen_forward https://t.me/source https://t.me/target --include-comment'
        listen_meta = asyncio.run(Bot.on_listen(bot, client, message))
        self.assertTrue(listen_meta['include_comment'])
        self.assertEqual(['https://t.me/source', 'https://t.me/target'], listen_meta['links'])

    def test_listen_forward_includes_discussion_replies_when_enabled(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        class FakeMessage:
            id = 5
            link = 'https://t.me/source/5'
            video = SimpleNamespace(file_size=10, file_name='source.mp4')
            chat = SimpleNamespace(id='source-chat')

            async def get_media_group(self):
                raise ValueError

        reply_message = SimpleNamespace(
            id=15,
            link='https://t.me/discuss/15',
            chat=SimpleNamespace(id='discussion-chat'),
            video=SimpleNamespace(file_size=10, file_name='reply.mp4')
        )

        class FakeClient:
            async def get_discussion_replies(self, chat_id, message_id):
                if chat_id == 'source-chat' and message_id == 5:
                    yield reply_message

        downloader.app = SimpleNamespace(client=FakeClient())
        downloader.gc = SimpleNamespace(forward_type={'video': True, 'photo': False, 'text': False})
        downloader.listen_forward_chat = {
            'https://t.me/source https://t.me/target --include-comment': object()
        }
        downloader.handle_media_groups = {}
        downloader.forward_calls = []

        async def fake_forward(**kwargs):
            downloader.forward_calls.append(kwargs)

        downloader.forward = fake_forward

        async def fake_parse_link(client, link):
            if link in ('https://t.me/source', 'https://t.me/source/5'):
                return {'chat_id': 'source-chat'}
            if link == 'https://t.me/target':
                return {'chat_id': 'target-chat'}
            return {'chat_id': 'unknown'}

        with patch('module.downloader.parse_link', side_effect=fake_parse_link):
            asyncio.run(downloader.listen_forward(object(), FakeMessage()))

        self.assertEqual([5, 15], [call['message_id'] for call in downloader.forward_calls])
        self.assertEqual('discussion-chat', downloader.forward_calls[1]['origin_chat_id'])

    def test_webui_accepts_non_recursive_directory_upload_for_upload_command_parity(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, 'media.bin'), 'wb') as file:
                file.write(b'12345')
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request(
                    'POST',
                    '/api/uploads',
                    body=json.dumps({
                        'path': directory,
                        'target_link': 'https://t.me/target',
                        'recursive': False
                    }),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(202, response.status)
                self.assertTrue(body['accepted'])
                self.assertEqual(os.path.abspath(directory), operations.created_uploads[0]['path'])
                self.assertFalse(operations.created_uploads[0]['recursive'])
            finally:
                server.stop()

    def test_webui_rejects_invalid_upload_path_with_stable_error_code(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            auth = base64.b64encode(b'admin:pass').decode('ascii')
            headers = {'Authorization': f'Basic {auth}'}
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request(
                    'POST',
                    '/api/uploads',
                    body=json.dumps({
                        'path': os.path.join(directory, 'missing.bin'),
                        'target_link': 'https://t.me/target',
                        'recursive': False
                    }),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(400, response.status)
                self.assertEqual('upload_path_not_found', body['error_code'])
            finally:
                server.stop()

    def test_webui_live_watch_delete_uses_client_that_registered_handler(self):
        import pyrogram

        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        user_client = FakeTelegramClient()
        app_client = FakeTelegramClient()
        pyrogram.filters.chat = lambda _chat_id: object()
        downloader.user = user_client
        downloader.app = SimpleNamespace(client=app_client)
        downloader.listen_download_chat = {}
        downloader.listen_forward_chat = {}
        downloader.web_pending_watches = {
            'download:https://t.me/source': {
                'id': 'download:https://t.me/source',
                'type': 'download',
                'source_link': 'https://t.me/source',
                'status': TransferStatus.PENDING
            }
        }
        downloader.web_watch_handler_clients = {}

        async def exercise_watch_lifecycle():
            await downloader.apply_web_watch({
                'watch_type': 'download',
                'source_link': 'https://t.me/source'
            })
            return downloader.delete_watch('download:https://t.me/source')

        deleted = __import__('asyncio').run(exercise_watch_lifecycle())
        self.assertTrue(deleted)
        self.assertEqual(1, len(user_client.added_handlers))
        self.assertEqual(user_client.added_handlers, user_client.removed_handlers)
        self.assertEqual([], app_client.removed_handlers)

    def test_webui_live_watch_persists_and_restores_after_restart(self):
        import asyncio
        import pyrogram

        TelegramRestrictedMediaDownloader = import_downloader_class()

        def build_downloader(store):
            downloader = object.__new__(TelegramRestrictedMediaDownloader)
            loop = asyncio.new_event_loop()
            downloader.loop = loop
            downloader.web_operation_queue = asyncio.Queue()
            downloader.web_operation_counter = 0
            downloader.web_operations = {}
            downloader.web_pending_watches = {}
            downloader.listen_download_chat = {}
            downloader.listen_forward_chat = {}
            downloader.web_watch_handler_clients = {}
            downloader.transfer_store = store
            downloader.user = FakeTelegramClient()
            downloader.app = SimpleNamespace(client=FakeTelegramClient())
            return downloader, loop

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            original, original_loop = build_downloader(store)
            restored, restored_loop = build_downloader(store)
            pyrogram.filters.chat = lambda _chat_id: object()
            try:
                original.create_watch({
                    'type': 'download',
                    'source_links': ['https://t.me/source']
                })

                self.assertEqual(
                    ['download:https://t.me/source'],
                    [watch['id'] for watch in restored.list_watches()]
                )

                asyncio.run(restored.restore_live_transfer_watches())

                self.assertEqual(1, len(restored.user.added_handlers))
                self.assertIn('https://t.me/source', restored.listen_download_chat)
                self.assertEqual(TransferStatus.RUNNING, restored.list_watches()[0]['status'])

                self.assertTrue(restored.delete_watch('download:https://t.me/source'))
                self.assertEqual([], restored.list_watches())
                self.assertEqual([], store.list_live_transfer_watches())
                self.assertEqual(restored.user.added_handlers, restored.user.removed_handlers)
            finally:
                original_loop.close()
                restored_loop.close()

    def test_webui_live_watch_delete_defaults_to_user_client_for_existing_bot_watches(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        user_client = FakeTelegramClient()
        app_client = FakeTelegramClient()
        handler = object()
        downloader.user = user_client
        downloader.app = SimpleNamespace(client=app_client)
        downloader.listen_download_chat = {'https://t.me/source': handler}
        downloader.listen_forward_chat = {}
        downloader.web_pending_watches = {}
        downloader.web_watch_handler_clients = {}

        deleted = downloader.delete_watch('download:https://t.me/source')

        self.assertTrue(deleted)
        self.assertEqual([handler], user_client.removed_handlers)
        self.assertEqual([], app_client.removed_handlers)

    def test_webui_live_watch_pending_sources_still_conflict(self):
        import asyncio

        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        loop = asyncio.new_event_loop()
        try:
            downloader.loop = loop
            downloader.web_operation_queue = asyncio.Queue()
            downloader.web_operation_counter = 0
            downloader.web_operations = {}
            downloader.web_pending_watches = {}
            downloader.listen_download_chat = {}
            downloader.listen_forward_chat = {}

            downloader.create_watch({
                'type': 'download',
                'source_links': ['https://t.me/source']
            })

            with self.assertRaisesRegex(ValueError, 'watch_source_conflict'):
                downloader.create_watch({
                    'type': 'forward',
                    'source_link': 'https://t.me/source',
                    'target_link': 'https://t.me/target'
                })
        finally:
            loop.close()


if __name__ == '__main__':
    unittest.main()
