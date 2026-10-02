# coding=UTF-8
"""首启安装向导的**契约**部分（ADR-0012）。

本模块只保留 HTTP handler 需要的契约，编排器 ``SetupCoordinator`` 已搬到
``module.webops.setup_coordinator``（它零 HTTP 原语，属业务编排）：

- ``BotTokenInvalidError`` / ``BotTokenNetworkError``：`handlers/setup_api.py`
  用它把 getMe 的失败区分成"参数被拒"与"网络不可达"两种 HTTP 响应；
- ``verify_bot_token`` 及脱敏辅助：token 校验与错误消息脱敏，属对外的展示契约；
- ``apply_web_safe_user_defaults`` / ``has_telegram_api_credentials``：
  从 ``core.setup_defaults`` re-export，供 webops 侧沿用既有导入路径。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable, Optional, Tuple

from module.core.setup_defaults import (  # noqa: F401  (re-exported for back-compat)
    apply_web_safe_user_defaults,
    has_telegram_api_credentials,
)


class BotTokenInvalidError(ValueError):
    """Bot token rejected by Telegram getMe / format check."""

class BotTokenNetworkError(RuntimeError):
    """getMe could not be reached (timeout, DNS, proxy, etc.)."""

def has_configured_bot_token(config: Optional[dict]) -> bool:
    if not isinstance(config, dict):
        return False
    token = str(config.get("bot_token") or "").strip()
    if not token:
        return False
    from module.core.enums import Validator

    return Validator.is_valid_bot_token(token)

_BOT_NETWORK_HINT = (
    "无法连接 Telegram 校验 Bot Token（网络/代理问题）。可跳过本步，稍后在设置中配置。"
)

def verify_bot_token(
    bot_token: str,
    *,
    proxy: Optional[dict] = None,
    fetch: Optional[Callable[[str], Tuple[int, str]]] = None,
    timeout: float = 15.0,
) -> dict:
    """Validate bot token via Telegram getMe. Returns result payload (username, …)."""
    token = str(bot_token or "").strip()
    from module.core.enums import Validator

    if not Validator.is_valid_bot_token(token):
        raise BotTokenInvalidError(
            'bot_token 格式无效，须包含 ":"（BotFather 发放的完整 token）。'
        )

    url = f"https://api.telegram.org/bot{token}/getMe"
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
        payload = json.loads(body or "{}")
    except json.JSONDecodeError as e:
        raise BotTokenNetworkError(
            "Telegram 响应无法解析，请稍后重试或跳过本步。"
        ) from e

    if status == 401 or (
        isinstance(payload, dict) and payload.get("error_code") == 401
    ):
        raise BotTokenInvalidError(
            "Bot Token 无效（Telegram 返回 Unauthorized）。请检查后重试，或跳过本步。"
        )
    if status >= 500 or status == 429:
        raise BotTokenNetworkError("Telegram 服务暂时不可用，请稍后重试或跳过本步。")
    if not isinstance(payload, dict) or not payload.get("ok"):
        description = ""
        if isinstance(payload, dict):
            description = str(payload.get("description") or "")
        lowered = description.lower()
        if status == 404 or "not found" in lowered or "unauthorized" in lowered:
            raise BotTokenInvalidError("Bot Token 无效。请检查后重试，或跳过本步。")
        if 400 <= status < 500:
            # Other client errors: treat as invalid token rather than leaking upstream text.
            raise BotTokenInvalidError(
                f"Bot Token 校验失败（HTTP {status}）。请检查后重试，或跳过本步。"
            )
        raise BotTokenNetworkError("校验 Bot Token 失败，请稍后重试或跳过本步。")

    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    username = str(result.get("username") or "").strip()
    return {
        "id": result.get("id"),
        "username": username,
        "first_name": result.get("first_name"),
        "is_bot": bool(result.get("is_bot")),
    }

def _network_error_message(exc: BaseException, *, token: str = "") -> str:
    detail = _redact_secrets(str(exc), token=token)
    if detail:
        return f"{_BOT_NETWORK_HINT}原因: {detail}"
    return _BOT_NETWORK_HINT

def _redact_secrets(text: str, *, token: str = "") -> str:
    out = str(text or "")
    if token:
        out = out.replace(token, "***")
    # Bot API path shape even if token formatting differs slightly.
    if "api.telegram.org/bot" in out:
        parts = out.split("api.telegram.org/bot", 1)
        rest = parts[1]
        slash = rest.find("/")
        if slash >= 0:
            out = parts[0] + "api.telegram.org/bot***/" + rest[slash + 1 :]
        else:
            out = parts[0] + "api.telegram.org/bot***"
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
        handlers.append(
            urllib.request.ProxyHandler(
                {
                    "http": proxy_url,
                    "https": proxy_url,
                }
            )
        )
    opener = (
        urllib.request.build_opener(*handlers)
        if handlers
        else urllib.request.build_opener()
    )
    request = urllib.request.Request(url, method="GET")
    token_for_redact = ""
    marker = "api.telegram.org/bot"
    if marker in url:
        token_for_redact = url.split(marker, 1)[1].split("/", 1)[0]
    try:
        with opener.open(request, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return int(getattr(resp, "status", 200) or 200), body
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return int(e.code), body
    except Exception as e:
        raise BotTokenNetworkError(
            _network_error_message(e, token=token_for_redact)
        ) from e

def _http_proxy_url(proxy: Optional[dict]) -> Optional[str]:
    if not isinstance(proxy, dict) or not proxy.get("enable_proxy"):
        return None
    scheme = str(proxy.get("scheme") or "").strip().lower()
    hostname = str(proxy.get("hostname") or "").strip()
    port = proxy.get("port")
    if not hostname or port in (None, ""):
        return None
    if scheme not in ("http", "https"):
        # Socks not supported by stdlib urllib here; caller relies on network-error + skip.
        return None
    try:
        port_int = int(port)
    except (TypeError, ValueError):
        return None
    user = str(proxy.get("username") or "").strip()
    password = str(proxy.get("password") or "")
    auth = f"{user}:{password}@" if user else ""
    return f"{scheme}://{auth}{hostname}:{port_int}"

def _sanitize_rclone_error(message: str) -> str:
    text = str(message or "")
    # Avoid echoing credentials if rclone reprints argv oddly.
    lowered = text.lower()
    for token in ("pass=", "password=", "passwd="):
        if token in lowered:
            return "rclone 配置失败（详情已脱敏）。请检查账号密码后重试。"
    if len(text) > 400:
        return text[:400] + "…"
    return text
