# coding=UTF-8
"""Progress jobs for Archive Author scan/reorganize (memory + optional SQLite)."""
from __future__ import annotations

import threading
import time
import uuid
from typing import Callable, Optional


class ArchiveAuthorJobStore:
    def __init__(self, transfer_store=None):
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}
        self._transfer_store = transfer_store
        self._last_persist_at: dict[str, float] = {}
        if transfer_store is not None and hasattr(transfer_store, 'mark_stale_archive_author_jobs'):
            # Leftover running rows from a previous process cannot continue.
            try:
                transfer_store.mark_stale_archive_author_jobs(older_than_seconds=0)
            except Exception:
                pass

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
            snapshot = dict(job)
        self._persist(snapshot, force=True)
        return snapshot

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
            snapshot = dict(job)
            status = str(job.get('status') or '')
        # Persist terminals always; throttle running progress writes.
        force = status in ('success', 'failure') or fields.get('result') is not None
        self._persist(snapshot, force=force)
        return snapshot

    def get(self, job_id: str) -> Optional[dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                return dict(job)
        store = self._transfer_store
        if store is not None and hasattr(store, 'get_archive_author_job'):
            try:
                persisted = store.get_archive_author_job(str(job_id))
            except Exception:
                persisted = None
            if persisted:
                with self._lock:
                    self._jobs[job_id] = dict(persisted)
                return dict(persisted)
        return None

    def find_running(self, *, channel_folder: Optional[str] = None, kind: Optional[str] = None) -> Optional[dict]:
        with self._lock:
            candidates = []
            for job in self._jobs.values():
                if job.get('status') != 'running':
                    continue
                if channel_folder and job.get('channel_folder') != channel_folder:
                    continue
                if kind and job.get('kind') != kind:
                    continue
                candidates.append(dict(job))
            if candidates:
                candidates.sort(key=lambda item: float(item.get('updated_at') or 0), reverse=True)
                return candidates[0]
        store = self._transfer_store
        if store is not None and hasattr(store, 'list_archive_author_jobs'):
            try:
                rows = store.list_archive_author_jobs(
                    channel_folder=channel_folder,
                    status='running',
                    limit=20,
                )
            except Exception:
                rows = []
            for row in rows:
                if kind and row.get('kind') != kind:
                    continue
                with self._lock:
                    self._jobs[row['id']] = dict(row)
                return dict(row)
        return None

    def latest(self, *, channel_folder: Optional[str] = None) -> Optional[dict]:
        running = self.find_running(channel_folder=channel_folder)
        if running:
            return running
        with self._lock:
            candidates = [
                dict(job)
                for job in self._jobs.values()
                if not channel_folder or job.get('channel_folder') == channel_folder
            ]
            if candidates:
                candidates.sort(key=lambda item: float(item.get('updated_at') or 0), reverse=True)
                return candidates[0]
        store = self._transfer_store
        if store is not None and hasattr(store, 'list_archive_author_jobs'):
            try:
                rows = store.list_archive_author_jobs(channel_folder=channel_folder, limit=1)
            except Exception:
                rows = []
            if rows:
                row = rows[0]
                with self._lock:
                    self._jobs[row['id']] = dict(row)
                return dict(row)
        return None

    def latest_successful_scan_result(self, channel_folder: str) -> Optional[dict]:
        """Full plan for reorganize (scan or resolve; not the truncated public view)."""
        channel_folder = str(channel_folder or '').strip()
        if not channel_folder:
            return None
        allowed = ('scan', 'resolve')
        with self._lock:
            candidates = [
                dict(job)
                for job in self._jobs.values()
                if job.get('kind') in allowed
                and job.get('status') == 'success'
                and job.get('channel_folder') == channel_folder
                and isinstance(job.get('result'), dict)
            ]
            if candidates:
                candidates.sort(key=lambda item: float(item.get('updated_at') or 0), reverse=True)
                return dict(candidates[0]['result'])
        store = self._transfer_store
        if store is not None and hasattr(store, 'list_archive_author_jobs'):
            try:
                rows = store.list_archive_author_jobs(
                    channel_folder=channel_folder,
                    status='success',
                    limit=20,
                )
            except Exception:
                rows = []
            for row in rows:
                if row.get('kind') not in allowed:
                    continue
                result = row.get('result')
                if isinstance(result, dict):
                    with self._lock:
                        self._jobs[row['id']] = dict(row)
                    return dict(result)
        return None

    def latest_directory_paths(self, channel_folder: str) -> list[str]:
        from module.archive_author_tool import directory_paths_from_plan

        plan = self.latest_successful_scan_result(channel_folder)
        return directory_paths_from_plan(plan)

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

    def _persist(self, job: dict, *, force: bool = False) -> None:
        store = self._transfer_store
        if store is None or not hasattr(store, 'upsert_archive_author_job'):
            return
        job_id = str(job.get('id') or '')
        now = time.time()
        if not force:
            last = self._last_persist_at.get(job_id, 0)
            if now - last < 1.0:
                return
        try:
            store.upsert_archive_author_job(job)
            self._last_persist_at[job_id] = now
        except Exception:
            pass

    def _prune_locked(self, now: float, keep_seconds: float = 3600) -> None:
        expired = [
            job_id
            for job_id, job in self._jobs.items()
            if job.get('status') in ('success', 'failure')
            and now - float(job.get('updated_at') or 0) > keep_seconds
        ]
        for job_id in expired:
            self._jobs.pop(job_id, None)
            self._last_persist_at.pop(job_id, None)


def public_job_view(job: Optional[dict]) -> Optional[dict]:
    if not job:
        return None
    result = job.get('result')
    # Keep browser payloads small: summary only; detail rows via moves API.
    if isinstance(result, dict):
        from module.archive_reorganize import summarize_move_rows

        result = dict(result)
        paths = result.get('directory_paths')
        if isinstance(paths, list):
            result['directory_path_count'] = len(paths)
            result.pop('directory_paths', None)
        moves = result.get('moves')
        if isinstance(moves, list):
            result['moves_total'] = len(moves)
            if not isinstance(result.get('summary'), dict):
                result['summary'] = summarize_move_rows(moves)
            # Prefer summary fields even when older plans lack them.
            summary = result['summary']
            result.setdefault('move_count', summary.get('move', 0))
            result.setdefault('confirm_count', summary.get('needs_confirm', 0))
            result.setdefault('review_count', summary.get('needs_review', 0))
            result.setdefault('executable_count', summary.get('executable', 0))
            result.setdefault('skip_count', (
                int(summary.get('skip_already') or 0)
                + int(summary.get('skip_nested') or 0)
                + int(summary.get('skip_invalid') or 0)
            ))
            result['moves'] = []
            result['moves_omitted'] = True
            result['moves_truncated'] = True
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


def list_job_plan_moves(
        job: Optional[dict],
        *,
        bucket: str = '',
        offset: int = 0,
        limit: int = 50,
) -> dict:
    from module.archive_reorganize import filter_plan_moves

    if not job:
        raise ValueError('job not found')
    result = job.get('result')
    if not isinstance(result, dict):
        return {
            'job_id': job.get('id'),
            'channel_folder': job.get('channel_folder'),
            'items': [],
            'total': 0,
            'offset': 0,
            'limit': limit,
            'bucket': bucket or None,
            'summary': {},
        }
    moves = result.get('moves') if isinstance(result.get('moves'), list) else []
    page = filter_plan_moves(moves, bucket=bucket, offset=offset, limit=limit)
    summary = result.get('summary')
    if not isinstance(summary, dict):
        from module.archive_reorganize import summarize_move_rows
        summary = summarize_move_rows(moves)
    return {
        'job_id': job.get('id'),
        'channel_folder': job.get('channel_folder'),
        'summary': summary,
        **page,
    }
