# coding=UTF-8
"""首启安装向导的编排器（ADR-0012）。

从 ``adapters/webui/setup.py`` **逐字搬移**：``SetupCoordinator`` 零 HTTP 原语，
做的是"探测 rclone 可用性、调用 Telegram getMe、维护向导步骤状态机"，
属于业务编排，因此归属 webops。

留在 ``adapters/webui/setup.py`` 的是 HTTP handler 需要的**契约**：
``BotTokenInvalidError`` / ``BotTokenNetworkError`` 与 token 校验函数。
`_sanitize_rclone_error` 也留在那边（它属于"错误消息脱敏"这一展示契约），
本模块按需 import。

依赖方向 ``webops → adapters``（允许）；adapters 不得反向 import 本模块，
由 ``architecture_guard.test_no_layer_inversions`` 约束。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading
from typing import Callable, Optional

from module.adapters.webui.setup import _sanitize_rclone_error


class SetupCoordinator:
    """Track setup readiness for WebUI first-run flow.

    Upgrade path: if API + Telegram are already ready at first status check,
    never force the full-screen wizard. New installs must configure rclone
    (download→PikPak ingest now depends on rclone copyto My Telegram), then
    optionally configure Bot Token (skip allowed).
    """

    def __init__(
        self,
        runner: Optional[Callable] = None,
        rclone_bin: str = "rclone",
    ):
        self._lock = threading.Lock()
        self._guided = False
        self._rclone_dismissed = False
        self._bot_dismissed = False
        self._api_ready_event = threading.Event()
        self.runner = runner or subprocess.run
        self.rclone_bin = rclone_bin

    def mark_guided_if_incomplete(self, ready: bool) -> None:
        with self._lock:
            if not ready:
                self._guided = True

    def dismiss_rclone(self) -> None:
        """Kept for settings re-config probe success bookkeeping; no longer skips wizard."""
        with self._lock:
            self._rclone_dismissed = True

    def dismiss_bot(self) -> None:
        """Mark optional Bot Token step as handled without saving a token."""
        with self._lock:
            self._bot_dismissed = True

    def signal_api_ready(self) -> None:
        self._api_ready_event.set()

    def wait_api_ready(self, timeout: Optional[float] = None) -> bool:
        return self._api_ready_event.wait(timeout=timeout)

    def clear_api_ready(self) -> None:
        self._api_ready_event.clear()

    @property
    def guided(self) -> bool:
        with self._lock:
            return self._guided

    @property
    def rclone_dismissed(self) -> bool:
        with self._lock:
            return self._rclone_dismissed

    @property
    def bot_dismissed(self) -> bool:
        with self._lock:
            return self._bot_dismissed

    def build_status(
        self,
        *,
        api_done: bool,
        telegram_done: bool,
        telegram_step: str = "none",
        telegram_error: Optional[str] = None,
        archive_enable: bool = False,
        archive_remote: str = "pikpak",
        bot_token_configured: bool = False,
    ) -> dict:
        ready = bool(api_done and telegram_done)
        self.mark_guided_if_incomplete(ready)

        rclone_info = self.probe_rclone(archive_remote)
        rclone_ok = bool(rclone_info.get("ok"))
        with self._lock:
            guided = self._guided
            dismissed = self._rclone_dismissed
            bot_dismissed = self._bot_dismissed

        # New installs (guided): rclone probe must succeed — skip/dismiss no longer resolves.
        # Upgrades that never entered incomplete setup remain unforced.
        rclone_resolved = rclone_ok or (not guided)
        bot_resolved = bool(bot_token_configured) or bot_dismissed or (not guided)
        wizard_active = (
            (not ready)
            or (guided and not rclone_resolved)
            or (guided and rclone_resolved and not bot_resolved)
        )

        if not api_done:
            current = "api"
        elif not telegram_done:
            current = "telegram"
        elif guided and not rclone_resolved:
            current = "rclone"
        elif guided and not bot_resolved:
            current = "bot"
        else:
            current = "done"

        return {
            "ready": ready,
            "wizard_active": wizard_active,
            "current_step": current,
            "steps": {
                "api": {"done": api_done},
                "telegram": {
                    "done": telegram_done,
                    "step": telegram_step,
                    "error": telegram_error,
                },
                "rclone": {
                    "done": rclone_resolved,
                    "ok": rclone_ok,
                    "prompt": guided and not rclone_resolved,
                    "required": guided,
                    "dismissed": dismissed,
                    "remote": (archive_remote or "pikpak").strip().rstrip(":")
                    or "pikpak",
                    "archive_enable": bool(archive_enable),
                    "message": rclone_info.get("message") or "",
                    "remotes": rclone_info.get("remotes") or [],
                },
                "bot": {
                    "done": bot_resolved,
                    "prompt": guided and rclone_resolved and not bot_resolved,
                    "optional": True,
                    "dismissed": bot_dismissed,
                    "configured": bool(bot_token_configured),
                },
            },
        }

    def rclone_config_path(self) -> str:
        return os.environ.get("RCLONE_CONFIG") or os.path.join(
            os.getcwd(), "rclone", "rclone.conf"
        )

    def list_remotes(self) -> list[str]:
        if not shutil.which(self.rclone_bin) and self.rclone_bin == "rclone":
            raise RuntimeError(
                "未找到 rclone 可执行文件，请确认镜像/环境已安装 rclone。"
            )
        result = self._run_rclone(["listremotes"])
        text = (getattr(result, "stdout", "") or "").strip()
        remotes = []
        for line in text.splitlines():
            name = line.strip().rstrip(":")
            if name:
                remotes.append(name)
        return remotes

    def probe_rclone(self, remote: str = "pikpak") -> dict:
        remote = (remote or "pikpak").strip().rstrip(":") or "pikpak"
        try:
            remotes = self.list_remotes()
        except Exception as e:
            return {
                "ok": False,
                "remote": remote,
                "remotes": [],
                "message": str(e),
            }
        if remote not in remotes:
            return {
                "ok": False,
                "remote": remote,
                "remotes": remotes,
                "message": f"未找到 remote「{remote}」。",
            }
        try:
            self._run_rclone(["lsd", f"{remote}:"])
            return {
                "ok": True,
                "remote": remote,
                "remotes": remotes,
                "message": f"remote「{remote}」可用。",
            }
        except Exception as e:
            return {
                "ok": False,
                "remote": remote,
                "remotes": remotes,
                "message": _sanitize_rclone_error(str(e)),
            }

    def configure_pikpak_remote(
        self,
        *,
        remote: str,
        username: str,
        password: str,
        overwrite: bool = True,
    ) -> dict:
        remote = (remote or "pikpak").strip().rstrip(":") or "pikpak"
        username = (username or "").strip()
        password = password or ""
        if not username:
            raise ValueError("请输入 PikPak 用户名（邮箱或手机号）。")
        if not password:
            raise ValueError("请输入 PikPak 密码。")

        config_path = self.rclone_config_path()
        os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)

        remotes = []
        try:
            remotes = self.list_remotes()
        except Exception:
            remotes = []
        if remote in remotes:
            if not overwrite:
                raise ValueError(f"remote「{remote}」已存在，请确认覆盖或更换名称。")
            self._run_rclone(["config", "delete", remote])

        obscure = self._run_rclone(["obscure", password])
        obscured = (getattr(obscure, "stdout", "") or "").strip()
        if not obscured:
            raise RuntimeError("rclone obscure 失败，无法安全写入密码。")

        self._run_rclone(
            [
                "config",
                "create",
                remote,
                "pikpak",
                f"user={username}",
                f"pass={obscured}",
            ]
        )
        probe = self.probe_rclone(remote)
        if not probe.get("ok"):
            raise RuntimeError(probe.get("message") or f"remote「{remote}」探测失败。")
        return probe

    def delete_remote(self, remote: str) -> None:
        """Delete an rclone remote entry (used when removing a bound PikPak account)."""
        remote = (remote or "").strip().rstrip(":")
        if not remote:
            raise ValueError("remote 不能为空。")
        self._run_rclone(["config", "delete", remote])

    def _run_rclone(self, args: list[str]):
        config_path = self.rclone_config_path()
        command = [self.rclone_bin, *args, "--config", config_path]
        result = self.runner(command, capture_output=True, text=True, timeout=120)
        if getattr(result, "returncode", 0) != 0:
            stderr = getattr(result, "stderr", "") or ""
            stdout = getattr(result, "stdout", "") or ""
            raise RuntimeError(
                _sanitize_rclone_error(
                    stderr.strip() or stdout.strip() or f"Command failed: {args}"
                )
            )
        return result

