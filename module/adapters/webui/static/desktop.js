/* TRMD WebUI - Desktop SPA Logic */

/* ====== View Switching ====== */
function switchView(view) {
  state.activeView = view;
  $$('.sidebar-nav-item').forEach(b => b.classList.remove('active'));
  const navBtn = document.querySelector('.sidebar-nav-item[data-nav="' + view + '"]');
  if (navBtn) navBtn.classList.add('active');

  $$('.view').forEach(v => v.classList.remove('active'));
  const viewEl = document.getElementById('view-' + view);
  if (viewEl) viewEl.classList.add('active');

  if (view === 'transfers') renderTasks();
  if (view === 'watches') loadWatches();
  if (view === 'downloads-uploads') { loadDownloadTypes(); loadOperations(); }
  if (view === 'settings') loadSettings();
  if (view === 'records') loadRecords();
  if (view === 'statistics') loadStatistics();
  if (view === 'media') loadMedia();
}

$$('[data-nav]').forEach(btn => btn.addEventListener('click', () => switchView(btn.dataset.nav)));

/* ====== Task List ====== */
async function loadTasks() {
  try {
    const data = await fetchJson('/api/tasks');
    state.tasks = data.tasks || [];
    renderTasks();
    updateStats();
  } catch(e) {
    if (e.error_code === 'auth_required') checkAuthStatus();
  }
}

function updateStats() {
  const stats = { total: state.tasks.length, running: 0, success: 0, failed: 0, failedItems: 0 };
  state.tasks.forEach(t => {
    if (t.status === 'running') stats.running++;
    if (t.status === 'success') stats.success++;
    if (t.status === 'failure') stats.failed++;
    if (t.failed_items) stats.failedItems += (t.failed_items || 0);
  });
  $('#stat-total').textContent = stats.total;
  $('#stat-success').textContent = stats.success;
  $('#stat-running').textContent = stats.running;
  $('#stat-failed').textContent = stats.failedItems;
  $('#metric-failed').textContent = stats.failedItems;
  $('#badge-transfers').textContent = stats.running || '';
  $('#badge-transfers').style.display = stats.running ? '' : 'none';
}

function renderTasks() {
  if (state.activeView !== 'transfers') return;
  const tbody = $('#tasks-tbody');
  const empty = $('#tasks-empty');
  if (!state.tasks.length) {
    tbody.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';
  tbody.innerHTML = state.tasks.map(task => {
    const isSelected = task.id === state.selectedTaskId;
    const progressPct = taskProgressPercent(task);
    return '<tr data-task-id="' + task.id + '" class="' + (isSelected ? 'selected' : '') + '">' +
      '<td class="font-semibold text-primary">#' + task.id + '</td>' +
      '<td>' + statusBadge(task.status) + '</td>' +
      '<td class="max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap text-xs" title="' + esc(task.source_link || '') + '">' + esc(task.source_link || '-') + '</td>' +
      '<td class="text-xs">' + esc(task.target_profile || task.target_link || '-') + '</td>' +
      '<td>' +
        (task.total_items > 0 ? (
          '<div class="flex items-center gap-2">' +
          '<span class="text-xs font-semibold">' + progressPct + '%</span>' +
          '<div class="flex-1 min-w-[60px]">' +
          '<div class="progress-bar"><div class="progress-fill" style="width:' + progressPct + '%"></div></div>' +
          '<span class="text-[11px] text-muted">' + taskCompletedLabel(task) + '</span>' +
          '</div></div>'
        ) : '<span class="text-muted text-xs">-</span>') +
      '</td>' +
      '<td>' + taskActions(task) + '</td>' +
      '</tr>';
  }).join('');

  $$('#tasks-tbody tr').forEach(row => {
    row.addEventListener('click', () => {
      const id = parseInt(row.dataset.taskId);
      state.selectedTaskId = id;
      renderTasks();
      loadTaskDetail(id);
    });
  });
}

function taskActions(task) {
  let actions = '';
  if (task.can_pause) {
    actions += '<button class="btn btn-sm" data-task-action="pause" data-task-id="' + task.id + '" title="' + t('tasks.pause') + '">⏸</button>';
  }
  if (task.can_resume) {
    actions += '<button class="btn btn-sm btn-primary" data-task-action="resume" data-task-id="' + task.id + '" title="' + t('tasks.resume') + '">▶</button>';
  }
  if (task.can_retry) {
    actions += '<button class="btn btn-sm btn-danger" data-task-action="retry" data-task-id="' + task.id + '" title="' + t('tasks.retryFailed') + '">↻</button>';
  }
  if (task.can_delete) {
    actions += '<button class="btn btn-sm btn-danger" data-task-action="delete" data-task-id="' + task.id + '" title="' + t('tasks.delete') + '">✕</button>';
  }
  return '<div class="flex gap-1">' + actions + '</div>';
}

/* task action delegation */
document.addEventListener('click', async function(e) {
  const btn = e.target.closest('[data-task-action]');
  if (!btn) return;
  e.stopPropagation();
  const taskId = parseInt(btn.dataset.taskId);
  const action = btn.dataset.taskAction;

  if (action === 'delete') {
    if (!confirm('确定删除任务 #' + taskId + '？')) return;
    try {
      await fetch('/api/tasks/' + taskId, { method: 'DELETE' });
      state.tasks = state.tasks.filter(t => t.id !== taskId);
      if (state.selectedTaskId === taskId) state.selectedTaskId = null;
      renderTasks();
      $('#task-detail').innerHTML = '<div class="p-8 text-center text-muted text-sm">' + t('items.selectTask') + '</div>';
    } catch(e) { /* ignore */ }
    return;
  }

  const actionMap = { pause: 'pause', resume: 'resume', retry: 'retry-failed' };
  try {
    await postJson('/api/tasks/' + taskId + '/' + actionMap[action], {});
    await loadTasks();
  } catch(e) { /* ignore */ }
});

/* ====== Task Detail ====== */
async function loadTaskDetail(taskId) {
  const container = $('#task-detail');
  container.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';

  try {
    const data = await fetchJson('/api/tasks/' + taskId + '/summary');
    state.itemData[taskId] = data;
    state.eventData[taskId] = data.events || [];
    state.itemPages = { running: 1, success: 1, skipped: 1, failure: 1 };
    state.activeItemStatus = 'running';
    renderTaskDetail(taskId, data);
  } catch(e) {
    container.innerHTML = '<div class="p-8 text-center text-muted text-sm">加载失败</div>';
  }
}

function renderTaskDetail(taskId, data) {
  const task = state.tasks.find(t => t.id === taskId);
  const summary = data.summary || {};
  const detailEl = $('#task-detail');

  let html = '<div class="panel-header">' +
    '<h3>任务 #' + taskId + ' · ' + esc(task ? (task.source_link || '') : '') + ' → ' + esc(task ? (task.target_profile || task.target_link || '') : '') + '</h3>' +
    '<div class="panel-tabs">' +
      '<button class="panel-tab active" data-item-tab="running">' + t('items.tab.running') + ' (' + (summary.running || 0) + ')</button>' +
      '<button class="panel-tab" data-item-tab="success">' + t('items.tab.success') + ' (' + (summary.success || 0) + ')</button>' +
      '<button class="panel-tab" data-item-tab="skipped">' + t('items.tab.skipped') + ' (' + (summary.skipped || 0) + ')</button>' +
      '<button class="panel-tab" data-item-tab="failure">' + t('items.tab.failure') + ' (' + (summary.failed || 0) + ')</button>' +
    '</div>' +
    '</div>' +
    '<div id="task-items-body" class="overflow-auto max-h-[300px]"></div>' +
    '<div class="flex items-center justify-between px-[18px] py-2 pb-[14px] gap-3 flex-wrap" id="task-items-pagination"></div>';

  detailEl.innerHTML = html;
  loadTaskItems(taskId, 'running');

  /* tab switching */
  $$('#task-detail [data-item-tab]').forEach(btn => {
    btn.addEventListener('click', function() {
      $$('#task-detail [data-item-tab]').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      state.activeItemStatus = this.dataset.itemTab;
      loadTaskItems(taskId, this.dataset.itemTab);
    });
  });
}

async function loadTaskItems(taskId, status) {
  const page = state.itemPages[status] || 1;
  const body = $('#task-items-body');
  const pagEl = $('#task-items-pagination');
  body.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';

  try {
    const data = await fetchJson('/api/tasks/' + taskId + '?items_limit=50&items_offset=' + ((page - 1) * 50) + '&item_status=' + encodeURIComponent(status));
    const items = data.items || [];
    state.itemData[taskId] = data;

    if (!items.length) {
      body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + t('items.empty.' + status) + '</div>';
    } else {
      body.innerHTML = '<table class="data-table"><thead><tr>' +
        '<th>文件</th><th>大小</th><th>来源</th><th>目标</th><th>状态</th>' +
        '</tr></thead><tbody>' +
        items.map(item => '<tr>' +
          '<td class="text-xs">' + esc(item.file_name || item.local_path || '-') + '</td>' +
          '<td class="text-xs">' + fmtSize(item.file_size) + '</td>' +
          '<td class="text-xs">' + esc(item.source_link || '-') + '</td>' +
          '<td class="text-xs">' + esc(item.target_path || '-') + '</td>' +
          '<td>' + statusBadge(item.status) + '</td>' +
          '</tr>').join('') +
        '</tbody></table>';
    }

    const statusToSummaryKey = { running: 'running', success: 'success', skipped: 'skipped', failure: 'failed' };
    const summaryKey = statusToSummaryKey[status] || status;
    const totalItems = state.itemData[taskId] ? (state.itemData[taskId].summary || {})[summaryKey] || 0 : 0;
    const totalPages = Math.max(1, Math.ceil(totalItems / 50));
    pagEl.innerHTML =
      '<span class="text-xs text-muted">第 ' + page + ' / ' + totalPages + ' 页</span>' +
      '<div class="flex gap-2">' +
        '<button class="btn btn-sm" ' + (page <= 1 ? 'disabled' : '') + ' id="items-prev-page">' + t('items.page.previous') + '</button>' +
        '<button class="btn btn-sm" ' + (page >= totalPages ? 'disabled' : '') + ' id="items-next-page">' + t('items.page.next') + '</button>' +
      '</div>';

    const prevBtn = $('#items-prev-page');
    const nextBtn = $('#items-next-page');
    if (prevBtn) prevBtn.addEventListener('click', () => {
      state.itemPages[state.activeItemStatus] = Math.max(1, page - 1);
      loadTaskItems(taskId, state.activeItemStatus);
    });
    if (nextBtn) nextBtn.addEventListener('click', () => {
      state.itemPages[state.activeItemStatus] = page + 1;
      loadTaskItems(taskId, state.activeItemStatus);
    });
  } catch(e) {
    body.innerHTML = '<div class="p-8 text-center text-muted text-sm">加载失败</div>';
  }
}

/* ====== Transfer Form ====== */
$('#transfer-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn = $('#transfer-submit');
  const btnText = btn.querySelector('span');
  const originalText = btnText.textContent;
  const notice = $('#transfer-notice');

  btn.disabled = true;
  btnText.textContent = t('form.creatingTransferShort');
  notice.className = 'text-xs text-muted mt-2';
  notice.textContent = t('form.creatingTransfer');
  notice.style.display = '';

  const fd = new FormData(this);
  const payload = {
    source_link: fd.get('source_link') || '',
    target_link: fd.get('target_link') || '',
    target_profile: fd.get('target_profile') || 'pikpak',
    start_id: fd.get('start_id') ? Number(fd.get('start_id')) : null,
    end_id: fd.get('end_id') ? Number(fd.get('end_id')) : null,
    include_comment: Boolean(fd.get('include_comment')),
  };

  try {
    const data = await postJson('/api/tasks', payload);
    state.selectedTaskId = data.task_id;
    notice.className = 'text-xs text-success mt-2';
    notice.textContent = t('form.createSuccess');
    await loadTasks();
  } catch(err) {
    notice.className = 'text-xs text-danger mt-2';
    notice.textContent = translateApiError(err, 'form.createFailed');
  } finally {
    btn.disabled = false;
    btnText.textContent = originalText;
  }
});

/* ====== Polling ====== */
function hasActiveTasks() {
  return state.tasks.some(t => t.status === 'pending' || t.status === 'running');
}

function startPolling() {
  if (state.taskPollTimer) return;
  const fast = 3000, slow = 15000;
  let interval = fast, lastPoll = 0;

  async function poll() {
    if (document.hidden) { state.taskPollTimer = setTimeout(poll, interval); return; }
    const now = Date.now();
    if (now - lastPoll < interval - 500) { state.taskPollTimer = setTimeout(poll, interval); return; }
    lastPoll = now;
    try { await loadTasks(); } catch(e) {}
    interval = hasActiveTasks() ? fast : slow;
    state.taskPollTimer = setTimeout(poll, interval);
  }
  poll();
}

document.addEventListener('visibilitychange', () => {
  if (!document.hidden && state.taskPollTimer) {
    clearTimeout(state.taskPollTimer);
    state.taskPollTimer = null;
    startPolling();
  }
});

/* ====== Auth Flow ====== */
let authPollTimer = null, authStep = '';

function showLoginStep(step) {
  authStep = step;
  ['login-form-phone','login-form-code','login-form-password','login-form-recovery','login-form-signup','login-form-done'].forEach(id => {
    const el = document.getElementById(id); if (el) el.style.display = 'none';
  });
  const el = document.getElementById('login-form-' + step);
  if (el) el.style.display = '';
  const container = document.getElementById('login-container');
  if (container) container.style.display = 'flex';
  const errEl = document.getElementById('login-error');
  if (errEl) errEl.classList.remove('visible');
}

function hideLogin() {
  const container = document.getElementById('login-container');
  if (container) container.style.display = 'none';
  if (authPollTimer) { clearInterval(authPollTimer); authPollTimer = null; }
}

function showLoginError(msg) {
  const el = document.getElementById('login-error');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
}

async function checkAuthStatus() {
  try {
    const resp = await fetch('/api/auth/status');
    if (resp.status === 401) return;
    const state = await resp.json();
    if (!state || !state.step) return;
    switch (state.step) {
      case 'pending': hideLogin(); return;
      case 'done': case 'none':
        hideLogin();
        loadTasks();
        startPolling();
        return;
      case 'phone': showLoginStep('phone'); if (state.error) showLoginError(state.error); break;
      case 'code':
        showLoginStep('code');
        if (state.code_type) {
          const desc = document.getElementById('login-code-desc');
          if (desc) desc.textContent = '验证码已通过「' + state.code_type + '」发送';
        }
        if (state.error) showLoginError(state.error);
        break;
      case 'password':
        showLoginStep('password');
        const hintEl = document.getElementById('login-password-hint-text');
        if (hintEl && state.hint) hintEl.textContent = state.hint;
        if (state.error) showLoginError(state.error);
        break;
      case 'recovery_code':
        showLoginStep('recovery');
        if (state.message) { const d = document.getElementById('login-recovery-desc'); if (d) d.textContent = state.message; }
        if (state.error) showLoginError(state.error);
        break;
      case 'signup': showLoginStep('signup'); if (state.error) showLoginError(state.error); break;
      case 'error': if (state.error) showLoginError(state.error); break;
    }
  } catch(e) {}
}

async function submitAuth(payload) {
  const btn = document.querySelector('.login-submit');
  if (btn) btn.disabled = true;
  showLoginError('');
  try {
    await fetch('/api/auth/submit', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    await new Promise(r => setTimeout(r, 500));
    await checkAuthStatus();
  } catch(e) {
    showLoginError('提交失败，请重试');
  } finally {
    if (btn) btn.disabled = false;
  }
}

/* auth event bindings */
document.getElementById('login-btn-phone')?.addEventListener('click', () => {
  const phone = document.getElementById('login-phone').value.trim();
  if (!phone) { showLoginError('请输入电话号码'); return; }
  if (!phone.startsWith('+')) { showLoginError('电话号码需以 +地区号开头'); return; }
  submitAuth({ phone });
});

document.getElementById('login-btn-code')?.addEventListener('click', () => {
  const code = document.getElementById('login-code').value.trim();
  if (!code) { showLoginError('请输入验证码'); return; }
  submitAuth({ code });
});

document.getElementById('login-btn-back')?.addEventListener('click', () => {
  showLoginStep('phone');
  document.getElementById('login-code').value = '';
});

document.getElementById('login-btn-password')?.addEventListener('click', () => {
  submitAuth({ password: document.getElementById('login-password').value });
});

document.getElementById('login-btn-back-pwd')?.addEventListener('click', () => {
  showLoginStep('code');
  document.getElementById('login-password').value = '';
});

document.getElementById('login-btn-recovery')?.addEventListener('click', () => {
  const code = document.getElementById('login-recovery').value.trim();
  if (!code) { showLoginError('请输入恢复代码'); return; }
  submitAuth({ recovery_code: code });
});

document.getElementById('login-btn-back-recovery')?.addEventListener('click', () => {
  showLoginStep('password');
  document.getElementById('login-recovery').value = '';
});

document.getElementById('login-btn-signup')?.addEventListener('click', () => {
  const first = document.getElementById('login-first-name').value.trim();
  if (!first) { showLoginError('请输入名字'); return; }
  submitAuth({ first_name: first, last_name: document.getElementById('login-last-name').value.trim() });
});

document.getElementById('login-phone')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('login-btn-phone').click();
});

document.getElementById('login-code')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('login-btn-code').click();
});

/* ====== Language ====== */
$('#language-select').addEventListener('change', e => {
  state.lang = e.target.value;
  localStorage.setItem('trmd-lang', state.lang);
  applyLanguageAndRefresh();
});

/* ====== Refresh ====== */
$('#refresh').addEventListener('click', () => {
  loadTasks();
  if (state.activeView === 'records') loadRecords();
  if (state.activeView === 'settings') loadSettings();
  if (state.activeView === 'watches') loadWatches();
  if (state.activeView === 'statistics') loadStatistics();
  if (state.activeView === 'downloads-uploads') loadOperations();
});

/* ====== Logout ====== */
$('#btn-logout').addEventListener('click', async () => {
  await fetch('/api/auth/logout', { method: 'POST' });
  window.location.reload();
});

/* ====== Records ====== */
async function loadRecords() {
  const tbody = $('#records-tbody');
  const empty = $('#records-empty');
  try {
    const data = await fetchJson('/api/download-records');
    const records = data.records || [];
    if (!records.length) {
      tbody.innerHTML = '';
      empty.style.display = '';
      return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = records.map(r => '<tr>' +
      '<td class="text-xs font-mono text-muted">' + esc(String(r.source_chat_id || '-')) + '</td>' +
      '<td class="text-xs font-mono text-muted">' + esc(String(r.source_message_id || '-')) + '</td>' +
      '<td class="text-xs max-w-[200px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(r.file_path || r.file_name || '-') + '</td>' +
      '<td class="text-xs">' + fmtSize(r.file_size) + '</td>' +
      '<td class="text-xs text-muted">' + fmtTime(r.updated_at) + '</td>' +
      '</tr>').join('');
  } catch(e) {}
}

/* ====== Watches ====== */
async function loadWatches() {
  try {
    const data = await fetchJson('/api/watches');
    state.watches = data.watches || [];
    renderWatches();
    updateWatchBadge();
  } catch(e) {}
}

function updateWatchBadge() {
  const count = (state.watches || []).filter(w => w.status !== 'paused').length;
  $('#badge-watches').textContent = count || '';
  $('#badge-watches').style.display = count ? '' : 'none';
}

function renderWatches() {
  if (state.activeView !== 'watches') return;
  const tbody = $('#watches-tbody');
  const empty = $('#watches-empty');
  const watches = state.watches || [];
  if (!watches.length) {
    tbody.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';
  tbody.innerHTML = watches.map(w => {
    const typeLabel = w.type === 'download' ? t('watches.download') : t('watches.forward');
    const typeCls = w.type === 'download' ? 'badge-success' : 'badge-running';
    const statusCls = w.status === 'paused' ? 'badge-paused' : 'badge-success';
    const statusLabel = w.status === 'paused' ? t('status.paused') : '● ' + t('status.running');
    const eventCount = w.event_count || 0;
    const eventBadge = w.type === 'forward' && eventCount ? ' <span class="badge badge-muted ml-1">' + eventCount + '</span>' : '';
    const sanitized = sanitizeWatchId(w.id);
    const rowAttrs = w.type === 'forward' ? ' class="watch-row" data-watch-id="' + esc(w.id) + '"' : '';
    const eventsRow = w.type === 'forward' ?
      '<tr class="watch-events-row" id="watch-events-' + sanitized + '">' +
      '<td colspan="6"><div class="watch-events-panel" id="watch-events-panel-' + sanitized + '"></div></td>' +
      '</tr>' : '';
    return '<tr' + rowAttrs + '>' +
      '<td><span class="badge ' + typeCls + '">' + typeLabel + '</span></td>' +
      '<td class="text-xs max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap font-mono text-muted">' + esc(w.source_link || '-') + '</td>' +
      '<td class="text-xs">' + esc(w.target_link || '本地') + '</td>' +
      '<td><span class="badge ' + statusCls + '">' + statusLabel + '</span>' + eventBadge + '</td>' +
      '<td class="text-xs font-semibold">' + eventCount + '</td>' +
      '<td><div class="flex gap-1">' +
        (w.type === 'forward' ? '<button class="btn btn-sm" data-edit-watch="' + esc(w.id) + '">✎</button>' : '') +
        '<button class="btn btn-sm btn-danger" data-delete-watch="' + esc(w.id) + '">✕</button>' +
      '</div></td>' +
      '</tr>' + eventsRow;
  }).join('');
}

/* ====== Watch Events (expandable forwarding log) ====== */
function sanitizeWatchId(id) {
  return (id || '').replace(/:/g, '_');
}

document.addEventListener('click', function(e) {
  const row = e.target.closest('.watch-row');
  if (!row) return;
  if (e.target.closest('button, a')) return;
  toggleWatchEvents(row.dataset.watchId);
});

function toggleWatchEvents(watchId) {
  const sanitized = sanitizeWatchId(watchId);
  const row = document.getElementById('watch-events-' + sanitized);
  if (!row) return;
  const isOpen = row.classList.contains('open');
  if (isOpen) {
    row.classList.remove('open');
    return;
  }
  row.classList.add('open');
  loadWatchEvents(watchId, 0);
}

async function loadWatchEvents(watchId, offset) {
  const sanitized = sanitizeWatchId(watchId);
  const panel = document.getElementById('watch-events-panel-' + sanitized);
  if (!panel) return;
  if (offset === 0) panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.eventLoading')) + '</div>';
  try {
    const res = await fetch('/api/watches/' + encodeURIComponent(watchId) + '/events?limit=50&offset=' + offset);
    const data = await res.json();
    if (!res.ok) { panel.innerHTML = '<div class="watch-event-item">' + esc(data.error || t('form.requestFailed')) + '</div>'; return; }
    const items = data.events || [];
    if (offset === 0) panel.innerHTML = '';
    if (!items.length && offset === 0) {
      panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.noEvents')) + '</div>';
      return;
    }
    items.forEach(evt => {
      const time = new Date(evt.created_at).toLocaleString();
      const statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
      const badgeCls = evt.status === 'success' ? 'badge-success' : 'badge-warning';
      const div = document.createElement('div');
      div.className = 'watch-event-item';
      div.innerHTML = '<span class="watch-event-time">' + esc(time) + '</span>'
        + '<span class="watch-event-badge"><span class="badge ' + badgeCls + '">' + esc(statusLabel) + '</span></span>'
        + '<span class="watch-event-info">' + esc(evt.message) + ' ' + esc(t('watches.source')) + ': #' + esc(String(evt.source_message_id || '')) + ' → ' + esc(t('watches.target')) + ': ' + esc(evt.target_link || evt.target_chat_id || '') + '</span>';
      panel.appendChild(div);
    });
    if (data.has_more) {
      const btn = document.createElement('button');
      btn.className = 'watch-events-load-more btn btn-sm';
      btn.textContent = t('watches.loadMore');
      btn.onclick = function() { loadWatchEvents(watchId, offset + items.length); };
      panel.appendChild(btn);
    }
  } catch (e) {
    panel.innerHTML = '<div class="watch-event-item">' + esc(t('form.requestFailed')) + '</div>';
  }
}

/* watch form */
$('#watch-download-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  const links = fd.get('source_links').split('\n').map(l => l.trim()).filter(Boolean);
  try {
    await postJson('/api/watches', { type: 'download', source_links: links });
    await loadWatches();
    this.reset();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

$('#watch-forward-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  try {
    await postJson('/api/watches', {
      type: 'forward',
      source_link: fd.get('source_link'),
      target_link: fd.get('target_link'),
      include_comment: Boolean(fd.get('include_comment')),
    });
    await loadWatches();
    this.reset();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

document.addEventListener('click', async function(e) {
  const delBtn = e.target.closest('[data-delete-watch]');
  if (delBtn) {
    if (!confirm('确定移除这个监听？')) return;
    try {
      await fetch('/api/watches/' + encodeURIComponent(delBtn.dataset.deleteWatch), { method: 'DELETE' });
      await loadWatches();
    } catch(err) {}
  }
  const editBtn = e.target.closest('[data-edit-watch]');
  if (editBtn) {
    openEditWatchModal(editBtn.dataset.editWatch);
  }
});

function openEditWatchModal(watchId) {
  const watch = (state.watches || []).find(w => w.id === watchId);
  if (!watch) return;
  $('#edit-watch-id').value = watch.id;
  $('#edit-watch-source').value = watch.source_link || '';
  $('#edit-watch-target').value = watch.target_link || '';
  $('#edit-watch-comment').checked = watch.include_comment || false;
  $('#watch-edit-overlay').classList.add('open');
}

function closeEditWatchModal() {
  $('#watch-edit-overlay').classList.remove('open');
}

$('#watch-edit-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeEditWatchModal();
});

$('#watch-edit-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  const watchId = fd.get('id');
  try {
    await fetch('/api/watches/' + encodeURIComponent(watchId), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_link: fd.get('source_link'),
        target_link: fd.get('target_link'),
        include_comment: Boolean(fd.get('include_comment')),
      }),
    });
    closeEditWatchModal();
    await loadWatches();
  } catch(err) {
    alert(translateApiError(err, 'form.requestFailed'));
  }
});

/* ====== Downloads & Uploads ====== */

/* download type checkboxes — populate from the unified settings schema */
async function loadDownloadTypes() {
  const grid = $('#dl-download-type-grid');
  if (!grid) return;
  if (!state.settings || !state.settingsSchema) {
    try {
      const data = await fetchJson('/api/settings');
      state.settings = data.settings || {};
      state.settingsSchema = data.schema || {};
      state.settingsModel = data.settings_model || {};
    } catch(e) {}
  }
  const types = optionValues((state.settingsModel.options || {}).download_type || (state.settingsSchema || {}).download_type || []);
  const selected = (state.settings && state.settings.user && state.settings.user.download_type) || types;
  grid.innerHTML = types.map(t =>
    '<label class="flex items-center gap-2 text-sm text-text cursor-pointer">' +
      '<input type="checkbox" name="download_type" value="' + t + '" class="w-4 h-4"' + (selected.includes(t) ? ' checked' : '') + '>' +
      '<span>' + t + '</span>' +
    '</label>'
  ).join('');
}

/* Channel Download form */
$('#channel-download-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  const payload = {
    chat_link: fd.get('chat_link'),
    download_type: fd.getAll('download_type'),
    keywords: fd.get('keywords') ? fd.get('keywords').split(',').map(k => k.trim()).filter(Boolean) : [],
    include_comment: Boolean(fd.get('include_comment')),
  };
  const startDate = fd.get('start_date');
  const endDate = fd.get('end_date');
  if (startDate || endDate) {
    payload.date_range = {
      start_date: startDate ? new Date(startDate).getTime() / 1000 : null,
      end_date: endDate ? new Date(endDate).getTime() / 1000 : null,
    };
  }
  try {
    await postJson('/api/channel-downloads', payload);
    alert(t('dl.accepted'));
    this.reset();
    loadDownloadTypes();
    loadOperations();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

/* Upload form */
$('#upload-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  try {
    await postJson('/api/uploads', {
      path: fd.get('path'),
      target_link: fd.get('target_link'),
      recursive: Boolean(fd.get('recursive')),
    });
    alert(t('dl.uploadAccepted'));
    this.reset();
    loadOperations();
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

/* Operations history */
async function loadOperations() {
  if (state.activeView !== 'downloads-uploads') return;
  const tbody = $('#dl-operations-tbody');
  const empty = $('#dl-operations-empty');
  try {
    const data = await fetchJson('/api/operations');
    const ops = data.operations || [];
    if (!ops.length) {
      tbody.innerHTML = '';
      empty.style.display = '';
      return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = ops.map(op => {
      const typeLabel = op.type === 'channel_download' ? t('dl.typeDownload') : t('dl.typeUpload');
      const payload = op.payload || {};
      const detail = op.type === 'channel_download'
        ? (payload.chat_link || '-')
        : (payload.path || '-');
      return '<tr>' +
        '<td class="font-mono text-xs text-muted">' + esc(String(op.id || '-')) + '</td>' +
        '<td><span class="badge ' + (op.type === 'channel_download' ? 'badge-running' : 'badge-success') + '">' + esc(typeLabel) + '</span></td>' +
        '<td class="text-xs max-w-[220px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(detail) + '</td>' +
        '<td>' + statusBadge(op.status) + '</td>' +
        '<td class="text-xs text-danger max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(op.error_message || '') + '">' + esc(op.error_message || '-') + '</td>' +
        '<td class="text-xs text-muted">' + fmtTime(op.created_at) + '</td>' +
        '</tr>';
    }).join('');
  } catch(e) {}
}

$('#dl-history-refresh')?.addEventListener('click', () => loadOperations());

/* poll operations when active */
setInterval(() => {
  if (state.activeView === 'downloads-uploads') loadOperations();
}, 10000);

/* ====== Statistics ====== */
async function loadStatistics() {
  try {
    const data = await fetchJson('/api/statistics');
    const tables = data.tables || {};
    const tbody = $('#statistics-tbody');
    const rows = [
      { key: 'link', label: t('statistics.link') },
      { key: 'count', label: t('statistics.count') },
      { key: 'upload', label: t('statistics.upload') },
    ];
    tbody.innerHTML = rows.map(r => {
      const tbl = tables[r.key] || {};
      return '<tr>' +
        '<td class="font-semibold">' + r.label + '</td>' +
        '<td>' + (tbl.available ? '<span class="badge badge-success">' + t('statistics.yes') + '</span>' : '<span class="badge badge-paused">' + t('statistics.no') + '</span>') + '</td>' +
        '<td>' + (tbl.rows || 0) + '</td>' +
        '<td>' + (tbl.available ? '<button class="btn btn-sm btn-primary" data-export="' + r.key + '">' + t('statistics.export' + r.key.charAt(0).toUpperCase() + r.key.slice(1)) + '</button>' : '-') + '</td>' +
        '</tr>';
    }).join('');
  } catch(e) {}
}

document.addEventListener('click', async function(e) {
  const exportBtn = e.target.closest('[data-export]');
  if (exportBtn) {
    try {
      await postJson('/api/tables/export', { table_type: exportBtn.dataset.export });
      alert(t('statistics.exported'));
    } catch(err) {
      alert(translateApiError(err, 'form.requestFailed'));
    }
  }
});

/* ====== Settings ====== */
async function loadSettings() {
  try {
    const data = await fetchJson('/api/settings');
    state.settings = data.settings || {};
    state.settingsSchema = data.schema || {};
    state.settingsModel = data.settings_model || {};
    renderSettings();
  } catch(e) {}
}

function renderSettings() {
  if (state.activeView !== 'settings') return;
  const s = state.settings || {};
  const su = s.user || {};
  const sg = s.global || {};

  /* fill paths */
  setFieldVal('user.save_directory', su.save_directory);
  setFieldVal('user.temp_directory', su.temp_directory);
  setFieldVal('user.session_directory', su.session_directory);
  setFieldVal('user.max_tasks.download', su.max_tasks?.download);
  setFieldVal('user.max_tasks.upload', su.max_tasks?.upload);
  setFieldVal('user.max_retries.download', su.max_retries?.download);
  setFieldVal('user.max_retries.upload', su.max_retries?.upload);
  setFieldVal('global.target_profiles.pikpak.max_file_size', sg.target_profiles?.pikpak?.max_file_size);

  /* behavior */
  setCheckboxVal('global.notice', sg.notice);
  setCheckboxVal('user.is_shutdown', su.is_shutdown);
  setCheckboxVal('global.upload.download_upload', sg.upload?.download_upload);
  setCheckboxVal('global.upload.delete', sg.upload?.delete);
  setFieldVal('global.upload.pending_limit', sg.upload?.pending_limit);

  /* archive */
  setCheckboxVal('global.target_profiles.pikpak.archive.enable', sg.target_profiles?.pikpak?.archive?.enable);
  setFieldVal('global.target_profiles.pikpak.archive.remote', sg.target_profiles?.pikpak?.archive?.remote);
  setFieldVal('global.target_profiles.pikpak.archive.source_directory', sg.target_profiles?.pikpak?.archive?.source_directory);
  setFieldVal('global.target_profiles.pikpak.archive.root_directory', sg.target_profiles?.pikpak?.archive?.root_directory);
  setFieldVal('global.target_profiles.pikpak.archive.poll_seconds', sg.target_profiles?.pikpak?.archive?.poll_seconds);
  setFieldVal('global.target_profiles.pikpak.archive.poll_interval_seconds', sg.target_profiles?.pikpak?.archive?.poll_interval_seconds);
  setFieldVal('global.target_profiles.pikpak.archive.match_window_seconds', sg.target_profiles?.pikpak?.archive?.match_window_seconds);

  /* sensitive */
  setSensitiveVal('user.api_id', su.api_id);
  setSensitiveVal('user.api_hash', su.api_hash);
  setSensitiveVal('user.bot_token', su.bot_token);
  setSensitiveVal('user.proxy.password', su.proxy?.password);

  /* download types */
  renderCheckboxGrid('download-type-grid', 'user.download_type', su.download_type || [], (state.settingsModel.options || {}).download_type || state.settingsSchema.download_type);
  /* forward types */
  renderCheckboxGrid('forward-type-grid', 'global.forward_type', sg.forward_type || [], (state.settingsModel.options || {}).forward_type || state.settingsSchema.forward_type);
  /* message filter */
  renderMessageFilter(sg.message_filter || {});
  /* exports */
  setCheckboxVal('global.export_table.link', sg.export_table?.link);
  setCheckboxVal('global.export_table.count', sg.export_table?.count);
  setCheckboxVal('global.export_table.upload', sg.export_table?.upload);
}

function setFieldVal(name, val) {
  const el = document.querySelector('[name="' + name + '"]');
  if (el) el.value = val ?? '';
}

function setCheckboxVal(name, val) {
  const el = document.querySelector('[name="' + name + '"]');
  if (el) el.checked = Boolean(val);
}

function setSensitiveVal(name, val) {
  const el = document.querySelector('[name="' + name + '"]');
  if (!el) return;
  if (val && typeof val === 'object' && val.configured) {
    el.placeholder = t('settings.secretConfigured');
    el.value = '';
  } else {
    el.value = val || '';
  }
}

function renderCheckboxGrid(containerId, inputName, selected, options) {
  const types = normalizeOptionList(options || ['video','photo','audio','voice','animation','document','video_note']);
  const container = document.getElementById(containerId);
  if (!container) return;
  var sel;
  if (Array.isArray(selected)) {
    sel = selected;
  } else if (selected && typeof selected === 'object') {
    // 兼容 dict 格式 {video: true, photo: false, ...}
    sel = Object.entries(selected).filter(function(e) { return e[1]; }).map(function(e) { return e[0]; });
  } else {
    sel = [];
  }
  container.innerHTML = types.map(function(t) {
    const value = typeof t === 'string' ? t : t.value;
    const label = typeof t === 'string' ? t : (t.label || t.value);
    return '<label class="flex items-center gap-2 text-sm text-text cursor-pointer">' +
      '<input type="checkbox" name="' + inputName + '" value="' + esc(value) + '" class="w-4 h-4"' + (sel.indexOf(value) >= 0 ? ' checked' : '') + '>' +
      '<span>' + esc(label) + '</span>' +
    '</label>';
  }).join('');
}

function normalizeOptionList(options) {
  if (Array.isArray(options)) {
    return options.map(function(option) {
      if (option && typeof option === 'object') {
        return {value: String(option.value), label: String(option.label || option.value)};
      }
      return {value: String(option), label: String(option)};
    });
  }
  return Object.keys(options || {}).map(function(key) {
    return {value: String(key), label: String(options[key] || key)};
  });
}

function renderMessageFilter(mf) {
  setCheckboxVal('global.message_filter.enabled', mf.enabled);
  /* media types */
  renderCheckboxGrid('filter-media-grid', 'global.message_filter.media_types', mf.media_types || [], (state.settingsModel.options || {}).message_filter_media_types || (state.settingsSchema.message_filter || {}).media_types);
  /* date range */
  setCheckboxVal('global.message_filter.date_range.enabled', mf.date_range?.enabled);
  setFieldVal('global.message_filter.date_range.start_date', mf.date_range?.start_date);
  setFieldVal('global.message_filter.date_range.end_date', mf.date_range?.end_date);
  /* keywords */
  setCheckboxVal('global.message_filter.keywords.enabled', mf.keywords?.enabled);
  setFieldVal('global.message_filter.keywords.words', (mf.keywords?.words || []).join(','));
}

$('#settings-save').addEventListener('click', async function() {
  const notice = $('#settings-notice');
  const payload = buildSettingsPayload();

  try {
    await patchJson('/api/settings', payload);
    notice.className = 'text-xs text-success mt-2';
    notice.textContent = t('settings.saved');
    notice.style.display = '';
    setTimeout(() => { notice.style.display = 'none'; }, 3000);
  } catch(err) {
    notice.className = 'text-xs text-danger mt-2';
    notice.textContent = translateApiError(err, 'form.requestFailed');
    notice.style.display = '';
  }
});

function buildSettingsPayload() {
  /* rebuild full settings structure from form */
  const payload = { user: {}, global: {} };

  /* user settings */
  $$('[name^="user."]').forEach(el => {
    if (!el.name) return;
    if (el.name === 'user.download_type') return;
    const parts = el.name.split('.');
    if (parts[0] !== 'user') return;
    if (el.type === 'checkbox') {
      setNested(payload, parts, el.checked);
    } else if (el.value !== '') {
      setNested(payload, parts, el.value);
    }
  });

  /* global settings */
  $$('[name^="global."]').forEach(el => {
    if (!el.name) return;
    if (el.name === 'global.forward_type' || el.name === 'global.message_filter.media_types') return;
    const parts = el.name.split('.');
    if (parts[0] !== 'global') return;
    if (el.type === 'checkbox') {
      setNested(payload, parts, el.checked);
    } else if (el.value !== '') {
      setNested(payload, parts, el.value);
    }
  });

  /* download types */
  const downloadTypes = Array.from($$('input[name="user.download_type"]:checked')).map(cb => cb.value);
  setNested(payload, ['user', 'download_type'], downloadTypes);

  /* forward types */
  const forwardTypes = Array.from($$('input[name="global.forward_type"]:checked')).map(cb => cb.value);
  const forwardTypeOptions = normalizeOptionList((state.settingsModel.options || {}).forward_type || state.settingsSchema.forward_type || []);
  const allForwardTypes = forwardTypeOptions.length ? forwardTypeOptions.map(function(option) { return option.value; }) : forwardTypes;
  const forwardTypesDict = {};
  allForwardTypes.forEach(function(t) { forwardTypesDict[t] = forwardTypes.indexOf(t) >= 0; });
  setNested(payload, ['global', 'forward_type'], forwardTypesDict);

  /* filter media types — 构建 {video: true, photo: false, ...} dict 格式与后端一致 */
  const mediaTypeOptions = normalizeOptionList((state.settingsModel.options || {}).message_filter_media_types || (state.settingsSchema.message_filter || {}).media_types || []);
  const allMediaTypes = mediaTypeOptions.length ? mediaTypeOptions.map(function(option) { return option.value; }) : ['video','photo','audio','document','voice','text','animation','video_note'];
  const checkedMedia = Array.from($$('input[name="global.message_filter.media_types"]:checked')).map(function(cb) { return cb.value; });
  const mediaTypesDict = {};
  allMediaTypes.forEach(function(t) { mediaTypesDict[t] = checkedMedia.indexOf(t) >= 0; });
  setNested(payload, ['global', 'message_filter', 'media_types'], mediaTypesDict);

  /* filter keywords */
  const kwInput = document.querySelector('[name="global.message_filter.keywords.words"]');
  if (kwInput && kwInput.value) {
    setNested(payload, ['global', 'message_filter', 'keywords', 'words'], kwInput.value.split(',').map(k => k.trim()).filter(Boolean));
  }

  return payload;
}

function setNested(obj, parts, value) {
  let current = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    if (!current[parts[i]]) current[parts[i]] = {};
    current = current[parts[i]];
  }
  current[parts[parts.length - 1]] = value;
}

/* ====== Media Management ====== */
let mediaScanResult = null;

async function loadMedia() {
  try {
    const data = await fetchJson('/api/media/scan');
    mediaScanResult = data;
    renderMediaResult(data);
    loadCleanupLogs();
  } catch(e) {}
}

function renderMediaResult(data) {
  const container = $('#media-result');
  if (!data) { container.style.display = 'none'; return; }
  container.style.display = '';

  const ti = data.transfer_items || {};
  const orph = data.orphan_files || {};

  /* summary */
  $('#media-summary').innerHTML =
    '<div><strong class="text-xl font-bold text-primary">' + (data.total_count || 0) + '</strong><span class="text-xs text-muted ml-1">' + t('media.totalFiles') + '</span></div>' +
    '<div><strong class="text-xl font-bold text-primary">' + fmtSize(data.total_size || 0) + '</strong><span class="text-xs text-muted ml-1">' + t('media.totalSize') + '</span></div>' +
    '<div><strong class="text-xl font-bold text-primary">' + (data.retention_days || 7) + '</strong><span class="text-xs text-muted ml-1">' + t('media.retentionDays') + '</span></div>';

  /* transfer items */
  const items = ti.items || [];
  const itemsSection = $('#media-items-section');
  if (items.length) {
    itemsSection.style.display = '';
    $('#media-items-tbody').innerHTML = items.map(item => '<tr>' +
      '<td><input type="checkbox" class="media-cb" data-type="item" data-id="' + item.item_id + '"></td>' +
      '<td class="text-xs max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(item.local_path || '') + '">' + esc(item.file_name || item.local_path || '-') + '</td>' +
      '<td class="text-xs text-right">' + fmtSize(item.file_size) + '</td>' +
      '<td class="text-center">' + statusBadge(item.status || '') + '</td>' +
      '<td class="text-xs max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(item.source_link || '-') + '</td>' +
      '</tr>').join('');
  } else {
    itemsSection.style.display = 'none';
  }

  /* orphans */
  const files = orph.files || [];
  const orphansSection = $('#media-orphans-section');
  if (files.length) {
    orphansSection.style.display = '';
    $('#media-orphans-tbody').innerHTML = files.map(f => '<tr>' +
      '<td><input type="checkbox" class="media-cb" data-type="orphan" data-path="' + esc(f.path) + '"></td>' +
      '<td class="text-xs max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(f.path) + '">' + esc(f.path) + '</td>' +
      '<td class="text-xs text-right">' + fmtSize(f.size) + '</td>' +
      '<td class="text-xs text-muted">' + fmtTimestamp(f.mtime) + '</td>' +
      '</tr>').join('');
  } else {
    orphansSection.style.display = 'none';
  }

  /* select-all */
  $('#media-select-all-items').onclick = function() {
    $$('#media-items-tbody .media-cb').forEach(cb => cb.checked = this.checked);
  };
  $('#media-select-all-orphans').onclick = function() {
    $$('#media-orphans-tbody .media-cb').forEach(cb => cb.checked = this.checked);
  };
}

async function doMediaCleanup() {
  const checked = $$('.media-cb:checked');
  if (!checked.length) { alert(t('media.noSelection')); return; }
  if (!confirm(t('media.confirmCleanup'))) return;

  const payload = { item_ids: [], file_paths: [] };
  checked.forEach(cb => {
    if (cb.dataset.type === 'item') payload.item_ids.push(Number(cb.dataset.id));
    else payload.file_paths.push(cb.dataset.path);
  });

  try {
    const result = await postJson('/api/media/cleanup', payload);
    alert(t('media.cleanupDone').replace('{count}', result.total_deleted_count || 0).replace('{size}', fmtSize(result.total_deleted_size || 0)));
    loadMedia();
  } catch(e) {
    alert(translateApiError(e, 'form.requestFailed'));
  }
}

async function loadCleanupLogs() {
  try {
    const data = await fetchJson('/api/media/cleanup-logs');
    const logs = (data && data.logs) || [];
    const section = $('#media-logs-section');
    if (logs.length) {
      section.style.display = '';
      $('#media-logs-tbody').innerHTML = logs.map(log => '<tr>' +
        '<td class="text-xs max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(log.file_path || '-') + '</td>' +
        '<td class="text-xs text-right">' + fmtSize(log.file_size) + '</td>' +
        '<td class="text-xs">' + esc(log.reason || '-') + '</td>' +
        '<td class="text-xs text-muted">' + fmtTime(log.created_at) + '</td>' +
        '</tr>').join('');
    } else {
      section.style.display = 'none';
    }
  } catch(e) {}
}

$('#media-scan-btn')?.addEventListener('click', loadMedia);
$('#media-cleanup-btn')?.addEventListener('click', doMediaCleanup);

/* ====== Init ====== */
(function init() {
  applyLanguage();
  checkAuthStatus();
  authPollTimer = setInterval(() => {
    if (authStep === 'done' || authStep === 'none') {
      clearInterval(authPollTimer);
      authPollTimer = null;
      return;
    }
    checkAuthStatus();
  }, 2000);
})();
