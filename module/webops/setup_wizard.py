# coding=UTF-8
"""WebUI 首启安装向导编排（ADR-0012）。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出的第六组：
就绪状态、API 凭证保存、rclone 配置/跳过/探测、可选 Bot Token 保存/跳过。

依赖以 getter 显式注入，可脱离宿主单独测试。PikPak 账号相关的四个动作复用
``SettingsOperations``（经注入的回调），避免同一逻辑两处实现。
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable, Optional

from module.core.config import UserConfig
from module.core.target_profiles import PIKPAK_MAX_ACCOUNTS


class SetupWizardOperations:
    """首启向导的状态与四个步骤。"""

    def __init__(
        self,
        *,
        app_getter: Callable[[], object],
        loop_getter: Callable[[], object],
        setup_coordinator_getter: Callable[[], object],
        auth_provider_getter: Callable[[], object],
        api_credentials_event_getter: Callable[[], object],
        archive_settings_getter: Callable[[], dict],
        set_archive_settings: Callable[..., None],
        pikpak_accounts_getter: Callable[[], list],
        set_pikpak_accounts: Callable[[list], None],
        invalidate_pikpak_archive_client: Callable[[], None],
        setup_status_getter: Callable[[], dict],
    ) -> None:
        self._app = app_getter
        self._loop = loop_getter
        self._setup_coordinator = setup_coordinator_getter
        self._auth_provider = auth_provider_getter
        self._api_credentials_event = api_credentials_event_getter
        self._archive_settings = archive_settings_getter
        self._set_archive_settings = set_archive_settings
        self._pikpak_accounts = pikpak_accounts_getter
        self._set_pikpak_accounts = set_pikpak_accounts
        self._invalidate_pikpak_archive_client = invalidate_pikpak_archive_client
        # 经宿主解析：宿主可覆盖 get_setup_status（测试替身就是这么做的）。
        self._setup_status = setup_status_getter

    # ── 状态 ──

    def is_setup_ready(self) -> bool:
        return bool(self._setup_status().get("ready"))

    def get_setup_status(self) -> dict:
        from module.adapters.webui.setup import (
            has_configured_bot_token,
            has_telegram_api_credentials,
        )

        app = self._app()
        coordinator = self._setup_coordinator()
        api_done = has_telegram_api_credentials(app.config)
        telegram_step = "none"
        telegram_error = None
        telegram_done = False
        auth = self._auth_provider()
        if auth is not None:
            state = auth.get_state()
            telegram_step = state.get("step") or "pending"
            telegram_error = state.get("error")
            telegram_done = telegram_step == "done"
        client = getattr(app, "client", None)
        if (
            client is not None
            and getattr(client, "is_connected", False)
            and getattr(client, "me", None)
        ):
            telegram_done = True
            if telegram_step in ("none", "pending"):
                telegram_step = "done"
        archive = self._archive_settings()
        return coordinator.build_status(
            api_done=api_done,
            telegram_done=telegram_done,
            telegram_step=telegram_step,
            telegram_error=telegram_error,
            archive_enable=bool(archive.get("enable")),
            archive_remote=str(archive.get("remote") or "pikpak"),
            bot_token_configured=has_configured_bot_token(app.config),
        )

    # ── 步骤 1：API 凭证 ──

    def save_setup_api_credentials(self, payload: dict) -> dict:
        from module.adapters.webui.setup import apply_web_safe_user_defaults

        payload = payload if isinstance(payload, dict) else {}
        api_hash = str(payload.get("api_hash") or "").strip()
        try:
            api_id_int = int(payload.get("api_id"))
        except (TypeError, ValueError):
            raise ValueError("api_id 必须是数字。")
        if api_id_int <= 0:
            raise ValueError("api_id 无效。")
        if len(api_hash) < 16:
            raise ValueError("api_hash 无效。")

        app = self._app()
        user_config = deepcopy(app.config)
        user_config["api_id"] = api_id_int
        user_config["api_hash"] = api_hash
        proxy_patch = payload.get("proxy")
        if isinstance(proxy_patch, dict):
            proxy = user_config.get("proxy") if isinstance(user_config.get("proxy"), dict) else {}
            if proxy_patch.get("enable_proxy") is not None:
                proxy["enable_proxy"] = bool(proxy_patch.get("enable_proxy"))
            for key in ("scheme", "hostname", "port", "username", "password"):
                if key in proxy_patch:
                    proxy[key] = proxy_patch.get(key)
            user_config["proxy"] = proxy
        user_config = apply_web_safe_user_defaults(user_config)
        user_config = UserConfig.normalize_runtime_numbers(user_config)
        app.save_config(user_config)
        app.config = user_config
        app.refresh_runtime_fields()

        # 通知主循环重建/授权 client。
        event = self._api_credentials_event()
        if event is not None:
            loop = self._loop()
            if loop is not None and loop.is_running():
                loop.call_soon_threadsafe(event.set)
            else:
                event.set()
        coordinator = self._setup_coordinator()
        if coordinator is not None:
            coordinator.signal_api_ready()
        return self._setup_status()

    # ── 步骤 2：rclone（新装强制）──

    def configure_setup_rclone(self, payload: dict) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        coordinator = self._setup_coordinator()
        remote = str(payload.get("remote") or "pikpak").strip().rstrip(":") or "pikpak"
        # 账号上限必须在创建 remote / 写配置**之前**判定：被拒的请求不能留下
        # 孤儿凭据、不能翻转 archive.enable、不能把 active 指针指向未注册 remote。
        accounts = self._pikpak_accounts()
        if remote not in {a["remote"] for a in accounts} and len(accounts) >= PIKPAK_MAX_ACCOUNTS:
            raise ValueError(f"最多只能绑定 {PIKPAK_MAX_ACCOUNTS} 个 PikPak 账号。")
        probe = coordinator.configure_pikpak_remote(
            remote=remote,
            username=str(payload.get("username") or ""),
            password=str(payload.get("password") or ""),
            overwrite=bool(payload.get("overwrite", True)),
        )
        self._set_archive_settings(enable=True, remote=remote)
        # 注册/替换为已绑定账号，切换 UI 才能看到它。
        if remote not in {a["remote"] for a in accounts}:
            accounts.append({"remote": remote})
            self._set_pikpak_accounts(accounts)
        self._invalidate_pikpak_archive_client()
        coordinator.dismiss_rclone()
        status = self._setup_status()
        status["rclone_probe"] = probe
        return status

    def skip_setup_rclone(self, payload: Optional[dict] = None) -> dict:
        raise ValueError("初始化必须配置 rclone（下载回退会直接上传到 My Telegram）。")

    def test_setup_rclone(self, payload: Optional[dict] = None) -> dict:
        payload = payload if isinstance(payload, dict) else {}
        coordinator = self._setup_coordinator()
        archive = self._archive_settings()
        remote = (
            str(payload.get("remote") or archive.get("remote") or "pikpak").strip().rstrip(":")
            or "pikpak"
        )
        probe = coordinator.probe_rclone(remote)
        if probe.get("ok"):
            self._set_archive_settings(enable=True, remote=remote)
            coordinator.dismiss_rclone()
        return {"probe": probe, "status": self._setup_status()}

    # ── 步骤 3：可选 Bot Token ──

    def save_setup_bot_token(self, payload: dict) -> dict:
        from module.adapters.webui.setup import apply_web_safe_user_defaults, verify_bot_token

        payload = payload if isinstance(payload, dict) else {}
        token = str(payload.get("bot_token") or "").strip()
        app = self._app()
        proxy = app.config.get("proxy") if isinstance(app.config.get("proxy"), dict) else None
        verified = verify_bot_token(token, proxy=proxy)
        user_config = deepcopy(app.config)
        user_config["bot_token"] = token
        user_config = apply_web_safe_user_defaults(user_config)
        user_config = UserConfig.normalize_runtime_numbers(user_config)
        app.save_config(user_config)
        app.config = user_config
        app.refresh_runtime_fields()
        self._setup_coordinator().dismiss_bot()
        status = self._setup_status()
        status["bot_probe"] = verified
        return status

    def skip_setup_bot_token(self, payload: Optional[dict] = None) -> dict:
        self._setup_coordinator().dismiss_bot()
        return self._setup_status()
