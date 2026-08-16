# coding=UTF-8
"""Telegram link parsing primitives (pure — no Pyrogram client).

Single source of truth for Telegram host recognition and ``t.me`` / ``tg://``
link parsing, shared by:

- ``module.utils.util``       (``extract_info_from_link`` / ``parse_link``)
- ``module.source_folders``   (``source_folder_from_link`` / ``message_id_from_telegram_link``)
- ``module.adapters.bot.guide_wizard`` (``normalize_telegram_link`` / ``to_channel_root`` / …)

Keep this module free of the Pyrogram client so callers can parse links without
a running session.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from module.core.enums import Link

TELEGRAM_HOSTS = frozenset({"t.me", "telegram.me", "telegram.dog"})

def normalize_bot_username(value: str) -> str:
    return str(value or "").strip().lstrip("@").lower()



def is_telegram_host(host: str | None) -> bool:
    """True when ``host`` is a Telegram link host (ignores a leading ``www.``)."""
    if not host:
        return False
    return host.lower().removeprefix("www.") in TELEGRAM_HOSTS


def normalize_telegram_link(text: str) -> str | None:
    """Normalize a raw user link into ``https://<host>/<path>`` or None.

    Accepts ``t.me/…``, ``telegram.me/…``, ``www.…`` and ``http://`` variants;
    strips query strings; rejects non-Telegram hosts.
    """
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("http://"):
        raw = "https://" + raw[7:]
    elif not raw.startswith("https://"):
        if raw.startswith(("t.me/", "telegram.me/", "telegram.dog/", "www.")):
            raw = "https://" + raw
        else:
            return None
    if "?" in raw:
        raw = raw.split("?", 1)[0]
    try:
        parsed = urlparse(raw)
    except ValueError:
        return None
    host = parsed.netloc.lower().removeprefix("www.")
    if host not in TELEGRAM_HOSTS:
        return None
    path = parsed.path.rstrip("/")
    if not path or path == "/":
        return None
    return f"https://{host}{path}"


def telegram_path_parts(link: str | None) -> list[str]:
    """Host-checked path segments of a Telegram link, or ``[]`` when not a valid one."""
    if not link:
        return []
    try:
        parsed = urlparse(str(link))
    except ValueError:
        return []
    # An empty netloc is tolerated (bare ``/c/...`` paths), mirroring historic
    # behavior; a present-but-foreign netloc is rejected.
    if parsed.netloc and not is_telegram_host(parsed.netloc):
        return []
    return [part for part in parsed.path.split("/") if part]


def channel_username_from_link(link: str | None) -> str | None:
    """First path segment when the link points at a public channel; else None.

    Private-channel links (``…/c/<id>/…``) yield None — they have no username
    to use as a folder name.
    """
    parts = telegram_path_parts(link)
    if not parts or parts[0] == "c":
        return None
    return parts[0]


def message_id_from_telegram_link(link: str | None) -> int | None:
    """Extract the message/post id from a ``t.me`` link, or None."""
    if not link:
        return None
    parts = telegram_path_parts(link)
    if not parts:
        return None
    try:
        if parts[0] == "c":
            if len(parts) >= 4 and parts[3].isdigit():
                return int(parts[3])
            if len(parts) >= 3 and parts[2].isdigit():
                return int(parts[2])
            return None
        if len(parts) >= 3 and parts[2].isdigit():
            return int(parts[2])
        if len(parts) >= 2 and parts[1].isdigit():
            return int(parts[1])
    except (TypeError, ValueError):
        return None
    return None


def _as_int(value, *, prefix: str = "") -> int:
    """Coerce a numeric path/query segment; raises ``ValueError`` on non-numeric."""
    try:
        return int(f"{prefix}{value}")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid numeric link segment: {value!r}") from exc


def extract_info_from_link(link: str) -> Link:
    """Parse a Telegram link into a :class:`~module.core.enums.Link`.

    Preserves the historic parser contract (``me`` / ``self`` → ``group_id``,
    public/private channel and topic layouts). Raises ``ValueError`` on
    malformed numeric segments, which ``parse_link`` surfaces as an invalid link.
    """
    if link in ("me", "self"):
        return Link(group_id=link)

    try:
        u = urlparse(link)
        paths = [p for p in u.path.split("/") if p]
        query = parse_qs(u.query)
    except ValueError:
        return Link()

    result = Link()

    if "comment" in query:
        result.group_id = paths[0]
        result.comment_id = _as_int(query["comment"][0])
    elif len(paths) == 1 and paths[0] != "c":
        result.group_id = paths[0]
    elif len(paths) == 2:
        if paths[0] == "c":
            result.group_id = _as_int(paths[1], prefix="-100")
        else:
            result.group_id = paths[0]
            result.post_id = _as_int(paths[1])
    elif len(paths) == 3:
        if paths[0] == "c":
            result.group_id = _as_int(paths[1], prefix="-100")
            result.post_id = _as_int(paths[2])
        else:
            result.group_id = paths[0]
            result.topic_id = _as_int(paths[1])
            result.post_id = _as_int(paths[2])
    elif len(paths) == 4 and paths[0] == "c":
        result.group_id = _as_int(paths[1], prefix="-100")
        result.topic_id = _as_int(paths[2])
        result.post_id = _as_int(paths[3])

    return result


def to_channel_root(link: str) -> str | None:
    """Reduce a channel or message link to its channel root (public or private)."""
    normalized = normalize_telegram_link(link)
    if not normalized:
        return None
    info = extract_info_from_link(normalized)
    if info.group_id is None:
        return None
    if isinstance(info.group_id, int):
        internal = str(info.group_id)
        if internal.startswith("-100"):
            internal = internal[4:]
        return f"https://t.me/c/{internal}"
    return f"https://t.me/{info.group_id}"


def extract_post_id(link: str) -> int | None:
    """Post/message id from a Telegram message link, or None."""
    normalized = normalize_telegram_link(link)
    if not normalized:
        return None
    info = extract_info_from_link(normalized)
    return info.post_id


def channels_match(channel_link: str, message_link: str) -> bool:
    """True when both links resolve to the same channel root."""
    left = to_channel_root(channel_link)
    right = to_channel_root(message_link)
    return bool(left and right and left.rstrip("/") == right.rstrip("/"))
