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
    --panel-head-min-height: 60px;
    --panel-head-padding-x: 18px;
    --panel-head-gap: 12px;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    min-height: 100svh;
  }
  button, input, select {
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
  }
  button:hover { background: var(--accent-strong); }
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
  input, select {
    width: 100%;
    border: 1px solid var(--line);
    background: #fff;
    color: var(--text);
    border-radius: 6px;
    padding: 10px 11px;
    outline: none;
    transition: border-color .18s ease, box-shadow .18s ease;
  }
  input:focus, select:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 4px rgba(15, 143, 114, .12);
  }
  label {
    display: grid;
    gap: 7px;
    color: var(--muted);
    font-size: 13px;
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
  .brand p { margin: 2px 0 0; color: var(--muted); font-size: 13px; }
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
    font-size: 12px;
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
    font-size: 14px;
  }
  .metric span { color: var(--muted); }
  .metric strong { font-weight: 650; }
  .hint {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.5;
    margin: 0;
  }
  .topbar {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    animation: rise .35s ease both;
  }
  .topbar h2 {
    font-size: clamp(26px, 3vw, 42px);
    line-height: 1.05;
    margin: 0 0 8px;
    letter-spacing: 0;
  }
  .topbar p {
    margin: 0;
    color: var(--muted);
    max-width: 760px;
    line-height: 1.5;
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
    align-items: start;
  }
  section {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    box-shadow: var(--shadow);
    min-width: 0;
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
    font-size: 15px;
    font-weight: 650;
    line-height: 1.25;
    letter-spacing: 0;
  }
  .panel-head__meta {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.35;
    text-align: right;
    overflow-wrap: anywhere;
  }
  form, .settings-form {
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
  .form-error, .notice {
    display: none;
    color: var(--danger);
    background: #fbe9e7;
    border: 1px solid #f3b5ad;
    border-radius: 6px;
    padding: 10px 12px;
    font-size: 13px;
    line-height: 1.45;
  }
  .notice.ok {
    color: var(--ok);
    background: #e5f5ed;
    border-color: #b9e4ca;
  }
  .task-list, .record-list {
    overflow: auto;
    min-height: 360px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  th, td {
    padding: 13px 14px;
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
  }
  th {
    color: var(--muted);
    font-size: 12px;
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
    font-size: 12px;
    color: var(--muted);
    overflow-wrap: anywhere;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 5px 9px;
    font-size: 12px;
    font-weight: 650;
    background: var(--surface-muted);
    color: var(--muted);
    white-space: nowrap;
  }
  .badge.success { background: #e5f5ed; color: var(--ok); }
  .badge.failure { background: #fbe9e7; color: var(--danger); }
  .badge.running { background: #e8f2ff; color: #145db2; }
  .badge.pending { background: #fff4df; color: var(--warn); }
  .badge.skipped { background: #eef2f7; color: #526070; }
  .progress {
    height: 8px;
    width: min(180px, 100%);
    background: #e7ece8;
    border-radius: 999px;
    overflow: hidden;
    margin-top: 6px;
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
  .file-row {
    display: grid;
    grid-template-columns: minmax(180px, 1fr) 130px 1fr 1fr;
    gap: 12px;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--line);
  }
  .file-row:last-child { border-bottom: 0; }
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
    font-size: 13px;
  }
  .event time, .event span { color: var(--muted); }
  .empty {
    padding: 36px 18px;
    color: var(--muted);
    text-align: center;
  }
  .settings-columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
  }
  .check-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .check {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 9px 10px;
    background: #fff;
  }
  .check input { width: auto; }
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
    .workspace, .settings-columns { grid-template-columns: 1fr; }
    .topbar { flex-direction: column; }
    .top-actions { width: 100%; }
  }
  @media (max-width: 680px) {
    main { padding: 14px; }
    .range, .settings-grid, .check-grid { grid-template-columns: 1fr; }
    .file-row { grid-template-columns: 1fr; }
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
      <div class="nav-title" data-i18n="side.policy">策略</div>
      <p class="hint" data-i18n="side.policyText">受限内容会先下载媒体，再默认以文档形式发送到目标会话。</p>
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
              <p class="hint" data-i18n="new.hint">单条消息链接不需要填写范围。频道范围转存请填写频道链接、起始 ID 和结束 ID。</p>
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
              <table>
                <thead>
                  <tr>
                    <th data-i18n="tasks.id">ID</th>
                    <th data-i18n="tasks.status">状态</th>
                    <th data-i18n="tasks.source">来源</th>
                    <th data-i18n="tasks.target">目标</th>
                    <th data-i18n="tasks.progress">进度</th>
                    <th data-i18n="tasks.updated">更新</th>
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
          <div class="file-progress" id="items"></div>
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
            <div class="settings-columns">
              <div class="settings-form">
                <h3 data-i18n="settings.paths">路径与任务</h3>
                <label><span data-i18n="settings.saveDirectory">保存目录</span><input name="user.save_directory"></label>
                <label><span data-i18n="settings.tempDirectory">临时目录</span><input name="user.temp_directory"></label>
                <label><span data-i18n="settings.sessionDirectory">会话目录</span><input name="user.session_directory"></label>
                <div class="settings-grid">
                  <label><span data-i18n="settings.maxDownload">最大下载任务</span><input name="user.max_tasks.download" type="number" min="1"></label>
                  <label><span data-i18n="settings.maxUpload">最大上传任务</span><input name="user.max_tasks.upload" type="number" min="1"></label>
                  <label><span data-i18n="settings.retryDownload">下载重试</span><input name="user.max_retries.download" type="number" min="0"></label>
                  <label><span data-i18n="settings.retryUpload">上传重试</span><input name="user.max_retries.upload" type="number" min="0"></label>
                </div>
              </div>
              <div class="settings-form">
                <h3 data-i18n="settings.behavior">行为</h3>
                <label class="check"><input name="global.notice" type="checkbox"><span data-i18n="settings.notice">机器人通知</span></label>
                <label class="check"><input name="user.is_shutdown" type="checkbox"><span data-i18n="settings.shutdown">退出后关机</span></label>
                <label class="check"><input name="global.upload.download_upload" type="checkbox"><span data-i18n="settings.downloadUpload">受限转发时下载后上传</span></label>
                <label class="check"><input name="global.upload.delete" type="checkbox"><span data-i18n="settings.uploadDelete">上传完成删除本地文件</span></label>
                <label><span data-i18n="settings.pendingLimit">下载后上传队列</span><input name="global.upload.pending_limit" type="number" min="1" max="5"></label>
                <h3 data-i18n="settings.sensitive">账号与代理</h3>
                <label><span>API ID</span><input name="user.api_id"></label>
                <label><span>API Hash</span><input name="user.api_hash" type="password" data-i18n-placeholder="settings.secretConfigured"></label>
                <label><span>Bot Token</span><input name="user.bot_token" type="password" data-i18n-placeholder="settings.secretConfigured"></label>
                <label><span data-i18n="settings.proxyPassword">代理密码</span><input name="user.proxy.password" type="password" data-i18n-placeholder="settings.secretConfigured"></label>
              </div>
            </div>
            <div>
              <h3 data-i18n="settings.downloadTypes">下载类型</h3>
              <div class="check-grid" id="download-type-settings"></div>
            </div>
            <div>
              <h3 data-i18n="settings.forwardTypes">转发类型</h3>
              <div class="check-grid" id="forward-type-settings"></div>
            </div>
            <div>
              <h3 data-i18n="settings.exports">导出表格</h3>
              <div class="check-grid">
                <label class="check"><input name="global.export_table.link" type="checkbox"><span data-i18n="settings.exportLink">链接统计表</span></label>
                <label class="check"><input name="global.export_table.count" type="checkbox"><span data-i18n="settings.exportCount">计数统计表</span></label>
                <label class="check"><input name="global.export_table.upload" type="checkbox"><span data-i18n="settings.exportUpload">上传统计表</span></label>
              </div>
            </div>
            <div class="notice" id="settings-notice"></div>
            <div class="actions">
              <button type="submit">
                <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                <span data-i18n="settings.save">保存设置</span>
              </button>
            </div>
          </form>
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
      'nav.settings': '设置',
      'nav.records': '下载记录',
      'nav.primary': '主导航',
      'side.runtime': '运行状态',
      'side.defaultTarget': '默认目标',
      'side.totalTasks': '任务总数',
      'side.running': '运行中',
      'side.failed': '失败',
      'side.policy': '策略',
      'side.policyText': '受限内容会先下载媒体，再默认以文档形式发送到目标会话。',
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
      'new.hint': '单条消息链接不需要填写范围。频道范围转存请填写频道链接、起始 ID 和结束 ID。',
      'new.create': '创建任务',
      'tasks.title': '转存任务',
      'tasks.notSynced': '尚未同步',
      'tasks.id': 'ID',
      'tasks.status': '状态',
      'tasks.source': '来源',
      'tasks.target': '目标',
      'tasks.progress': '进度',
      'tasks.updated': '更新',
      'tasks.actions': '操作',
      'tasks.delete': '删除',
      'tasks.empty': '还没有转存任务。',
      'items.title': '文件进度',
      'items.selectTask': '选择一个任务',
      'items.empty': '该任务还没有文件记录。',
      'items.download': '下载',
      'items.upload': '上传',
      'events.title': '最近事件',
      'events.empty': '没有事件记录。',
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
      'error.auth_required': '需要登录。',
      'error.invalid_task_id': '任务 ID 无效。',
      'error.task_not_found': '找不到任务。',
      'error.not_found': '找不到请求的资源。',
      'error.source_link_required': '请填写来源链接。',
      'error.target_link_required': '请填写目标链接。',
      'error.range_ids_required': '起始 ID 和结束 ID 必须同时填写。',
      'error.range_end_before_start': '结束 ID 必须大于或等于起始 ID。',
      'error.range_source_must_be_chat_link': '范围转存的来源必须是频道链接，不能是单条消息链接。',
      'error.create_task_failed': '创建任务失败。',
      'error.update_settings_failed': '更新设置失败。',
      'event.level.info': '信息',
      'event.level.warning': '警告',
      'event.level.error': '错误',
      'event.fileReady': '文件已准备上传到目标：{name}',
      'event.sentToTarget': '已发送到目标：{name}',
      'event.uploadFailed': '上传失败：{reason}',
      'event.reusedDownload': '已复用下载成功记录：{name}',
      'event.rangeAssigned': '范围转存已分配：{range}',
      'event.singleAssigned': '单条消息转存已分配。',
      'status.pending': '等待',
      'status.running': '运行中',
      'status.success': '成功',
      'status.failure': '失败',
      'status.skipped': '跳过'
    },
    en: {
      'app.subtitle': 'Transfer Console',
      'app.title': 'TRMD Transfer Console',
      'nav.transfers': 'Transfer tasks',
      'nav.settings': 'Settings',
      'nav.records': 'Download records',
      'nav.primary': 'Primary navigation',
      'side.runtime': 'Runtime',
      'side.defaultTarget': 'Default target',
      'side.totalTasks': 'Total tasks',
      'side.running': 'Running',
      'side.failed': 'Failed',
      'side.policy': 'Policy',
      'side.policyText': 'Restricted content is downloaded first, then sent to the target conversation as a document by default.',
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
      'new.hint': 'For a single message link, leave the range empty. For a channel range, provide the channel link plus start and end message IDs.',
      'new.create': 'Create task',
      'tasks.title': 'Transfer tasks',
      'tasks.notSynced': 'Not synced',
      'tasks.id': 'ID',
      'tasks.status': 'Status',
      'tasks.source': 'Source',
      'tasks.target': 'Target',
      'tasks.progress': 'Progress',
      'tasks.updated': 'Updated',
      'tasks.actions': 'Actions',
      'tasks.delete': 'Delete',
      'tasks.empty': 'No transfer tasks yet.',
      'items.title': 'File progress',
      'items.selectTask': 'Select a task',
      'items.empty': 'No file records for this task yet.',
      'items.download': 'Download',
      'items.upload': 'Upload',
      'events.title': 'Latest events',
      'events.empty': 'No events recorded.',
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
      'error.auth_required': 'Authentication required.',
      'error.invalid_task_id': 'Invalid task ID.',
      'error.task_not_found': 'Task not found.',
      'error.not_found': 'Resource not found.',
      'error.source_link_required': 'Source link is required.',
      'error.target_link_required': 'Target link is required.',
      'error.range_ids_required': 'Start ID and End ID must be provided together.',
      'error.range_end_before_start': 'End ID must be greater than or equal to Start ID.',
      'error.range_source_must_be_chat_link': 'Range transfer source must be a chat link, not a message link.',
      'error.create_task_failed': 'Create task failed.',
      'error.update_settings_failed': 'Update settings failed.',
      'event.level.info': 'info',
      'event.level.warning': 'warning',
      'event.level.error': 'error',
      'event.fileReady': 'File ready for target upload: {name}',
      'event.sentToTarget': 'Sent to target: {name}',
      'event.uploadFailed': 'Upload failed: {reason}',
      'event.reusedDownload': 'Reused download success record: {name}',
      'event.rangeAssigned': 'Range transfer assigned: {range}',
      'event.singleAssigned': 'Single-message transfer assigned.',
      'status.pending': 'pending',
      'status.running': 'running',
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
    lastSync: null
  };

  const $ = selector => document.querySelector(selector);
  const $$ = selector => Array.from(document.querySelectorAll(selector));

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
    match = message.match(/^Range transfer assigned: (.+)\.$/);
    if (match) return interpolate(t('event.rangeAssigned'), {range: match[1]});
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
  }

  function badge(status) {
    return `<span class="badge ${esc(status)}">${esc(t(`status.${status}`))}</span>`;
  }

  function taskProgress(task) {
    const total = Number(task.total_items || 0);
    const done = Number(task.completed_items || 0);
    const failed = Number(task.failed_items || 0);
    const percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
    return `<div>${done}/${total}, ${failed} ${esc(t('side.failed'))}</div><div class="progress"><div style="width:${percent}%"></div></div>`;
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
        <td class="mono">${esc(task.updated_at)}</td>
        <td>
          <button class="danger icon-only" type="button" title="${esc(t('tasks.delete'))}" aria-label="${esc(t('tasks.delete'))}" onclick="deleteTask(event, ${task.id})">
            <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span class="sr-only" data-i18n="tasks.delete">${esc(t('tasks.delete'))}</span>
          </button>
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
      await loadTask(state.tasks[0].id);
    } else if (state.selectedTaskId) {
      await loadTask(state.selectedTaskId);
    }
  }

  async function loadTask(id) {
    state.selectedTaskId = Number(id);
    const res = await fetch(`/api/tasks/${state.selectedTaskId}`);
    if (!res.ok) {
      state.selectedTaskId = null;
      state.items = [];
      state.events = [];
      $('#selected-task').textContent = t('items.selectTask');
      renderItems(state.items);
      renderEvents(state.events);
      return;
    }
    const data = await res.json();
    $('#selected-task').textContent = `#${state.selectedTaskId}`;
    state.items = data.items || [];
    state.events = data.events || [];
    renderItems(state.items);
    renderEvents(state.events);
  }

  function progressLine(label, current, total) {
    const percent = pct(current, total);
    return `<div><div>${esc(label)} ${percent}%</div><div class="progress"><div style="width:${percent}%"></div></div><div class="mono">${formatBytes(current)} / ${formatBytes(total)}</div></div>`;
  }

  function renderItems(items) {
    $('#items').innerHTML = items.length ? items.map(item => `
      <div class="file-row">
        <div>
          <div>${esc(item.file_name || item.local_path || item.source_link || `#${item.source_message_id || item.id}`)}</div>
          <div class="mono">${esc(item.source_chat_id || '')} ${esc(item.source_message_id || '')}</div>
        </div>
        <div>${badge(item.status)}</div>
        ${progressLine(t('items.download'), item.download_current, item.download_total)}
        ${progressLine(t('items.upload'), item.upload_current, item.upload_total)}
      </div>
    `).join('') : `<div class="empty">${esc(t('items.empty'))}</div>`;
  }

  function renderEvents(events) {
    $('#event-count').textContent = events.length;
    $('#events').innerHTML = events.length ? events.map(event => `
      <div class="event">
        <time>${esc(event.created_at)}</time>
        <span>${esc(localizeEventLevel(event.level))}</span>
        <div>${esc(localizeEventMessage(event))}</div>
      </div>
    `).join('') : `<div class="empty">${esc(t('events.empty'))}</div>`;
  }

  async function deleteTask(event, taskId) {
    event.stopPropagation();
    const res = await fetch(`/api/tasks/${taskId}`, {method: 'DELETE'});
    if (res.ok && state.selectedTaskId === taskId) {
      state.selectedTaskId = null;
      state.items = [];
      state.events = [];
      $('#selected-task').textContent = t('items.selectTask');
      $('#items').innerHTML = '';
      $('#events').innerHTML = '';
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
      <label class="check"><input name="user.download_type" value="${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
    `).join('');
    $('#forward-type-settings').innerHTML = forwardTypes.map(type => `
      <label class="check"><input name="global.forward_type.${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
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
  $('#refresh').addEventListener('click', () => {
    loadTasks();
    if ($('#view-records').classList.contains('active')) loadRecords();
    if ($('#view-settings').classList.contains('active')) loadSettings();
  });
  $('#transfer-form').addEventListener('submit', async event => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    payload.start_id = payload.start_id ? Number(payload.start_id) : null;
    payload.end_id = payload.end_id ? Number(payload.end_id) : null;
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      $('#form-error').textContent = translateApiError(data, 'form.createFailed');
      $('#form-error').style.display = 'block';
      return;
    }
    $('#form-error').style.display = 'none';
    state.selectedTaskId = data.task_id;
    await loadTasks();
  });
  $('#settings-form').addEventListener('submit', saveSettings);

  applyLanguage();
  loadTasks();
  setInterval(loadTasks, 3000);
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
