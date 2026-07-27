# coding=UTF-8
"""First-run Setup Wizard coordinator (ADR-0012)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from typing import Callable, Optional, Tuple


class BotTokenInvalidError(ValueError):
    """Bot token rejected by Telegram getMe / format check."""


class BotTokenNetworkError(RuntimeError):
    """getMe could not be reached (timeout, DNS, proxy, etc.)."""


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
            rclone_bin: str = 'rclone',
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
            telegram_step: str = 'none',
            telegram_error: Optional[str] = None,
            archive_enable: bool = False,
            archive_remote: str = 'pikpak',
            bot_token_configured: bool = False,
    ) -> dict:
        ready = bool(api_done and telegram_done)
        self.mark_guided_if_incomplete(ready)

        rclone_info = self.probe_rclone(archive_remote)
        rclone_ok = bool(rclone_info.get('ok'))
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
            current = 'api'
        elif not telegram_done:
            current = 'telegram'
        elif guided and not rclone_resolved:
            current = 'rclone'
        elif guided and not bot_resolved:
            current = 'bot'
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
                    'required': guided,
                    'dismissed': dismissed,
                    'remote': (archive_remote or 'pikpak').strip().rstrip(':') or 'pikpak',
                    'archive_enable': bool(archive_enable),
                    'message': rclone_info.get('message') or '',
                    'remotes': rclone_info.get('remotes') or [],
                },
                'bot': {
                    'done': bot_resolved,
                    'prompt': guided and rclone_resolved and not bot_resolved,
                    'optional': True,
                    'dismissed': bot_dismissed,
                    'configured': bool(bot_token_configured),
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


def has_configured_bot_token(config: Optional[dict]) -> bool:
    if not isinstance(config, dict):
        return False
    token = str(config.get('bot_token') or '').strip()
    if not token:
        return False
    from module.core.enums import Validator
    return Validator.is_valid_bot_token(token)


_BOT_NETWORK_HINT = (
    '无法连接 Telegram 校验 Bot Token（网络/代理问题）。可跳过本步，稍后在设置中配置。'
)


def verify_bot_token(
        bot_token: str,
        *,
        proxy: Optional[dict] = None,
        fetch: Optional[Callable[[str], Tuple[int, str]]] = None,
        timeout: float = 15.0,
) -> dict:
    """Validate bot token via Telegram getMe. Returns result payload (username, …)."""
    token = str(bot_token or '').strip()
    from module.core.enums import Validator
    if not Validator.is_valid_bot_token(token):
        raise BotTokenInvalidError('bot_token 格式无效，须包含 ":"（BotFather 发放的完整 token）。')

    url = f'https://api.telegram.org/bot{token}/getMe'
    fetcher = fetch or (lambda u: _default_getme_fetch(u, proxy=proxy, timeout=timeout))
    try:
        status, body = fetcher(url)
    except BotTokenInvalidError:
        raise
    except BotTokenNetworkError:
        raise
    except Exception as e:
        raise BotTokenNetworkError(_network_error_message(e, token=token)) from e

    try:
        payload = json.loads(body or '{}')
    except json.JSONDecodeError as e:
        raise BotTokenNetworkError('Telegram 响应无法解析，请稍后重试或跳过本步。') from e

    if status == 401 or (isinstance(payload, dict) and payload.get('error_code') == 401):
        raise BotTokenInvalidError('Bot Token 无效（Telegram 返回 Unauthorized）。请检查后重试，或跳过本步。')
    if status >= 500 or status == 429:
        raise BotTokenNetworkError('Telegram 服务暂时不可用，请稍后重试或跳过本步。')
    if not isinstance(payload, dict) or not payload.get('ok'):
        description = ''
        if isinstance(payload, dict):
            description = str(payload.get('description') or '')
        lowered = description.lower()
        if status == 404 or 'not found' in lowered or 'unauthorized' in lowered:
            raise BotTokenInvalidError(
                'Bot Token 无效。请检查后重试，或跳过本步。'
            )
        if 400 <= status < 500:
            # Other client errors: treat as invalid token rather than leaking upstream text.
            raise BotTokenInvalidError(
                f'Bot Token 校验失败（HTTP {status}）。请检查后重试，或跳过本步。'
            )
        raise BotTokenNetworkError('校验 Bot Token 失败，请稍后重试或跳过本步。')

    result = payload.get('result') if isinstance(payload.get('result'), dict) else {}
    username = str(result.get('username') or '').strip()
    return {
        'id': result.get('id'),
        'username': username,
        'first_name': result.get('first_name'),
        'is_bot': bool(result.get('is_bot')),
    }


def _network_error_message(exc: BaseException, *, token: str = '') -> str:
    detail = _redact_secrets(str(exc), token=token)
    if detail:
        return f'{_BOT_NETWORK_HINT}原因: {detail}'
    return _BOT_NETWORK_HINT


def _redact_secrets(text: str, *, token: str = '') -> str:
    out = str(text or '')
    if token:
        out = out.replace(token, '***')
    # Bot API path shape even if token formatting differs slightly.
    if 'api.telegram.org/bot' in out:
        parts = out.split('api.telegram.org/bot', 1)
        rest = parts[1]
        slash = rest.find('/')
        if slash >= 0:
            out = parts[0] + 'api.telegram.org/bot***/' + rest[slash + 1:]
        else:
            out = parts[0] + 'api.telegram.org/bot***'
    return out


def _default_getme_fetch(
        url: str,
        *,
        proxy: Optional[dict] = None,
        timeout: float = 15.0,
) -> Tuple[int, str]:
    handlers = []
    proxy_url = _http_proxy_url(proxy)
    if proxy_url:
        handlers.append(urllib.request.ProxyHandler({
            'http': proxy_url,
            'https': proxy_url,
        }))
    opener = urllib.request.build_opener(*handlers) if handlers else urllib.request.build_opener()
    request = urllib.request.Request(url, method='GET')
    token_for_redact = ''
    marker = 'api.telegram.org/bot'
    if marker in url:
        token_for_redact = url.split(marker, 1)[1].split('/', 1)[0]
    try:
        with opener.open(request, timeout=timeout) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            return int(getattr(resp, 'status', 200) or 200), body
    except urllib.error.HTTPError as e:
        body = ''
        try:
            body = e.read().decode('utf-8', errors='replace')
        except Exception:
            body = ''
        return int(e.code), body
    except Exception as e:
        raise BotTokenNetworkError(_network_error_message(e, token=token_for_redact)) from e


def _http_proxy_url(proxy: Optional[dict]) -> Optional[str]:
    if not isinstance(proxy, dict) or not proxy.get('enable_proxy'):
        return None
    scheme = str(proxy.get('scheme') or '').strip().lower()
    hostname = str(proxy.get('hostname') or '').strip()
    port = proxy.get('port')
    if not hostname or port in (None, ''):
        return None
    if scheme not in ('http', 'https'):
        # Socks not supported by stdlib urllib here; caller relies on network-error + skip.
        return None
    try:
        port_int = int(port)
    except (TypeError, ValueError):
        return None
    user = str(proxy.get('username') or '').strip()
    password = str(proxy.get('password') or '')
    auth = f'{user}:{password}@' if user else ''
    return f'{scheme}://{auth}{hostname}:{port_int}'


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
