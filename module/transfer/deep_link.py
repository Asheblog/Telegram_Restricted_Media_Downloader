# coding=UTF-8
from __future__ import annotations

import asyncio
import re
import secrets
import time
from typing import Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

DeepLink = Tuple[str, str]  # (bot_username_lower, start_param)

_TME_START_RE = re.compile(
    r'(?:https?://)?(?:t\.me|telegram\.me)/([A-Za-z0-9_]+)\?start=([A-Za-z0-9_-]+)',
    re.I,
)


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


class DeepLinkResolveError(Exception):
    pass


class DeepLinkResolver:
    def __init__(
            self,
            timeout_seconds: int = 60,
            poll_interval: float = 1.5,
            min_interval_seconds: float = 30,
    ):
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval
        self.min_interval_seconds = max(float(min_interval_seconds or 0), 0.0)
        self._lock = asyncio.Lock()
        self._last_start_bot_at: float = 0.0

    @staticmethod
    def message_has_resolvable_media(message) -> bool:
        return any(getattr(message, attr, None) for attr in ('video', 'document', 'animation'))

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
    async def _collect_chat_history(client, bot_username: str, limit: int = 10) -> list:
        return [message async for message in client.get_chat_history(bot_username, limit=limit)]

    async def wait_for_media(
            self,
            client,
            bot_username: str,
            started_at: float,
            deadline: Optional[float] = None,
    ):
        if deadline is None:
            deadline = started_at + self.timeout_seconds
        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                history = await asyncio.wait_for(
                    self._collect_chat_history(client, bot_username, limit=10),
                    timeout=remaining,
                )
            except asyncio.TimeoutError:
                break
            for message in history:
                msg_date = getattr(message, 'date', None)
                ts = msg_date.timestamp() if hasattr(msg_date, 'timestamp') else float(msg_date or 0)
                if ts + 2 < started_at:  # allow small skew
                    continue
                if getattr(message, 'outgoing', False):
                    continue
                if self.message_has_resolvable_media(message):
                    return message
            sleep_for = min(self.poll_interval, max(0.0, deadline - time.time()))
            if sleep_for <= 0:
                break
            await asyncio.sleep(sleep_for)
        raise DeepLinkResolveError('资源 bot 未在超时内返回媒体')

    async def resolve(
            self,
            client,
            message,
            whitelist,
            timeout_seconds=None,
            min_interval_seconds=None,
    ) -> Optional[object]:
        """若命中白名单深链则返回 bot 媒体消息；无深链返回 None；失败抛 DeepLinkResolveError。"""
        picked = pick_whitelisted_deep_link(extract_deep_link_candidates(message), whitelist)
        if not picked:
            return None
        bot, param = picked
        async with self._lock:
            if timeout_seconds is not None:
                self.timeout_seconds = int(timeout_seconds)
            if min_interval_seconds is not None:
                self.min_interval_seconds = max(float(min_interval_seconds or 0), 0.0)
            await self._wait_min_interval()
            started_at = time.time()
            deadline = started_at + self.timeout_seconds

            async def _fetch():
                await self.start_bot(client, bot, param, deadline=deadline)
                return await self.wait_for_media(client, bot, started_at, deadline=deadline)

            try:
                media_msg = await asyncio.wait_for(_fetch(), timeout=self.timeout_seconds)
            except asyncio.TimeoutError as e:
                raise DeepLinkResolveError('资源 bot 未在超时内返回媒体') from e
            media_msg._deep_link_meta = {'bot': bot, 'start_param': param}
            return media_msg
