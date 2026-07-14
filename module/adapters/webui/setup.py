# coding=UTF-8
"""First-run Setup Wizard coordinator (ADR-0012)."""
from __future__ import annotations

import os
import shutil
import subprocess
import threading
from typing import Callable, Optional


class SetupCoordinator:
    """Track setup readiness for WebUI first-run flow.

    Upgrade path: if API + Telegram are already ready at first status check,
    never force the full-screen wizard (including optional rclone).
    """

    def __init__(
            self,
            runner: Optional[Callable] = None,
            rclone_bin: str = 'rclone',
    ):
        self._lock = threading.Lock()
        self._guided = False
        self._rclone_dismissed = False
        self._api_ready_event = threading.Event()
        self.runner = runner or subprocess.run
        self.rclone_bin = rclone_bin

    def mark_guided_if_incomplete(self, ready: bool) -> None:
        with self._lock:
            if not ready:
                self._guided = True

    def dismiss_rclone(self) -> None:
        with self._lock:
            self._rclone_dismissed = True

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

    def build_status(
            self,
            *,
            api_done: bool,
            telegram_done: bool,
            telegram_step: str = 'none',
            telegram_error: Optional[str] = None,
            archive_enable: bool = False,
            archive_remote: str = 'pikpak',
    ) -> dict:
        ready = bool(api_done and telegram_done)
        self.mark_guided_if_incomplete(ready)

        rclone_info = self.probe_rclone(archive_remote)
        rclone_ok = bool(rclone_info.get('ok'))
        with self._lock:
            guided = self._guided
            dismissed = self._rclone_dismissed

        # Upgrade: never entered incomplete state → do not force rclone step.
        rclone_resolved = rclone_ok or dismissed or (not guided)
        wizard_active = (not ready) or (guided and not rclone_resolved)

        if not api_done:
            current = 'api'
        elif not telegram_done:
            current = 'telegram'
        elif guided and not rclone_resolved:
            current = 'rclone'
        else:
            current = 'done'

        return {
            'ready': ready,
            'wizard_active': wizard_active,
            'current_step': current,
            'steps': {
                'api': {'done': api_done},
                'telegram': {
                    'done': telegram_done,
                    'step': telegram_step,
                    'error': telegram_error,
                },
                'rclone': {
                    'done': rclone_resolved,
                    'ok': rclone_ok,
                    'prompt': guided and not rclone_resolved,
                    'dismissed': dismissed,
                    'remote': (archive_remote or 'pikpak').strip().rstrip(':') or 'pikpak',
                    'archive_enable': bool(archive_enable),
                    'message': rclone_info.get('message') or '',
                    'remotes': rclone_info.get('remotes') or [],
                },
            },
        }

    def rclone_config_path(self) -> str:
        return (
            os.environ.get('RCLONE_CONFIG')
            or os.path.join(os.getcwd(), 'rclone', 'rclone.conf')
        )

    def list_remotes(self) -> list[str]:
        if not shutil.which(self.rclone_bin) and self.rclone_bin == 'rclone':
            raise RuntimeError('未找到 rclone 可执行文件，请确认镜像/环境已安装 rclone。')
        result = self._run_rclone(['listremotes'])
        text = (getattr(result, 'stdout', '') or '').strip()
        remotes = []
        for line in text.splitlines():
            name = line.strip().rstrip(':')
            if name:
                remotes.append(name)
        return remotes

    def probe_rclone(self, remote: str = 'pikpak') -> dict:
        remote = (remote or 'pikpak').strip().rstrip(':') or 'pikpak'
        try:
            remotes = self.list_remotes()
        except Exception as e:
            return {
                'ok': False,
                'remote': remote,
                'remotes': [],
                'message': str(e),
            }
        if remote not in remotes:
            return {
                'ok': False,
                'remote': remote,
                'remotes': remotes,
                'message': f'未找到 remote「{remote}」。',
            }
        try:
            self._run_rclone(['lsd', f'{remote}:'])
            return {
                'ok': True,
                'remote': remote,
                'remotes': remotes,
                'message': f'remote「{remote}」可用。',
            }
        except Exception as e:
            return {
                'ok': False,
                'remote': remote,
                'remotes': remotes,
                'message': _sanitize_rclone_error(str(e)),
            }

    def configure_pikpak_remote(
            self,
            *,
            remote: str,
            username: str,
            password: str,
            overwrite: bool = True,
    ) -> dict:
        remote = (remote or 'pikpak').strip().rstrip(':') or 'pikpak'
        username = (username or '').strip()
        password = password or ''
        if not username:
            raise ValueError('请输入 PikPak 用户名（邮箱或手机号）。')
        if not password:
            raise ValueError('请输入 PikPak 密码。')

        config_path = self.rclone_config_path()
        os.makedirs(os.path.dirname(config_path) or '.', exist_ok=True)

        remotes = []
        try:
            remotes = self.list_remotes()
        except Exception:
            remotes = []
        if remote in remotes:
            if not overwrite:
                raise ValueError(f'remote「{remote}」已存在，请确认覆盖或更换名称。')
            self._run_rclone(['config', 'delete', remote])

        obscure = self._run_rclone(['obscure', password])
        obscured = (getattr(obscure, 'stdout', '') or '').strip()
        if not obscured:
            raise RuntimeError('rclone obscure 失败，无法安全写入密码。')

        self._run_rclone([
            'config', 'create', remote, 'pikpak',
            f'user={username}',
            f'pass={obscured}',
        ])
        probe = self.probe_rclone(remote)
        if not probe.get('ok'):
            raise RuntimeError(probe.get('message') or f'remote「{remote}」探测失败。')
        return probe

    def _run_rclone(self, args: list[str]):
        config_path = self.rclone_config_path()
        command = [self.rclone_bin, *args, '--config', config_path]
        result = self.runner(command, capture_output=True, text=True, timeout=120)
        if getattr(result, 'returncode', 0) != 0:
            stderr = getattr(result, 'stderr', '') or ''
            stdout = getattr(result, 'stdout', '') or ''
            raise RuntimeError(_sanitize_rclone_error(stderr.strip() or stdout.strip() or f'Command failed: {args}'))
        return result


def has_telegram_api_credentials(config: Optional[dict]) -> bool:
    if not isinstance(config, dict):
        return False
    api_id = config.get('api_id')
    api_hash = config.get('api_hash')
    if api_id in (None, '', 0, '0') or api_hash in (None, ''):
        return False
    try:
        int(api_id)
    except (TypeError, ValueError):
        return False
    return len(str(api_hash).strip()) >= 16


def apply_web_safe_user_defaults(config: dict) -> dict:
    """Fill non-interactive defaults for --web first run. Never prompts stdin."""
    if not isinstance(config, dict):
        return config
    dirs = _default_directories()
    if not config.get('save_directory'):
        config['save_directory'] = dirs['save_directory']
    if not config.get('session_directory'):
        config['session_directory'] = dirs['session_directory']
    if not config.get('temp_directory'):
        config['temp_directory'] = dirs['temp_directory']
    if not config.get('download_type'):
        config['download_type'] = [
            'video', 'photo', 'document', 'audio', 'voice', 'animation', 'video_note'
        ]
    if config.get('is_shutdown') is None:
        config['is_shutdown'] = False
    proxy = config.get('proxy')
    if not isinstance(proxy, dict):
        proxy = {}
        config['proxy'] = proxy
    if proxy.get('enable_proxy') is None:
        proxy['enable_proxy'] = False
    max_tasks = config.get('max_tasks')
    if not isinstance(max_tasks, dict):
        max_tasks = {}
        config['max_tasks'] = max_tasks
    max_tasks.setdefault('download', 1)
    max_tasks.setdefault('upload', 1)
    max_retries = config.get('max_retries')
    if not isinstance(max_retries, dict):
        max_retries = {}
        config['max_retries'] = max_retries
    if max_retries.get('download') is None:
        max_retries['download'] = 5
    if max_retries.get('upload') is None:
        max_retries['upload'] = 3
    return config


def _default_directories() -> dict:
    if os.path.isdir('/app'):
        return {
            'save_directory': '/app/downloads',
            'session_directory': '/app/sessions',
            'temp_directory': '/app/temp',
        }
    cwd = os.getcwd()
    return {
        'save_directory': os.path.join(cwd, 'downloads'),
        'session_directory': os.path.join(cwd, 'sessions'),
        'temp_directory': os.path.join(cwd, 'temp'),
    }


def _sanitize_rclone_error(message: str) -> str:
    text = str(message or '')
    # Avoid echoing credentials if rclone reprints argv oddly.
    lowered = text.lower()
    for token in ('pass=', 'password=', 'passwd='):
        if token in lowered:
            return 'rclone 配置失败（详情已脱敏）。请检查账号密码后重试。'
    if len(text) > 400:
        return text[:400] + '…'
    return text
