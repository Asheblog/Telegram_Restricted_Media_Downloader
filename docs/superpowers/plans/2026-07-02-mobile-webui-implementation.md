# 移动版 WebUI 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 TRMD 转存控制台构建移动版 WebUI，通过服务端 UA 检测自动切换到移动端优化页面。

**Architecture:** 在 `web_ui_assets.py` 中新增独立的移动版 CSS/HTML/JS 变量，在 `web_ui.py` 中通过 `_send_html()` 的 UA 检测选择返回桌面版或移动版。移动版采用底部 4 Tab 导航 + 卡片列表布局，共享现有 API 调用逻辑。

**Tech Stack:** Python 3.13 `http.server`, vanilla HTML/CSS/JS (内嵌在 Python 字符串中)

**Design Spec:** `docs/superpowers/specs/2026-07-02-mobile-webui-design.md`

---

## 文件变更总览

| 文件 | 操作 | 说明 |
|------|------|------|
| `module/web_ui.py` | 修改 | `_send_html()` 增加 UA 检测 |
| `module/web_ui_assets.py` | 修改 | 提取共享 JS，新增移动端变量 |

---

### Task 1: 服务端 UA 检测

**Files:**
- Modify: `module/web_ui.py:19-20` (imports)
- Modify: `module/web_ui.py:188-195` (`_send_html`)

- [ ] **Step 1: 添加 `import re`**

在 `web_ui.py` 头部 import 区域，`from urllib.parse import unquote, urlparse, parse_qs` 之前添加：

```python
import re
```

- [ ] **Step 2: 修改 import 语句，导入移动版 HTML**

将 `module/web_ui.py:20` 的 import 改为：

```python
from module.web_ui_assets import WEB_UI_HTML, WEB_UI_MOBILE_HTML
```

- [ ] **Step 3: 修改 `_send_html()` 方法**

将 `module/web_ui.py:188-195` 的 `_send_html` 方法改为：

```python
def _send_html(self):
    ua = self.headers.get('user-agent', '')
    is_mobile = bool(re.search(r'Mobile|Android|iPhone|iPod', ua))
    html = WEB_UI_MOBILE_HTML if is_mobile else WEB_UI_HTML
    data = html.encode('utf-8')
    self.send_response(HTTPStatus.OK)
    self.send_header('content-type', 'text/html; charset=utf-8')
    self.send_header('cache-control', 'no-store')
    self.send_header('content-length', str(len(data)))
    self.end_headers()
    self.wfile.write(data)
```

- [ ] **Step 4: 验证语法**

```bash
python3 -c "import ast; ast.parse(open('module/web_ui.py').read()); print('OK')"
```

- [ ] **Step 5: 提交**

```bash
git add module/web_ui.py
git commit -m "feat: add UA-based mobile detection in WebUI"
```

---

### Task 2: 提取共享 JS 模块

**Files:**
- Modify: `module/web_ui_assets.py:1267-1762` (i18n + state + utility functions)
- Modify: `module/web_ui_assets.py:1764-1893` ($/$$ helpers, lower-level utilities)
- Modify: `module/web_ui_assets.py:1894-2703` (desktop-only rendering/binding code)

**策略**：将 `WEB_UI_SCRIPT` 拆分为两部分：
1. `SHARED_WEB_UI_SCRIPT` — 所有平台共享的逻辑（i18n、state、API 调用、工具函数、轮询）
2. `WEB_UI_SCRIPT` — 桌面版专用（DOM 绑定、表格渲染、桌面端组件）

移动版也将引用 `SHARED_WEB_UI_SCRIPT` 加上自己的移动端绑定。

- [ ] **Step 1: 在 `WEB_UI_SCRIPT` 之前插入 `SHARED_WEB_UI_SCRIPT` 变量**

在 `module/web_ui_assets.py` 中，`WEB_UI_SCRIPT = r'''` 行（约 1267 行）**之前**插入：

```python
SHARED_WEB_UI_SCRIPT = r'''
```

然后在 i18n 字典和 state 对象之后、桌面专用渲染代码之前（约 1893 行 `refreshVisibleDynamicText` 结束之后）插入：

```python
'''
```

具体来说，`SHARED_WEB_UI_SCRIPT` 包含从 `const i18n = {` 到 `function loadRecords()` 结尾的所有共享代码。切割点在 `renderTasks()` 等桌面端渲染函数之前。

- [ ] **Step 2: 识别共享边界，将 `SHARED_WEB_UI_SCRIPT` 结束**

在 `module/web_ui_assets.py` 中定位以下函数的结束位置作为共享代码的切割点：
- `postJson()` (约 1843 行结束)
- `localizeEventMessage()` / `localizeEventLevel()` (约 1871 行结束)
- `applyLanguage()` (约 1889 行结束)
- `refreshVisibleDynamicText()` (约 1898 行结束)
- `applyLanguageAndRefresh()` (约 1903 行结束)
- `switchView()` (约 1912 行结束)
- `badge()` (约 1916 行结束)
- `taskProgress()` (约 1935 行结束)

`SHARED_WEB_UI_SCRIPT` 的结束标记应放在 `taskProgress()` 函数之后。

- [ ] **Step 3: 重构 `WEB_UI_SCRIPT` 为共享 + 桌面专用**

将原来的 `WEB_UI_SCRIPT = r'''` 改为：

```python
WEB_UI_SCRIPT = SHARED_WEB_UI_SCRIPT + r'''
```

然后保留桌面端专用代码：`renderTasks()`、`loadTaskDetail()`、`renderItems()`、`renderEvents()`、`renderRecords()`、桌面端 DOM 绑定等。

- [ ] **Step 4: 验证 JS 语法完整性**

```bash
python3 -c "
from module.web_ui_assets import SHARED_WEB_UI_SCRIPT, WEB_UI_SCRIPT
print('SHARED_WEB_UI_SCRIPT length:', len(SHARED_WEB_UI_SCRIPT))
print('WEB_UI_SCRIPT length:', len(WEB_UI_SCRIPT))
# 验证 WEB_UI_SCRIPT 包含 SHARED_WEB_UI_SCRIPT
assert SHARED_WEB_UI_SCRIPT in WEB_UI_SCRIPT, 'WEB_UI_SCRIPT does not contain shared script'
print('OK: shared script embedded correctly')
"
```

- [ ] **Step 5: 提交**

```bash
git add module/web_ui_assets.py
git commit -m "refactor: extract shared JS module for mobile reuse"
```

---

### Task 3: 移动端 CSS

**Files:**
- Modify: `module/web_ui_assets.py` (在 `WEB_UI_CSS` 之后新增 `WEB_UI_MOBILE_CSS`)

- [ ] **Step 1: 新增 `WEB_UI_MOBILE_CSS` 变量**

在 `module/web_ui_assets.py` 中，`WEB_UI_CSS` 的结束 `'''` 之后，`WEB_UI_BODY` 之前插入：

```python
WEB_UI_MOBILE_CSS = r'''
  :root {
    color-scheme: light;
    --bg: #f7f8fa;
    --surface: #ffffff;
    --surface-muted: #f0f3f5;
    --text: #17201b;
    --muted: #5b6670;
    --line: #d8dee4;
    --accent: #0f8f72;
    --accent-strong: #0a6f5a;
    --blue: #2563eb;
    --danger: #b42318;
    --warn: #a15c07;
    --ok: #127c52;
    --font-xs: 12px;
    --font-sm: 13px;
    --font-md: 15px;
    --font-lg: 16px;
    --font-xl: 20px;
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --tab-height: 56px;
    --topbar-height: 48px;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: var(--font-md);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    min-height: 100svh;
    -webkit-tap-highlight-color: transparent;
    user-select: none;
    padding-top: var(--topbar-height);
    padding-bottom: calc(var(--tab-height) + var(--safe-bottom));
  }
  button, input, select, textarea {
    font: inherit;
  }
  button {
    border: 0;
    border-radius: 8px;
    padding: 12px 16px;
    background: var(--accent);
    color: #fff;
    font-weight: 600;
    cursor: pointer;
    min-height: 44px;
    min-width: 44px;
    transition: opacity .15s;
  }
  button:active { opacity: .75; }
  button.secondary {
    background: var(--surface);
    border: 1px solid var(--line);
    color: var(--text);
  }
  button.danger {
    background: transparent;
    color: var(--danger);
    border: 1px solid var(--danger);
  }
  button.small {
    padding: 8px 12px;
    min-height: 36px;
    font-size: var(--font-sm);
  }
  input, select, textarea {
    width: 100%;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 12px 14px;
    background: var(--surface);
    color: var(--text);
    min-height: 44px;
    font-size: 16px;
  }
  input:focus, select:focus, textarea:focus {
    border-color: var(--accent);
    outline: none;
    box-shadow: 0 0 0 3px rgba(15, 143, 114, .15);
  }
  label {
    display: grid;
    gap: 6px;
    color: var(--muted);
    font-size: var(--font-sm);
  }

  /* ---- Top Bar ---- */
  .mob-topbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: var(--topbar-height);
    background: var(--surface);
    border-bottom: 1px solid var(--line);
    display: flex;
    align-items: center;
    padding: 0 14px;
    gap: 10px;
    z-index: 100;
  }
  .mob-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    font-size: var(--font-lg);
  }
  .mob-brand .mark {
    width: 28px; height: 28px;
    border-radius: 6px;
    background: var(--accent);
    display: grid;
    place-items: center;
    color: #fff;
  }
  .mob-topbar-actions {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .mob-topbar-actions select {
    width: auto;
    min-height: 0;
    padding: 4px 8px;
    font-size: var(--font-sm);
    border-radius: 6px;
  }

  /* ---- Bottom Tab Bar ---- */
  .mob-tabbar {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    height: calc(var(--tab-height) + var(--safe-bottom));
    padding-bottom: var(--safe-bottom);
    background: var(--surface);
    border-top: 1px solid var(--line);
    display: flex;
    justify-content: space-around;
    align-items: flex-start;
    padding-top: 6px;
    z-index: 100;
  }
  .mob-tab {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    font-size: 10px;
    color: var(--muted);
    min-width: 44px;
    cursor: pointer;
    padding: 4px 0;
    border: 0;
    background: transparent;
    border-radius: 0;
    min-height: auto;
    font-weight: 400;
  }
  .mob-tab.active {
    color: var(--accent);
    font-weight: 600;
  }
  .mob-tab svg {
    width: 22px;
    height: 22px;
  }

  /* ---- Content Area ---- */
  .mob-content {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    animation: mobRise .3s ease both;
  }
  @keyframes mobRise {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .mob-view {
    display: none;
  }
  .mob-view.active {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  /* ---- Card List ---- */
  .mob-card {
    background: var(--surface);
    border-radius: 10px;
    padding: 14px;
    border: 1px solid var(--line);
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
  }
  .mob-card__head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
  }
  .mob-card__title {
    font-weight: 650;
    font-size: var(--font-md);
    word-break: break-all;
  }
  .mob-card__badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: var(--font-xs);
    font-weight: 600;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .mob-card__badge.pending { background: #f1f5f9; color: #475569; }
  .mob-card__badge.running { background: #dcfce7; color: #166534; }
  .mob-card__badge.paused { background: #fef9c3; color: #a16207; }
  .mob-card__badge.completed { background: #dbeafe; color: #1e40af; }
  .mob-card__badge.failure { background: #fee2e2; color: #b91c1c; }
  .mob-card__badge.cancelled { background: #f1f5f9; color: #64748b; }
  .mob-card__row {
    display: flex;
    justify-content: space-between;
    padding: 3px 0;
    font-size: var(--font-sm);
  }
  .mob-card__row .label {
    color: var(--muted);
  }
  .mob-card__progress {
    margin: 6px 0;
    height: 6px;
    border-radius: 3px;
    background: var(--surface-muted);
    overflow: hidden;
  }
  .mob-card__progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 3px;
    transition: width .3s;
  }
  .mob-card__actions {
    display: flex;
    gap: 6px;
    margin-top: 8px;
    flex-wrap: wrap;
  }

  /* ---- Collapse Panel ---- */
  .mob-collapse {
    border: 1px solid var(--line);
    border-radius: 10px;
    overflow: hidden;
    background: var(--surface);
  }
  .mob-collapse__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px;
    cursor: pointer;
    font-weight: 600;
    user-select: none;
  }
  .mob-collapse__head:active { background: var(--surface-muted); }
  .mob-collapse__arrow {
    transition: transform .2s;
    color: var(--muted);
  }
  .mob-collapse.open .mob-collapse__arrow {
    transform: rotate(180deg);
  }
  .mob-collapse__body {
    display: none;
    padding: 0 14px 14px;
    flex-direction: column;
    gap: 10px;
  }
  .mob-collapse.open .mob-collapse__body {
    display: flex;
  }

  /* ---- Drawer (更多菜单) ---- */
  .mob-drawer-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.35);
    z-index: 200;
    display: none;
    align-items: flex-end;
  }
  .mob-drawer-overlay.open {
    display: flex;
  }
  .mob-drawer {
    width: 100%;
    background: var(--surface);
    border-radius: 16px 16px 0 0;
    padding: 8px 0 calc(24px + var(--safe-bottom));
    max-height: 70vh;
    overflow: auto;
  }
  .mob-drawer__handle {
    width: 36px;
    height: 4px;
    background: var(--line);
    border-radius: 2px;
    margin: 8px auto 12px;
  }
  .mob-drawer__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    font-size: var(--font-md);
    cursor: pointer;
    border: 0;
    background: transparent;
    width: 100%;
    min-height: auto;
    border-radius: 0;
    color: var(--text);
    font-weight: 400;
  }
  .mob-drawer__item:active {
    background: var(--surface-muted);
  }
  .mob-drawer__item svg {
    width: 20px;
    height: 20px;
    color: var(--muted);
  }

  /* ---- FAB ---- */
  .mob-fab {
    position: fixed;
    bottom: calc(var(--tab-height) + var(--safe-bottom) + 16px);
    right: 16px;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    font-size: 24px;
    display: grid;
    place-items: center;
    box-shadow: 0 4px 16px rgba(15, 143, 114, .4);
    z-index: 90;
    cursor: pointer;
    transition: transform .2s, box-shadow .2s;
    min-height: auto;
    min-width: auto;
    padding: 0;
  }
  .mob-fab:active {
    transform: scale(.92);
    box-shadow: 0 2px 8px rgba(15, 143, 114, .3);
  }

  /* ---- FAB Menu ---- */
  .mob-fab-menu {
    position: fixed;
    bottom: calc(var(--tab-height) + var(--safe-bottom) + 72px);
    right: 16px;
    display: none;
    flex-direction: column;
    gap: 8px;
    z-index: 90;
  }
  .mob-fab-menu.open {
    display: flex;
  }
  .mob-fab-menu__item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 10px;
    font-size: var(--font-sm);
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0,0,0,.08);
    cursor: pointer;
    white-space: nowrap;
    min-height: auto;
    color: var(--text);
  }
  .mob-fab-menu__item:active {
    background: var(--surface-muted);
  }

  /* ---- Bottom Sheet ---- */
  .mob-sheet-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.35);
    z-index: 300;
    display: none;
    align-items: flex-end;
  }
  .mob-sheet-overlay.open {
    display: flex;
  }
  .mob-sheet {
    width: 100%;
    background: var(--surface);
    border-radius: 16px 16px 0 0;
    padding: 20px 16px max(24px, var(--safe-bottom));
    max-height: 85vh;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .mob-sheet__title {
    font-size: var(--font-lg);
    font-weight: 700;
    margin: 0;
  }
  .mob-sheet__close {
    position: absolute;
    top: 16px;
    right: 16px;
    min-width: 32px;
    min-height: 32px;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--surface-muted);
    color: var(--muted);
    display: grid;
    place-items: center;
    font-size: 16px;
    padding: 0;
  }

  /* ---- Toast ---- */
  .mob-toast {
    position: fixed;
    bottom: calc(var(--tab-height) + var(--safe-bottom) + 16px);
    left: 50%;
    transform: translateX(-50%);
    background: var(--text);
    color: #fff;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: var(--font-sm);
    z-index: 400;
    opacity: 0;
    pointer-events: none;
    transition: opacity .25s;
    white-space: nowrap;
  }
  .mob-toast.show {
    opacity: 1;
    pointer-events: auto;
  }

  /* ---- Empty State ---- */
  .mob-empty {
    text-align: center;
    color: var(--muted);
    padding: 40px 20px;
    font-size: var(--font-sm);
  }

  /* ---- Section Header ---- */
  .mob-section-title {
    font-size: var(--font-xs);
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--muted);
    padding: 4px 0;
  }

  /* ---- Scrollable Table (统计) ---- */
  .mob-table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border: 1px solid var(--line);
    border-radius: 8px;
  }
  .mob-table-wrap table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--font-sm);
  }
  .mob-table-wrap th,
  .mob-table-wrap td {
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid var(--line);
    white-space: nowrap;
  }
  .mob-table-wrap th {
    background: var(--surface-muted);
    font-weight: 600;
    position: sticky;
    top: 0;
  }
'''
```

- [ ] **Step 2: 验证 CSS 语法**

```bash
python3 -c "
from module.web_ui_assets import WEB_UI_MOBILE_CSS
print('WEB_UI_MOBILE_CSS length:', len(WEB_UI_MOBILE_CSS))
print('OK')
"
```

- [ ] **Step 3: 提交**

```bash
git add module/web_ui_assets.py
git commit -m "feat: add mobile WebUI CSS"
```

---

### Task 4: 移动端 HTML 结构

**Files:**
- Modify: `module/web_ui_assets.py` (新增 `WEB_UI_MOBILE_BODY`)

- [ ] **Step 1: 新增 `WEB_UI_MOBILE_BODY` 变量**

在 `WEB_UI_MOBILE_CSS` 之后插入：

```python
WEB_UI_MOBILE_BODY = f'''
<div class="mob-topbar">
  <div class="mob-brand">
    <div class="mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </div>
    <span>TRMD</span>
  </div>
  <div class="mob-topbar-actions">
    <select id="language-select" aria-label="语言">
      <option value="zh">中文</option>
      <option value="en">EN</option>
    </select>
    <button class="secondary small" type="button" id="refresh" aria-label="刷新">
      <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
  </div>
</div>

<div class="mob-content" id="mob-content">
  <!-- 转存任务 -->
  <div class="mob-view active" id="mob-view-transfers">
    <div class="mob-collapse" id="collapse-transfer-form">
      <div class="mob-collapse__head" data-i18n="new.title">新建转存 <span class="mob-collapse__arrow">▼</span></div>
      <div class="mob-collapse__body">
        <form id="mob-transfer-form">
          <label><span data-i18n="new.source">来源链接</span>
            <input type="text" name="source_link" placeholder="https://t.me/..." required>
          </label>
          <label><span data-i18n="new.target">目标</span>
            <input type="text" name="target_link" value="https://t.me/pikpak_bot" required>
          </label>
          <label><span data-i18n="new.targetProfile">目标配置</span>
            <select name="target_profile">
              <option value="pikpak" data-i18n="profile.pikpak">PikPak 文档转存</option>
              <option value="generic" data-i18n="profile.generic">通用 Telegram 目标</option>
            </select>
          </label>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <label><span data-i18n="new.startId">起始 ID</span>
              <input type="number" name="start_id" placeholder="可选">
            </label>
            <label><span data-i18n="new.endId">结束 ID</span>
              <input type="number" name="end_id" placeholder="可选">
            </label>
          </div>
          <label style="flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" name="include_comment" style="width:auto;min-height:auto;">
            <span data-i18n="new.includeComment">包含评论区</span>
          </label>
          <button type="submit" style="width:100%;" data-i18n="new.create">创建任务</button>
          <p class="mob-empty" id="mob-form-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-tasks-list"></div>
  </div>

  <!-- 实时监听 -->
  <div class="mob-view" id="mob-view-watches">
    <div class="mob-collapse" id="collapse-watch-form">
      <div class="mob-collapse__head" data-i18n="watches.title">实时监听 <span class="mob-collapse__arrow">▼</span></div>
      <div class="mob-collapse__body">
        <form id="mob-watch-form">
          <label><span data-i18n="watches.type">类型</span>
            <select name="watch_type" id="mob-watch-type">
              <option value="download" data-i18n="watches.download">监听下载</option>
              <option value="forward" data-i18n="watches.forward">监听转发</option>
            </select>
          </label>
          <div id="mob-watch-source-group">
            <label><span data-i18n="watches.sources">来源频道</span>
              <textarea name="source_links" rows="3" placeholder="每行一个 https://t.me/... 链接" required></textarea>
            </label>
          </div>
          <div id="mob-watch-target-group" style="display:none;">
            <label><span data-i18n="watches.target">目标频道</span>
              <input type="text" name="target_link" placeholder="https://t.me/...">
            </label>
          </div>
          <div id="mob-watch-comment-group" style="display:none;">
            <label style="flex-direction:row;align-items:center;gap:8px;">
              <input type="checkbox" name="include_comment" style="width:auto;min-height:auto;">
              <span data-i18n="watches.includeComment">包含评论区</span>
            </label>
          </div>
          <button type="submit" style="width:100%;" data-i18n="watches.createDownload">新增监听</button>
          <p class="mob-empty" id="mob-watch-notice" style="display:none;"></p>
        </form>
      </div>
    </div>
    <div id="mob-watches-list"></div>
  </div>

  <!-- 设置 -->
  <div class="mob-view" id="mob-view-settings">
    <div class="mob-collapse open" id="collapse-settings-paths">
      <div class="mob-collapse__head" data-i18n="settings.paths">路径与任务 <span class="mob-collapse__arrow">▼</span></div>
      <div class="mob-collapse__body" id="mob-settings-path-fields">
        <!-- JS 动态填充 -->
      </div>
    </div>
    <div class="mob-collapse" id="collapse-settings-behavior">
      <div class="mob-collapse__head" data-i18n="settings.behavior">行为 <span class="mob-collapse__arrow">▼</span></div>
      <div class="mob-collapse__body" id="mob-settings-behavior-fields">
        <!-- JS 动态填充 -->
      </div>
    </div>
    <div class="mob-collapse" id="collapse-settings-sensitive">
      <div class="mob-collapse__head" data-i18n="settings.sensitive">账号与代理 <span class="mob-collapse__arrow">▼</span></div>
      <div class="mob-collapse__body" id="mob-settings-sensitive-fields">
        <!-- JS 动态填充 -->
      </div>
    </div>
    <div class="mob-collapse" id="collapse-settings-archive">
      <div class="mob-collapse__head" data-i18n="settings.pikpakArchive">PikPak 归档 <span class="mob-collapse__arrow">▼</span></div>
      <div class="mob-collapse__body" id="mob-settings-archive-fields">
        <!-- JS 动态填充 -->
      </div>
    </div>
    <button id="mob-save-settings" style="width:100%;margin-top:4px;" data-i18n="settings.save">保存设置</button>
  </div>

  <!-- 频道下载 -->
  <div class="mob-view" id="mob-view-channel-downloads">
    <div class="mob-empty" data-i18n="channel.title">频道下载 — 即将推出</div>
  </div>

  <!-- 本地上传 -->
  <div class="mob-view" id="mob-view-uploads">
    <div class="mob-empty" data-i18n="uploads.title">本地上传 — 即将推出</div>
  </div>

  <!-- 统计 -->
  <div class="mob-view" id="mob-view-statistics">
    <div class="mob-empty" data-i18n="statistics.title">统计 — 即将推出</div>
  </div>

  <!-- 下载记录 -->
  <div class="mob-view" id="mob-view-records">
    <div class="mob-empty" data-i18n="records.title">下载记录 — 即将推出</div>
  </div>
</div>

<!-- FAB + Menu -->
<div class="mob-fab-menu" id="mob-fab-menu">
  <button class="mob-fab-menu__item" id="mob-fab-new-transfer">
    <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="new.title">新建转存</span>
  </button>
  <button class="mob-fab-menu__item" id="mob-fab-new-watch">
    <svg viewBox="0 0 24 24" fill="none" width="18" height="18"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/></svg>
    <span data-i18n="watches.title">新建监听</span>
  </button>
</div>
<button class="mob-fab" id="mob-fab" aria-label="新建">+</button>

<!-- Bottom Tab Bar -->
<div class="mob-tabbar" id="mob-tabbar">
  <button class="mob-tab active" data-mob-nav="transfers">
    <svg viewBox="0 0 24 24" fill="none"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="nav.transfers">转存</span>
  </button>
  <button class="mob-tab" data-mob-nav="watches">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/><path d="M4 12s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 9v3l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    <span data-i18n="nav.watches">监听</span>
  </button>
  <button class="mob-tab" data-mob-nav="settings">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3.5" stroke="currentColor" stroke-width="2"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 1.98l.04.04a2 2 0 0 1-2.82 2.82l-.04-.04A1.8 1.8 0 0 0 15 19.4M4.6 9a1.8 1.8 0 0 0-.36-1.98l-.04-.04a2 2 0 0 1 2.82-2.82l.04.04A1.8 1.8 0 0 0 9 4.6" stroke="currentColor" stroke-width="1.5"/></svg>
    <span data-i18n="nav.settings">设置</span>
  </button>
  <button class="mob-tab" data-mob-nav="more">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="5" cy="12" r="1.5" fill="currentColor"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="19" cy="12" r="1.5" fill="currentColor"/></svg>
    <span>更多</span>
  </button>
</div>

<!-- 更多 Drawer -->
<div class="mob-drawer-overlay" id="mob-drawer-overlay">
  <div class="mob-drawer" id="mob-drawer">
    <div class="mob-drawer__handle"></div>
    <button class="mob-drawer__item" data-mob-drawer-nav="channel-downloads">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 5h14v10H8l-3 3V5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.channelDownloads">频道下载</span>
    </button>
    <button class="mob-drawer__item" data-mob-drawer-nav="uploads">
      <svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span data-i18n="nav.uploads">本地上传</span>
    </button>
    <button class="mob-drawer__item" data-mob-drawer-nav="statistics">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 19V9M12 19V5M19 19v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M4 19h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.statistics">统计</span>
    </button>
    <button class="mob-drawer__item" data-mob-drawer-nav="records">
      <svg viewBox="0 0 24 24" fill="none"><path d="M5 4h14v16H5z" stroke="currentColor" stroke-width="2"/><path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span data-i18n="nav.records">下载记录</span>
    </button>
  </div>
</div>

<!-- Bottom Sheet Overlay (通用) -->
<div class="mob-sheet-overlay" id="mob-sheet-overlay">
  <div class="mob-sheet" id="mob-sheet"></div>
</div>

<!-- Toast -->
<div class="mob-toast" id="mob-toast"></div>
'''
```

注意：HTML 中混用了部分 `f''` 中不存在的 Python 表达式时需要检查。`WEB_UI_MOBILE_BODY` 使用 `f'...'` 可以与 `panel_head()` 配合，但目前这段 HTML 中暂不需要 Python 函数嵌入。如果后续需要动态生成 HTML 片段，可以参考现有 `WEB_UI_BODY` 的做法。

- [ ] **Step 2: 验证 HTML 变量加载**

```bash
python3 -c "
from module.web_ui_assets import WEB_UI_MOBILE_BODY
print('WEB_UI_MOBILE_BODY length:', len(WEB_UI_MOBILE_BODY))
print('OK')
"
```

- [ ] **Step 3: 提交**

```bash
git add module/web_ui_assets.py
git commit -m "feat: add mobile WebUI HTML structure with bottom tab bar"
```

---

### Task 5: 移动端 JS

**Files:**
- Modify: `module/web_ui_assets.py` (在 `WEB_UI_MOBILE_BODY` 之后新增 `WEB_UI_MOBILE_SCRIPT`)

- [ ] **Step 1: 新增 `WEB_UI_MOBILE_SCRIPT` 变量**

```python
WEB_UI_MOBILE_SCRIPT = SHARED_WEB_UI_SCRIPT + r'''
  /* ====== 移动端视图切换 ====== */
  function mobSwitchView(view) {
    $$('.mob-view').forEach(el => el.classList.toggle('active', el.id === `mob-view-${view}`));
    $$('.mob-tab').forEach(el => el.classList.toggle('active', el.dataset.mobNav === view));
    closeDrawer();
    closeFabMenu();
    if (view === 'settings') loadSettings();
    if (view === 'records') loadRecords();
    if (view === 'watches') loadWatches();
    if (view === 'statistics') loadStatistics();
  }

  /* ====== 抽屉（更多菜单） ====== */
  function openDrawer() {
    $('#mob-drawer-overlay').classList.add('open');
  }
  function closeDrawer() {
    $('#mob-drawer-overlay').classList.remove('open');
  }

  /* ====== FAB 菜单 ====== */
  function toggleFabMenu() {
    const menu = $('#mob-fab-menu');
    const fab = $('#mob-fab');
    const isOpen = menu.classList.contains('open');
    if (isOpen) {
      menu.classList.remove('open');
      fab.textContent = '+';
    } else {
      menu.classList.add('open');
      fab.textContent = '\u00d7';
    }
  }
  function closeFabMenu() {
    const menu = $('#mob-fab-menu');
    const fab = $('#mob-fab');
    menu.classList.remove('open');
    fab.textContent = '+';
  }

  /* ====== 折叠面板 ====== */
  function toggleCollapse(head) {
    head.closest('.mob-collapse').classList.toggle('open');
  }

  /* ====== Toast ====== */
  let mobToastTimer = null;
  function showToast(message, duration = 2500) {
    const toast = $('#mob-toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(mobToastTimer);
    mobToastTimer = setTimeout(() => toast.classList.remove('show'), duration);
  }

  /* ====== Bottom Sheet ====== */
  function openSheet(html) {
    $('#mob-sheet').innerHTML = html;
    $('#mob-sheet-overlay').classList.add('open');
  }
  function closeSheet() {
    $('#mob-sheet-overlay').classList.remove('open');
  }

  /* ====== 卡片状态徽章 ====== */
  function mobBadge(status) {
    const cls = status === 'running' ? 'running' :
                status === 'completed' ? 'completed' :
                status === 'paused' ? 'paused' :
                status === 'failure' ? 'failure' :
                status === 'cancelled' ? 'cancelled' : 'pending';
    return `<span class="mob-card__badge ${cls}">${esc(t('status.' + status))}</span>`;
  }

  /* ====== 渲染转存任务卡片列表 ====== */
  function renderMobTasks() {
    const tasks = state.tasks || [];
    const container = $('#mob-tasks-list');
    if (!tasks.length) {
      container.innerHTML = `<div class="mob-empty" data-i18n="tasks.empty">${t('tasks.empty')}</div>`;
      return;
    }
    container.innerHTML = tasks.map(task => {
      const total = Number(task.total_items || 0);
      const done = Number(task.completed_items || 0);
      const failed = Number(task.failed_items || 0);
      const percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
      return `
        <div class="mob-card">
          <div class="mob-card__head">
            <span class="mob-card__title">${esc(task.source_link)}</span>
            ${mobBadge(task.status)}
          </div>
          <div class="mob-card__row">
            <span class="label">${t('tasks.target')}</span>
            <span>${esc(task.target_link)}</span>
          </div>
          <div class="mob-card__row">
            <span class="label">${t('tasks.progress')}</span>
            <span>${done}/${total}${failed ? ` (${failed} ${t('side.failed')})` : ''}</span>
          </div>
          <div class="mob-card__progress">
            <div class="mob-card__progress-fill" style="width:${percent}%"></div>
          </div>
          <div class="mob-card__actions">
            ${task.status === 'running'
              ? `<button class="secondary small" data-pause="${task.id}">${t('tasks.pause')}</button>`
              : ''}
            ${task.status === 'paused'
              ? `<button class="secondary small" data-resume="${task.id}">${t('tasks.resume')}</button>`
              : ''}
            ${task.failed_items > 0
              ? `<button class="secondary small" data-retry="${task.id}">${t('tasks.retryFailed')}</button>`
              : ''}
            <button class="danger small" data-delete="${task.id}">${t('tasks.delete')}</button>
          </div>
        </div>`;
    }).join('');

    container.querySelectorAll('[data-pause]').forEach(btn =>
      btn.addEventListener('click', e => runTaskAction(e, Number(e.target.dataset.pause), 'pause')));
    container.querySelectorAll('[data-resume]').forEach(btn =>
      btn.addEventListener('click', e => runTaskAction(e, Number(e.target.dataset.resume), 'resume')));
    container.querySelectorAll('[data-retry]').forEach(btn =>
      btn.addEventListener('click', e => runTaskAction(e, Number(e.target.dataset.retry), 'retry-failed')));
    container.querySelectorAll('[data-delete]').forEach(btn =>
      btn.addEventListener('click', e => deleteTask(e, Number(e.target.dataset.delete))));
  }

  /* ====== 渲染监听卡片列表 ====== */
  function renderMobWatches() {
    const watches = state.watches || [];
    const container = $('#mob-watches-list');
    if (!watches.length) {
      container.innerHTML = `<div class="mob-empty" data-i18n="watches.empty">${t('watches.empty')}</div>`;
      return;
    }
    container.innerHTML = watches.map(w => `
      <div class="mob-card">
        <div class="mob-card__head">
          <span class="mob-card__title">${esc(w.type === 'download' ? t('watches.download') : t('watches.forward'))}</span>
          <span class="mob-card__badge running">${esc(w.type)}</span>
        </div>
        ${w.source_links ? `
          <div class="mob-card__row">
            <span class="label">${t('watches.sources')}</span>
            <span>${esc((w.source_links || []).join(', '))}</span>
          </div>` : ''}
        ${w.source_link ? `
          <div class="mob-card__row">
            <span class="label">${t('watches.source')}</span>
            <span>${esc(w.source_link)}</span>
          </div>` : ''}
        ${w.target_link ? `
          <div class="mob-card__row">
            <span class="label">${t('watches.target')}</span>
            <span>${esc(w.target_link)}</span>
          </div>` : ''}
        <div class="mob-card__actions">
          <button class="danger small" data-delete-watch="${w.encoded_id || w.id}">${t('watches.delete')}</button>
        </div>
      </div>`).join('');

    container.querySelectorAll('[data-delete-watch]').forEach(btn =>
      btn.addEventListener('click', () => deleteWatch(btn.dataset.deleteWatch)));
  }

  /* ====== 渲染设置表单 ====== */
  function renderMobSettingsForm() {
    if (!state.settings || !state.schema) return;
    const s = state.settings;
    const commonPasswordPattern = state.schema.sensitive_keys || [];

    function sensitiveField(key, value) {
      return `
        <label><span>${esc(key)}</span>
          <input type="password" name="${esc(key)}" placeholder="${value && value.configured ? t('settings.secretConfigured') : t('settings.secretNotConfigured')}" autocomplete="new-password">
        </label>`;
    }

    function numberField(key, value, schema) {
      const min = schema && schema.min != null ? `min="${schema.min}"` : '';
      const max = schema && schema.max != null ? `max="${schema.max}"` : '';
      return `
        <label><span>${esc(key)}</span>
          <input type="number" name="${esc(key)}" value="${esc(value)}" ${min} ${max}>
        </label>`;
    }

    function textField(key, value) {
      return `
        <label><span>${esc(key)}</span>
          <input type="text" name="${esc(key)}" value="${esc(value)}">
        </label>`;
    }

    function checkboxField(key, value) {
      return `
        <label style="flex-direction:row;align-items:center;gap:8px;">
          <input type="checkbox" name="${esc(key)}" ${value ? 'checked' : ''} style="width:auto;min-height:auto;">
          <span>${esc(key)}</span>
        </label>`;
    }

    const user = s.user || {};
    const glob = s.global || {};

    $('#mob-settings-path-fields').innerHTML = `
      ${textField('save_directory', user.save_directory || '')}
      ${textField('temp_directory', user.temp_directory || '')}
      ${textField('session_directory', user.session_directory || '')}
      ${numberField('max_tasks', user.max_tasks || 0, state.schema)}
      ${numberField('max_retries', user.max_retries || 0, {min: 0})}
    `;

    $('#mob-settings-behavior-fields').innerHTML = `
      ${checkboxField('notice', glob.notice)}
      ${checkboxField('is_shutdown', user.is_shutdown)}
      ${numberField('upload_pending_limit', glob.upload_pending_limit || 1, state.schema)}
    `;

    $('#mob-settings-sensitive-fields').innerHTML = commonPasswordPattern.map(k =>
      sensitiveField(k, user[k])
    ).join('');

    const targetProfiles = glob.target_profiles || {};
    const pikpak = targetProfiles.pikpak || {};
    $('#mob-settings-archive-fields').innerHTML = `
      ${checkboxField('pikpak_archive_enable', glob.pikpak_archive_enable)}
      ${textField('pikpak_archive_remote', glob.pikpak_archive_remote || '')}
      ${textField('pikpak_archive_source', glob.pikpak_archive_source || '')}
      ${textField('pikpak_archive_root', glob.pikpak_archive_root || '')}
      ${numberField('pikpak_archive_poll', glob.pikpak_archive_poll || 60, {min: 1})}
    `;
  }

  /* ====== 覆盖：loadTasks / loadWatches 完成后回调 ====== */
  const _originalLoadTasks = loadTasks;
  loadTasks = async function() {
    await _originalLoadTasks();
    if (state.tasks) renderMobTasks();
  };

  const _originalLoadWatches = loadWatches;
  loadWatches = async function() {
    await _originalLoadWatches();
    if (state.watches) renderMobWatches();
  };

  const _originalLoadSettings = loadSettings;
  loadSettings = async function() {
    await _originalLoadSettings();
    renderMobSettingsForm();
  };

  /* ====== 事件绑定 ====== */
  $('#language-select').addEventListener('change', event => {
    state.lang = event.target.value;
    localStorage.setItem('trmd-lang', state.lang);
    applyLanguageAndRefresh();
    renderMobTasks();
    renderMobWatches();
  });

  $('#refresh').addEventListener('click', () => {
    loadTasks();
    const activeView = document.querySelector('.mob-view.active');
    if (activeView) {
      const viewId = activeView.id.replace('mob-view-', '');
      if (viewId === 'settings') loadSettings();
      if (viewId === 'watches') loadWatches();
    }
    showToast(t('action.refresh') + ' OK');
  });

  /* Tab 栏点击 */
  $$('.mob-tab').forEach(tab => {
    tab.addEventListener('click', () => mobSwitchView(tab.dataset.mobNav));
  });

  /* "更多"按钮 -> 打开 Drawer */
  $('.mob-tab[data-mob-nav="more"]').addEventListener('click', openDrawer);

  /* Drawer 内菜单项点击 */
  $$('[data-mob-drawer-nav]').forEach(item => {
    item.addEventListener('click', () => mobSwitchView(item.dataset.mobDrawerNav));
  });

  /* Drawer overlay 点击关闭 */
  $('#mob-drawer-overlay').addEventListener('click', function(e) {
    if (e.target === this) closeDrawer();
  });

  /* FAB 点击 */
  $('#mob-fab').addEventListener('click', toggleFabMenu);

  /* FAB 菜单项 */
  $('#mob-fab-new-transfer').addEventListener('click', () => {
    closeFabMenu();
    const collapse = $('#collapse-transfer-form');
    collapse.classList.add('open');
    collapse.scrollIntoView({ behavior: 'smooth' });
  });
  $('#mob-fab-new-watch').addEventListener('click', () => {
    closeFabMenu();
    mobSwitchView('watches');
    const collapse = $('#collapse-watch-form');
    collapse.classList.add('open');
    collapse.scrollIntoView({ behavior: 'smooth' });
  });

  /* 折叠面板切换 */
  $$('.mob-collapse__head').forEach(head => {
    head.addEventListener('click', () => toggleCollapse(head));
  });

  /* Bottom Sheet overlay 点击关闭 */
  $('#mob-sheet-overlay').addEventListener('click', function(e) {
    if (e.target === this) closeSheet();
  });

  /* 点击空白关闭 FAB 菜单 */
  document.addEventListener('click', function(e) {
    if (!e.target.closest('#mob-fab') && !e.target.closest('#mob-fab-menu')) {
      closeFabMenu();
    }
  });

  /* 监听类型切换 */
  $('#mob-watch-type')?.addEventListener('change', function() {
    const isForward = this.value === 'forward';
    $('#mob-watch-source-group').style.display = isForward ? 'none' : '';
    $('#mob-watch-target-group').style.display = isForward ? '' : 'none';
    $('#mob-watch-comment-group').style.display = isForward ? '' : 'none';
  });

  /* 新建转存表单提交 */
  $('#mob-transfer-form')?.addEventListener('submit', async function(event) {
    event.preventDefault();
    const form = new FormData(this);
    const payload = Object.fromEntries(form.entries());
    payload.start_id = payload.start_id ? Number(payload.start_id) : null;
    payload.end_id = payload.end_id ? Number(payload.end_id) : null;
    payload.include_comment = !!payload.include_comment;
    try {
      await postJson('/api/tasks', payload);
      showToast(t('form.transferCreated'));
      this.reset();
      $('#collapse-transfer-form').classList.remove('open');
      loadTasks();
    } catch (err) {
      showToast(translateApiError(err, 'form.requestFailed'), false);
    }
  });

  /* 新建监听表单提交 */
  $('#mob-watch-form')?.addEventListener('submit', async function(event) {
    event.preventDefault();
    const form = new FormData(this);
    const payload = Object.fromEntries(form.entries());
    payload.include_comment = !!payload.include_comment;
    if (payload.watch_type !== 'forward') {
      payload.source_links = String(payload.source_links || '')
        .split('\n').map(s => s.trim()).filter(Boolean);
    }
    try {
      await postJson('/api/watches', payload);
      showToast(t('watches.created'));
      this.reset();
      $('#collapse-watch-form').classList.remove('open');
      loadWatches();
    } catch (err) {
      showToast(translateApiError(err, 'form.requestFailed'), false);
    }
  });

  /* 保存设置 */
  $('#mob-save-settings')?.addEventListener('click', async function() {
    const formData = new FormData();
    const pathInputs = document.querySelectorAll('#mob-settings-path-fields input');
    const behaviorInputs = document.querySelectorAll('#mob-settings-behavior-fields input');
    const archiveInputs = document.querySelectorAll('#mob-settings-archive-fields input');

    const userPayload = {};
    const globalPayload = {};

    pathInputs.forEach(input => {
      if (input.type === 'checkbox') userPayload[input.name] = input.checked;
      else if (input.name && input.value) userPayload[input.name] = input.type === 'number' ? Number(input.value) : input.value;
    });

    behaviorInputs.forEach(input => {
      if (input.type === 'checkbox') globalPayload[input.name] = input.checked;
    });

    archiveInputs.forEach(input => {
      if (input.type === 'checkbox') globalPayload[input.name] = input.checked;
      else if (input.name && input.value) globalPayload[input.name] = input.type === 'number' ? Number(input.value) : input.value;
    });

    try {
      await postJson('/api/settings', { user: userPayload, global: globalPayload });
      showToast(t('settings.saved'));
      loadSettings();
    } catch (err) {
      showToast(translateApiError(err, 'form.requestFailed'), false);
    }
  });

  /* ====== 页面可见性变化时触发轮询 ====== */
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && state.taskPollTimer) {
      stopPolling();
      startPolling();
    }
  });

  /* ====== 初始加载 ====== */
  loadTasks();
  startPolling();
'''
```

- [ ] **Step 2: 验证 JS 语法**

```bash
python3 -c "
from module.web_ui_assets import WEB_UI_MOBILE_SCRIPT
print('WEB_UI_MOBILE_SCRIPT length:', len(WEB_UI_MOBILE_SCRIPT))
# 验证包含共享脚本
assert 'SHARED_WEB_UI_SCRIPT' not in WEB_UI_MOBILE_SCRIPT, 'SHARED_WEB_UI_SCRIPT not expanded'
print('OK')
"
```

实际上这里有个问题：`WEB_UI_MOBILE_SCRIPT = SHARED_WEB_UI_SCRIPT + r'''` 会直接在 Python 运行时把字符串拼接好。`WEB_UI_MOBILE_SCRIPT` 是一个完整的 JS 字符串。

- [ ] **Step 3: 提交**

```bash
git add module/web_ui_assets.py
git commit -m "feat: add mobile WebUI JS with navigation and card rendering"
```

---

### Task 6: 组装 `WEB_UI_MOBILE_HTML` 并完成集成

**Files:**
- Modify: `module/web_ui_assets.py` (最末尾新增 `WEB_UI_MOBILE_HTML`)

- [ ] **Step 1: 新增 `WEB_UI_MOBILE_HTML` 变量**

在 `module/web_ui_assets.py` 末尾（`WEB_UI_HTML` 定义之后）新增：

```python
WEB_UI_MOBILE_HTML = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>TRMD 转存控制台</title>
  <style>{WEB_UI_MOBILE_CSS}</style>
</head>
<body>
{WEB_UI_MOBILE_BODY}
  <script>{WEB_UI_MOBILE_SCRIPT}</script>
</body>
</html>'''
```

- [ ] **Step 2: 验证完整模块加载**

```bash
python3 -c "
from module.web_ui_assets import WEB_UI_MOBILE_HTML, WEB_UI_HTML
print('Desktop HTML length:', len(WEB_UI_HTML))
print('Mobile HTML length:', len(WEB_UI_MOBILE_HTML))
print('OK')
"
```

- [ ] **Step 3: 验证 web_ui.py 导入正常**

```bash
python3 -c "
from module.web_ui import WebUiServer
print('WebUiServer imported OK')
"
```

- [ ] **Step 4: 提交**

```bash
git add module/web_ui_assets.py
git commit -m "feat: assemble mobile WebUI HTML and complete integration"
```

---

### Task 7: 端到端验证

**Files:**
- 无新建，验证现有文件

- [ ] **Step 1: 启动 WebUI 并验证桌面版正常工作**

```bash
python3 -c "
from module.web_ui_assets import WEB_UI_HTML
assert '<!doctype html>' in WEB_UI_HTML
assert 'WEB_UI_CSS' not in WEB_UI_HTML  # 确保 CSS 已展开
assert 'WEB_UI_SCRIPT' not in WEB_UI_HTML  # 确保 JS 已展开
assert 'SHARED_WEB_UI_SCRIPT' not in WEB_UI_HTML  # 确保共享脚本已内嵌
print('Desktop HTML: OK')
"
```

- [ ] **Step 2: 验证移动版 HTML 结构完整性**

```bash
python3 -c "
from module.web_ui_assets import WEB_UI_MOBILE_HTML

# 核心结构
assert '<!doctype html>' in WEB_UI_MOBILE_HTML
assert 'user-scalable=no' in WEB_UI_MOBILE_HTML
assert 'mob-view' in WEB_UI_MOBILE_HTML, 'Missing mob-view'

# 7 个视图
for view in ['transfers', 'watches', 'settings', 'channel-downloads', 'uploads', 'statistics', 'records']:
    assert f'mob-view-{view}' in WEB_UI_MOBILE_HTML, f'Missing view: {view}'

# 导航元素
assert 'mob-tabbar' in WEB_UI_MOBILE_HTML, 'Missing tab bar'
assert 'mob-drawer' in WEB_UI_MOBILE_HTML, 'Missing drawer'
assert 'mob-fab' in WEB_UI_MOBILE_HTML, 'Missing FAB'

# 关键 CSS 变量
assert 'env(safe-area-inset-bottom' in WEB_UI_MOBILE_HTML, 'Missing safe area'

# 关键 JS 函数
assert 'mobSwitchView' in WEB_UI_MOBILE_HTML, 'Missing mobSwitchView'
assert 'renderMobTasks' in WEB_UI_MOBILE_HTML, 'Missing renderMobTasks'
assert 'showToast' in WEB_UI_MOBILE_HTML, 'Missing showToast'

print('Mobile HTML: all structural checks passed')
"
```

- [ ] **Step 3: 验证 JS 函数覆盖——确保移动版 JS 包含所需共享函数**

```bash
python3 -c "
from module.web_ui_assets import WEB_UI_MOBILE_SCRIPT

required_functions = [
    'function postJson',
    'function loadTasks',
    'function loadSettings',
    'function loadWatches',
    'function loadRecords',
    'function loadStatistics',
    'function deleteTask',
    'function runTaskAction',
    'function deleteWatch',
    'function t(key)',
    'function esc(value)',
    'function startPolling',
    'function stopPolling',
    'function applyLanguage',
    'function switchView',
    'const state = {',
]

missing = [f for f in required_functions if f not in WEB_UI_MOBILE_SCRIPT]
if missing:
    print('MISSING SHARED FUNCTIONS:')
    for m in missing:
        print(f'  {m}')
else:
    print('Shared JS functions: all present')

assert not missing, f'{len(missing)} shared functions missing'
"
```

- [ ] **Step 4: 统一 lint（如果有）**

```bash
flake8 module/web_ui.py module/web_ui_assets.py --ignore=E501,W503 || echo "No flake8, checking syntax only"
python3 -m py_compile module/web_ui.py
python3 -m py_compile module/web_ui_assets.py
echo "Syntax check: OK"
```

- [ ] **Step 5: 提交**

```bash
git add module/web_ui.py module/web_ui_assets.py
git commit -m "test: add end-to-end validation of mobile WebUI assets"
```

---

### Task 8: Phase 2 — 次要视图补全

**Files:**
- Modify: `module/web_ui_assets.py` (移动版 JS 和 HTML)

- [ ] **Step 1: 频道下载表单**

替换 `mob-view-channel-downloads` 的占位内容为实际表单：

在 `WEB_UI_MOBILE_BODY` 中的 `mob-view-channel-downloads` div 内容改为：

```html
<div class="mob-collapse" id="collapse-channel-form">
  <div class="mob-collapse__head" data-i18n="channel.title">频道下载 <span class="mob-collapse__arrow">▼</span></div>
  <div class="mob-collapse__body">
    <form id="mob-channel-form">
      <label><span data-i18n="channel.link">频道链接</span>
        <input type="text" name="chat_link" placeholder="https://t.me/..." required>
      </label>
      <label><span data-i18n="channel.keywords">关键词</span>
        <input type="text" name="keywords" data-i18n-placeholder="channel.keywordsPlaceholder" placeholder="逗号分隔，可留空">
      </label>
      <button type="submit" style="width:100%;" data-i18n="channel.create">创建频道下载</button>
    </form>
  </div>
</div>
```

在 `WEB_UI_MOBILE_SCRIPT` 末尾添加频道下载表单提交处理。

- [ ] **Step 2: 下载记录列表**

在 `WEB_UI_MOBILE_SCRIPT` 中添加 `renderMobRecords()` 函数，覆盖 `loadRecords()` 渲染行为。

- [ ] **Step 3: 统计页表格式**

在 `mob-view-statistics` 中添加统计表渲染逻辑。

- [ ] **Step 4: 提交**

```bash
git add module/web_ui_assets.py
git commit -m "feat: add channel download, records, statistics to mobile WebUI"
```

---

## 验证清单

完成后逐项确认：

- [ ] 桌面浏览器访问 WebUI → 显示桌面版（侧边栏 + 双栏布局）
- [ ] 手机浏览器访问 WebUI → 显示移动版（底部 Tab + 卡片列表）
- [ ] Chrome DevTools 模拟 iPhone → 显示移动版
- [ ] 移动版底部 Tab 切换正常（转存 / 监听 / 设置 / 更多）
- [ ] "更多"抽屉弹出并关闭正常
- [ ] FAB 菜单展开/收起正常
- [ ] 新建转存折叠面板展开/收起 + 提交
- [ ] 新建监听折叠面板 + 类型切换
- [ ] 设置表单加载 + 保存
- [ ] Toast 操作反馈显示
- [ ] 语言切换正常
- [ ] 刷新按钮正常
- [ ] 任务卡片操作（暂停/恢复/重试/删除）
- [ ] 轮询正常工作
- [ ] safe-area 适配（iPhone 底部无遮挡）
