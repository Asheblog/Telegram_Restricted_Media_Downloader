# coding=UTF-8

from html import escape


def _html_attr(name: str, value: str = None) -> str:
    if value is None:
        return ''
    return f' {name}="{escape(str(value), quote=True)}"'


def panel_head(
        *,
        title_i18n: str,
        title_text: str,
        meta_i18n: str = None,
        meta_text: str = None,
        meta_id: str = None,
        indent: int = 10
) -> str:
    pad = ' ' * indent
    child_pad = ' ' * (indent + 2)
    title = escape(title_text, quote=False)
    head = [
        f'{pad}<div class="panel-head" data-component="panel-head">',
        f'{child_pad}<h3 class="panel-head__title"{_html_attr("data-i18n", title_i18n)}>{title}</h3>'
    ]
    if meta_text is not None or meta_i18n is not None or meta_id is not None:
        meta = escape(meta_text or '', quote=False)
        head.append(
            f'{child_pad}<div class="panel-head__meta"'
            f'{_html_attr("id", meta_id)}'
            f'{_html_attr("data-i18n", meta_i18n)}>{meta}</div>'
        )
    head.append(f'{pad}</div>')
    return '\n'.join(head)


WEB_UI_CSS = r'''
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
    --shadow: 0 18px 42px rgba(31, 48, 38, .08);
    --font-xs: 12px;
    --font-sm: 13px;
    --font-md: 14px;
    --font-lg: 16px;
    --font-xl: 22px;
    --panel-head-min-height: 58px;
    --panel-head-padding-x: 18px;
    --panel-head-gap: 12px;
    --control-height: 42px;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: var(--font-md);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    min-height: 100svh;
  }
  button, input, select, textarea {
    font: inherit;
  }
  button {
    border: 0;
    border-radius: 6px;
    padding: 10px 12px;
    color: #fff;
    background: var(--accent);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: background .18s ease, border-color .18s ease;
    min-height: 38px;
    white-space: nowrap;
    font-size: var(--font-md);
  }
  button:hover { background: var(--accent-strong); }
  button:disabled {
    cursor: not-allowed;
    opacity: .58;
  }
  button:disabled:hover { background: var(--accent); }
  button.secondary {
    color: var(--text);
    background: var(--surface-muted);
    border: 1px solid var(--line);
  }
  button.secondary:hover { background: #e5ebef; }
  button.danger {
    color: var(--danger);
    background: #fff4f2;
    border: 1px solid #f3b5ad;
  }
  button.danger:hover { background: #fbe9e7; }
  button.icon-only {
    width: 38px;
    padding: 0;
  }
  svg { width: 18px; height: 18px; flex: 0 0 auto; }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
  input, select, textarea {
    width: 100%;
    border: 1px solid var(--line);
    background: #fff;
    color: var(--text);
    border-radius: 6px;
    min-height: var(--control-height);
    padding: 10px 11px;
    outline: none;
    transition: border-color .18s ease, box-shadow .18s ease;
  }
  textarea {
    min-height: 86px;
    resize: vertical;
  }
  input:focus, select:focus, textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 4px rgba(15, 143, 114, .12);
  }
  label {
    display: grid;
    gap: 7px;
    color: var(--muted);
    font-size: var(--font-sm);
  }
  .shell {
    min-height: 100svh;
    display: grid;
    grid-template-columns: 260px minmax(0, 1fr);
  }
  aside {
    border-right: 1px solid var(--line);
    background: rgba(255, 255, 255, .86);
    padding: 24px 20px;
    position: sticky;
    top: 0;
    height: 100svh;
    display: flex;
    flex-direction: column;
  }
  main {
    min-width: 0;
    padding: 24px;
    display: grid;
    gap: 18px;
    align-content: start;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
  }
  .mark {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: var(--accent);
    display: grid;
    place-items: center;
    color: #fff;
  }
  .brand h1 { font-size: 18px; margin: 0; letter-spacing: 0; }
  .brand p { margin: 2px 0 0; color: var(--muted); font-size: var(--font-sm); }
  .nav {
    display: grid;
    gap: 8px;
    margin-bottom: 24px;
  }
  .nav button {
    justify-content: flex-start;
    background: transparent;
    border: 1px solid transparent;
    color: var(--muted);
  }
  .nav button:hover,
  .nav button.active {
    color: var(--text);
    background: var(--surface-muted);
    border-color: var(--line);
  }
  .nav-title {
    color: var(--muted);
    font-size: var(--font-xs);
    text-transform: uppercase;
    letter-spacing: .08em;
    margin: 22px 0 8px;
  }
  .metric {
    display: grid;
    grid-template-columns: 1fr auto;
    padding: 9px 0;
    border-bottom: 1px solid var(--line);
    gap: 10px;
    font-size: var(--font-md);
  }
  .metric span { color: var(--muted); }
  .metric strong { font-weight: 650; }
  .hint {
    color: var(--muted);
    font-size: var(--font-sm);
    line-height: 1.5;
    margin: 0;
  }
  .sidebar-footer {
    margin-top: auto;
    padding-top: 16px;
    border-top: 1px solid var(--line);
  }
  .sidebar-footer__link {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--muted);
    text-decoration: none;
    font-size: var(--font-xs);
    transition: color .18s ease;
  }
  .sidebar-footer__link:hover {
    color: var(--accent);
  }
  .sidebar-footer__link:hover .sidebar-footer__icon {
    opacity: 1;
  }
  .sidebar-footer__icon {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    opacity: .65;
    transition: opacity .18s ease;
  }
  .sidebar-footer__author {
    margin: 5px 0 0;
    color: var(--muted);
    font-size: var(--font-xs);
    opacity: .62;
  }
  .sidebar-footer__version {
    display: inline-block;
    margin-top: 6px;
    padding: 2px 7px;
    border-radius: 4px;
    background: var(--surface-muted);
    color: var(--muted);
    font-size: 11px;
    font-weight: 500;
    letter-spacing: .03em;
    border: 1px solid var(--line);
  }
  .topbar {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    animation: rise .35s ease both;
  }
  .topbar h2 {
    font-size: var(--font-xl);
    line-height: 1.2;
    margin: 0 0 6px;
    letter-spacing: 0;
  }
  .topbar p {
    margin: 0;
    color: var(--muted);
    max-width: 760px;
    line-height: 1.5;
    font-size: var(--font-md);
  }
  .top-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 220px;
  }
  .view {
    display: none;
    gap: 18px;
  }
  .view.active { display: grid; }
  .workspace {
    display: grid;
    grid-template-columns: minmax(300px, 390px) minmax(0, 1fr);
    gap: 18px;
    align-items: stretch;
  }
  .operation-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
    align-items: stretch;
  }
  .wide-section { grid-column: 1 / -1; }
  section {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    box-shadow: var(--shadow);
    min-width: 0;
  }
  .operation-grid > section,
  .workspace > section {
    display: flex;
    flex-direction: column;
  }
  .operation-grid > section > form {
    flex: 1;
  }
  .workspace > section > form,
  .workspace > section > .task-list {
    flex: 1;
  }
  .panel-head {
    min-height: var(--panel-head-min-height);
    padding: 12px var(--panel-head-padding-x);
    border-bottom: 1px solid var(--line);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--panel-head-gap);
  }
  .panel-head__title {
    margin: 0;
    font-size: var(--font-lg);
    font-weight: 650;
    line-height: 1.25;
    letter-spacing: 0;
  }
  .panel-head__meta {
    color: var(--muted);
    font-size: var(--font-sm);
    line-height: 1.35;
    text-align: right;
    overflow-wrap: anywhere;
  }
  form {
    padding: 18px;
    display: grid;
    gap: 14px;
  }
  .range, .settings-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .actions {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }
  .operation-grid > section > form > .actions {
    margin-top: auto;
  }
  .form-error, .notice {
    display: none;
    color: var(--danger);
    background: #fbe9e7;
    border: 1px solid #f3b5ad;
    border-radius: 6px;
    padding: 10px 12px;
    font-size: var(--font-sm);
    line-height: 1.45;
  }
  .form-error.ok,
  .notice.ok {
    color: var(--ok);
    background: #e5f5ed;
    border-color: #b9e4ca;
  }
  .notice.is-visible,
  .form-error.is-visible {
    display: block;
  }
  .task-list, .record-list, .watch-list, .statistics-list {
    overflow: auto;
    min-height: 0;
  }
  .task-list {
    min-height: 0;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--font-sm);
  }
  th, td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
  }
  th {
    color: var(--muted);
    font-size: var(--font-xs);
    font-weight: 650;
    text-transform: uppercase;
    letter-spacing: .06em;
    background: #f5f7f8;
    position: sticky;
    top: 0;
  }
  tr[data-task-id] { cursor: pointer; }
  tr[data-task-id]:hover { background: #f8faf9; }
  .mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: var(--font-xs);
    color: var(--muted);
    overflow-wrap: anywhere;
  }
  .tasks-table th:nth-child(1) { width: 70px; }
  .tasks-table th:nth-child(2) { width: 92px; }
  .tasks-table th:nth-child(5) { width: 28%; min-width: 220px; }
  .tasks-table th:nth-child(6) { width: 150px; }
  .task-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 134px;
  }
  .task-actions .icon-only {
    flex: 0 0 38px;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 5px 9px;
    font-size: var(--font-xs);
    font-weight: 650;
    background: var(--surface-muted);
    color: var(--muted);
    white-space: nowrap;
  }
  .badge.success { background: #e5f5ed; color: var(--ok); }
  .badge.failure { background: #fbe9e7; color: var(--danger); }
  .badge.running { background: #e8f2ff; color: #145db2; }
  .badge.pending { background: #fff4df; color: var(--warn); }
  .badge.paused { background: #eef2f7; color: #475569; }
  .badge.skipped { background: #eef2f7; color: #526070; }
  .progress {
    height: 8px;
    width: 100%;
    background: #e7ece8;
    border-radius: 999px;
    overflow: hidden;
    margin-top: 6px;
  }
  .task-progress {
    display: grid;
    gap: 7px;
    min-width: 210px;
  }
  .task-progress__head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
  }
  .task-progress__percent {
    font-weight: 650;
    color: var(--text);
  }
  .task-progress__detail {
    color: var(--muted);
    font-size: var(--font-xs);
    white-space: nowrap;
  }
  .task-progress__failed {
    color: var(--danger);
  }
  .progress div {
    height: 100%;
    width: 0%;
    background: var(--accent);
    transition: width .25s ease;
  }
  .file-progress {
    display: grid;
    gap: 9px;
    padding: 14px 18px 18px;
  }
  .item-tabs {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    padding: 14px 18px 0;
  }
  .item-toolbar {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    padding: 10px 18px 0;
  }
  .item-tab {
    min-height: 44px;
    color: var(--muted);
    background: var(--surface-muted);
    border: 1px solid var(--line);
    padding: 8px 10px;
  }
  .item-tab:hover,
  .item-tab.active {
    color: var(--text);
    background: #fff;
    border-color: var(--accent);
  }
  .item-tab__count {
    min-width: 24px;
    border-radius: 999px;
    padding: 2px 7px;
    background: #fff;
    color: var(--muted);
    font-size: var(--font-xs);
    font-weight: 650;
  }
  .item-tab.active .item-tab__count {
    color: var(--accent-strong);
    background: #e4f5ef;
  }
  .file-row {
    display: grid;
    grid-template-columns: minmax(180px, 1fr) 130px 1fr 1fr;
    gap: 12px;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--line);
  }
  .file-row:last-child { border-bottom: 0; }
.load-more-row { padding: 12px 16px; text-align: center; border-top: 1px solid var(--line); }
.load-more-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 20px; border: 1px solid var(--line); border-radius: 6px;
  background: var(--surface); color: var(--accent); font-size: 13px; cursor: pointer;
  font-family: inherit; transition: all .15s;
}
.load-more-btn:hover { border-color: var(--accent); background: #e6f7f2; }
.load-more-btn:disabled { opacity: .5; cursor: not-allowed; }
  .item-pagination {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    padding: 0 18px 18px;
    color: var(--muted);
    font-size: var(--font-sm);
  }
  .item-page-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .item-page-controls button {
    min-height: 44px;
  }
  .item-page-controls button:disabled {
    cursor: not-allowed;
    opacity: .52;
  }
  .item-page-controls button:disabled:hover {
    background: var(--surface-muted);
  }
  .events {
    max-height: 220px;
    overflow: auto;
    padding: 8px 18px 16px;
  }
  .event {
    display: grid;
    grid-template-columns: 150px 70px 1fr;
    gap: 12px;
    padding: 9px 0;
    border-bottom: 1px solid var(--line);
    font-size: var(--font-sm);
  }
  .event time, .event span { color: var(--muted); }
  .empty {
    padding: 36px 18px;
    color: var(--muted);
    text-align: center;
  }
  .settings-form {
    padding: 0;
    display: block;
  }
  .settings-layout {
    width: min(100%, 1120px);
    margin: 0 auto;
    padding: 18px 18px 96px;
    display: grid;
    gap: 16px;
  }
  .settings-section {
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
    min-width: 0;
  }
  .settings-section__head {
    min-height: 52px;
    padding: 14px 16px 12px;
    border-bottom: 1px solid #edf1f3;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
  }
  .settings-section__title {
    margin: 0;
    color: var(--text);
    font-size: var(--font-lg);
    font-weight: 650;
    line-height: 1.3;
    letter-spacing: 0;
  }
  .settings-section__body {
    padding: 16px;
    display: grid;
    gap: 12px;
  }
  .field-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }
  .field-grid--single {
    grid-template-columns: 1fr;
  }
  .field {
    display: grid;
    gap: 7px;
    align-content: start;
    color: var(--muted);
    font-size: var(--font-sm);
  }
  .field > span {
    min-height: 18px;
    line-height: 1.35;
  }
  .check-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .settings-check-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 10px;
  }
  .settings-check-grid--single {
    grid-template-columns: 1fr;
  }
  .check {
    min-height: 24px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: var(--text);
    cursor: pointer;
  }
  .check input {
    width: 16px;
    height: 16px;
    min-height: 0;
    padding: 0;
    margin: 0;
    flex: 0 0 auto;
  }
  .check span {
    line-height: 1.35;
  }
  .check-card {
    min-height: var(--control-height);
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 10px 12px;
    background: #fff;
    cursor: pointer;
    transition: background .18s ease, border-color .18s ease, box-shadow .18s ease;
  }
  .check-card:hover,
  .check-card:focus-within {
    background: #f8fbfa;
    border-color: #9fcfbe;
    box-shadow: 0 0 0 4px rgba(15, 143, 114, .08);
  }
  .check-card input {
    width: 16px;
    height: 16px;
    flex: 0 0 auto;
  }
  .check-card span {
    line-height: 1.35;
  }
  .settings-actions {
    position: sticky;
    bottom: 0;
    z-index: 5;
    width: min(100%, 1120px);
    margin: 0 auto;
    padding: 12px 18px;
    border-top: 1px solid var(--line);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    background: rgba(255, 255, 255, .94);
    backdrop-filter: blur(10px);
    box-shadow: 0 -10px 24px rgba(15, 23, 42, .06);
  }
  .settings-actions .notice {
    flex: 1 1 260px;
  }
  .settings-actions button {
    min-height: var(--control-height);
  }
  @keyframes rise {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @media (max-width: 1040px) {
    .shell { grid-template-columns: 1fr; }
    aside {
      position: static;
      height: auto;
      border-right: 0;
      border-bottom: 1px solid var(--line);
    }
    main { padding: 18px; }
    .workspace, .operation-grid { grid-template-columns: 1fr; }
    .topbar { flex-direction: column; }
    .top-actions { width: 100%; }
  }
  @media (max-width: 680px) {
    main { padding: 14px; }
    .range, .settings-grid, .field-grid, .check-grid, .settings-check-grid { grid-template-columns: 1fr; }
    .file-row { grid-template-columns: 1fr; }
    .settings-layout { padding: 14px 14px 104px; gap: 14px; }
    .settings-section__head { min-height: auto; align-items: flex-start; flex-direction: column; }
    .settings-actions { align-items: stretch; }
    .settings-actions button { width: 100%; }
    .item-tab { flex: 1 1 calc(50% - 8px); }
    .item-pagination { align-items: stretch; }
    .item-page-controls, .item-page-controls button { width: 100%; }
    .event { grid-template-columns: 1fr; gap: 4px; }
    th, td { padding: 11px 10px; }
  }
'''

WEB_UI_BODY = f'''
  <div class="shell">
    <aside>
      <div class="brand">
        <div class="mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <div>
          <h1>TRMD</h1>
          <p data-i18n="app.subtitle">转存控制台</p>
        </div>
      </div>
      <nav class="nav" aria-label="主导航" data-i18n-aria-label="nav.primary">
        <button type="button" class="active" data-nav="transfers">
          <svg viewBox="0 0 24 24" fill="none"><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span data-i18n="nav.transfers">转存任务</span>
        </button>
        <button type="button" data-nav="watches">
          <svg viewBox="0 0 24 24" fill="none"><path d="M4 12s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 9v3l2 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span data-i18n="nav.watches">实时监听</span>
        </button>
        <button type="button" data-nav="channel-downloads">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 5h14v10H8l-3 3V5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M9 9h6M9 12h4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span data-i18n="nav.channelDownloads">频道下载</span>
        </button>
        <button type="button" data-nav="uploads">
          <svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span data-i18n="nav.uploads">本地上传</span>
        </button>
        <button type="button" data-nav="statistics">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 19V9M12 19V5M19 19v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M4 19h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span data-i18n="nav.statistics">统计</span>
        </button>
        <button type="button" data-nav="settings" data-view="settings">
          <svg viewBox="0 0 24 24" fill="none"><path d="M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5Z" stroke="currentColor" stroke-width="2"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 1.98l.04.04a2 2 0 0 1-2.82 2.82l-.04-.04A1.8 1.8 0 0 0 15 19.4a1.8 1.8 0 0 0-1 .6l-.02.02a2 2 0 0 1-3.96 0L10 20a1.8 1.8 0 0 0-1-.6 1.8 1.8 0 0 0-1.98.36l-.04.04a2 2 0 0 1-2.82-2.82l.04-.04A1.8 1.8 0 0 0 4.6 15a1.8 1.8 0 0 0-.6-1l-.02-.02a2 2 0 0 1 0-3.96L4 10a1.8 1.8 0 0 0 .6-1 1.8 1.8 0 0 0-.36-1.98l-.04-.04a2 2 0 1 1 2.82-2.82l.04.04A1.8 1.8 0 0 0 9 4.6a1.8 1.8 0 0 0 1-.6l.02-.02a2 2 0 0 1 3.96 0L14 4a1.8 1.8 0 0 0 1 .6 1.8 1.8 0 0 0 1.98-.36l.04-.04a2 2 0 1 1 2.82 2.82l-.04.04A1.8 1.8 0 0 0 19.4 9c.24.35.45.69.6 1l.02.02a2 2 0 0 1 0 3.96L20 14c-.15.31-.36.65-.6 1Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span data-i18n="nav.settings">设置</span>
        </button>
        <button type="button" data-nav="records">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 4h14v16H5z" stroke="currentColor" stroke-width="2"/><path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span data-i18n="nav.records">下载记录</span>
        </button>
      </nav>
      <div class="nav-title" data-i18n="side.runtime">运行状态</div>
      <div class="metric"><span data-i18n="side.defaultTarget">默认目标</span><strong>@pikpak_bot</strong></div>
      <div class="metric"><span data-i18n="side.totalTasks">任务总数</span><strong id="metric-total">0</strong></div>
      <div class="metric"><span data-i18n="side.running">运行中</span><strong id="metric-running">0</strong></div>
      <div class="metric"><span data-i18n="side.failed">失败</span><strong id="metric-failed">0</strong></div>
      <div class="sidebar-footer">
        <a class="sidebar-footer__link" href="https://github.com/Asheblog/Telegram_Restricted_Media_Downloader" target="_blank" rel="noopener" title="GitHub">
          <svg class="sidebar-footer__icon" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12Z"/></svg>
          <span>Asheblog/TRMD</span>
        </a>
        <p class="sidebar-footer__author">by Gentlesprite</p>
        <span class="sidebar-footer__version">v0.2.24</span>
      </div>
    </aside>
    <main>
      <div class="topbar">
        <div>
          <h2 data-i18n="hero.title">PikPak 转存队列</h2>
          <p data-i18n="hero.body">创建、监控和配置 Telegram 受限内容转存任务。状态、文件进度、失败事件和下载成功记录会持久化保存。</p>
        </div>
        <div class="top-actions">
          <select id="language-select" aria-label="语言" data-i18n-aria-label="language.label">
            <option value="zh">中文</option>
            <option value="en">English</option>
          </select>
          <button class="secondary" type="button" id="refresh">
            <svg viewBox="0 0 24 24" fill="none"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="action.refresh">刷新</span>
          </button>
        </div>
      </div>

      <div class="view active" id="view-transfers">
        <div class="workspace">
          <section>
{panel_head(title_i18n='new.title', title_text='新建转存', meta_i18n='new.profileNote', meta_text='目标配置', indent=12)}
            <form id="transfer-form">
              <label>
                <span data-i18n="new.source">来源链接</span>
                <input name="source_link" type="url" placeholder="https://t.me/source/123" required>
              </label>
              <label>
                <span data-i18n="new.target">目标</span>
                <input name="target_link" type="url" value="https://t.me/pikpak_bot" required>
              </label>
              <label>
                <span data-i18n="new.targetProfile">目标配置</span>
                <select name="target_profile">
                  <option value="pikpak" data-i18n="profile.pikpak">PikPak 文档转存</option>
                  <option value="generic" data-i18n="profile.generic">通用 Telegram 目标</option>
                </select>
              </label>
              <div class="range">
                <label>
                  <span data-i18n="new.startId">起始 ID</span>
                  <input name="start_id" inputmode="numeric" data-i18n-placeholder="new.optional">
                </label>
                <label>
                  <span data-i18n="new.endId">结束 ID</span>
                  <input name="end_id" inputmode="numeric" data-i18n-placeholder="new.optional">
                </label>
              </div>
              <label class="check"><input id="transfer-include-comment" name="include_comment" type="checkbox"><span data-i18n="new.includeComment">包含评论区</span></label>
              <p class="hint" data-i18n="new.hint">单条消息链接可留空。频道或群链接不填 ID 时会自动探测可访问范围，也可手动指定起止 ID。</p>
              <div class="form-error" id="form-error" role="alert" aria-live="polite"></div>
              <div class="actions">
                <button type="submit">
                  <svg viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                  <span data-i18n="new.create">创建任务</span>
                </button>
              </div>
            </form>
          </section>
          <section>
{panel_head(title_i18n='tasks.title', title_text='转存任务', meta_i18n='tasks.notSynced', meta_text='尚未同步', meta_id='last-sync', indent=12)}
            <div class="task-list">
              <table class="tasks-table">
                <thead>
                  <tr>
                    <th data-i18n="tasks.id">ID</th>
                    <th data-i18n="tasks.status">状态</th>
                    <th data-i18n="tasks.source">来源</th>
                    <th data-i18n="tasks.target">目标</th>
                    <th data-i18n="tasks.progress">进度</th>
                    <th data-i18n="tasks.actions">操作</th>
                  </tr>
                </thead>
                <tbody id="tasks"></tbody>
              </table>
              <div class="empty" id="empty" data-i18n="tasks.empty">还没有转存任务。</div>
            </div>
          </section>
        </div>
        <section>
{panel_head(title_i18n='items.title', title_text='文件进度', meta_i18n='items.selectTask', meta_text='选择一个任务', meta_id='selected-task', indent=10)}
          <div class="item-tabs" role="tablist" aria-label="文件状态分类" data-i18n-aria-label="items.tabsLabel">
            <button class="item-tab active" type="button" role="tab" aria-selected="true" data-item-tab="running">
              <span data-i18n="items.tab.running">进行中</span>
              <span class="item-tab__count" data-item-count="running">0</span>
            </button>
            <button class="item-tab" type="button" role="tab" aria-selected="false" data-item-tab="success">
              <span data-i18n="items.tab.success">已完成</span>
              <span class="item-tab__count" data-item-count="success">0</span>
            </button>
            <button class="item-tab" type="button" role="tab" aria-selected="false" data-item-tab="skipped">
              <span data-i18n="items.tab.skipped">跳过</span>
              <span class="item-tab__count" data-item-count="skipped">0</span>
            </button>
            <button class="item-tab" type="button" role="tab" aria-selected="false" data-item-tab="failure">
              <span data-i18n="items.tab.failure">失败</span>
              <span class="item-tab__count" data-item-count="failure">0</span>
            </button>
          </div>
          <div class="item-toolbar">
            <button class="secondary" type="button" id="retry-selected-failed" disabled>
              <svg viewBox="0 0 24 24" fill="none"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span data-i18n="items.retryFailed">重试当前任务失败项</span>
            </button>
          </div>
          <div class="file-progress" id="items" role="tabpanel"></div>
          <div class="item-pagination" id="items-pagination">
            <div id="items-page-range">0 / 0</div>
            <div class="item-page-controls">
              <button class="secondary" type="button" id="items-page-prev" aria-label="上一页" data-i18n-aria-label="items.page.previous">
                <svg viewBox="0 0 24 24" fill="none"><path d="M15 6l-6 6 6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                <span data-i18n="items.page.previous">上一页</span>
              </button>
              <span id="items-page-summary">1 / 1</span>
              <button class="secondary" type="button" id="items-page-next" aria-label="下一页" data-i18n-aria-label="items.page.next">
                <span data-i18n="items.page.next">下一页</span>
                <svg viewBox="0 0 24 24" fill="none"><path d="M9 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>
          </div>
        </section>
        <section>
{panel_head(title_i18n='events.title', title_text='最近事件', meta_text='0', meta_id='event-count', indent=10)}
          <div class="events" id="events"></div>
        </section>
      </div>

      <div class="view" id="view-settings">
        <section>
{panel_head(title_i18n='settings.title', title_text='设置', meta_i18n='settings.safeNote', meta_text='敏感字段只显示是否已配置', indent=10)}
          <form id="settings-form" class="settings-form">
            <div class="settings-layout">
              <div class="settings-section">
                <div class="settings-section__head">
                  <h3 class="settings-section__title" data-i18n="settings.paths">路径与任务</h3>
                </div>
                <div class="settings-section__body">
                  <div class="field-grid field-grid--single">
                    <label class="field"><span data-i18n="settings.saveDirectory">保存目录</span><input name="user.save_directory"></label>
                    <label class="field"><span data-i18n="settings.tempDirectory">临时目录</span><input name="user.temp_directory"></label>
                    <label class="field"><span data-i18n="settings.sessionDirectory">会话目录</span><input name="user.session_directory"></label>
                  </div>
                  <div class="field-grid">
                    <label class="field"><span data-i18n="settings.maxDownload">最大下载任务</span><input name="user.max_tasks.download" type="number" min="1"></label>
                    <label class="field"><span data-i18n="settings.maxUpload">最大上传任务</span><input name="user.max_tasks.upload" type="number" min="1"></label>
                    <label class="field"><span data-i18n="settings.retryDownload">下载重试</span><input name="user.max_retries.download" type="number" min="0"></label>
                    <label class="field"><span data-i18n="settings.retryUpload">上传重试</span><input name="user.max_retries.upload" type="number" min="0"></label>
                    <label class="field"><span data-i18n="settings.pikpakMaxFileSize">PikPak大小上限(字节)</span><input name="global.target_profiles.pikpak.max_file_size" type="number" min="1"></label>
                  </div>
                </div>
              </div>
              <div class="settings-section">
                <div class="settings-section__head">
                  <h3 class="settings-section__title" data-i18n="settings.behavior">行为</h3>
                </div>
                <div class="settings-section__body">
                  <div class="settings-check-grid">
                    <label class="check-card"><input name="global.notice" type="checkbox"><span data-i18n="settings.notice">机器人通知</span></label>
                    <label class="check-card"><input name="user.is_shutdown" type="checkbox"><span data-i18n="settings.shutdown">退出后关机</span></label>
                    <label class="check-card"><input name="global.upload.download_upload" type="checkbox"><span data-i18n="settings.downloadUpload">受限转发时下载后上传</span></label>
                    <label class="check-card"><input name="global.upload.delete" type="checkbox"><span data-i18n="settings.uploadDelete">上传完成删除本地文件</span></label>
                  </div>
                  <div class="field-grid field-grid--single">
                    <label class="field"><span data-i18n="settings.pendingLimit">下载后上传队列</span><input name="global.upload.pending_limit" type="number" min="1" max="5"></label>
                  </div>
                </div>
              </div>
              <div class="settings-section">
                <div class="settings-section__head">
                  <h3 class="settings-section__title" data-i18n="settings.pikpakArchive">PikPak 归档</h3>
                </div>
                <div class="settings-section__body">
                  <div class="settings-check-grid settings-check-grid--single">
                    <label class="check-card"><input name="global.target_profiles.pikpak.archive.enable" type="checkbox"><span data-i18n="settings.pikpakArchiveEnable">PikPak按来源频道归档</span></label>
                  </div>
                  <div class="field-grid">
                    <label class="field"><span data-i18n="settings.pikpakArchiveRemote">PikPak rclone remote</span><input name="global.target_profiles.pikpak.archive.remote"></label>
                    <label class="field"><span data-i18n="settings.pikpakArchiveSource">PikPak入库目录</span><input name="global.target_profiles.pikpak.archive.source_directory"></label>
                    <label class="field"><span data-i18n="settings.pikpakArchiveRoot">PikPak归档根目录</span><input name="global.target_profiles.pikpak.archive.root_directory"></label>
                    <label class="field"><span data-i18n="settings.pikpakArchivePoll">入库轮询秒数</span><input name="global.target_profiles.pikpak.archive.poll_seconds" type="number" min="0"></label>
                    <label class="field"><span data-i18n="settings.pikpakArchiveInterval">轮询间隔秒数</span><input name="global.target_profiles.pikpak.archive.poll_interval_seconds" type="number" min="0"></label>
                    <label class="field"><span data-i18n="settings.pikpakArchiveWindow">匹配时间窗口秒数</span><input name="global.target_profiles.pikpak.archive.match_window_seconds" type="number" min="0"></label>
                  </div>
                </div>
              </div>
              <div class="settings-section">
                <div class="settings-section__head">
                  <h3 class="settings-section__title" data-i18n="settings.sensitive">账号与代理</h3>
                </div>
                <div class="settings-section__body">
                  <div class="field-grid field-grid--single">
                    <label class="field"><span>API ID</span><input name="user.api_id"></label>
                    <label class="field"><span>API Hash</span><input name="user.api_hash" type="password" data-i18n-placeholder="settings.secretConfigured"></label>
                    <label class="field"><span>Bot Token</span><input name="user.bot_token" type="password" data-i18n-placeholder="settings.secretConfigured"></label>
                    <label class="field"><span data-i18n="settings.proxyPassword">代理密码</span><input name="user.proxy.password" type="password" data-i18n-placeholder="settings.secretConfigured"></label>
                  </div>
                </div>
              </div>
              <div class="settings-section">
                <div class="settings-section__head">
                  <h3 class="settings-section__title" data-i18n="settings.downloadTypes">下载类型</h3>
                </div>
                <div class="settings-section__body">
                  <div class="settings-check-grid" id="download-type-settings"></div>
                </div>
              </div>
              <div class="settings-section">
                <div class="settings-section__head">
                  <h3 class="settings-section__title" data-i18n="settings.forwardTypes">转发类型</h3>
                </div>
                <div class="settings-section__body">
                  <div class="settings-check-grid" id="forward-type-settings"></div>
                </div>
              </div>
              <div class="settings-section">
                <div class="settings-section__head">
                  <h3 class="settings-section__title" data-i18n="settings.exports">导出表格</h3>
                </div>
                <div class="settings-section__body">
                  <div class="settings-check-grid">
                    <label class="check-card"><input name="global.export_table.link" type="checkbox"><span data-i18n="settings.exportLink">链接统计表</span></label>
                    <label class="check-card"><input name="global.export_table.count" type="checkbox"><span data-i18n="settings.exportCount">计数统计表</span></label>
                    <label class="check-card"><input name="global.export_table.upload" type="checkbox"><span data-i18n="settings.exportUpload">上传统计表</span></label>
                  </div>
                </div>
              </div>
            </div>
            <div class="settings-actions">
              <div class="notice" id="settings-notice" role="alert" aria-live="polite"></div>
              <button type="submit">
                <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                <span data-i18n="settings.save">保存设置</span>
              </button>
            </div>
          </form>
        </section>
      </div>

      <div class="view" id="view-watches">
        <div class="operation-grid">
          <section>
{panel_head(title_i18n='watches.downloadTitle', title_text='监听下载', meta_i18n='watches.downloadMeta', meta_text='新消息转存', indent=12)}
            <form id="watch-download-form">
              <label>
                <span data-i18n="watches.sources">来源频道</span>
                <textarea name="source_links" placeholder="https://t.me/source" required></textarea>
              </label>
              <p class="hint" data-i18n="watches.sourcesHint">每行一个 Telegram 频道链接。监听下载会处理新到达的视频和图片。</p>
              <div class="notice" id="watch-download-notice" role="alert" aria-live="polite"></div>
              <div class="actions">
                <button type="submit">
                  <svg viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                  <span data-i18n="watches.createDownload">新增监听下载</span>
                </button>
              </div>
            </form>
          </section>
          <section>
{panel_head(title_i18n='watches.forwardTitle', title_text='监听转发', meta_i18n='watches.forwardMeta', meta_text='新消息转发', indent=12)}
            <form id="watch-forward-form">
              <label>
                <span data-i18n="watches.source">来源频道</span>
                <input name="source_link" type="url" placeholder="https://t.me/source" required>
              </label>
              <label>
                <span data-i18n="watches.target">目标频道</span>
                <input name="target_link" type="url" placeholder="https://t.me/target" required>
              </label>
              <label class="check"><input id="watch-forward-include-comment" name="include_comment" type="checkbox"><span data-i18n="watches.includeComment">包含评论区</span></label>
              <p class="hint" data-i18n="watches.forwardHint">同一来源不能同时存在监听下载和监听转发。</p>
              <div class="notice" id="watch-forward-notice" role="alert" aria-live="polite"></div>
              <div class="actions">
                <button type="submit">
                  <svg viewBox="0 0 24 24" fill="none"><path d="M5 12h13M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  <span data-i18n="watches.createForward">新增监听转发</span>
                </button>
              </div>
            </form>
          </section>
          <section class="wide-section">
{panel_head(title_i18n='watches.title', title_text='当前实时监听', meta_text='0', meta_id='watch-count', indent=12)}
            <div class="watch-list">
              <table>
                <thead>
                  <tr>
                    <th data-i18n="watches.type">类型</th>
                    <th data-i18n="tasks.status">状态</th>
                    <th data-i18n="watches.source">来源频道</th>
                    <th data-i18n="watches.target">目标频道</th>
                    <th data-i18n="tasks.actions">操作</th>
                  </tr>
                </thead>
                <tbody id="watches"></tbody>
              </table>
              <div class="empty" id="watches-empty" data-i18n="watches.empty">还没有实时监听。</div>
            </div>
          </section>
        </div>
      </div>

      <div class="view" id="view-channel-downloads">
        <section>
{panel_head(title_i18n='channel.title', title_text='频道下载', meta_i18n='channel.meta', meta_text='筛选后创建下载', indent=10)}
          <form id="channel-download-form">
            <label>
              <span data-i18n="channel.link">频道链接</span>
              <input name="chat_link" type="url" placeholder="https://t.me/source" required>
            </label>
            <div class="range">
              <label>
                <span data-i18n="channel.startDate">起始时间</span>
                <input name="start_date" type="datetime-local">
              </label>
              <label>
                <span data-i18n="channel.endDate">结束时间</span>
                <input name="end_date" type="datetime-local">
              </label>
            </div>
            <div>
              <h3 data-i18n="channel.types">下载类型</h3>
              <div class="check-grid" id="channel-download-types">
                <label class="check"><input type="checkbox" name="download_type" value="video" checked><span>video</span></label>
                <label class="check"><input type="checkbox" name="download_type" value="photo" checked><span>photo</span></label>
                <label class="check"><input type="checkbox" name="download_type" value="audio" checked><span>audio</span></label>
                <label class="check"><input type="checkbox" name="download_type" value="voice" checked><span>voice</span></label>
                <label class="check"><input type="checkbox" name="download_type" value="animation" checked><span>animation</span></label>
                <label class="check"><input type="checkbox" name="download_type" value="document" checked><span>document</span></label>
                <label class="check"><input type="checkbox" name="download_type" value="video_note" checked><span>video_note</span></label>
              </div>
            </div>
            <label>
              <span data-i18n="channel.keywords">关键词</span>
              <input name="keywords" data-i18n-placeholder="channel.keywordsPlaceholder">
            </label>
            <label class="check"><input name="include_comment" type="checkbox"><span data-i18n="channel.includeComment">包含评论区</span></label>
            <p class="hint" data-i18n="channel.hint">频道下载会检索匹配消息并创建下载任务，执行时间取决于频道历史消息数量。</p>
            <div class="notice" id="channel-download-notice" role="alert" aria-live="polite"></div>
            <div class="actions">
              <button type="submit">
                <svg viewBox="0 0 24 24" fill="none"><path d="M12 5v10M8 11l4 4 4-4M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                <span data-i18n="channel.create">创建频道下载</span>
              </button>
            </div>
          </form>
        </section>
      </div>

      <div class="view" id="view-uploads">
        <section>
{panel_head(title_i18n='uploads.title', title_text='本地上传', meta_i18n='uploads.meta', meta_text='服务器路径', indent=10)}
          <form id="upload-form">
            <label>
              <span data-i18n="uploads.path">本地路径</span>
              <input name="path" required>
            </label>
            <label>
              <span data-i18n="uploads.target">目标频道</span>
              <input name="target_link" placeholder="https://t.me/target" required>
            </label>
            <label class="check"><input name="recursive" type="checkbox"><span data-i18n="uploads.recursive">递归上传文件夹</span></label>
            <p class="hint" data-i18n="uploads.serverPathHint">路径位于运行 TRMD 的服务器或容器，不是当前浏览器所在电脑。关闭递归时，文件夹只上传第一层文件；开启递归时包含子文件夹。</p>
            <div class="notice" id="upload-notice" role="alert" aria-live="polite"></div>
            <div class="actions">
              <button type="submit">
                <svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                <span data-i18n="uploads.create">创建上传</span>
              </button>
            </div>
          </form>
        </section>
      </div>

      <div class="view" id="view-statistics">
        <section>
{panel_head(title_i18n='statistics.title', title_text='统计与导出', meta_i18n='statistics.meta', meta_text='运行态数据', indent=10)}
          <div class="statistics-list">
            <table>
              <thead>
                <tr>
                  <th data-i18n="statistics.table">表格</th>
                  <th data-i18n="statistics.available">可用</th>
                  <th data-i18n="statistics.rows">数量</th>
                  <th data-i18n="tasks.actions">操作</th>
                </tr>
              </thead>
              <tbody id="statistics"></tbody>
            </table>
            <div class="notice" id="statistics-notice" role="alert" aria-live="polite"></div>
          </div>
        </section>
      </div>

      <div class="view" id="view-records">
        <section>
{panel_head(title_i18n='records.title', title_text='下载成功记录', meta_text='0', meta_id='record-count', indent=10)}
          <div class="record-list">
            <table>
              <thead>
                <tr>
                  <th data-i18n="records.chat">频道 ID</th>
                  <th data-i18n="records.message">消息 ID</th>
                  <th data-i18n="records.file">文件</th>
                  <th data-i18n="records.size">大小</th>
                  <th data-i18n="records.updated">更新时间</th>
                </tr>
              </thead>
              <tbody id="records"></tbody>
            </table>
            <div class="empty" id="records-empty" data-i18n="records.empty">还没有下载成功记录。</div>
          </div>
        </section>
      </div>
    </main>
  </div>
'''

WEB_UI_SCRIPT = r'''
  const i18n = {
    zh: {
      'app.subtitle': '转存控制台',
      'app.title': 'TRMD 转存控制台',
      'nav.transfers': '转存任务',
      'nav.watches': '实时监听',
      'nav.channelDownloads': '频道下载',
      'nav.uploads': '本地上传',
      'nav.statistics': '统计',
      'nav.settings': '设置',
      'nav.records': '下载记录',
      'nav.primary': '主导航',
      'side.runtime': '运行状态',
      'side.defaultTarget': '默认目标',
      'side.totalTasks': '任务总数',
      'side.running': '运行中',
      'side.failed': '失败',
      'hero.title': 'PikPak 转存队列',
      'hero.body': '创建、监控和配置 Telegram 受限内容转存任务。状态、文件进度、失败事件和下载成功记录会持久化保存。',
      'action.refresh': '刷新',
      'language.label': '语言',
      'new.title': '新建转存',
      'new.profileNote': '目标配置',
      'new.source': '来源链接',
      'new.target': '目标',
      'new.targetProfile': '目标配置',
      'profile.pikpak': 'PikPak 文档转存',
      'profile.generic': '通用 Telegram 目标',
      'new.startId': '起始 ID',
      'new.endId': '结束 ID',
      'new.optional': '可选',
      'new.includeComment': '包含评论区',
      'new.hint': '单条消息链接可留空。频道或群链接不填 ID 时会自动探测可访问范围，也可手动指定起止 ID。',
      'new.create': '创建任务',
      'watches.title': '当前实时监听',
      'watches.downloadTitle': '监听下载',
      'watches.downloadMeta': '新消息转存',
      'watches.forwardTitle': '监听转发',
      'watches.forwardMeta': '新消息转发',
      'watches.sources': '来源频道',
      'watches.sourcesHint': '每行一个 Telegram 频道链接。监听下载会处理新到达的视频和图片。',
      'watches.source': '来源频道',
      'watches.target': '目标频道',
      'watches.includeComment': '包含评论区',
      'watches.forwardHint': '同一来源不能同时存在监听下载和监听转发。',
      'watches.createDownload': '新增监听下载',
      'watches.createForward': '新增监听转发',
      'watches.type': '类型',
      'watches.empty': '还没有实时监听。',
      'watches.delete': '移除监听',
      'watches.download': '监听下载',
      'watches.forward': '监听转发',
      'watches.created': '实时监听已接收。',
      'watches.deleted': '实时监听已移除。',
      'channel.title': '频道下载',
      'channel.meta': '筛选后创建下载',
      'channel.link': '频道链接',
      'channel.startDate': '起始时间',
      'channel.endDate': '结束时间',
      'channel.types': '下载类型',
      'channel.keywords': '关键词',
      'channel.keywordsPlaceholder': '逗号分隔，可留空',
      'channel.includeComment': '包含评论区',
      'channel.hint': '频道下载会检索匹配消息并创建下载任务，执行时间取决于频道历史消息数量。',
      'channel.create': '创建频道下载',
      'channel.accepted': '频道下载已接收。',
      'uploads.title': '本地上传',
      'uploads.meta': '服务器路径',
      'uploads.path': '本地路径',
      'uploads.target': '目标频道',
      'uploads.recursive': '递归上传文件夹',
      'uploads.serverPathHint': '路径位于运行 TRMD 的服务器或容器，不是当前浏览器所在电脑。关闭递归时，文件夹只上传第一层文件；开启递归时包含子文件夹。',
      'uploads.create': '创建上传',
      'uploads.accepted': '上传任务已接收。',
      'statistics.title': '统计与导出',
      'statistics.meta': '运行态数据',
      'statistics.table': '表格',
      'statistics.available': '可用',
      'statistics.rows': '数量',
      'statistics.yes': '是',
      'statistics.no': '否',
      'statistics.link': '链接统计表',
      'statistics.count': '计数统计表',
      'statistics.upload': '上传统计表',
      'statistics.exportLink': '导出链接统计表',
      'statistics.exportCount': '导出计数统计表',
      'statistics.exportUpload': '导出上传统计表',
      'statistics.exported': '统计表已导出到：{directory}',
      'tasks.title': '转存任务',
      'tasks.notSynced': '尚未同步',
      'tasks.id': 'ID',
      'tasks.status': '状态',
      'tasks.source': '来源',
      'tasks.target': '目标',
      'tasks.progress': '进度',
      'tasks.actions': '操作',
      'tasks.pause': '暂停',
      'tasks.resume': '继续',
      'tasks.retryFailed': '重试失败',
      'tasks.delete': '删除',
      'tasks.empty': '还没有转存任务。',
      'items.title': '文件进度',
      'items.selectTask': '选择一个任务',
      'items.empty': '该任务还没有文件记录。',
      'items.tabsLabel': '文件状态分类',
      'items.tab.running': '进行中',
      'items.tab.success': '已完成',
      'items.tab.skipped': '跳过',
      'items.tab.failure': '失败',
      'items.empty.running': '当前没有进行中的文件。',
      'items.empty.success': '当前没有已完成的文件。',
      'items.empty.skipped': '当前没有跳过的文件。',
      'items.empty.failure': '当前没有失败的文件。',
      'items.retryFailed': '重试当前任务失败项',
      'items.page.previous': '上一页',
      'items.page.next': '下一页',
      'items.page.status': '第 {page} / {pages} 页',
      'items.page.range': '{start}-{end} / {total}',
      'items.download': '下载',
      'items.upload': '上传',
      'items.loadMore': '加载更多文件',
      'items.remaining': '条剩余',
      'events.title': '最近事件',
      'events.empty': '没有事件记录。',
      'events.loadMore': '加载更多事件',
      'events.remaining': '条剩余',
      'settings.title': '设置',
      'settings.safeNote': '敏感字段只显示是否已配置',
      'settings.paths': '路径与任务',
      'settings.saveDirectory': '保存目录',
      'settings.tempDirectory': '临时目录',
      'settings.sessionDirectory': '会话目录',
      'settings.maxDownload': '最大下载任务',
      'settings.maxUpload': '最大上传任务',
      'settings.retryDownload': '下载重试',
      'settings.retryUpload': '上传重试',
      'settings.pikpakMaxFileSize': 'PikPak大小上限(字节)',
      'settings.pikpakArchive': 'PikPak 归档',
      'settings.pikpakArchiveEnable': 'PikPak按来源频道归档',
      'settings.pikpakArchiveRemote': 'PikPak rclone remote',
      'settings.pikpakArchiveSource': 'PikPak入库目录',
      'settings.pikpakArchiveRoot': 'PikPak归档根目录',
      'settings.pikpakArchivePoll': '入库轮询秒数',
      'settings.pikpakArchiveInterval': '轮询间隔秒数',
      'settings.pikpakArchiveWindow': '匹配时间窗口秒数',
      'settings.behavior': '行为',
      'settings.notice': '机器人通知',
      'settings.shutdown': '退出后关机',
      'settings.downloadUpload': '受限转发时下载后上传',
      'settings.uploadDelete': '上传完成删除本地文件',
      'settings.pendingLimit': '下载后上传队列',
      'settings.sensitive': '账号与代理',
      'settings.proxyPassword': '代理密码',
      'settings.secretConfigured': '已配置，如需更换请填写',
      'settings.secretNotConfigured': '未配置',
      'settings.downloadTypes': '下载类型',
      'settings.forwardTypes': '转发类型',
      'settings.exports': '导出表格',
      'settings.exportLink': '链接统计表',
      'settings.exportCount': '计数统计表',
      'settings.exportUpload': '上传统计表',
      'settings.save': '保存设置',
      'settings.saved': '设置已保存。',
      'records.title': '下载成功记录',
      'records.chat': '频道 ID',
      'records.message': '消息 ID',
      'records.file': '文件',
      'records.size': '大小',
      'records.updated': '更新时间',
      'records.empty': '还没有下载成功记录。',
      'form.createFailed': '创建任务失败。',
      'form.requestFailed': '请求失败。',
      'form.creatingTransfer': '正在分析来源消息范围，Telegram 限流时可能需要等待。请保持页面打开。',
      'form.creatingTransferShort': '正在分析',
      'form.createSuccess': '任务已创建并开始排队。可以关闭页面，也可以继续查看进度。',
      'error.auth_required': '需要登录。',
      'error.invalid_task_id': '任务 ID 无效。',
      'error.task_not_found': '找不到任务。',
      'error.not_found': '找不到请求的资源。',
      'error.source_link_required': '请填写来源链接。',
      'error.target_link_required': '请填写目标链接。',
      'error.range_ids_required': '起始 ID 和结束 ID 必须同时填写。',
      'error.range_end_before_start': '结束 ID 必须大于或等于起始 ID。',
      'error.range_source_must_be_chat_link': '范围转存的来源必须是频道链接，不能是单条消息链接。',
      'error.transfer_range_detection_unavailable': '当前运行模式无法自动探测消息范围。',
      'error.transfer_range_detection_failed': '自动探测消息范围失败。',
      'error.transfer_range_empty': '来源中没有可访问的消息。',
      'error.create_task_failed': '创建任务失败。',
      'error.update_settings_failed': '更新设置失败。',
      'error.watch_source_conflict': '同一来源不能同时存在监听下载和监听转发。',
      'error.watch_already_exists': '实时监听已存在。',
      'error.watch_source_required': '请填写监听来源。',
      'error.watch_target_required': '请填写监听目标。',
      'error.invalid_payload': '请求内容无效。',
      'error.invalid_watch_type': '实时监听类型无效。',
      'error.invalid_watch_source': '监听来源必须以 https://t.me/ 开头。',
      'error.invalid_watch_target': '监听目标必须以 https://t.me/ 开头。',
      'error.watch_operations_unavailable': '实时监听操作不可用。',
      'error.upload_path_not_found': '服务器或容器中找不到该路径。',
      'error.upload_path_required': '请填写上传路径。',
      'error.upload_target_required': '请填写上传目标。',
      'error.upload_recursive_requires_directory': '递归上传需要选择文件夹路径。',
      'error.invalid_upload_target': '上传目标必须是 Telegram 链接、me 或 self。',
      'error.upload_operations_unavailable': '上传操作不可用。',
      'error.invalid_table_type': '统计表类型无效。',
      'error.table_operations_unavailable': '统计表操作不可用。',
      'error.invalid_channel_link': '频道链接必须以 https://t.me/ 开头。',
      'error.channel_link_required': '请填写频道链接。',
      'error.channel_download_type_required': '请至少选择一种下载类型。',
      'error.invalid_channel_download_type': '频道下载类型无效。',
      'error.channel_download_operations_unavailable': '频道下载操作不可用。',
      'action.taskUpdated': '任务操作已提交。',
      'error.invalid_date_range': '时间范围格式无效。',
      'error.date_range_end_before_start': '结束时间必须大于或等于起始时间。',
      'event.level.info': '信息',
      'event.level.warning': '警告',
      'event.level.error': '错误',
      'event.fileReady': '文件已准备上传到目标：{name}',
      'event.sentToTarget': '已发送到目标：{name}',
      'event.uploadFailed': '上传失败：{reason}',
      'event.reusedDownload': '已复用下载成功记录：{name}',
      'event.directForward': '已直接发送到目标：{link}',
      'event.rangeAssigned': '范围转存已分配：{range}',
      'event.rangeAssignedWithFallback': '范围转存已分配：{range}，回退下载 {count} 条。',
      'event.singleAssigned': '单条消息转存已分配。',
      'event.singleAssignedWithFallback': '单条消息转存已分配，回退下载 {count} 条。',
      'status.pending': '等待',
      'status.running': '运行中',
      'status.paused': '已暂停',
      'status.success': '成功',
      'status.failure': '失败',
      'status.skipped': '跳过'
    },
    en: {
      'app.subtitle': 'Transfer Console',
      'app.title': 'TRMD Transfer Console',
      'nav.transfers': 'Transfer tasks',
      'nav.watches': 'Live watches',
      'nav.channelDownloads': 'Channel downloads',
      'nav.uploads': 'Local uploads',
      'nav.statistics': 'Statistics',
      'nav.settings': 'Settings',
      'nav.records': 'Download records',
      'nav.primary': 'Primary navigation',
      'side.runtime': 'Runtime',
      'side.defaultTarget': 'Default target',
      'side.totalTasks': 'Total tasks',
      'side.running': 'Running',
      'side.failed': 'Failed',
      'hero.title': 'PikPak transfer queue',
      'hero.body': 'Create, monitor, and configure Telegram restricted content transfer tasks. State, file progress, failure events, and download success records are persisted.',
      'action.refresh': 'Refresh',
      'language.label': 'Language',
      'new.title': 'New transfer',
      'new.profileNote': 'Target profile',
      'new.source': 'Source link',
      'new.target': 'Target',
      'new.targetProfile': 'Target profile',
      'profile.pikpak': 'PikPak document transfer',
      'profile.generic': 'Generic Telegram target',
      'new.startId': 'Start ID',
      'new.endId': 'End ID',
      'new.optional': 'Optional',
      'new.includeComment': 'Include discussion replies',
      'new.hint': 'Leave the range empty for a message link. For a channel or group link, empty IDs auto-detect the accessible range, or you can set start and end IDs manually.',
      'new.create': 'Create task',
      'watches.title': 'Current live watches',
      'watches.downloadTitle': 'Download watch',
      'watches.downloadMeta': 'Transfer new messages',
      'watches.forwardTitle': 'Forward watch',
      'watches.forwardMeta': 'Forward new messages',
      'watches.sources': 'Source channels',
      'watches.sourcesHint': 'One Telegram channel link per line. Download watches handle new video and photo messages.',
      'watches.source': 'Source channel',
      'watches.target': 'Target channel',
      'watches.includeComment': 'Include discussion replies',
      'watches.forwardHint': 'The same source cannot have a download watch and a forward watch at the same time.',
      'watches.createDownload': 'Add download watch',
      'watches.createForward': 'Add forward watch',
      'watches.type': 'Type',
      'watches.empty': 'No live watches yet.',
      'watches.delete': 'Remove watch',
      'watches.download': 'Download watch',
      'watches.forward': 'Forward watch',
      'watches.created': 'Live watch accepted.',
      'watches.deleted': 'Live watch removed.',
      'channel.title': 'Channel download',
      'channel.meta': 'Create downloads after filtering',
      'channel.link': 'Channel link',
      'channel.startDate': 'Start time',
      'channel.endDate': 'End time',
      'channel.types': 'Download types',
      'channel.keywords': 'Keywords',
      'channel.keywordsPlaceholder': 'Comma-separated, optional',
      'channel.includeComment': 'Include discussion replies',
      'channel.hint': 'Channel download scans matching messages and creates download tasks. Runtime depends on channel history size.',
      'channel.create': 'Create channel download',
      'channel.accepted': 'Channel download accepted.',
      'uploads.title': 'Local upload',
      'uploads.meta': 'Server path',
      'uploads.path': 'Local path',
      'uploads.target': 'Target channel',
      'uploads.recursive': 'Upload folder recursively',
      'uploads.serverPathHint': 'The path is on the server or container running TRMD, not on this browser device. With recursion off, a folder uploads only its top-level files; with recursion on, subfolders are included.',
      'uploads.create': 'Create upload',
      'uploads.accepted': 'Upload request accepted.',
      'statistics.title': 'Statistics and export',
      'statistics.meta': 'Runtime data',
      'statistics.table': 'Table',
      'statistics.available': 'Available',
      'statistics.rows': 'Rows',
      'statistics.yes': 'Yes',
      'statistics.no': 'No',
      'statistics.link': 'Link table',
      'statistics.count': 'Count table',
      'statistics.upload': 'Upload table',
      'statistics.exportLink': 'Export link table',
      'statistics.exportCount': 'Export count table',
      'statistics.exportUpload': 'Export upload table',
      'statistics.exported': 'Table exported to: {directory}',
      'tasks.title': 'Transfer tasks',
      'tasks.notSynced': 'Not synced',
      'tasks.id': 'ID',
      'tasks.status': 'Status',
      'tasks.source': 'Source',
      'tasks.target': 'Target',
      'tasks.progress': 'Progress',
      'tasks.actions': 'Actions',
      'tasks.pause': 'Pause',
      'tasks.resume': 'Resume',
      'tasks.retryFailed': 'Retry failed',
      'tasks.delete': 'Delete',
      'tasks.empty': 'No transfer tasks yet.',
      'items.title': 'File progress',
      'items.selectTask': 'Select a task',
      'items.empty': 'No file records for this task yet.',
      'items.tabsLabel': 'File status categories',
      'items.tab.running': 'Running',
      'items.tab.success': 'Completed',
      'items.tab.skipped': 'Skipped',
      'items.tab.failure': 'Failed',
      'items.empty.running': 'No running files in this task.',
      'items.empty.success': 'No completed files in this task.',
      'items.empty.skipped': 'No skipped files in this task.',
      'items.empty.failure': 'No failed files in this task.',
      'items.retryFailed': 'Retry failed items in this task',
      'items.page.previous': 'Previous',
      'items.page.next': 'Next',
      'items.page.status': 'Page {page} / {pages}',
      'items.page.range': '{start}-{end} / {total}',
      'items.download': 'Download',
      'items.upload': 'Upload',
      'items.loadMore': 'Load more files',
      'items.remaining': 'remaining',
      'events.title': 'Latest events',
      'events.empty': 'No events recorded.',
      'events.loadMore': 'Load more events',
      'events.remaining': 'remaining',
      'settings.title': 'Settings',
      'settings.safeNote': 'Sensitive fields only show configured state',
      'settings.paths': 'Paths and tasks',
      'settings.saveDirectory': 'Save directory',
      'settings.tempDirectory': 'Temp directory',
      'settings.sessionDirectory': 'Session directory',
      'settings.maxDownload': 'Max download tasks',
      'settings.maxUpload': 'Max upload tasks',
      'settings.retryDownload': 'Download retries',
      'settings.retryUpload': 'Upload retries',
      'settings.pikpakMaxFileSize': 'PikPak size limit (bytes)',
      'settings.pikpakArchive': 'PikPak archive',
      'settings.pikpakArchiveEnable': 'Archive PikPak by source channel',
      'settings.pikpakArchiveRemote': 'PikPak rclone remote',
      'settings.pikpakArchiveSource': 'PikPak source folder',
      'settings.pikpakArchiveRoot': 'PikPak archive root',
      'settings.pikpakArchivePoll': 'Ingest poll seconds',
      'settings.pikpakArchiveInterval': 'Poll interval seconds',
      'settings.pikpakArchiveWindow': 'Match window seconds',
      'settings.behavior': 'Behavior',
      'settings.notice': 'Bot notifications',
      'settings.shutdown': 'Shutdown after exit',
      'settings.downloadUpload': 'Download then upload restricted forwards',
      'settings.uploadDelete': 'Delete local file after upload',
      'settings.pendingLimit': 'Upload-after-download queue',
      'settings.sensitive': 'Account and proxy',
      'settings.proxyPassword': 'Proxy password',
      'settings.secretConfigured': 'Configured; enter a new value to replace',
      'settings.secretNotConfigured': 'Not configured',
      'settings.downloadTypes': 'Download types',
      'settings.forwardTypes': 'Forward types',
      'settings.exports': 'Table exports',
      'settings.exportLink': 'Link table',
      'settings.exportCount': 'Count table',
      'settings.exportUpload': 'Upload table',
      'settings.save': 'Save settings',
      'settings.saved': 'Settings saved.',
      'records.title': 'Download success records',
      'records.chat': 'Channel ID',
      'records.message': 'Message ID',
      'records.file': 'File',
      'records.size': 'Size',
      'records.updated': 'Updated',
      'records.empty': 'No download success records yet.',
      'form.createFailed': 'Create task failed.',
      'form.requestFailed': 'Request failed.',
      'form.creatingTransfer': 'Analyzing the source message range. Telegram flood waits can take a while; keep this page open.',
      'form.creatingTransferShort': 'Analyzing',
      'form.createSuccess': 'Task created and queued. You can close this page or keep watching progress.',
      'error.auth_required': 'Authentication required.',
      'error.invalid_task_id': 'Invalid task ID.',
      'error.task_not_found': 'Task not found.',
      'error.not_found': 'Resource not found.',
      'error.source_link_required': 'Source link is required.',
      'error.target_link_required': 'Target link is required.',
      'error.range_ids_required': 'Start ID and End ID must be provided together.',
      'error.range_end_before_start': 'End ID must be greater than or equal to Start ID.',
      'error.range_source_must_be_chat_link': 'Range transfer source must be a chat link, not a message link.',
      'error.transfer_range_detection_unavailable': 'Automatic message range detection is unavailable in this runtime.',
      'error.transfer_range_detection_failed': 'Automatic message range detection failed.',
      'error.transfer_range_empty': 'No accessible messages were found for the source.',
      'error.create_task_failed': 'Create task failed.',
      'error.update_settings_failed': 'Update settings failed.',
      'error.watch_source_conflict': 'The same source cannot have a download watch and a forward watch at the same time.',
      'error.watch_already_exists': 'Live watch already exists.',
      'error.watch_source_required': 'Watch source is required.',
      'error.watch_target_required': 'Watch target is required.',
      'error.invalid_payload': 'Invalid request payload.',
      'error.invalid_watch_type': 'Invalid live watch type.',
      'error.invalid_watch_source': 'Watch source must start with https://t.me/.',
      'error.invalid_watch_target': 'Watch target must start with https://t.me/.',
      'error.watch_operations_unavailable': 'Live watch operations are unavailable.',
      'error.upload_path_not_found': 'Path not found on the server or container.',
      'error.upload_path_required': 'Upload path is required.',
      'error.upload_target_required': 'Upload target is required.',
      'error.upload_recursive_requires_directory': 'Recursive upload requires a folder path.',
      'error.invalid_upload_target': 'Upload target must be a Telegram link, me, or self.',
      'error.upload_operations_unavailable': 'Upload operations are unavailable.',
      'error.invalid_table_type': 'Invalid table type.',
      'error.table_operations_unavailable': 'Table operations are unavailable.',
      'error.invalid_channel_link': 'Channel link must start with https://t.me/.',
      'error.channel_link_required': 'Channel link is required.',
      'error.channel_download_type_required': 'Select at least one download type.',
      'error.invalid_channel_download_type': 'Invalid channel download type.',
      'error.channel_download_operations_unavailable': 'Channel download operations are unavailable.',
      'error.invalid_date_range': 'Invalid date range.',
      'error.date_range_end_before_start': 'End time must be greater than or equal to start time.',
      'action.taskUpdated': 'Task action submitted.',
      'event.level.info': 'info',
      'event.level.warning': 'warning',
      'event.level.error': 'error',
      'event.fileReady': 'File ready for target upload: {name}',
      'event.sentToTarget': 'Sent to target: {name}',
      'event.uploadFailed': 'Upload failed: {reason}',
      'event.reusedDownload': 'Reused download success record: {name}',
      'event.directForward': 'Directly sent to target: {link}',
      'event.rangeAssigned': 'Range transfer assigned: {range}',
      'event.rangeAssignedWithFallback': 'Range transfer assigned: {range}; fallback downloads: {count}.',
      'event.singleAssigned': 'Single-message transfer assigned.',
      'event.singleAssignedWithFallback': 'Single-message transfer assigned; fallback downloads: {count}.',
      'status.pending': 'pending',
      'status.running': 'running',
      'status.paused': 'paused',
      'status.success': 'success',
      'status.failure': 'failure',
      'status.skipped': 'skipped'
    }
  };

  const state = {
    lang: localStorage.getItem('trmd-lang') || 'zh',
    selectedTaskId: null,
    settings: null,
    schema: null,
    tasks: [],
    items: [],
    events: [],
    records: [],
    watches: [],
    statistics: null,
    lastSync: null,
    activeItemStatus: 'running',
    itemPages: {
      running: 1,
      success: 1,
      skipped: 1,
      failure: 1
    },
    itemsTotal: 0,
    eventsTotal: 0,
    itemsOffset: 0,
    eventsOffset: 0,
    hasMoreItems: false,
    hasMoreEvents: false,
    taskPollTimer: null,
    loadingDetail: false
  };

  const $ = selector => document.querySelector(selector);
  const $$ = selector => Array.from(document.querySelectorAll(selector));
  const ITEMS_PAGE_SIZE = 10;
  const ITEM_STATUS_TABS = ['running', 'success', 'skipped', 'failure'];

  function t(key) {
    return (i18n[state.lang] && i18n[state.lang][key]) || i18n.zh[key] || key;
  }

  function interpolate(template, values) {
    return String(template).replace(/\{(\w+)}/g, (_, key) => values[key] ?? '');
  }

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  function pct(current, total) {
    current = Number(current || 0);
    total = Number(total || 0);
    return total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  }

  function formatBytes(value) {
    value = Number(value || 0);
    const units = ['B', 'KiB', 'MiB', 'GiB'];
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value = value / 1024;
      unit += 1;
    }
    return `${value.toFixed(unit ? 1 : 0)} ${units[unit]}`;
  }

  function translateApiError(payload, fallbackKey = 'form.requestFailed') {
    if (payload && payload.error_code) {
      const key = `error.${payload.error_code}`;
      const message = t(key);
      return message === key ? (payload.error || t(fallbackKey)) : message;
    }
    return (payload && payload.error) || t(fallbackKey);
  }

  function showNotice(selector, message, ok = true) {
    const notice = $(selector);
    if (!notice) return;
    notice.textContent = message;
    notice.classList.toggle('ok', ok);
    notice.classList.add('is-visible');
  }

  function showFormMessage(message, ok = true) {
    const formNotice = $('#form-error');
    formNotice.textContent = message;
    formNotice.classList.toggle('ok', ok);
    formNotice.classList.add('is-visible');
  }

  async function withLoading(button, task) {
    const previous = button ? button.disabled : false;
    if (button) button.disabled = true;
    try {
      return await task();
    } finally {
      if (button) button.disabled = previous;
    }
  }

  async function postJson(path, payload) {
    const res = await fetch(path, {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  function localizeEventMessage(event) {
    const message = String((event && event.message) || '');
    let match = message.match(/^File ready for target upload: (.+)$/);
    if (match) return interpolate(t('event.fileReady'), {name: match[1]});
    match = message.match(/^Sent to target: (.+)$/);
    if (match) return interpolate(t('event.sentToTarget'), {name: match[1]});
    match = message.match(/^Upload failed: (.+)$/);
    if (match) return interpolate(t('event.uploadFailed'), {reason: match[1]});
    match = message.match(/^Reused download success record: (.+)$/);
    if (match) return interpolate(t('event.reusedDownload'), {name: match[1]});
    match = message.match(/^Direct forward succeeded: (.+)$/);
    if (match) return interpolate(t('event.directForward'), {link: match[1]});
    match = message.match(/^Range transfer assigned: (.+)\. Fallback downloads: (\d+)\.$/);
    if (match) return interpolate(t('event.rangeAssignedWithFallback'), {range: match[1], count: match[2]});
    match = message.match(/^Range transfer assigned: (.+)\.$/);
    if (match) return interpolate(t('event.rangeAssigned'), {range: match[1]});
    match = message.match(/^Single-message transfer assigned\. Fallback downloads: (\d+)\.$/);
    if (match) return interpolate(t('event.singleAssignedWithFallback'), {count: match[1]});
    if (message === 'Single-message transfer assigned.') return t('event.singleAssigned');
    return message;
  }

  function localizeEventLevel(level) {
    const key = `event.level.${level}`;
    const translated = t(key);
    return translated === key ? level : translated;
  }

  function applyLanguage() {
    document.documentElement.lang = state.lang === 'zh' ? 'zh-CN' : 'en';
    document.title = t('app.title');
    $('#language-select').value = state.lang;
    $$('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
    $$('[data-i18n-placeholder]').forEach(el => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    $$('[data-i18n-aria-label]').forEach(el => {
      el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel));
    });
    $$('[data-i18n-title]').forEach(el => {
      el.setAttribute('title', t(el.dataset.i18nTitle));
    });
  }

  function refreshVisibleDynamicText() {
    renderTasks();
    $('#selected-task').textContent = state.selectedTaskId ? `#${state.selectedTaskId}` : t('items.selectTask');
    renderItems(state.items);
    renderEvents(state.events);
    renderRecords();
    if (state.settings) fillSettingsForm();
  }

  function applyLanguageAndRefresh() {
    applyLanguage();
    refreshVisibleDynamicText();
  }

  function switchView(view) {
    $$('.view').forEach(el => el.classList.toggle('active', el.id === `view-${view}`));
    $$('[data-nav]').forEach(el => el.classList.toggle('active', el.dataset.nav === view));
    if (view === 'settings') loadSettings();
    if (view === 'records') loadRecords();
    if (view === 'watches') loadWatches();
    if (view === 'statistics') loadStatistics();
  }

  function badge(status) {
    return `<span class="badge ${esc(status)}">${esc(t(`status.${status}`))}</span>`;
  }

  function taskProgress(task) {
    const total = Number(task.total_items || 0);
    const done = Number(task.completed_items || 0);
    const failed = Number(task.failed_items || 0);
    const percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
    const progressLabel = `${percent}% · ${done}/${total}${failed ? ` · ${failed} ${t('side.failed')}` : ''}`;
    return `
      <div class="task-progress" aria-label="${esc(progressLabel)}">
        <div class="task-progress__head">
          <span class="task-progress__percent">${percent}%</span>
          <span class="task-progress__detail">
            ${done}/${total}${failed ? ` <span class="task-progress__failed">${failed} ${esc(t('side.failed'))}</span>` : ''}
          </span>
        </div>
        <div class="progress" title="${esc(progressLabel)}"><div style="width:${percent}%"></div></div>
      </div>
    `;
  }

  function renderTasks() {
    const tasks = state.tasks || [];
    $('#metric-total').textContent = tasks.length;
    $('#metric-running').textContent = tasks.filter(task => task.status === 'running').length;
    $('#metric-failed').textContent = tasks.filter(task => task.status === 'failure').length;
    if (state.lastSync) $('#last-sync').textContent = state.lastSync;
    $('#empty').style.display = tasks.length ? 'none' : 'block';
    $('#tasks').innerHTML = tasks.map(task => `
      <tr data-task-id="${task.id}">
        <td class="mono">#${task.id}</td>
        <td>${badge(task.status)}</td>
        <td class="mono">${esc(task.source_link)}</td>
        <td class="mono">${esc(task.target_link)}</td>
        <td>${taskProgress(task)}</td>
        <td>
          <div class="task-actions">
            <button class="secondary icon-only" type="button" title="${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}" aria-label="${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}" onclick="${task.status === 'paused' ? `resumeTask(event, ${task.id})` : `pauseTask(event, ${task.id})`}">
              ${task.status === 'paused'
                ? '<svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14l11-7L8 5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14M16 5v14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'}
              <span class="sr-only">${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}</span>
            </button>
            <button class="secondary icon-only" type="button" title="${esc(t('tasks.retryFailed'))}" aria-label="${esc(t('tasks.retryFailed'))}" onclick="retryFailedTask(event, ${task.id})" ${Number(task.failed_items || 0) ? '' : 'disabled'}>
              <svg viewBox="0 0 24 24" fill="none"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 8v4l3 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
              <span class="sr-only">${esc(t('tasks.retryFailed'))}</span>
            </button>
            <button class="danger icon-only" type="button" title="${esc(t('tasks.delete'))}" aria-label="${esc(t('tasks.delete'))}" onclick="deleteTask(event, ${task.id})">
              <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span class="sr-only" data-i18n="tasks.delete">${esc(t('tasks.delete'))}</span>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
    $$('tr[data-task-id]').forEach(row => {
      row.addEventListener('click', () => loadTask(row.dataset.taskId));
    });
  }

  async function loadTasks() {
    const res = await fetch('/api/tasks');
    const data = await res.json();
    state.tasks = data.tasks || [];
    state.lastSync = new Date().toLocaleTimeString();
    renderTasks();
    if (!state.selectedTaskId && state.tasks[0]) {
      await loadTaskDetail(state.tasks[0].id, true);
    } else if (state.selectedTaskId) {
      await loadTaskSummary(state.selectedTaskId);
    } else {
      state.items = [];
      state.events = [];
      state.itemsTotal = 0;
      state.eventsTotal = 0;
      $('#selected-task').textContent = t('items.selectTask');
      renderItems();
      renderEvents();
    }
  }

  async function loadTaskSummary(id) {
    const taskId = Number(id);
    const res = await fetch(`/api/tasks/${taskId}/summary`);
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.task) {
      state.selectedTaskId = taskId;
      state.itemsTotal = data.item_count || 0;
      state.eventsTotal = data.event_count || 0;
      // 更新侧边栏和标题中的任务状态
      updateTaskSummaryDisplay(data.task);
    }
  }

  function updateTaskSummaryDisplay(task) {
    $('#selected-task').textContent = `#${task.id}`;
    renderEventCount();
  }

  async function loadTaskDetail(id, keepExistingItems) {
    const taskId = Number(id);
    if (state.selectedTaskId !== taskId) {
      resetItemPages();
      state.items = [];
      state.events = [];
      state.itemsOffset = 0;
      state.eventsOffset = 0;
      state.hasMoreItems = false;
      state.hasMoreEvents = false;
    }
    state.selectedTaskId = taskId;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=200&items_offset=0&events_limit=100&events_offset=0`);
      if (!res.ok) {
        state.selectedTaskId = null;
        state.items = [];
        state.events = [];
        $('#selected-task').textContent = t('items.selectTask');
        renderItems();
        renderEvents();
        return;
      }
      const data = await res.json();
      $('#selected-task').textContent = `#${taskId}`;
      state.items = data.items || [];
      state.events = data.events || [];
      state.itemsTotal = data.item_count || 0;
      state.eventsTotal = data.event_count || 0;
      state.itemsOffset = data.items_offset || 0;
      state.eventsOffset = data.events_offset || 0;
      state.hasMoreItems = data.has_more_items || false;
      state.hasMoreEvents = data.has_more_events || false;
      renderItems();
      renderEvents();
    } finally {
      state.loadingDetail = false;
    }
  }

  async function loadMoreItems() {
    if (state.loadingDetail) return;
    const taskId = state.selectedTaskId;
    if (!taskId) return;
    const offset = state.itemsOffset + 200;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=200&items_offset=${offset}&events_limit=0&events_offset=0`);
      if (!res.ok) return;
      const data = await res.json();
      state.items = state.items.concat(data.items || []);
      state.itemsTotal = data.item_count || state.itemsTotal;
      state.itemsOffset = offset;
      state.hasMoreItems = data.has_more_items || false;
      renderItems();
    } finally {
      state.loadingDetail = false;
    }
  }

  async function loadMoreEvents() {
    if (state.loadingDetail) return;
    const taskId = state.selectedTaskId;
    if (!taskId) return;
    const offset = state.eventsOffset + 100;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=0&items_offset=0&events_limit=100&events_offset=${offset}`);
      if (!res.ok) return;
      const data = await res.json();
      state.events = state.events.concat(data.events || []);
      state.eventsTotal = data.event_count || state.eventsTotal;
      state.eventsOffset = offset;
      state.hasMoreEvents = data.has_more_events || false;
      renderEvents();
    } finally {
      state.loadingDetail = false;
    }
  }

  // 保留 loadTask 作为点击任务时的入口
  async function loadTask(id) {
    await loadTaskDetail(id, false);
  }

  function progressLine(label, current, total) {
    const percent = pct(current, total);
    return `<div><div>${esc(label)} ${percent}%</div><div class="progress"><div style="width:${percent}%"></div></div><div class="mono">${formatBytes(current)} / ${formatBytes(total)}</div></div>`;
  }

  function itemStatusGroup(item) {
    const status = String((item && item.status) || 'pending');
    if (status === 'success' || status === 'skipped' || status === 'failure') return status;
    if (['pending', 'running'].includes(status)) return 'running';
    return 'running';
  }

  function categorizedItems(items) {
    const groups = {
      running: [],
      success: [],
      skipped: [],
      failure: []
    };
    (items || []).forEach(item => {
      groups[itemStatusGroup(item)].push(item);
    });
    return groups;
  }

  function itemPageState(total) {
    const pages = Math.max(1, Math.ceil(total / ITEMS_PAGE_SIZE));
    const current = Math.min(Math.max(Number(state.itemPages[state.activeItemStatus] || 1), 1), pages);
    state.itemPages[state.activeItemStatus] = current;
    const startIndex = (current - 1) * ITEMS_PAGE_SIZE;
    const endIndex = Math.min(startIndex + ITEMS_PAGE_SIZE, total);
    return {current, pages, startIndex, endIndex};
  }

  function renderItemTabs(groups) {
    ITEM_STATUS_TABS.forEach(status => {
      const tab = $(`[data-item-tab="${status}"]`);
      const count = $(`[data-item-count="${status}"]`);
      if (!tab || !count) return;
      const active = state.activeItemStatus === status;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      count.textContent = groups[status].length;
    });
  }

  function renderItems(items) {
    items = items || state.items;
    const groups = categorizedItems(items);
    const activeItems = groups[state.activeItemStatus] || [];
    const page = itemPageState(activeItems.length);
    const visibleItems = activeItems.slice(page.startIndex, page.endIndex);
    renderItemTabs(groups);
    const retryButton = $('#retry-selected-failed');
    if (retryButton) {
      retryButton.disabled = !(state.selectedTaskId && groups.failure.length);
      retryButton.style.display = state.activeItemStatus === 'failure' ? 'inline-flex' : 'none';
    }
    const loadMoreHtml = state.hasMoreItems
      ? `<div class="load-more-row"><button type="button" class="load-more-btn" onclick="loadMoreItems()">
          ${esc(t('items.loadMore'))} (${state.itemsTotal - items.length} ${esc(t('items.remaining'))})
        </button></div>`
      : '';
    $('#items').innerHTML = (visibleItems.length ? visibleItems.map(item => `
      <div class="file-row">
        <div>
          <div>${esc(item.file_name || item.local_path || item.source_link || `#${item.source_message_id || item.id}`)}</div>
          <div class="mono">${esc(item.source_chat_id || '')} ${esc(item.source_message_id || '')}</div>
        </div>
        <div>${badge(item.status)}</div>
        ${progressLine(t('items.download'), item.download_current, item.download_total)}
        ${progressLine(t('items.upload'), item.upload_current, item.upload_total)}
      </div>
    `).join('') : `<div class="empty">${esc(t(`items.empty.${state.activeItemStatus}`))}</div>`) + loadMoreHtml;

    const range = activeItems.length
      ? interpolate(t('items.page.range'), {
        start: page.startIndex + 1,
        end: page.endIndex,
        total: activeItems.length
      })
      : interpolate(t('items.page.range'), {start: 0, end: 0, total: 0});
    $('#items-page-range').textContent = range;
    $('#items-page-summary').textContent = interpolate(t('items.page.status'), {
      page: page.current,
      pages: page.pages
    });
    $('#items-page-prev').disabled = page.current <= 1;
    $('#items-page-next').disabled = page.current >= page.pages;
  }

  function resetItemPages() {
    ITEM_STATUS_TABS.forEach(status => {
      state.itemPages[status] = 1;
    });
  }

  function switchItemTab(status) {
    if (!ITEM_STATUS_TABS.includes(status)) return;
    state.activeItemStatus = status;
    renderItems(state.items);
  }

  function renderEvents() {
    const events = state.events || [];
    const countText = state.eventsTotal > events.length
      ? `${events.length} / ${state.eventsTotal}`
      : String(events.length);
    $('#event-count').textContent = countText;
    const loadMoreHtml = state.hasMoreEvents
      ? `<div class="load-more-row"><button type="button" class="load-more-btn" onclick="loadMoreEvents()">
          ${esc(t('events.loadMore'))} (${state.eventsTotal - events.length} ${esc(t('events.remaining'))})
        </button></div>`
      : '';
    $('#events').innerHTML = (events.length ? events.map(event => `
      <div class="event">
        <time>${esc(event.created_at)}</time>
        <span>${esc(localizeEventLevel(event.level))}</span>
        <div>${esc(localizeEventMessage(event))}</div>
      </div>
    `).join('') : `<div class="empty">${esc(t('events.empty'))}</div>`) + loadMoreHtml;
  }

  function renderEventCount() {
    if (state.events && state.events.length) {
      const countText = state.eventsTotal > state.events.length
        ? `${state.events.length} / ${state.eventsTotal}`
        : String(state.events.length);
      $('#event-count').textContent = countText;
    }
  }

  async function loadWatches() {
    const res = await fetch('/api/watches');
    const data = await res.json();
    state.watches = data.watches || [];
    renderWatches();
  }

  async function refreshWatchesAfterMutation() {
    try {
      await loadWatches();
    } catch (error) {
      console.warn('Failed to refresh watches after mutation.', error);
    }
  }

  function renderWatches() {
    const watches = state.watches || [];
    $('#watch-count').textContent = watches.length;
    $('#watches-empty').style.display = watches.length ? 'none' : 'block';
    $('#watches').innerHTML = watches.map(watch => `
      <tr>
        <td>${esc(t(`watches.${watch.type}`))}</td>
        <td>${badge(watch.status || 'running')}</td>
        <td class="mono">${esc(watch.source_link || '')}</td>
        <td class="mono">${esc(watch.target_link || '')}${watch.include_comment ? `<div>${esc(t('watches.includeComment'))}</div>` : ''}${watch.error_message ? `<div>${esc(watch.error_message)}</div>` : ''}</td>
        <td>
          <button class="danger" type="button" onclick="deleteWatch('${encodeURIComponent(watch.id)}')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="watches.delete">${esc(t('watches.delete'))}</span>
          </button>
        </td>
      </tr>
    `).join('');
  }

  async function deleteWatch(encodedId) {
    if (!window.confirm(t('watches.delete'))) return;
    const res = await fetch(`/api/watches/${encodedId}`, {method: 'DELETE'});
    const data = await res.json();
    if (!res.ok) {
      showNotice('#watch-download-notice', translateApiError(data), false);
      return;
    }
    showNotice('#watch-download-notice', t('watches.deleted'), true);
    await loadWatches();
  }
  window.deleteWatch = deleteWatch;

  async function loadStatistics() {
    const res = await fetch('/api/statistics');
    const data = await res.json();
    state.statistics = data;
    renderStatistics();
  }

  function renderStatistics() {
    const tables = (state.statistics && state.statistics.tables) || {};
    const rows = ['link', 'count', 'upload'];
    $('#statistics').innerHTML = rows.map(type => {
      const table = tables[type] || {};
      const exportKey = type === 'link' ? 'statistics.exportLink' : type === 'count' ? 'statistics.exportCount' : 'statistics.exportUpload';
      return `
        <tr>
          <td>${esc(t(`statistics.${type}`))}</td>
          <td>${esc(table.available ? t('statistics.yes') : t('statistics.no'))}</td>
          <td class="mono">${esc(table.rows || 0)}</td>
          <td>
            <button type="button" onclick="exportTable('${type}')">
              <svg viewBox="0 0 24 24" fill="none"><path d="M12 5v10M8 11l4 4 4-4M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span>${esc(t(exportKey))}</span>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }

  async function exportTable(tableType) {
    try {
      const data = await postJson('/api/tables/export', {table_type: tableType});
      showNotice('#statistics-notice', interpolate(t('statistics.exported'), {directory: data.directory || ''}), true);
      await loadStatistics();
    } catch (payload) {
      showNotice('#statistics-notice', translateApiError(payload), false);
    }
  }
  window.exportTable = exportTable;

  async function postTaskAction(taskId, action) {
    const res = await fetch(`/api/tasks/${taskId}/${action}`, {method: 'POST'});
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  async function runTaskAction(event, taskId, action) {
    event.stopPropagation();
    const button = event.currentTarget;
    await withLoading(button, async () => {
      try {
        await postTaskAction(taskId, action);
        showFormMessage(t('action.taskUpdated'), true);
        await loadTasks();
      } catch (payload) {
        showFormMessage(translateApiError(payload), false);
      }
    });
  }

  function pauseTask(event, taskId) {
    return runTaskAction(event, taskId, 'pause');
  }
  window.pauseTask = pauseTask;

  function resumeTask(event, taskId) {
    return runTaskAction(event, taskId, 'resume');
  }
  window.resumeTask = resumeTask;

  function retryFailedTask(event, taskId) {
    return runTaskAction(event, taskId, 'retry-failed');
  }
  window.retryFailedTask = retryFailedTask;

  async function deleteTask(event, taskId) {
    event.stopPropagation();
    const res = await fetch(`/api/tasks/${taskId}`, {method: 'DELETE'});
    if (res.ok && state.selectedTaskId === taskId) {
      state.selectedTaskId = null;
      state.items = [];
      state.events = [];
      resetItemPages();
      $('#selected-task').textContent = t('items.selectTask');
      renderItems();
      renderEvents();
    }
    await loadTasks();
  }
  window.deleteTask = deleteTask;

  function getPath(obj, path) {
    return path.split('.').reduce((cur, key) => cur && cur[key], obj);
  }

  function setPath(obj, path, value) {
    const parts = path.split('.');
    let cur = obj;
    parts.slice(0, -1).forEach(key => {
      cur[key] = cur[key] || {};
      cur = cur[key];
    });
    cur[parts[parts.length - 1]] = value;
  }

  async function loadSettings() {
    const res = await fetch('/api/settings');
    const data = await res.json();
    state.settings = data.settings || {};
    state.schema = data.schema || {};
    renderTypeSettings();
    fillSettingsForm();
  }

  function renderTypeSettings() {
    const downloadTypes = state.schema.download_type || [];
    const forwardTypes = state.schema.forward_type || [];
    $('#download-type-settings').innerHTML = downloadTypes.map(type => `
      <label class="check-card"><input name="user.download_type" value="${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
    `).join('');
    $('#forward-type-settings').innerHTML = forwardTypes.map(type => `
      <label class="check-card"><input name="global.forward_type.${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
    `).join('');
  }

  function fillSettingsForm() {
    const form = $('#settings-form');
    Array.from(form.elements).forEach(el => {
      if (!el.name) return;
      if (el.name === 'user.download_type') {
        el.checked = (getPath(state.settings, 'user.download_type') || []).includes(el.value);
        return;
      }
      const value = getPath(state.settings, el.name);
      if (el.type === 'checkbox') {
        el.checked = Boolean(value);
      } else if (value && typeof value === 'object' && 'configured' in value) {
        el.placeholder = value.configured ? t('settings.secretConfigured') : t('settings.secretNotConfigured');
        el.value = '';
      } else {
        el.value = value ?? '';
      }
    });
  }

  function settingsPayload() {
    const payload = {};
    const downloadTypes = [];
    Array.from($('#settings-form').elements).forEach(el => {
      if (!el.name) return;
      if (el.name === 'user.download_type') {
        if (el.checked) downloadTypes.push(el.value);
        return;
      }
      let value = el.type === 'checkbox' ? el.checked : el.value;
      if (el.type === 'number') value = value === '' ? null : Number(value);
      if (el.type === 'password' && value === '') return;
      setPath(payload, el.name, value);
    });
    setPath(payload, 'user.download_type', downloadTypes);
    return payload;
  }

  async function saveSettings(event) {
    event.preventDefault();
    const res = await fetch('/api/settings', {
      method: 'PATCH',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(settingsPayload())
    });
    const data = await res.json();
    const notice = $('#settings-notice');
    notice.style.display = 'block';
    notice.classList.toggle('ok', res.ok);
    notice.textContent = res.ok ? t('settings.saved') : translateApiError(data, 'error.update_settings_failed');
    if (res.ok) {
      state.settings = data.settings || {};
      state.schema = data.schema || state.schema;
      fillSettingsForm();
    }
  }

  async function createDownloadWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const sourceLinks = new FormData(event.currentTarget)
        .get('source_links')
        .split(/\r?\n/)
        .map(value => value.trim())
        .filter(Boolean);
      try {
        await postJson('/api/watches', {type: 'download', source_links: sourceLinks});
      } catch (payload) {
        showNotice('#watch-download-notice', translateApiError(payload), false);
        return;
      }
      showNotice('#watch-download-notice', t('watches.created'), true);
      event.currentTarget.reset();
      await refreshWatchesAfterMutation();
    });
  }

  async function createForwardWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      try {
        await postJson('/api/watches', {
          type: 'forward',
          source_link: form.get('source_link'),
          target_link: form.get('target_link'),
          include_comment: Boolean(form.get('include_comment'))
        });
      } catch (payload) {
        showNotice('#watch-forward-notice', translateApiError(payload), false);
        return;
      }
      showNotice('#watch-forward-notice', t('watches.created'), true);
      event.currentTarget.reset();
      await refreshWatchesAfterMutation();
    });
  }

  async function createChannelDownload(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      const downloadType = Array.from(event.currentTarget.querySelectorAll('input[name="download_type"]:checked')).map(el => el.value);
      const keywords = String(form.get('keywords') || '').split(',').map(value => value.trim()).filter(Boolean);
      try {
        await postJson('/api/channel-downloads', {
          chat_link: form.get('chat_link'),
          date_range: {
            start_date: form.get('start_date') || null,
            end_date: form.get('end_date') || null
          },
          download_type: downloadType,
          keywords,
          include_comment: Boolean(form.get('include_comment'))
        });
        showNotice('#channel-download-notice', t('channel.accepted'), true);
      } catch (payload) {
        showNotice('#channel-download-notice', translateApiError(payload), false);
      }
    });
  }

  async function createUpload(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      try {
        await postJson('/api/uploads', {
          path: form.get('path'),
          target_link: form.get('target_link'),
          recursive: Boolean(form.get('recursive'))
        });
        showNotice('#upload-notice', t('uploads.accepted'), true);
      } catch (payload) {
        showNotice('#upload-notice', translateApiError(payload), false);
      }
    });
  }

  async function loadRecords() {
    const res = await fetch('/api/download-records');
    const data = await res.json();
    state.records = data.records || [];
    renderRecords();
  }

  function renderRecords() {
    const records = state.records || [];
    $('#record-count').textContent = records.length;
    $('#records-empty').style.display = records.length ? 'none' : 'block';
    $('#records').innerHTML = records.map(record => `
      <tr>
        <td class="mono">${esc(record.source_chat_id)}</td>
        <td class="mono">${esc(record.source_message_id)}</td>
        <td><div>${esc(record.file_name || '')}</div><div class="mono">${esc(record.local_path || '')}</div></td>
        <td>${formatBytes(record.file_size)}</td>
        <td class="mono">${esc(record.updated_at || record.downloaded_at)}</td>
      </tr>
    `).join('');
  }

  $('#language-select').addEventListener('change', event => {
    state.lang = event.target.value;
    localStorage.setItem('trmd-lang', state.lang);
    applyLanguageAndRefresh();
  });
  $$('[data-nav]').forEach(button => button.addEventListener('click', () => switchView(button.dataset.nav)));
  $$('[data-item-tab]').forEach(button => button.addEventListener('click', () => switchItemTab(button.dataset.itemTab)));
  $('#items-page-prev').addEventListener('click', () => {
    state.itemPages[state.activeItemStatus] = Number(state.itemPages[state.activeItemStatus] || 1) - 1;
    renderItems();
  });
  $('#items-page-next').addEventListener('click', () => {
    state.itemPages[state.activeItemStatus] = Number(state.itemPages[state.activeItemStatus] || 1) + 1;
    renderItems();
  });
  $('#retry-selected-failed').addEventListener('click', event => {
    if (!state.selectedTaskId) return;
    retryFailedTask(event, state.selectedTaskId);
  });
  $('#refresh').addEventListener('click', () => {
    loadTasks();
    if ($('#view-records').classList.contains('active')) loadRecords();
    if ($('#view-settings').classList.contains('active')) loadSettings();
    if ($('#view-watches').classList.contains('active')) loadWatches();
    if ($('#view-statistics').classList.contains('active')) loadStatistics();
  });
  $('#transfer-form').addEventListener('submit', async event => {
    event.preventDefault();
    const submitButton = event.submitter;
    const submitLabel = submitButton ? submitButton.querySelector('span') : null;
    const previousLabel = submitLabel ? submitLabel.textContent : '';
    if (submitButton) submitButton.disabled = true;
    if (submitLabel) submitLabel.textContent = t('form.creatingTransferShort');
    showFormMessage(t('form.creatingTransfer'), true);
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    payload.start_id = payload.start_id ? Number(payload.start_id) : null;
    payload.end_id = payload.end_id ? Number(payload.end_id) : null;
    payload.include_comment = Boolean(form.get('include_comment'));
    try {
      const res = await fetch('/api/tasks', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        showFormMessage(translateApiError(data, 'form.createFailed'), false);
        return;
      }
      showFormMessage(t('form.createSuccess'), true);
      state.selectedTaskId = data.task_id;
      await loadTasks();
    } catch (_error) {
      showFormMessage(t('form.requestFailed'), false);
    } finally {
      if (submitButton) submitButton.disabled = false;
      if (submitLabel) submitLabel.textContent = previousLabel;
    }
  });
  $('#settings-form').addEventListener('submit', saveSettings);
  $('#watch-download-form').addEventListener('submit', createDownloadWatch);
  $('#watch-forward-form').addEventListener('submit', createForwardWatch);
  $('#channel-download-form').addEventListener('submit', createChannelDownload);
  $('#upload-form').addEventListener('submit', createUpload);

  applyLanguage();
  loadTasks();
  startPolling();

  function hasActiveTasks() {
    return state.tasks.some(t => t.status === 'pending' || t.status === 'running');
  }

  function isSelectedTaskTerminal() {
    const task = state.tasks.find(t => t.id === state.selectedTaskId);
    return task && (task.status === 'success' || task.status === 'failure');
  }

  function startPolling() {
    if (state.taskPollTimer) return;
    const fastInterval = 3000;
    const slowInterval = 15000;
    let currentInterval = fastInterval;
    let lastPollTime = 0;

    async function poll() {
      if (document.hidden) {
        // 页面不可见时不做轮询
        scheduleNext(currentInterval);
        return;
      }
      const now = Date.now();
      const minGap = currentInterval - 500;
      if (now - lastPollTime < minGap) {
        scheduleNext(currentInterval);
        return;
      }
      lastPollTime = now;
      try {
        await loadTasks();
      } catch (e) {
        console.warn('Poll failed:', e);
      }
      // 根据是否有活跃任务动态调整轮询间隔
      currentInterval = hasActiveTasks() ? fastInterval : slowInterval;
      scheduleNext(currentInterval);
    }

    function scheduleNext(interval) {
      state.taskPollTimer = setTimeout(poll, interval);
    }

    poll();
  }

  function stopPolling() {
    if (state.taskPollTimer) {
      clearTimeout(state.taskPollTimer);
      state.taskPollTimer = null;
    }
  }

  // 页面可见性变化时立即触发一次轮询
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && state.taskPollTimer) {
      stopPolling();
      startPolling();
    }
  });
'''

WEB_UI_HTML = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TRMD 转存控制台</title>
  <style>{WEB_UI_CSS}</style>
</head>
<body>
{WEB_UI_BODY}
  <script>{WEB_UI_SCRIPT}</script>
</body>
</html>'''
