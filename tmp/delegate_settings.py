# coding=UTF-8
"""把 WebOperationsMixin 的设置/PikPak 账号方法改为委派到 SettingsOperations。

按行号区间精确替换（先读原文件确认边界），避免误伤相邻组。
"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
OPS = REPO / "module" / "webops" / "operations.py"
text = OPS.read_text(encoding="utf-8")

# 1) 用委派替换 get_web_settings / update_web_settings 的整段实现
START = "    def get_web_settings(self) -> dict:\n"
END = "    def start_web_ui(self, with_auth_provider: bool = False"

i = text.index(START)
j = text.index(END)
DELEGATE = '''    def _ensure_settings_ops(self):
        """设置/PikPak 账号编排实例（懒建并缓存；实现见 module.webops.settings_operations）。"""
        ops = self.__dict__.get('_settings_ops_impl')
        if ops is None:
            from module.webops.settings_operations import SettingsOperations
            ops = SettingsOperations(
                app_getter=lambda: getattr(self, 'app', None),
                gc_getter=lambda: getattr(self, 'gc', None),
                download_upload_window_getter=lambda: getattr(
                    self, 'download_upload_window', None
                ),
                local_storage_guard_getter=lambda: getattr(
                    self, 'local_storage_guard', None
                ),
                pikpak_manager_getter=lambda: getattr(self, 'pikpak_manager', None),
                setup_coordinator_getter=self._setup_coordinator,
            )
            self._settings_ops_impl = ops
        return ops

    def get_web_settings(self) -> dict:
        return self._ensure_settings_ops().get_web_settings()

    def update_web_settings(self, payload: dict) -> dict:
        return self._ensure_settings_ops().update_web_settings(payload)

'''
text = text[:i] + DELEGATE + text[j:]

# 2) 归档设置 + 账号组：从 _archive_settings 起，到 is_setup_ready 前
START2 = "    def _archive_settings(self) -> dict:\n"
END2 = "    def is_setup_ready(self) -> bool:\n"
i2 = text.index(START2)
j2 = text.index(END2)
ACCOUNT_DELEGATE = '''    def _archive_settings(self) -> dict:
        return self._ensure_settings_ops()._archive_settings()

    def _set_archive_settings(self, *, enable: Optional[bool] = None, remote: Optional[str] = None) -> None:
        return self._ensure_settings_ops()._set_archive_settings(enable=enable, remote=remote)

    @staticmethod
    def _normalize_account_remote(value: str) -> str:
        from module.webops.settings_operations import SettingsOperations
        return SettingsOperations._normalize_account_remote(value)

    def _pikpak_accounts(self) -> list:
        return self._ensure_settings_ops()._pikpak_accounts()

    def _set_pikpak_accounts(self, accounts: list) -> None:
        return self._ensure_settings_ops()._set_pikpak_accounts(accounts)

    @staticmethod
    def _next_pikpak_remote_name(existing: set) -> str:
        from module.webops.settings_operations import SettingsOperations
        return SettingsOperations._next_pikpak_remote_name(existing)

    def _invalidate_pikpak_archive_client(self) -> None:
        return self._ensure_settings_ops()._invalidate_pikpak_archive_client()

    def _read_rclone_remotes(self) -> tuple:
        return self._ensure_settings_ops()._read_rclone_remotes()

    def list_pikpak_accounts(self) -> dict:
        return self._ensure_settings_ops().list_pikpak_accounts()

    def add_pikpak_account(self, payload: dict) -> dict:
        return self._ensure_settings_ops().add_pikpak_account(payload)

    def switch_pikpak_account(self, payload: dict) -> dict:
        return self._ensure_settings_ops().switch_pikpak_account(payload)

    def remove_pikpak_account(self, payload: dict) -> dict:
        return self._ensure_settings_ops().remove_pikpak_account(payload)

'''
text = text[:i2] + ACCOUNT_DELEGATE + text[j2:]

OPS.write_text(text, encoding="utf-8")
print("delegated; new line count:", len(text.splitlines()))
