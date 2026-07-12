# coding=UTF-8
import os
import tempfile
import time
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.media_manager import MediaManager
from module.transfer_store import TransferStatus, TransferStore


class MediaManagerCase(unittest.TestCase):
    def test_scan_transfer_items_counts_final_and_temp_files(self):
        with tempfile.TemporaryDirectory() as directory:
            final_path = os.path.join(directory, 'movie.mp4')
            temp_path = os.path.join(directory, 'movie.mp4.cache')
            active_cache_path = f'{temp_path}.temp'
            for path, data in (
                    (final_path, b'1234'),
                    (temp_path, b'12'),
                    (active_cache_path, b'123'),
            ):
                with open(path, 'wb') as file:
                    file.write(data)

            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')
            store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=1,
                source_link='https://t.me/source/1',
                target_link='https://t.me/pikpak_bot',
                file_name='movie.mp4',
                file_size=9,
                local_path=final_path,
                temp_path=temp_path,
                status=TransferStatus.FAILURE,
                phase='failure',
            )
            manager = MediaManager(store, save_directory=directory, temp_directory=directory)

            result = manager.scan_transfer_items()

            self.assertEqual(1, result['total_count'])
            self.assertEqual(9, result['total_size'])
            self.assertEqual(4, len(result['items'][0]['paths']))

    def test_scan_orphan_files_includes_temp_directory_but_keeps_paused_cache(self):
        with tempfile.TemporaryDirectory() as save_directory, tempfile.TemporaryDirectory() as temp_directory:
            orphan_path = os.path.join(temp_directory, 'orphan.bin.temp')
            paused_path = os.path.join(temp_directory, 'paused.bin.temp')
            for path in (orphan_path, paused_path):
                with open(path, 'wb') as file:
                    file.write(b'12345')
                old = time.time() - 3 * 86400
                os.utime(path, (old, old))

            store = TransferStore(directory=temp_directory)
            task_id = store.create_task('https://t.me/source/2', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.PAUSED)
            store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=2,
                source_link='https://t.me/source/2',
                target_link='https://t.me/pikpak_bot',
                file_name='paused.bin',
                temp_path=paused_path[:-len('.temp')],
                status=TransferStatus.RUNNING,
                phase='downloading',
            )
            manager = MediaManager(
                store,
                save_directory=save_directory,
                temp_directory=temp_directory,
                retention_days=1,
            )

            result = manager.scan_orphan_files()
            paths = {item['path'] for item in result['files']}

            self.assertIn(orphan_path, paths)
            self.assertNotIn(paused_path, paths)

    def test_scan_orphan_files_does_not_protect_terminal_item_paths_on_running_task(self):
        """同一任务下已终结 item 的残留不应再被活跃任务整表保护。"""
        with tempfile.TemporaryDirectory() as directory:
            leftover_path = os.path.join(directory, 'done.bin')
            active_path = os.path.join(directory, 'active.bin')
            for path in (leftover_path, active_path):
                with open(path, 'wb') as file:
                    file.write(b'12345')
                old = time.time() - 3 * 86400
                os.utime(path, (old, old))

            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/20', 'https://t.me/pikpak_bot')
            store.update_task(task_id, status=TransferStatus.RUNNING, total_items=2, assignment_completed=False)
            store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=20,
                source_link='https://t.me/source/20',
                target_link='https://t.me/pikpak_bot',
                file_name='done.bin',
                local_path=leftover_path,
                status=TransferStatus.SUCCESS,
                phase='sent',
            )
            store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=21,
                source_link='https://t.me/source/21',
                target_link='https://t.me/pikpak_bot',
                file_name='active.bin',
                local_path=active_path,
                status=TransferStatus.RUNNING,
                phase='uploading',
            )
            manager = MediaManager(
                store,
                save_directory=directory,
                temp_directory=directory,
                retention_days=1,
            )

            result = manager.scan_orphan_files()
            paths = {item['path'] for item in result['files']}

            self.assertIn(leftover_path, paths)
            self.assertNotIn(active_path, paths)

    def test_cleanup_task_files_deletes_item_paths_before_task_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            final_path = os.path.join(directory, 'media.bin')
            temp_path = os.path.join(directory, 'media.bin.cache')
            active_cache_path = f'{temp_path}.temp'
            for path in (final_path, active_cache_path):
                with open(path, 'wb') as file:
                    file.write(b'12345')

            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/3', 'https://t.me/pikpak_bot')
            store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=3,
                source_link='https://t.me/source/3',
                target_link='https://t.me/pikpak_bot',
                file_name='media.bin',
                local_path=final_path,
                temp_path=temp_path,
                status=TransferStatus.RUNNING,
                phase='uploading',
            )
            manager = MediaManager(store, save_directory=directory, temp_directory=directory)

            result = manager.cleanup_task_files(task_id)

            self.assertEqual([], result['failed'])
            self.assertEqual(1, result['total_deleted_count'])
            self.assertFalse(os.path.exists(final_path))
            self.assertFalse(os.path.exists(active_cache_path))

    def test_scan_transfer_items_includes_ghost_files_marked_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            final_path = os.path.join(directory, 'ghost.mp4')
            with open(final_path, 'wb') as file:
                file.write(b'12345')

            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/4', 'https://t.me/pikpak_bot')
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=4,
                source_link='https://t.me/source/4',
                target_link='https://t.me/pikpak_bot',
                file_name='ghost.mp4',
                local_path=final_path,
                status=TransferStatus.SUCCESS,
                phase='sent',
            )
            store.mark_item_local_file_deleted(item_id)
            manager = MediaManager(store, save_directory=directory, temp_directory=directory)

            result = manager.scan_transfer_items()

            self.assertEqual(1, result['total_count'])
            self.assertTrue(result['items'][0]['ghost'])
            self.assertTrue(result['items'][0]['file_exists'])

    def test_scan_transfer_items_includes_zombie_running_item_on_terminal_task(self):
        """任务已终结但 item 仍 running 时，媒体管理应能扫到并清理其本地文件。"""
        with tempfile.TemporaryDirectory() as directory:
            leftover_path = os.path.join(directory, 'zombie.bin')
            with open(leftover_path, 'wb') as file:
                file.write(b'12345')

            store = TransferStore(directory=directory)
            task_id = store.create_task('https://t.me/source/5', 'https://t.me/pikpak_bot')
            store.update_task(
                task_id,
                status=TransferStatus.SUCCESS,
                total_items=1,
                completed_items=1,
                assignment_completed=True,
                finished=True,
            )
            store.add_item(
                task_id=task_id,
                source_chat_id='source',
                source_message_id=5,
                source_link='https://t.me/source/5',
                target_link='https://t.me/pikpak_bot',
                file_name='zombie.bin',
                local_path=leftover_path,
                status=TransferStatus.RUNNING,
                phase='downloaded',
            )
            manager = MediaManager(store, save_directory=directory, temp_directory=directory)

            result = manager.scan_transfer_items()

            self.assertEqual(1, result['total_count'])
            self.assertEqual(leftover_path, result['items'][0]['local_path'])
            self.assertTrue(result['items'][0]['file_exists'])
            self.assertEqual(TransferStatus.RUNNING, result['items'][0]['status'])

    def test_scan_orphan_files_includes_store_directory_when_temp_directory_changed(self):
        with tempfile.TemporaryDirectory() as save_directory, tempfile.TemporaryDirectory() as old_temp_directory:
            orphan_path = os.path.join(old_temp_directory, 'leftover.bin')
            with open(orphan_path, 'wb') as file:
                file.write(b'12345')
            old = time.time() - 3 * 86400
            os.utime(orphan_path, (old, old))

            store = TransferStore(directory=old_temp_directory)
            manager = MediaManager(
                store,
                save_directory=save_directory,
                temp_directory=os.path.join(save_directory, 'new-temp'),
                retention_days=1,
            )

            result = manager.scan_orphan_files()
            paths = {item['path'] for item in result['files']}

            self.assertIn(orphan_path, paths)

    def test_auto_cleanup_orphan_files_deletes_stale_orphans(self):
        with tempfile.TemporaryDirectory() as directory:
            orphan_path = os.path.join(directory, 'stale.bin')
            with open(orphan_path, 'wb') as file:
                file.write(b'data')
            old = time.time() - 10 * 86400
            os.utime(orphan_path, (old, old))

            store = TransferStore(directory=directory)
            manager = MediaManager(
                store,
                save_directory=directory,
                temp_directory=directory,
                retention_days=7,
            )

            result = manager.auto_cleanup_orphan_files()

            self.assertEqual(1, result['total_deleted_count'])
            self.assertEqual(1, result['scanned_count'])
            self.assertFalse(os.path.exists(orphan_path))

    def test_scan_transfer_items_allows_expanded_placeholder_save_paths(self):
        """save_directory 含 %CHAT_ID% 时，展开后的实际文件仍应可被扫描清理。"""
        with tempfile.TemporaryDirectory() as save_root, tempfile.TemporaryDirectory() as store_root:
            save_template = os.path.join(save_root, 'media', '%CHAT_ID%')
            expanded_dir = os.path.join(save_root, 'media', '-100123')
            os.makedirs(expanded_dir, exist_ok=True)
            final_path = os.path.join(expanded_dir, 'movie.mp4')
            with open(final_path, 'wb') as file:
                file.write(b'12345')

            store = TransferStore(directory=store_root)
            task_id = store.create_task('https://t.me/source/6', 'https://t.me/pikpak_bot')
            store.add_item(
                task_id=task_id,
                source_chat_id='-100123',
                source_message_id=6,
                source_link='https://t.me/source/6',
                target_link='https://t.me/pikpak_bot',
                file_name='movie.mp4',
                local_path=final_path,
                status=TransferStatus.SUCCESS,
                phase='sent',
            )
            manager = MediaManager(
                store,
                save_directory=save_template,
                temp_directory=store_root,
            )

            result = manager.scan_transfer_items()

            self.assertEqual(1, result['total_count'])
            self.assertTrue(result['items'][0]['file_exists'])
            self.assertEqual(final_path, result['items'][0]['local_path'])


if __name__ == '__main__':
    unittest.main()
