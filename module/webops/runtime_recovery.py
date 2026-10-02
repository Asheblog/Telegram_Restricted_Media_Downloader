# coding=UTF-8
"""WebUI 运行时恢复编排。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出：进程启动/WebUI 起来后
把上一轮残留的状态恢复过来 —— 未完成的转存任务重新入队、PAUSING 无在途项时落为
PAUSED、待归档的 PikPak 任务继续、僵尸任务对账、评论延迟调度器与归档整理任务续跑。

依赖全部以回调注入（不持有宿主），因此可以脱离宿主单独测试。
"""
from __future__ import annotations

from typing import Callable

from module import log
from module.persistence.transfer_store import TransferStatus


class RuntimeRecoveryOperations:
    """启动期状态恢复。"""

    def __init__(
        self,
        *,
        transfer_store_getter: Callable[[], object],
        diagnostic_getter: Callable[[], object],
        submit_web_task: Callable[[int], None],
        progress_tracker_getter: Callable[[], object],
        ensure_comment_delay_scheduler: Callable[[], object],
        resume_interrupted_archive_author_jobs: Callable[[], int],
    ) -> None:
        self._transfer_store = transfer_store_getter
        self._diagnostic = diagnostic_getter
        self._submit_web_task = submit_web_task
        self._progress_tracker = progress_tracker_getter
        self._ensure_comment_delay_scheduler = ensure_comment_delay_scheduler
        self._resume_archive_author_jobs = resume_interrupted_archive_author_jobs

    def recover(self) -> None:
        """Setup Ready 之后恢复未完成的转存任务与归档。"""
        store = self._transfer_store()
        if not store:
            return
        from module.transfer.watch_inline import is_watch_inline_task

        for task in store.list_tasks():
            status = task.get("status")
            task_id = int(task.get("id"))
            if is_watch_inline_task(task):
                continue
            if status == TransferStatus.PAUSING:
                has_active_item = any(
                    item.get("status") in (TransferStatus.PENDING, TransferStatus.RUNNING)
                    for item in store.list_items(task_id)
                )
                if has_active_item:
                    self._submit_web_task(task_id)
                else:
                    store.update_task(task_id, status=TransferStatus.PAUSED)
                    store.add_event(
                        task_id,
                        "Transfer task paused after restart with no in-flight item.",
                        level="warning",
                    )
                continue
            if status not in (
                TransferStatus.PENDING,
                TransferStatus.RUNNING,
                TransferStatus.FAILURE,
            ):
                continue
            self._submit_web_task(task_id)

        recovered_archives = 0
        progress_tracker = self._progress_tracker()
        if progress_tracker is not None:
            recovered_archives = progress_tracker.recover_pending_upload_archives()
        if recovered_archives:
            self._diagnostic().info(
                f"Recovered {recovered_archives} pending PikPak upload archive job(s)."
            )

        store = self._transfer_store()
        if store:
            reconcile = getattr(store, "reconcile_active_tasks", None)
            if callable(reconcile):
                reconciled = reconcile(force=True)
                if reconciled:
                    self._diagnostic().info(
                        f"Reconciled {reconciled} stale transfer task(s)."
                    )

        try:
            self._ensure_comment_delay_scheduler()
        except Exception as e:  # noqa: BLE001 - 恢复失败不应阻断启动
            log.debug(f"Comment delay scheduler start skipped: {e}")
        try:
            self._resume_archive_author_jobs()
        except Exception as e:  # noqa: BLE001 - 同上
            log.debug(f"Archive author reorganize resume skipped: {e}")
