# coding=UTF-8
import re

from typing import Optional, Union
from urllib.parse import urlparse

from module.path_tool import validate_title


WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    *(f'COM{i}' for i in range(1, 10)),
    *(f'LPT{i}' for i in range(1, 10))
}

POST_TITLE_BYTE_LIMIT = 60


def source_folder_from_link(link: Optional[str]) -> Optional[str]:
    if not link:
        return None
    try:
        parsed = urlparse(str(link))
    except ValueError:
        return None
    if parsed.netloc and parsed.netloc.lower() not in ('t.me', 'telegram.me', 'telegram.dog'):
        return None
    parts = [part for part in parsed.path.split('/') if part]
    if not parts or parts[0] == 'c':
        return None
    return sanitize_source_folder(parts[0])


def message_id_from_telegram_link(link: Optional[str]) -> Optional[int]:
    if not link:
        return None
    try:
        parsed = urlparse(str(link))
    except ValueError:
        return None
    if parsed.netloc and parsed.netloc.lower() not in ('t.me', 'telegram.me', 'telegram.dog'):
        return None
    parts = [part for part in parsed.path.split('/') if part]
    if not parts:
        return None
    try:
        if parts[0] == 'c':
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


def source_folder_from_message(message, fallback_chat_id=None, fallback_link: Optional[str] = None) -> str:
    chat = getattr(message, 'chat', None) if message is not None else None
    candidates = [
        getattr(chat, 'username', None),
        getattr(chat, 'title', None),
        getattr(chat, 'full_name', None),
        source_folder_from_link(getattr(message, 'link', None) if message is not None else None),
        source_folder_from_link(fallback_link),
        fallback_chat_id,
        getattr(chat, 'id', None)
    ]
    for candidate in candidates:
        folder = sanitize_source_folder(candidate)
        if folder:
            return folder
    return 'UNKNOWN_SOURCE'


def sanitize_source_folder(value, limit: int = 80) -> Optional[str]:
    if value is None:
        return None
    folder = validate_title(str(value).strip())
    folder = re.sub(r'\s+', ' ', folder).strip()
    folder = folder.strip('. ')
    if not folder:
        return None
    if folder.upper() in WINDOWS_RESERVED_NAMES:
        folder = f'_{folder}'
    if len(folder.encode('utf-8')) <= limit:
        return folder
    raw = folder.encode('utf-8')[:limit]
    return raw.decode('utf-8', errors='ignore').strip('. ') or None


def post_title_from_message(message) -> Optional[str]:
    if message is None:
        return None
    inherited_title = getattr(message, '_trmd_source_title', None)
    if isinstance(inherited_title, str) and inherited_title.strip():
        return sanitize_source_folder(inherited_title.strip(), limit=POST_TITLE_BYTE_LIMIT)
    for attr in ('caption', 'text'):
        title = getattr(message, attr, None)
        if isinstance(title, str):
            title = next((line.strip() for line in title.splitlines() if line.strip()), '')
            if title:
                return sanitize_source_folder(title, limit=POST_TITLE_BYTE_LIMIT)
    web_page = getattr(message, 'web_page', None)
    title = getattr(web_page, 'title', None)
    if isinstance(title, str) and title.strip():
        return sanitize_source_folder(title.strip(), limit=POST_TITLE_BYTE_LIMIT)
    return None


def post_folder_segment(
        message_id: Optional[Union[int, str]],
        title: Optional[str] = None,
        limit: int = 80,
) -> Optional[str]:
    if message_id is None:
        return None
    try:
        mid = str(int(message_id))
    except (TypeError, ValueError):
        mid = sanitize_source_folder(message_id, limit=limit)
        if not mid:
            return None
    title_part = sanitize_source_folder(title, limit=POST_TITLE_BYTE_LIMIT) if title else None
    if title_part:
        combined = f'{mid} - {title_part}'
        return sanitize_source_folder(combined, limit=limit) or mid
    return mid


def join_archive_source_folder(*segments: Optional[str]) -> str:
    parts = []
    for segment in segments:
        if segment is None:
            continue
        for part in str(segment).replace('\\', '/').split('/'):
            cleaned = sanitize_source_folder(part)
            if cleaned:
                parts.append(cleaned)
    return '/'.join(parts) if parts else 'UNKNOWN_SOURCE'


def channel_folder_from_archive_path(source_folder: Optional[str]) -> Optional[str]:
    if not source_folder:
        return None
    text = str(source_folder).replace('\\', '/').strip('/')
    if not text:
        return None
    return text.split('/', 1)[0] or None


def archive_source_folder(
        message=None,
        *,
        fallback_chat_id=None,
        fallback_link: Optional[str] = None,
        post_message=None,
        post_message_id: Optional[Union[int, str]] = None,
        post_title: Optional[str] = None,
) -> str:
    """Build relative archive path: {channel}/{postId - title} (post segment omitted if no id)."""
    folder_message = post_message if post_message is not None else message
    channel = source_folder_from_message(
        folder_message,
        fallback_chat_id=fallback_chat_id,
        fallback_link=fallback_link,
    )
    msg_id = post_message_id
    if msg_id is None and post_message is not None:
        msg_id = getattr(post_message, 'id', None)
    if msg_id is None and message is not None and post_message is None:
        msg_id = getattr(message, 'id', None)
    if msg_id is None:
        msg_id = message_id_from_telegram_link(
            fallback_link or (getattr(folder_message, 'link', None) if folder_message is not None else None)
        )
    title = post_title
    if title is None:
        title = post_title_from_message(folder_message if folder_message is not None else message)
    post_segment = post_folder_segment(msg_id, title)
    if not post_segment:
        return channel
    return join_archive_source_folder(channel, post_segment)


def archive_folder_has_post_title(source_folder: Optional[str]) -> bool:
    if not source_folder:
        return False
    parts = [part for part in str(source_folder).replace('\\', '/').split('/') if part]
    if len(parts) < 2:
        return False
    return ' - ' in parts[-1]


def resolve_forward_archive_source_folder(
        *,
        source_folder: Optional[str] = None,
        messages=None,
        post_message_id: Optional[Union[int, str]] = None,
        fallback_chat_id=None,
        fallback_link: Optional[str] = None,
) -> str:
    """Prefer an explicit Source Post Archive Path; enrich ID-only paths with album caption."""
    message_list = list(messages or [])
    title = None
    for message in message_list:
        title = post_title_from_message(message)
        if title:
            break
    folder_message = message_list[0] if message_list else None
    built = archive_source_folder(
        folder_message,
        fallback_chat_id=fallback_chat_id,
        fallback_link=fallback_link,
        post_message_id=post_message_id,
        post_title=title,
    )
    if not source_folder:
        return built
    if title and not archive_folder_has_post_title(source_folder):
        return built
    return source_folder


def join_local_source_folder(base_directory: str, source_folder: Optional[str]) -> str:
    import os

    if not source_folder:
        return base_directory
    parts = [part for part in str(source_folder).replace('\\', '/').split('/') if part]
    if not parts:
        return base_directory
    return os.path.join(base_directory, *parts)
