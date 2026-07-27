# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/9/25 1:22
# File:filter.py
import datetime
from typing import Optional

import pyrogram

from module.core import media_types as media_types_mod
from module.source_folders import MEDIA_FILE_NAME_ATTRS


def message_keyword_scan_text(message: pyrogram.types.Message) -> str:
    """Collect all text surfaces that can become archive titles / visible spam.

    Matches the Keyword Blacklist corpus: text, caption, inherited album title,
    web_page.title, and media file_name (full name, including extension).
    """
    parts: list[str] = []
    for attr in ('text', 'caption'):
        value = getattr(message, attr, None)
        if isinstance(value, str) and value.strip():
            parts.append(value)
    inherited = getattr(message, '_trmd_source_title', None)
    if isinstance(inherited, str) and inherited.strip():
        parts.append(inherited)
    web_page = getattr(message, 'web_page', None)
    web_title = getattr(web_page, 'title', None) if web_page is not None else None
    if isinstance(web_title, str) and web_title.strip():
        parts.append(web_title)
    for media_attr in MEDIA_FILE_NAME_ATTRS:
        media = getattr(message, media_attr, None)
        if media is None:
            continue
        file_name = getattr(media, 'file_name', None)
        if isinstance(file_name, str) and file_name.strip():
            parts.append(file_name)
    return '\n'.join(parts)


class MessageFilter:
    """共享消息过滤器，所有管线（转发、下载、监听）统一使用。

    媒体类型始终生效；enabled 总开关只控制日期与关键词。
    采用 AND 逻辑：所有启用的过滤维度都满足才放行。未启用的维度视为"通过"。
    """

    MEDIA_TYPES = media_types_mod.MEDIA_TYPES
    MEDIA_TYPES_DEFAULT = media_types_mod.MEDIA_TYPES_DEFAULT

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

    def check_pass_with_reason(
            self,
            message: pyrogram.types.Message,
            *,
            ignore_keywords: bool = False,
    ) -> tuple[bool, Optional[str]]:
        """判断消息是否通过过滤，并返回拒绝原因（若被拒绝）。

        媒体类型始终生效（不受 enabled 总开关影响）；enabled 只控制日期与关键词。
        ignore_keywords：深链评论/取回媒体跳过关键词黑名单（资源卡常含「搜索」等）。
        """
        if not self._check_media_type(message):
            enabled_types = [k for k, v in self.media_types.items() if v]
            return False, f'媒体类型不匹配(允许: {", ".join(enabled_types) or "全部"})'
        if not self.enabled:
            return True, None
        if not self._check_date_range(message):
            return False, '消息日期不在允许范围内'
        if not ignore_keywords:
            reject_keyword = self._reject_keyword(message)
            if reject_keyword:
                return False, f'命中过滤关键词: {reject_keyword}'
        return True, None

    def should_pass(
            self,
            message: pyrogram.types.Message,
            *,
            ignore_keywords: bool = False,
    ) -> bool:
        """判断消息是否通过所有启用的过滤条件。"""
        passed, _reason = self.check_pass_with_reason(
            message, ignore_keywords=ignore_keywords,
        )
        return passed

    def get_reject_reason(
            self,
            message: pyrogram.types.Message,
            *,
            ignore_keywords: bool = False,
    ) -> Optional[str]:
        """若消息被过滤则返回原因，否则返回 None。"""
        passed, reason = self.check_pass_with_reason(
            message, ignore_keywords=ignore_keywords,
        )
        if passed:
            return None
        return reason

    def _reject_keyword(self, message: pyrogram.types.Message) -> Optional[str]:
        if not self.keywords_enabled:
            return None
        words = self.keywords
        if not words:
            return None
        text_lower = message_keyword_scan_text(message).lower()
        if not text_lower:
            return None
        for keyword in words:
            if not keyword:
                continue
            if str(keyword).lower() in text_lower:
                return keyword
        return None

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
        """排除包含关键词的消息（黑名单模式）。"""
        return self._reject_keyword(message) is None

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
        """Bot/Web 会话白名单：仅匹配 text/caption（与全局 Keyword Blacklist 扫描面分离）。"""
        if not keywords:
            return True
        text = getattr(message, 'text', None) or getattr(message, 'caption', None) or ''
        if not text:
            return False
        text_lower = text.lower()
        return any(str(keyword).lower() in text_lower for keyword in keywords if keyword)


# 向后兼容别名：旧代码中用 Filter 的地方仍可工作
Filter = MessageFilter
