# 实时监听操作整合 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将「活跃监听」收成「记录 N + ⋯」、取消行内展开，并用统一 `WatchDetail` 壳展示转发记录 / 下载记录 / 待抓评论区（桌面 modal、移动 sheet）。

**Architecture:** 新增无浏览器依赖的 `watch_ui_helpers.js`（短链路、事件短标题、状态筛选），由 `build_frontend.py` 在 `shared.js` 前注入；桌面/移动共用这些函数。桌面把 history/download overlay 收敛为 `#watch-detail-overlay`；移动继续用 `#mob-sheet`，内容结构对齐。删除 `watch-events-row` / `mob-watch-events` 展开路径。改完后跑 `build_frontend.py` 重生 `assets.py`。

**Tech Stack:** 现有 WebUI（`watch_ui_helpers.js` / `shared.js` / `desktop.js` / `mobile_script.js` / `views.html` / `tailwind.css`）、`build_frontend.py`、Node 测纯函数、`unittest` 测内嵌 HTML 契约。

**Spec:** `docs/superpowers/specs/2026-07-12-watches-action-consolidation-design.md`

**无新增领域边界:** 不改后端 API / `CONTEXT.md` / ADR（默认）。

---

## File map

| 文件 | 职责 |
|------|------|
| `module/adapters/webui/static/watch_ui_helpers.js` | 纯展示函数（可 Node 单测；挂到 `globalThis.WatchUiHelpers`） |
| `module/adapters/webui/build_frontend.py` | 在 desktop/mobile HTML 中于 `shared.js` 前注入 helpers |
| `module/adapters/webui/static/shared.js` | i18n 新文案；可选薄封装调用 `WatchUiHelpers` |
| `module/adapters/webui/static/desktop.js` | 紧凑 `renderWatches`、`⋯` 菜单、`WatchDetail`、删除展开逻辑 |
| `module/adapters/webui/static/mobile_script.js` | 同构卡片、`⋯` Action Sheet、Sheet 详情壳、删除行内展开 |
| `module/adapters/webui/templates/views.html` | 表头两列；合并为 `#watch-detail-overlay` |
| `module/adapters/webui/static/tailwind.css` | 紧凑行、菜单、状态优先列表、触控尺寸 |
| `module/adapters/webui/assets.py` | 生成物（勿手改） |
| `unit_tests/watch_ui_helpers.test.mjs` | Node：纯函数单测 |
| `unit_tests/web_ui_assets_case.py` | 断言新 DOM 契约 |

---

### Task 1: `watch_ui_helpers.js` + Node 测试 + build 注入（TDD）

**Files:**
- Create: `module/adapters/webui/static/watch_ui_helpers.js`
- Create: `unit_tests/watch_ui_helpers.test.mjs`
- Modify: `module/adapters/webui/build_frontend.py`
- Modify: `module/adapters/webui/static/shared.js`（仅 i18n 键）

- [ ] **Step 1: 写失败的 Node 测试**

```js
// unit_tests/watch_ui_helpers.test.mjs
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const { WatchUiHelpers: h } = require(
  path.join(__dirname, '../module/adapters/webui/static/watch_ui_helpers.js')
);

assert.equal(h.shortTelegramLink('https://t.me/pikpak_bot'), 'pikpak_bot');
assert.equal(h.shortTelegramLink('https://t.me/c/4209310295'), 'c/4209310295');
assert.equal(h.shortTelegramLink(''), '-');

assert.equal(
  h.formatWatchRoute('https://t.me/c/4209310295', 'https://t.me/pikpak_bot'),
  'c/4209310295 → pikpak_bot'
);

assert.deepEqual(
  h.summarizeWatchEvent({ status: 'success', message: '转发成功。' }),
  { kind: 'success', titleKey: 'watches.eventForwarded', detail: '' }
);
assert.equal(
  h.summarizeWatchEvent({
    status: 'skipped',
    message: '跳过转发(已被消息过滤器过滤：命中过滤关键词：[广告])',
  }).titleKey,
  'watches.eventFilterKeyword'
);
assert.equal(
  h.summarizeWatchEvent({ status: 'failure', message: '转发失败：timeout' }).kind,
  'failure'
);

const events = [
  { status: 'success', message: 'ok' },
  { status: 'skipped', message: 'filtered' },
  { status: 'failure', message: 'err' },
];
assert.equal(h.filterWatchEventsByStatus(events, 'all').length, 3);
assert.equal(h.filterWatchEventsByStatus(events, 'success').length, 1);
assert.equal(h.filterWatchEventsByStatus(events, 'filtered').length, 1);
assert.equal(h.filterWatchEventsByStatus(events, 'failure').length, 1);

console.log('watch_ui_helpers.test.mjs: ok');
```

- [ ] **Step 2: 跑测试确认失败**

```bash
node unit_tests/watch_ui_helpers.test.mjs
```

Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 `watch_ui_helpers.js`（无 DOM / 无 localStorage）**

```js
// module/adapters/webui/static/watch_ui_helpers.js
(function (root) {
  function shortTelegramLink(link) {
    if (!link) return '-';
    return String(link)
      .replace(/^https?:\/\/(t\.me|telegram\.me)\//i, '')
      .replace(/\/+$/, '') || '-';
  }

  function formatWatchRoute(sourceLink, targetLink) {
    return shortTelegramLink(sourceLink) + ' → ' + shortTelegramLink(targetLink || '本地');
  }

  function summarizeWatchEvent(evt) {
    const status = evt && evt.status;
    const message = (evt && evt.message) || '';
    if (status === 'success') {
      return { kind: 'success', titleKey: 'watches.eventForwarded', detail: '' };
    }
    if (status === 'skipped' || /过滤|filter/i.test(message)) {
      var titleKey = 'watches.eventSkipped';
      if (/关键词|keyword/i.test(message)) titleKey = 'watches.eventFilterKeyword';
      return { kind: 'filtered', titleKey: titleKey, detail: message };
    }
    return { kind: 'failure', titleKey: 'watches.eventFailed', detail: message };
  }

  function filterWatchEventsByStatus(events, filter) {
    var list = events || [];
    if (!filter || filter === 'all') return list.slice();
    return list.filter(function (evt) {
      var kind = summarizeWatchEvent(evt).kind;
      if (filter === 'filtered') return kind === 'filtered';
      return kind === filter;
    });
  }

  var WatchUiHelpers = {
    shortTelegramLink: shortTelegramLink,
    formatWatchRoute: formatWatchRoute,
    summarizeWatchEvent: summarizeWatchEvent,
    filterWatchEventsByStatus: filterWatchEventsByStatus,
  };

  root.WatchUiHelpers = WatchUiHelpers;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WatchUiHelpers: WatchUiHelpers };
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);
```

在 `shared.js` 的 zh/en 词典增加：

```js
'watches.task': '任务',
'watches.eventFilterKeyword': '命中过滤关键词',
'watches.eventFailed': '转发失败',
'watches.moreActions': '更多操作',
'watches.filterAll': '全部',
'watches.filterSuccess': '成功',
'watches.filterFiltered': '已过滤',
'watches.filterFailure': '失败',
'watches.detailExpandReason': '点击展开原因',
```

英文对应：`Task` / `Filter keyword hit` / `Forward failed` / `More actions` / `All` / `Success` / `Filtered` / `Failure` / `Tap to expand reason`。

- [ ] **Step 4: 改 `build_frontend.py` 注入 helpers**

在 `build_desktop_html` / `build_mobile_html` 读取 helpers，并替换时放在 shared 之前，例如：

```python
helpers_js = read_text(STATIC_DIR / "watch_ui_helpers.js")
# desktop:
html = html.replace("/* shared.js */", helpers_js + "\n" + shared_js)
# mobile: 同样先 helpers 再 shared
```

（若占位符是整段 `/* shared.js */`，保持一次 replace，前缀拼接即可。）

- [ ] **Step 5: 再跑 Node 测试**

```bash
node unit_tests/watch_ui_helpers.test.mjs
```

Expected: `watch_ui_helpers.test.mjs: ok`

- [ ] **Step 6: Commit**

```bash
git add module/adapters/webui/static/watch_ui_helpers.js module/adapters/webui/build_frontend.py module/adapters/webui/static/shared.js unit_tests/watch_ui_helpers.test.mjs
git commit -m "$(cat <<'EOF'
feat(webui): add watch UI presenter helpers

EOF
)"
```

---

### Task 2: 桌面表头 + 统一详情壳 DOM

**Files:**
- Modify: `module/adapters/webui/templates/views.html`（活跃监听表头；history/download overlay）
- Modify: `unit_tests/web_ui_assets_case.py`（先加失败断言，build 后再绿——本任务只改模板，末尾需 build）

- [ ] **Step 1: 改表头为两列**

把 `views.html` 中活跃监听 `<thead>` 换成：

```html
<thead>
  <tr>
    <th data-i18n="watches.task">任务</th>
    <th class="watch-col-actions" data-i18n="tasks.actions">操作</th>
  </tr>
</thead>
```

在 `shared.js` 增加 `'watches.task': '任务'` / `'Task'`。

- [ ] **Step 2: 合并 overlay 为统一壳**

删除（或不再使用）独立的 `#watch-download-overlay` 结构，将 `#watch-history-overlay` 升级为：

```html
<div class="watch-overlay" id="watch-detail-overlay">
  <div class="watch-dialog watch-detail-dialog">
    <div class="watch-detail-header">
      <div>
        <h3 class="text-base font-semibold" id="watch-detail-title"></h3>
        <div class="text-xs text-muted font-mono mt-1" id="watch-detail-subtitle"></div>
      </div>
      <button type="button" class="btn btn-sm btn-icon" id="watch-detail-close" aria-label="Close">✕</button>
    </div>
    <div class="watch-detail-summary" id="watch-detail-summary"></div>
    <div class="watch-detail-filters" id="watch-detail-filters"></div>
    <div class="watch-detail-body" id="watch-detail-body"></div>
    <div class="watch-detail-footer" id="watch-detail-footer"></div>
  </div>
</div>
```

保留 `#watch-edit-overlay` 不动。

兼容：若仍有旧 id 引用，在 `desktop.js` 用新 id；本任务同时全局替换 `watch-history-overlay` → `watch-detail-overlay` 等（Task 3/4 完成逻辑）。

- [ ] **Step 3: 在 `web_ui_assets_case.py` 增加契约断言（先写，build 后才会绿）**

```python
def test_watches_detail_shell_present(self):
    self.assertIn('id="watch-detail-overlay"', WEB_UI_HTML)
    self.assertIn('id="watch-detail-body"', WEB_UI_HTML)
    self.assertNotIn('id="watch-download-overlay"', WEB_UI_HTML)

def test_watches_table_compact_headers(self):
    self.assertIn('data-i18n="watches.task"', WEB_UI_HTML)
```

- [ ] **Step 4: Commit 模板与测试断言（assets 生成放 Task 6）**

```bash
git add module/adapters/webui/templates/views.html module/adapters/webui/static/shared.js unit_tests/web_ui_assets_case.py
git commit -m "$(cat <<'EOF'
feat(webui): add watch detail shell markup and compact table headers

EOF
)"
```

---

### Task 3: 桌面紧凑列表 + `⋯` 菜单

**Files:**
- Modify: `module/adapters/webui/static/desktop.js`（`renderWatches`、点击委托、菜单）
- Modify: `module/adapters/webui/static/tailwind.css`（菜单 / 紧凑行样式）

- [ ] **Step 1: 重写 `renderWatches` 行 HTML（无 expand 行）**

目标行结构（逻辑示意）：

```js
function renderWatchRow(w) {
  const todayCount = w.today_count || 0;
  const eventCount = w.event_count || 0;
  const deferredCount = w.deferred_comment_count || 0;
  const route = formatWatchRoute(w.source_link, w.target_link);
  const fullSource = w.source_link || '';
  const statusDot = w.status === 'paused' ? 'watch-status-dot is-paused' : 'watch-status-dot is-running';
  const typeLabel = w.type === 'download' ? t('watches.download') : t('watches.forward');

  let deferredBadge = '';
  if (w.type === 'forward' && w.include_comment && deferredCount > 0) {
    deferredBadge = '<button type="button" class="watch-deferred-badge" data-watch-detail="deferred" data-watch-id="' + esc(w.id) + '">' +
      esc(t('watches.deferredComments')) + ' ' + deferredCount + '</button>';
  }

  let primary = '';
  if (w.type === 'forward') {
    primary = '<button type="button" class="btn btn-sm btn-primary" data-watch-detail="history" data-watch-id="' + esc(w.id) + '">' +
      esc(t('watches.history')) + (eventCount ? ' ' + eventCount : '') + '</button>';
  }

  return '<tr class="watch-row" data-watch-id="' + esc(w.id) + '" data-watch-type="' + esc(w.type || '') + '">' +
    '<td class="watch-col-task text-left">' +
      '<div class="watch-task-main">' +
        '<span class="' + statusDot + '" aria-hidden="true"></span>' +
        '<strong>' + esc(typeLabel) + '</strong>' +
        '<span class="text-muted text-xs">今日 ' + todayCount + '</span>' +
        deferredBadge +
      '</div>' +
      '<div class="watch-task-route font-mono text-xs text-muted" title="' + esc(fullSource) + '">' + esc(route) + '</div>' +
    '</td>' +
    '<td class="watch-col-actions">' +
      '<div class="table-actions flex gap-1 whitespace-nowrap">' +
        primary +
        '<button type="button" class="btn btn-sm" data-watch-menu="' + esc(w.id) + '" aria-label="' + esc(t('watches.moreActions')) + '" aria-haspopup="menu">⋯</button>' +
      '</div>' +
    '</td>' +
  '</tr>';
}
```

- 删除 `eventsRow` / `watch-events-row` 生成。
- 删除行点击 `toggleWatchEvents` 的 `document.addEventListener('click', … .watch-row)`（避免误开详情）。

- [ ] **Step 2: 实现桌面 `⋯` 下拉**

```js
function buildWatchMenuItems(w) {
  const items = [];
  if (w.type === 'forward') {
    items.push({ action: 'edit', label: t('watches.edit') });
    items.push({ action: 'downloads', label: t('watches.downloadRecords') });
    if (w.include_comment) {
      const n = w.deferred_comment_count || 0;
      items.push({ action: 'deferred', label: t('watches.deferredComments') + (n ? ' ' + n : '') });
    }
  }
  items.push({ action: 'delete', label: t('action.delete') || '删除', danger: true });
  return items;
}

function openWatchOverflowMenu(anchorBtn, watchId) {
  closeWatchOverflowMenu();
  const w = (state.watches || []).find(function(x) { return x.id === watchId; });
  if (!w) return;
  const menu = document.createElement('div');
  menu.id = 'watch-overflow-menu';
  menu.className = 'watch-overflow-menu';
  menu.setAttribute('role', 'menu');
  menu.innerHTML = buildWatchMenuItems(w).map(function(item) {
    return '<button type="button" role="menuitem" class="watch-overflow-item' + (item.danger ? ' is-danger' : '') +
      '" data-watch-menu-action="' + item.action + '" data-watch-id="' + esc(watchId) + '">' + esc(item.label) + '</button>';
  }).join('');
  document.body.appendChild(menu);
  const rect = anchorBtn.getBoundingClientRect();
  menu.style.top = (rect.bottom + 4 + window.scrollY) + 'px';
  menu.style.left = Math.max(8, rect.right - 200 + window.scrollX) + 'px';
}

function closeWatchOverflowMenu() {
  document.getElementById('watch-overflow-menu')?.remove();
}
```

点击委托：

- `data-watch-menu` → `openWatchOverflowMenu`
- `data-watch-menu-action="edit"` → 现有 `openEditWatchModal`
- `downloads` / `history` / `deferred` → `openWatchDetail(watchId, mode)`
- `delete` → 现有删除确认
- document click 外部关闭菜单

- [ ] **Step 3: CSS**

在 `tailwind.css` `@layer components` 增加：

```css
.watch-status-dot {
  @apply inline-block w-2 h-2 rounded-full shrink-0;
}
.watch-status-dot.is-running { @apply bg-success; }
.watch-status-dot.is-paused { @apply bg-muted; }

.watch-task-main {
  @apply flex items-center gap-2 flex-wrap;
}
.watch-task-route {
  @apply mt-1 overflow-hidden text-ellipsis whitespace-nowrap max-w-[36rem];
}
.watch-overflow-menu {
  @apply fixed z-[80] min-w-[180px] rounded-lg border border-line bg-surface shadow-lg py-1;
}
.watch-overflow-item {
  @apply block w-full text-left px-3 py-2 text-sm hover:bg-surface-hover cursor-pointer;
}
.watch-overflow-item.is-danger {
  @apply text-danger border-t border-line-light mt-1;
}
.watch-deferred-badge {
  @apply text-xs px-2 py-0.5 rounded-full bg-warning-soft text-warning cursor-pointer;
}
```

（token 名以现有 theme 为准：若无 `bg-success` 则用已有 badge/绿点色。）

- [ ] **Step 4: 手工/目视检查点（本任务不要求自动化 UI）**

打开桌面活跃监听：每行仅「记录」+「⋯」；无行内展开；暂停/运行点可见。

- [ ] **Step 5: Commit**

```bash
git add module/adapters/webui/static/desktop.js module/adapters/webui/static/tailwind.css
git commit -m "$(cat <<'EOF'
feat(webui): compact watch rows with overflow menu on desktop

EOF
)"
```

---

### Task 4: 桌面 `openWatchDetail` — history / downloads / deferred

**Files:**
- Modify: `module/adapters/webui/static/desktop.js`
- 删除或停用：`toggleWatchEvents`、`toggleWatchDeferred`、`restoreExpandedWatches`、`setExpandedWatch`、行内 panel 加载路径

- [ ] **Step 1: 统一打开函数**

```js
// state.watchDetail = { watchId, mode: 'history'|'downloads'|'deferred', page, pageSize, filter, total }

async function openWatchDetail(watchId, mode, page) {
  closeWatchOverflowMenu();
  const w = (state.watches || []).find(function(x) { return x.id === watchId; }) || {};
  state.watchDetail = {
    watchId: watchId,
    mode: mode || 'history',
    page: page || 1,
    pageSize: 20,
    filter: 'all',
    total: 0,
    watch: w,
  };
  const overlay = $('#watch-detail-overlay');
  if (!overlay) return;
  overlay.classList.add('open');
  $('#watch-detail-title').textContent =
    mode === 'downloads' ? t('watches.downloadRecordsTitle') :
    mode === 'deferred' ? t('watches.deferredComments') :
    t('watches.historyTitle');
  $('#watch-detail-subtitle').textContent = formatWatchRoute(w.source_link, w.target_link);
  await loadWatchDetail();
}

function closeWatchDetail() {
  $('#watch-detail-overlay')?.classList.remove('open');
  state.watchDetail = null;
  // stop download poll timer if any
}
```

- [ ] **Step 2: history 模式 — 状态优先列表 + 前端筛选**

```js
function renderWatchHistoryList(items, filter) {
  const filtered = filterWatchEventsByStatus(items, filter);
  if (!filtered.length) {
    return '<div class="p-8 text-center text-muted text-sm">' + esc(t('watches.noEvents')) + '</div>';
  }
  return '<div class="watch-detail-list">' + filtered.map(function(evt, idx) {
    const sum = summarizeWatchEvent(evt);
    const badgeCls = sum.kind === 'success' ? 'badge-success' : sum.kind === 'filtered' ? 'badge-warning' : 'badge-failed';
    const title = t(sum.titleKey);
    const meta = '#' + (evt.source_message_id || '-') + ' · ' + fmtTime(evt.created_at);
    const detailId = 'watch-evt-detail-' + idx;
    const canExpand = !!sum.detail;
    return '<div class="watch-detail-row"' + (canExpand ? ' data-expand-detail="' + detailId + '"' : '') + '>' +
      '<span class="badge ' + badgeCls + '">' + esc(title) + '</span>' +
      '<div class="watch-detail-row-main">' +
        '<div class="font-medium">' + esc(title) + '</div>' +
        '<div class="text-xs text-muted">' + esc(meta) +
          (canExpand ? ' · ' + esc(t('watches.detailExpandReason')) : '') +
        '</div>' +
        (canExpand ? '<div id="' + detailId + '" class="watch-detail-reason hidden text-xs text-muted mt-1">' + esc(sum.detail) + '</div>' : '') +
      '</div>' +
    '</div>';
  }).join('') + '</div>';
}
```

摘要条：`今日 {today_count} · 全部 {total}`（today 来自 `state.watchDetail.watch`）。  
筛选 chips 写入 `#watch-detail-filters`，点击改 `state.watchDetail.filter` 后重渲当前页 items（前端过滤）。  
分页：继续打 `/api/watches/:id/events?limit=&offset=`（与现逻辑相同），footer 用现有 `renderPaginationBar`。

- [ ] **Step 3: downloads / deferred 迁入同壳**

- downloads：把 `renderWatchDownloadSections` 输出塞进 `#watch-detail-body`；摘要用现有 bucket 计数；保留删除确认与 poll。
- deferred：把 `renderDeferredCommentRows` 改为状态优先行布局（可仍用 table，但包在 detail body）；API 与 run_now/cancel/retry 事件委托保持；**不再** `row.classList.add('open')`。

- [ ] **Step 4: 接线旧按钮数据属性**

将原 `data-watch-history` / `data-watch-downloads` / `data-watch-deferred` 处理改为 `data-watch-detail` 或统一走 `openWatchDetail`。删除对 `expandedWatches` 的依赖（`shared.js` state 字段可留空对象以免别处报错，或清掉并全局搜删）。

- [ ] **Step 5: Commit**

```bash
git add module/adapters/webui/static/desktop.js
git commit -m "$(cat <<'EOF'
feat(webui): unify desktop watch detail modal for history/downloads/deferred

EOF
)"
```

---

### Task 5: 移动端同构

**Files:**
- Modify: `module/adapters/webui/static/mobile_script.js`
- Modify: `module/adapters/webui/static/tailwind.css`（Action Sheet / 触控，如需）

- [ ] **Step 1: 重写移动 watch 卡片 actions**

每卡：

- 信息区：状态点 + 类型 + 今日 + 可选待抓徽标 + `formatWatchRoute`
- 底部：主按钮「记录 N」（仅 forward）+ `⋯`
- **删除** `mob-watch-events` 面板节点及 `data-watch-deferred` 行内展开逻辑

- [ ] **Step 2: `⋯` → 底部 Action Sheet**

复用现有 `#mob-sheet`：

```js
function openMobileWatchMenu(watchId) {
  const w = (state.watches || []).find(function(x) { return x.id === watchId; });
  if (!w) return;
  sheetState.sheetType = 'watch-menu';
  // render menu buttons mirroring buildWatchMenuItems(w)
  // 取消按钮 closeSheet
}
```

菜单动作打开 `openMobileWatchDetail(watchId, mode)`（history 已有 `openMobileWatchHistory` → 改名为统一入口）。

- [ ] **Step 3: 详情 Sheet 对齐桌面壳结构**

`openMobileWatchDetail`：

1. 标题 + 短链路副标题  
2. 摘要  
3. 筛选 chips（history）  
4. `renderWatchHistoryList`（直接复用 `shared.js` 函数）  
5. 分页  

downloads / deferred 同样进 sheet，不再插入列表中部。

触控：主按钮与 `⋯` 使用 `min-height: 44px`（CSS class `watch-touch-btn`）。

- [ ] **Step 4: Commit**

```bash
git add module/adapters/webui/static/mobile_script.js module/adapters/webui/static/tailwind.css
git commit -m "$(cat <<'EOF'
feat(webui): compact mobile watches with action sheet and detail sheet

EOF
)"
```

---

### Task 6: 样式收尾 + `build_frontend` + 资产契约测试

**Files:**
- Modify: `module/adapters/webui/static/tailwind.css`（detail list、filters）
- Run: `module/adapters/webui/build_frontend.py`（若项目有单独 tailwind build 步骤，先按 README/`package.json` 编译 CSS 再 embed）
- Modify: `module/adapters/webui/assets.py`（生成）
- 确认 `module/web_ui_assets.py` 仍指向生成物（若为 re-export，一般不用改）

- [ ] **Step 1: detail 列表 CSS**

```css
.watch-detail-summary {
  @apply px-4 py-2 bg-surface-alt border-b border-line text-xs text-muted flex flex-wrap gap-2 justify-between items-center;
}
.watch-detail-filters {
  @apply px-4 py-2 flex gap-2 overflow-x-auto border-b border-line;
}
.watch-detail-filter {
  @apply shrink-0 px-3 py-1 rounded-full border border-line text-xs cursor-pointer;
}
.watch-detail-filter.is-active {
  @apply bg-primary text-on-primary border-primary;
}
.watch-detail-row {
  @apply flex gap-3 px-4 py-3 border-b border-line-light cursor-pointer;
}
.watch-detail-reason.hidden { display: none; }
.watch-touch-btn {
  min-height: 44px;
  min-width: 44px;
}
```

- [ ] **Step 2: 构建**

先查仓库惯用命令（示例）：

```bash
# 若有 npm tailwind build：
# npm run build:css
python3 module/adapters/webui/build_frontend.py
```

Expected: 打印 Written `assets.py` 与各段 byte 数。

- [ ] **Step 3: 跑测试**

```bash
node unit_tests/watch_ui_helpers.test.mjs
python -m unittest unit_tests.web_ui_assets_case -v
```

Expected: 全部 PASS；`test_watches_detail_shell_present` / `test_watches_table_compact_headers` 绿；HTML 中不再依赖 `watch-events-row` 作为默认列表结构（若断言加了 `assertNotIn('watch-events-row'`，确保桌面 JS 模板字符串也不再包含——`WEB_UI_HTML` 内嵌 JS，故 `desktop.js` 删干净后自然消失）。

可选加强断言：

```python
self.assertNotIn('watch-events-row', WEB_UI_HTML)
self.assertNotIn('mob-watch-events', WEB_UI_MOBILE_HTML)
self.assertIn('data-watch-menu', WEB_UI_HTML)
```

- [ ] **Step 4: Commit**

```bash
git add module/adapters/webui/static/tailwind.css module/adapters/webui/assets.py module/adapters/webui/dist/tailwind.min.css unit_tests/web_ui_assets_case.py
git commit -m "$(cat <<'EOF'
feat(webui): build assets for watch action consolidation

EOF
)"
```

---

### Task 7: 手工验收清单（实现者勾选）

- [ ] 桌面：转发行只有「记录 N」+「⋯」；菜单含编辑/下载记录/待抓(条件)/删除
- [ ] 桌面：点记录打开统一壳；无目标列；长原因可展开；筛选切换当前页
- [ ] 桌面：⋯ → 下载记录 / 待抓 打开同壳不同 mode；列表不被撑开
- [ ] 桌面：监听下载行仅「⋯」，可删除
- [ ] 移动：卡片同构；⋯ 为 Action Sheet；详情为 Sheet；无横向滚动
- [ ] 待抓徽标仅 `deferred_comment_count > 0` 显示；菜单项在 `include_comment` 时始终有
- [ ] 编辑/删除确认行为与改前一致

---

## Spec coverage (self-review)

| Spec 要求 | Task |
|-----------|------|
| 记录外露 + ⋯ | Task 3 / 5 |
| 紧凑行 / 短链路 | Task 1 helpers + Task 3/5 |
| 取消行内展开 | Task 3/4/5 |
| 统一详情壳 history 状态优先 | Task 2 + 4 |
| downloads / deferred 同壳 | Task 4 / 5 |
| 移动 sheet / Action Sheet / 44px | Task 5 / 6 |
| 无新 API | 全程遵守 |
| 成功标准 ≤2 控件 | Task 3/5 + Task 7 |

## Placeholder scan

无 TBD；下载类主按钮已钉死为「仅 ⋯」。

## Type consistency

- `openWatchDetail(watchId, mode)` / `state.watchDetail.mode ∈ {history, downloads, deferred}`
- `globalThis.WatchUiHelpers` / `module.exports.WatchUiHelpers` 与 Node 测试同名；桌面/移动通过 `WatchUiHelpers.shortTelegramLink` 等调用
- DOM：`#watch-detail-overlay` 及 `title|subtitle|summary|filters|body|footer`
