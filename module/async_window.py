# coding=UTF-8
from typing import Callable


class DynamicAsyncWindow:
    def __init__(
            self,
            limit_provider: Callable[[], int],
            minimum: int = 1,
            maximum: int = 5
    ):
        if minimum > maximum:
            raise ValueError('minimum must be less than or equal to maximum.')
        self._limit_provider = limit_provider
        self._minimum = minimum
        self._maximum = maximum
        self._active_count = 0
        self._wakeup = None

    @property
    def current_limit(self) -> int:
        try:
            limit = int(self._limit_provider())
        except (TypeError, ValueError):
            limit = self._minimum
        return min(max(limit, self._minimum), self._maximum)

    @property
    def active_count(self) -> int:
        return self._active_count

    async def acquire(self) -> Callable[[], None]:
        import asyncio

        if self._wakeup is None:
            self._wakeup = asyncio.Event()
            self._wakeup.set()

        while True:
            if self._active_count < self.current_limit:
                self._active_count += 1
                released = False

                def release() -> None:
                    nonlocal released
                    if released:
                        return
                    released = True
                    if self._active_count > 0:
                        self._active_count -= 1
                    self.notify_limit_changed()

                return release

            self._wakeup.clear()
            await self._wakeup.wait()

    def notify_limit_changed(self) -> None:
        if self._wakeup is not None:
            self._wakeup.set()
