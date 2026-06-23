# coding=UTF-8

WEB_UI_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TRMD Transfer Console</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f4;
      --panel: #ffffff;
      --panel-soft: #eef3f0;
      --text: #17201b;
      --muted: #5d6b62;
      --line: #d8ded8;
      --accent: #0f8f72;
      --accent-strong: #0a6f5a;
      --danger: #b42318;
      --warn: #a15c07;
      --ok: #127c52;
      --shadow: 0 16px 45px rgba(31, 48, 38, .08);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        linear-gradient(180deg, rgba(15, 143, 114, .08), transparent 280px),
        var(--bg);
      color: var(--text);
      min-height: 100svh;
    }
    button, input, select {
      font: inherit;
    }
    .shell {
      min-height: 100svh;
      display: grid;
      grid-template-columns: 280px 1fr;
    }
    aside {
      border-right: 1px solid var(--line);
      background: rgba(255, 255, 255, .72);
      backdrop-filter: blur(20px);
      padding: 28px 22px;
      position: sticky;
      top: 0;
      height: 100svh;
    }
    main {
      padding: 30px;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 22px;
      min-width: 0;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 28px;
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
    .brand h1 {
      font-size: 18px;
      margin: 0;
      letter-spacing: 0;
    }
    .brand p {
      margin: 2px 0 0;
      color: var(--muted);
      font-size: 13px;
    }
    .nav-title {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      margin: 26px 0 8px;
    }
    .metric {
      display: grid;
      grid-template-columns: 1fr auto;
      padding: 10px 0;
      border-bottom: 1px solid var(--line);
      gap: 10px;
      font-size: 14px;
    }
    .metric span { color: var(--muted); }
    .metric strong { font-weight: 650; }
    .hero {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 24px;
      min-width: 0;
      animation: rise .42s ease both;
    }
    .hero h2 {
      font-size: clamp(28px, 4vw, 52px);
      line-height: 1;
      margin: 0 0 10px;
      letter-spacing: 0;
    }
    .hero p {
      margin: 0;
      color: var(--muted);
      max-width: 680px;
      line-height: 1.55;
    }
    .status-dot {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.72);
      border-radius: 999px;
      white-space: nowrap;
      color: var(--muted);
      font-size: 14px;
    }
    .status-dot::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 0 6px rgba(15, 143, 114, .12);
    }
    .workspace {
      display: grid;
      grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
      gap: 22px;
      min-height: 0;
    }
    section {
      background: rgba(255, 255, 255, .82);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      min-width: 0;
    }
    .panel-head {
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .panel-head h3 {
      margin: 0;
      font-size: 15px;
      letter-spacing: 0;
    }
    .panel-head span {
      color: var(--muted);
      font-size: 13px;
    }
    form {
      padding: 20px;
      display: grid;
      gap: 16px;
    }
    label {
      display: grid;
      gap: 7px;
      color: var(--muted);
      font-size: 13px;
    }
    input, select {
      width: 100%;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 6px;
      padding: 11px 12px;
      outline: none;
      transition: border-color .18s ease, box-shadow .18s ease;
    }
    input:focus, select:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 4px rgba(15, 143, 114, .12);
    }
    .range {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .actions {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 4px;
    }
    button {
      border: 0;
      border-radius: 6px;
      padding: 11px 14px;
      color: #fff;
      background: var(--accent);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: background .18s ease, transform .18s ease;
      min-height: 42px;
    }
    button:hover { background: var(--accent-strong); }
    button:active { transform: translateY(1px); }
    button.secondary {
      color: var(--text);
      background: var(--panel-soft);
      border: 1px solid var(--line);
    }
    button.secondary:hover { background: #e2ece7; }
    .hint {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
      margin: 0;
    }
    .form-error {
      display: none;
      color: var(--danger);
      background: #fbe9e7;
      border: 1px solid #f3b5ad;
      border-radius: 6px;
      padding: 10px 12px;
      font-size: 13px;
      line-height: 1.45;
    }
    .tasks {
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
    }
    .task-list {
      overflow: auto;
      min-height: 420px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }
    th {
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .08em;
      background: rgba(246,247,244,.75);
      position: sticky;
      top: 0;
    }
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
      background: var(--panel-soft);
      color: var(--muted);
      white-space: nowrap;
    }
    .badge.success { background: #e5f5ed; color: var(--ok); }
    .badge.failure { background: #fbe9e7; color: var(--danger); }
    .badge.running { background: #e8f2ff; color: #145db2; }
    .badge.pending { background: #fff4df; color: var(--warn); }
    .progress {
      height: 8px;
      width: min(170px, 100%);
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
    .event-log {
      margin-top: 22px;
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      animation: rise .48s ease both;
    }
    .events {
      max-height: 240px;
      overflow: auto;
      padding: 8px 20px 18px;
    }
    .event {
      display: grid;
      grid-template-columns: 120px 70px 1fr;
      gap: 12px;
      padding: 9px 0;
      border-bottom: 1px solid var(--line);
      font-size: 13px;
    }
    .event time, .event span { color: var(--muted); }
    .empty {
      padding: 42px 20px;
      color: var(--muted);
      text-align: center;
    }
    svg { width: 18px; height: 18px; }
    @keyframes rise {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @media (max-width: 980px) {
      .shell { grid-template-columns: 1fr; }
      aside {
        position: static;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      main { padding: 22px; }
      .workspace { grid-template-columns: 1fr; }
      .hero { align-items: flex-start; flex-direction: column; }
    }
    @media (max-width: 620px) {
      main { padding: 16px; }
      .range { grid-template-columns: 1fr; }
      th:nth-child(3), td:nth-child(3) { display: none; }
      .event { grid-template-columns: 1fr; gap: 4px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <div class="mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <div>
          <h1>TRMD</h1>
          <p>Transfer Console</p>
        </div>
      </div>
      <div class="nav-title">Runtime</div>
      <div class="metric"><span>Default target</span><strong>@pikpak_bot</strong></div>
      <div class="metric"><span>Total tasks</span><strong id="metric-total">0</strong></div>
      <div class="metric"><span>Running</span><strong id="metric-running">0</strong></div>
      <div class="metric"><span>Failed</span><strong id="metric-failed">0</strong></div>
      <div class="nav-title">Policy</div>
      <p class="hint">Restricted content is transferred by downloading media and sending it to the target conversation as a document by default.</p>
    </aside>
    <main>
      <div class="hero">
        <div>
          <h2>PikPak transfer queue</h2>
          <p>Create durable transfer tasks for Telegram media that cannot be forwarded natively. The WebUI tracks state, failures, and retry-ready records in SQLite.</p>
        </div>
        <div class="status-dot">WebUI active</div>
      </div>
      <div class="workspace">
        <section>
          <div class="panel-head">
            <h3>New transfer</h3>
            <span>PikPak profile</span>
          </div>
          <form id="transfer-form">
            <label>
              Source link
              <input name="source_link" placeholder="https://t.me/source/123" required>
            </label>
            <label>
              Target
              <input name="target_link" value="https://t.me/pikpak_bot" required>
            </label>
            <label>
              Target profile
              <select name="target_profile">
                <option value="pikpak">PikPak document transfer</option>
                <option value="generic">Generic Telegram target</option>
              </select>
            </label>
            <div class="range">
              <label>
                Start ID
                <input name="start_id" inputmode="numeric" placeholder="optional">
              </label>
              <label>
                End ID
                <input name="end_id" inputmode="numeric" placeholder="optional">
              </label>
            </div>
            <p class="hint">For a single message link, leave the range empty. For a channel range, provide the channel link plus start and end message IDs.</p>
            <div class="form-error" id="form-error" role="alert"></div>
            <div class="actions">
              <button type="submit">
                <svg viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                Create task
              </button>
              <button class="secondary" type="button" id="refresh">
                <svg viewBox="0 0 24 24" fill="none"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                Refresh
              </button>
            </div>
          </form>
        </section>
        <section class="tasks">
          <div class="panel-head">
            <h3>Transfer tasks</h3>
            <span id="last-sync">Not synced</span>
          </div>
          <div class="task-list">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Status</th>
                  <th>Source</th>
                  <th>Target</th>
                  <th>Progress</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody id="tasks"></tbody>
            </table>
            <div class="empty" id="empty">No transfer tasks yet.</div>
          </div>
        </section>
      </div>
      <section class="event-log">
        <div class="panel-head">
          <h3>Latest events</h3>
          <span id="selected-task">Select a task</span>
        </div>
        <div class="events" id="events"></div>
      </section>
    </main>
  </div>
  <script>
    const tasksEl = document.querySelector('#tasks');
    const eventsEl = document.querySelector('#events');
    const emptyEl = document.querySelector('#empty');
    const selectedTaskEl = document.querySelector('#selected-task');
    const formErrorEl = document.querySelector('#form-error');
    let selectedTaskId = null;

    function esc(value) {
      return String(value ?? '').replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[ch]));
    }

    function badge(status) {
      return `<span class="badge ${esc(status)}">${esc(status)}</span>`;
    }

    function progress(task) {
      const total = Number(task.total_items || 0);
      const done = Number(task.completed_items || 0);
      const failed = Number(task.failed_items || 0);
      const pct = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
      return `<div>${done}/${total} done, ${failed} failed</div><div class="progress"><div style="width:${pct}%"></div></div>`;
    }

    async function loadTasks() {
      const res = await fetch('/api/tasks');
      const data = await res.json();
      const tasks = data.tasks || [];
      document.querySelector('#metric-total').textContent = tasks.length;
      document.querySelector('#metric-running').textContent = tasks.filter(t => t.status === 'running').length;
      document.querySelector('#metric-failed').textContent = tasks.filter(t => t.status === 'failure').length;
      document.querySelector('#last-sync').textContent = new Date().toLocaleTimeString();
      emptyEl.style.display = tasks.length ? 'none' : 'block';
      tasksEl.innerHTML = tasks.map(task => `
        <tr data-task-id="${task.id}">
          <td class="mono">#${task.id}</td>
          <td>${badge(task.status)}</td>
          <td class="mono">${esc(task.source_link)}</td>
          <td class="mono">${esc(task.target_link)}</td>
          <td>${progress(task)}</td>
          <td class="mono">${esc(task.updated_at)}</td>
        </tr>
      `).join('');
      document.querySelectorAll('tr[data-task-id]').forEach(row => {
        row.addEventListener('click', () => loadTask(row.dataset.taskId));
      });
      if (!selectedTaskId && tasks[0]) {
        await loadTask(tasks[0].id);
      } else if (selectedTaskId) {
        await loadTask(selectedTaskId);
      }
    }

    async function loadTask(id) {
      selectedTaskId = Number(id);
      const res = await fetch(`/api/tasks/${selectedTaskId}`);
      if (!res.ok) return;
      const data = await res.json();
      selectedTaskEl.textContent = `Task #${selectedTaskId}`;
      const events = data.events || [];
      eventsEl.innerHTML = events.length ? events.map(event => `
        <div class="event">
          <time>${esc(event.created_at)}</time>
          <span>${esc(event.level)}</span>
          <div>${esc(event.message)}</div>
        </div>
      `).join('') : '<div class="empty">No events recorded.</div>';
    }

    document.querySelector('#transfer-form').addEventListener('submit', async event => {
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
        formErrorEl.textContent = data.error || 'Create task failed.';
        formErrorEl.style.display = 'block';
        return;
      }
      formErrorEl.textContent = '';
      formErrorEl.style.display = 'none';
      selectedTaskId = data.task_id;
      await loadTasks();
    });

    document.querySelector('#refresh').addEventListener('click', loadTasks);
    loadTasks();
    setInterval(loadTasks, 3000);
  </script>
</body>
</html>'''
