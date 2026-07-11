# Deep Link Resolve（深链取片）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在转存任务与监听转发中可选启用「深链取片」：从频道帖解析白名单 bot 的 `t.me/<bot>?start=`，用用户会话 `messages.startBot` 取回 `video`/`document`/`animation`，再走现有转发→下载上传链路到 PikPak。

**Architecture:** 纯函数负责从消息提取深链；`DeepLinkResolver` 串行调用 StartBot 并轮询 bot 私聊等待媒体；任务/监听用 `resolve_deep_link` 开关；全局 `deep_link.bot_whitelist` + `timeout_seconds`。接入点在 `transfer_message_to_web_target` 与 `listen_forward`：有白名单深链则替换为 bot 回传消息再转发，失败不回退频道预览。

**Tech Stack:** Python 3.13、Pyrogram（`raw.functions.messages.StartBot`）、SQLite（TransferStore 列迁移）、现有 WebUI（views.html / desktop.js / mobile → `build_frontend` → assets.py）

**Agreed behavior (grilling):**
1. 任务勾选 + 白名单非空才启用；勾选但白名单空 → 创建失败提示去设置填写
2. 链接优先级：按钮 URL → 正文/caption；评论区仅在 `include_comment` 时扫描
3. 白名单内深链存在 → 以 bot 回传为准；取片失败不回退频道媒体
4. 仅非白名单深链或无深链 → 走原频道媒体逻辑
5. 成功媒体：`video` / `document` / `animation`；仅 photo/文字失败
6. 串行取片、默认超时 60s、不过验证/加频道、bot 私聊不删
7. 归档来源仍算原频道帖；事件日志记 `resolved_via=@bot start=param`
8. 监听转发与转存任务同一套规则

**Test seams:**
1. `extract_deep_link_candidates` / whitelist match（纯函数）
2. `GlobalConfig` deep_link getters
3. `TransferStore` / watch rule `resolve_deep_link` 持久化
4. create_task / create_watch 白名单空校验
5. `DeepLinkResolver.resolve`（mock client）成功/超时/非媒体
6. `transfer_message_to_web_target` / `listen_forward` 分支（mock resolver）

---

## File map

| File | Responsibility |
|------|----------------|
| `module/transfer/deep_link.py` | 提取深链、白名单规范化、`DeepLinkResolver`、错误类型 |
| `module/core/config.py` | `deep_link` 默认配置与 getter |
| `module/persistence/transfer_store.py` | `resolve_deep_link` 列（tasks + watches） |
| `module/utils/util.py` | watch rule `--resolve-deep-link` 标志 |
| `module/transfer/runner.py` | 转存前可选 resolve |
| `module/downloader.py` | `listen_forward` 可选 resolve |
| `module/transfer/live_watch.py` + applicator | 创建/编辑 watch 传旗标 |
| `module/adapters/webui/server.py` | API 校验 + settings schema |
| `module/web_operations.py` | settings allowed keys |
| `module/adapters/webui/view_model.py` | 序列化新字段 |
| WebUI templates/JS | 设置区 + 任务/监听勾选 |
| `CONTEXT.md` + `docs/adr/0008-*.md` | 领域术语与 ADR |

---

### Task 1: Domain docs

**Files:**
- Modify: `CONTEXT.md`
- Create: `docs/adr/0008-deep-link-resolve.md`

- [ ] **Step 1: Add glossary term**

在 `CONTEXT.md` 领域术语表加入：

```markdown
**Deep Link Resolve** — 可选的转存前置步骤：当来源消息含白名单资源 bot 的 `t.me/<bot>?start=<param>`（或等价 `tg://`）时，用用户会话调用 `messages.startBot` 取回 bot 私聊中的 video/document/animation，再对取回消息执行既有转发/下载上传；业务来源仍记为原频道帖。由任务/监听上的 `resolve_deep_link` 开关控制；全局 `deep_link.bot_whitelist` 限定可解析 bot。
_Avoid_: Bot scrape, start param hack, auto click teaser
```

- [ ] **Step 2: Write ADR 0008**

记录决策：用户会话而非 Bot API；白名单 + 任务级开关；深链优先于频道预览；失败不回退；串行；60s 默认超时；归档归属原频道。

- [ ] **Step 3: Commit**

```bash
git add CONTEXT.md docs/adr/0008-deep-link-resolve.md
git commit -m "$(cat <<'EOF'
docs: add Deep Link Resolve glossary and ADR

EOF
)"
```

---

### Task 2: Pure extract + whitelist helpers (TDD)

**Files:**
- Create: `module/transfer/deep_link.py`
- Test: `unit_tests/deep_link_extract_case.py`

- [ ] **Step 1: Write failing tests**

```python
# coding=UTF-8
import unittest
from types import SimpleNamespace

from module.transfer.deep_link import (
    extract_deep_link_candidates,
    normalize_bot_username,
    pick_whitelisted_deep_link,
    parse_deep_link_url,
)


class DeepLinkExtractCase(unittest.TestCase):
    def test_normalize_strips_at_and_lower(self):
        self.assertEqual('a82bot', normalize_bot_username('@A82Bot'))

    def test_parse_tme_and_tg_urls(self):
        self.assertEqual(
            ('a82bot', 'v_db7c66a8e8'),
            parse_deep_link_url('https://t.me/a82bot?start=v_db7c66a8e8'),
        )
        self.assertEqual(
            ('a82bot', 'v_abc'),
            parse_deep_link_url('tg://resolve?domain=a82bot&start=v_abc'),
        )
        self.assertIsNone(parse_deep_link_url('https://t.me/a82bot'))

    def test_button_before_text(self):
        msg = SimpleNamespace(
            reply_markup=SimpleNamespace(inline_keyboard=[[
                SimpleNamespace(url='https://t.me/otherbot?start=skip'),
                SimpleNamespace(url='https://t.me/a82bot?start=from_btn'),
            ]]),
            text='see https://t.me/a82bot?start=from_text',
            caption=None,
            entities=None,
            caption_entities=None,
        )
        cands = extract_deep_link_candidates(msg)
        self.assertEqual('from_btn', cands[0][1])
        picked = pick_whitelisted_deep_link(cands, ['a82bot'])
        self.assertEqual(('a82bot', 'from_btn'), picked)

    def test_non_whitelist_returns_none(self):
        cands = [('otherbot', 'x')]
        self.assertIsNone(pick_whitelisted_deep_link(cands, ['a82bot']))


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run to verify fail**

```bash
python -m unit_tests.deep_link_extract_case
```

Expected: FAIL import / missing symbols

- [ ] **Step 3: Implement minimal helpers in `module/transfer/deep_link.py`**

```python
# coding=UTF-8
from __future__ import annotations

import re
from typing import Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

DeepLink = Tuple[str, str]  # (bot_username_lower, start_param)

_TME_START_RE = re.compile(
    r'(?:https?://)?(?:t\.me|telegram\.me)/([A-Za-z0-9_]+)\?start=([A-Za-z0-9_-]+)',
    re.I,
)


def normalize_bot_username(value: str) -> str:
    return str(value or '').strip().lstrip('@').lower()


def parse_deep_link_url(url: str) -> Optional[DeepLink]:
    raw = str(url or '').strip()
    if not raw:
        return None
    if raw.lower().startswith('tg://'):
        parsed = urlparse(raw)
        qs = parse_qs(parsed.query)
        domain = (qs.get('domain') or [None])[0]
        start = (qs.get('start') or [None])[0]
        if domain and start:
            return normalize_bot_username(domain), str(start)
        return None
    m = _TME_START_RE.search(raw)
    if not m:
        return None
    return normalize_bot_username(m.group(1)), m.group(2)


def _iter_button_urls(message) -> List[str]:
    urls = []
    markup = getattr(message, 'reply_markup', None)
    keyboard = getattr(markup, 'inline_keyboard', None) or []
    for row in keyboard:
        for btn in row or []:
            url = getattr(btn, 'url', None)
            if url:
                urls.append(str(url))
    return urls


def _iter_text_urls(message) -> List[str]:
    urls = []
    for text_attr, ent_attr in (('text', 'entities'), ('caption', 'caption_entities')):
        text = getattr(message, text_attr, None) or ''
        entities = getattr(message, ent_attr, None) or []
        for ent in entities:
            url = getattr(ent, 'url', None)
            if url:
                urls.append(str(url))
            elif getattr(ent, 'type', None) and 'url' in str(getattr(ent, 'type', '')).lower():
                offset = int(getattr(ent, 'offset', 0) or 0)
                length = int(getattr(ent, 'length', 0) or 0)
                urls.append(text[offset:offset + length])
        for m in _TME_START_RE.finditer(str(text)):
            urls.append(m.group(0))
    return urls


def extract_deep_link_candidates(message) -> List[DeepLink]:
    ordered: List[DeepLink] = []
    seen = set()
    for url in _iter_button_urls(message) + _iter_text_urls(message):
        parsed = parse_deep_link_url(url)
        if not parsed or parsed in seen:
            continue
        seen.add(parsed)
        ordered.append(parsed)
    return ordered


def pick_whitelisted_deep_link(
        candidates: Iterable[DeepLink],
        whitelist: Iterable[str],
) -> Optional[DeepLink]:
    allowed = {normalize_bot_username(x) for x in (whitelist or []) if normalize_bot_username(x)}
    if not allowed:
        return None
    for bot, param in candidates:
        if bot in allowed:
            return bot, param
    return None
```

- [ ] **Step 4: Tests pass**

```bash
python -m unit_tests.deep_link_extract_case
```

- [ ] **Step 5: Commit**

```bash
git add module/transfer/deep_link.py unit_tests/deep_link_extract_case.py
git commit -m "$(cat <<'EOF'
feat: add deep link extract and whitelist helpers

EOF
)"
```

---

### Task 3: GlobalConfig `deep_link`

**Files:**
- Modify: `module/core/config.py`
- Modify: `module/web_operations.py` (`update_web_settings` allowed)
- Modify: `module/adapters/webui/server.py` (`settings_schema` + `save_runtime_settings` allowed)
- Test: `unit_tests/deep_link_config_case.py`

- [ ] **Step 1: Failing config tests**

```python
# coding=UTF-8
import sys
import unittest
from copy import deepcopy

from unit_tests.pyrogram_stub import install_pyrogram_stub
install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
from module.core.config import GlobalConfig
sys.argv = _ORIGINAL_ARGV


class DeepLinkConfigCase(unittest.TestCase):
    def test_template_defaults(self):
        self.assertEqual([], GlobalConfig.TEMPLATE['deep_link']['bot_whitelist'])
        self.assertEqual(60, GlobalConfig.TEMPLATE['deep_link']['timeout_seconds'])

    def test_getters(self):
        gc = GlobalConfig.__new__(GlobalConfig)
        gc.default_deep_link_nesting = deepcopy(GlobalConfig.TEMPLATE['deep_link'])
        gc.config = {'deep_link': {'bot_whitelist': ['@A82Bot', ''], 'timeout_seconds': 60}}
        self.assertEqual(['a82bot'], gc.get_deep_link_bot_whitelist())
        gc.config = {'deep_link': {'timeout_seconds': 0}}
        self.assertEqual(1, gc.get_deep_link_timeout_seconds())  # clamp min 1
        gc.config = {'deep_link': {'timeout_seconds': 9999}}
        self.assertEqual(600, gc.get_deep_link_timeout_seconds())  # clamp max 600
        gc.config = {}
        self.assertEqual([], gc.get_deep_link_bot_whitelist())
        self.assertEqual(60, gc.get_deep_link_timeout_seconds())


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Implement**

在 `GlobalConfig.TEMPLATE` 增加：

```python
'deep_link': {
    'bot_whitelist': [],
    'timeout_seconds': 60,
},
```

实现：

```python
def get_deep_link_bot_whitelist(self) -> list:
    raw = self.get_nesting_config(
        nesting='deep_link',
        nesting_param='bot_whitelist',
        default_config=getattr(self, 'default_deep_link_nesting', self.TEMPLATE['deep_link']),
    )
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.replace('\n', ',').split(',')]
        raw = parts
    if not isinstance(raw, list):
        return []
    from module.transfer.deep_link import normalize_bot_username
    out = []
    seen = set()
    for item in raw:
        name = normalize_bot_username(item)
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out

def get_deep_link_timeout_seconds(self) -> int:
    raw = self.get_nesting_config(
        nesting='deep_link',
        nesting_param='timeout_seconds',
        default_config=getattr(self, 'default_deep_link_nesting', self.TEMPLATE['deep_link']),
    )
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = 60
    return max(1, min(600, value))
```

在 `__init__` / `save_config` 路径同步缓存属性（对齐 `comment_delay_minutes`）。

`settings_schema` 增加：

```python
'deep_link': {
    'timeout_seconds': {'min': 1, 'max': 600},
},
```

`save_runtime_settings` / `update_web_settings` 的 `allowed` 集合加入 `'deep_link'`。

合并白名单字符串→列表：在 `merge_allowed_settings` 之后或 `_coerce_type` 中，若 key 为 `bot_whitelist` 且值为 str，按逗号/换行切分为 list。

- [ ] **Step 3: Pass tests + commit**

```bash
python -m unit_tests.deep_link_config_case
git add module/core/config.py module/web_operations.py module/adapters/webui/server.py unit_tests/deep_link_config_case.py
git commit -m "$(cat <<'EOF'
feat: add deep_link global config whitelist and timeout

EOF
)"
```

---

### Task 4: Persist `resolve_deep_link` on tasks + watches (TDD)

**Files:**
- Modify: `module/persistence/transfer_store.py`
- Modify: `module/utils/util.py`（watch rule 标志）
- Modify: `module/adapters/webui/view_model.py`
- Test: `unit_tests/deep_link_store_case.py`

- [ ] **Step 1: Failing store + rule tests**

```python
# coding=UTF-8
import tempfile
import unittest
from pathlib import Path

from module.persistence.transfer_store import TransferStore
from module.utils.util import make_forward_watch_rule, parse_forward_watch_rule


class DeepLinkStoreCase(unittest.TestCase):
    def test_create_task_persists_flag(self):
        db = Path(tempfile.mkdtemp()) / 't.sqlite'
        store = TransferStore(str(db))
        tid = store.create_task(
            source_link='https://t.me/swag_vip',
            target_link='https://t.me/pikpak_bot',
            target_profile='pikpak',
            start_id=1,
            end_id=2,
            include_comment=False,
            resolve_deep_link=True,
        )
        task = store.get_task(tid)
        self.assertTrue(task['resolve_deep_link'])

    def test_watch_rule_flag(self):
        rule = make_forward_watch_rule('https://t.me/a', 'https://t.me/b', False, True)
        parsed = parse_forward_watch_rule(rule)
        self.assertTrue(parsed['resolve_deep_link'])
        self.assertFalse(parsed['include_comment'])


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Schema + API**

`transfer_tasks` / `live_transfer_watches` 经 `_ensure_columns` 增加：

```python
'resolve_deep_link': 'INTEGER NOT NULL DEFAULT 0',
```

`create_task(..., resolve_deep_link: bool = False)` 写入并在 `get_task`/`list_tasks` 布尔化（对齐 `include_comment`）。

`upsert_live_transfer_watch(..., resolve_deep_link: bool = False)` 同理。

`util.py`：

```python
RESOLVE_DEEP_LINK_FLAGS = {'--resolve-deep-link', '--resolve_deep_link'}

def split_resolve_deep_link_flag(args: list) -> Tuple[list, bool]:
    ...

def make_forward_watch_rule(source_link, target_link, include_comment=False, resolve_deep_link=False) -> str:
    rule = f'{source_link} {target_link}'
    if include_comment:
        rule += ' --include-comment'
    if resolve_deep_link:
        rule += ' --resolve-deep-link'
    return rule

def parse_forward_watch_rule(rule: str) -> dict:
    args, include_comment = split_include_comment_flag(str(rule).split())
    args, resolve_deep_link = split_resolve_deep_link_flag(args)
    return {
        'source_link': safe_index(args, 0, ''),
        'target_link': safe_index(args, 1, ''),
        'include_comment': include_comment,
        'resolve_deep_link': resolve_deep_link,
    }
```

`view_model.task_model` / watch model 增加 `'resolve_deep_link': bool(...)`。

- [ ] **Step 3: Pass + commit**

```bash
python -m unit_tests.deep_link_store_case
git add module/persistence/transfer_store.py module/utils/util.py module/adapters/webui/view_model.py unit_tests/deep_link_store_case.py
git commit -m "$(cat <<'EOF'
feat: persist resolve_deep_link on tasks and watches

EOF
)"
```

---

### Task 5: API validation + LiveWatch wiring

**Files:**
- Modify: `module/adapters/webui/server.py` (`create_task`, `create_watch`, edit watch payload)
- Modify: `module/transfer/live_watch.py`
- Modify: `module/live_watch_applicator.py`
- Modify: `module/web_operations.py`（若有 watch payload 透传）
- Test: `unit_tests/deep_link_api_validation_case.py`

- [ ] **Step 1: Failing validation test**

用假 store / 假 settings：当 `resolve_deep_link=True` 且 `get_deep_link_bot_whitelist()` 为空时，`create_task` 抛 `WebUiApiError`，code=`deep_link_whitelist_required`，中文消息含「系统设置」与「白名单」。

- [ ] **Step 2: Implement**

在 `WebUiServer.__init__` 增加可选 `deep_link_whitelist_getter: Callable[[], list] | None = None`（composition_root 注入 `lambda: self.gc.get_deep_link_bot_whitelist()`）。

共享校验：

```python
def _require_deep_link_whitelist_if_enabled(self, resolve_deep_link: bool) -> None:
    if not resolve_deep_link:
        return
    getter = getattr(self, 'deep_link_whitelist_getter', None)
    whitelist = list(getter() or []) if callable(getter) else []
    if not whitelist:
        raise WebUiApiError(
            'deep_link_whitelist_required',
            '已开启深链取片，请先在系统设置填写资源 bot 白名单。',
            HTTPStatus.BAD_REQUEST,
        )
```

`create_task`：

```python
resolve_deep_link = bool(payload.get('resolve_deep_link'))
self._require_deep_link_whitelist_if_enabled(resolve_deep_link)
task_id = self.store.create_task(..., include_comment=include_comment, resolve_deep_link=resolve_deep_link)
```

`create_watch` / `update_watch`：同样读取 `resolve_deep_link`、调用校验，并传入 `LiveWatchManager`。

`LiveWatchManager.create_watch` / `persist_watch`：

```python
resolve_deep_link = bool(payload.get('resolve_deep_link'))
rule = make_forward_watch_rule(source_link, target_link, include_comment, resolve_deep_link)
# upsert_live_transfer_watch(..., resolve_deep_link=resolve_deep_link)
# 返回/payload 含 resolve_deep_link
```

`live_watch_applicator.apply_watch`：

```python
resolve_deep_link = bool(payload.get('resolve_deep_link'))
rule = make_forward_watch_rule(source_link, target_link, include_comment, resolve_deep_link)
```

- [ ] **Step 3: Pass + commit**

```bash
python -m unit_tests.deep_link_api_validation_case
git add module/adapters/webui/server.py module/transfer/live_watch.py module/live_watch_applicator.py module/web_operations.py unit_tests/deep_link_api_validation_case.py
git commit -m "$(cat <<'EOF'
feat: validate deep link whitelist on task and watch create

EOF
)"
```

---

### Task 6: `DeepLinkResolver` (TDD with mocks)

**Files:**
- Modify: `module/transfer/deep_link.py`
- Test: `unit_tests/deep_link_resolver_case.py`

- [ ] **Step 1: Failing resolver tests**

覆盖：
1. 成功：StartBot 后 history 出现带 `video` 的消息 → 返回该 message
2. 超时：仅文字 → `DeepLinkResolveError`
3. 串行：第二个 resolve 在第一个 lock 释放前不调用 StartBot（可用异步 stub）

- [ ] **Step 2: Implement**

```python
class DeepLinkResolveError(Exception):
    pass


class DeepLinkResolver:
    def __init__(self, timeout_seconds: int = 60, poll_interval: float = 1.5):
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval
        self._lock = asyncio.Lock()

    @staticmethod
    def message_has_resolvable_media(message) -> bool:
        return any(getattr(message, attr, None) for attr in ('video', 'document', 'animation'))

    async def start_bot(self, client, bot_username: str, start_param: str):
        from pyrogram import raw
        peer = await client.resolve_peer(bot_username)
        await client.invoke(
            raw.functions.messages.StartBot(
                bot=peer,
                peer=peer,
                random_id=client.rnd_id(),
                start_param=start_param,
            )
        )

    async def wait_for_media(self, client, bot_username: str, started_at: float):
        deadline = started_at + self.timeout_seconds
        while time.time() < deadline:
            async for message in client.get_chat_history(bot_username, limit=10):
                msg_date = getattr(message, 'date', None)
                ts = msg_date.timestamp() if hasattr(msg_date, 'timestamp') else float(msg_date or 0)
                if ts + 2 < started_at:  # allow small skew
                    continue
                if getattr(message, 'outgoing', False):
                    continue
                if self.message_has_resolvable_media(message):
                    return message
            await asyncio.sleep(self.poll_interval)
        raise DeepLinkResolveError('资源 bot 未在超时内返回媒体')

    async def resolve(self, client, message, whitelist, timeout_seconds=None) -> Optional[object]:
        """若命中白名单深链则返回 bot 媒体消息；无深链返回 None；失败抛 DeepLinkResolveError。"""
        picked = pick_whitelisted_deep_link(extract_deep_link_candidates(message), whitelist)
        if not picked:
            return None
        bot, param = picked
        async with self._lock:
            started_at = time.time()
            if timeout_seconds is not None:
                self.timeout_seconds = int(timeout_seconds)
            await self.start_bot(client, bot, param)
            media_msg = await self.wait_for_media(client, bot, started_at)
            # 调用方可从 media_msg 读取；解析元数据由调用方写 event
            media_msg._deep_link_meta = {'bot': bot, 'start_param': param}
            return media_msg
```

注意：Pyrogram 版本若无 `rnd_id`，用 `client.rnd_id()` 的既有用法或 `secrets.randbits(63)` 对齐仓库其它 invoke。

- [ ] **Step 3: Pass + commit**

```bash
python -m unit_tests.deep_link_resolver_case
git add module/transfer/deep_link.py unit_tests/deep_link_resolver_case.py
git commit -m "$(cat <<'EOF'
feat: add serial DeepLinkResolver with StartBot wait

EOF
)"
```

---

### Task 7: Wire into transfer runner + listen_forward

**Files:**
- Modify: `module/transfer/runner.py` (`transfer_message_to_web_target`)
- Modify: `module/downloader.py` (`listen_forward`；host 持有 resolver）
- Modify: `module/composition_root.py`（如需注入）
- Test: `unit_tests/deep_link_transfer_wire_case.py`

- [ ] **Step 1: Failing wire tests**

1. `resolve_deep_link=False` → 不调用 resolver，直接用原 message
2. `resolve_deep_link=True` 且 resolver 返回媒体 → `forward` 收到的是 resolved message；`add_event` 含 `resolved_via=`
3. resolver 抛 `DeepLinkResolveError` → `fail_transfer_item`（或不调用 channel fallback download）

- [ ] **Step 2: Implement hook**

在 `transfer_message_to_web_target` 空消息检查之后、`forward` 之前：

```python
from module.transfer.deep_link import DeepLinkResolveError

resolved_meta = None
if bool(task.get('resolve_deep_link')):
    resolver = host.get_deep_link_resolver()
    try:
        resolved = await resolver.resolve(
            client=host.app.client,
            message=message,
            whitelist=host.gc.get_deep_link_bot_whitelist(),
            timeout_seconds=host.gc.get_deep_link_timeout_seconds(),
        )
    except DeepLinkResolveError as e:
        task_id = int(task.get('id'))
        item_id = host.transfer_store.add_item(
            task_id=task_id,
            source_chat_id=origin_chat_id,
            source_message_id=message_id,
            range_message_id=range_message_id,
            source_link=source_link,
            target_link=task.get('target_link'),
            media_type='deep_link',
            phase='failed',
            status=TransferStatus.FAILURE,
            error_message=str(e),
        )
        host.transfer_store.add_event(task_id, f'Deep link resolve failed: {e}', level='error', item_id=item_id)
        host._refresh_counts(task_id) if hasattr(host, '_refresh_counts') else host.transfer_store.refresh_task_counts(task_id)
        return False
    if resolved is not None:
        resolved_meta = getattr(resolved, '_deep_link_meta', {}) or {}
        message = resolved

# 随后既有 forward(...)；add_item 仍用频道 origin_chat_id / message_id / source_folder
# forward 成功后若 resolved_meta：
#   store.add_event(..., f'resolved_via=@{bot} start={param} source={source_link}', item_id=item_id)
```

`listen_forward`：`resolve_deep_link = bool(rule.get('resolve_deep_link'))`；为 True 时在 `forward(...)` 前调用同一 resolver；`DeepLinkResolveError` 时 `_log_system_chain(..., stage='deep_link_failed')` 并 `continue`（不转频道预览）。

Host：

```python
def get_deep_link_resolver(self):
    if getattr(self, '_deep_link_resolver', None) is None:
        from module.transfer.deep_link import DeepLinkResolver
        self._deep_link_resolver = DeepLinkResolver()
    return self._deep_link_resolver
```

**重要：** `add_item` 的 `source_chat_id` / `source_message_id` / `source_folder` 继续用频道入参，不要改成 bot 私聊 id。

- [ ] **Step 3: Pass + commit**

```bash
python -m unit_tests.deep_link_transfer_wire_case
git add module/transfer/runner.py module/downloader.py module/composition_root.py unit_tests/deep_link_transfer_wire_case.py
git commit -m "$(cat <<'EOF'
feat: resolve whitelisted deep links before transfer and listen-forward

EOF
)"
```

---

### Task 8: WebUI — settings + checkboxes

**Files:**
- Modify: `module/adapters/webui/templates/views.html`
- Modify: `module/adapters/webui/static/desktop.js`（及 mobile 对应表单提交）
- Modify: `module/adapters/webui/static/shared.js`（i18n）
- Modify: `module/adapters/webui/templates/mobile_body.html`（若有独立设置/表单）
- Run: `python -m module.adapters.webui.build_frontend`

- [ ] **Step 1: Settings block「深链取片」**

放在系统设置、靠近 `live_watch` 评论延迟处：

```html
<section>
  <h4 data-i18n="settings.deepLinkTitle">深链取片</h4>
  <label>
    <span data-i18n="settings.deepLinkWhitelist">资源 bot 白名单</span>
    <textarea class="form-input" name="global.deep_link.bot_whitelist" rows="3"
      placeholder="每行一个，例如：&#10;a82bot"></textarea>
  </label>
  <p class="text-xs text-muted" data-i18n="settings.deepLinkWhitelistHint">
    每行一个 bot 用户名（可带 @）。仅名单内的 t.me/&lt;bot&gt;?start= 会触发取片。留空且任务未勾选时功能关闭。
  </p>
  <label>
    <span data-i18n="settings.deepLinkTimeout">取片超时（秒）</span>
    <input class="form-input" name="global.deep_link.timeout_seconds" type="number" min="1" max="600">
  </label>
</section>
```

回填：若 `bot_whitelist` 为 list，`join('\n')` 进 textarea。

- [ ] **Step 2: Task / watch checkboxes**

在「新建转存」「监听转发」「编辑监听」以及同链路含 `include_comment` 的表单旁增加：

```html
<label class="flex items-center gap-2">
  <input type="checkbox" name="resolve_deep_link" class="w-4 h-4">
  <span data-i18n="new.resolveDeepLink">深链取片</span>
</label>
<p class="text-xs text-muted" data-i18n="new.resolveDeepLinkHint">
  勾选后，对白名单 bot 的 ?start= 链接取片再转存；需先在系统设置填写白名单。
</p>
```

JS payload：`resolve_deep_link: Boolean(fd.get('resolve_deep_link'))`。

编辑监听回填 `watch.resolve_deep_link`。

- [ ] **Step 3: Build frontend**

```bash
python -m module.adapters.webui.build_frontend
```

- [ ] **Step 4: Commit**

```bash
git add module/adapters/webui/
git commit -m "$(cat <<'EOF'
feat(webui): deep link resolve settings and task checkboxes

EOF
)"
```

---

### Task 9: Regression + docs map

**Files:**
- Modify: `CONTEXT-MAP.md`（配置项表加 `deep_link.*`）
- Run existing related tests

- [ ] **Step 1: Run focused suites**

```bash
python -m unit_tests.deep_link_extract_case
python -m unit_tests.deep_link_config_case
python -m unit_tests.deep_link_store_case
python -m unit_tests.deep_link_api_validation_case
python -m unit_tests.deep_link_resolver_case
python -m unit_tests.deep_link_transfer_wire_case
python -m unit_tests.comment_delay_config_case
```

- [ ] **Step 2: Update CONTEXT-MAP 配置项表**

| `deep_link.bot_whitelist` | GlobalConfig | 资源 bot 白名单 |
| `deep_link.timeout_seconds` | GlobalConfig | 取片超时秒数 |

- [ ] **Step 3: Final commit if map changed**

```bash
git add CONTEXT-MAP.md
git commit -m "$(cat <<'EOF'
docs: map deep_link config keys

EOF
)"
```

---

## Spec coverage checklist

| Requirement | Task |
|-------------|------|
| 白名单配置 + 说明文案 | 3, 8 |
| 任务/监听勾选 | 4, 5, 8 |
| 勾选但白名单空 → 创建失败 | 5 |
| 按钮优先于正文 | 2 |
| StartBot + 等待媒体 | 6 |
| video/document/animation | 6 |
| 串行 | 6 |
| 超时 60 可配 | 3, 6 |
| 不过验证 | 6（不实现 join） |
| 失败不回退频道媒体 | 7 |
| 转发→下载上传复用 | 7（替换 message 后走原路径） |
| 来源归档仍算频道 | 7 |
| 监听转发同规则 | 7 |
| bot 私聊不删 | （不实现删除） |
| 领域文档 | 1 |

## Out of scope

- Bot CLI `/listen_forward` 文案中的深链旗标（若 Bot 路径也创建 watch，Task 5 应透传；纯 CLI 开关可后续加）
- 自动加入关联频道 / 点击验证按钮
- 并行取片
- 取片后删除 bot 私聊媒体
