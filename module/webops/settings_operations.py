# coding=UTF-8
"""WebUI 系统设置与 PikPak 多账号编排（ADR-0016）。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出的第五组：
用户/全局设置读写、归档开关与 remote 指针、PikPak 账号绑定/切换/删除。

依赖以 getter 显式注入，可脱离宿主单独测试。类内互相调用**直接走本类**，
不再绕回宿主（否则等于把耦合换个地方藏起来）。
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable, Optional

from module.core.config import UserConfig
from module.core.target_profiles import PIKPAK_MAX_ACCOUNTS
from module.utils.parser import PARSE_ARGS


class SettingsOperations:
    """系统设置 + PikPak 账号管理。"""

    def __init__(
        self,
        *,
        app_getter: Callable[[], object],
        gc_getter: Callable[[], object],
        download_upload_window_getter: Callable[[], object],
        local_storage_guard_getter: Callable[[], object],
        pikpak_manager_getter: Callable[[], object],
        setup_coordinator_getter: Callable[[], object],
    ) -> None:
        self._app = app_getter
        self._gc = gc_getter
        self._download_upload_window = download_upload_window_getter
        self._local_storage_guard = local_storage_guard_getter
        self._pikpak_manager = pikpak_manager_getter
        self._setup_coordinator = setup_coordinator_getter

    # ── 系统设置 ──

    def get_web_settings(self) -> dict:
        app = self._app()
        gc = self._gc()
        return {
            "user": {
                "config_path": app.config_path,
                "api_id": app.config.get("api_id"),
                "api_hash": app.config.get("api_hash"),
                "bot_token": app.config.get("bot_token"),
                "session_directory": app.config.get("session_directory"),
                "save_directory": app.config.get("save_directory"),
                "temp_directory": app.config.get("temp_directory"),
                "max_tasks": app.config.get("max_tasks"),
                "max_retries": app.config.get("max_retries"),
                "download_type": app.config.get("download_type"),
                "is_shutdown": app.config.get("is_shutdown"),
                "proxy": app.config.get("proxy"),
            },
            "global": gc.config,
        }

    def update_web_settings(self, payload: dict) -> dict:
        # 直接依赖"设置合并"所在的模块，而不是经 1,900 行的 HTTP 壳中转 ——
        # 这是把配置面从 server.py 拆出去的直接收益（webops 不再依赖 HTTP 层）。
        from module.adapters.webui.settings_support import merge_allowed_settings

        app = self._app()
        gc = self._gc()
        user_config = merge_allowed_settings(
            target=deepcopy(app.config),
            patch=payload.get("user", {}) if isinstance(payload, dict) else {},
            allowed={
                "api_id", "api_hash", "bot_token", "session_directory", "save_directory",
                "temp_directory", "max_tasks", "max_retries", "download_type", "is_shutdown",
                "proxy",
            },
        )
        global_config = merge_allowed_settings(
            target=deepcopy(gc.config),
            patch=payload.get("global", {}) if isinstance(payload, dict) else {},
            allowed={
                "notice", "export_table", "upload", "forward_type", "target_profiles",
                "message_filter", "live_watch", "transfer", "deep_link",
            },
        )
        user_config = UserConfig.normalize_runtime_numbers(user_config)
        app.save_config(user_config)
        app.config = user_config
        app.download_type = user_config.get("download_type")
        app.is_shutdown = user_config.get("is_shutdown")
        app.max_download_task = user_config["max_tasks"]["download"]
        app.max_upload_task = user_config["max_tasks"]["upload"]
        app.max_download_retries = user_config["max_retries"]["download"]
        app.max_upload_retries = user_config["max_retries"]["upload"]
        app.save_directory = user_config.get("save_directory")
        app.temp_directory = PARSE_ARGS.temp or (
            user_config.get("temp_directory") or app.TEMP_DIRECTORY
        )
        app.work_directory = PARSE_ARGS.session or (
            user_config.get("session_directory") or app.WORK_DIRECTORY
        )
        gc.save_config(global_config)
        self._download_upload_window().notify_limit_changed()
        guard = self._local_storage_guard()
        if guard:
            guard.notify_limit_changed()
        return self.get_web_settings()

    # ── 归档开关 / remote 指针 ──

    def _archive_settings(self) -> dict:
        profiles = (self._gc().config or {}).get("target_profiles") or {}
        pikpak = profiles.get("pikpak") if isinstance(profiles, dict) else {}
        archive = (pikpak or {}).get("archive") if isinstance(pikpak, dict) else {}
        return archive if isinstance(archive, dict) else {}

    def _set_archive_settings(
        self, *, enable: Optional[bool] = None, remote: Optional[str] = None
    ) -> None:
        gc = self._gc()
        config = deepcopy(gc.config)
        profiles = config.setdefault("target_profiles", {})
        if not isinstance(profiles, dict):
            profiles = {}
            config["target_profiles"] = profiles
        pikpak = profiles.setdefault("pikpak", {})
        if not isinstance(pikpak, dict):
            pikpak = {}
            profiles["pikpak"] = pikpak
        archive = pikpak.setdefault("archive", {})
        if not isinstance(archive, dict):
            archive = {}
            pikpak["archive"] = archive
        if enable is not None:
            archive["enable"] = bool(enable)
        if remote is not None:
            archive["remote"] = str(remote).strip().rstrip(":") or "pikpak"
        gc.save_config(config)
        gc.target_profiles = config.get("target_profiles", gc.target_profiles)

    # ── PikPak 多账号（ADR-0016）──

    @staticmethod
    def _normalize_account_remote(value: str) -> str:
        return str(value or "").strip().rstrip(":")

    def _pikpak_accounts(self) -> list:
        """已绑定的账号列表（每项 ``{'remote': str}``），去重且丢弃空值。"""
        profiles = (self._gc().config or {}).get("target_profiles") or {}
        pikpak = profiles.get("pikpak") if isinstance(profiles, dict) else {}
        accounts = (pikpak or {}).get("accounts") if isinstance(pikpak, dict) else None
        if not isinstance(accounts, list):
            return []
        normalized = []
        seen = set()
        for entry in accounts:
            if not isinstance(entry, dict):
                continue
            remote = self._normalize_account_remote(entry.get("remote"))
            if not remote or remote in seen:
                continue
            seen.add(remote)
            normalized.append({"remote": remote})
        return normalized

    def _set_pikpak_accounts(self, accounts: list) -> None:
        """持久化账号 remote 列表到 target_profiles.pikpak.accounts。"""
        gc = self._gc()
        config = deepcopy(gc.config)
        profiles = config.setdefault("target_profiles", {})
        if not isinstance(profiles, dict):
            profiles = {}
            config["target_profiles"] = profiles
        pikpak = profiles.setdefault("pikpak", {})
        if not isinstance(pikpak, dict):
            pikpak = {}
            profiles["pikpak"] = pikpak
        pikpak["accounts"] = [
            {"remote": self._normalize_account_remote(entry.get("remote"))}
            for entry in accounts
            if isinstance(entry, dict)
            and self._normalize_account_remote(entry.get("remote"))
        ]
        gc.save_config(config)
        gc.target_profiles = config.get("target_profiles", gc.target_profiles)

    @staticmethod
    def _next_pikpak_remote_name(existing: set) -> str:
        """自动命名新 remote：``pikpak``，然后 ``pikpak2`` … ``pikpak5``。"""
        if "pikpak" not in existing:
            return "pikpak"
        for n in range(2, PIKPAK_MAX_ACCOUNTS + 1):
            candidate = f"pikpak{n}"
            if candidate not in existing:
                return candidate
        raise ValueError(f"最多只能绑定 {PIKPAK_MAX_ACCOUNTS} 个 PikPak 账号。")

    def _invalidate_pikpak_archive_client(self) -> None:
        manager = self._pikpak_manager()
        invalidate = getattr(manager, "invalidate_archive_client", None)
        if callable(invalidate):
            invalidate()

    def _read_rclone_remotes(self) -> tuple:
        """返回 ``(remotes, error)``。调用方必须区分"没配 remote"与"rclone 不可用" ——
        把读取失败当成空列表会把每个账号都标成 missing，并可能在删除时孤立凭据。"""
        try:
            return self._setup_coordinator().list_remotes(), ""
        except Exception as e:  # noqa: BLE001 - 失败要带回原因给 UI
            return [], str(e)

    def list_pikpak_accounts(self) -> dict:
        """返回已绑定账号、当前激活 remote、以及 rclone 原始 remote 列表。"""
        accounts = self._pikpak_accounts()
        active = self._normalize_account_remote(self._archive_settings().get("remote"))
        remotes, rclone_error = self._read_rclone_remotes()
        remote_set = set(remotes)
        remotes_known = not rclone_error
        payload_accounts = []
        for entry in accounts:
            remote = entry["remote"]
            payload_accounts.append({
                "remote": remote,
                "active": remote == active,
                # 只有确实不在 rclone 配置里才算 missing；rclone 读不到时"不知道"，
                # 不能把账号误标为 missing。
                "missing": remotes_known and remote not in remote_set,
            })
        return {
            "accounts": payload_accounts,
            "active": active,
            "remotes": remotes,
            "limit": PIKPAK_MAX_ACCOUNTS,
            "rclone_error": rclone_error,
        }

    def add_pikpak_account(self, payload: dict) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        username = str(payload.get("username") or "").strip()
        password = str(payload.get("password") or "")
        accounts = self._pikpak_accounts()
        if len(accounts) >= PIKPAK_MAX_ACCOUNTS:
            raise ValueError(f"最多只能绑定 {PIKPAK_MAX_ACCOUNTS} 个 PikPak 账号。")

        existing_remotes, _ = self._read_rclone_remotes()
        remote = self._next_pikpak_remote_name(
            set(existing_remotes) | {a["remote"] for a in accounts}
        )

        probe = self._setup_coordinator().configure_pikpak_remote(
            remote=remote,
            username=username,
            password=password,
            overwrite=False,
        )
        if not probe.get("ok"):
            raise RuntimeError(probe.get("message") or f"remote「{remote}」探测失败。")

        accounts.append({"remote": remote})
        self._set_pikpak_accounts(accounts)
        # 只把激活指针指向新账号；**不**强制打开归档开关 —— 用户的选择必须保留。
        self._set_archive_settings(remote=remote)
        self._invalidate_pikpak_archive_client()
        return self.list_pikpak_accounts()

    def switch_pikpak_account(self, payload: dict) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        remote = self._normalize_account_remote(payload.get("remote"))
        accounts = self._pikpak_accounts()
        bound = {a["remote"] for a in accounts}
        if not remote:
            raise ValueError("请指定要切换到的 remote。")
        if remote not in bound:
            raise ValueError(f"remote「{remote}」未绑定。")
        remotes, rclone_error = self._read_rclone_remotes()
        if rclone_error:
            raise ValueError("无法读取 rclone 配置，请确认 rclone 已安装且配置可读。")
        if remote not in set(remotes):
            raise ValueError(f"remote「{remote}」已不在 rclone 配置中，请先重新配置。")
        # 只翻转激活指针，归档开关保持原样。
        self._set_archive_settings(remote=remote)
        self._invalidate_pikpak_archive_client()
        return self.list_pikpak_accounts()

    def remove_pikpak_account(self, payload: dict) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        remote = self._normalize_account_remote(payload.get("remote"))
        accounts = self._pikpak_accounts()
        bound = {a["remote"] for a in accounts}
        if not remote:
            raise ValueError("请指定要删除的 remote。")
        if remote not in bound:
            raise ValueError(f"remote「{remote}」未绑定。")
        active = self._normalize_account_remote(self._archive_settings().get("remote"))
        if remote == active:
            raise ValueError("不能删除当前激活的账号，请先切换到其他账号。")

        # 仅当 rclone 里确实还存在该 remote 时才删除它；"已缺失"的账号仍可解绑。
        # rclone 读不到时必须显式失败，而不是静默丢绑定、把凭据留在 rclone.conf。
        remotes, rclone_error = self._read_rclone_remotes()
        if rclone_error:
            raise ValueError("无法读取 rclone 配置，请确认 rclone 已安装且配置可读。")
        if remote in set(remotes):
            self._setup_coordinator().delete_remote(remote)

        self._set_pikpak_accounts([a for a in accounts if a["remote"] != remote])
        return self.list_pikpak_accounts()
