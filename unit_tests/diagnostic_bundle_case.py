# coding=UTF-8
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.persistence.diagnostic_bundle import (
    DEFAULT_PROBE_LIMIT,
    MAX_PROBE_LIMIT,
    PROBE_ERROR_MARKER,
    build_diagnostic_bundle,
    clamp_probe_limit,
    collect_session_files,
    select_probe_items,
)
from module.persistence.transfer_store import TransferStatus, TransferStore


class DiagnosticBundleCase(unittest.TestCase):
    def test_clamp_probe_limit(self):
        self.assertEqual(DEFAULT_PROBE_LIMIT, clamp_probe_limit(None))
        self.assertEqual(1, clamp_probe_limit(0))
        self.assertEqual(MAX_PROBE_LIMIT, clamp_probe_limit(999))

    def test_select_probe_items_prefers_marker_failures(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source', 'https://t.me/pikpak_bot')
            store.add_item(
                task_id=task_id,
                source_chat_id='bot-chat',
                source_message_id=1,
                source_link='https://t.me/c/1/1',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.FAILURE,
                error_message=f'{PROBE_ERROR_MARKER}: https://t.me/c/1/1',
            )
            store.add_item(
                task_id=task_id,
                source_chat_id='bot-chat',
                source_message_id=2,
                source_link='https://t.me/c/1/1',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.FAILURE,
                error_message='other failure',
            )
            store.add_item(
                task_id=task_id,
                source_chat_id='bot-chat',
                source_message_id=3,
                source_link='https://t.me/c/1/1',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.SUCCESS,
                error_message='',
            )
            selected = select_probe_items(store, task_id=task_id, limit=5)
            self.assertEqual(1, len(selected))
            self.assertEqual(1, selected[0]['source_message_id'])

    def test_build_bundle_includes_secrets_and_probe_json(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            root = Path(directory)
            config = root / 'config.yaml'
            config.write_text('api_id: 1\napi_hash: secret\n', encoding='utf-8')
            global_cfg = root / '.CONFIG.yaml'
            global_cfg.write_text('notice: true\n', encoding='utf-8')
            session_dir = root / 'sessions'
            session_dir.mkdir()
            (session_dir / 'TelegramRestrictedMediaDownloader.session').write_bytes(b'session-bytes')

            store = TransferStore(directory=str(root / 'db'))
            task_id = store.create_task('https://t.me/source', 'https://t.me/pikpak_bot')
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='7542243325',
                source_message_id=154026,
                source_link='https://t.me/c/2775073467/142125',
                target_link='https://t.me/pikpak_bot',
                status=TransferStatus.FAILURE,
                error_message=f'{PROBE_ERROR_MARKER}: https://t.me/c/2775073467/142125',
            )
            items = select_probe_items(store, task_id=task_id)
            out_dir = root / 'out'
            out_dir.mkdir()
            zip_path = build_diagnostic_bundle(
                work_dir=out_dir,
                version='0.0.0-test',
                config_yaml_path=config,
                global_config_path=global_cfg,
                session_directory=session_dir,
                transfer_db_path=Path(store.path),
                store=store,
                system_logs_text='log-line\n',
                probe_items=items,
                probe_results={'results': [{'item_id': item_id, 'copy_result': {'present': False}}]},
                task_id=task_id,
            )
            self.assertTrue(zip_path.is_file())
            with zipfile.ZipFile(zip_path, 'r') as zf:
                names = set(zf.namelist())
                self.assertIn('WARNING.txt', names)
                self.assertIn('META.json', names)
                self.assertIn('config/config.yaml', names)
                self.assertIn('config/.CONFIG.yaml', names)
                self.assertIn('session/TelegramRestrictedMediaDownloader.session', names)
                self.assertIn('transfer/transfer_tasks.sqlite3', names)
                self.assertIn(f'transfer/task_{task_id}_items.json', names)
                self.assertIn('logs/system-logs.txt', names)
                self.assertIn('probes/forward_probe.json', names)
                meta = json.loads(zf.read('META.json'))
                self.assertTrue(meta['contains_secrets'])
                self.assertEqual([item_id], meta['probe_item_ids'])
                self.assertIn('secret', zf.read('config/config.yaml').decode('utf-8'))

    def test_collect_session_files(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            root = Path(directory)
            (root / 'a.session').write_bytes(b'1')
            (root / 'a.session-journal').write_bytes(b'2')
            (root / 'ignore.txt').write_bytes(b'3')
            names = {p.name for p in collect_session_files(root)}
            self.assertEqual({'a.session', 'a.session-journal'}, names)


if __name__ == '__main__':
    unittest.main()
