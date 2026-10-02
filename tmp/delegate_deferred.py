# coding=UTF-8
"""把延迟抓取相关方法改为委派到 DeferredDiscussionOperations。"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
OPS = REPO / "module" / "webops" / "operations.py"
text = OPS.read_text(encoding="utf-8")

START = "    def _ensure_comment_delay_scheduler(self) -> CommentDelayScheduler:\n"
END = "    def _web_ui_operations(self) -> 'WebOperationsFacade':\n"
i = text.index(START)
j = text.index(END)

DELEGATE = '''    def _ensure_deferred_discussion_ops(self):
        """延迟抓取编排实例（懒建并缓存；实现见 module.webops.deferred_discussion）。"""
        ops = self.__dict__.get('_deferred_discussion_ops_impl')
        if ops is None:
            from module.webops.deferred_discussion import DeferredDiscussionOperations

            ops = DeferredDiscussionOperations(
                transfer_store_getter=self._ensure_transfer_store,
                user_getter=lambda: getattr(self, 'user', None),
                app_getter=lambda: getattr(self, 'app', None),
                gc_getter=lambda: getattr(self, 'gc', None),
                loop_getter=lambda: getattr(self, 'loop', None),
                # 经实例解析：宿主/测试替身会覆盖这些方法。
                forward_discussion_replies=lambda *a, **kw: self.forward_discussion_replies(
                    *a, **kw
                ),
                record_watch_event=lambda *a, **kw: self._record_watch_event(*a, **kw),
                delete_web_task=lambda task_id: self.delete_web_task(task_id),
            )
            self._deferred_discussion_ops_impl = ops
        return ops

    def _ensure_comment_delay_scheduler(self) -> CommentDelayScheduler:
        return self._ensure_deferred_discussion_ops().ensure_scheduler()

    def _has_active_derived_tasks_for_deferred_capture(self, capture: dict) -> bool:
        return self._ensure_deferred_discussion_ops().has_active_derived_tasks(capture)

    def _cancel_derived_tasks_for_deferred_capture(self, capture: dict) -> None:
        """Best-effort cancel web transfer tasks spawned by a running deferred capture."""
        return self._ensure_deferred_discussion_ops().cancel_derived_tasks(capture)

    async def schedule_or_forward_discussion_replies(
            self,
            *,
            client,
            source_chat_id,
            source_message_id: int,
            target_chat_id,
            target_link: str,
            watch_id: Optional[str] = None,
            done_notice: Optional[bool] = True,
    ) -> Optional[dict]:
        return await self._ensure_deferred_discussion_ops().schedule_or_forward(
            client=client,
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            target_chat_id=target_chat_id,
            target_link=target_link,
            watch_id=watch_id,
            done_notice=done_notice,
        )

'''
text = text[:i] + DELEGATE + text[j:]
OPS.write_text(text, encoding="utf-8")
print("delegated; lines:", len(text.splitlines()))
