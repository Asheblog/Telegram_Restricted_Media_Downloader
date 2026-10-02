# coding=UTF-8
"""把安装向导方法改为委派到 SetupWizardOperations（按行号区间精确替换）。"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
OPS = REPO / "module" / "webops" / "operations.py"
text = OPS.read_text(encoding="utf-8")

START = "    def is_setup_ready(self) -> bool:\n"
END = "    async def process_web_operation(self, operation_id: str) -> None:\n"
i = text.index(START)
j = text.index(END)

DELEGATE = '''    def _ensure_setup_wizard_ops(self):
        """安装向导编排实例（懒建并缓存；实现见 module.webops.setup_wizard）。"""
        ops = self.__dict__.get('_setup_wizard_ops_impl')
        if ops is None:
            from module.webops.setup_wizard import SetupWizardOperations

            ops = SetupWizardOperations(
                app_getter=lambda: getattr(self, 'app', None),
                loop_getter=lambda: getattr(self, 'loop', None),
                setup_coordinator_getter=lambda: self._setup_coordinator(),
                auth_provider_getter=lambda: self.__dict__.get('web_ui_auth'),
                api_credentials_event_getter=lambda: self.__dict__.get(
                    '_api_credentials_event'
                ),
                archive_settings_getter=lambda: self._archive_settings(),
                set_archive_settings=lambda **kw: self._set_archive_settings(**kw),
                pikpak_accounts_getter=lambda: self._pikpak_accounts(),
                set_pikpak_accounts=lambda accounts: self._set_pikpak_accounts(accounts),
                invalidate_pikpak_archive_client=self._invalidate_pikpak_archive_client,
            )
            self._setup_wizard_ops_impl = ops
        return ops

    def is_setup_ready(self) -> bool:
        return self._ensure_setup_wizard_ops().is_setup_ready()

    def get_setup_status(self) -> dict:
        return self._ensure_setup_wizard_ops().get_setup_status()

    def save_setup_api_credentials(self, payload: dict) -> dict:
        return self._ensure_setup_wizard_ops().save_setup_api_credentials(payload)

    def configure_setup_rclone(self, payload: dict) -> dict:
        return self._ensure_setup_wizard_ops().configure_setup_rclone(payload)

    def skip_setup_rclone(self, payload: Optional[dict] = None) -> dict:
        return self._ensure_setup_wizard_ops().skip_setup_rclone(payload)

    def test_setup_rclone(self, payload: Optional[dict] = None) -> dict:
        return self._ensure_setup_wizard_ops().test_setup_rclone(payload)

    def save_setup_bot_token(self, payload: dict) -> dict:
        return self._ensure_setup_wizard_ops().save_setup_bot_token(payload)

    def skip_setup_bot_token(self, payload: Optional[dict] = None) -> dict:
        return self._ensure_setup_wizard_ops().skip_setup_bot_token(payload)

'''
text = text[:i] + DELEGATE + text[j:]
OPS.write_text(text, encoding="utf-8")
print("delegated; lines:", len(text.splitlines()))
