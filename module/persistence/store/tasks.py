# coding=UTF-8
import datetime
import os
import sqlite3
from typing import Any, Dict, List, Optional

from module.core.archive_title_source import normalize_archive_title_source
from module.core.media_types import normalize_media_types, serialize_media_types
from module.persistence.store.constants import (
    DEFAULT_RECONCILE_MIN_INTERVAL_SECONDS,
    STALE_EMPTY_WATCH_INLINE_TIMEOUT_SECONDS,
)
from module.persistence.store.status import ExecutionMode, TransferStatus


class TasksMixin:
    def create_task(
        self,
        source_link: str,
        target_link: str = "https://t.me/pikpak_bot",
        target_profile: str = "pikpak",
        start_id: Optional[int] = None,
        end_id: Optional[int] = None,
        include_comment: bool = False,
        resolve_deep_link: bool = False,
        archive_by_author: bool = False,
        archive_title_source: str = "auto",
        execution_mode: str = ExecutionMode.WEB_QUEUE,
        watch_id: Optional[str] = None,
        media_types: Optional[dict] = None,
    ) -> int:
        now = self.utc_now()
        mode = execution_mode or ExecutionMode.WEB_QUEUE
        if mode not in (ExecutionMode.WEB_QUEUE, ExecutionMode.WATCH_INLINE):
            mode = ExecutionMode.WEB_QUEUE
        media_types_json = serialize_media_types(media_types)
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO transfer_tasks (
                    source_link, target_link, target_profile, start_id, end_id,
                    include_comment, resolve_deep_link, archive_by_author,
                    archive_title_source, execution_mode, watch_id,
                    media_types, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_link,
                    target_link,
                    target_profile,
                    start_id,
                    end_id,
                    int(bool(include_comment)),
                    int(bool(resolve_deep_link)),
                    int(bool(archive_by_author)),
                    normalize_archive_title_source(archive_title_source),
                    mode,
                    watch_id or None,
                    media_types_json,
                    TransferStatus.PENDING,
                    now,
                    now,
                ),
            )
            task_id = int(cursor.lastrowid)
            conn.execute(
                """
                INSERT INTO transfer_events (task_id, level, message, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, "info", "Transfer task created.", now),
            )
            return task_id

    @staticmethod
    def _task_row(row: sqlite3.Row) -> Dict[str, Any]:
        task = dict(row)
        task["resolve_deep_link"] = bool(task.get("resolve_deep_link"))
        task["archive_by_author"] = bool(task.get("archive_by_author"))
        task["archive_title_source"] = normalize_archive_title_source(
            task.get("archive_title_source")
        )
        task["assignment_completed"] = bool(task.get("assignment_completed"))
        task["execution_mode"] = task.get("execution_mode") or ExecutionMode.WEB_QUEUE
        task["watch_id"] = task.get("watch_id") or None
        task["media_types"] = normalize_media_types(task.get("media_types"))
        return task

    def list_tasks(
        self,
        limit: int = 100,
        *,
        execution_mode: Optional[str] = None,
        exclude_execution_mode: Optional[str] = None,
        watch_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if execution_mode:
            clauses.append("execution_mode = ?")
            params.append(execution_mode)
        if exclude_execution_mode:
            clauses.append("(COALESCE(execution_mode, 'web_queue') != ?)")
            params.append(exclude_execution_mode)
        if watch_id:
            clauses.append("watch_id = ?")
            params.append(watch_id)
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM transfer_tasks
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
            return [self._task_row(row) for row in rows]

    def summarize_watch_inline_tasks_by_watch_id(self) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT watch_id, status, COUNT(*) AS count
                FROM transfer_tasks
                WHERE execution_mode = ?
                  AND watch_id IS NOT NULL
                  AND TRIM(watch_id) != ''
                GROUP BY watch_id, status
                """,
                (ExecutionMode.WATCH_INLINE,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_watch_inline_tasks_without_watch_id(
        self, limit: int = 5000
    ) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM transfer_tasks
                WHERE execution_mode = ?
                  AND (watch_id IS NULL OR TRIM(watch_id) = '')
                ORDER BY id DESC
                LIMIT ?
                """,
                (ExecutionMode.WATCH_INLINE, limit),
            ).fetchall()
            return [self._task_row(row) for row in rows]

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM transfer_tasks WHERE id = ?", (task_id,)
            ).fetchone()
            return self._task_row(row) if row else None

    def update_task(
        self,
        task_id: int,
        status: Optional[str] = None,
        total_items: Optional[int] = None,
        completed_items: Optional[int] = None,
        failed_items: Optional[int] = None,
        error_message: Optional[str] = None,
        started: bool = False,
        finished: bool = False,
        assignment_completed: Optional[bool] = None,
    ) -> None:
        task = self.get_task(task_id)
        if not task:
            return
        now = self.utc_now()
        values = {
            "status": status if status is not None else task["status"],
            "total_items": total_items
            if total_items is not None
            else task["total_items"],
            "completed_items": completed_items
            if completed_items is not None
            else task["completed_items"],
            "failed_items": failed_items
            if failed_items is not None
            else task["failed_items"],
            "error_message": error_message
            if error_message is not None
            else task["error_message"],
            "updated_at": now,
            "started_at": now
            if started and not task["started_at"]
            else task["started_at"],
            "finished_at": (
                now
                if finished
                else None
                if status
                in (
                    TransferStatus.PENDING,
                    TransferStatus.RUNNING,
                    TransferStatus.PAUSING,
                )
                else task["finished_at"]
            ),
            "assignment_completed": (
                int(assignment_completed)
                if assignment_completed is not None
                else int(task.get("assignment_completed") or 0)
            ),
        }
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE transfer_tasks
                SET status = :status,
                    total_items = :total_items,
                    completed_items = :completed_items,
                    failed_items = :failed_items,
                    error_message = :error_message,
                    updated_at = :updated_at,
                    started_at = :started_at,
                    finished_at = :finished_at,
                    assignment_completed = :assignment_completed
                WHERE id = :task_id
                """,
                {**values, "task_id": task_id},
            )

    def task_payload(
        self,
        task_id: int,
        item_limit: int = 200,
        item_offset: int = 0,
        event_limit: int = 100,
        event_offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            task = conn.execute(
                "SELECT * FROM transfer_tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if not task:
                return None
            total_items = conn.execute(
                "SELECT COUNT(*) FROM transfer_items WHERE task_id = ?", (task_id,)
            ).fetchone()[0]
            total_events = conn.execute(
                "SELECT COUNT(*) FROM transfer_events WHERE task_id = ?", (task_id,)
            ).fetchone()[0]
            items = conn.execute(
                """
                SELECT * FROM transfer_items
                WHERE task_id = ?
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                """,
                (task_id, item_limit, item_offset),
            ).fetchall()
            events = conn.execute(
                """
                SELECT * FROM transfer_events
                WHERE task_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (task_id, event_limit, event_offset),
            ).fetchall()
        return {
            "task": dict(task),
            "items": [dict(row) for row in items],
            "events": [dict(row) for row in events],
            "item_count": total_items,
            "event_count": total_events,
            "has_more_items": (item_offset + len(items)) < total_items,
            "has_more_events": (event_offset + len(events)) < total_events,
            "items_offset": item_offset,
            "events_offset": event_offset,
        }

    def task_summary(
        self, task_id: int, recent_event_limit: int = 30
    ) -> Optional[Dict[str, Any]]:
        """轻量级任务摘要查询——仅返回任务信息和计数，不加载 items/events 数组。
        用于 WebUI 轮询更新时避免重复加载大量数据。"""
        with self.connect() as conn:
            task = conn.execute(
                "SELECT * FROM transfer_tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if not task:
                return None
            total_items = conn.execute(
                "SELECT COUNT(*) FROM transfer_items WHERE task_id = ?", (task_id,)
            ).fetchone()[0]
            total_events = conn.execute(
                "SELECT COUNT(*) FROM transfer_events WHERE task_id = ?", (task_id,)
            ).fetchone()[0]
            recent_events = conn.execute(
                """
                SELECT * FROM transfer_events
                WHERE task_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (task_id, recent_event_limit),
            ).fetchall()
        return {
            "task": dict(task),
            "item_count": total_items,
            "event_count": total_events,
            "recent_events": [dict(row) for row in recent_events],
        }

    def aggregate_channel_download_stats(
        self,
        days: int = 7,
        tz_offset_minutes: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Aggregate terminal transfer items by source channel for a local window."""
        cutoff = self.local_calendar_window_start_utc(
            days=days,
            tz_offset_minutes=tz_offset_minutes,
        )
        terminal = (
            TransferStatus.SUCCESS,
            TransferStatus.FAILURE,
            TransferStatus.SKIPPED,
        )
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    CASE
                        WHEN source_folder IS NOT NULL AND TRIM(source_folder) != ''
                            THEN CASE
                                WHEN INSTR(REPLACE(TRIM(source_folder), '\\', '/'), '/') > 0
                                    THEN SUBSTR(
                                        REPLACE(TRIM(source_folder), '\\', '/'),
                                        1,
                                        INSTR(REPLACE(TRIM(source_folder), '\\', '/'), '/') - 1
                                    )
                                ELSE TRIM(source_folder)
                            END
                        WHEN source_chat_id IS NOT NULL AND TRIM(CAST(source_chat_id AS TEXT)) != ''
                            THEN TRIM(CAST(source_chat_id AS TEXT))
                        ELSE 'unknown'
                    END AS channel,
                    status,
                    COUNT(*) AS cnt
                FROM transfer_items
                WHERE updated_at >= ?
                  AND status IN (?, ?, ?)
                GROUP BY channel, status
                """,
                (cutoff, *terminal),
            ).fetchall()

        aggregated: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            channel = str(row["channel"] or "unknown")
            bucket = aggregated.setdefault(
                channel,
                {
                    "channel": channel,
                    "success": 0,
                    "failure": 0,
                    "skip": 0,
                    "total": 0,
                },
            )
            count = int(row["cnt"] or 0)
            status = str(row["status"] or "")
            if status == TransferStatus.SUCCESS:
                bucket["success"] += count
            elif status == TransferStatus.FAILURE:
                bucket["failure"] += count
            elif status == TransferStatus.SKIPPED:
                bucket["skip"] += count
            bucket["total"] = bucket["success"] + bucket["failure"] + bucket["skip"]

        return sorted(
            aggregated.values(),
            key=lambda item: (-int(item["total"]), str(item["channel"])),
        )

    def refresh_task_counts(
        self,
        task_id: int,
        expected_total: Optional[int] = None,
        assignment_completed: Optional[bool] = None,
    ) -> None:
        task = self.get_task(task_id)
        if not task:
            return
        expected = (
            expected_total if expected_total is not None else task.get("total_items")
        )
        with self.connect(run_maintenance=False) as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM transfer_items
                WHERE task_id = ?
                GROUP BY status
                """,
                (task_id,),
            ).fetchall()
        counts = {str(row["status"]): int(row["count"]) for row in rows}
        item_count = sum(counts.values())
        expected = int(expected or item_count)
        completed = counts.get(TransferStatus.SUCCESS, 0) + counts.get(
            TransferStatus.SKIPPED, 0
        )
        failed = counts.get(TransferStatus.FAILURE, 0)
        active = counts.get(TransferStatus.RUNNING, 0) + counts.get(
            TransferStatus.PENDING, 0
        )
        assigned = bool(task.get("assignment_completed"))
        if assignment_completed is not None:
            assigned = assignment_completed

        status = TransferStatus.RUNNING
        finished = False
        error_message = task.get("error_message")
        if task.get("status") == TransferStatus.PAUSED:
            status = TransferStatus.PAUSED
        elif task.get("status") == TransferStatus.PAUSING:
            status = TransferStatus.PAUSING
        elif task.get("status") == TransferStatus.PENDING:
            status = TransferStatus.PENDING

        # Only finalize after assignment is done. Range deep-link/comment tasks can
        # create more items than the message-span expected_total while still scanning;
        # finalizing on item_count >= expected would mark the whole task failed mid-run.
        can_finalize = assigned and active == 0

        if can_finalize:
            if item_count == 0:
                status = TransferStatus.FAILURE
                finished = True
                expected = 0
                if not error_message:
                    error_message = "No transfer items were produced."
            else:
                status = (
                    TransferStatus.FAILURE if failed > 0 else TransferStatus.SUCCESS
                )
                finished = True
                expected = item_count
        elif status == TransferStatus.PENDING and item_count == 0:
            status = TransferStatus.PENDING

        self.update_task(
            task_id=task_id,
            status=status,
            total_items=expected,
            completed_items=completed,
            failed_items=failed,
            error_message=error_message,
            finished=finished,
            assignment_completed=assigned,
        )

    def reconcile_active_tasks(
        self,
        *,
        min_interval_seconds: int = DEFAULT_RECONCILE_MIN_INTERVAL_SECONDS,
        force: bool = False,
        item_timeout_seconds: int | None = None,
        empty_watch_timeout_seconds: int = STALE_EMPTY_WATCH_INLINE_TIMEOUT_SECONDS,
    ) -> int:
        if getattr(self._tls, "reconciling", False):
            return 0
        now = datetime.datetime.now(datetime.UTC).timestamp()
        if not force and now - self._last_reconcile_check < max(
            1, int(min_interval_seconds)
        ):
            return 0
        self._last_reconcile_check = now
        self._tls.reconciling = True
        try:
            changed = 0
            resolved_item_timeout = (
                int(item_timeout_seconds)
                if item_timeout_seconds is not None
                else self.resolve_item_stale_timeout_seconds()
            )
            changed += self._fail_stale_active_items(resolved_item_timeout)
            changed += self._fail_stale_empty_watch_inline_tasks(
                empty_watch_timeout_seconds
            )

            with self.connect(run_maintenance=False) as conn:
                rows = conn.execute(
                    """
                    SELECT id
                    FROM transfer_tasks
                    WHERE status IN (?, ?, ?)
                    """,
                    (
                        TransferStatus.PENDING,
                        TransferStatus.RUNNING,
                        TransferStatus.PAUSING,
                    ),
                ).fetchall()
            for row in rows:
                task_id = int(row["id"])
                before = self.get_task(task_id)
                self.refresh_task_counts(task_id)
                after = self.get_task(task_id)
                if (
                    before
                    and after
                    and (
                        before.get("status") != after.get("status")
                        or bool(before.get("finished")) != bool(after.get("finished"))
                    )
                ):
                    changed += 1
            return changed
        finally:
            self._tls.reconciling = False

    def _fail_stale_active_items(self, timeout_seconds: int) -> int:
        cutoff = self._iso_before_now(timeout_seconds)
        timeout_label = max(1, int(timeout_seconds) // 60)
        with self.connect(run_maintenance=False) as conn:
            rows = conn.execute(
                """
                SELECT id, task_id
                FROM transfer_items
                WHERE status IN (?, ?)
                  AND updated_at < ?
                """,
                (TransferStatus.PENDING, TransferStatus.RUNNING, cutoff),
            ).fetchall()
        if not rows:
            return 0
        now = self.utc_now()
        message = (
            f"转存项超过{timeout_label}分钟无进展，已超时失败 "
            f"(timed out after {timeout_label} minutes without progress)."
        )
        affected_tasks: set[int] = set()
        logger = self._stale_item_logger
        with self.connect(run_maintenance=False) as conn:
            for row in rows:
                item_id = int(row["id"])
                task_id = int(row["task_id"])
                conn.execute(
                    """
                    UPDATE transfer_items
                    SET status = ?,
                        phase = 'failure',
                        error_message = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (TransferStatus.FAILURE, message, now, item_id),
                )
                affected_tasks.add(task_id)
                if callable(logger):
                    try:
                        logger(item_id, task_id, message)
                    except Exception:
                        pass
        for task_id in affected_tasks:
            self.add_event(task_id, message, level="warning")
            self.refresh_task_counts(task_id)
        return len(rows)

    def _fail_stale_empty_watch_inline_tasks(self, timeout_seconds: int) -> int:
        cutoff = self._iso_before_now(timeout_seconds)
        timeout_label = max(1, int(timeout_seconds) // 60)
        with self.connect(run_maintenance=False) as conn:
            rows = conn.execute(
                """
                SELECT t.id
                FROM transfer_tasks AS t
                LEFT JOIN transfer_items AS i ON i.task_id = t.id
                WHERE t.execution_mode = ?
                  AND t.status IN (?, ?, ?)
                  AND COALESCE(t.assignment_completed, 0) = 1
                  AND COALESCE(t.updated_at, t.created_at) < ?
                GROUP BY t.id
                HAVING COUNT(i.id) = 0
                """,
                (
                    ExecutionMode.WATCH_INLINE,
                    TransferStatus.PENDING,
                    TransferStatus.RUNNING,
                    TransferStatus.PAUSING,
                    cutoff,
                ),
            ).fetchall()
        changed = 0
        message = (
            f"Watch inline download timed out after {timeout_label} minutes "
            f"without producing transfer items."
        )
        for row in rows:
            task_id = int(row["id"])
            self.update_task(
                task_id,
                status=TransferStatus.FAILURE,
                total_items=0,
                completed_items=0,
                failed_items=0,
                error_message=message,
                finished=True,
            )
            self.add_event(task_id, message, level="warning")
            changed += 1
        return changed

    def update_task_range_runtime(
        self,
        task_id: int,
        *,
        current_range_message_id: Optional[int] = None,
        current_range_video_captured: Optional[int] = None,
        current_range_video_index: Optional[int] = None,
    ) -> None:
        task = self.get_task(task_id)
        if not task:
            return
        fields: dict[str, Any] = {"updated_at": self.utc_now()}
        if current_range_message_id is not None:
            fields["current_range_message_id"] = int(current_range_message_id)
        if current_range_video_captured is not None:
            fields["current_range_video_captured"] = max(
                0, int(current_range_video_captured)
            )
        if current_range_video_index is not None:
            fields["current_range_video_index"] = max(0, int(current_range_video_index))
        if len(fields) <= 1:
            return
        set_clause = ", ".join([f"{key} = :{key}" for key in fields])
        with self.connect() as conn:
            conn.execute(
                f"UPDATE transfer_tasks SET {set_clause} WHERE id = :task_id",
                {**fields, "task_id": int(task_id)},
            )

    def range_transfer_progress(self, task: dict[str, Any]) -> Optional[dict[str, int]]:
        start_id = task.get("start_id")
        end_id = task.get("end_id")
        if start_id is None or end_id is None:
            return None
        start_id = int(start_id)
        end_id = int(end_id)
        if end_id < start_id:
            return None

        task_id = int(task.get("id") or 0)
        terminal_statuses = {
            TransferStatus.SUCCESS,
            TransferStatus.SKIPPED,
            TransferStatus.FAILURE,
        }
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    COALESCE(
                        range_message_id,
                        CASE
                            WHEN source_message_id BETWEEN ? AND ? THEN source_message_id
                        END
                    ) AS range_id,
                    status,
                    COUNT(*) AS count
                FROM transfer_items
                WHERE task_id = ?
                GROUP BY range_id, status
                HAVING range_id IS NOT NULL
                """,
                (start_id, end_id, task_id),
            ).fetchall()

        counts_by_range: dict[int, dict[str, int]] = {}
        for row in rows:
            range_id = int(row["range_id"])
            if not (start_id <= range_id <= end_id):
                continue
            counts_by_range.setdefault(range_id, {})[str(row["status"])] = int(
                row["count"]
            )

        total_ids = end_id - start_id + 1
        completed_ids = 0
        # First incomplete id in assignment order (for detail when runtime cursor is absent).
        first_incomplete_id: Optional[int] = None
        first_incomplete_video_total = 0
        first_incomplete_video_done = 0
        first_incomplete_video_index = 0

        # Count every fully-terminal range id, not only the contiguous prefix from
        # start_id. Deep-link / download-fallback assignment walks the interval and
        # advances current_range_message_id while earlier posts may still have
        # RUNNING items; freezing completed_ids at the first hole leaves the bar at
        # 0% while the main-post ID keeps moving.
        for message_id in range(start_id, end_id + 1):
            status_counts = counts_by_range.get(message_id)
            if not status_counts:
                if first_incomplete_id is None:
                    first_incomplete_id = message_id
                continue

            total_videos = sum(status_counts.values())
            done_videos = sum(
                status_counts.get(status, 0) for status in terminal_statuses
            )
            if done_videos >= total_videos and total_videos > 0:
                completed_ids += 1
                continue

            if first_incomplete_id is None:
                first_incomplete_id = message_id
                first_incomplete_video_total = total_videos
                first_incomplete_video_done = done_videos
                active_videos = status_counts.get(
                    TransferStatus.RUNNING, 0
                ) + status_counts.get(TransferStatus.PENDING, 0)
                first_incomplete_video_index = done_videos + (1 if active_videos else 0)

        current_id = first_incomplete_id
        video_total = first_incomplete_video_total
        video_done = first_incomplete_video_done
        video_index = first_incomplete_video_index

        runtime_current_id = task.get("current_range_message_id")
        runtime_captured = int(task.get("current_range_video_captured") or 0)
        runtime_index = int(task.get("current_range_video_index") or 0)
        if runtime_current_id is not None:
            runtime_current_id = int(runtime_current_id)
            if current_id is None or runtime_current_id >= current_id:
                current_id = runtime_current_id
            # Prefer per-id item counts for the displayed runtime cursor when present.
            runtime_counts = counts_by_range.get(runtime_current_id)
            if runtime_counts:
                runtime_total = sum(runtime_counts.values())
                runtime_done = sum(
                    runtime_counts.get(status, 0) for status in terminal_statuses
                )
                if runtime_done < runtime_total or runtime_total == 0:
                    video_total = runtime_total
                    video_done = runtime_done
                    active_videos = runtime_counts.get(
                        TransferStatus.RUNNING, 0
                    ) + runtime_counts.get(TransferStatus.PENDING, 0)
                    video_index = runtime_done + (1 if active_videos else 0)
            if runtime_captured > video_total:
                video_total = runtime_captured
            if runtime_index > video_index:
                video_index = runtime_index

        progress_percent = (
            min(100, round((completed_ids / total_ids) * 100)) if total_ids else 0
        )

        assignment_done = bool(task.get("assignment_completed"))
        task_status = str(task.get("status") or "")
        task_finished = bool(task.get("finished_at"))
        if (
            assignment_done
            and task_finished
            and task_status in (TransferStatus.SUCCESS, TransferStatus.SKIPPED)
        ):
            # Legacy tasks may finish assignment before every non-transferable ID received
            # an explicit skipped placeholder; treat empty holes as done for display.
            for message_id in range(start_id, end_id + 1):
                if message_id not in counts_by_range:
                    completed_ids += 1
            progress_percent = (
                min(100, round((completed_ids / total_ids) * 100)) if total_ids else 0
            )
            if completed_ids >= total_ids:
                current_id = None
                video_total = 0
                video_done = 0
                video_index = 0

        return {
            "range_total_ids": total_ids,
            "range_completed_ids": completed_ids,
            "range_progress_percent": progress_percent,
            "current_range_message_id": current_id,
            "current_range_video_total": video_total,
            "current_range_video_done": video_done,
            "current_range_video_index": video_index,
            "current_range_video_captured": runtime_captured,
            "uses_range_progress": True,
        }

    def retry_failed_items(self, task_id: int) -> int:
        task = self.get_task(task_id)
        if not task:
            return 0
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id FROM transfer_items
                WHERE task_id = ? AND status = ?
                ORDER BY id ASC
                """,
                (task_id, TransferStatus.FAILURE),
            ).fetchall()
            failed_item_ids = [int(row["id"]) for row in rows]
        return self.retry_failed_item_ids(task_id, failed_item_ids)

    def retry_failed_item_ids(self, task_id: int, item_ids: List[int]) -> int:
        task = self.get_task(task_id)
        if not task:
            return 0
        item_ids = [int(item_id) for item_id in item_ids]
        if not item_ids:
            return 0
        now = self.utc_now()
        placeholders = ",".join(["?"] * len(item_ids))
        with self.connect() as conn:
            cursor = conn.execute(
                f"""
                UPDATE transfer_items
                SET status = ?,
                    phase = 'pending',
                    download_current = 0,
                    upload_current = 0,
                    error_message = NULL,
                    updated_at = ?
                WHERE task_id = ?
                  AND status = ?
                  AND id IN ({placeholders})
                """,
                (
                    TransferStatus.PENDING,
                    now,
                    task_id,
                    TransferStatus.FAILURE,
                    *item_ids,
                ),
            )
            reset_items = int(cursor.rowcount)
        if reset_items:
            self.refresh_task_counts(task_id)
            self.update_task(
                task_id, status=TransferStatus.RUNNING, error_message="", finished=False
            )
            self.add_event(task_id, f"Retry failed items requested: {reset_items}.")
        return reset_items

    def delete_task(self, task_id: int) -> bool:
        with self.connect() as conn:
            cursor = conn.execute("DELETE FROM transfer_tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    def upsert_download_success_record(
        self,
        source_chat_id: str,
        source_message_id: int,
        source_link: Optional[str],
        media_type: Optional[str],
        local_path: str,
        file_size: Optional[int],
        file_name: Optional[str],
    ) -> None:
        now = self.utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO download_success_records (
                    source_chat_id, source_message_id, source_link, media_type,
                    local_path, file_size, file_name, downloaded_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_chat_id, source_message_id) DO UPDATE SET
                    source_link = excluded.source_link,
                    media_type = excluded.media_type,
                    local_path = excluded.local_path,
                    file_size = excluded.file_size,
                    file_name = excluded.file_name,
                    updated_at = excluded.updated_at
                """,
                (
                    str(source_chat_id),
                    int(source_message_id),
                    source_link,
                    media_type,
                    local_path,
                    file_size,
                    file_name,
                    now,
                    now,
                ),
            )

    def get_download_success_record(
        self,
        source_chat_id: str,
        source_message_id: int,
        expected_size: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM download_success_records
                WHERE source_chat_id = ? AND source_message_id = ?
                """,
                (str(source_chat_id), int(source_message_id)),
            ).fetchone()
        if not row:
            return None
        record = dict(row)
        local_path = record.get("local_path")
        if not local_path or not os.path.isfile(local_path):
            return None
        size_to_check = (
            expected_size if expected_size is not None else record.get("file_size")
        )
        if size_to_check is not None and os.path.getsize(local_path) != int(
            size_to_check
        ):
            return None
        return record

    def count_download_success_records(self) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM download_success_records"
            ).fetchone()
            return int(row["total"] if row else 0)

    def list_download_success_records(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM download_success_records
                ORDER BY updated_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
            return [dict(row) for row in rows]

    def clear_download_success_records(self) -> int:
        with self.connect() as conn:
            cursor = conn.execute("DELETE FROM download_success_records")
            conn.commit()
            return int(cursor.rowcount or 0)
