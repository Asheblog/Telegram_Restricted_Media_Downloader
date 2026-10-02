# coding=UTF-8
"""WebUI 转存任务队列编排。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出的第七组：队列消费、
启动下一个任务、可调度性判定、完成收尾。

## 为什么保留"宿主优先、本地兜底"两条分支
宿主（真实装配）总有 ``web_task_manager``，此时本类只是转发；而裸宿主
（测试替身、恢复路径）没有它，需要自己按 transfer_store 判定。
两条分支的判定依据**本来就不同**（`web_task_manager` 的策略 vs
`transfer_store` 的状态字段），审计时被记为"同一语义两份实现"。
本次搬运**保持原样**：把行为一致性留给后续统一（改判定等于改行为，
不该混在搬运提交里）。已在此处标注，避免读者以为是复制粘贴。
"""
from __future__ import annotations

import asyncio
from typing import Callable, Optional

from module import log
from module.core.enums import KeyWord
from module.persistence.transfer_store import TransferStatus
from module.utils.language import _t


class TaskQueueOperations:
    """WebUI 转存任务队列：串行启动、暂停/失败收尾、操作队列消费。"""

    def __init__(
        self,
        *,
        web_task_manager_getter: Callable[[], object],
        web_task_queue_getter: Callable[[], object],
        web_operation_queue_getter: Callable[[], object],
        submitted_task_ids_getter: Callable[[], set],
        running_task_getter: Callable[[], object],
        running_task_setter: Callable[[object], None],
        running_task_id_getter: Callable[[], Optional[int]],
        running_task_id_setter: Callable[[Optional[int]], None],
        transfer_store_getter: Callable[[], object],
        loop_getter: Callable[[], object],
        process_web_transfer_task: Callable[[int], object],
        process_web_operation: Callable[[str], object],
    ) -> None:
        self._web_task_manager = web_task_manager_getter
        self._web_task_queue = web_task_queue_getter
        self._web_operation_queue = web_operation_queue_getter
        self._submitted_task_ids = submitted_task_ids_getter
        self._running_task = running_task_getter
        self._set_running_task = running_task_setter
        self._running_task_id = running_task_id_getter
        self._set_running_task_id = running_task_id_setter
        self._transfer_store = transfer_store_getter
        self._loop = loop_getter
        self._process_web_transfer_task = process_web_transfer_task
        self._process_web_operation = process_web_operation

    async def process_web_task_queue(self) -> None:
        self.start_next_web_transfer_task()
        while not self._web_task_queue().empty():
            if self._running_task() and not self._running_task().done():
                break
            self.start_next_web_transfer_task()
            if self._running_task() and not self._running_task().done():
                break
        while not self._web_operation_queue().empty():
            operation_id = await self._web_operation_queue().get()
            try:
                await self._process_web_operation(operation_id)
            finally:
                self._web_operation_queue().task_done()

    def start_next_web_transfer_task(self) -> None:
        wm = self._web_task_manager()
        if wm is not None:
            return wm.start_next_web_transfer_task()
        running = self._running_task()
        if running and not running.done():
            return
        if running and running.done():
            self.finish_web_transfer_task(self._running_task_id(), running)
        queue = self._web_task_queue()
        while not queue.empty():
            try:
                task_id = int(queue.get_nowait())
            except asyncio.QueueEmpty:
                return
            try:
                if not self.is_web_transfer_task_schedulable(task_id):
                    self._submitted_task_ids().discard(task_id)
                    continue
                runner = self._loop().create_task(self._process_web_transfer_task(task_id))
                self._set_running_task(runner)
                self._set_running_task_id(task_id)
                runner.add_done_callback(
                    lambda completed_task, completed_task_id=task_id: self.finish_web_transfer_task(
                        completed_task_id,
                        completed_task,
                    )
                )
                return
            finally:
                queue.task_done()

    def is_web_transfer_task_schedulable(self, task_id: int) -> bool:
        wm = self._web_task_manager()
        if wm is not None:
            return wm.is_web_transfer_task_schedulable(task_id)
        store = self._transfer_store()
        if not store:
            return False
        task = store.get_task(task_id)
        if not task:
            return False
        from module.transfer.watch_inline import is_watch_inline_task

        if is_watch_inline_task(task):
            return False
        return task.get("status") in (
            TransferStatus.PENDING,
            TransferStatus.RUNNING,
            TransferStatus.PAUSING,
            TransferStatus.FAILURE,
        )

    def finish_web_transfer_task(
        self, task_id: Optional[int], completed_task: asyncio.Task
    ) -> None:
        wm = self._web_task_manager()
        if wm is not None:
            return wm.finish_web_transfer_task(task_id, completed_task)
        if task_id is not None:
            self._submitted_task_ids().discard(task_id)
        if self._running_task() is completed_task:
            self._set_running_task(None)
            self._set_running_task_id(None)
        if not completed_task.cancelled():
            error = completed_task.exception()
            if error:
                log.error(
                    f'WebUI转存任务执行失败:{task_id},{_t(KeyWord.REASON)}:"{error}"',
                    exc_info=(type(error), error, error.__traceback__),
                )
        if not self._web_task_queue().empty():
            self._loop().create_task(self.process_web_task_queue())
