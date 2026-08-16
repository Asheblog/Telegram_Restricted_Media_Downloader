# coding=UTF-8
"""Seam tests for narrowed TransferPorts clusters."""
import sys
import unittest
from types import SimpleNamespace

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]


class TransferPortsCase(unittest.TestCase):
    """TransferPorts exposes duty clusters instead of a flat 30+ Callable bag."""

    def test_transfer_ports_exposes_duty_clusters(self):
        from module.transfer.context import (
            TransferPorts,
            TransferPathPorts,
            TransferProgressPorts,
            TransferTargetPorts,
            TransferStoragePorts,
            TransferRuntimePorts,
        )

        ports = TransferPorts()
        self.assertIsInstance(ports.paths, TransferPathPorts)
        self.assertIsInstance(ports.progress, TransferProgressPorts)
        self.assertIsInstance(ports.target, TransferTargetPorts)
        self.assertIsInstance(ports.storage, TransferStoragePorts)
        self.assertIsInstance(ports.runtime, TransferRuntimePorts)

    def test_transfer_ports_drops_unused_host_notify_callables(self):
        from module.transfer.context import TransferPorts
        from dataclasses import fields

        flat_names = set()
        for cluster_name in ('paths', 'progress', 'target', 'storage', 'runtime'):
            cluster = getattr(TransferPorts(), cluster_name)
            flat_names.update(f.name for f in fields(cluster))

        # These lived on TransferPorts but TransferEngine never called them via ports.
        for dead in (
            'notify_bot_transfer_download_progress',
            'notify_bot_transfer_downloaded',
            'notify_bot_transfer_upload_progress',
            'notify_bot_transfer_upload_status',
            'try_reuse_transfer_download_record',
            'transfer_send_interval',
        ):
            self.assertNotIn(dead, flat_names)

    def test_transfer_ports_no_longer_reflect_over_host_attributes(self):
        from module.transfer.context import TransferPorts

        self.assertFalse(hasattr(TransferPorts, "from_host"))

    def test_engine_build_download_upload_meta_uses_progress_cluster(self):
        """Behaviour lock: TransferEngine still wires upload callbacks via ports.progress."""
        from module.transfer.context import TransferContext, TransferPorts, TransferProgressPorts
        from module.transfer.engine import TransferEngine

        calls = []

        def on_ready(path, wu):
            calls.append(('ready', path))
            return 1

        ports = TransferPorts(
            progress=TransferProgressPorts(
                on_transfer_file_ready=on_ready,
                on_transfer_upload_status=lambda *a, **kw: calls.append(('status',)),
                on_transfer_upload_progress=lambda *a, **kw: calls.append(('progress',)),
                on_transfer_item_skipped=lambda *a, **kw: calls.append(('skip',)),
                on_transfer_item_failed=lambda *a, **kw: calls.append(('fail',)),
            ),
            target=__import__('module.transfer.context', fromlist=['TransferTargetPorts']).TransferTargetPorts(
                infer_target_profile=lambda *a, **kw: 'pikpak',
                is_pikpak_target=lambda *a, **kw: True,
            ),
        )
        engine = TransferEngine(
            ctx=TransferContext(gc=SimpleNamespace(upload_delete=False)),
            ports=ports,
        )
        meta = engine.build_download_upload_meta(
            target_link='https://t.me/pikpakbot',
            source_link='https://t.me/source/1',
            task_id=9,
        )
        self.assertEqual('pikpak', meta['target_profile'])
        self.assertIs(ports.progress.on_transfer_file_ready, meta['on_file_ready'])
        self.assertIs(ports.progress.on_transfer_upload_status, meta['status_callback'])
        self.assertIs(ports.progress.on_transfer_item_failed, meta['failure_callback'])
        meta['on_file_ready']('/tmp/f.bin', meta)
        self.assertEqual([('ready', '/tmp/f.bin')], calls)


if __name__ == '__main__':
    unittest.main()
