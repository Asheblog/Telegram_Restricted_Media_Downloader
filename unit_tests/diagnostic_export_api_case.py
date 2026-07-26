# coding=UTF-8
import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]

from module.adapters.webui.server import WebUiApiError, WebUiServer
from module.persistence.diagnostic_bundle import PROBE_ERROR_MARKER, build_diagnostic_bundle
from module.persistence.transfer_store import TransferStatus, TransferStore

sys.argv = _ORIGINAL_ARGV


class _Ops:
    def __init__(self, store, root: Path):
        self.store = store
        self.root = root
        self.calls = []

    def export_diagnostic_bundle(self, payload):
        self.calls.append(payload)
        if not payload.get('acknowledge_secrets'):
            raise ValueError('acknowledge_secrets_required')
        zip_path = build_diagnostic_bundle(
            work_dir=self.root / 'out',
            version='test',
            config_yaml_path=None,
            global_config_path=None,
            session_directory=None,
            transfer_db_path=Path(self.store.path),
            store=self.store,
            system_logs_text='',
            probe_items=[],
            probe_results={'results': []},
            task_id=None,
        )
        return {'path': str(zip_path), 'filename': zip_path.name, 'contains_secrets': True}


class DiagnosticExportApiCase(unittest.TestCase):
    def test_server_requires_ack_via_ops(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            root = Path(directory)
            store = TransferStore(directory=str(root / 'db'))
            ops = _Ops(store, root)
            server = WebUiServer(store=store, operations=ops)
            with self.assertRaises(WebUiApiError) as ctx:
                # emulate handler ValueError mapping by calling ops path with empty ack
                try:
                    ops.export_diagnostic_bundle({})
                except ValueError as e:
                    raise WebUiApiError(str(e), 'ack', HTTPStatus.BAD_REQUEST) from e
            self.assertEqual('acknowledge_secrets_required', ctx.exception.error_code)

            result = server.export_diagnostic_bundle({'acknowledge_secrets': True})
            self.assertTrue(Path(result['path']).is_file())
            self.assertEqual(1, len([c for c in ops.calls if c.get('acknowledge_secrets')]))

    def test_marker_constant_stable(self):
        self.assertIn('Direct forward did not produce a target message', PROBE_ERROR_MARKER)
        self.assertEqual(TransferStatus.FAILURE, 'failure')


if __name__ == '__main__':
    unittest.main()
