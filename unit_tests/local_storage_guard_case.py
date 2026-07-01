# coding=UTF-8
import asyncio
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.local_storage_guard import LocalStorageGuard


class LocalStorageGuardCase(unittest.TestCase):
    def test_acquire_waits_until_materialized_file_is_released(self):
        async def run_case():
            free_space = {'value': 150}
            guard = LocalStorageGuard(
                free_space_provider=lambda _path: free_space['value'],
                reserve_bytes_provider=lambda: 50
            )
            first_release = await guard.acquire('first', '/tmp/a.bin', 100)
            guard.mark_materialized('first')
            free_space['value'] = 50
            second_started = asyncio.Event()
            second_finished = asyncio.Event()

            async def acquire_second():
                second_started.set()
                release = await guard.acquire('second', '/tmp/b.bin', 60)
                release()
                second_finished.set()

            task = asyncio.create_task(acquire_second())
            await second_started.wait()
            await asyncio.sleep(0)
            self.assertFalse(second_finished.is_set())
            free_space['value'] = 150
            first_release()
            await asyncio.wait_for(second_finished.wait(), timeout=1)
            await task

        asyncio.run(run_case())

    def test_pending_reservations_count_against_free_space(self):
        async def run_case():
            guard = LocalStorageGuard(
                free_space_provider=lambda _path: 220,
                reserve_bytes_provider=lambda: 50
            )
            release = await guard.acquire('first', '/tmp/a.bin', 100)
            self.assertEqual(100, guard.pending_bytes)
            self.assertEqual(100, guard.reserved_bytes)
            guard.mark_materialized('first')
            self.assertEqual(0, guard.pending_bytes)
            self.assertEqual(100, guard.reserved_bytes)
            release()
            self.assertEqual(0, guard.reserved_bytes)

        asyncio.run(run_case())


if __name__ == '__main__':
    unittest.main()
