# coding=UTF-8
"""Export/import helpers for live forward watch rules."""

from __future__ import annotations

import datetime
from typing import Any, Callable


FORWARD_WATCH_BACKUP_KIND = 'live_forward_watches'
FORWARD_WATCH_BACKUP_VERSION = 1


def forward_watch_key(source_link: str, target_link: str) -> tuple[str, str]:
    return source_link.strip(), target_link.strip()


def normalize_forward_watch_entry(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    source_link = str(raw.get('source_link') or '').strip()
    target_link = str(raw.get('target_link') or '').strip()
    if not source_link or not target_link:
        return None
    if not source_link.startswith('https://t.me/'):
        return None
    if not target_link.startswith('https://t.me/'):
        return None
    from module.transfer.comment_delay import normalize_optional_comment_delay_minutes

    try:
        comment_delay_minutes = normalize_optional_comment_delay_minutes(
            raw.get('comment_delay_minutes')
        )
    except ValueError:
        return None
    return {
        'source_link': source_link,
        'target_link': target_link,
        'include_comment': bool(raw.get('include_comment')),
        'resolve_deep_link': bool(raw.get('resolve_deep_link')),
        'comment_delay_minutes': comment_delay_minutes,
    }


def build_forward_watch_export_payload(watches: list[dict[str, Any]]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for watch in watches:
        entry = normalize_forward_watch_entry(watch)
        if not entry:
            continue
        key = forward_watch_key(entry['source_link'], entry['target_link'])
        if key in seen:
            continue
        seen.add(key)
        entries.append(entry)
    entries.sort(key=lambda item: (item['source_link'], item['target_link']))
    return {
        'version': FORWARD_WATCH_BACKUP_VERSION,
        'kind': FORWARD_WATCH_BACKUP_KIND,
        'exported_at': datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        'watches': entries,
    }


def parse_forward_watch_import_payload(payload: Any) -> tuple[list[Any], list[str]]:
    if isinstance(payload, list):
        return payload, []
    if not isinstance(payload, dict):
        return [], ['invalid_payload']
    kind = payload.get('kind')
    if kind and kind != FORWARD_WATCH_BACKUP_KIND:
        return [], ['invalid_kind']
    version = payload.get('version')
    if version is not None and version != FORWARD_WATCH_BACKUP_VERSION:
        return [], ['unsupported_version']
    watches = payload.get('watches')
    if watches is None:
        return [], ['missing_watches']
    if not isinstance(watches, list):
        return [], ['invalid_watches']
    return watches, []


def import_forward_watch_entries(
        entries: list[Any],
        create_watch: Callable[[dict[str, Any]], dict[str, Any]],
        *,
        parse_errors: list[str] | None = None,
        already_exists_error: str = 'watch_already_exists',
        source_conflict_error: str = 'watch_source_conflict',
) -> dict[str, Any]:
    result: dict[str, Any] = {
        'created': 0,
        'skipped': 0,
        'failed': 0,
        'errors': [],
        'watches': [],
    }
    for code in parse_errors or []:
        result['failed'] += 1
        result['errors'].append({'code': code})
    for index, raw in enumerate(entries):
        entry = normalize_forward_watch_entry(raw)
        if not entry:
            result['failed'] += 1
            result['errors'].append({'index': index, 'code': 'invalid_entry'})
            continue
        try:
            created = create_watch({'type': 'forward', **entry})
        except ValueError as exc:
            code = str(exc)
            if code == already_exists_error:
                result['skipped'] += 1
                continue
            result['failed'] += 1
            error = {'index': index, 'code': code or 'create_failed'}
            if code == source_conflict_error:
                error['source_link'] = entry['source_link']
            result['errors'].append(error)
            continue
        except Exception as exc:
            result['failed'] += 1
            result['errors'].append({
                'index': index,
                'code': 'create_failed',
                'message': str(exc),
            })
            continue
        result['created'] += 1
        result['watches'].extend(created.get('watches') or [])
    return result
