# coding=UTF-8
"""Plan PikPak Source Post Archive Path moves under Post Author folders."""
from dataclasses import dataclass, field
from typing import Iterable, Optional, Union

from module.source_folders import (
    UNKNOWN_AUTHOR_FOLDER,
    author_folder_segment,
    is_denied_post_author,
    is_post_folder_segment,
    message_id_from_post_folder_segment,
    split_archive_source_folder,
)

EXECUTABLE_ACTIONS = frozenset({'move', 'needs_confirm'})
AUTO_ACTIONS = frozenset({'move'})
REVIEW_ACTIONS = frozenset({'needs_review'})


def actions_for_execute_mode(execute_mode: Optional[str] = None) -> frozenset[str]:
    """Map reorganize execute_mode to the move-row actions it may perform."""
    mode = str(execute_mode or 'all').strip().lower() or 'all'
    if mode in ('auto', 'high', 'move'):
        return AUTO_ACTIONS
    if mode in ('review', 'unknown', 'needs_review'):
        return REVIEW_ACTIONS
    return EXECUTABLE_ACTIONS


def planned_count_for_execute_mode(
        plan: Optional[dict],
        execute_mode: Optional[str] = None,
) -> int:
    """How many plan rows a given execute_mode would attempt to move."""
    if not isinstance(plan, dict):
        return 0
    actions = actions_for_execute_mode(execute_mode)
    if actions is AUTO_ACTIONS:
        return int(plan.get('move_count') or 0)
    if actions is REVIEW_ACTIONS:
        return int(plan.get('review_count') or 0)
    if plan.get('executable_count') is not None:
        return int(plan.get('executable_count') or 0)
    return int(plan.get('move_count') or 0) + int(plan.get('confirm_count') or 0)


@dataclass(frozen=True)
class AuthorHint:
    """Resolved Post Author hint for one main-post directory."""

    name: Optional[str] = None
    confidence: str = 'none'  # high | medium | low | none
    method: str = 'none'  # signature | media_group | neighbor | hashtag_* | none
    matched_tag: str = ''
    preview: str = ''


@dataclass(frozen=True)
class AuthorReorganizeMove:
    """One directory move relative to the Source Channel Folder."""

    message_id: Optional[int]
    from_relative: str
    to_relative: str
    author: str
    action: str  # move | needs_confirm | needs_review | skip_already | skip_nested | skip_invalid
    confidence: str = 'none'
    resolution_method: str = 'none'
    matched_tag: str = ''
    preview: str = ''


@dataclass
class AuthorReorganizePlan:
    channel_folder: str
    moves: list[AuthorReorganizeMove] = field(default_factory=list)

    @property
    def authors(self) -> list[str]:
        names = sorted({
            item.author
            for item in self.moves
            if item.action in ('move', 'needs_confirm', 'skip_already')
            and item.author != UNKNOWN_AUTHOR_FOLDER
        })
        return names

    @property
    def author_count(self) -> int:
        return len(self.authors)

    @property
    def move_count(self) -> int:
        return sum(1 for item in self.moves if item.action == 'move')

    @property
    def confirm_count(self) -> int:
        return sum(1 for item in self.moves if item.action == 'needs_confirm')

    @property
    def review_count(self) -> int:
        return sum(1 for item in self.moves if item.action == 'needs_review')

    @property
    def executable_count(self) -> int:
        return sum(1 for item in self.moves if item.action in EXECUTABLE_ACTIONS)

    @property
    def skip_count(self) -> int:
        return sum(
            1 for item in self.moves
            if item.action in ('skip_already', 'skip_nested', 'skip_invalid')
        )

    def summary(self) -> dict:
        counts = {
            'move': 0,
            'needs_confirm': 0,
            'needs_review': 0,
            'skip_already': 0,
            'skip_nested': 0,
            'skip_invalid': 0,
        }
        for item in self.moves:
            if item.action in counts:
                counts[item.action] += 1
        counts['executable'] = counts['move'] + counts['needs_confirm']
        counts['authors'] = self.author_count
        return counts

    def to_dict(self) -> dict:
        return {
            'channel_folder': self.channel_folder,
            'author_count': self.author_count,
            'authors': self.authors,
            'move_count': self.move_count,
            'confirm_count': self.confirm_count,
            'review_count': self.review_count,
            'executable_count': self.executable_count,
            'skip_count': self.skip_count,
            'summary': self.summary(),
            'moves': [
                {
                    'message_id': item.message_id,
                    'from_relative': item.from_relative,
                    'to_relative': item.to_relative,
                    'author': item.author,
                    'action': item.action,
                    'confidence': item.confidence,
                    'resolution_method': item.resolution_method,
                    'matched_tag': item.matched_tag,
                    'preview': item.preview,
                }
                for item in self.moves
            ],
        }


def preserved_author_hints_from_plan(plan: Optional[dict]) -> dict[int, AuthorHint]:
    """Keep already-recognized Post Authors from a prior plan.

    Rows that are ``needs_review`` or target ``_未知作者`` are left out so a
    scoped re-resolve can refetch only those message ids.
    """
    out: dict[int, AuthorHint] = {}
    if not isinstance(plan, dict):
        return out
    for item in plan.get('moves') or []:
        if not isinstance(item, dict):
            continue
        mid = item.get('message_id')
        if mid is None:
            continue
        try:
            mid_int = int(mid)
        except (TypeError, ValueError):
            continue
        action = str(item.get('action') or '')
        author = str(item.get('author') or '').strip()
        if action == 'needs_review':
            continue
        if not author or author == UNKNOWN_AUTHOR_FOLDER or is_denied_post_author(author):
            continue
        if action not in ('move', 'needs_confirm', 'skip_already', 'skip_nested'):
            continue
        out[mid_int] = AuthorHint(
            name=author,
            confidence=str(item.get('confidence') or 'high'),
            method=str(item.get('resolution_method') or item.get('method') or 'signature'),
            matched_tag=str(item.get('matched_tag') or ''),
            preview=str(item.get('preview') or ''),
        )
    return out


def coerce_author_hint(value: Union[None, str, dict, AuthorHint]) -> AuthorHint:
    if isinstance(value, AuthorHint):
        return value
    if value is None:
        return AuthorHint()
    if isinstance(value, str):
        name = value.strip() or None
        if not name:
            return AuthorHint()
        return AuthorHint(name=name, confidence='high', method='signature')
    if isinstance(value, dict):
        name = value.get('name')
        if name is not None:
            name = str(name).strip() or None
        return AuthorHint(
            name=name,
            confidence=str(value.get('confidence') or 'none'),
            method=str(value.get('method') or 'none'),
            matched_tag=str(value.get('matched_tag') or ''),
            preview=str(value.get('preview') or ''),
        )
    return AuthorHint()


def _action_for_resolved_author(hint: AuthorHint) -> str:
    if not hint.name:
        return 'needs_review'
    if (
        hint.method in ('hashtag_substring', 'hashtag_candidate')
        or hint.confidence == 'low'
    ):
        return 'needs_confirm'
    return 'move'


def _relative_under_channel(path: str, channel_folder: str) -> Optional[str]:
    text = str(path or '').replace('\\', '/').strip('/')
    prefix = f'{channel_folder.strip("/")}/'
    if text == channel_folder.strip('/'):
        return ''
    if text.startswith(prefix):
        return text[len(prefix):]
    # Entries listed as names directly under the channel.
    if '/' not in text and text:
        return text
    return None


def known_authors_from_directory_paths(
        channel_folder: str,
        directory_paths: Iterable[str],
) -> set[str]:
    """Collect Post Author folder names already present under a channel."""
    channel = str(channel_folder or '').strip().strip('/')
    known: set[str] = set()
    if not channel:
        return known
    for raw in directory_paths:
        relative = _relative_under_channel(str(raw or ''), channel)
        if not relative:
            continue
        parts = [part for part in relative.split('/') if part]
        if len(parts) >= 2 and is_post_folder_segment(parts[-1]):
            author = parts[0]
            if author and author != UNKNOWN_AUTHOR_FOLDER and not is_denied_post_author(author):
                known.add(author)
        elif len(parts) == 1 and not is_post_folder_segment(parts[0]):
            author = parts[0]
            if author and author != UNKNOWN_AUTHOR_FOLDER and not is_denied_post_author(author):
                known.add(author)
    return known


def plan_author_reorganize(
        *,
        channel_folder: str,
        directory_paths: Iterable[str],
        author_by_message_id: dict[int, Union[None, str, dict, AuthorHint]],
) -> AuthorReorganizePlan:
    """Build a move plan for flat (or misplaced) post folders under a channel.

    ``directory_paths`` may be absolute-under-archive (``channel/post``) or
    relative names (``post`` / ``author/post``). ``author_by_message_id`` maps
    Telegram main-post ids to raw author names or :class:`AuthorHint`.
    """
    channel = str(channel_folder or '').strip().strip('/')
    plan = AuthorReorganizePlan(channel_folder=channel)
    if not channel:
        return plan

    seen_targets: set[str] = set()
    for raw in directory_paths:
        relative = _relative_under_channel(str(raw or ''), channel)
        if relative is None or relative == '':
            continue
        parts = [part for part in relative.split('/') if part]
        if not parts:
            continue

        # Already nested: channel/author/post → skip when last is post folder.
        if len(parts) >= 2 and is_post_folder_segment(parts[-1]):
            author_part = '/'.join(parts[:-1])
            post_segment = parts[-1]
            message_id = message_id_from_post_folder_segment(post_segment)
            hint = coerce_author_hint(
                author_by_message_id.get(message_id) if message_id is not None else None
            )
            desired = author_folder_segment(hint.name)
            target = f'{desired}/{post_segment}'
            if author_part == desired:
                plan.moves.append(AuthorReorganizeMove(
                    message_id=message_id,
                    from_relative=relative,
                    to_relative=relative,
                    author=desired,
                    action='skip_already',
                    confidence=hint.confidence if hint.name else 'none',
                    resolution_method=hint.method if hint.name else 'none',
                    matched_tag=hint.matched_tag,
                    preview=hint.preview,
                ))
            else:
                action = _action_for_resolved_author(hint)
                if action in EXECUTABLE_ACTIONS and target in seen_targets:
                    action = 'skip_nested'
                elif action in EXECUTABLE_ACTIONS:
                    seen_targets.add(target)
                plan.moves.append(AuthorReorganizeMove(
                    message_id=message_id,
                    from_relative=relative,
                    to_relative=target,
                    author=desired,
                    action=action,
                    confidence=hint.confidence,
                    resolution_method=hint.method,
                    matched_tag=hint.matched_tag,
                    preview=hint.preview,
                ))
            continue

        # Flat legacy: channel/post
        if len(parts) == 1 and is_post_folder_segment(parts[0]):
            post_segment = parts[0]
            message_id = message_id_from_post_folder_segment(post_segment)
            hint = coerce_author_hint(
                author_by_message_id.get(message_id) if message_id is not None else None
            )
            author = author_folder_segment(hint.name)
            target = f'{author}/{post_segment}'
            action = _action_for_resolved_author(hint)
            if action in EXECUTABLE_ACTIONS and target in seen_targets:
                plan.moves.append(AuthorReorganizeMove(
                    message_id=message_id,
                    from_relative=relative,
                    to_relative=target,
                    author=author,
                    action='skip_nested',
                    confidence=hint.confidence,
                    resolution_method=hint.method,
                    matched_tag=hint.matched_tag,
                    preview=hint.preview,
                ))
                continue
            if action in EXECUTABLE_ACTIONS:
                seen_targets.add(target)
            plan.moves.append(AuthorReorganizeMove(
                message_id=message_id,
                from_relative=relative,
                to_relative=target,
                author=author,
                action=action,
                confidence=hint.confidence,
                resolution_method=hint.method,
                matched_tag=hint.matched_tag,
                preview=hint.preview,
            ))
            continue

        plan.moves.append(AuthorReorganizeMove(
            message_id=None,
            from_relative=relative,
            to_relative=relative,
            author=UNKNOWN_AUTHOR_FOLDER,
            action='skip_invalid',
        ))
    return plan


def summarize_move_rows(moves: Iterable[dict]) -> dict:
    counts = {
        'move': 0,
        'needs_confirm': 0,
        'needs_review': 0,
        'skip_already': 0,
        'skip_nested': 0,
        'skip_invalid': 0,
    }
    authors: set[str] = set()
    for item in moves:
        action = str((item or {}).get('action') or '')
        if action in counts:
            counts[action] += 1
        author = str((item or {}).get('author') or '')
        if (
            action in ('move', 'needs_confirm', 'skip_already')
            and author
            and author != UNKNOWN_AUTHOR_FOLDER
        ):
            authors.add(author)
    counts['executable'] = counts['move'] + counts['needs_confirm']
    counts['authors'] = len(authors)
    return counts


def filter_plan_moves(
        moves: list,
        *,
        bucket: str = '',
        offset: int = 0,
        limit: int = 50,
) -> dict:
    """Paginate plan moves, optionally filtered by summary bucket."""
    rows = list(moves or [])
    key = str(bucket or '').strip()
    if key == 'executable':
        rows = [item for item in rows if item.get('action') in EXECUTABLE_ACTIONS]
    elif key == 'auto':
        rows = [item for item in rows if item.get('action') in AUTO_ACTIONS]
    elif key:
        rows = [item for item in rows if item.get('action') == key]
    total = len(rows)
    try:
        offset = max(0, int(offset))
    except (TypeError, ValueError):
        offset = 0
    try:
        limit = max(1, min(200, int(limit)))
    except (TypeError, ValueError):
        limit = 50
    return {
        'items': rows[offset:offset + limit],
        'total': total,
        'offset': offset,
        'limit': limit,
        'bucket': key or None,
    }


def rewrite_transfer_source_folder(
        source_folder: Optional[str],
        *,
        channel_folder: str,
        from_relative: str,
        to_relative: str,
) -> Optional[str]:
    """Rewrite a stored Transfer Item source_folder when it matches a move."""
    if not source_folder:
        return None
    channel, author, post = split_archive_source_folder(source_folder)
    if channel != channel_folder:
        return None
    current = '/'.join(part for part in (author, post) if part)
    if not current:
        return None
    if current != from_relative.replace('\\', '/').strip('/'):
        return None
    return f'{channel_folder}/{to_relative.strip("/")}'
