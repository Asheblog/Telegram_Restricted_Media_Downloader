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


if __name__ == '__main__':
    unittest.main()
