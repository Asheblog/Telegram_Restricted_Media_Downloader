# coding=UTF-8
"""Plan PikPak Source Post Archive Path moves under Post Author folders."""
from dataclasses import dataclass, field
from typing import Iterable, Optional

from module.source_folders import (
    UNKNOWN_AUTHOR_FOLDER,
    author_folder_segment,
    is_post_folder_segment,
    message_id_from_post_folder_segment,
    split_archive_source_folder,
)


@dataclass(frozen=True)
class AuthorReorganizeMove:
    """One directory move relative to the Source Channel Folder."""

    message_id: Optional[int]
    from_relative: str
    to_relative: str
    author: str
    action: str  # move | skip_already | skip_nested | skip_invalid


@dataclass
class AuthorReorganizePlan:
    channel_folder: str
    moves: list[AuthorReorganizeMove] = field(default_factory=list)

    @property
    def authors(self) -> list[str]:
        names = sorted({
            item.author
            for item in self.moves
            if item.action == 'move' or item.action == 'skip_already'
        })
        return names

    @property
    def author_count(self) -> int:
        return len(self.authors)

    @property
    def move_count(self) -> int:
        return sum(1 for item in self.moves if item.action == 'move')

    @property
    def skip_count(self) -> int:
        return sum(1 for item in self.moves if item.action != 'move')

    def to_dict(self) -> dict:
        return {
            'channel_folder': self.channel_folder,
            'author_count': self.author_count,
            'authors': self.authors,
            'move_count': self.move_count,
            'skip_count': self.skip_count,
            'moves': [
                {
                    'message_id': item.message_id,
                    'from_relative': item.from_relative,
                    'to_relative': item.to_relative,
                    'author': item.author,
                    'action': item.action,
                }
                for item in self.moves
            ],
        }


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


def plan_author_reorganize(
        *,
        channel_folder: str,
        directory_paths: Iterable[str],
        author_by_message_id: dict[int, Optional[str]],
) -> AuthorReorganizePlan:
    """Build a move plan for flat (or misplaced) post folders under a channel.

    ``directory_paths`` may be absolute-under-archive (``channel/post``) or
    relative names (``post`` / ``author/post``). ``author_by_message_id`` maps
    Telegram main-post ids to raw author names (or None → unknown).
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
            desired = author_folder_segment(
                author_by_message_id.get(message_id) if message_id is not None else None
            )
            target = f'{desired}/{post_segment}'
            if author_part == desired:
                plan.moves.append(AuthorReorganizeMove(
                    message_id=message_id,
                    from_relative=relative,
                    to_relative=relative,
                    author=desired,
                    action='skip_already',
                ))
            else:
                # Nested under wrong/unknown author — still offer a move.
                plan.moves.append(AuthorReorganizeMove(
                    message_id=message_id,
                    from_relative=relative,
                    to_relative=target,
                    author=desired,
                    action='move' if target not in seen_targets else 'skip_nested',
                ))
                if target not in seen_targets:
                    seen_targets.add(target)
            continue

        # Flat legacy: channel/post
        if len(parts) == 1 and is_post_folder_segment(parts[0]):
            post_segment = parts[0]
            message_id = message_id_from_post_folder_segment(post_segment)
            raw_author = (
                author_by_message_id.get(message_id)
                if message_id is not None
                else None
            )
            author = author_folder_segment(raw_author)
            target = f'{author}/{post_segment}'
            if target in seen_targets:
                plan.moves.append(AuthorReorganizeMove(
                    message_id=message_id,
                    from_relative=relative,
                    to_relative=target,
                    author=author,
                    action='skip_nested',
                ))
                continue
            seen_targets.add(target)
            plan.moves.append(AuthorReorganizeMove(
                message_id=message_id,
                from_relative=relative,
                to_relative=target,
                author=author,
                action='move',
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
