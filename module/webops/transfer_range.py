# coding=UTF-8
"""转存区间探测（Automatic Transfer Range）。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出：只给了频道链接、没有
消息 ID 时，探测可访问范围的最早/最晚消息以确定区间。

两条路径：
- ``detect_transfer_range_fast``：用 ``get_chat_history_count`` + 首尾各取一条，
  代价小；异常或结果不自洽时返回 None（由调用方回退）。
- ``detect_transfer_range_by_history_scan``：分页遍历全部历史，代价大但兜底。

依赖以回调注入；``wait_for_telegram_flood`` 经宿主解析（宿主/测试替身可覆盖它）。
"""
from __future__ import annotations

from typing import Callable, Optional

from pyrogram.errors import FloodPremiumWait, FloodWait

from module.utils.util import parse_link


class TransferRangeDetector:
    """自动区间探测。"""

    def __init__(
        self,
        *,
        app_getter: Callable[[], object],
        wait_for_telegram_flood: Callable[..., object],
        first_history_message: Callable[..., object],
        iter_history: Callable[..., object],
        fast_detect: Callable[..., object],
        history_scan: Callable[..., object],
        parse_link: Callable[..., object],
    ) -> None:
        self._app = app_getter
        self._wait_for_telegram_flood = wait_for_telegram_flood
        # 这些钩子必须**经宿主解析**：宿主（含测试替身）会覆盖同名方法，测试也常用
        # 字符串 patch 指向宿主模块命名空间；类内直接调自身方法、或在本模块 import
        # 函数，都会绕过覆盖（实测导致 5 个区间探测用例失败）。
        self._first_history_message = first_history_message
        self._iter_history = iter_history
        self._fast_detect = fast_detect
        self._history_scan = history_scan
        self._parse_link = parse_link

    async def detect_transfer_range_async(self, source_link: str) -> Optional[dict]:
        origin_meta = await self._parse_link(client=self._app().client, link=source_link)
        chat_id = origin_meta.get("chat_id")
        if not chat_id:
            raise ValueError("Invalid source link.")
        detected = await self._fast_detect(chat_id)
        if detected:
            return detected
        return await self._history_scan(chat_id)

    async def detect_transfer_range_by_history_scan(self, chat_id) -> Optional[dict]:
        oldest = None
        newest = None
        async for message in self._iter_history(chat_id=chat_id):
            newest = newest or message
            oldest = message
        if not newest or not oldest:
            return None
        return {
            "start_id": int(getattr(oldest, "id")),
            "end_id": int(getattr(newest, "id")),
        }

    async def detect_transfer_range_fast(self, chat_id) -> Optional[dict]:
        client = self._app().client
        history_count = getattr(client, "get_chat_history_count", None)
        if not callable(history_count):
            return None
        try:
            newest = await self._first_history_message(chat_id=chat_id, limit=1)
            if not newest:
                return None
            count = int(await history_count(chat_id))
            if count <= 1:
                oldest = newest
            else:
                oldest = await self._first_history_message(
                    chat_id=chat_id, limit=1, offset=count - 1
                )
            if not oldest:
                return None
            start_id = int(getattr(oldest, "id"))
            end_id = int(getattr(newest, "id"))
            if start_id > end_id:
                return None
            if count > 1 and start_id == end_id:
                return None
        except (FloodWait, FloodPremiumWait) as e:
            await self._wait_for_telegram_flood(e, action="detect transfer range")
            return None
        except Exception:  # noqa: BLE001 - 快速路径失败即回退扫描，不视为错误
            return None
        return {"start_id": start_id, "end_id": end_id}

    async def get_first_transfer_range_history_message(
        self, chat_id, limit: int = 1, **kwargs
    ):
        async for message in self._app().client.get_chat_history(
            chat_id=chat_id, limit=limit, **kwargs
        ):
            return message
        return None

    async def iter_transfer_range_history(self, chat_id, limit: int = 100):
        offset_id = 0
        while True:
            last_message_id = None
            try:
                async for message in self._app().client.get_chat_history(
                    chat_id=chat_id, limit=limit, offset_id=offset_id
                ):
                    last_message_id = getattr(message, "id", None)
                    yield message
            except (FloodWait, FloodPremiumWait) as e:
                await self._wait_for_telegram_flood(
                    e, action="detect transfer range"
                )
                continue
            if last_message_id is None:
                return
            next_offset_id = int(last_message_id)
            if next_offset_id <= 0 or next_offset_id == offset_id:
                return
            offset_id = next_offset_id
