# coding=UTF-8
from __future__ import annotations

import asyncio
import logging
import re
import secrets
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlparse

DeepLink = Tuple[str, str]  # (bot_username_lower, start_param)

_TME_START_RE = re.compile(
    r'(?:https?://)?(?:t\.me|telegram\.me)/([A-Za-z0-9_]+)\?start=([A-Za-z0-9_-]+)',
    re.I,
)

_RESOLVABLE_MEDIA_ATTRS = ('video', 'document', 'animation', 'photo')

_NEXT_RE = re.compile(r'(下一页|next\b|▶️|▶|»|››?)', re.I)
_PREV_RE = re.compile(r'(上一页|previous\b|prev\b|◀️|◀|«|‹‹?)', re.I)
_GROUP_RE = re.compile(
    r'^(?:(?:[\U0001F300-\U0001FAFF\u2600-\u27BF]|\ufe0f|\u200d)*)\s*(\d{1,3})\s*$',
)
_PAGE_STATUS_RE = re.compile(
    r'(?:(\d+)\s*-\s*)?(\d+)\s*/\s*(\d+)',
)

# 资源 bot 业务会话失败文案（命中后可再 StartBot）。
# 硬标记：无论是否已有媒体，整波作废（预览图 + 超时文案）。
_HARD_SESSION_FAILURE_MARKERS = (
    '会话已超时关闭',
    '会话超时',
)
# 软标记：仅在本波无媒体或仅有 photo（预览）时作废并重试。
# 已有 video/document/animation 时视为正常收尾（见 3b37e9c），保留已收媒体，避免误伤。
_SOFT_SESSION_FAILURE_MARKERS = (
    '会话已关闭',
    '会话已退出',
)
_SESSION_FAILURE_MARKERS = _HARD_SESSION_FAILURE_MARKERS + _SOFT_SESSION_FAILURE_MARKERS
_MAX_START_BOT_ATTEMPTS = 3
_SESSION_FAILURE_MESSAGE = '资源 bot 会话已超时关闭'
# 预览图 settle 后「会话已超时关闭」常晚到几十到数百毫秒；终检只查一次会漏掉并误标成功。
_POST_SETTLE_SESSION_GRACE_SECONDS = 2.0
DEEP_LINK_NO_LINK_AWAIT_COMMENT_MESSAGE = (
    '主贴无白名单深链，不转发封面，交由评论区取片'
)
DEEP_LINK_NO_LINK_FAILURE_MESSAGE = (
    '消息无白名单深链，未向资源 bot 取片（请开启包含评论区，或确认主贴/评论含白名单深链）'
)
_NON_PREVIEW_MEDIA_ATTRS = ('video', 'document', 'animation')

log = logging.getLogger('deep_link')


def text_has_hard_session_failure(text) -> bool:
    raw = str(text or '')
    if not raw:
        return False
    return any(marker in raw for marker in _HARD_SESSION_FAILURE_MARKERS)


def text_has_soft_session_failure(text) -> bool:
    raw = str(text or '')
    if not raw:
        return False
    return any(marker in raw for marker in _SOFT_SESSION_FAILURE_MARKERS)


def text_has_session_failure(text) -> bool:
    return text_has_hard_session_failure(text) or text_has_soft_session_failure(text)


@dataclass(frozen=True)
class PaginationClickTarget:
    message: object
    callback_data: bytes
    kind: str  # 'next' | 'group'
    button_text: str = ''


def normalize_bot_username(value: str) -> str:
    return str(value or '').strip().lstrip('@').lower()


def parse_deep_link_url(url: str) -> Optional[DeepLink]:
    raw = str(url or '').strip()
    if not raw:
        return None
    if raw.lower().startswith('tg://'):
        parsed = urlparse(raw)
        qs = parse_qs(parsed.query)
        domain = (qs.get('domain') or [None])[0]
        start = (qs.get('start') or [None])[0]
        if domain and start:
            return normalize_bot_username(domain), str(start)
        return None
    m = _TME_START_RE.search(raw)
    if not m:
        return None
    return normalize_bot_username(m.group(1)), m.group(2)


def _iter_button_urls(message) -> List[str]:
    urls = []
    markup = getattr(message, 'reply_markup', None)
    keyboard = getattr(markup, 'inline_keyboard', None) or []
    for row in keyboard:
        for btn in row or []:
            url = getattr(btn, 'url', None)
            if url:
                urls.append(str(url))
    return urls


def _iter_text_urls(message) -> List[str]:
    urls = []
    for text_attr, ent_attr in (('text', 'entities'), ('caption', 'caption_entities')):
        text = getattr(message, text_attr, None) or ''
        entities = getattr(message, ent_attr, None) or []
        for ent in entities:
            url = getattr(ent, 'url', None)
            if url:
                urls.append(str(url))
            elif getattr(ent, 'type', None) and 'url' in str(getattr(ent, 'type', '')).lower():
                offset = int(getattr(ent, 'offset', 0) or 0)
                length = int(getattr(ent, 'length', 0) or 0)
                urls.append(text[offset:offset + length])
        for m in _TME_START_RE.finditer(str(text)):
            urls.append(m.group(0))
    return urls


def extract_deep_link_candidates(message) -> List[DeepLink]:
    ordered: List[DeepLink] = []
    seen = set()
    for url in _iter_button_urls(message) + _iter_text_urls(message):
        parsed = parse_deep_link_url(url)
        if not parsed or parsed in seen:
            continue
        seen.add(parsed)
        ordered.append(parsed)
    return ordered


def pick_whitelisted_deep_link(
        candidates: Iterable[DeepLink],
        whitelist: Iterable[str],
) -> Optional[DeepLink]:
    allowed = {normalize_bot_username(x) for x in (whitelist or []) if normalize_bot_username(x)}
    if not allowed:
        return None
    for bot, param in candidates:
        if bot in allowed:
            return bot, param
    return None


def message_has_whitelisted_deep_link(message, whitelist: Iterable[str]) -> bool:
    return pick_whitelisted_deep_link(extract_deep_link_candidates(message), whitelist) is not None


def normalize_resolved_messages(resolved) -> Optional[List[object]]:
    """Normalize resolver output to a message list (None = no deep link)."""
    if resolved is None:
        return None
    if isinstance(resolved, list):
        return resolved or None
    return [resolved]


def messages_after_deep_link_resolve(
        *,
        resolve_enabled: bool,
        source_message,
        resolved_list: Optional[List[object]],
) -> Optional[List[object]]:
    """选择实际转发的消息列表。

    开启深链取片时：仅转发 bot 回传；无白名单深链（resolved_list is None）则返回 None，
    表示不转发频道封面（不回退预览），由调用方继续评论区取片或标失败。
    未开启时：原样转发来源消息。
    """
    if not resolve_enabled:
        return [source_message]
    if resolved_list is None:
        return None
    return resolved_list


def classify_pagination_button(text: str) -> str:
    """Classify inline button label: next|prev|status|group|other."""
    raw = str(text or '').strip()
    if not raw:
        return 'other'
    if _PREV_RE.search(raw):
        return 'prev'
    if _NEXT_RE.search(raw):
        return 'next'
    if _PAGE_STATUS_RE.search(raw) and ('/' in raw):
        # Status-like "1/2" or "1-2/2" without next/prev wording.
        if not _GROUP_RE.match(raw):
            return 'status'
    if _GROUP_RE.match(raw):
        return 'group'
    return 'other'


def parse_group_button(text: str) -> Optional[Tuple[int, bool]]:
    """Return (group_number, is_marked) for group labels; else None."""
    raw = str(text or '').strip()
    m = _GROUP_RE.match(raw)
    if not m:
        return None
    return int(m.group(1)), not re.fullmatch(r'\d{1,3}', raw)


def group_button_number(text: str) -> Optional[int]:
    parsed = parse_group_button(text)
    return parsed[0] if parsed else None


def group_button_is_marked(text: str) -> bool:
    """True when group label has a current/visited marker (e.g. ❄️ 1 / ✅2)."""
    parsed = parse_group_button(text)
    return bool(parsed and parsed[1])


def group_button_is_current_mark(text: str) -> bool:
    """True when label looks like the active page marker (❄/❄️), not merely visited (✅)."""
    raw = str(text or '').strip()
    parsed = parse_group_button(raw)
    if not parsed or not parsed[1]:
        return False
    return '❄' in raw


def page_status_total(text: str) -> Optional[int]:
    m = _PAGE_STATUS_RE.search(str(text or ''))
    if not m:
        return None
    total = int(m.group(3))
    return total if total > 0 else None


def is_last_page_status_text(text: str) -> bool:
    """True when page indicator shows we are already on the last page."""
    m = _PAGE_STATUS_RE.search(str(text or ''))
    if not m:
        return False
    end = int(m.group(2))
    total = int(m.group(3))
    return total > 0 and end >= total


def _normalize_callback_data(data) -> Optional[bytes]:
    if data is None:
        return None
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, str):
        return data.encode('utf-8')
    return None


def _iter_callback_buttons(message) -> List[Tuple[str, bytes]]:
    markup = getattr(message, 'reply_markup', None)
    keyboard = getattr(markup, 'inline_keyboard', None) or []
    out: List[Tuple[str, bytes]] = []
    for row in keyboard:
        for btn in row or []:
            data = _normalize_callback_data(getattr(btn, 'callback_data', None))
            if not data:
                continue
            text = str(getattr(btn, 'text', None) or '')
            out.append((text, data))
    return out


def pick_pagination_click_target(
        messages: Iterable[object],
        clicked_callback_data: Optional[Set[bytes]] = None,
        *,
        has_media: bool = False,
) -> Optional[PaginationClickTarget]:
    """Pick next pagination/group callback to click from recent bot messages.

    When media is already collected, skip the marked current group (e.g. ❄️ 1)
    and prefer a higher group number or 「下一页」— re-clicking the current page
    yields no new media and would stop pagination early.
    """
    clicked = clicked_callback_data or set()
    for message in messages:
        buttons = _iter_callback_buttons(message)
        if not buttons:
            continue
        groups: List[PaginationClickTarget] = []
        nexts: List[PaginationClickTarget] = []
        on_last_page = False
        status_total: Optional[int] = None
        snowflake_current: Optional[int] = None
        first_marked: Optional[int] = None
        for text, data in buttons:
            kind = classify_pagination_button(text)
            if kind == 'status':
                total = page_status_total(text)
                if total is not None:
                    status_total = total
                if is_last_page_status_text(text):
                    on_last_page = True
            if kind == 'group':
                parsed = parse_group_button(text)
                if parsed and parsed[1]:
                    num, _marked = parsed
                    if first_marked is None:
                        first_marked = num
                    if snowflake_current is None and group_button_is_current_mark(text):
                        snowflake_current = num
            if data in clicked:
                continue
            if kind == 'group':
                groups.append(PaginationClickTarget(
                    message=message, callback_data=data, kind='group', button_text=text,
                ))
            elif kind == 'next':
                nexts.append(PaginationClickTarget(
                    message=message, callback_data=data, kind='next', button_text=text,
                ))
        current_group_num = (
            snowflake_current if snowflake_current is not None else first_marked
        )
        if has_media:
            # 发片机「📋 1-3/3」表示页码条范围，不等于内容已在末页；
            # 有当前组别时用 current/total 判断是否还可点「下一页」。
            if current_group_num is not None and status_total is not None:
                on_last_page = current_group_num >= status_total
            forward_groups = []
            for target in groups:
                num = group_button_number(target.button_text)
                if num is None:
                    continue
                if current_group_num is not None and num <= current_group_num:
                    continue
                forward_groups.append(target)
            if forward_groups:
                return forward_groups[0]
            if nexts and not on_last_page:
                return nexts[0]
            continue
        if groups:
            return groups[0]
        if nexts and not on_last_page:
            return nexts[0]
    return None


class DeepLinkResolveError(Exception):
    pass


class DeepLinkSessionFailure(Exception):
    """资源 bot 业务会话失败；resolve 内可重试，耗尽后升为 DeepLinkResolveError。"""


class DeepLinkResolver:
    def __init__(
            self,
            timeout_seconds: int = 60,
            poll_interval: float = 1.5,
            min_interval_seconds: float = 30,
            settle_seconds: float = 3.0,
            max_pages: int = 20,
            page_click_interval_seconds: float = 1.0,
    ):
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval
        self.min_interval_seconds = max(float(min_interval_seconds or 0), 0.0)
        self.settle_seconds = max(float(settle_seconds or 0), 0.0)
        self.max_pages = max(int(max_pages or 1), 1)
        self.page_click_interval_seconds = max(float(page_click_interval_seconds or 0), 0.0)
        self._lock = asyncio.Lock()
        self._last_start_bot_at: float = 0.0

    @staticmethod
    def message_has_resolvable_media(message) -> bool:
        if message is None or bool(getattr(message, 'empty', False)):
            return False
        return any(getattr(message, attr, None) for attr in _RESOLVABLE_MEDIA_ATTRS)

    @classmethod
    def message_has_session_failure(cls, message) -> bool:
        if message is None or bool(getattr(message, 'empty', False)):
            return False
        if bool(getattr(message, 'outgoing', False)):
            return False
        return (
            text_has_session_failure(getattr(message, 'text', None))
            or text_has_session_failure(getattr(message, 'caption', None))
        )

    @staticmethod
    def collected_is_preview_only(collected: Optional[dict]) -> bool:
        """True when wave is empty or only photo media (no video/document/animation)."""
        if not collected:
            return True
        for message in collected.values():
            if any(getattr(message, attr, None) for attr in _NON_PREVIEW_MEDIA_ATTRS):
                return False
        return True

    def _history_triggers_session_failure(
            self,
            history: list,
            started_at: float,
            collected: Optional[dict] = None,
    ) -> bool:
        """硬标记始终触发；软标记仅在预览波（无片或仅 photo）时触发。"""
        saw_hard = False
        saw_soft = False
        for message in history:
            ts = self._message_timestamp(message)
            if ts + 2 < started_at:  # allow small skew
                continue
            if bool(getattr(message, 'outgoing', False)):
                continue
            text = getattr(message, 'text', None)
            caption = getattr(message, 'caption', None)
            if text_has_hard_session_failure(text) or text_has_hard_session_failure(caption):
                saw_hard = True
            if text_has_soft_session_failure(text) or text_has_soft_session_failure(caption):
                saw_soft = True
        if saw_hard:
            return True
        if saw_soft and self.collected_is_preview_only(collected):
            return True
        return False

    def _history_has_session_failure(self, history: list, started_at: float) -> bool:
        """兼容旧调用：无 collected 时按预览波处理（软标记也会触发）。"""
        return self._history_triggers_session_failure(history, started_at, collected=None)

    @staticmethod
    def _message_timestamp(message) -> float:
        msg_date = getattr(message, 'date', None)
        if hasattr(msg_date, 'timestamp'):
            return float(msg_date.timestamp())
        return float(msg_date or 0)

    @staticmethod
    def _message_key(message) -> Tuple:
        msg_id = getattr(message, 'id', None)
        chat = getattr(message, 'chat', None)
        chat_id = getattr(chat, 'id', None)
        if msg_id is not None:
            return chat_id, int(msg_id)
        return chat_id, id(message)

    @staticmethod
    def _media_fingerprint(message) -> Optional[str]:
        """Stable content key for bot media; prefers file_unique_id over file_id."""
        for attr in _RESOLVABLE_MEDIA_ATTRS:
            media = getattr(message, attr, None)
            if media is None:
                continue
            # pyrogram photo may be a list of sizes; use the last (largest) entry.
            if attr == 'photo' and isinstance(media, (list, tuple)) and media:
                media = media[-1]
            unique = getattr(media, 'file_unique_id', None)
            if unique:
                return f'uid:{unique}'
            file_id = getattr(media, 'file_id', None)
            if file_id:
                return f'fid:{file_id}'
        return None

    async def _wait_min_interval(self) -> None:
        if self.min_interval_seconds <= 0 or self._last_start_bot_at <= 0:
            return
        elapsed = time.time() - self._last_start_bot_at
        remaining = self.min_interval_seconds - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)

    async def start_bot(
            self,
            client,
            bot_username: str,
            start_param: str,
            deadline: Optional[float] = None,
    ):
        from pyrogram import raw
        from pyrogram.errors import FloodWait, FloodPremiumWait
        peer = await client.resolve_peer(bot_username)
        random_id = getattr(client, 'rnd_id', None)
        while True:
            if deadline is not None and time.time() >= deadline:
                raise DeepLinkResolveError('资源 bot 未在超时内返回媒体')
            rid = random_id() if callable(random_id) else secrets.randbits(63)
            try:
                await client.invoke(
                    raw.functions.messages.StartBot(
                        bot=peer,
                        peer=peer,
                        random_id=rid,
                        start_param=start_param,
                    )
                )
                self._last_start_bot_at = time.time()
                return
            except (FloodWait, FloodPremiumWait) as e:
                amount = max(0, int(getattr(e, 'value', 0) or 0))
                if deadline is not None:
                    remaining = deadline - time.time()
                    if remaining <= 0 or amount > remaining:
                        raise DeepLinkResolveError(
                            f'资源 bot 限流，等待时间超过超时预算（需等待 {amount}s）'
                        )
                await asyncio.sleep(amount)

    @staticmethod
    async def _collect_chat_history(client, bot_username: str, limit: int = 30) -> list:
        return [message async for message in client.get_chat_history(bot_username, limit=limit)]

    def _collect_new_media(
            self,
            history: list,
            started_at: float,
            collected: dict,
            seen_fingerprints: Optional[Set[str]] = None,
    ) -> bool:
        """Merge newly seen media into collected. Returns True if any new media added."""
        fingerprints = seen_fingerprints if seen_fingerprints is not None else set()
        added = False
        for message in history:
            ts = self._message_timestamp(message)
            if ts + 2 < started_at:  # allow small skew
                continue
            if getattr(message, 'outgoing', False):
                continue
            if not self.message_has_resolvable_media(message):
                continue
            key = self._message_key(message)
            if key in collected:
                continue
            fingerprint = self._media_fingerprint(message)
            if fingerprint is not None and fingerprint in fingerprints:
                continue
            collected[key] = message
            if fingerprint is not None:
                fingerprints.add(fingerprint)
            added = True
        return added

    async def _click_callback(
            self,
            client,
            target: PaginationClickTarget,
            deadline: Optional[float] = None,
    ) -> None:
        remaining = 10.0
        if deadline is not None:
            remaining = max(0.1, min(10.0, deadline - time.time()))
            if time.time() >= deadline:
                raise TimeoutError('pagination click deadline exceeded')
        message = target.message
        chat = getattr(message, 'chat', None)
        chat_id = getattr(chat, 'id', None)
        if chat_id is None:
            chat_id = getattr(message, 'chat_id', None)
        message_id = getattr(message, 'id', None)
        click = getattr(message, 'click', None)
        if callable(click):
            await click(target.button_text or 0)
            return
        request = getattr(client, 'request_callback_answer', None)
        if not callable(request):
            raise DeepLinkResolveError('客户端不支持点击 inline 按钮')
        await request(
            chat_id,
            message_id,
            target.callback_data,
            timeout=int(max(1, remaining)),
        )

    async def _collect_wave(
            self,
            client,
            bot_username: str,
            started_at: float,
            collected: dict,
            clicked_callback_data: Set[bytes],
            deadline: float,
            *,
            seen_fingerprints: Optional[Set[str]] = None,
            allow_empty_for_pagination: bool = True,
            should_continue=None,
    ) -> Optional[PaginationClickTarget]:
        """Collect media until settle; return a pending click target if any."""
        first_media_at: Optional[float] = None
        last_new_at: Optional[float] = None
        pending_target: Optional[PaginationClickTarget] = None
        fingerprints = seen_fingerprints if seen_fingerprints is not None else set()

        while time.time() < deadline:
            if callable(should_continue) and not should_continue():
                break
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                history = await asyncio.wait_for(
                    self._collect_chat_history(client, bot_username, limit=50),
                    timeout=remaining,
                )
            except asyncio.TimeoutError:
                break
            now = time.time()
            # 先收媒体再判会话失败：同一波里 video +「会话已关闭」时，须先把真资源记入 collected，
            # 否则软标记会在空 collected 上误触发（回归 3b37e9c）。
            if self._collect_new_media(history, started_at, collected, fingerprints):
                if first_media_at is None:
                    first_media_at = now
                last_new_at = now
            if self._history_triggers_session_failure(history, started_at, collected):
                collected.clear()
                fingerprints.clear()
                raise DeepLinkSessionFailure(_SESSION_FAILURE_MESSAGE)

            # 只点本次 StartBot 之后的翻页/组别按钮，避免误点历史菜单提前收工。
            recent_history = [
                message for message in history
                if self._message_timestamp(message) + 2 >= started_at
            ]
            pending_target = pick_pagination_click_target(
                recent_history,
                clicked_callback_data,
                has_media=bool(collected),
            )

            if first_media_at is not None:
                if self.settle_seconds <= 0:
                    break
                if last_new_at is not None and (now - last_new_at) >= self.settle_seconds:
                    break
            elif pending_target is None and collected:
                # Prior waves already have media; this wave accepted nothing and
                # there is no pagination target — do not spin until deadline.
                break
            elif allow_empty_for_pagination and pending_target is not None:
                # Zero-media start: leave early to click pagination.
                break

            sleep_for = min(self.poll_interval, max(0.0, deadline - time.time()))
            if first_media_at is not None and self.settle_seconds > 0 and last_new_at is not None:
                until_settle = self.settle_seconds - (time.time() - last_new_at)
                if until_settle > 0:
                    sleep_for = min(sleep_for, until_settle)
            if sleep_for <= 0:
                break
            await asyncio.sleep(sleep_for)

        return pending_target

    async def wait_for_media(
            self,
            client,
            bot_username: str,
            started_at: float,
            deadline: Optional[float] = None,
    ):
        """Backward-compatible: return the first collected media message."""
        messages = await self.wait_for_media_batch(
            client, bot_username, started_at, deadline=deadline,
        )
        return messages[0]

    async def wait_for_media_batch(
            self,
            client,
            bot_username: str,
            started_at: float,
            deadline: Optional[float] = None,
            should_continue=None,
    ) -> List[object]:
        """Wait for bot media (with optional pagination), return collected messages."""
        if deadline is None:
            deadline = started_at + self.timeout_seconds
        collected: dict = {}
        seen_fingerprints: Set[str] = set()
        clicked: Set[bytes] = set()
        pages_clicked = 0

        while time.time() < deadline:
            if callable(should_continue) and not should_continue():
                break
            count_before = len(collected)
            pending = await self._collect_wave(
                client,
                bot_username,
                started_at,
                collected,
                clicked,
                deadline,
                seen_fingerprints=seen_fingerprints,
                should_continue=should_continue,
            )
            if pages_clicked > 0 and len(collected) == count_before:
                # 已有媒体时：翻页无新媒体则停翻，保留已收结果。
                # 零媒体时：可能是点了失效按钮或 bot 仍在出片，继续等到 deadline。
                if collected:
                    break
            if pages_clicked >= self.max_pages:
                break
            if pending is None:
                # _collect_wave 在无按钮时会等到 deadline（或已有媒体 settle 结束）。
                break
            if callable(should_continue) and not should_continue():
                break
            try:
                await self._click_callback(client, pending, deadline=deadline)
            except Exception as e:
                # Mark failed callback so we do not tight-loop the same dead button.
                # With zero media, continue so the next wave can wait for late media.
                clicked.add(pending.callback_data)
                log.warning(
                    'deep_link pagination click failed%s: %s',
                    ' (partial ok)' if collected else '; keep waiting for media',
                    e,
                )
                if collected:
                    break
                continue
            clicked.add(pending.callback_data)
            pages_clicked += 1
            if self.page_click_interval_seconds > 0:
                sleep_for = min(
                    self.page_click_interval_seconds,
                    max(0.0, deadline - time.time()),
                )
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)

        if not collected:
            raise DeepLinkResolveError('资源 bot 未在超时内返回媒体')
        # 收齐后终检。仅 photo 预览波做宽限轮询：图4 常在 collage 后才出「会话已超时关闭」。
        # 已有 video/document/animation 时只查一次，避免拖长成功路径。
        grace_until = time.time()
        if self.collected_is_preview_only(collected):
            grace_until = min(float(deadline), time.time() + _POST_SETTLE_SESSION_GRACE_SECONDS)
        while True:
            if callable(should_continue) and not should_continue():
                break
            remaining = max(0.05, float(deadline) - time.time())
            try:
                history = await asyncio.wait_for(
                    self._collect_chat_history(client, bot_username, limit=50),
                    timeout=remaining,
                )
            except asyncio.TimeoutError:
                history = []
            if self._history_triggers_session_failure(history, started_at, collected):
                raise DeepLinkSessionFailure(_SESSION_FAILURE_MESSAGE)
            now = time.time()
            if now >= grace_until or now >= float(deadline):
                break
            await asyncio.sleep(min(self.poll_interval, max(0.0, grace_until - now)))
        return sorted(
            collected.values(),
            key=lambda message: (
                self._message_timestamp(message),
                int(getattr(message, 'id', 0) or 0),
            ),
        )

    async def resolve(
            self,
            client,
            message,
            whitelist,
            timeout_seconds=None,
            min_interval_seconds=None,
            settle_seconds=None,
            max_pages=None,
            page_click_interval_seconds=None,
            should_continue=None,
    ) -> Optional[List[object]]:
        """若命中白名单深链则返回 bot 媒体消息列表；无深链返回 None；失败抛 DeepLinkResolveError。"""
        picked = pick_whitelisted_deep_link(extract_deep_link_candidates(message), whitelist)
        if not picked:
            return None
        bot, param = picked
        async with self._lock:
            if timeout_seconds is not None:
                self.timeout_seconds = int(timeout_seconds)
            if min_interval_seconds is not None:
                self.min_interval_seconds = max(float(min_interval_seconds or 0), 0.0)
            if settle_seconds is not None:
                self.settle_seconds = max(float(settle_seconds or 0), 0.0)
            if max_pages is not None:
                self.max_pages = max(int(max_pages or 1), 1)
            if page_click_interval_seconds is not None:
                self.page_click_interval_seconds = max(
                    float(page_click_interval_seconds or 0), 0.0,
                )
            last_session_failure: Optional[BaseException] = None
            attempts_used = 0
            interrupted = False
            for attempt in range(1, _MAX_START_BOT_ATTEMPTS + 1):
                # 仅在重试前检查暂停；首次不占用 should_continue 计数（与收片波次共用）。
                if (
                        attempt > 1
                        and callable(should_continue)
                        and not should_continue()
                ):
                    interrupted = True
                    break
                await self._wait_min_interval()
                started_at = time.time()
                deadline = started_at + self.timeout_seconds
                attempts_used = attempt
                try:
                    await self.start_bot(client, bot, param, deadline=deadline)
                    media_msgs = await self.wait_for_media_batch(
                        client,
                        bot,
                        started_at,
                        deadline=deadline,
                        should_continue=should_continue,
                    )
                except DeepLinkSessionFailure as e:
                    last_session_failure = e
                    log.warning(
                        'deep_link session failure attempt %s/%s for @%s: %s',
                        attempt,
                        _MAX_START_BOT_ATTEMPTS,
                        bot,
                        e,
                    )
                    continue
                except asyncio.TimeoutError as e:
                    raise DeepLinkResolveError('资源 bot 未在超时内返回媒体') from e
                meta = {'bot': bot, 'start_param': param}
                for media_msg in media_msgs:
                    media_msg._deep_link_meta = dict(meta)
                return media_msgs
            if last_session_failure is not None:
                if interrupted:
                    raise DeepLinkResolveError(
                        f'资源 bot 会话超时（已尝试 {attempts_used} 次后中断）'
                    ) from last_session_failure
                raise DeepLinkResolveError(
                    f'资源 bot 会话超时，已尝试 {_MAX_START_BOT_ATTEMPTS} 次仍失败'
                ) from last_session_failure
            raise DeepLinkResolveError('资源 bot 未在超时内返回媒体')
