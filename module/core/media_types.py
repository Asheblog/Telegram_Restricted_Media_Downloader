# coding=UTF-8
"""Unified Media Type Allowlist helpers."""
from __future__ import annotations

import json
from typing import Any, Optional

MEDIA_TYPES = (
    'video', 'photo', 'audio', 'document',
    'voice', 'text', 'animation', 'video_note',
)

MEDIA_TYPES_DEFAULT = {t: True for t in MEDIA_TYPES}
DOWNLOAD_MEDIA_TYPES = tuple(t for t in MEDIA_TYPES if t != 'text')


def normalize_media_types(raw: Any) -> Optional[dict]:
    """Normalize override/allowlist payload.

    Returns:
        None — inherit / unset
        dict — complete {type: bool} allowlist
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        try:
            raw = json.loads(text)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
    if not isinstance(raw, dict):
        return None
    return {t: bool(raw.get(t, False)) for t in MEDIA_TYPES}


def serialize_media_types(raw: Any) -> Optional[str]:
    """Serialize override for SQLite TEXT column; None when inheriting."""
    normalized = normalize_media_types(raw)
    if normalized is None:
        return None
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True)


def resolve_allowed_media_types(
        global_types: Any = None,
        override: Any = None,
) -> dict:
    """Resolve effective allowlist: override replaces global entirely when set."""
    override_norm = normalize_media_types(override)
    if override_norm is not None:
        return override_norm
    global_norm = normalize_media_types(global_types)
    if global_norm is not None:
        return global_norm
    return dict(MEDIA_TYPES_DEFAULT)


def media_types_to_download_type_list(media_types: Any) -> list[str]:
    """Derive UserConfig.download_type list (no text) from an allowlist."""
    allowed = resolve_allowed_media_types(media_types)
    return [t for t in DOWNLOAD_MEDIA_TYPES if allowed.get(t)]


def message_matches_media_types(message: Any, media_types: Any) -> bool:
    """Return True when message matches at least one allowed media type."""
    from module.core.filter import MessageFilter

    allowed = resolve_allowed_media_types(media_types)
    return MessageFilter({'media_types': allowed}).should_pass_media_type(message)


def build_runtime_message_filter(
        message_filter_config: Any = None,
        media_types_override: Any = None,
):
    """Build MessageFilter with Media Type Allowlist (+ optional override)."""
    from module.core.filter import MessageFilter

    config = dict(message_filter_config or {})
    config['media_types'] = resolve_allowed_media_types(
        config.get('media_types'),
        media_types_override,
    )
    return MessageFilter(config)


def parse_media_types_payload(raw: Any) -> Optional[dict]:
    """Parse API/UI payload: omit/null → inherit; dict/list → override allowlist."""
    if raw is None:
        return None
    if isinstance(raw, str):
        return normalize_media_types(raw)
    if isinstance(raw, list):
        selected = {str(item) for item in raw}
        return {t: (t in selected) for t in MEDIA_TYPES}
    if isinstance(raw, dict):
        # Explicit empty with use_global marker
        if raw.get('use_global') is True or raw.get('inherit') is True:
            return None
        return normalize_media_types(raw)
    return None
