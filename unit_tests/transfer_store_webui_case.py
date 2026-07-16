# coding=UTF-8
import asyncio
import datetime
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
from urllib.parse import quote

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

import module as trmd_module
from module.core.media_types import MEDIA_TYPES_DEFAULT, build_runtime_message_filter
from module.live_watch_manager import LiveWatchManager
from module.pikpak_integration import PikpakIntegrationManager
from module.transfer_store import ExecutionMode, TransferStatus, TransferStore
from module.webui_view_model import WebUiViewModel
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

    def list_watches(self, tz_offset_minutes=None):
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
            for existing in self.watches.values():
                if (
                    existing.get('type') == 'forward'
                    and existing.get('source_link') == source_link
                    and existing.get('target_link') == target_link
                ):
                    raise ValueError('watch_already_exists')
            watch_id = f'forward:{source_link}->{target_link}'
            self.watches[watch_id] = {
                'id': watch_id,
                'type': 'forward',
                'source_link': source_link,
                'target_link': target_link,
                'include_comment': bool(payload.get('include_comment')),
                'resolve_deep_link': bool(payload.get('resolve_deep_link')),
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

    def statistics(self, tz_offset_minutes=None):
        return {
            'tables': {
                'channel': {'available': True, 'rows': 2},
            },
            'summary': {
                'channels': 2,
                'downloads_total': 10,
                'success_rate': 80.0,
                'failure_count': 1,
                'skip_count': 1,
                'issue_count': 2,
                'window_days': 7,
            },
            'channels': [],
            'chart_by_channel': [],
        }

    def export_table(self, table_type):
        self.exported_tables.append(table_type)
        return {'exported': True, 'table_type': table_type, 'directory': 'form'}

    def export_forward_watches(self):
        from module.transfer.forward_watch_backup import build_forward_watch_export_payload

        watches = [
            {
                'source_link': watch['source_link'],
                'target_link': watch['target_link'],
                'include_comment': bool(watch.get('include_comment')),
                'resolve_deep_link': bool(watch.get('resolve_deep_link')),
            }
            for watch in self.watches.values()
            if watch.get('type') == 'forward'
        ]
        return build_forward_watch_export_payload(watches)

    def import_forward_watches(self, payload):
        from module.transfer.forward_watch_backup import (
            import_forward_watch_entries,
            parse_forward_watch_import_payload,
        )

        entries, parse_errors = parse_forward_watch_import_payload(payload)
        fatal_codes = {
            'invalid_payload',
            'invalid_kind',
            'unsupported_version',
            'missing_watches',
            'invalid_watches',
        }
        for code in parse_errors:
            if code in fatal_codes:
                raise ValueError(code)
        return import_forward_watch_entries(entries, self.create_watch, parse_errors=parse_errors)

    def delete_web_task(self, task_id: int) -> bool:
        return True

    def pause_web_task(self, task_id: int) -> bool:
        return True

    def resume_web_task(self, task_id: int) -> bool:
        return True

    def retry_failed_web_task(self, task_id: int) -> int:
        return 0

    def submit_web_task(self, task_id: int) -> None:
        pass


class TaskDeletingOperations:
    def __init__(self, store):
        self.store = store
        self.deleted_task_ids = []

    def delete_web_task(self, task_id):
        self.deleted_task_ids.append(task_id)
        return self.store.delete_task(task_id)

    def list_watches(self, tz_offset_minutes=None) -> list:
        return []

    def create_watch(self, payload: dict) -> dict:
        return {}

    def delete_watch(self, watch_id: str) -> bool:
        return True

    def pause_web_task(self, task_id: int) -> bool:
        return True

    def resume_web_task(self, task_id: int) -> bool:
        return True

    def retry_failed_web_task(self, task_id: int) -> int:
        return 0

    def submit_web_task(self, task_id: int) -> None:
        pass

    def statistics(self) -> dict:
        return {}

    def export_table(self, table_type: str) -> dict:
        return {}

    def create_upload(self, payload: dict) -> dict:
        return {}

    def create_channel_download(self, payload: dict) -> dict:
        return {}

    def detect_transfer_range(self, source_link: str):
        return None


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
    def _login_headers(self, conn, content_type: str | None = None) -> dict:
        conn.request(
            'POST',
            '/api/auth/login',
            body=json.dumps({
                'username': 'admin',
                'password': 'pass',
                'remember_me': True
            }),
            headers={'Content-Type': 'application/json'}
        )
        response = conn.getresponse()
        body = json.loads(response.read().decode('utf-8'))
        self.assertEqual(200, response.status)
        self.assertTrue(body['success'])
        cookie = response.getheader('Set-Cookie')
        self.assertIsNotNone(cookie)
        headers = {'Cookie': cookie.split(';', 1)[0]}
        if content_type:
            headers['Content-Type'] = content_type
        return headers

    def _authenticated_headers(self, server, content_type: str | None = None) -> dict:
        conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
        try:
            return self._login_headers(conn, content_type=content_type)
        finally:
            conn.close()

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

    def test_start_periodic_log_cleanup_starts_only_once(self):
        trmd_module._log_cleanup_thread_started = False
        with patch.object(trmd_module.threading, 'Thread') as mock_thread:
            mock_thread.return_value.start = lambda: None
            trmd_module.start_periodic_log_cleanup(interval_seconds=3600)
            trmd_module.start_periodic_log_cleanup(interval_seconds=3600)
            mock_thread.assert_called_once()
        trmd_module._log_cleanup_thread_started = False

    def test_transfer_store_purges_old_event_records_without_deleting_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1')
            store.add_event(task_id, 'recent event')
            old_cutoff = TransferStore.retention_cutoff_iso(
                TransferStore.TRANSFER_EVENTS_RETENTION_DAYS + 1
            )
            with store.connect(run_maintenance=False) as conn:
                conn.execute(
                    'UPDATE transfer_events SET created_at = ? WHERE message = ?',
                    (old_cutoff, 'recent event')
                )
                conn.execute(
                    '''
                    INSERT INTO transfer_events (task_id, level, message, created_at)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (task_id, 'info', 'fresh event', store.utc_now())
                )

            counts = store.purge_old_event_records(force=True)

            self.assertEqual(1, counts['transfer_events'])
            self.assertIsNotNone(store.get_task(task_id))
            events = store.list_events(task_id, limit=10)
            messages = {event['message'] for event in events}
            self.assertIn('fresh event', messages)
            self.assertNotIn('recent event', messages)

    def test_transfer_store_skips_event_purge_until_weekly_interval(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            store.purge_old_event_records(force=True)
            skipped = store.purge_old_event_records(force=False)
            self.assertIsNone(skipped)

    def test_transfer_store_purges_old_live_watch_and_cleanup_log_records(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            watch_id = 'watch-1'
            store.upsert_live_transfer_watch(watch_id, 'download', 'https://t.me/source')
            old_watch_cutoff = TransferStore.retention_cutoff_iso(
                TransferStore.LIVE_WATCH_EVENTS_RETENTION_DAYS + 1
            )
            store.add_live_watch_event(watch_id, '123', 1, None, None, 'success', 'old event')
            with store.connect(run_maintenance=False) as conn:
                conn.execute(
                    'UPDATE live_watch_events SET created_at = ?',
                    (old_watch_cutoff,)
                )

            store.insert_cleanup_log('/tmp/old.bin', reason='test')
            old_cleanup_cutoff = TransferStore.retention_cutoff_iso(
                TransferStore.CLEANUP_LOG_RETENTION_DAYS + 1
            )
            with store.connect(run_maintenance=False) as conn:
                conn.execute(
                    'UPDATE cleanup_log SET created_at = ?',
                    (old_cleanup_cutoff,)
                )

            counts = store.purge_old_event_records(force=True)

            self.assertGreaterEqual(counts['live_watch_events'], 1)
            self.assertGreaterEqual(counts['cleanup_log'], 1)
            self.assertIsNotNone(store.get_live_transfer_watch(watch_id))

    def test_transfer_store_purges_old_system_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            store.add_system_log('watch', 'message_received', 'new message')
            old_cutoff = TransferStore.retention_cutoff_iso(
                TransferStore.SYSTEM_LOGS_RETENTION_DAYS + 1
            )
            with store.connect(run_maintenance=False) as conn:
                conn.execute(
                    'UPDATE system_logs SET created_at = ?',
                    (old_cutoff,)
                )
            store.add_system_log('watch', 'message_received', 'fresh message')

            counts = store.purge_old_event_records(force=True)

            self.assertGreaterEqual(counts['system_logs'], 1)
            logs, total = store.list_system_logs(limit=10)
            messages = {row['message'] for row in logs}
            self.assertIn('fresh message', messages)
            self.assertNotIn('new message', messages)

    def test_list_system_logs_supports_filters_and_pagination(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            store.add_system_log('watch', 'message_received', 'watch log', level='info')
            store.add_system_log('filter', 'filter_reject', 'filter log', level='warning')
            store.add_system_log('archive', 'archive_success', 'archive log', level='info')

            filtered, total = store.list_system_logs(category='filter', limit=10)
            self.assertEqual(1, total)
            self.assertEqual('filter log', filtered[0]['message'])

            page, page_total = store.list_system_logs(limit=1, offset=1)
            self.assertEqual(3, page_total)
            self.assertEqual(1, len(page))

    def test_export_system_logs_text_exports_all_matching_rows(self):
        from module.persistence.system_log import build_system_logs_export_text

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            store.add_system_log(
                'watch', 'message_received', 'watch log',
                level='info', trace_id='t1', watch_id='w1'
            )
            store.add_system_log(
                'filter', 'filter_reject', 'filter log A',
                level='warning', trace_id='t2'
            )
            store.add_system_log(
                'filter', 'filter_reject', 'filter log B',
                level='warning', source_chat_id='-1001', source_message_id=42
            )

            text = build_system_logs_export_text(
                store,
                category='filter',
            )
            lines = text.splitlines()
            self.assertEqual(2, len(lines))
            self.assertTrue(all('[WARNING]' in line for line in lines))
            self.assertTrue(all('[filter/filter_reject]' in line for line in lines))
            self.assertIn('filter log A', text)
            self.assertIn('filter log B', text)
            self.assertIn('Trace: t2', text)
            self.assertIn('chat: -1001', text)
            self.assertIn('msg: 42', text)
            self.assertNotIn('watch log', text)

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
        self.assertEqual(1, UserConfig.TEMPLATE['max_tasks']['upload'])
        self.assertEqual(
            4 * 1024 ** 3,
            GlobalConfig.TEMPLATE['target_profiles']['pikpak']['max_file_size']
        )
        archive = GlobalConfig.TEMPLATE['target_profiles']['pikpak']['archive']
        # ADR-0012: archive stays off until First-run Setup Wizard probes rclone.
        self.assertFalse(archive['enable'])
        self.assertEqual('pikpak', archive['remote'])
        self.assertEqual('My Telegram', archive['source_directory'])
        self.assertEqual('Telegram', archive['root_directory'])

        settings = merge_allowed_settings(
            target=deepcopy(GlobalConfig.TEMPLATE),
            patch={'target_profiles': {'pikpak': {'max_file_size': 1024}}},
            allowed={'target_profiles'}
        )
        self.assertEqual(1024, settings['target_profiles']['pikpak']['max_file_size'])
        self.assertFalse(settings['target_profiles']['pikpak']['archive']['enable'])
        self.assertEqual(
            4 * 1024 ** 3,
            GlobalConfig.TEMPLATE['target_profiles']['pikpak']['max_file_size']
        )

    def test_user_config_normalizes_runtime_numeric_settings(self):
        UserConfig = import_with_clean_argv(
            lambda: __import__('module.config', fromlist=['UserConfig'])
        ).UserConfig

        config = UserConfig.normalize_runtime_numbers({
            'max_tasks': {
                'download': '2',
                'upload': '0'
            },
            'max_retries': {
                'download': '7',
                'upload': None
            }
        })

        self.assertEqual(2, config['max_tasks']['download'])
        self.assertEqual(1, config['max_tasks']['upload'])
        self.assertEqual(7, config['max_retries']['download'])
        self.assertEqual(3, config['max_retries']['upload'])
        self.assertIs(int, type(config['max_tasks']['download']))
        self.assertIs(int, type(config['max_retries']['download']))

    def test_update_web_settings_keeps_runtime_task_limits_numeric_from_string_config(self):
        from module.downloader import TelegramRestrictedMediaDownloader

        saved_user_configs = []
        saved_global_configs = []

        def save_global_config(config):
            saved_global_configs.append(config)
            downloader.gc.config = config

        downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
        downloader.app = SimpleNamespace(
            config={
                'api_id': '123',
                'api_hash': 'hash',
                'bot_token': '',
                'session_directory': '/tmp/session',
                'save_directory': '/tmp/downloads',
                'temp_directory': '/tmp/temp',
                'download_type': ['video'],
                'is_shutdown': False,
                'proxy': {},
                'max_tasks': {
                    'download': '1',
                    'upload': '1'
                },
                'max_retries': {
                    'download': '5',
                    'upload': '3'
                }
            },
            config_path='/tmp/config.yaml',
            save_config=saved_user_configs.append,
            TEMP_DIRECTORY='/tmp/temp-default',
            WORK_DIRECTORY='/tmp/session-default'
        )
        downloader.gc = SimpleNamespace(
            config={'notice': True},
            save_config=save_global_config
        )
        downloader.download_upload_window = SimpleNamespace(notify_limit_changed=lambda: None)
        downloader.local_storage_guard = None

        settings = downloader.update_web_settings({'global': {'notice': False}})

        self.assertFalse(settings['global']['notice'])
        self.assertEqual(1, downloader.app.max_download_task)
        self.assertEqual(1, downloader.app.max_upload_task)
        self.assertEqual(5, downloader.app.max_download_retries)
        self.assertEqual(3, downloader.app.max_upload_retries)
        self.assertIs(int, type(downloader.app.max_download_task))
        self.assertIs(int, type(downloader.app.max_upload_task))
        self.assertEqual(1, saved_user_configs[0]['max_tasks']['download'])
        self.assertEqual(5, saved_user_configs[0]['max_retries']['download'])

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
        self.assertEqual(180, archive['poll_seconds'])
        self.assertEqual(5, archive['poll_interval_seconds'])
        self.assertEqual(3600, archive['match_window_seconds'])
        self.assertEqual(300, archive['archive_retry_interval_seconds'])

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

    def test_webui_view_model_is_the_public_task_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/source',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=4
            )
            success_item = store.add_item(
                task_id=task_id,
                source_message_id=1,
                source_link='https://t.me/source/1',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.SUCCESS,
                file_name='done.mp4',
                file_size=1024
            )
            failed_item = store.add_item(
                task_id=task_id,
                source_message_id=2,
                source_link='https://t.me/source/2',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.FAILURE,
                error_message='target rejected file'
            )
            skipped_item = store.add_item(
                task_id=task_id,
                source_message_id=3,
                source_link='https://t.me/source/3',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.SKIPPED
            )
            store.add_item(
                task_id=task_id,
                source_message_id=4,
                source_link='https://t.me/source/4',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.RUNNING
            )
            store.update_item_progress(success_item, phase='uploaded', download_current=1024, download_total=1024)
            store.update_item_progress(failed_item, phase='failed', upload_current=3, upload_total=10)
            store.update_item(skipped_item, phase='skipped')
            store.refresh_task_counts(task_id, expected_total=4, assignment_completed=False)

            model = WebUiViewModel(store)
            task_list = model.task_list()['tasks']
            detail = model.task_detail(task_id, item_limit=10, event_limit=10)
            failed_detail = model.task_detail(task_id, item_limit=10, item_status=TransferStatus.FAILURE)

            self.assertEqual(1, len(task_list))
            task = task_list[0]
            self.assertEqual(task_id, task['id'])
            self.assertEqual(4, task['total_items'])
            self.assertEqual(2, task['completed_items'])
            self.assertEqual(1, task['failed_items'])
            self.assertEqual(1, task['skipped_items'])
            self.assertEqual(1, task['running_items'])
            self.assertEqual(50, task['progress_percent'])
            self.assertTrue(task['can_pause'])
            self.assertFalse(task['can_resume'])
            self.assertTrue(task['can_retry'])
            self.assertNotIn('success_count', task)
            self.assertNotIn('failed_count', task)
            self.assertNotIn('skipped_count', task)

            self.assertEqual(task, detail['task'])
            self.assertEqual(
                {
                    'total': 4,
                    'completed': 2,
                    'success': 1,
                    'skipped': 1,
                    'failed': 1,
                    'running': 1,
                    'pending': 0,
                    'terminal': 3,
                    'progress_percent': 50,
                },
                detail['summary']
            )
            self.assertEqual(4, len(detail['items']))
            self.assertEqual(10, detail['page']['items_limit'])
            self.assertEqual(10, detail['page']['events_limit'])
            self.assertEqual(1, failed_detail['page']['item_count'])
            self.assertEqual(1, len(failed_detail['items']))
            self.assertEqual(TransferStatus.FAILURE, failed_detail['items'][0]['status'])
            self.assertEqual(4, failed_detail['summary']['total'])

    def test_webui_task_stats_use_task_level_counts_across_the_full_web_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_ids = {}
            for status in (
                TransferStatus.PENDING,
                TransferStatus.RUNNING,
                TransferStatus.PAUSED,
                TransferStatus.SUCCESS,
                TransferStatus.SKIPPED,
                TransferStatus.FAILURE,
            ):
                task_id = store.create_task(
                    f'https://t.me/source/{status}',
                    'https://t.me/pikpak_bot',
                )
                store.update_task(task_id, status=status)
                task_ids[status] = task_id

            failed_task_id = task_ids[TransferStatus.FAILURE]
            for message_id in (1, 2):
                store.add_item(
                    task_id=failed_task_id,
                    source_message_id=message_id,
                    source_link=f'https://t.me/source/{message_id}',
                    target_link='https://t.me/pikpak_bot',
                    status=TransferStatus.FAILURE,
                )

            store.create_task(
                'https://t.me/watch/1',
                'https://t.me/pikpak_bot',
                execution_mode=ExecutionMode.WATCH_INLINE,
            )

            payload = WebUiViewModel(store).task_list(limit=1)

            self.assertEqual(1, len(payload['tasks']))
            self.assertEqual(
                {
                    'total_tasks': 6,
                    'completed_tasks': 2,
                    'running_tasks': 1,
                    'failed_tasks': 1,
                    'pending_tasks': 1,
                    'paused_tasks': 1,
                    'failed_items': 2,
                },
                payload['task_stats'],
            )
            store.connect().close()
            store._tls.conn = None

    def test_webui_settings_model_is_the_public_settings_contract(self):
        settings = {
            'user': {
                'download_type': ['video', 'document'],
            },
            'global': {
                'forward_type': {'video': True, 'photo': False},
                'message_filter': {
                    'media_types': {'video': True, 'text': False}
                }
            }
        }
        schema = {
            'download_type': ['video', 'photo', 'document'],
            'forward_type': ['video', 'photo'],
            'message_filter': {
                'media_types': ['video', 'text']
            }
        }

        model = WebUiViewModel.settings_model(settings, schema)

        self.assertEqual(
            [{'value': 'video', 'label': 'video'}, {'value': 'photo', 'label': 'photo'}, {'value': 'document', 'label': 'document'}],
            model['options']['download_type']
        )
        self.assertEqual(['video', 'document'], model['selections']['user_download_type'])
        self.assertEqual({'video': True, 'photo': False}, model['selections']['forward_type'])
        self.assertEqual({'video': True, 'text': False}, model['selections']['message_filter_media_types'])

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
            headers = self._authenticated_headers(server)
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
                self.assertEqual(1, body['total'])

                conn.request('DELETE', f'/api/tasks/{task_id}', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['deleted'])
                self.assertIsNone(store.get_task(task_id))
                self.assertEqual(1, len(store.list_download_success_records()))
            finally:
                server.stop()

    def test_webui_download_records_support_pagination_and_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            for index in range(3):
                store.upsert_download_success_record(
                    source_chat_id='source',
                    source_message_id=index + 1,
                    source_link=f'https://t.me/source/{index + 1}',
                    media_type='document',
                    local_path=os.path.join(directory, f'file-{index + 1}.bin'),
                    file_size=index + 1,
                    file_name=f'file-{index + 1}.bin'
                )
            server = WebUiServer(store=store, username='admin', password='pass')
            server.start(open_browser=False)
            headers = self._authenticated_headers(server)
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request('GET', '/api/download-records?limit=2&offset=0', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertEqual(2, len(body['records']))
                self.assertEqual(3, body['total'])
                self.assertEqual(2, body['limit'])
                self.assertEqual(0, body['offset'])

                conn.request('GET', '/api/download-records?limit=2&offset=2', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertEqual(1, len(body['records']))
                self.assertEqual(3, body['total'])

                conn.request('DELETE', '/api/download-records', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['cleared'])
                self.assertEqual(3, body['count'])
                self.assertEqual(0, store.count_download_success_records())
            finally:
                server.stop()

    def test_telegram_auth_status_requires_webui_session(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            server = WebUiServer(store=store, username='admin', password='pass')
            server.start(open_browser=False)
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request('GET', '/api/auth/status')
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(401, response.status)
                self.assertEqual('auth_required', body['error_code'])
                self.assertIsNone(response.getheader('WWW-Authenticate'))

                conn.request(
                    'POST',
                    '/api/auth/submit',
                    body=json.dumps({'phone': '+8615000000000'}),
                    headers={'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(401, response.status)
                self.assertEqual('auth_required', body['error_code'])
                self.assertIsNone(response.getheader('WWW-Authenticate'))

                headers = self._login_headers(conn)
                conn.request('GET', '/api/auth/status', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertEqual('none', body['step'])
            finally:
                server.stop()

    def test_webui_rejects_legacy_basic_authorization_header(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            server = WebUiServer(store=store, username='admin', password='pass')
            server.start(open_browser=False)
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                conn.request(
                    'GET',
                    '/api/auth/status',
                    headers={'Authorization': 'Basic YWRtaW46cGFzcw=='}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(401, response.status)
                self.assertEqual('auth_required', body['error_code'])
                self.assertIsNone(response.getheader('WWW-Authenticate'))
                self.assertIsNone(response.getheader('Set-Cookie'))
            finally:
                server.stop()

    def test_webui_api_errors_include_stable_error_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            server = WebUiServer(store=store, username='admin', password='pass')
            server.start(open_browser=False)
            headers = self._authenticated_headers(server)
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
            headers = self._authenticated_headers(server, content_type='application/json')
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
            headers = self._authenticated_headers(server, content_type='application/json')
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
            headers = self._authenticated_headers(server, content_type='application/json')
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
            headers = self._authenticated_headers(server, content_type='application/json')
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
                file_name='73962 - 作者_ #示例社区 #示例标签.mp4',
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
                        archive_path='Telegram/chengdudiyi8/73962 - 作者_ #示例社区 #示例标签.mp4'
                    )

            downloader.transfer_store = store
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )
            downloader.submit_web_task = lambda submitted_task_id: submitted.append(submitted_task_id)

            reset_items = downloader.retry_failed_web_task(task_id)

            self.assertEqual(0, reset_items)
            self.assertEqual([], submitted)
            self.assertEqual(1, len(archive_calls))
            self.assertEqual('chengdudiyi8', archive_calls[0]['source_folder'])
            self.assertEqual('73962 - 作者_ #示例社区 #示例标签.mp4', archive_calls[0]['file_name'])
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
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )
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
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )
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
            self.assertEqual([f'discard:{task_id}:True'], submitted)

            self.assertTrue(downloader.resume_web_task(task_id))
            self.assertEqual(TransferStatus.PENDING, store.get_task(task_id)['status'])
            self.assertEqual([f'discard:{task_id}:True', task_id], submitted)

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

            def list_watches(self, tz_offset_minutes=None) -> list:
                return []

            def create_watch(self, payload: dict) -> dict:
                return {}

            def delete_watch(self, watch_id: str) -> bool:
                return True

            def delete_web_task(self, task_id: int) -> bool:
                return self.store.delete_task(task_id)

            def retry_failed_web_task(self, task_id: int) -> int:
                return 0

            def submit_web_task(self, task_id: int) -> None:
                pass

            def statistics(self) -> dict:
                return {}

            def export_table(self, table_type: str) -> dict:
                return {}

            def create_upload(self, payload: dict) -> dict:
                return {}

            def create_channel_download(self, payload: dict) -> dict:
                return {}

            def detect_transfer_range(self, source_link: str):
                return None

        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source', 'https://t.me/pikpak_bot')
            operations = TaskControlOperations(store)
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            headers = self._authenticated_headers(server, content_type='application/json')
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
            headers = self._authenticated_headers(server)
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

    def test_webui_exports_and_imports_forward_watches(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            headers = self._authenticated_headers(server)
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request(
                    'POST',
                    '/api/watches',
                    body=json.dumps({
                        'type': 'forward',
                        'source_link': 'https://t.me/source-a',
                        'target_link': 'https://t.me/target-a',
                        'include_comment': True,
                    }),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                response.read()
                self.assertEqual(201, response.status)

                conn.request('GET', '/api/watches/forward/export', headers=headers)
                response = conn.getresponse()
                export_body = response.read().decode('utf-8')
                self.assertEqual(200, response.status)
                self.assertIn('attachment; filename="forward-watches-', response.getheader('content-disposition') or '')
                export_payload = json.loads(export_body)
                self.assertEqual('live_forward_watches', export_payload['kind'])
                self.assertEqual(1, len(export_payload['watches']))
                self.assertTrue(export_payload['watches'][0]['include_comment'])

                conn.request(
                    'POST',
                    '/api/watches/forward/import',
                    body=export_body,
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                import_body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertEqual(0, import_body['created'])
                self.assertEqual(1, import_body['skipped'])
                self.assertEqual(0, import_body['failed'])

                export_payload['watches'].append({
                    'source_link': 'https://t.me/source-b',
                    'target_link': 'https://t.me/target-b',
                    'include_comment': False,
                    'resolve_deep_link': False,
                })
                conn.request(
                    'POST',
                    '/api/watches/forward/import',
                    body=json.dumps(export_payload),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                import_body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertEqual(1, import_body['created'])
                self.assertEqual(1, import_body['skipped'])
                self.assertEqual(0, import_body['failed'])
            finally:
                server.stop()

    def test_webui_rejects_conflicting_live_transfer_watch_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            headers = self._authenticated_headers(server)
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
            headers = self._authenticated_headers(server)
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)

                conn.request('GET', '/api/statistics', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['tables']['channel']['available'])
                self.assertEqual(2, body['summary']['channels'])

                conn.request(
                    'POST',
                    '/api/tables/export',
                    body=json.dumps({'table_type': 'channel'}),
                    headers={**headers, 'Content-Type': 'application/json'}
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['exported'])
                self.assertEqual('channel', body['table_type'])
                self.assertEqual(['channel'], operations.exported_tables)
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
            headers = self._authenticated_headers(server)
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
            headers = self._authenticated_headers(server, content_type='application/json')
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
            headers = self._authenticated_headers(server, content_type='application/json')
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
            headers = self._authenticated_headers(server, content_type='application/json')
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
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )
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
                        archive_path='Telegram/chengdudiyi8/73962 - 作者_ #示例社区 #示例标签.mp4'
                    )

            downloader.forward = fake_forward
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )

            asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(
                    id=73962,
                    link='https://t.me/chengdudiyi8/73962',
                    caption='作者： #示例社区 #示例标签\n主题：【合集】 示例标题',
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
            self.assertEqual(
                'chengdudiyi8/73962 - 作者_ #示例社区 #示例标签',
                archive_calls[0]['source_folder']
            )
            self.assertEqual(
                '73962 - 作者_ #示例社区 #示例标签.mp4',
                archive_calls[0]['file_name']
            )
            self.assertFalse(archive_calls[0]['match_original_name'])
            item = store.list_items(task_id)[0]
            self.assertEqual('73962 - 作者_ #示例社区 #示例标签.mp4', item['file_name'])
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
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )

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
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )

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

    def test_direct_pikpak_forward_without_media_metadata_skips_archive_folder(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
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
                download_upload=True,
                message_filter={'enabled': True, 'media_types': dict(MEDIA_TYPES_DEFAULT)},
            )
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
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )
            downloader.wait_for_pikpak_ingest_confirmation = AsyncMock(return_value=True)
            downloader.get_message_media_target_limit_meta = (
                downloader.pikpak_manager.get_message_media_target_limit_meta
            )
            downloader.get_message_media_archive_filename = (
                PikpakIntegrationManager.get_message_media_archive_filename
            )
            downloader.get_task_target_size_limit_error = (
                downloader.pikpak_manager.get_task_target_size_limit_error
            )
            downloader.is_pikpak_target = PikpakIntegrationManager.is_pikpak_target
            downloader.forwarded_message_has_identity = (
                PikpakIntegrationManager.forwarded_message_has_identity
            )
            downloader.complete_forwarded_pikpak_item = (
                downloader.pikpak_manager.complete_forwarded_pikpak_item
            )
            downloader.archive_pikpak_item = downloader.pikpak_manager.archive_pikpak_item
            downloader.refresh_transfer_task_counts = (
                lambda tid: store.refresh_task_counts(tid)
            )
            downloader.runtime_message_filter = lambda override=None: build_runtime_message_filter(
                downloader.gc.message_filter,
                override,
            )

            asyncio.run(downloader.transfer_message_to_web_target(
                task=task,
                message=SimpleNamespace(
                    id=1,
                    text='求片 取一',
                    caption=None,
                    link='https://t.me/ctuxas/1',
                    chat=SimpleNamespace(id=-100123, username='ctuxas')
                ),
                origin_chat_id='source-chat',
                target_chat_id='target-chat',
                source_link='https://t.me/ctuxas/1'
            ))

            self.assertEqual([], archive_calls)
            self.assertEqual([], folder_calls)
            item = store.list_items(task_id)[0]
            self.assertEqual(TransferStatus.SKIPPED, item['status'])
            self.assertIn('PikPak 不支持无媒体消息', item['error_message'] or '')
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
        downloader.pikpak_manager = PikpakIntegrationManager(
            transfer_store_getter=lambda: None,
            pikpak_archive_client_getter=lambda: FakeArchiveClient(),
            diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
            gc_getter=lambda: None,
            refresh_counts=lambda tid: None,
        )

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
        self.assertFalse(archive_calls[0]['match_original_name'])

    def test_pikpak_upload_archive_failure_keeps_upload_success_and_records_archive_error(self):
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
                archive_match_original_name=False,
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
            downloader.gc = SimpleNamespace(config={
                'target_profiles': {
                    'pikpak': {
                        'archive': {
                            'enable': True,
                            'remote': 'pikpak',
                            'archive_delay_seconds': 0,
                            'match_window_seconds': 0
                        }
                    }
                }
            })
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )

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

            async def run():
                downloader.on_transfer_upload_status(upload_task)
                await asyncio.sleep(0.05)

            asyncio.run(run())

            self.assertEqual(1, len(archive_calls))
            self.assertFalse(archive_calls[0]['match_original_name'])
            item = store.list_items(task_id)[0]
            self.assertEqual(TransferStatus.SUCCESS, item['status'])
            self.assertEqual('sent', item['phase'])
            self.assertEqual('not_found', item['archive_status'])
            self.assertIn('PikPak archive not_found', item['error_message'])
            task = store.get_task(task_id)
            self.assertEqual(1, task['completed_items'])
            self.assertEqual(0, task['failed_items'])

    def test_downloader_retry_failed_recovers_pikpak_upload_archive_failure_before_resubmitting(self):
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
                source_message_id=1,
                source_link='https://t.me/ctuxas/1',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='73962 - 作者_ #示例社区 #示例标签.mp4',
                file_size=5,
                source_folder='ctuxas',
                archive_status='not_found',
                archive_match_original_name=False,
                phase='sent',
                status=TransferStatus.SUCCESS,
                error_message='PikPak archive not_found: No PikPak file matched 73962 - 作者_ #示例社区 #示例标签.mp4.'
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
                        archive_path='Telegram/ctuxas/73962 - 作者_ #示例社区 #示例标签.mp4'
                    )

            downloader.transfer_store = store
            downloader.pikpak_manager = PikpakIntegrationManager(
                transfer_store_getter=lambda: downloader.__dict__.get('transfer_store'),
                pikpak_archive_client_getter=lambda: FakeArchiveClient(),
                diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
                gc_getter=lambda: downloader.__dict__.get('gc'),
                refresh_counts=lambda tid: (s.refresh_task_counts(tid) if (s := downloader.__dict__.get('transfer_store')) else None),
            )
            downloader.submit_web_task = lambda submitted_task_id: submitted.append(submitted_task_id)

            reset_items = downloader.retry_failed_web_task(task_id)

            self.assertEqual(0, reset_items)
            self.assertEqual([], submitted)
            self.assertEqual(1, len(archive_calls))
            self.assertEqual('73962 - 作者_ #示例社区 #示例标签.mp4', archive_calls[0]['file_name'])
            self.assertFalse(archive_calls[0]['match_original_name'])
            item = store.list_items(task_id)[0]
            self.assertEqual(item_id, item['id'])
            self.assertEqual(TransferStatus.SUCCESS, item['status'])
            self.assertEqual('sent', item['phase'])
            self.assertEqual('success', item['archive_status'])
            self.assertEqual(0, item['archive_match_original_name'])
            task = store.get_task(task_id)
            self.assertEqual(TransferStatus.SUCCESS, task['status'])
            self.assertEqual(1, task['completed_items'])
            self.assertEqual(0, task['failed_items'])

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
        self.assertEqual('on_transfer_upload_status', meta['status_callback'].__name__)
        self.assertEqual('on_transfer_upload_status', meta['status_callback'].__func__.__name__)
        self.assertEqual('on_transfer_file_ready', meta['on_file_ready'].__name__)
        self.assertEqual('on_transfer_file_ready', meta['on_file_ready'].__func__.__name__)

    def test_pikpak_transfer_over_target_limit_skips_before_forward_or_download(self):
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
            self.assertEqual(TransferStatus.SKIPPED, items[0]['status'])
            self.assertEqual('skipped', items[0]['phase'])
            self.assertIn('PikPak', items[0]['error_message'])
            events = store.list_events(task_id)
            self.assertTrue(any(event['level'] == 'warning' and 'PikPak' in event['message'] for event in events))
            task = store.get_task(task_id)
            self.assertEqual(1, task['completed_items'])
            self.assertEqual(0, task['failed_items'])

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
        downloader.pikpak_manager = PikpakIntegrationManager(
            transfer_store_getter=lambda: None,
            pikpak_archive_client_getter=lambda: FakeArchiveClient(),
            diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
            gc_getter=lambda: None,
            refresh_counts=lambda tid: None,
        )

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

    def test_forward_media_group_archives_each_member_to_pikpak(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)
        archive_calls = []

        def fake_archive_pikpak_item(**kwargs):
            archive_calls.append(kwargs)
            return SimpleNamespace(ok=True, status='success')

        video_message = SimpleNamespace(
            id=1,
            link='https://t.me/source/1',
            chat=SimpleNamespace(id='source-chat', username='chengdudiyi8'),
            video=SimpleNamespace(file_size=500, file_name='video.mp4'),
            caption='共同标题'
        )
        photo_message = SimpleNamespace(
            id=2,
            link='https://t.me/source/2',
            chat=SimpleNamespace(id='source-chat', username='chengdudiyi8'),
            photo=SimpleNamespace(file_size=100, file_id='photo-file-id'),
            caption=None
        )

        async def get_media_group():
            return [video_message, photo_message]

        video_message.get_media_group = get_media_group

        class FakeClient:
            async def copy_media_group(self, **_kwargs):
                return [SimpleNamespace(id=101), SimpleNamespace(id=102)]

        downloader.app = SimpleNamespace(client=FakeClient())
        downloader.transfer_store = None
        downloader.archive_pikpak_item = fake_archive_pikpak_item

        result = asyncio.run(downloader.forward(
            client=downloader.app.client,
            message=video_message,
            message_id=1,
            origin_chat_id='source-chat',
            target_chat_id='target-chat',
            target_link='https://t.me/pikpak_bot',
            media_group=[1, 2],
            done_notice=False,
            ignore_type_filter=True
        ))

        self.assertEqual([101, 102], [item.id for item in result])
        self.assertEqual(2, len(archive_calls))
        self.assertEqual({1, 2}, {call['message'].id for call in archive_calls})
        self.assertEqual('chengdudiyi8', archive_calls[0]['source_folder'])
        self.assertEqual('chengdudiyi8', archive_calls[1]['source_folder'])
        self.assertEqual('2 - 共同标题.jpg', PikpakIntegrationManager.get_message_media_archive_filename(photo_message))

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

    def test_listen_forward_downloads_discussion_reply_when_direct_copy_fails(self):
        from pyrogram.errors.exceptions.bad_request_400 import MediaCaptionTooLong
        from pyrogram.types import Message

        TelegramRestrictedMediaDownloader = import_downloader_class()
        downloader = object.__new__(TelegramRestrictedMediaDownloader)

        reply_message = Message()
        reply_message.id = 15
        reply_message.link = 'https://t.me/discuss/15'
        reply_message.chat = SimpleNamespace(id='discussion-chat')
        reply_message.video = SimpleNamespace(file_size=10, file_name='reply.mp4')

        class FakeClient:
            async def get_discussion_replies(self, chat_id, message_id):
                if chat_id == 'source-chat' and message_id == 5:
                    yield reply_message

            async def copy_message(self, **kwargs):
                raise MediaCaptionTooLong()

        downloader.app = SimpleNamespace(client=FakeClient())
        downloader.gc = SimpleNamespace(
            download_upload=True,
            upload_delete=False,
            message_filter={'enabled': False}
        )
        downloader.download_calls = []

        async def fake_create_download_task(**kwargs):
            downloader.download_calls.append(kwargs)
            return {'status': 'success'}

        downloader.check_type = lambda message: True
        downloader.create_download_task = fake_create_download_task
        downloader.build_download_upload_meta = lambda **kwargs: {
            'link': kwargs.get('target_link'),
            'with_delete': True,
            'send_as_media_group': False,
            'source_link': kwargs.get('source_link'),
            'source_folder': kwargs.get('source_folder')
        }
        downloader.create_bot_transfer_progress = AsyncMock(return_value=None)
        downloader.done_notice = AsyncMock()

        count = asyncio.run(downloader.forward_discussion_replies(
            client=SimpleNamespace(me=SimpleNamespace(id=123)),
            source_chat_id='source-chat',
            source_message_id=5,
            target_chat_id='target-chat',
            target_link='https://t.me/pikpak_bot',
            done_notice=False,
            watch_id='forward:https://t.me/source https://t.me/pikpak_bot --include-comment'
        ))

        self.assertEqual(1, count)
        self.assertEqual(1, len(downloader.download_calls))
        fallback = downloader.download_calls[0]
        self.assertIs(reply_message, fallback['message_ids'])
        self.assertEqual('https://t.me/pikpak_bot', fallback['with_upload']['link'])
        self.assertTrue(fallback['with_upload']['with_delete'])
        self.assertFalse(fallback['with_upload']['send_as_media_group'])

    def test_webui_accepts_non_recursive_directory_upload_for_upload_command_parity(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, 'media.bin'), 'wb') as file:
                file.write(b'12345')
            store = TransferStore(directory=directory)
            operations = FakeWebUiOperations()
            server = WebUiServer(store=store, operations=operations, username='admin', password='pass')
            server.start(open_browser=False)
            headers = self._authenticated_headers(server)
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
            headers = self._authenticated_headers(server)
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
        downloader.watch_manager = LiveWatchManager(
            listen_download_chat=downloader.listen_download_chat,
            listen_forward_chat=downloader.listen_forward_chat,
            web_pending_watches=downloader.web_pending_watches,
            web_watch_handler_clients=downloader.web_watch_handler_clients,
            transfer_store_getter=lambda: getattr(downloader, 'transfer_store', None),
            operation_submitter=downloader.submit_web_operation,
            user_getter=lambda: getattr(downloader, 'user', None),
            app_getter=lambda: getattr(downloader, 'app', None),
        )

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
            downloader.watch_manager = LiveWatchManager(
                listen_download_chat=downloader.listen_download_chat,
                listen_forward_chat=downloader.listen_forward_chat,
                web_pending_watches=downloader.web_pending_watches,
                web_watch_handler_clients=downloader.web_watch_handler_clients,
                transfer_store_getter=lambda: getattr(downloader, 'transfer_store', None),
                operation_submitter=downloader.submit_web_operation,
                user_getter=lambda: getattr(downloader, 'user', None),
                app_getter=lambda: getattr(downloader, 'app', None),
            )
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
        downloader.watch_manager = LiveWatchManager(
            listen_download_chat=downloader.listen_download_chat,
            listen_forward_chat=downloader.listen_forward_chat,
            web_pending_watches=downloader.web_pending_watches,
            web_watch_handler_clients=downloader.web_watch_handler_clients,
            transfer_store_getter=lambda: getattr(downloader, 'transfer_store', None),
            operation_submitter=downloader.submit_web_operation,
            user_getter=lambda: getattr(downloader, 'user', None),
            app_getter=lambda: getattr(downloader, 'app', None),
        )

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
            downloader.watch_manager = LiveWatchManager(
                listen_download_chat=downloader.listen_download_chat,
                listen_forward_chat=downloader.listen_forward_chat,
                web_pending_watches=downloader.web_pending_watches,
                transfer_store_getter=lambda: getattr(downloader, 'transfer_store', None),
                operation_submitter=downloader.submit_web_operation,
                user_getter=lambda: getattr(downloader, 'user', None),
                app_getter=lambda: getattr(downloader, 'app', None),
            )

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

    def test_live_watch_manager_reports_total_and_today_event_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            watch_id = 'forward:https://t.me/source -> https://t.me/target'
            store.upsert_live_transfer_watch(
                watch_id=watch_id,
                watch_type='forward',
                source_link='https://t.me/source',
                target_link='https://t.me/target',
                include_comment=False,
                status=TransferStatus.RUNNING,
                error_message=None
            )
            old_event_id = store.add_live_watch_event(
                watch_id=watch_id,
                source_chat_id='source',
                source_message_id=1,
                target_chat_id='target',
                target_link='https://t.me/target',
                status=TransferStatus.SUCCESS,
                message='old event'
            )
            store.add_live_watch_event(
                watch_id=watch_id,
                source_chat_id='source',
                source_message_id=2,
                target_chat_id='target',
                target_link='https://t.me/target',
                status=TransferStatus.SUCCESS,
                message='today event'
            )
            today_start, _ = store.local_today_utc_bounds()
            old_at = (
                datetime.datetime.fromisoformat(today_start) - datetime.timedelta(seconds=1)
            ).isoformat(timespec='seconds')
            with store.connect() as conn:
                conn.execute(
                    'UPDATE live_watch_events SET created_at = ? WHERE id = ?',
                    (old_at, old_event_id)
                )

            manager = LiveWatchManager(transfer_store_getter=lambda: store)
            watch = manager.list_watches()[0]
            self.assertEqual(2, watch['event_count'])
            self.assertEqual(1, watch['today_count'])

            today_events = manager.list_watch_events(watch_id, limit=50, offset=0, today_only=True)
            self.assertEqual(1, today_events['total'])
            self.assertEqual(2, today_events['events'][0]['source_message_id'])

            all_events = manager.list_watch_events(watch_id, limit=50, offset=0)
            self.assertEqual(2, all_events['total'])

    def test_live_watch_events_filter_by_status_and_return_status_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            watch_id = 'forward:https://t.me/source -> https://t.me/target'
            store.upsert_live_transfer_watch(
                watch_id=watch_id,
                watch_type='forward',
                source_link='https://t.me/source',
                target_link='https://t.me/target',
                include_comment=False,
                status=TransferStatus.RUNNING,
                error_message=None
            )
            store.add_live_watch_event(
                watch_id, 'source', 1, 'target', 'https://t.me/target',
                TransferStatus.SUCCESS, 'ok'
            )
            store.add_live_watch_event(
                watch_id, 'source', 2, 'target', 'https://t.me/target',
                TransferStatus.SKIPPED, 'filtered'
            )
            store.add_live_watch_event(
                watch_id, 'source', 3, 'target', 'https://t.me/target',
                TransferStatus.SKIPPED, 'filtered-2'
            )
            store.add_live_watch_event(
                watch_id, 'source', 4, 'target', 'https://t.me/target',
                TransferStatus.FAILURE, 'boom'
            )

            skipped, skipped_total = store.list_live_watch_events(
                watch_id, limit=10, offset=0, status=TransferStatus.SKIPPED
            )
            self.assertEqual(2, skipped_total)
            self.assertEqual([3, 2], [evt['source_message_id'] for evt in skipped])

            failure, failure_total = store.list_live_watch_events(
                watch_id, limit=10, offset=0, status=TransferStatus.FAILURE
            )
            self.assertEqual(1, failure_total)
            self.assertEqual([4], [evt['source_message_id'] for evt in failure])

            self.assertEqual(
                {'all': 4, 'success': 1, 'skipped': 2, 'failure': 1},
                store.count_live_watch_events_by_status(watch_id)
            )

            manager = LiveWatchManager(transfer_store_getter=lambda: store)
            payload = manager.list_watch_events(
                watch_id, limit=1, offset=0, status=TransferStatus.SKIPPED
            )
            self.assertEqual(2, payload['total'])
            self.assertEqual(1, len(payload['events']))
            self.assertEqual(3, payload['events'][0]['source_message_id'])
            self.assertEqual(
                {'all': 4, 'success': 1, 'skipped': 2, 'failure': 1},
                payload['status_counts']
            )
            self.assertEqual(TransferStatus.SKIPPED, payload['status'])

            with self.assertRaises(ValueError):
                manager.list_watch_events(watch_id, status='nope')

            server = WebUiServer(
                store=store,
                operations=SimpleNamespace(
                    list_watch_events=lambda *args, **kwargs: manager.list_watch_events(*args, **kwargs)
                ),
                username='admin',
                password='pass'
            )
            server.start(open_browser=False)
            headers = self._authenticated_headers(server)
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                path = f'/api/watches/{quote(watch_id, safe="")}/events?limit=10&offset=0&status=skipped'
                conn.request('GET', path, headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertEqual(2, body['total'])
                self.assertEqual(2, len(body['events']))
                self.assertEqual(
                    {'all': 4, 'success': 1, 'skipped': 2, 'failure': 1},
                    body['status_counts']
                )

                conn.request(
                    'GET',
                    f'/api/watches/{quote(watch_id, safe="")}/events?status=bogus',
                    headers=headers
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(400, response.status)
                self.assertEqual('invalid_status', body.get('error_code'))
            finally:
                server.stop()

    def test_live_watch_today_count_respects_client_timezone_offset(self):
        fixed_now = datetime.datetime(2026, 7, 10, 2, 0, 0, tzinfo=datetime.UTC)
        with patch('module.transfer_store.datetime.datetime') as dt_mock:
            dt_mock.now.return_value = fixed_now
            dt_mock.UTC = datetime.UTC
            dt_mock.timedelta = datetime.timedelta
            with tempfile.TemporaryDirectory() as directory:
                store = TransferStore(directory=directory)
                watch_id = 'forward:https://t.me/source -> https://t.me/target'
                store.upsert_live_transfer_watch(
                    watch_id=watch_id,
                    watch_type='forward',
                    source_link='https://t.me/source',
                    target_link='https://t.me/target',
                    include_comment=False,
                    status=TransferStatus.RUNNING,
                    error_message=None
                )
                # Jul 10 04:00 CST = Jul 9 20:00 UTC; local day for UTC+8, not for UTC server day.
                event_at = '2026-07-09T20:00:00+00:00'
                store.add_live_watch_event(
                    watch_id=watch_id,
                    source_chat_id='source',
                    source_message_id=9,
                    target_chat_id='target',
                    target_link='https://t.me/target',
                    status=TransferStatus.SUCCESS,
                    message='client-local today event'
                )
                with store.connect() as conn:
                    conn.execute(
                        'UPDATE live_watch_events SET created_at = ? WHERE watch_id = ?',
                        (event_at, watch_id)
                    )

                self.assertEqual(0, store.get_live_watch_event_count(
                    watch_id,
                    today_only=True,
                    tz_offset_minutes=0
                ))
                self.assertEqual(1, store.get_live_watch_event_count(
                    watch_id,
                    today_only=True,
                    tz_offset_minutes=-480
                ))

                manager = LiveWatchManager(transfer_store_getter=lambda: store)
                server_watch = manager.list_watches(tz_offset_minutes=-480)[0]
                self.assertEqual(1, server_watch['today_count'])

    def test_webui_task_model_exposes_active_transfer_progress_and_speed(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                source_link='https://t.me/source/7',
                target_link='https://t.me/pikpak_bot'
            )
            store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=7,
                source_link='https://t.me/source/7',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='movie.mp4',
                file_size=100,
                phase='downloading',
                status=TransferStatus.RUNNING
            )
            item_id = store.list_items(task_id)[0]['id']
            store.update_item_progress(
                item_id=item_id,
                phase='downloading',
                download_current=40,
                download_total=100,
                download_speed_bps=2048,
                upload_current=0,
                upload_total=100,
                upload_speed_bps=0
            )
            store.refresh_task_counts(task_id, expected_total=1, assignment_completed=False)

            task = WebUiViewModel(store).task_list()['tasks'][0]

            self.assertEqual('downloading', task['active_phase'])
            self.assertEqual('movie.mp4', task['active_file_name'])
            self.assertEqual(40, task['download_current'])
            self.assertEqual(100, task['download_total'])
            self.assertEqual(2048, task['download_speed_bps'])
            self.assertEqual(40, task['active_progress_percent'])

    def test_webui_item_model_exposes_upload_and_download_speed(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                source_link='https://t.me/source/8',
                target_link='https://t.me/pikpak_bot'
            )
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=8,
                source_link='https://t.me/source/8',
                target_link='https://t.me/pikpak_bot',
                file_name='movie.mp4',
                phase='uploading',
                status=TransferStatus.RUNNING
            )
            store.update_item_progress(
                item_id=item_id,
                phase='uploading',
                download_current=100,
                download_total=100,
                download_speed_bps=0,
                upload_current=64,
                upload_total=100,
                upload_speed_bps=4096
            )

            detail = WebUiViewModel(store).task_detail(task_id, item_status=TransferStatus.RUNNING)
            item = detail['items'][0]

            self.assertEqual(0, item['download_speed_bps'])
            self.assertEqual(4096, item['upload_speed_bps'])
            self.assertEqual(64, item['active_progress_percent'])

    def test_webui_task_list_exposes_transfer_and_disk_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                source_link='https://t.me/source/9',
                target_link='https://t.me/pikpak_bot'
            )
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=9,
                source_link='https://t.me/source/9',
                target_link='https://t.me/pikpak_bot',
                file_name='movie.mp4',
                phase='downloading',
                status=TransferStatus.RUNNING
            )
            store.update_item_progress(
                item_id=item_id,
                phase='downloading',
                download_current=40,
                download_total=100,
                download_speed_bps=2048,
                upload_current=10,
                upload_total=100,
                upload_speed_bps=1024
            )

            model = WebUiViewModel(store)
            speeds = model.transfer_speed_metrics()
            disk = WebUiViewModel.disk_metrics([directory])

            self.assertEqual(2048, speeds['download_speed_bps'])
            self.assertEqual(1024, speeds['upload_speed_bps'])
            self.assertGreater(disk['disk_free_bytes'], 0)
            self.assertEqual(directory, disk['disk_path'])

    def test_transfer_speed_metrics_includes_slow_but_active_download(self):
        """1MB download chunks at ~100KB/s update only every ~10s; must still count."""
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                source_link='https://t.me/source/12',
                target_link='https://t.me/pikpak_bot'
            )
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=12,
                source_link='https://t.me/source/12',
                target_link='https://t.me/pikpak_bot',
                file_name='slow.mp4',
                phase='downloading',
                status=TransferStatus.RUNNING
            )
            store.update_item_progress(
                item_id=item_id,
                phase='downloading',
                download_current=2 * 1024 * 1024,
                download_total=20 * 1024 * 1024,
                download_speed_bps=102400,
                upload_speed_bps=0
            )
            slow_active_at = (
                datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=15)
            ).isoformat(timespec='seconds')
            with store.connect() as conn:
                conn.execute(
                    'UPDATE transfer_items SET updated_at = ? WHERE id = ?',
                    (slow_active_at, item_id),
                )

            speeds = WebUiViewModel(store).transfer_speed_metrics()

            self.assertEqual(102400, speeds['download_speed_bps'])
            self.assertEqual(0, speeds['upload_speed_bps'])

    def test_transfer_speed_metrics_ignores_stale_running_item_speeds(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                source_link='https://t.me/source/10',
                target_link='https://t.me/pikpak_bot'
            )
            stale_id = store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=10,
                source_link='https://t.me/source/10',
                target_link='https://t.me/pikpak_bot',
                file_name='stale.mp4',
                phase='downloading',
                status=TransferStatus.RUNNING
            )
            fresh_id = store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=11,
                source_link='https://t.me/source/11',
                target_link='https://t.me/pikpak_bot',
                file_name='fresh.mp4',
                phase='downloading',
                status=TransferStatus.RUNNING
            )
            store.update_item_progress(
                item_id=stale_id,
                phase='downloading',
                download_current=40,
                download_total=100,
                download_speed_bps=3040870,
                upload_speed_bps=0
            )
            store.update_item_progress(
                item_id=fresh_id,
                phase='downloading',
                download_current=20,
                download_total=100,
                download_speed_bps=1024,
                upload_speed_bps=512
            )
            stale_at = (
                datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=120)
            ).isoformat(timespec='seconds')
            with store.connect() as conn:
                conn.execute(
                    'UPDATE transfer_items SET updated_at = ? WHERE id = ?',
                    (stale_at, stale_id),
                )

            speeds = WebUiViewModel(store).transfer_speed_metrics()

            self.assertEqual(1024, speeds['download_speed_bps'])
            self.assertEqual(512, speeds['upload_speed_bps'])

    def test_range_transfer_progress_uses_message_id_counts_for_range_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                source_link='https://t.me/source',
                target_link='https://t.me/pikpak_bot',
                start_id=100,
                end_id=102,
                include_comment=True
            )
            store.update_task_range_runtime(
                task_id,
                current_range_message_id=101,
                current_range_video_captured=12,
                current_range_video_index=8
            )
            for message_id in range(100, 101):
                store.add_item(
                    task_id=task_id,
                    source_chat_id='source',
                    source_message_id=message_id,
                    range_message_id=message_id,
                    source_link=f'https://t.me/source/{message_id}',
                    target_link='https://t.me/pikpak_bot',
                    phase='forwarded',
                    status=TransferStatus.SUCCESS
                )
            for index in range(1, 8):
                store.add_item(
                    task_id=task_id,
                    source_chat_id='discussion',
                    source_message_id=500 + index,
                    range_message_id=101,
                    source_link=f'https://t.me/discuss/{500 + index}',
                    target_link='https://t.me/pikpak_bot',
                    phase='forwarded',
                    status=TransferStatus.SUCCESS
                )
            store.add_item(
                task_id=task_id,
                source_chat_id='discussion',
                source_message_id=508,
                range_message_id=101,
                source_link='https://t.me/discuss/508',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='clip.mp4',
                phase='downloading',
                status=TransferStatus.RUNNING
            )

            task = store.get_task(task_id)
            progress = store.range_transfer_progress(task)
            task_model = WebUiViewModel(store).task_list()['tasks'][0]

            self.assertTrue(progress['uses_range_progress'])
            self.assertEqual(3, progress['range_total_ids'])
            self.assertEqual(1, progress['range_completed_ids'])
            self.assertEqual(33, progress['range_progress_percent'])
            self.assertEqual(101, progress['current_range_message_id'])
            self.assertEqual(12, progress['current_range_video_captured'])
            self.assertEqual(8, progress['current_range_video_index'])
            self.assertEqual(33, task_model['range_progress_percent'])
            self.assertEqual('1/3', f"{task_model['range_completed_ids']}/{task_model['range_total_ids']}")

    def test_range_progress_advances_past_album_when_members_use_own_range_ids(self):
        """Album archive shares one folder, but each member must keep its own range_message_id.

        If every album member is stored under the min id, range_transfer_progress hits a hole at
        the next member id and freezes completed_ids (UI stuck at ID 1/N).
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                source_link='https://t.me/chengdudiyi8',
                target_link='https://t.me/pikpak_bot',
                start_id=73464,
                end_id=73466,
            )
            # Wrong shape (pre-fix regression): both members under min id → progress freezes at 1.
            store.add_item(
                task_id=task_id,
                source_chat_id=-1001,
                source_message_id=73464,
                range_message_id=73464,
                source_link='https://t.me/chengdudiyi8/73464',
                target_link='https://t.me/pikpak_bot',
                source_folder='chengdudiyi8/73464 - title',
                phase='forwarded',
                status=TransferStatus.SUCCESS,
            )
            store.add_item(
                task_id=task_id,
                source_chat_id=-1001,
                source_message_id=73465,
                range_message_id=73464,
                source_link='https://t.me/chengdudiyi8/73465',
                target_link='https://t.me/pikpak_bot',
                source_folder='chengdudiyi8/73464 - title',
                phase='forwarded',
                status=TransferStatus.SUCCESS,
            )
            store.add_item(
                task_id=task_id,
                source_chat_id=-1001,
                source_message_id=73466,
                range_message_id=73466,
                source_link='https://t.me/chengdudiyi8/73466',
                target_link='https://t.me/pikpak_bot',
                source_folder='chengdudiyi8/73466 - next',
                phase='forwarded',
                status=TransferStatus.RUNNING,
            )
            stuck = store.range_transfer_progress(store.get_task(task_id))
            self.assertEqual(1, stuck['range_completed_ids'])
            self.assertEqual(73465, stuck['current_range_message_id'])

            # Correct shape: member keeps own range_message_id, shared folder for archive only.
            with store.connect() as conn:
                conn.execute(
                    'UPDATE transfer_items SET range_message_id = 73465 WHERE source_message_id = 73465'
                )
            progress = store.range_transfer_progress(store.get_task(task_id))
            self.assertEqual(2, progress['range_completed_ids'])
            self.assertEqual(73466, progress['current_range_message_id'])
            self.assertEqual(67, progress['range_progress_percent'])

    def test_is_range_message_complete_requires_all_comment_items_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                source_link='https://t.me/source',
                target_link='https://t.me/pikpak_bot',
                start_id=10,
                end_id=10,
                include_comment=True
            )
            store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=10,
                range_message_id=10,
                source_link='https://t.me/source/10',
                target_link='https://t.me/pikpak_bot',
                phase='forwarded',
                status=TransferStatus.SUCCESS
            )
            store.add_item(
                task_id=task_id,
                source_chat_id='discussion',
                source_message_id=299,
                range_message_id=10,
                source_link='https://t.me/c/3923609459/299',
                target_link='https://t.me/pikpak_bot',
                media_type='video',
                file_name='299 - 006.mp4',
                phase='downloading',
                status=TransferStatus.RUNNING
            )

            self.assertFalse(store.is_range_message_complete(task_id, 10))
            self.assertEqual(
                1,
                len(store.list_resumable_items_for_range_message(task_id, 10))
            )

    def test_runner_resumes_comment_item_before_advancing_range_message(self):
        TelegramRestrictedMediaDownloader = import_downloader_class()

        async def run_case():
            with tempfile.TemporaryDirectory() as directory:
                store = TransferStore(directory=directory)
                task_id = store.create_task(
                    'https://t.me/source',
                    'https://t.me/pikpak_bot',
                    start_id=10,
                    end_id=11,
                    include_comment=True
                )
                store.add_item(
                    task_id=task_id,
                    source_chat_id='source',
                    source_message_id=10,
                    range_message_id=10,
                    source_link='https://t.me/source/10',
                    target_link='https://t.me/pikpak_bot',
                    phase='forwarded',
                    status=TransferStatus.SUCCESS
                )
                store.add_item(
                    task_id=task_id,
                    source_chat_id='discussion',
                    source_message_id=299,
                    range_message_id=10,
                    source_link='https://t.me/c/3923609459/299',
                    target_link='https://t.me/pikpak_bot',
                    media_type='video',
                    file_name='299 - 006.mp4',
                    phase='downloading',
                    status=TransferStatus.RUNNING
                )
                store.update_task(task_id, status=TransferStatus.RUNNING)
                store.update_task_range_runtime(task_id, current_range_message_id=10)

                downloader = object.__new__(TelegramRestrictedMediaDownloader)
                downloader.transfer_store = store
                downloader.uploader = object()
                downloader.app = SimpleNamespace(client=SimpleNamespace())
                downloader.gc = SimpleNamespace(download_upload=True, upload_delete=False)
                downloader.forward_calls = []
                downloader.fallback_calls = []

                async def fake_forward(**kwargs):
                    downloader.forward_calls.append(kwargs)
                    return SimpleNamespace(id=100 + kwargs['message_id'])

                async def fake_create_download_task(**kwargs):
                    downloader.fallback_calls.append(kwargs)
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

                async def fake_discussion_replies(**kwargs):
                    if False:
                        yield None

                with patch('module.downloader.parse_link', side_effect=fake_parse_link), \
                        patch('module.transfer.runner.iter_discussion_reply_messages', new=fake_discussion_replies), \
                        patch.object(downloader, 'wait_between_transfer_messages', new=AsyncMock()):
                    await downloader.process_web_transfer_task(task_id)

                self.assertEqual([], downloader.forward_calls)
                self.assertEqual(1, len(downloader.fallback_calls))
                self.assertEqual(
                    'https://t.me/c/3923609459/299',
                    downloader.fallback_calls[0]['with_upload']['source_link']
                )

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
