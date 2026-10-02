# coding=UTF-8
"""把任务队列方法改为委派到 TaskQueueOperations。"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
OPS = REPO / "module" / "webops" / "operations.py"
text = OPS.read_text(encoding="utf-8")

START = "    async def process_web_task_queue(self) -> None:\n"
END = "\n\n    def list_deferred_discussion_captures(self, watch_id: str) -> dict:\n"
i = text.index(START)
j = text.index(END)

DELEGATE = '''    def _ensure_task_queue_ops(self):
        """任务队列编排实例（懒建并缓存；实现见 module.webops.task_queue）。"""
        ops = self.__dict__.get('_task_queue_ops_impl')
        if ops is None:
            from module.webops.task_queue import TaskQueueOperations

            ops = TaskQueueOperations(
                web_task_manager_getter=lambda: getattr(self, 'web_task_manager', None),
                web_task_queue_getter=lambda: getattr(self, 'web_task_queue', None),
                web_operation_queue_getter=lambda: getattr(
                    self, 'web_operation_queue', None
                ),
                submitted_task_ids_getter=lambda: getattr(
                    self, 'web_submitted_task_ids', set()
                ),
                running_task_getter=lambda: getattr(self, 'web_running_task', None),
                running_task_setter=lambda value: setattr(
                    self, 'web_running_task', value
                ),
                running_task_id_getter=lambda: getattr(
                    self, 'web_running_task_id', None
                ),
                running_task_id_setter=lambda value: setattr(
                    self, 'web_running_task_id', value
                ),
                transfer_store_getter=lambda: getattr(self, 'transfer_store', None),
                loop_getter=lambda: getattr(self, 'loop', None),
                process_web_transfer_task=self.process_web_transfer_task,
                process_web_operation=self.process_web_operation,
            )
            self._task_queue_ops_impl = ops
        return ops

    async def process_web_task_queue(self) -> None:
        return await self._ensure_task_queue_ops().process_web_task_queue()

    def start_next_web_transfer_task(self) -> None:
        return self._ensure_task_queue_ops().start_next_web_transfer_task()

    def is_web_transfer_task_schedulable(self, task_id: int) -> bool:
        return self._ensure_task_queue_ops().is_web_transfer_task_schedulable(task_id)

    def finish_web_transfer_task(self, task_id: Optional[int], completed_task: asyncio.Task) -> None:
        return self._ensure_task_queue_ops().finish_web_transfer_task(task_id, completed_task)
'''
text = text[:i] + DELEGATE + text[j + 2:]
OPS.write_text(text, encoding="utf-8")
print("delegated; lines:", len(text.splitlines()))
