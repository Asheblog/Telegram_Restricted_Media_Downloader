# coding=UTF-8
"""把 recover_web_runtime 改为委派到 RuntimeRecoveryOperations。"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
OPS = REPO / "module" / "webops" / "operations.py"
text = OPS.read_text(encoding="utf-8")

START = "    def recover_web_runtime(self) -> None:\n"
END = "    def _archive_settings(self) -> dict:\n"
i = text.index(START)
j = text.index(END)

DELEGATE = '''    def _ensure_runtime_recovery_ops(self):
        """运行时恢复编排实例（懒建并缓存；实现见 module.webops.runtime_recovery）。"""
        ops = self.__dict__.get('_runtime_recovery_ops_impl')
        if ops is None:
            from module.webops.runtime_recovery import RuntimeRecoveryOperations

            ops = RuntimeRecoveryOperations(
                transfer_store_getter=lambda: getattr(self, 'transfer_store', None),
                diagnostic_getter=lambda: getattr(self, 'diagnostic', None),
                submit_web_task=self.submit_web_task,
                progress_tracker_getter=lambda: getattr(self, 'progress_tracker', None),
                ensure_comment_delay_scheduler=self._ensure_comment_delay_scheduler,
                resume_interrupted_archive_author_jobs=self.resume_interrupted_archive_author_jobs,
            )
            self._runtime_recovery_ops_impl = ops
        return ops

    def recover_web_runtime(self) -> None:
        """Resume pending web tasks / archives after Setup Ready."""
        return self._ensure_runtime_recovery_ops().recover()

'''
text = text[:i] + DELEGATE + text[j:]
OPS.write_text(text, encoding="utf-8")
print("delegated; lines:", len(text.splitlines()))
