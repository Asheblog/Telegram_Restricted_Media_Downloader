# coding=UTF-8
"""把操作应用方法改为委派到 WebOperationApplicator。"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
OPS = REPO / "module" / "webops" / "operations.py"
text = OPS.read_text(encoding="utf-8")

START = "    async def process_web_operation(self, operation_id: str) -> None:\n"
END = "    def _ensure_task_queue_ops(self):\n"
i = text.index(START)
j = text.index(END)

DELEGATE = '''    def _ensure_operation_applicator(self):
        """操作应用编排实例（懒建并缓存；实现见 module.webops.operation_applicator）。"""
        ops = self.__dict__.get('_operation_applicator_impl')
        if ops is None:
            from module.webops.operation_applicator import WebOperationApplicator

            ops = WebOperationApplicator(
                web_operations_getter=lambda: getattr(self, 'web_operations', {}),
                app_getter=lambda: getattr(self, 'app', None),
                gc_getter=lambda: getattr(self, 'gc', None),
                uploader_getter=lambda: getattr(self, 'uploader', None),
                set_uploader=lambda value: setattr(self, 'uploader', value),
                runtime_message_filter_getter=lambda: (
                    self.runtime_message_filter()
                    if hasattr(self, 'runtime_message_filter')
                    else None
                ),
                watch_applicator_getter=self._ensure_watch_applicator,
                persisted_watch_records_getter=self._persisted_watch_records,
                listen_download_chat_getter=lambda: getattr(
                    self, 'listen_download_chat', {}
                ),
                listen_forward_chat_getter=lambda: getattr(
                    self, 'listen_forward_chat', {}
                ),
                web_pending_watches_getter=lambda: getattr(
                    self, 'web_pending_watches', {}
                ),
                set_live_watch_status=self._set_live_watch_status,
                mark_pending_watch=self.mark_pending_watch,
                watch_payload_from_record=self._watch_payload_from_record,
                create_download_task=self.create_download_task,
                uploader_context=self,
            )
            self._operation_applicator_impl = ops
        return ops

    async def process_web_operation(self, operation_id: str) -> None:
        return await self._ensure_operation_applicator().process_web_operation(operation_id)

    async def restore_live_transfer_watches(self) -> None:
        return await self._ensure_operation_applicator().restore_live_transfer_watches()

    async def apply_web_watch(self, payload: dict) -> None:
        return await self._ensure_operation_applicator().apply_web_watch(payload)

    def remove_web_watch(self, watch_id: str) -> bool:
        return self._ensure_operation_applicator().remove_web_watch(watch_id)

    async def apply_web_upload(self, payload: dict) -> None:
        return await self._ensure_operation_applicator().apply_web_upload(payload)

    async def apply_web_channel_download(self, payload: dict) -> None:
        return await self._ensure_operation_applicator().apply_web_channel_download(payload)

'''
text = text[:i] + DELEGATE + text[j:]
OPS.write_text(text, encoding="utf-8")
print("delegated; lines:", len(text.splitlines()))
