# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/9/25 1:22
# File:filter.py
import datetime
from typing import Optional

import pyrogram


class MessageFilter:
    """共享消息过滤器，所有管线（转发、下载、监听）统一使用。

    采用 AND 逻辑：所有启用的过滤维度都满足才放行。未启用的维度视为"通过"。
    """

    # 支持的媒体类型列表
    MEDIA_TYPES = (
        'video', 'photo', 'audio', 'document',
        'voice', 'text', 'animation', 'video_note'
    )

    # 默认媒体类型配置（全部启用），供 GlobalConfig 和 WebUI 共享引用
    MEDIA_TYPES_DEFAULT = {t: True for t in MEDIA_TYPES}

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: message_filter 配置字典，格式与 GlobalConfig.message_filter 一致。
                    为 None 时所有过滤维度默认通过。
        """
        self._config = config or {}

    # ── 配置读取 ──

    @property
    def enabled(self) -> bool:
        """总开关。"""
        return bool(self._config.get('enabled', True))

    @property
    def media_types(self) -> dict:
        """媒体类型过滤配置 {type_name: bool}。"""
        return self._config.get('media_types', {}) or {}

    @property
    def date_range_config(self) -> dict:
        """日期范围配置 {enabled, start_date, end_date}。"""
        return self._config.get('date_range', {}) or {}

    @property
    def date_range_enabled(self) -> bool:
        return bool(self.date_range_config.get('enabled', False))

    @property
    def start_date(self) -> Optional[float]:
        return self.date_range_config.get('start_date')

    @property
    def end_date(self) -> Optional[float]:
        return self.date_range_config.get('end_date')

    @property
    def keywords_config(self) -> dict:
        """关键词配置 {enabled, words}。"""
        return self._config.get('keywords', {}) or {}

    @property
    def keywords_enabled(self) -> bool:
        return bool(self.keywords_config.get('enabled', False))

    @property
    def keywords(self) -> list:
        """启用的关键词列表。"""
        return self.keywords_config.get('words', []) or []

    # ── 主入口 ──

    def should_pass(self, message: pyrogram.types.Message) -> bool:
        """判断消息是否通过所有启用的过滤条件。

        Returns:
            True 表示消息应被处理，False 表示应跳过。
        """
        if not self.enabled:
            return True
        if not self._check_media_type(message):
            return False
        if not self._check_date_range(message):
            return False
        if not self._check_keywords(message):
            return False
        return True

    # ── 各维度检查方法 ──

    def should_pass_media_type(self, message: pyrogram.types.Message) -> bool:
        """公开方法：仅检查消息媒体类型是否在允许列表中（兼容 TransferEngine.check_type）。"""
        return self._check_media_type(message)

    def _check_media_type(self, message: pyrogram.types.Message) -> bool:
        """检查消息媒体类型是否在允许列表中。"""
        media_types = self.media_types
        if not media_types:
            return True  # 未配置则通过
        for dtype, is_allowed in media_types.items():
            if is_allowed and getattr(message, dtype, None):
                return True
        # 所有启用的类型都不匹配 → 拒绝
        enabled_types = [k for k, v in media_types.items() if v]
        if not enabled_types:
            return True  # 全部禁用 → 通过
        return False

    def _check_date_range(self, message: pyrogram.types.Message) -> bool:
        """检查消息日期是否在允许范围内。"""
        if not self.date_range_enabled:
            return True
        start = self.start_date
        end = self.end_date
        if start is None and end is None:
            return True
        msg_ts = datetime.datetime.timestamp(message.date)
        if start is not None and msg_ts < start:
            return False
        if end is not None and msg_ts > end:
            return False
        return True

    def _check_keywords(self, message: pyrogram.types.Message) -> bool:
        """检查消息文本/标题是否包含任一关键词。"""
        if not self.keywords_enabled:
            return True
        words = self.keywords
        if not words:
            return True
        text = getattr(message, 'text', None) or getattr(message, 'caption', None) or ''
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in words)

    # ── 兼容旧版 static 方法（供 download_chat 的 per-chat 过滤使用）──

    @staticmethod
    def date_range(
            message: pyrogram.types.Message,
            start_date: Optional[float],
            end_date: Optional[float]
    ) -> bool:
        if start_date and end_date:
            return start_date <= datetime.datetime.timestamp(message.date) <= end_date
        elif start_date:
            return start_date <= datetime.datetime.timestamp(message.date)
        elif end_date:
            return datetime.datetime.timestamp(message.date) <= end_date
        return True

    @staticmethod
    def dtype(
            message: pyrogram.types.Message,
            download_type: dict
    ) -> bool:
        table: list = []
        for dtype, status in download_type.items():
            if getattr(message, dtype) and status:
                table.append(True)
            table.append(False)
        if True in table:
            return True
        return False

    @staticmethod
    def keyword_filter(
            message: pyrogram.types.Message,
            keywords: Optional[list]
    ) -> bool:
        if not keywords:
            return True
        text = getattr(message, 'text') or getattr(message, 'caption') or ''
        return any(keyword.lower() in text.lower() for keyword in keywords)


# 向后兼容别名：旧代码中用 Filter 的地方仍可工作
Filter = MessageFilter
