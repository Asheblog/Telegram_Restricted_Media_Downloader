# coding=UTF-8

WEB_UI_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TRMD Web Command Center</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-soft: #eef4fb;
      --text: #1e293b;
      --muted: #64748b;
      --line: #e2e8f0;
      --primary: #3b82f6;
      --primary-strong: #1d4ed8;
      --cta: #f97316;
      --danger: #b42318;
      --warn: #a15c07;
      --ok: #127c52;
      --shadow: 0 18px 48px rgba(15, 23, 42, .08);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100svh;
      background: linear-gradient(180deg, rgba(59,130,246,.08), transparent 260px), var(--bg);
      color: var(--text);
    }
    button, input, select, textarea { font: inherit; }
    button, .command-tab, tr[data-task-id] { cursor: pointer; }
    .shell {
      min-height: 100svh;
      display: grid;
      grid-template-columns: 292px minmax(0, 1fr);
    }
    aside {
      position: sticky;
      top: 0;
      height: 100svh;
      overflow: auto;
      border-right: 1px solid var(--line);
      background: rgba(255,255,255,.84);
      backdrop-filter: blur(18px);
      padding: 24px 18px;
    }
    main {
      min-width: 0;
      padding: 24px;
      display: grid;
      gap: 18px;
      grid-template-rows: auto auto minmax(0, 1fr);
    }
    .brand {
      display: flex;
      gap: 12px;
      align-items: center;
      margin-bottom: 20px;
    }
    .mark {
      width: 38px;
      height: 38px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      color: #fff;
      background: var(--primary);
    }
    svg { width: 18px; height: 18px; }
    .brand h1, .panel-head h2, .panel-head h3 { margin: 0; letter-spacing: 0; }
    .brand h1 { font-size: 18px; }
    .brand p, .hint, .meta, .metric span { color: var(--muted); }
    .brand p { margin: 2px 0 0; font-size: 13px; }
    .nav-title {
      margin: 18px 0 8px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    .command-tabs {
      display: grid;
      gap: 4px;
    }
    .command-tab {
      width: 100%;
      display: grid;
      grid-template-columns: 22px 1fr;
      align-items: center;
      gap: 8px;
      min-height: 38px;
      border: 1px solid transparent;
      border-radius: 6px;
      background: transparent;
      color: var(--text);
      padding: 8px 10px;
      text-align: left;
      transition: background .18s ease, border-color .18s ease, color .18s ease;
    }
    .command-tab:hover, .command-tab.active {
      background: var(--surface-soft);
      border-color: #c8dbf6;
      color: var(--primary-strong);
    }
    .command-tab span:first-child {
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
    }
    .metric {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      padding: 9px 0;
      border-bottom: 1px solid var(--line);
      font-size: 13px;
    }
    .topbar {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      animation: enter .28s ease both;
    }
    .topbar h2 {
      margin: 0 0 5px;
      font-size: clamp(24px, 3vw, 38px);
      letter-spacing: 0;
    }
    .topbar p { max-width: 760px; margin: 0; line-height: 1.5; color: var(--muted); }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 36px;
      white-space: nowrap;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 7px 11px;
      background: rgba(255,255,255,.78);
      color: var(--muted);
      font-size: 13px;
    }
    .status::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--ok);
      box-shadow: 0 0 0 5px rgba(18,124,82,.12);
    }
    .workspace {
      display: grid;
      grid-template-columns: minmax(330px, 430px) minmax(0, 1fr);
      gap: 18px;
      min-height: 0;
    }
    section {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,.88);
      box-shadow: var(--shadow);
    }
    .panel-head {
      min-height: 58px;
      padding: 15px 18px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .panel-head h3 { font-size: 15px; }
    .panel-head .meta { font-size: 12px; }
    form {
      padding: 18px;
      display: grid;
      gap: 14px;
    }
    .field { display: grid; gap: 7px; color: var(--muted); font-size: 13px; }
    .field strong { color: var(--text); font-weight: 650; }
    .required::after { content: " *"; color: var(--cta); }
    input, select, textarea {
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      padding: 10px 11px;
      outline: none;
      transition: border-color .18s ease, box-shadow .18s ease;
    }
    textarea { min-height: 92px; resize: vertical; line-height: 1.45; }
    input:focus, select:focus, textarea:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 4px rgba(59,130,246,.14);
    }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .checks {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 7px 9px;
      background: #fff;
      color: var(--text);
    }
    .check input { width: 16px; min-height: 16px; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    button {
      min-height: 40px;
      border: 0;
      border-radius: 6px;
      padding: 10px 13px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      color: #fff;
      background: var(--primary);
      transition: background .18s ease, transform .18s ease, opacity .18s ease;
    }
    button:hover { background: var(--primary-strong); }
    button:active { transform: translateY(1px); }
    button:disabled { opacity: .56; cursor: not-allowed; }
    button.secondary {
      background: var(--surface-soft);
      border: 1px solid var(--line);
      color: var(--text);
    }
    button.secondary:hover { background: #dfeaf8; }
    button.danger { background: var(--cta); }
    button.danger:hover { background: #c2410c; }
    .feedback {
      display: none;
      border-radius: 6px;
      padding: 10px 11px;
      font-size: 13px;
      line-height: 1.45;
    }
    .feedback.error { display: block; color: var(--danger); background: #fef2f2; border: 1px solid #fecaca; }
    .feedback.ok { display: block; color: var(--ok); background: #ecfdf3; border: 1px solid #bbf7d0; }
    .hint { margin: 0; font-size: 12px; line-height: 1.5; }
    .tables {
      display: grid;
      grid-template-rows: minmax(0, 1fr) auto;
      overflow: hidden;
    }
    .table-wrap {
      overflow: auto;
      min-height: 360px;
    }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td {
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }
    th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: #f8fafc;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    tr[data-task-id]:hover { background: #f8fafc; }
    tr.selected { background: #eff6ff; }
    .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 4px 8px;
      background: #eef2ff;
      color: #3730a3;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .badge.success { background: #dcfce7; color: var(--ok); }
    .badge.failure { background: #fee2e2; color: var(--danger); }
    .badge.running { background: #dbeafe; color: var(--primary-strong); }
    .badge.pending { background: #ffedd5; color: var(--warn); }
    .details {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 18px;
    }
    .event-log {
      max-height: 250px;
      overflow: auto;
      padding: 8px 18px 16px;
    }
    .event {
      display: grid;
      grid-template-columns: 150px 74px minmax(0, 1fr);
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid var(--line);
      font-size: 12px;
    }
    .event time, .event span { color: var(--muted); }
    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      padding: 14px 18px;
      border-top: 1px solid var(--line);
      background: #fbfdff;
    }
    .summary-item {
      min-height: 54px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      background: #fff;
    }
    .summary-item span { display: block; color: var(--muted); font-size: 11px; }
    .summary-item strong { font-size: 18px; }
    .empty { padding: 28px 18px; color: var(--muted); text-align: center; }
    @keyframes enter {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @media (max-width: 1080px) {
      .shell { grid-template-columns: 1fr; }
      aside { position: static; height: auto; }
      .command-tabs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .workspace { grid-template-columns: 1fr; }
    }
    @media (max-width: 680px) {
      main { padding: 14px; }
      .topbar { align-items: flex-start; flex-direction: column; }
      .grid-2, .checks, .summary, .command-tabs { grid-template-columns: 1fr; }
      th:nth-child(4), td:nth-child(4), th:nth-child(5), td:nth-child(5) { display: none; }
      .event { grid-template-columns: 1fr; gap: 4px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <div class="mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M4 12h16M4 17h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </div>
        <div>
          <h1>TRMD</h1>
          <p>Web Command Center</p>
        </div>
      </div>
      <div class="nav-title">Commands</div>
      <nav class="command-tabs" id="command-tabs"></nav>
      <div class="nav-title">Runtime</div>
      <div class="metric"><span>Web tasks</span><strong id="metric-web">0</strong></div>
      <div class="metric"><span>Downloads</span><strong id="metric-downloads">0</strong></div>
      <div class="metric"><span>Uploads</span><strong id="metric-uploads">0</strong></div>
      <div class="metric"><span>Listeners</span><strong id="metric-listeners">0</strong></div>
    </aside>
    <main>
      <div class="topbar">
        <div>
          <h2>Command center</h2>
          <p>创建、监听、上传、转发和查看统计都在同一个 Web 工作台中完成。消息链接导入是浏览器中的 Telegram 转发等价入口。</p>
        </div>
        <div class="status" id="runtime-status">WebUI active</div>
      </div>

      <div class="workspace">
        <section>
          <div class="panel-head">
            <div>
              <h3 id="form-title">Download</h3>
              <div class="meta" id="form-usage">/download</div>
            </div>
            <span class="meta" id="form-mode">Create task</span>
          </div>
          <form id="command-form">
            <div id="form-fields"></div>
            <div class="feedback" id="form-feedback" role="alert"></div>
            <div class="actions">
              <button type="submit" id="submit-command">
                <svg viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                <span id="submit-label">Create task</span>
              </button>
              <button type="button" class="secondary" id="refresh">
                <svg viewBox="0 0 24 24" fill="none"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                Refresh
              </button>
            </div>
          </form>
        </section>

        <section class="tables">
          <div class="panel-head">
            <h3>Tasks</h3>
            <span class="meta" id="last-sync">Not synced</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Command</th>
                  <th>Status</th>
                  <th>Source</th>
                  <th>Target</th>
                  <th>Action</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody id="tasks"></tbody>
            </table>
            <div class="empty" id="task-empty">No Web tasks yet.</div>
          </div>
          <div class="summary">
            <div class="summary-item"><span>Running</span><strong id="summary-running">0</strong></div>
            <div class="summary-item"><span>Failed</span><strong id="summary-failed">0</strong></div>
            <div class="summary-item"><span>Listen download</span><strong id="summary-listen-download">0</strong></div>
            <div class="summary-item"><span>Listen forward</span><strong id="summary-listen-forward">0</strong></div>
          </div>
        </section>
      </div>

      <div class="details">
        <section>
          <div class="panel-head">
            <h3>Events</h3>
            <span class="meta" id="selected-task">Select a task</span>
          </div>
          <div class="event-log" id="events"></div>
        </section>
        <section>
          <div class="panel-head">
            <h3>Runtime table</h3>
            <span class="meta">download / upload / listener</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Source</th>
                  <th>Target</th>
                </tr>
              </thead>
              <tbody id="runtime-table"></tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  </div>

  <script>
    const commands = [
      {command:'download', title:'Download', usage:'/download https://t.me/x/x 起始ID 结束ID', mode:'Create task'},
      {command:'forward', title:'Forward', usage:'/forward https://t.me/A https://t.me/B 1 100', mode:'Create task'},
      {command:'listen_download', title:'Listen download', usage:'/listen_download https://t.me/A https://t.me/B', mode:'Register listener'},
      {command:'listen_forward', title:'Listen forward', usage:'/listen_forward 监听频道 转发频道', mode:'Register listener'},
      {command:'listen_info', title:'Listen info', usage:'/listen_info', mode:'View runtime'},
      {command:'upload', title:'Upload', usage:'/upload 本地文件 目标频道', mode:'Create task'},
      {command:'upload_r', title:'Upload recursive', usage:'/upload_r 本地文件夹 目标频道', mode:'Create task'},
      {command:'download_chat', title:'Download chat', usage:'/download_chat 频道链接', mode:'Create task'}
    ];
    const downloadTypes = ['video','photo','document','audio','voice','animation','video_note'];
    let activeCommand = 'download';
    let selectedTaskId = null;
    let latestTasks = [];

    const $ = selector => document.querySelector(selector);
    const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
    }[ch]));
    const icon = '<svg viewBox="0 0 24 24" fill="none"><path d="M8 5l8 7-8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    function setFeedback(kind, message) {
      const el = $('#form-feedback');
      el.className = message ? `feedback ${kind}` : 'feedback';
      el.textContent = message || '';
    }

    function field(name, label, attrs = {}) {
      const required = attrs.required ? ' required' : '';
      const type = attrs.type || 'text';
      const placeholder = attrs.placeholder || '';
      const value = attrs.value || '';
      return `<label class="field"><strong class="${required ? 'required' : ''}">${label}</strong><input name="${name}" type="${type}" value="${esc(value)}" placeholder="${esc(placeholder)}"${required}></label>`;
    }

    function textarea(name, label, placeholder, required = false) {
      return `<label class="field"><strong class="${required ? 'required' : ''}">${label}</strong><textarea name="${name}" placeholder="${esc(placeholder)}"${required ? ' required' : ''}></textarea></label>`;
    }

    function typeChecks() {
      return `<div class="field"><strong class="required">Download types</strong><div class="checks">${
        downloadTypes.map(type => `<label class="check"><input type="checkbox" name="download_type" value="${type}" checked>${type}</label>`).join('')
      }</div></div>`;
    }

    function renderFields() {
      const title = commands.find(item => item.command === activeCommand);
      $('#form-title').textContent = title.title;
      $('#form-usage').textContent = title.usage;
      $('#form-mode').textContent = title.mode;
      $('#submit-command').style.display = activeCommand === 'listen_info' ? 'none' : 'inline-flex';
      $('#submit-command').className = '';
      $('#submit-label').textContent = 'Create task';
      let html = '';
      if (activeCommand === 'download') {
        html = textarea('links', 'Message links or chat link', 'https://t.me/source/123\\nhttps://t.me/source/124', true)
          + field('file_path', 'Optional txt file path', {placeholder:'C:\\\\links.txt or /home/user/links.txt'})
          + '<div class="grid-2">' + field('start_id', 'Start ID', {type:'number'}) + field('end_id', 'End ID', {type:'number'}) + '</div>'
          + field('target_link', 'Optional target for download-upload', {placeholder:'https://t.me/target or me'})
          + '<label class="field"><strong>Target profile</strong><select name="target_profile"><option value="generic">Generic Telegram target</option><option value="pikpak">PikPak document transfer</option></select></label>'
          + '<p class="hint">消息链接导入用于替代浏览器无法接收的 Telegram 原生转发事件。</p>';
      } else if (activeCommand === 'forward') {
        html = field('origin_link', 'Origin channel', {placeholder:'https://t.me/A', required:true})
          + field('target_link', 'Target channel', {placeholder:'https://t.me/B or me', required:true})
          + '<div class="grid-2">' + field('start_id', 'Start ID', {type:'number', required:true}) + field('end_id', 'End ID', {type:'number', required:true}) + '</div>';
      } else if (activeCommand === 'listen_download') {
        html = textarea('links', 'Listen channels', 'https://t.me/A\\nhttps://t.me/B', true);
      } else if (activeCommand === 'listen_forward') {
        html = field('listen_link', 'Listen channel', {placeholder:'https://t.me/A', required:true})
          + field('target_link', 'Forward target', {placeholder:'https://t.me/B or me', required:true});
      } else if (activeCommand === 'upload') {
        html = field('file_path', 'Local file path', {placeholder:'C:\\\\files\\\\video.mp4 or /home/user/files/video.mp4', required:true})
          + field('target_link', 'Target channel', {placeholder:'https://t.me/target or me', required:true})
          + '<label class="check"><input type="checkbox" name="delete_after_upload">Delete after upload</label>';
      } else if (activeCommand === 'upload_r') {
        html = field('directory_path', 'Local directory path', {placeholder:'C:\\\\files or /home/user/files', required:true})
          + field('target_link', 'Target channel', {placeholder:'https://t.me/target or me', required:true})
          + '<label class="check"><input type="checkbox" name="delete_after_upload">Delete after upload</label>';
      } else if (activeCommand === 'download_chat') {
        html = field('chat_link', 'Chat link', {placeholder:'https://t.me/channel or me', required:true})
          + '<div class="grid-2">' + field('start_date', 'Start date', {type:'date'}) + field('end_date', 'End date', {type:'date'}) + '</div>'
          + typeChecks()
          + textarea('keywords', 'Keywords', 'one keyword per line or space separated')
          + '<label class="check"><input type="checkbox" name="include_comment">Include discussion replies</label>';
      } else {
        html = '<div class="empty">Use the runtime table below to inspect current downloads, uploads, listeners, and Web tasks.</div>';
      }
      $('#form-fields').innerHTML = html;
      setFeedback('', '');
    }

    function renderTabs() {
      $('#command-tabs').innerHTML = commands.map((item, index) => `
        <button type="button" class="command-tab ${item.command === activeCommand ? 'active' : ''}" data-command="${item.command}">
          <span>${String(index + 1).padStart(2, '0')}</span><strong>${esc(item.title)}</strong>
        </button>
      `).join('');
      document.querySelectorAll('.command-tab').forEach(tab => {
        tab.addEventListener('click', () => {
          activeCommand = tab.dataset.command;
          renderTabs();
          renderFields();
        });
      });
    }

    function formPayload(form) {
      const data = new FormData(form);
      const payload = {};
      for (const [key, value] of data.entries()) {
        if (key === 'download_type') continue;
        payload[key] = value;
      }
      if (activeCommand === 'download') {
        payload.links = payload.links || '';
        payload.start_id = payload.start_id ? Number(payload.start_id) : null;
        payload.end_id = payload.end_id ? Number(payload.end_id) : null;
      }
      if (activeCommand === 'forward') {
        payload.start_id = Number(payload.start_id);
        payload.end_id = Number(payload.end_id);
      }
      if (activeCommand === 'download_chat') {
        payload.download_type = data.getAll('download_type');
        payload.include_comment = data.get('include_comment') === 'on';
      }
      if (activeCommand === 'upload' || activeCommand === 'upload_r') {
        payload.delete_after_upload = data.get('delete_after_upload') === 'on';
      }
      return payload;
    }

    async function submitCommand(event) {
      event.preventDefault();
      if (activeCommand === 'listen_info') return;
      const button = $('#submit-command');
      button.disabled = true;
      setFeedback('', '');
      try {
        const body = {command: activeCommand, payload: formPayload(event.currentTarget)};
        const res = await fetch('/api/tasks', {
          method: 'POST',
          headers: {'content-type':'application/json'},
          body: JSON.stringify(body)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Request failed.');
        selectedTaskId = data.task_id;
        setFeedback('ok', `Task #${data.task_id} accepted.`);
        await refreshAll();
      } catch (error) {
        setFeedback('error', error.message);
      } finally {
        button.disabled = false;
      }
    }

    function badge(status) {
      return `<span class="badge ${esc(status)}">${esc(status)}</span>`;
    }

    async function loadTasks() {
      const res = await fetch('/api/tasks');
      const data = await res.json();
      latestTasks = data.tasks || [];
      $('#task-empty').style.display = latestTasks.length ? 'none' : 'block';
      $('#tasks').innerHTML = latestTasks.map(task => `
        <tr data-task-id="${task.id}" class="${Number(task.id) === selectedTaskId ? 'selected' : ''}">
          <td class="mono">#${task.id}</td>
          <td class="mono">${esc(task.command || 'transfer')}</td>
          <td>${badge(task.status)}</td>
          <td class="mono">${esc(task.source_link)}</td>
          <td class="mono">${esc(task.target_link)}</td>
          <td class="mono">${esc(task.updated_at)}</td>
        </tr>
      `).join('');
      document.querySelectorAll('tr[data-task-id]').forEach(row => {
        row.addEventListener('click', () => loadTask(Number(row.dataset.taskId)));
      });
      $('#last-sync').textContent = new Date().toLocaleTimeString();
      $('#summary-running').textContent = latestTasks.filter(t => t.status === 'running').length;
      $('#summary-failed').textContent = latestTasks.filter(t => t.status === 'failure').length;
      $('#metric-web').textContent = latestTasks.length;
      if (!selectedTaskId && latestTasks[0]) selectedTaskId = Number(latestTasks[0].id);
      if (selectedTaskId) await loadTask(selectedTaskId);
    }

    async function loadTask(id) {
      selectedTaskId = id;
      const res = await fetch(`/api/tasks/${id}`);
      if (!res.ok) return;
      const data = await res.json();
      $('#selected-task').textContent = `Task #${id}`;
      const events = data.events || [];
      $('#events').innerHTML = events.length ? events.map(event => `
        <div class="event">
          <time>${esc(event.created_at)}</time>
          <span>${esc(event.level)}</span>
          <div>${esc(event.message)}</div>
        </div>
      `).join('') : '<div class="empty">No events recorded.</div>';
      document.querySelectorAll('tr[data-task-id]').forEach(row => {
        row.classList.toggle('selected', Number(row.dataset.taskId) === id);
      });
    }

    async function loadSummary() {
      const res = await fetch('/api/runtime/summary');
      const summary = await res.json();
      const counts = summary.counts || {};
      $('#metric-downloads').textContent = counts.downloads || 0;
      $('#metric-uploads').textContent = counts.uploads || 0;
      $('#metric-listeners').textContent = (counts.listen_download || 0) + (counts.listen_forward || 0);
      $('#summary-listen-download').textContent = counts.listen_download || 0;
      $('#summary-listen-forward').textContent = counts.listen_forward || 0;
      $('#runtime-status').textContent = summary.shutdown_requested ? 'Shutdown requested' : 'WebUI active';
      const rows = [];
      for (const item of summary.downloads || []) {
        rows.push({type:'download', status:`${item.complete_num}/${item.member_num}`, source:item.link, target:'', id:''});
      }
      for (const item of summary.uploads || []) {
        rows.push({type:'upload', status:item.status, source:item.file_path, target:item.chat_id || '', id:''});
      }
      for (const item of summary.listeners || []) {
        rows.push({type:item.command, status:'listening', source:item.listen_link, target:item.target_link, id:item.id});
      }
      $('#runtime-table').innerHTML = rows.length ? rows.map(row => `
        <tr>
          <td class="mono">${esc(row.type)}</td>
          <td>${esc(row.status)}</td>
          <td class="mono">${esc(row.source)}</td>
          <td class="mono">${esc(row.target)}</td>
          <td>${row.id ? `<button type="button" class="secondary" data-listener-id="${esc(row.id)}">Stop</button>` : ''}</td>
        </tr>
      `).join('') : '<tr><td colspan="5" class="empty">No runtime entries.</td></tr>';
      document.querySelectorAll('[data-listener-id]').forEach(button => {
        button.addEventListener('click', async () => {
          button.disabled = true;
          const res = await fetch(`/api/listeners/${encodeURIComponent(button.dataset.listenerId)}`, {method:'DELETE'});
          if (!res.ok) {
            const data = await res.json();
            setFeedback('error', data.error || 'Stop listener failed.');
          }
          await refreshAll();
        });
      });
    }

    async function refreshAll() {
      await Promise.all([loadTasks(), loadSummary()]);
    }

    $('#command-form').addEventListener('submit', submitCommand);
    $('#refresh').addEventListener('click', refreshAll);
    renderTabs();
    renderFields();
    refreshAll();
    setInterval(refreshAll, 3000);
  </script>
</body>
</html>'''
