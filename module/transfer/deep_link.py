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

log = logging.getLogger('deep_link')


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
) -> Optional[PaginationClickTarget]:
    """Pick next pagination/group callback to click from recent bot messages."""
    clicked = clicked_callback_data or set()
    for message in messages:
        buttons = _iter_callback_buttons(message)
        if not buttons:
            continue
        groups: List[PaginationClickTarget] = []
        nexts: List[PaginationClickTarget] = []
        on_last_page = False
        for text, data in buttons:
            kind = classify_pagination_button(text)
            if kind == 'status' and is_last_page_status_text(text):
                on_last_page = True
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
        if groups:
            return groups[0]
        if nexts and not on_last_page:
            return nexts[0]
    return None


class DeepLinkResolveError(Exception):
    pass


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
        return any(getattr(message, attr, None) for attr in _RESOLVABLE_MEDIA_ATTRS)

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
                        raise DeepLinkResolveError('资源 bot 未在超时内返回媒体')
                await asyncio.sleep(amount)

    @staticmethod
    async def _collect_chat_history(client, bot_username: str, limit: int = 30) -> list:
        return [message async for message in client.get_chat_history(bot_username, limit=limit)]

    def _collect_new_media(self, history: list, started_at: float, collected: dict) -> bool:
        """Merge newly seen media into collected. Returns True if any new media added."""
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
            collected[key] = message
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
            allow_empty_for_pagination: bool = True,
    ) -> Optional[PaginationClickTarget]:
        """Collect media until settle; return a pending click target if any."""
        first_media_at: Optional[float] = None
        last_new_at: Optional[float] = None
        pending_target: Optional[PaginationClickTarget] = None

        while time.time() < deadline:
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
            if self._collect_new_media(history, started_at, collected):
                if first_media_at is None:
                    first_media_at = now
                last_new_at = now

            pending_target = pick_pagination_click_target(history, clicked_callback_data)

            if first_media_at is not None:
                if self.settle_seconds <= 0:
                    break
                if last_new_at is not None and (now - last_new_at) >= self.settle_seconds:
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
    ) -> List[object]:
        """Wait for bot media (with optional pagination), return collected messages."""
        if deadline is None:
            deadline = started_at + self.timeout_seconds
        collected: dict = {}
        clicked: Set[bytes] = set()
        pages_clicked = 0

        while time.time() < deadline:
            pending = await self._collect_wave(
                client,
                bot_username,
                started_at,
                collected,
                clicked,
                deadline,
            )
            if pages_clicked >= self.max_pages:
                break
            if pending is None:
                break
            try:
                await self._click_callback(client, pending, deadline=deadline)
            except Exception as e:
                log.warning(
                    'deep_link pagination click failed (partial ok): %s',
                    e,
                )
                break
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
            await self._wait_min_interval()
            started_at = time.time()
            deadline = started_at + self.timeout_seconds

            async def _fetch():
                await self.start_bot(client, bot, param, deadline=deadline)
                return await self.wait_for_media_batch(
                    client, bot, started_at, deadline=deadline,
                )

            try:
                media_msgs = await _fetch()
            except asyncio.TimeoutError as e:
                raise DeepLinkResolveError('资源 bot 未在超时内返回媒体') from e
            meta = {'bot': bot, 'start_param': param}
            for media_msg in media_msgs:
                media_msg._deep_link_meta = dict(meta)
            return media_msgs
