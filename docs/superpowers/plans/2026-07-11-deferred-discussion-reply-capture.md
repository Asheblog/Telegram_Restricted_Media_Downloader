# Deferred Discussion Reply Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 监听转发开启「包含评论区」时，主贴立刻转发，评论区延迟 N 分钟（默认可配置）后再抓取一次；任务持久化、可取消/立即执行，并在 WebUI 列表中可见。

**Architecture:** 在 SQLite 新增 `deferred_discussion_captures` 表；`CommentDelayScheduler` 负责入队、到期执行、重启恢复；`listen_forward` 在 `include_comment` 时改为调度而非立刻抓；全局配置 `live_watch.comment_delay_minutes`；WebUI 提供设置项与按 watch 的待抓列表 API。

**Tech Stack:** Python 3.13、SQLite（TransferStore）、asyncio、现有 WebUI（desktop.js / mobile_script.js → build_frontend → assets.py）

**Test seams (confirmed by design grilling):**
1. `TransferStore` deferred capture CRUD
2. `CommentDelayScheduler` schedule / due / cancel / run_now / cancel_by_watch
3. `GlobalConfig` `comment_delay_minutes` 解析（含默认 20、`0` 立刻）
4. `listen_forward` 分支：有 delay → schedule；delay=0 → 立刻 `forward_discussion_replies`

---

### Task 1: Domain docs

**Files:**
- Modify: `CONTEXT.md`
- Create: `docs/adr/0007-defer-discussion-reply-capture.md`

- [x] Add glossary term **Deferred Discussion Reply Capture**
- [x] Add ADR recording single delayed fetch + absolute due_at + listen-forward-only scope

---

### Task 2: TransferStore table + CRUD (TDD)

**Files:**
- Modify: `module/persistence/transfer_store.py`
- Test: `unit_tests/deferred_discussion_capture_store_case.py`

Schema:

```sql
CREATE TABLE IF NOT EXISTS deferred_discussion_captures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id TEXT NOT NULL,
    source_chat_id TEXT NOT NULL,
    source_message_id INTEGER NOT NULL,
    target_chat_id TEXT NOT NULL,
    target_link TEXT NOT NULL,
    due_at REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending|running|done|cancelled
    error_message TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE(watch_id, source_chat_id, source_message_id)
);
```

API:
- `schedule_deferred_discussion_capture(...)` → upsert pending if not already pending/running
- `list_deferred_discussion_captures(watch_id=None, statuses=None)`
- `get_deferred_discussion_capture(id)`
- `claim_due_deferred_discussion_captures(now)` → pending where due_at <= now → running
- `mark_deferred_discussion_capture(id, status, error_message=None)`
- `cancel_deferred_discussion_captures_for_watch(watch_id)` → pending → cancelled
- `cancel_deferred_discussion_capture(id)` → pending → cancelled

- [ ] Write failing store tests
- [ ] Implement schema + methods
- [ ] Tests pass

---

### Task 3: Config `live_watch.comment_delay_minutes`

**Files:**
- Modify: `module/core/config.py` (`GlobalConfig.TEMPLATE`)
- Modify: `module/web_operations.py` (`update_web_settings` allowed keys)
- Modify: `module/adapters/webui/server.py` (`settings_schema` min/max)
- Test: `unit_tests/comment_delay_config_case.py`

- Default nesting:

```python
'live_watch': {
    'comment_delay_minutes': 20,
}
```

- Getter clamps to `>= 0` int; missing key → 20
- Allow `live_watch` in WebUI global settings merge
- Schema: `{'min': 0, 'max': 1440}`

- [ ] Failing test for default / zero / clamp
- [ ] Implement
- [ ] Pass

---

### Task 4: CommentDelayScheduler

**Files:**
- Create: `module/transfer/comment_delay.py`
- Shim optional if needed
- Test: `unit_tests/comment_delay_scheduler_case.py`

Responsibilities:
- `schedule(...)` reads delay minutes; if 0 call executor immediately (or return None and let caller call immediately); else insert row with `due_at = now + minutes*60`
- Background loop every ~5s: `claim_due` → call async executor `forward_discussion_replies` → mark done/cancelled on failure
- `restore_on_startup()` arms loop
- `cancel(job_id)`, `run_now(job_id)` (set due_at=now or claim immediately), `cancel_for_watch(watch_id)`
- Changing config does **not** rewrite existing `due_at`

- [ ] Failing scheduler unit tests with fake store + fake clock/executor
- [ ] Implement
- [ ] Pass

---

### Task 5: Wire listen_forward + delete_watch

**Files:**
- Modify: `module/downloader.py` (`listen_forward`, `forward_discussion_replies` call sites)
- Modify: `module/transfer/live_watch.py` (`delete_watch`)
- Modify: composition/startup to start scheduler restore

Behavior:
- After main post forward succeeds path, if `include_comment`:
  - delay==0 → existing `forward_discussion_replies`
  - else → `scheduler.schedule(...)` and add live_watch_event “已调度延迟抓评论区”
- On watch delete → `cancel_for_watch`
- On execute → add live_watch_event with result count

- [ ] Integration-style unit test or focused mock test for branch
- [ ] Implement wiring
- [ ] Pass

---

### Task 6: WebUI API + list + settings

**Files:**
- Modify: `module/adapters/webui/server.py` routes
- Modify: `module/ports.py` / web operations if needed
- Modify: `module/adapters/webui/templates/views.html` (settings field)
- Modify: `module/adapters/webui/static/desktop.js`
- Modify: `module/adapters/webui/static/mobile_script.js` (+ mobile settings if present)
- Modify: i18n JSON if present
- Run: `python -m module.adapters.webui.build_frontend`

API:
- `GET /api/watches/{id}/deferred-comments`
- `POST /api/watches/{id}/deferred-comments/{job_id}/cancel`
- `POST /api/watches/{id}/deferred-comments/{job_id}/run-now`

UI:
- Settings「行为」：`global.live_watch.comment_delay_minutes`
- Forward watch row：按钮「待抓评论区」展开列表（主贴 ID、due_at、status、取消、立即执行）

- [ ] Implement backend routes
- [ ] Implement desktop + mobile UI
- [ ] Rebuild assets
- [ ] Smoke / unit coverage for list/cancel API if covered by existing webui test patterns

---

### Task 7: Verification

- [ ] Run targeted unit tests
- [ ] Confirm no doc/config gaps vs grilling summary

---

## Spec coverage checklist

| Requirement | Task |
|-------------|------|
| 主贴立刻、评论区延迟 | 5 |
| 仅监听转发 + include_comment | 5 |
| 默认 20 / 可配置 / 0=立刻 | 3 |
| SQLite 持久化 + 重启恢复 | 2, 4 |
| 到期只抓一次 | 4 |
| 删 watch 取消 pending | 5 |
| 改分钟数不影响已排队 | 4 |
| WebUI 列表 + 取消 + 立即执行 | 6 |
| 设置页分钟数 | 3, 6 |
