# coding=UTF-8
"""把区间探测方法改为委派到 TransferRangeDetector。"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
OPS = REPO / "module" / "webops" / "operations.py"
text = OPS.read_text(encoding="utf-8")

START = "    async def detect_transfer_range_async(self, source_link: str) -> Optional[dict]:\n"
END = "    def statistics(self, tz_offset_minutes: int | None = None) -> dict:\n"
i = text.index(START)
j = text.index(END)

DELEGATE = '''    def _ensure_transfer_range_detector(self):
        """区间探测器（懒建并缓存；实现见 module.webops.transfer_range）。"""
        detector = self.__dict__.get('_transfer_range_detector_impl')
        if detector is None:
            from module.webops.transfer_range import TransferRangeDetector

            detector = TransferRangeDetector(
                app_getter=lambda: getattr(self, 'app', None),
                # 经实例解析：宿主/测试替身可覆盖 wait_for_telegram_flood。
                wait_for_telegram_flood=lambda *a, **kw: self.wait_for_telegram_flood(
                    *a, **kw
                ),
            )
            self._transfer_range_detector_impl = detector
        return detector

    async def detect_transfer_range_async(self, source_link: str) -> Optional[dict]:
        return await self._ensure_transfer_range_detector().detect_transfer_range_async(
            source_link
        )

    async def detect_transfer_range_by_history_scan(self, chat_id) -> Optional[dict]:
        return await self._ensure_transfer_range_detector().detect_transfer_range_by_history_scan(
            chat_id
        )

    async def detect_transfer_range_fast(self, chat_id) -> Optional[dict]:
        return await self._ensure_transfer_range_detector().detect_transfer_range_fast(
            chat_id
        )

    async def get_first_transfer_range_history_message(self, chat_id, limit: int = 1, **kwargs):
        return await self._ensure_transfer_range_detector().get_first_transfer_range_history_message(
            chat_id, limit=limit, **kwargs
        )

    async def iter_transfer_range_history(self, chat_id, limit: int = 100):
        async for message in self._ensure_transfer_range_detector().iter_transfer_range_history(
            chat_id, limit=limit
        ):
            yield message

'''
text = text[:i] + DELEGATE + text[j:]
OPS.write_text(text, encoding="utf-8")
print("delegated; lines:", len(text.splitlines()))
