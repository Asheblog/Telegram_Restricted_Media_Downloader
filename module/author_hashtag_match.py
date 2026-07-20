# coding=UTF-8
"""Match plain hashtags against a channel's known Post Author set."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

from module.source_folders import (
    TOPIC_AUTHOR_DENYLIST,
    UNKNOWN_AUTHOR_FOLDER,
    is_denied_post_author,
    normalize_author_label,
)

# Back-compat aliases used by older imports/tests.
TOPIC_HASHTAG_DENYLIST = TOPIC_AUTHOR_DENYLIST
__all__ = [
    'TOPIC_HASHTAG_DENYLIST',
    'TOPIC_AUTHOR_DENYLIST',
    'HashtagAuthorMatch',
    'core_author_label',
    'extract_hashtags_from_text',
    'match_author_from_hashtags',
    'normalize_author_label',
]

_HASHTAG_RE = re.compile(r'[#＃]([^\s#＃@＠]+)')
_TRAILING_PUNCT = re.compile(r'[\s\-—_.,，。、;；:：!！?？\'\"“”‘’（）()【】\[\]<>《》]+$')
_LEADING_PUNCT = re.compile(r'^[\s\-—_.,，。、;；:：!！?？\'\"“”‘’（）()【】\[\]<>《》]+')
# Optional honorific / filler characters often inserted into author-like tags.
_AUTHOR_NOISE_CHARS = frozenset('亲会的大小我你他她了呢啊呀')


def core_author_label(value: Optional[str]) -> str:
    """Normalized label with common filler characters removed."""
    return ''.join(
        ch for ch in normalize_author_label(value)
        if ch not in _AUTHOR_NOISE_CHARS
    )


def extract_hashtags_from_text(text: Optional[str]) -> list[str]:
    """Return raw hashtag bodies (without #) in appearance order, de-duplicated."""
    if not isinstance(text, str) or not text.strip():
        return []
    seen: set[str] = set()
    out: list[str] = []
    for match in _HASHTAG_RE.finditer(text):
        raw = (match.group(1) or '').strip()
        raw = _TRAILING_PUNCT.sub('', raw)
        if not raw:
            continue
        key = normalize_author_label(raw)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(raw)
    return out


@dataclass(frozen=True)
class HashtagAuthorMatch:
    author: Optional[str]
    confidence: str  # medium | low | none
    method: str  # hashtag_exact | hashtag_substring | none
    matched_tag: str = ''


def match_author_from_hashtags(
        tags: Iterable[str],
        known_authors: Iterable[str],
        *,
        extra_deny: Optional[Iterable[str]] = None,
) -> HashtagAuthorMatch:
    """Map hashtags onto a trusted author set.

    Exact normalized match → medium / hashtag_exact (auto-move eligible).
    Unique substring containment either way → low / hashtag_substring (confirm).
    Topic denylist / ambiguous / unknown tags → none.
    Never matches site labels such as ``海角社区``.
    """
    known_map: dict[str, str] = {}
    for name in known_authors:
        text = str(name or '').strip()
        if not text or text == UNKNOWN_AUTHOR_FOLDER or is_denied_post_author(text):
            continue
        key = normalize_author_label(text)
        if not key:
            continue
        # Prefer first seen canonical spelling.
        known_map.setdefault(key, text)
    if not known_map:
        return HashtagAuthorMatch(author=None, confidence='none', method='none')

    deny = set(TOPIC_AUTHOR_DENYLIST)
    if extra_deny:
        for item in extra_deny:
            key = normalize_author_label(item)
            if key:
                deny.add(key)

    candidates: list[str] = []
    for tag in tags:
        key = normalize_author_label(tag)
        if not key or key in deny or is_denied_post_author(tag):
            continue
        candidates.append(str(tag).strip())

    exact_authors: list[tuple[str, str]] = []
    for tag in candidates:
        key = normalize_author_label(tag)
        author = known_map.get(key)
        if author:
            exact_authors.append((author, tag))
    exact_unique = {author for author, _ in exact_authors}
    if len(exact_unique) == 1:
        author, tag = exact_authors[0]
        return HashtagAuthorMatch(
            author=author,
            confidence='medium',
            method='hashtag_exact',
            matched_tag=tag,
        )
    if len(exact_unique) > 1:
        return HashtagAuthorMatch(author=None, confidence='none', method='none')

    fuzzy_hits: list[tuple[str, str]] = []
    for tag in candidates:
        tag_key = normalize_author_label(tag)
        if len(tag_key) < 2:
            continue
        tag_core = core_author_label(tag_key)
        for known_key, author in known_map.items():
            if len(known_key) < 2:
                continue
            if tag_key == known_key:
                continue
            if tag_key in known_key or known_key in tag_key:
                fuzzy_hits.append((author, tag))
                continue
            if len(tag_core) >= 3 and tag_core == core_author_label(known_key):
                fuzzy_hits.append((author, tag))
    fuzzy_unique = {author for author, _ in fuzzy_hits}
    if len(fuzzy_unique) == 1:
        author, tag = fuzzy_hits[0]
        return HashtagAuthorMatch(
            author=author,
            confidence='low',
            method='hashtag_substring',
            matched_tag=tag,
        )
    return HashtagAuthorMatch(author=None, confidence='none', method='none')
