import asyncio
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / 'module' / 'async_window.py'
SPEC = importlib.util.spec_from_file_location('async_window', MODULE_PATH)
async_window = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(async_window)
DynamicAsyncWindow = async_window.DynamicAsyncWindow


class DynamicAsyncWindowTest(unittest.IsolatedAsyncioTestCase):
    async def test_waits_until_a_slot_is_released(self):
        window = DynamicAsyncWindow(lambda: 2, minimum=1, maximum=5)

        release_one = await window.acquire()
        release_two = await window.acquire()

        waiter = asyncio.create_task(window.acquire())
        await asyncio.sleep(0)

        self.assertFalse(waiter.done())
        self.assertEqual(window.active_count, 2)

        release_one()
        release_one()
        release_three = await asyncio.wait_for(waiter, timeout=0.2)

        self.assertEqual(window.active_count, 2)

        release_two()
        release_three()

        self.assertEqual(window.active_count, 0)

    async def test_limit_can_grow_while_tasks_are_waiting(self):
        state = {'limit': 1}
        window = DynamicAsyncWindow(lambda: state['limit'], minimum=1, maximum=5)

        release_one = await window.acquire()
        waiter = asyncio.create_task(window.acquire())
        await asyncio.sleep(0)

        self.assertFalse(waiter.done())

        state['limit'] = 2
        window.notify_limit_changed()
        release_two = await asyncio.wait_for(waiter, timeout=0.2)

        self.assertEqual(window.active_count, 2)

        release_one()
        release_two()

    def test_limit_is_clamped_to_allowed_range(self):
        too_low = DynamicAsyncWindow(lambda: 0, minimum=1, maximum=5)
        too_high = DynamicAsyncWindow(lambda: 99, minimum=1, maximum=5)
        invalid = DynamicAsyncWindow(lambda: 'bad', minimum=1, maximum=5)

        self.assertEqual(too_low.current_limit, 1)
        self.assertEqual(too_high.current_limit, 5)
        self.assertEqual(invalid.current_limit, 1)

