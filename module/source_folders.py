# coding=UTF-8
import re

from typing import Optional
from urllib.parse import urlparse

from module.path_tool import validate_title


WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    *(f'COM{i}' for i in range(1, 10)),
    *(f'LPT{i}' for i in range(1, 10))
}


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


def source_folder_from_message(message, fallback_chat_id=None, fallback_link: Optional[str] = None) -> str:
    chat = getattr(message, 'chat', None)
    candidates = [
        getattr(chat, 'username', None),
        getattr(chat, 'title', None),
        getattr(chat, 'full_name', None),
        source_folder_from_link(getattr(message, 'link', None)),
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
