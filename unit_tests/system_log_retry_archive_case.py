# coding=UTF-8
"""Manual archive retry from system logs (not_found)."""
import http.client
import json
import tempfile
import threading
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.adapters.pikpak.integration import PikpakIntegrationManager
from module.adapters.webui.server import WebUiServer
from module.persistence.system_log import (
    archive_retry_inflight_key,
    resolve_archive_retry_meta,
    system_log_can_retry_archive,
)
from module.transfer_store import TransferStatus, TransferStore
from module.web_operations import WebOperationsMixin


class _ArchiveRetryHost(WebOperationsMixin):
    def __init__(self, store, archive_client):
        self.transfer_store = store
        self._archive_client = archive_client
        self.pikpak_manager = PikpakIntegrationManager(
            transfer_store_getter=lambda: self.transfer_store,
            pikpak_archive_client_getter=lambda: self._archive_client,
            diagnostic=SimpleNamespace(warning=lambda m: None, info=lambda m: None, status=lambda m: None),
            gc_getter=lambda: SimpleNamespace(config={}),
            refresh_counts=lambda tid: self.transfer_store.refresh_task_counts(tid),
        )

    def archive_pikpak_item(self, *args, **kwargs):
        return self.pikpak_manager.archive_pikpak_item(*args, **kwargs)

    def is_pikpak_target(self, target_link, target_profile=None):
        return True

    def transfer_item_archive_timestamp(self, item):
        return PikpakIntegrationManager.transfer_item_archive_timestamp(item)

    def transfer_item_archive_match_original_name(self, item):
        return PikpakIntegrationManager.transfer_item_archive_match_original_name(item)

    def refresh_transfer_task_counts(self, task_id):
        self.transfer_store.refresh_task_counts(task_id)


class SystemLogRetryArchiveCase(unittest.TestCase):
    def _login_headers(self, conn):
        conn.request(
            'POST',
            '/api/auth/login',
            body=json.dumps({'username': 'admin', 'password': 'pass', 'remember_me': True}),
            headers={'Content-Type': 'application/json'},
        )
        response = conn.getresponse()
        body = json.loads(response.read().decode('utf-8'))
        self.assertEqual(200, response.status)
        self.assertTrue(body['success'])
        cookie = response.getheader('Set-Cookie')
        return {'Cookie': cookie.split(';', 1)[0]}

    def test_can_retry_true_only_for_archive_not_found_with_metadata(self):
        with_item = {
            'category': 'archive',
            'stage': 'archive_not_found',
            'message': 'rclone 归档失败(not_found): No PikPak file matched a.mp4.',
            'details': json.dumps({'task_id': 1, 'item_id': 2, 'source_folder': 'ch', 'file_name': 'a.mp4'}),
        }
        live = {
            'category': 'archive',
            'stage': 'archive_not_found',
            'message': 'rclone 归档失败(not_found): No PikPak file matched 9 - title.mp4.',
            'target_link': 'https://t.me/ch/9',
            'source_chat_id': '-1001',
            'source_message_id': 9,
            'details': json.dumps({'source_folder': 'ch', 'file_name': None}),
        }
        other = {
            'category': 'archive',
            'stage': 'archive_error',
            'message': 'rclone 归档失败(error): boom',
            'details': json.dumps({'source_folder': 'ch', 'file_name': 'a.mp4'}),
        }
        missing = {
            'category': 'archive',
            'stage': 'archive_not_found',
            'message': 'rclone 归档失败(not_found): No PikPak file matched.',
            'details': json.dumps({'source_folder': None}),
        }
        self.assertTrue(system_log_can_retry_archive(with_item))
        self.assertTrue(system_log_can_retry_archive(live))
        self.assertFalse(system_log_can_retry_archive(other))
        self.assertFalse(system_log_can_retry_archive(missing))
        live_meta = resolve_archive_retry_meta(live)
        self.assertEqual('ch', live_meta['source_folder'])
        self.assertEqual('9 - title.mp4', live_meta['file_name'])

    def test_list_system_logs_includes_can_retry(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            retryable_id = store.add_system_log(
                'archive',
                'archive_not_found',
                'rclone 归档失败(not_found): No PikPak file matched clip.mp4.',
                level='warning',
                details={'source_folder': 'ctuxas', 'file_name': 'clip.mp4'},
            )
            store.add_system_log(
                'archive',
                'archive_success',
                'rclone 归档成功: Telegram/ctuxas/clip.mp4',
                level='info',
                details={'source_folder': 'ctuxas', 'file_name': 'clip.mp4'},
            )
            host = _ArchiveRetryHost(store, SimpleNamespace())
            payload = host.list_system_logs(limit=10)
            by_id = {entry['id']: entry for entry in payload['logs']}
            self.assertTrue(by_id[retryable_id]['can_retry'])
            self.assertFalse(any(
                entry['can_retry']
                for entry in payload['logs']
                if entry['id'] != retryable_id
            ))

    def test_retry_archive_from_system_log_recovers_deferred_item(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task(
                'https://t.me/ctuxas',
                'https://t.me/pikpak_bot',
                target_profile='pikpak',
                start_id=1,
                end_id=1,
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
                phase='forwarded',
                status=TransferStatus.SUCCESS,
            )
            log_id = store.add_system_log(
                'archive',
                'archive_not_found',
                'rclone 归档失败(not_found): No PikPak file matched 1 - 标题.mp4.',
                level='warning',
                target_link='https://t.me/ctuxas/1',
                details={
                    'source_folder': 'ctuxas',
                    'file_name': '1 - 标题.mp4',
                    'task_id': task_id,
                    'item_id': item_id,
                },
            )
            archive_calls = []

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(
                        ok=True,
                        status='success',
                        archive_path='Telegram/ctuxas/1 - 标题.mp4',
                        message='',
                    )

            host = _ArchiveRetryHost(store, FakeArchiveClient())
            result = host.retry_archive_from_system_log(log_id)

            self.assertTrue(result['ok'])
            self.assertEqual('success', result['status'])
            self.assertEqual(1, len(archive_calls))
            self.assertIsNone(archive_calls[0].get('transferred_at'))
            item = store.get_item(item_id)
            self.assertEqual('success', item['archive_status'])

    def test_retry_archive_from_system_log_live_path_without_item(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            log_id = store.add_system_log(
                'archive',
                'archive_not_found',
                'rclone 归档失败(not_found): No PikPak file matched 68043 - 片名.mp4.',
                level='warning',
                source_chat_id='-1002738448787',
                source_message_id=68043,
                target_link='https://t.me/c/2738448787/68043',
                details={'source_folder': 'ch', 'file_name': None},
            )
            archive_calls = []

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(
                        ok=True,
                        status='success',
                        archive_path='Telegram/ch/68043 - 片名.mp4',
                        message='',
                    )

            host = _ArchiveRetryHost(store, FakeArchiveClient())
            result = host.retry_archive_from_system_log(log_id)

            self.assertTrue(result['ok'])
            self.assertEqual(1, len(archive_calls))
            self.assertEqual('ch', archive_calls[0]['source_folder'])
            self.assertEqual('68043 - 片名.mp4', archive_calls[0]['file_name'])
            self.assertFalse(archive_calls[0]['match_original_name'])

    def test_retry_archive_still_not_found_raises(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            log_id = store.add_system_log(
                'archive',
                'archive_not_found',
                'rclone 归档失败(not_found): No PikPak file matched missing.mp4.',
                level='warning',
                details={'source_folder': 'ch', 'file_name': 'missing.mp4'},
            )

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    return SimpleNamespace(
                        ok=False,
                        status='not_found',
                        archive_path=None,
                        message='No PikPak file matched missing.mp4.',
                    )

            host = _ArchiveRetryHost(store, FakeArchiveClient())
            with self.assertRaises(RuntimeError) as ctx:
                host.retry_archive_from_system_log(log_id)
            self.assertIn('missing.mp4', str(ctx.exception).lower())

    def test_retry_archive_rejects_non_retryable_and_missing_log(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            log_id = store.add_system_log(
                'archive',
                'archive_ambiguous',
                'rclone 归档失败(ambiguous): many',
                level='warning',
                details={'source_folder': 'ch', 'file_name': 'a.mp4'},
            )
            host = _ArchiveRetryHost(store, SimpleNamespace(archive_file=lambda **k: None))
            with self.assertRaises(ValueError):
                host.retry_archive_from_system_log(log_id)
            with self.assertRaises(LookupError):
                host.retry_archive_from_system_log(999999)

    def test_retry_archive_dedupes_inflight(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            log_id = store.add_system_log(
                'archive',
                'archive_not_found',
                'rclone 归档失败(not_found): No PikPak file matched wait.mp4.',
                level='warning',
                source_chat_id='1',
                source_message_id=2,
                details={'source_folder': 'ch', 'file_name': 'wait.mp4'},
            )
            started = threading.Event()
            release = threading.Event()

            class SlowArchiveClient:
                def archive_file(self, **kwargs):
                    started.set()
                    release.wait(timeout=5)
                    return SimpleNamespace(
                        ok=True,
                        status='success',
                        archive_path='Telegram/ch/wait.mp4',
                        message='',
                    )

            host = _ArchiveRetryHost(store, SlowArchiveClient())
            meta = resolve_archive_retry_meta(store.get_system_log(log_id))
            self.assertEqual('msg:1:2', archive_retry_inflight_key(meta))

            errors = []

            def run_first():
                try:
                    host.retry_archive_from_system_log(log_id)
                except Exception as exc:  # pragma: no cover
                    errors.append(exc)

            worker = threading.Thread(target=run_first)
            worker.start()
            self.assertTrue(started.wait(timeout=5))
            with self.assertRaises(RuntimeError) as ctx:
                host.retry_archive_from_system_log(log_id)
            self.assertIn('progress', str(ctx.exception).lower())
            release.set()
            worker.join(timeout=5)
            self.assertEqual([], errors)

    def test_api_retry_archive_and_list_can_retry(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            log_id = store.add_system_log(
                'archive',
                'archive_not_found',
                'rclone 归档失败(not_found): No PikPak file matched api.mp4.',
                level='warning',
                details={'source_folder': 'ch', 'file_name': 'api.mp4'},
            )
            archive_calls = []

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    archive_calls.append(kwargs)
                    return SimpleNamespace(
                        ok=True,
                        status='success',
                        archive_path='Telegram/ch/api.mp4',
                        message='',
                    )

            host = _ArchiveRetryHost(store, FakeArchiveClient())
            server = WebUiServer(
                store=store,
                operations=host,
                username='admin',
                password='pass',
            )
            server.start(open_browser=False)
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                headers = self._login_headers(conn)
                conn.request('GET', '/api/system-logs?limit=10', headers=headers)
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                entry = next(item for item in body['logs'] if item['id'] == log_id)
                self.assertTrue(entry['can_retry'])

                conn.request(
                    'POST',
                    f'/api/system-logs/{log_id}/retry-archive',
                    headers=headers,
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(200, response.status)
                self.assertTrue(body['ok'])
                self.assertEqual(1, len(archive_calls))
            finally:
                server.stop()

    def test_api_retry_archive_returns_failure_body_when_still_not_found(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            log_id = store.add_system_log(
                'archive',
                'archive_not_found',
                'rclone 归档失败(not_found): No PikPak file matched gone.mp4.',
                level='warning',
                details={'source_folder': 'ch', 'file_name': 'gone.mp4'},
            )

            class FakeArchiveClient:
                def archive_file(self, **kwargs):
                    return SimpleNamespace(
                        ok=False,
                        status='not_found',
                        archive_path=None,
                        message='No PikPak file matched gone.mp4.',
                    )

            host = _ArchiveRetryHost(store, FakeArchiveClient())
            server = WebUiServer(
                store=store,
                operations=host,
                username='admin',
                password='pass',
            )
            server.start(open_browser=False)
            try:
                conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
                headers = self._login_headers(conn)
                conn.request(
                    'POST',
                    f'/api/system-logs/{log_id}/retry-archive',
                    headers=headers,
                )
                response = conn.getresponse()
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(400, response.status)
                self.assertEqual('archive_failed', body.get('error_code'))
                self.assertIn('gone.mp4', body.get('error') or '')
            finally:
                server.stop()


if __name__ == '__main__':
    unittest.main()
