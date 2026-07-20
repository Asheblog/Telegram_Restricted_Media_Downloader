# coding=UTF-8
import os
import re

from typing import Optional, Union
from urllib.parse import urlparse

from module.path_tool import extract_full_extension, validate_title


WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    *(f'COM{i}' for i in range(1, 10)),
    *(f'LPT{i}' for i in range(1, 10))
}

POST_TITLE_CHAR_LIMIT = 120
POST_TITLE_BYTE_LIMIT = 360
# Keep every local/archive path component below common Linux NAME_MAX (255 bytes).
POST_FOLDER_SEGMENT_BYTE_LIMIT = 230

MEDIA_FILE_NAME_ATTRS = (
    'video', 'document', 'animation', 'audio', 'voice', 'video_note', 'photo'
)
GENERIC_FILE_NAME_PREFIXES = ('video_', 'photo_', 'audio_', 'animation_')
GENERIC_FILE_NAME_STEMS = frozenset({
    'video', 'photo', 'image', 'audio', 'document', 'file', 'none', 'unknown', 'animation',
})
LEADING_ID_IN_STEM = re.compile(r'^\d+[\s._-]+')
HASHTAG_TOKEN = re.compile(r'#\S+')
DATE_ONLY_LINE = re.compile(
    r'^('
    r'\d{1,2}月\d{1,2}日(\(\d+\))?'
    r'|\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?'
    r'|\d{1,2}[-/.]\d{1,2}([-/]\d{2,4})?'
    r')$'
)
NUMBERED_TITLE_LINE = re.compile(r'^\d+[\.、．]\s*\S')
BOILERPLATE_TITLE_LINES = frozenset({
    '帖子内容', '转发内容', '消息内容', '正文', '内容', 'title', 'caption',
})
# Nested under Source Channel Folder when body has no recognisable author line.
UNKNOWN_AUTHOR_FOLDER = '_未知作者'
# Marker kept as escapes so the public tree has no sensitive site name plaintext.
_POST_AUTHOR_MARKER = '\u6d77\u89d2\u793e\u533a\u4f5c\u8005'
_AUTHOR_COLON = r'[：:﹕∶꞉]'
_AUTHOR_TAG = r'[#＃@＠]'
# Prefix of an author signature line; following tokens may be one or more #tags.
POST_AUTHOR_PREFIX = re.compile(
    r'(?:'
    + _POST_AUTHOR_MARKER + r'\s*' + _AUTHOR_COLON
    + r'|作者\s*' + _AUTHOR_COLON
    + r')\s*'
)
# Kept for callers/tests that still reference the old single-capture pattern.
POST_AUTHOR_LINE = re.compile(
    r'(?:'
    + _POST_AUTHOR_MARKER + r'\s*' + _AUTHOR_COLON + r'\s*' + _AUTHOR_TAG + r'?'
    + r'|作者\s*' + _AUTHOR_COLON + r'\s*' + _AUTHOR_TAG
    + r')([^\s#＃@＠]+)'
)
_AUTHOR_TAG_TOKEN = re.compile(r'[#＃@＠]([^\s#＃@＠]+)')
_AUTHOR_BARE_TOKEN = re.compile(r'^([^\s#＃@＠]+)')
POST_FOLDER_SEGMENT_RE = re.compile(r'^\d+(?:\s+-\s+.+)?$')

# Site / topic labels that must never become Post Author folder names.
TOPIC_AUTHOR_DENYLIST = frozenset({
    '人妻', '熟女', '少妇', '乱伦', '母子', '原创', '合集', '视频', '图片',
    '国产', '无码', '有码', '自拍', '户外', '剧情', '长篇', '短篇', '调教',
    '海角社区', '海角', '社区', '俱乐部', '资源', '分享', '推荐', '更新', '标题',
})
# Brand / site labels only — uploader UIDs like ``海角_171861476401`` are allowed.
_DENIED_AUTHOR_PREFIXES = ('海角社区_',)
_HAIJIAO_UPLOADER_ID_RE = re.compile(r'^海角_\d+$')


def normalize_author_label(value: Optional[str]) -> str:
    """NFKC-normalize an author/tag label for comparison."""
    if not isinstance(value, str):
        return ''
    import unicodedata
    text = unicodedata.normalize('NFKC', value).strip()
    text = text.lstrip('#＃@＠')
    text = re.sub(r'^[\s\-—_.,，。、;；:：!！?？\'\"“”‘’（）()【】\[\]<>《》]+', '', text)
    text = re.sub(r'[\s\-—_.,，。、;；:：!！?？\'\"“”‘’（）()【】\[\]<>《》]+$', '', text)
    text = re.sub(r'\s+', '', text)
    return text.casefold()


def is_denied_post_author(value: Optional[str]) -> bool:
    """True when a label is a site/topic token, never a Post Author folder.

    ``海角社区`` / topic tags stay denied. Uploader IDs ``海角_<digits>`` are
    accepted as Post Author folder names.
    """
    key = normalize_author_label(value)
    if not key:
        return True
    if _HAIJIAO_UPLOADER_ID_RE.fullmatch(key):
        return False
    if key in TOPIC_AUTHOR_DENYLIST:
        return True
    for prefix in _DENIED_AUTHOR_PREFIXES:
        if key.startswith(normalize_author_label(prefix)):
            return True
    return False


def extract_post_author_candidates_from_text(text: Optional[str]) -> list[str]:
    """All author-line tags/names in order (may include denied site labels)."""
    if not isinstance(text, str) or not text.strip():
        return []
    out: list[str] = []
    seen: set[str] = set()
    for match in POST_AUTHOR_PREFIX.finditer(text):
        rest = text[match.end():]
        line_rest = rest.split('\n', 1)[0]
        tags = [m.group(1).strip() for m in _AUTHOR_TAG_TOKEN.finditer(line_rest)]
        if tags:
            candidates = tags
        else:
            bare = _AUTHOR_BARE_TOKEN.match(line_rest.lstrip())
            candidates = [bare.group(1).strip()] if bare else []
        for raw in candidates:
            name = raw.strip().lstrip('#＃@＠')
            if not name:
                continue
            key = normalize_author_label(name)
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(name)
    return out


def extract_post_author_from_text(text: Optional[str]) -> Optional[str]:
    """Parse post-author line; skip site/topic tags like ``#海角社区``.

    ``作者：#海角社区 #翘臀巨乳小妈`` → ``翘臀巨乳小妈``.
    """
    for candidate in extract_post_author_candidates_from_text(text):
        if not is_denied_post_author(candidate):
            return candidate
    return None


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


def _first_non_empty_line(text: Optional[str]) -> Optional[str]:
    if not isinstance(text, str):
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _is_hashtag_only_line(line: str) -> bool:
    remainder = HASHTAG_TOKEN.sub('', line)
    remainder = re.sub(r'[\s|｜,/，、\-—_]+', '', remainder)
    return not remainder


def _is_date_only_line(line: str) -> bool:
    compact = re.sub(r'\s+', '', line)
    return bool(DATE_ONLY_LINE.match(compact))


def _is_boilerplate_title_line(line: str) -> bool:
    return line.casefold() in BOILERPLATE_TITLE_LINES


def post_author_from_message(message) -> Optional[str]:
    if message is None:
        return None
    if getattr(message, 'empty', False):
        return None
    for attr in ('caption', 'text'):
        author = extract_post_author_from_text(getattr(message, attr, None))
        if author:
            return author
    web_page = getattr(message, 'web_page', None)
    if web_page is not None:
        for attr in ('title', 'description', 'display_url'):
            author = extract_post_author_from_text(getattr(web_page, attr, None))
            if author:
                return author
    return None


async def post_author_from_telegram_message(message, *, client=None, chat_id=None) -> Optional[str]:
    """Resolve author from one message, expanding media-group siblings when needed."""
    author = post_author_from_message(message)
    if author:
        return author
    if message is None or getattr(message, 'empty', False):
        return None
    group_messages = None
    get_media_group = getattr(message, 'get_media_group', None)
    if callable(get_media_group):
        try:
            group_messages = await get_media_group()
        except Exception:
            group_messages = None
    if not group_messages and client is not None and getattr(message, 'media_group_id', None):
        getter = getattr(client, 'get_media_group', None)
        if callable(getter):
            try:
                group_messages = await getter(
                    chat_id=chat_id,
                    message_id=getattr(message, 'id', None),
                )
            except Exception:
                group_messages = None
    if group_messages:
        author = post_author_from_messages(group_messages)
        if author:
            return author
    return None


def post_author_from_messages(messages) -> Optional[str]:
    for message in messages or []:
        author = post_author_from_message(message)
        if author:
            return author
    return None


def author_folder_segment(author: Optional[str]) -> str:
    if author and is_denied_post_author(author):
        return UNKNOWN_AUTHOR_FOLDER
    cleaned = sanitize_source_folder(author, limit=POST_FOLDER_SEGMENT_BYTE_LIMIT) if author else None
    if cleaned and is_denied_post_author(cleaned):
        return UNKNOWN_AUTHOR_FOLDER
    return cleaned or UNKNOWN_AUTHOR_FOLDER


def is_post_folder_segment(segment: Optional[str]) -> bool:
    if not isinstance(segment, str) or not segment.strip():
        return False
    return bool(POST_FOLDER_SEGMENT_RE.match(segment.strip()))


def message_id_from_post_folder_segment(segment: Optional[str]) -> Optional[int]:
    if not is_post_folder_segment(segment):
        return None
    head = str(segment).split(' - ', 1)[0].strip()
    try:
        return int(head)
    except (TypeError, ValueError):
        return None


def split_archive_source_folder(
        source_folder: Optional[str],
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (channel, author_or_none, post_segment_or_none).

    Legacy flat paths ``{channel}/{post}`` yield author=None.
    Nested paths ``{channel}/{author}/{post}`` yield the author segment(s).
    """
    parts = [part for part in str(source_folder or '').replace('\\', '/').split('/') if part]
    if not parts:
        return None, None, None
    channel = parts[0]
    if len(parts) == 1:
        return channel, None, None
    if is_post_folder_segment(parts[-1]):
        if len(parts) == 2:
            return channel, None, parts[1]
        return channel, '/'.join(parts[1:-1]), parts[-1]
    if len(parts) == 2:
        return channel, parts[1], None
    return channel, '/'.join(parts[1:]), None


def resolve_post_author_folder(
        *,
        message=None,
        messages=None,
        source_folder: Optional[str] = None,
        post_author: Optional[str] = None,
) -> str:
    if post_author:
        return author_folder_segment(post_author)
    author = post_author_from_messages(messages) if messages else None
    if not author:
        author = post_author_from_message(message)
    if author:
        return author_folder_segment(author)
    _channel, existing_author, _post = split_archive_source_folder(source_folder)
    if existing_author:
        return author_folder_segment(existing_author)
    return UNKNOWN_AUTHOR_FOLDER


def score_title_line(line: Optional[str]) -> float:
    """Higher is better. Non-positive means the line should not win on its own."""
    if not isinstance(line, str):
        return 0.0
    text = re.sub(r'\s+', ' ', line).strip()
    if not text:
        return 0.0
    if _is_boilerplate_title_line(text):
        return 0.0
    if POST_AUTHOR_LINE.match(text):
        return 0.0
    if _is_date_only_line(text):
        return 0.0
    if _is_hashtag_only_line(text):
        return 0.0
    score = float(min(len(text), 80))
    if '【' in text or '】' in text:
        score += 50.0
    if NUMBERED_TITLE_LINE.match(text):
        score += 40.0
    hashtag_count = len(HASHTAG_TOKEN.findall(text))
    if hashtag_count:
        plain = HASHTAG_TOKEN.sub('', text).strip()
        if len(plain) < 8:
            score *= 0.25
        else:
            score += 5.0
    cjk_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    if cjk_count:
        score += min(cjk_count, 40) * 0.5
    return score


def pick_best_title_line(text: Optional[str]) -> Optional[str]:
    if not isinstance(text, str):
        return None
    candidates = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        score = score_title_line(stripped)
        if score > 0:
            candidates.append((score, stripped))
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]
    return _first_non_empty_line(text)


def pick_best_message_title(messages) -> Optional[str]:
    best_title = None
    best_score = 0.0
    for message in messages or []:
        title = extract_message_body_title(message, allow_inherited=True)
        if not title:
            continue
        score = score_title_line(title)
        if score > best_score:
            best_score = score
            best_title = title
    return best_title


def _stem_from_media_file_name(file_name: Optional[str]) -> Optional[str]:
    if not isinstance(file_name, str):
        return None
    name = file_name.strip()
    if not name:
        return None
    extension = extract_full_extension(name)
    if extension:
        suffix = f'.{extension}'
        if name.lower().endswith(suffix.lower()):
            stem = name[: -len(suffix)]
        else:
            stem = os.path.splitext(name)[0]
    else:
        stem = os.path.splitext(name)[0]
    stem = stem.strip()
    if not stem:
        return None
    lowered = stem.casefold()
    if lowered in GENERIC_FILE_NAME_STEMS:
        return None
    if any(lowered.startswith(prefix) for prefix in GENERIC_FILE_NAME_PREFIXES):
        return None
    stem = LEADING_ID_IN_STEM.sub('', stem).strip(' ._')
    if not stem or stem.casefold() in GENERIC_FILE_NAME_STEMS:
        return None
    return stem or None


def title_from_media_file_name(message) -> Optional[str]:
    if message is None:
        return None
    for attr in MEDIA_FILE_NAME_ATTRS:
        media = getattr(message, attr, None)
        if media is None:
            continue
        stem = _stem_from_media_file_name(getattr(media, 'file_name', None))
        if stem:
            return stem
    return None


def extract_message_body_title(message, *, allow_inherited: bool = True) -> Optional[str]:
    """Raw body title: inherited/caption/text/web_page, else media file_name stem.

    Caption/text lines are scored so hashtag-only / date-only / boilerplate lines lose to
    real titles such as ``【...】`` or ``27. ...``.
    """
    if message is None:
        return None
    if allow_inherited:
        inherited_title = getattr(message, '_trmd_source_title', None)
        if isinstance(inherited_title, str) and inherited_title.strip():
            inherited = inherited_title.strip()
            # Weak inherited titles (tags/dates) must not block a better caption on this message.
            if score_title_line(inherited) > 0:
                caption_title = pick_best_title_line(getattr(message, 'caption', None))
                text_title = pick_best_title_line(getattr(message, 'text', None))
                best_local = None
                best_score = score_title_line(inherited)
                for candidate in (caption_title, text_title):
                    if not candidate:
                        continue
                    score = score_title_line(candidate)
                    if score > best_score:
                        best_score = score
                        best_local = candidate
                return best_local or inherited
    candidates = []
    for attr in ('caption', 'text'):
        title = pick_best_title_line(getattr(message, attr, None))
        if title:
            candidates.append(title)
    web_page = getattr(message, 'web_page', None)
    title = getattr(web_page, 'title', None)
    if isinstance(title, str) and title.strip():
        candidates.append(title.strip())
    file_title = title_from_media_file_name(message)
    if file_title:
        candidates.append(file_title)
    if not candidates:
        return None
    return max(candidates, key=score_title_line)


def post_title_from_message(message) -> Optional[str]:
    title = extract_message_body_title(message)
    if not title:
        return None
    return sanitize_source_folder(title[:POST_TITLE_CHAR_LIMIT], limit=POST_TITLE_BYTE_LIMIT)


def post_folder_segment(
        message_id: Optional[Union[int, str]],
        title: Optional[str] = None,
        limit: int = POST_FOLDER_SEGMENT_BYTE_LIMIT,
) -> Optional[str]:
    if message_id is None:
        return None
    try:
        mid = str(int(message_id))
    except (TypeError, ValueError):
        mid = sanitize_source_folder(message_id, limit=limit)
        if not mid:
            return None
    title_part = None
    if title:
        title_part = sanitize_source_folder(
            str(title)[:POST_TITLE_CHAR_LIMIT],
            limit=POST_TITLE_BYTE_LIMIT,
        )
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
            cleaned = sanitize_source_folder(part, limit=POST_FOLDER_SEGMENT_BYTE_LIMIT)
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
        post_author: Optional[str] = None,
        archive_by_author: bool = False,
) -> str:
    """Build relative archive path.

    Default (archive_by_author=False): ``{channel}/{postId - title}``.
    Opt-in author nesting: ``{channel}/{author}/{postId - title}``.
    """
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
    if not archive_by_author:
        if not post_segment:
            return channel
        return join_archive_source_folder(channel, post_segment)
    author = resolve_post_author_folder(
        message=folder_message if folder_message is not None else message,
        post_author=post_author,
    )
    if not post_segment:
        return join_archive_source_folder(channel, author) if channel else channel
    return join_archive_source_folder(channel, author, post_segment)


def media_group_post_message_id(messages) -> Optional[int]:
    """Canonical album post id: smallest numeric message id in the group."""
    ids = []
    for message in messages or []:
        value = getattr(message, 'id', None)
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return min(ids) if ids else None


def archive_source_folder_for_messages(
        messages,
        *,
        fallback_chat_id=None,
        fallback_link: Optional[str] = None,
        post_message_id: Optional[Union[int, str]] = None,
        archive_by_author: bool = False,
) -> str:
    """Build one Source Post Archive Path shared by all media-group members."""
    message_list = [message for message in (messages or []) if message is not None]
    if not message_list:
        return archive_source_folder(
            fallback_chat_id=fallback_chat_id,
            fallback_link=fallback_link,
            post_message_id=post_message_id,
            archive_by_author=archive_by_author,
        )
    folder_message = message_list[0]
    for message in message_list:
        chat = getattr(message, 'chat', None)
        if getattr(chat, 'username', None) or source_folder_from_link(getattr(message, 'link', None)):
            folder_message = message
            break
    return archive_source_folder(
        folder_message,
        fallback_chat_id=fallback_chat_id,
        fallback_link=fallback_link or getattr(folder_message, 'link', None),
        post_message_id=(
            post_message_id
            if post_message_id is not None
            else media_group_post_message_id(message_list)
        ),
        post_title=pick_best_message_title(message_list),
        post_author=post_author_from_messages(message_list) if archive_by_author else None,
        archive_by_author=archive_by_author,
    )


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
        archive_by_author: bool = False,
) -> str:
    """Prefer an explicit Source Post Archive Path; enrich ID-only paths with album caption."""
    message_list = list(messages or [])
    title = pick_best_message_title(message_list)
    group_post_id = (
        post_message_id
        if post_message_id is not None
        else media_group_post_message_id(message_list)
    )
    folder_message = message_list[0] if message_list else None
    author = None
    if archive_by_author:
        author = resolve_post_author_folder(
            message=folder_message,
            messages=message_list,
            source_folder=source_folder,
            post_author=post_author_from_messages(message_list),
        )
    built = archive_source_folder(
        folder_message,
        fallback_chat_id=fallback_chat_id,
        fallback_link=fallback_link,
        post_message_id=group_post_id,
        post_title=title,
        post_author=author,
        archive_by_author=archive_by_author,
    )
    if not source_folder:
        return built
    channel, _existing_author, existing_post = split_archive_source_folder(source_folder)
    if not channel:
        channel = channel_folder_from_archive_path(source_folder)

    def _join_channel_post(post_segment: Optional[str]) -> Optional[str]:
        if not channel or not post_segment:
            return None
        if archive_by_author and author:
            return join_archive_source_folder(channel, author, post_segment)
        return join_archive_source_folder(channel, post_segment)

    existing_id = None
    existing_title = None
    if existing_post:
        if ' - ' in existing_post:
            head, existing_title = existing_post.split(' - ', 1)
            existing_id = head.strip() or None
            existing_title = existing_title.strip() or None
        else:
            existing_id = existing_post.strip() or None
    # Never let a later album member rewrite the canonical post id already stored on the path.
    stable_id = existing_id if existing_id is not None else group_post_id
    if title and channel and stable_id is not None:
        if not existing_title or score_title_line(title) > score_title_line(existing_title):
            post_segment = post_folder_segment(stable_id, title)
            joined = _join_channel_post(post_segment)
            if joined:
                return joined
    if title and not archive_folder_has_post_title(source_folder):
        if channel:
            post_segment = post_folder_segment(stable_id, title)
            joined = _join_channel_post(post_segment)
            if joined:
                return joined
            if archive_by_author and author:
                return join_archive_source_folder(channel, author)
            return channel
        return built
    if archive_by_author and channel and existing_post and _existing_author is None:
        # Lift legacy flat {channel}/{post} into {channel}/{author}/{post} only when opted in.
        return join_archive_source_folder(channel, author, existing_post)
    if (
            archive_by_author
            and channel
            and existing_post
            and _existing_author
            and _existing_author != author
            and author
            and author != UNKNOWN_AUTHOR_FOLDER
    ):
        return join_archive_source_folder(channel, author, existing_post)
    return source_folder


def join_local_source_folder(base_directory: str, source_folder: Optional[str]) -> str:
    if not source_folder:
        return base_directory
    parts = []
    for part in str(source_folder).replace('\\', '/').split('/'):
        cleaned = sanitize_source_folder(part, limit=POST_FOLDER_SEGMENT_BYTE_LIMIT)
        if cleaned:
            parts.append(cleaned)
    if not parts:
        return base_directory
    return os.path.join(base_directory, *parts)
