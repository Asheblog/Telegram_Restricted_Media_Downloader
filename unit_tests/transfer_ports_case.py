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

    def test_from_host_wires_clusters_from_host_methods(self):
        from module.transfer.context import TransferPorts

        host = SimpleNamespace(
            env_save_directory=lambda *a, **kw: '/save',
            get_final_save_directory=lambda *a, **kw: '/final',
            get_final_file_path=lambda *a, **kw: '/final/f.bin',
            infer_target_profile=lambda *a, **kw: 'pikpak',
            normalize_download_upload_meta=lambda wu: {**wu, 'normalized': True},
            is_pikpak_target=lambda *a, **kw: True,
            build_transfer_upload_meta=lambda *a, **kw: {'meta': 1},
            record_transfer_download_success=lambda **kw: 'recorded',
            on_transfer_file_ready=lambda *a, **kw: 7,
            on_transfer_item_skipped=lambda *a, **kw: None,
            on_transfer_item_failed=lambda *a, **kw: None,
            on_transfer_upload_progress=lambda *a, **kw: None,
            on_transfer_upload_status=lambda *a, **kw: None,
            release_download_upload_window=lambda wu: setattr(wu, 'released', True) if False else None,
            release_transfer_local_storage=lambda wu: None,
            mark_transfer_local_storage_materialized=lambda wu: None,
            ensure_uploader=lambda: 'uploader',
            build_bot_transfer_progress_text=lambda *a, **kw: 'text',
            schedule_bot_transfer_progress_update=lambda *a, **kw: None,
            bot_task_link={'https://t.me/x/1'},
            queue=SimpleNamespace(task_done=lambda: None),
            pb=SimpleNamespace(progress=SimpleNamespace(remove_task=lambda **kw: None)),
            event=SimpleNamespace(set=lambda: None),
            create_download_task=lambda **kw: {'ok': True},
            detect_transfer_range_async=lambda link: ('a', 'b'),
        )

        ports = TransferPorts.from_host(host)

        self.assertEqual('/save', ports.paths.env_save_directory())
        self.assertEqual('pikpak', ports.target.infer_target_profile('x'))
        self.assertTrue(ports.target.is_pikpak_target('x'))
        self.assertEqual(7, ports.progress.on_transfer_file_ready('p', {}))
        self.assertEqual('text', ports.progress.build_bot_transfer_progress_text({}))
        self.assertIs(host.bot_task_link, ports.runtime.bot_task_link())
        self.assertEqual('uploader', ports.runtime.ensure_uploader())
        self.assertIs(host.queue, ports.runtime.queue())
        self.assertIs(host.pb.progress, ports.runtime.pb_progress())
        self.assertIs(host.event, ports.runtime.event())

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
