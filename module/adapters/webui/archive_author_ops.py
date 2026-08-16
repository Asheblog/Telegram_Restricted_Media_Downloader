# coding=UTF-8
"""Archive Author WebUI orchestration — deep module for scan/resolve/execute jobs."""
from __future__ import annotations

from typing import Optional


class ArchiveAuthorOps:
    """Owns Archive Author job orchestration; reads runtime deps from ``host``."""

    def __init__(self, host):
        self._host = host

    def _archive_author_service(self):
        from module.adapters.pikpak.archive_author import ArchiveAuthorReorganizeService
        from module.adapters.pikpak.archive import build_pikpak_archive_client

        host = self._host
        client = getattr(host, 'pikpak_archive_client', None)
        manager = getattr(host, 'pikpak_manager', None)
        if client is None and manager is not None:
            getter = getattr(manager, '_pikpak_archive_client_getter', None)
            if callable(getter):
                try:
                    client = getter()
                except Exception:
                    client = None
            if client is None:
                existing = getattr(manager, '_pikpak_archive_client', None)
                if existing is not None:
                    client = existing
        if client is None:
            config = {}
            gc = getattr(host, 'gc', None)
            raw = getattr(gc, 'config', None) if gc is not None else None
            if isinstance(raw, dict):
                config = (
                    (raw.get('target_profiles') or {})
                    .get('pikpak', {})
                    .get('archive')
                    or {}
                )
            client = build_pikpak_archive_client(config if isinstance(config, dict) else {})
        app = getattr(host, 'app', None)
        telegram = getattr(host, 'user', None)
        if telegram is None and app is not None:
            telegram = getattr(app, 'client', None)
        store = None
        try:
            store = host._ensure_transfer_store()
        except Exception:
            store = getattr(host, 'transfer_store', None)
        return ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=telegram,
            transfer_store=store,
            run_coro=host._run_telegram_coro,
            on_log=self._archive_author_log,
        )

    def _archive_author_log(
            self,
            *,
            stage: str,
            message: str,
            level: str = 'info',
            source_message_id=None,
            details=None,
    ) -> None:
        host = self._host
        system_log = getattr(host, 'system_log', None)
        if system_log is not None and hasattr(system_log, 'log'):
            try:
                system_log.log(
                    category='archive',
                    stage=stage,
                    message=message,
                    level=level,
                    source_message_id=source_message_id,
                    details=details,
                )
                return
            except Exception:
                pass
        diagnostic = getattr(host, 'diagnostic', None)
        if diagnostic is None:
            return
        line = f'[archive/{stage}] {message}'
        try:
            if level == 'error' and hasattr(diagnostic, 'error'):
                diagnostic.error(line)
            elif level == 'warning' and hasattr(diagnostic, 'warning'):
                diagnostic.warning(line)
            elif hasattr(diagnostic, 'info'):
                diagnostic.info(line)
        except Exception:
            pass

    def list_archive_author_channels(self) -> dict:
        service = self._archive_author_service()
        return {'channels': service.list_channels()}

    def _archive_author_job_store(self):
        from module.adapters.webui.archive_author_jobs import ArchiveAuthorJobStore

        host = self._host
        store = getattr(host, '_archive_author_jobs', None)
        if store is None:
            transfer_store = None
            try:
                transfer_store = host._ensure_transfer_store()
            except Exception:
                transfer_store = getattr(host, 'transfer_store', None)
            store = ArchiveAuthorJobStore(transfer_store=transfer_store)
            host._archive_author_jobs = store
        return store

    def _spawn_archive_author_runner(
            self,
            *,
            job_id: str,
            kind: str,
            channel_folder: str,
            execute_mode: str = 'all',
            resolve_scope: str = 'all',
            completed_keys: Optional[set] = None,
    ) -> None:
        import threading

        from module.adapters.webui.archive_author_jobs import completed_keys_from_job

        host = self._host
        jobs = self._archive_author_job_store()
        on_progress = jobs.progress_callback(job_id)
        on_checkpoint = jobs.checkpoint_callback(job_id)
        service = self._archive_author_service()
        mode = str(execute_mode or 'all').strip().lower() or 'all'
        scope = str(resolve_scope or 'all').strip().lower() or 'all'
        seed_keys = set(completed_keys or set())
        jobs.mark_runner_live(job_id)
        # Clear any previous stop request when (re)starting the runner.
        flag = jobs.attach_cancel_flag(job_id)
        flag.clear()

        def runner():
            try:
                if kind == 'scan':
                    result = service.scan(channel_folder, on_progress=on_progress)
                elif kind == 'resolve':
                    prior = jobs.latest_successful_scan_result(channel_folder)
                    paths = jobs.latest_directory_paths(channel_folder)
                    result = service.resolve_from_listing(
                        channel_folder,
                        directory_paths=paths or None,
                        prior_plan=prior,
                        on_progress=on_progress,
                        done_label=(
                            '未识别解析完成'
                            if scope in ('unresolved', 'review', 'needs_review', 'miss')
                            else '解析完成'
                        ),
                        require_telegram=True,
                        resolve_scope=scope,
                    )
                else:
                    # Reuse last successful scan/resolve plan — never rescan before move.
                    plan = jobs.latest_successful_scan_result(channel_folder)
                    from module.domain.archive_author.reorganize import planned_count_for_execute_mode
                    executable = planned_count_for_execute_mode(plan, mode)
                    if not plan or executable <= 0:
                        raise RuntimeError(
                            '请先完成「扫描作者分布」或「重新解析作者」。'
                            '整理会复用计划并串行移动，不会再次全量扫描网盘。'
                        )
                    if not seed_keys:
                        seed_keys.update(completed_keys_from_job(jobs.get(job_id)))
                    result = service.execute_plan(
                        plan,
                        on_progress=on_progress,
                        execute_mode=mode,
                        completed_keys=seed_keys,
                        should_stop=lambda: jobs.should_stop(job_id),
                        on_checkpoint=on_checkpoint,
                    )
                if kind in ('scan', 'resolve'):
                    stats = result.get('resolve_stats') or {}
                    scope_note = ''
                    if kind == 'resolve' and (stats.get('preserved') or 0):
                        scope_note = (
                            f'保留已识别 {stats.get("preserved") or 0}，'
                            f'回查未识别 {stats.get("refetch") or 0}；'
                        )
                    done_message = (
                        f'{"扫描" if kind == "scan" else "解析"}完成：'
                        f'{scope_note}'
                        f'解析到作者 {result.get("resolved_author_count") or 0}/'
                        f'{result.get("message_id_count") or 0}'
                        f'（抓取 {stats.get("fetched") or 0}，'
                        f'相册 {stats.get("media_group_hits") or 0}，'
                        f'邻条 {stats.get("neighbor_hits") or 0}，'
                        f'标签精确 {stats.get("hashtag_exact_hits") or 0}，'
                        f'标签待确认 {stats.get("hashtag_substring_hits") or 0}），'
                        f'{result.get("author_count") or 0} 个作者目录，'
                        f'待移动 {result.get("move_count") or 0}，'
                        f'待确认 {result.get("confirm_count") or 0}，'
                        f'未识别 {result.get("review_count") or 0}，'
                        f'跳过 {result.get("skip_count") or 0}'
                    )
                    jobs.update(
                        job_id,
                        status='success',
                        phase='done',
                        result=result,
                        message=done_message,
                        percent=100,
                    )
                else:
                    if result.get('stopped'):
                        done_message = (
                            f'已停止：新移动 {result.get("moved_count") or 0}，'
                            f'已就位跳过 {result.get("skipped_already_count") or 0}，'
                            f'失败 {result.get("error_count") or 0}；重启或再次迁移可续跑'
                        )
                        jobs.update(
                            job_id,
                            status='stopped',
                            phase='stopped',
                            result=result,
                            message=done_message,
                        )
                    else:
                        done_message = (
                            f'整理完成：新移动 {result.get("moved_count") or 0}，'
                            f'已就位跳过 {result.get("skipped_already_count") or 0}，'
                            f'失败 {result.get("error_count") or 0}'
                        )
                        jobs.update(
                            job_id,
                            status='success',
                            phase='done',
                            result=result,
                            message=done_message,
                            percent=100,
                        )
                if kind in ('scan', 'resolve'):
                    system_log = getattr(host, 'system_log', None)
                    if system_log is not None and hasattr(system_log, 'log'):
                        try:
                            system_log.log(
                                category='archive',
                                stage=f'author_{kind}',
                                message=done_message,
                                level='info',
                                details={
                                    'channel_folder': channel_folder,
                                    'resolve_stats': result.get('resolve_stats'),
                                    'miss_samples': (result.get('miss_samples') or [])[:10],
                                },
                            )
                        except Exception:
                            pass
                elif kind == 'reorganize':
                    system_log = getattr(host, 'system_log', None)
                    if system_log is not None and hasattr(system_log, 'log'):
                        try:
                            system_log.log(
                                category='archive',
                                stage='author_reorganize',
                                message=done_message,
                                level=(
                                    'info'
                                    if not (result.get('error_count') or 0)
                                    and not result.get('stopped')
                                    else 'warning'
                                ),
                                details={
                                    'channel_folder': channel_folder,
                                    'moved_count': result.get('moved_count'),
                                    'error_count': result.get('error_count'),
                                    'skipped_already_count': result.get('skipped_already_count'),
                                    'execute_mode': result.get('execute_mode'),
                                    'stopped': bool(result.get('stopped')),
                                },
                            )
                        except Exception:
                            pass
            except Exception as error:
                message = str(error) or error.__class__.__name__
                jobs.update(
                    job_id,
                    status='failure',
                    phase='error',
                    error=message,
                    message=message,
                )
                diagnostic = getattr(host, 'diagnostic', None)
                if diagnostic is not None:
                    try:
                        diagnostic.exception(f'[ArchiveAuthor] {kind} failed: {message}')
                    except Exception:
                        pass
                system_log = getattr(host, 'system_log', None)
                if system_log is not None and hasattr(system_log, 'log'):
                    try:
                        system_log.log(
                            category='archive',
                            stage=f'author_{kind}',
                            message=message,
                            level='error',
                            details={'channel_folder': channel_folder},
                        )
                    except Exception:
                        pass
            finally:
                jobs.mark_runner_done(job_id)

        threading.Thread(target=runner, name=f'archive-author-{kind}', daemon=True).start()

    def _start_archive_author_job(
            self,
            *,
            kind: str,
            channel_folder: str,
            execute_mode: str = 'all',
            resolve_scope: str = 'all',
    ) -> dict:
        from module.adapters.webui.archive_author_jobs import (
            completed_keys_from_job,
            public_job_view,
        )

        channel_folder = str(channel_folder or '').strip()
        if not channel_folder:
            raise ValueError('channel_folder is required')
        jobs = self._archive_author_job_store()
        existing = jobs.find_running(channel_folder=channel_folder)
        if existing:
            # Refresh reconnects to the same background job instead of starting another.
            return public_job_view(existing)

        mode = str(execute_mode or 'all').strip().lower() or 'all'
        if kind == 'reorganize':
            resumable = jobs.find_resumable_reorganize(channel_folder=channel_folder)
            if resumable:
                return self._resume_archive_author_reorganize_job(
                    resumable,
                    execute_mode=mode,
                )

        job = jobs.create(kind=kind, channel_folder=channel_folder)
        job_id = job['id']
        self._spawn_archive_author_runner(
            job_id=job_id,
            kind=kind,
            channel_folder=channel_folder,
            execute_mode=mode,
            resolve_scope=resolve_scope,
            completed_keys=completed_keys_from_job(job),
        )
        return public_job_view(jobs.get(job_id))

    def _resume_archive_author_reorganize_job(
            self,
            job: dict,
            *,
            execute_mode: str = 'all',
    ) -> dict:
        from module.adapters.webui.archive_author_jobs import (
            completed_keys_from_job,
            public_job_view,
        )

        jobs = self._archive_author_job_store()
        job_id = str(job.get('id') or '')
        channel_folder = str(job.get('channel_folder') or '').strip()
        if not job_id or not channel_folder:
            raise ValueError('resumable reorganize job is invalid')
        if jobs.is_runner_live(job_id):
            return public_job_view(jobs.get(job_id))
        result = job.get('result') if isinstance(job.get('result'), dict) else {}
        mode = str(
            execute_mode
            or result.get('execute_mode')
            or 'all'
        ).strip().lower() or 'all'
        jobs.update(
            job_id,
            status='running',
            phase='moving',
            error=None,
            message='续跑整理中…',
        )
        self._spawn_archive_author_runner(
            job_id=job_id,
            kind='reorganize',
            channel_folder=channel_folder,
            execute_mode=mode,
            completed_keys=completed_keys_from_job(job),
        )
        return public_job_view(jobs.get(job_id))

    def resume_interrupted_archive_author_jobs(self) -> int:
        """Auto-resume orphaned reorganize jobs after process restart."""
        jobs = self._archive_author_job_store()
        resumed = 0
        for job in jobs.list_orphaned_reorganize():
            try:
                self._resume_archive_author_reorganize_job(
                    job,
                    execute_mode=str(
                        ((job.get('result') or {}) if isinstance(job.get('result'), dict) else {})
                        .get('execute_mode')
                        or 'all'
                    ),
                )
                resumed += 1
            except Exception as error:
                diagnostic = getattr(self._host, 'diagnostic', None)
                if diagnostic is not None:
                    try:
                        diagnostic.warning(
                            f'[ArchiveAuthor] resume interrupted job failed: {error}'
                        )
                    except Exception:
                        pass
        if resumed:
            diagnostic = getattr(self._host, 'diagnostic', None)
            if diagnostic is not None:
                try:
                    diagnostic.info(
                        f'Resumed {resumed} interrupted archive author reorganize job(s).'
                    )
                except Exception:
                    pass
        return resumed

    def stop_archive_author_job(self, job_id: str) -> dict:
        from module.adapters.webui.archive_author_jobs import public_job_view

        jobs = self._archive_author_job_store()
        job = jobs.get(str(job_id or '').strip())
        if not job:
            raise ValueError('job not found')
        if str(job.get('kind') or '') != 'reorganize':
            raise ValueError('只有整理任务可以停止')
        if str(job.get('status') or '') != 'running':
            return public_job_view(job)
        if not jobs.request_stop(job['id']):
            raise RuntimeError('无法停止该任务')
        return public_job_view(jobs.get(job['id']))

    def scan_archive_author_reorganize(self, payload: dict) -> dict:
        channel_folder = str((payload or {}).get('channel_folder') or '').strip()
        return self._start_archive_author_job(kind='scan', channel_folder=channel_folder)

    def resolve_archive_author_reorganize(self, payload: dict) -> dict:
        channel_folder = str((payload or {}).get('channel_folder') or '').strip()
        scope = str(
            (payload or {}).get('scope')
            or (payload or {}).get('resolve_scope')
            or 'all'
        ).strip().lower() or 'all'
        return self._start_archive_author_job(
            kind='resolve',
            channel_folder=channel_folder,
            resolve_scope=scope,
        )

    def execute_archive_author_reorganize(self, payload: dict) -> dict:
        channel_folder = str((payload or {}).get('channel_folder') or '').strip()
        mode = str((payload or {}).get('mode') or 'all').strip().lower() or 'all'
        return self._start_archive_author_job(
            kind='reorganize',
            channel_folder=channel_folder,
            execute_mode=mode,
        )

    def list_archive_author_plan_moves(self, payload: dict | None = None) -> dict:
        from module.adapters.webui.archive_author_jobs import list_job_plan_moves

        data = payload or {}
        job_id = str(data.get('job_id') or '').strip()
        channel_folder = str(data.get('channel_folder') or '').strip()
        bucket = str(data.get('bucket') or '').strip()
        offset = data.get('offset', 0)
        limit = data.get('limit', 50)
        jobs = self._archive_author_job_store()
        job = None
        if job_id:
            job = jobs.get(job_id)
        elif channel_folder:
            # Prefer latest successful scan/resolve for the channel.
            with jobs._lock:
                candidates = [
                    dict(item)
                    for item in jobs._jobs.values()
                    if item.get('channel_folder') == channel_folder
                    and item.get('kind') in ('scan', 'resolve')
                    and item.get('status') == 'success'
                    and isinstance(item.get('result'), dict)
                ]
            if candidates:
                candidates.sort(key=lambda item: float(item.get('updated_at') or 0), reverse=True)
                job = candidates[0]
            else:
                plan = jobs.latest_successful_scan_result(channel_folder)
                if plan:
                    job = {
                        'id': None,
                        'channel_folder': channel_folder,
                        'result': plan,
                    }
        if not job:
            raise ValueError('plan not found')
        return list_job_plan_moves(
            job,
            bucket=bucket,
            offset=offset,
            limit=limit,
        )

    def get_archive_author_job(self, job_id: str) -> dict:
        from module.adapters.webui.archive_author_jobs import public_job_view

        job = self._archive_author_job_store().get(str(job_id or '').strip())
        if not job:
            raise ValueError('job not found')
        return public_job_view(job)

    def get_active_archive_author_job(self, channel_folder: str | None = None) -> dict:
        from module.adapters.webui.archive_author_jobs import public_job_view

        jobs = self._archive_author_job_store()
        channel = str(channel_folder or '').strip() or None
        job = (
            jobs.find_running(channel_folder=channel)
            or jobs.find_resumable_reorganize(channel_folder=channel)
            or jobs.latest(channel_folder=channel)
        )
        # Cross-device resume: if the selected channel has no match, still surface
        # any live running / resumable job so mobile can attach to a desktop start.
        if channel and (not job or not job.get('id') or str(job.get('status') or '') != 'running'):
            global_running = (
                jobs.find_running(channel_folder=None)
                or jobs.find_resumable_reorganize(channel_folder=None)
            )
            if global_running and global_running.get('id'):
                job = global_running
        view = public_job_view(job)
        return view or {'id': None, 'status': None}
