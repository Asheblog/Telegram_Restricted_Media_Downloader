# coding=UTF-8
"""Temporary debug-session NDJSON logger (session 17c235). Remove after fix verified."""
from __future__ import annotations

import json
import time
from typing import Any, Optional

from module import log

_SESSION_ID = '17c235'
_PATHS = (
    '/app/TRMD/debug-17c235.log',
    'debug-17c235.log',
)


def agent_debug_log(
        *,
        hypothesis_id: str,
        location: str,
        message: str,
        data: Optional[dict[str, Any]] = None,
        run_id: str = 'pre-fix',
) -> None:
    payload = {
        'sessionId': _SESSION_ID,
        'hypothesisId': hypothesis_id,
        'location': location,
        'message': message,
        'data': data or {},
        'timestamp': int(time.time() * 1000),
        'runId': run_id,
    }
    line = json.dumps(payload, ensure_ascii=False)
    for path in _PATHS:
        try:
            with open(path, 'a', encoding='utf-8') as handle:
                handle.write(line + '\n')
            break
        except Exception:
            continue
    try:
        log.info('[debug-%s] %s | %s | %s', _SESSION_ID, location, message, line)
    except Exception:
        pass
