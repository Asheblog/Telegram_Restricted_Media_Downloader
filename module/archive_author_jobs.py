# coding=UTF-8
"""In-memory progress jobs for Archive Author scan/reorganize."""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Callable, Optional


class ArchiveAuthorJobStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}

    def create(self, *, kind: str, channel_folder: str) -> dict:
        job_id = f'archive-author-{kind}-{uuid.uuid4().hex[:12]}'
        now = time.time()
        job = {
            'id': job_id,
            'kind': kind,  # scan | reorganize
            'channel_folder': channel_folder,
            'status': 'running',  # running | success | failure
            'phase': 'queued',
            'current': 0,
            'total': 0,
            'percent': 0,
            'message': '排队中…',
            'error': None,
            'result': None,
            'created_at': now,
            'updated_at': now,
        }
        with self._lock:
            self._jobs[job_id] = job
            self._prune_locked(now)
        return dict(job)

    def update(self, job_id: str, **fields) -> Optional[dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.update(fields)
            job['updated_at'] = time.time()
            current = int(job.get('current') or 0)
            total = int(job.get('total') or 0)
            if total > 0:
                job['percent'] = max(0, min(100, int(round(100.0 * current / total))))
            elif job.get('status') == 'success':
                job['percent'] = 100
            return dict(job)

    def get(self, job_id: str) -> Optional[dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def progress_callback(self, job_id: str) -> Callable[..., None]:
        def _on_progress(
                *,
                phase: str,
                current: int = 0,
                total: int = 0,
                message: str = '',
        ) -> None:
            self.update(
                job_id,
                phase=phase,
                current=int(current or 0),
                total=int(total or 0),
                message=str(message or ''),
                status='running',
            )
        return _on_progress

    def _prune_locked(self, now: float, keep_seconds: float = 3600) -> None:
        expired = [
            job_id
            for job_id, job in self._jobs.items()
            if job.get('status') in ('success', 'failure')
            and now - float(job.get('updated_at') or 0) > keep_seconds
        ]
        for job_id in expired:
            self._jobs.pop(job_id, None)


def public_job_view(job: Optional[dict]) -> Optional[dict]:
    if not job:
        return None
    result = job.get('result')
    # Cap move rows returned to the browser for huge channels.
    if isinstance(result, dict) and isinstance(result.get('moves'), list):
        moves = result['moves']
        if len(moves) > 200:
            result = dict(result)
            result['moves'] = moves[:200]
            result['moves_truncated'] = True
            result['moves_total'] = len(moves)
    return {
        'id': job.get('id'),
        'kind': job.get('kind'),
        'channel_folder': job.get('channel_folder'),
        'status': job.get('status'),
        'phase': job.get('phase'),
        'current': job.get('current') or 0,
        'total': job.get('total') or 0,
        'percent': job.get('percent') or 0,
        'message': job.get('message') or '',
        'error': job.get('error'),
        'result': result,
    }
