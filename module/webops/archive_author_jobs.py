# coding=UTF-8
"""Progress jobs for Archive Author scan/reorganize (memory + optional SQLite)."""
from __future__ import annotations

import threading
import time
import uuid
from typing import Callable, Optional


TERMINAL_STATUSES = frozenset({'success', 'failure', 'stopped'})
RESUMABLE_STATUSES = frozenset({'running', 'stopped'})


class ArchiveAuthorJobStore:
    def __init__(self, transfer_store=None):
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}
        self._transfer_store = transfer_store
        self._last_persist_at: dict[str, float] = {}
        self._cancel_flags: dict[str, threading.Event] = {}
        self._live_runners: set[str] = set()
        if transfer_store is not None and hasattr(transfer_store, 'mark_stale_archive_author_jobs'):
            # Scan/resolve cannot continue mid-flight after process restart.
            # Reorganize jobs stay resumable (running/stopped + checkpoint).
            try:
                transfer_store.mark_stale_archive_author_jobs(
                    older_than_seconds=0,
                    kinds=('scan', 'resolve'),
                )
            except TypeError:
                # Older TransferStore without kinds= — fail safe for non-reorganize only
                # by leaving rows alone when signature mismatches; callers still resume.
                try:
                    transfer_store.mark_stale_archive_author_jobs(older_than_seconds=0)
                except Exception:
                    pass
            except Exception:
                pass

    def create(self, *, kind: str, channel_folder: str) -> dict:
        job_id = f'archive-author-{kind}-{uuid.uuid4().hex[:12]}'
        now = time.time()
        job = {
            'id': job_id,
            'kind': kind,  # scan | resolve | reorganize
            'channel_folder': channel_folder,
            'status': 'running',  # running | success | failure | stopped
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
            self._cancel_flags[job_id] = threading.Event()
            self._prune_locked(now)
            snapshot = dict(job)
        self._persist(snapshot, force=True)
        return snapshot

    def attach_cancel_flag(self, job_id: str) -> threading.Event:
        with self._lock:
            event = self._cancel_flags.get(job_id)
            if event is None:
                event = threading.Event()
                self._cancel_flags[job_id] = event
            return event

    def mark_runner_live(self, job_id: str) -> None:
        with self._lock:
            self._live_runners.add(str(job_id))
            if job_id not in self._cancel_flags:
                self._cancel_flags[job_id] = threading.Event()

    def mark_runner_done(self, job_id: str) -> None:
        with self._lock:
            self._live_runners.discard(str(job_id))

    def is_runner_live(self, job_id: str) -> bool:
        with self._lock:
            return str(job_id) in self._live_runners

    def request_stop(self, job_id: str) -> bool:
        job_id = str(job_id or '').strip()
        if not job_id:
            return False
        with self._lock:
            job = self._jobs.get(job_id)
            event = self._cancel_flags.get(job_id)
            if job is None:
                return False
            if str(job.get('status') or '') != 'running':
                return False
            if event is None:
                event = threading.Event()
                self._cancel_flags[job_id] = event
            event.set()
            job['message'] = '正在停止…'
            job['updated_at'] = time.time()
            snapshot = dict(job)
        self._persist(snapshot, force=True)
        return True

    def should_stop(self, job_id: str) -> bool:
        with self._lock:
            event = self._cancel_flags.get(str(job_id))
            return bool(event and event.is_set())

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
        force = status in TERMINAL_STATUSES or fields.get('result') is not None
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
                    if job_id not in self._cancel_flags:
                        self._cancel_flags[job_id] = threading.Event()
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
                # Prefer live runners; orphaned DB "running" is resumed separately.
                if str(job.get('id')) not in self._live_runners:
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
                job_id = str(row.get('id') or '')
                with self._lock:
                    self._jobs[job_id] = dict(row)
                    if job_id not in self._cancel_flags:
                        self._cancel_flags[job_id] = threading.Event()
                    if job_id in self._live_runners:
                        return dict(row)
        return None

    def find_resumable_reorganize(
            self,
            *,
            channel_folder: Optional[str] = None,
    ) -> Optional[dict]:
        """Return interrupted reorganize job that has no live runner."""
        channel_folder = str(channel_folder or '').strip() or None
        candidates = []
        with self._lock:
            for job in self._jobs.values():
                if job.get('kind') != 'reorganize':
                    continue
                if str(job.get('status') or '') not in RESUMABLE_STATUSES:
                    continue
                job_id = str(job.get('id') or '')
                if job_id in self._live_runners:
                    continue
                if channel_folder and job.get('channel_folder') != channel_folder:
                    continue
                candidates.append(dict(job))
        store = self._transfer_store
        if store is not None and hasattr(store, 'list_archive_author_jobs'):
            for status in ('running', 'stopped'):
                try:
                    rows = store.list_archive_author_jobs(
                        channel_folder=channel_folder,
                        status=status,
                        limit=20,
                    )
                except Exception:
                    rows = []
                for row in rows:
                    if row.get('kind') != 'reorganize':
                        continue
                    job_id = str(row.get('id') or '')
                    with self._lock:
                        if job_id in self._live_runners:
                            continue
                        self._jobs[job_id] = dict(row)
                        if job_id not in self._cancel_flags:
                            self._cancel_flags[job_id] = threading.Event()
                    if channel_folder and row.get('channel_folder') != channel_folder:
                        continue
                    candidates.append(dict(row))
        if not candidates:
            return None
        # Deduplicate by id, newest first.
        by_id = {}
        for item in candidates:
            by_id[str(item.get('id'))] = item
        ordered = sorted(
            by_id.values(),
            key=lambda item: float(item.get('updated_at') or 0),
            reverse=True,
        )
        return ordered[0]

    def list_orphaned_reorganize(self) -> list[dict]:
        found = []
        seen = set()
        candidate = self.find_resumable_reorganize()
        # Collect all channels with orphaned reorganize jobs.
        store = self._transfer_store
        rows = []
        if store is not None and hasattr(store, 'list_archive_author_jobs'):
            for status in ('running', 'stopped'):
                try:
                    rows.extend(store.list_archive_author_jobs(status=status, limit=50) or [])
                except Exception:
                    pass
        with self._lock:
            memory_rows = [
                dict(job) for job in self._jobs.values()
                if job.get('kind') == 'reorganize'
                and str(job.get('status') or '') in RESUMABLE_STATUSES
            ]
        for row in list(rows) + memory_rows:
            if row.get('kind') != 'reorganize':
                continue
            if str(row.get('status') or '') not in RESUMABLE_STATUSES:
                continue
            job_id = str(row.get('id') or '')
            if not job_id or job_id in seen:
                continue
            with self._lock:
                if job_id in self._live_runners:
                    continue
                self._jobs[job_id] = dict(row)
                if job_id not in self._cancel_flags:
                    self._cancel_flags[job_id] = threading.Event()
            seen.add(job_id)
            found.append(dict(row))
        found.sort(key=lambda item: float(item.get('updated_at') or 0), reverse=True)
        if candidate and str(candidate.get('id')) not in seen:
            found.insert(0, candidate)
        return found

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
        from module.adapters.pikpak.archive_author import directory_paths_from_plan

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
            status = 'running'
            if phase == 'stopped':
                status = 'stopped'
            self.update(
                job_id,
                phase=phase,
                current=int(current or 0),
                total=int(total or 0),
                message=str(message or ''),
                status=status,
            )
        return _on_progress

    def checkpoint_callback(self, job_id: str) -> Callable[..., None]:
        def _on_checkpoint(**payload) -> None:
            completed = payload.get('completed_keys') or []
            result = {
                'checkpoint': True,
                'channel_folder': payload.get('channel_folder'),
                'execute_mode': payload.get('execute_mode') or 'all',
                'completed_from_relatives': list(completed),
                'moved_count': int(payload.get('moved_count') or 0),
                'error_count': int(payload.get('error_count') or 0),
                'skipped_already_count': int(payload.get('skipped_already_count') or 0),
                'errors': list(payload.get('errors') or [])[-40:],
                'stopped': bool(payload.get('stopped')),
            }
            fields = {
                'result': result,
                'current': int(payload.get('current') or 0),
                'total': int(payload.get('total') or 0),
            }
            if payload.get('stopped'):
                fields['status'] = 'stopped'
                fields['phase'] = 'stopped'
            self.update(job_id, **fields)
        return _on_checkpoint

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
            self._cancel_flags.pop(job_id, None)
            self._live_runners.discard(job_id)


def public_job_view(job: Optional[dict]) -> Optional[dict]:
    if not job:
        return None
    result = job.get('result')
    # Keep browser payloads small: summary only; detail rows via moves API.
    if isinstance(result, dict):
        from module.domain.archive_author.reorganize import summarize_move_rows

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
        # Checkpoint payloads stay small already.
        if result.get('checkpoint'):
            result.pop('errors', None)
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
        'can_stop': (
            str(job.get('status') or '') == 'running'
            and str(job.get('kind') or '') == 'reorganize'
        ),
    }


def list_job_plan_moves(
        job: Optional[dict],
        *,
        bucket: str = '',
        offset: int = 0,
        limit: int = 50,
) -> dict:
    from module.domain.archive_author.reorganize import filter_plan_moves

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
        from module.domain.archive_author.reorganize import summarize_move_rows
        summary = summarize_move_rows(moves)
    return {
        'job_id': job.get('id'),
        'channel_folder': job.get('channel_folder'),
        'summary': summary,
        **page,
    }


def completed_keys_from_job(job: Optional[dict]) -> set[str]:
    if not isinstance(job, dict):
        return set()
    result = job.get('result')
    if not isinstance(result, dict):
        return set()
    keys = result.get('completed_from_relatives') or []
    return {
        str(item).replace('\\', '/').strip('/')
        for item in keys
        if str(item).strip()
    }
