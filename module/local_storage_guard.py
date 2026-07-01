# coding=UTF-8
import asyncio
import os
import shutil
from typing import Callable, Optional


class LocalStorageGuard:
    """Reserve local disk capacity for download-then-upload transfer files."""

    DEFAULT_RESERVE_BYTES = 1024 * 1024 * 1024

    def __init__(
            self,
            free_space_provider: Callable[[str], int] = None,
            reserve_bytes_provider: Callable[[], int] = None
    ):
        self._free_space_provider = free_space_provider or self._disk_free_bytes
        self._reserve_bytes_provider = reserve_bytes_provider or (lambda: self.DEFAULT_RESERVE_BYTES)
        self._reservations = {}
        self._condition = None

    @staticmethod
    def _disk_free_bytes(path: str) -> int:
        probe = path
        while probe and not os.path.exists(probe):
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent
        if not probe:
            probe = os.getcwd()
        return int(shutil.disk_usage(probe).free)

    @property
    def reserved_bytes(self) -> int:
        return sum(record['size'] for record in self._reservations.values())

    @property
    def pending_bytes(self) -> int:
        return sum(
            record['size']
            for record in self._reservations.values()
            if not record['materialized']
        )

    @staticmethod
    def _normalize_size(size: Optional[int]) -> int:
        try:
            return max(0, int(size or 0))
        except (TypeError, ValueError):
            return 0

    def reserve_bytes(self) -> int:
        return self._normalize_size(self._reserve_bytes_provider())

    async def acquire(self, token: object, path: str, size: Optional[int]) -> Callable[[], None]:
        if token is None:
            token = object()
        size = self._normalize_size(size)
        if size <= 0:
            return lambda: None
        if self._condition is None:
            self._condition = asyncio.Condition()
        async with self._condition:
            while not self._can_fit(path, size, token):
                await self._condition.wait()
            self._reservations[token] = {'size': size, 'materialized': False}
        released = False

        def release() -> None:
            nonlocal released
            if released:
                return
            released = True
            if self._reservations.pop(token, None) is None:
                return
            self._notify()

        return release

    def release(self, token: object) -> None:
        if token is None:
            return
        if self._reservations.pop(token, None) is not None:
            self._notify()

    def notify_limit_changed(self) -> None:
        self._notify()

    def mark_materialized(self, token: object) -> None:
        if token is None:
            return
        record = self._reservations.get(token)
        if not record:
            return
        record['materialized'] = True
        self._notify()

    def _can_fit(self, path: str, size: int, token: object) -> bool:
        current = self._reservations.get(token)
        current_token_size = current['size'] if current and not current['materialized'] else 0
        projected_reserved = self.pending_bytes - current_token_size + size
        free_bytes = self._free_space_provider(path)
        return free_bytes - projected_reserved >= self.reserve_bytes()

    def _notify(self) -> None:
        if self._condition is None:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        async def notify_waiters() -> None:
            async with self._condition:
                self._condition.notify_all()

        loop.create_task(notify_waiters())
