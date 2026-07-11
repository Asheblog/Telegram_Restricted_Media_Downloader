# coding=UTF-8
"""Build structured statistics payloads for WebUI dashboards."""

from __future__ import annotations

from typing import Any

CHANNEL_CHART_LIMIT = 12
OTHER_CHANNEL_LABEL = '其他'
DEFAULT_STATISTICS_WINDOW_DAYS = 7


def _success_rate(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(success / total * 100, 1)


def _normalize_channel_row(row: dict[str, Any]) -> dict[str, Any]:
    success = int(row.get('success') or 0)
    failure = int(row.get('failure') or 0)
    skip = int(row.get('skip') or 0)
    total = int(row.get('total') or (success + failure + skip))
    channel = str(row.get('channel') or 'unknown')
    return {
        'channel': channel,
        'success': success,
        'failure': failure,
        'skip': skip,
        'total': total,
        'success_rate': _success_rate(success, total),
        'is_other': bool(row.get('is_other')),
    }


def _collapse_chart_rows(
        rows: list[dict[str, Any]],
        chart_limit: int,
) -> list[dict[str, Any]]:
    if len(rows) <= chart_limit:
        return [dict(row) for row in rows]
    head = [dict(row) for row in rows[:chart_limit]]
    overflow = rows[chart_limit:]
    other = {
        'channel': OTHER_CHANNEL_LABEL,
        'success': sum(row['success'] for row in overflow),
        'failure': sum(row['failure'] for row in overflow),
        'skip': sum(row['skip'] for row in overflow),
        'total': sum(row['total'] for row in overflow),
        'is_other': True,
    }
    other['success_rate'] = _success_rate(other['success'], other['total'])
    head.append(other)
    return head


def build_statistics_payload(
        channel_rows: list[dict[str, Any]] | None = None,
        *,
        chart_limit: int = CHANNEL_CHART_LIMIT,
        window_days: int = DEFAULT_STATISTICS_WINDOW_DAYS,
) -> dict:
    """Build dashboard payload from per-channel terminal-item aggregates."""
    normalized = [_normalize_channel_row(row) for row in (channel_rows or [])]
    normalized.sort(key=lambda row: (-row['total'], row['channel']))

    success_total = sum(row['success'] for row in normalized)
    failure_total = sum(row['failure'] for row in normalized)
    skip_total = sum(row['skip'] for row in normalized)
    downloads_total = success_total + failure_total + skip_total
    available = downloads_total > 0

    return {
        'tables': {
            'channel': {
                'available': available,
                'rows': len(normalized),
            },
        },
        'summary': {
            'channels': len(normalized),
            'downloads_total': downloads_total,
            'success_rate': _success_rate(success_total, downloads_total),
            'failure_count': failure_total,
            'skip_count': skip_total,
            'issue_count': failure_total + skip_total,
            'window_days': int(window_days),
        },
        'channels': normalized,
        'count_by_channel': normalized,
        'chart_by_channel': _collapse_chart_rows(normalized, max(1, int(chart_limit))),
    }
