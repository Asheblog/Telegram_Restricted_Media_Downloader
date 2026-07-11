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
  if (view === 'system-logs') loadSystemLogs();
}

$$('[data-nav]').forEach(btn => btn.addEventListener('click', () => switchView(btn.dataset.nav)));

/* ====== Task List ====== */
async function loadTasks() {
  try {
    const data = await fetchJson('/api/tasks');
    state.tasks = data.tasks || [];
    state.metrics = data.metrics || {};
    state.lastSync = new Date();
    const syncEl = $('#last-sync');
    if (syncEl) syncEl.textContent = state.lastSync.toLocaleTimeString();
    renderTasks();
    updateStats();
  } catch(e) {
    if (e.error_code === 'auth_required') redirectToLoginPage();
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

  const metrics = state.metrics || {};
  const uploadEl = $('#stat-upload-speed');
  const downloadEl = $('#stat-download-speed');
  const diskEl = $('#stat-disk-free');
  if (uploadEl) uploadEl.textContent = formatSpeedStat(metrics.upload_speed_bps);
  if (downloadEl) downloadEl.textContent = formatSpeedStat(metrics.download_speed_bps);
  if (diskEl) {
    const freeBytes = Number(metrics.disk_free_bytes);
    diskEl.textContent = Number.isFinite(freeBytes) && freeBytes >= 0 ? fmtSize(freeBytes) : '-';
    if (metrics.disk_path) diskEl.title = metrics.disk_path;
  }
}

function renderTasks() {
  if (state.activeView !== 'transfers') return;
  const list = $('#tasks-list');
  const empty = $('#tasks-empty');
  if (!state.tasks.length) {
    list.innerHTML = '';
    list.classList.add('hidden');
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';
  list.classList.remove('hidden');
  list.innerHTML = state.tasks.map(task => {
    const isSelected = task.id === state.selectedTaskId;
    const progressPct = taskProgressPercent(task);
    const activeSummary = activeTransferSummary(task);
    const source = esc(task.source_link || '-');
    const target = esc(task.target_profile || task.target_link || '-');
    const route = source + ' → ' + target;
    let progressHtml = '';
    if (task.uses_range_progress || task.total_items > 0) {
      const rangeDetail = taskRangeDetailSummary(task);
      const fileDetail = taskFileTransferDetail(task);
      progressHtml =
        '<div class="task-row-progress">' +
          '<span class="task-row-progress-pct">' + progressPct + '%</span>' +
          '<div class="task-row-progress-bar">' +
            '<div class="progress-fill" style="width:' + progressPct + '%"></div>' +
          '</div>' +
          '<span class="task-row-progress-count">' + taskCompletedLabel(task) + '</span>' +
        '</div>';
      if (rangeDetail) {
        progressHtml +=
          '<div class="task-row-progress-summary task-row-progress-range" title="' + esc(rangeDetail) + '">' +
            esc(rangeDetail) +
          '</div>';
      }
      if (fileDetail) {
        progressHtml +=
          '<div class="task-row-progress-summary task-row-progress-file" title="' + esc(fileDetail) + '">' +
            esc(fileDetail) +
          '</div>';
      } else if (!rangeDetail && activeSummary) {
        progressHtml +=
          '<div class="task-row-progress-summary" title="' + esc(activeSummary) + '">' +
            esc(activeSummary) +
          '</div>';
      }
    } else {
      progressHtml = '<div class="task-row-progress"><span class="text-muted text-xs">-</span></div>';
    }
    return '<div class="task-row' + (isSelected ? ' selected' : '') + '" data-task-id="' + task.id + '">' +
      '<div class="task-row-id">#' + task.id + '</div>' +
      '<div class="task-row-status">' + statusBadge(task.status) + '</div>' +
      '<div class="task-row-route" title="' + esc(task.source_link || '') + ' → ' + esc(task.target_profile || task.target_link || '') + '">' + route + '</div>' +
      '<div class="task-row-actions"><div class="task-row-actions-inner">' + taskActions(task) + '</div></div>' +
      progressHtml +
      '</div>';
  }).join('');

  $$('#tasks-list .task-row').forEach(row => {
    row.addEventListener('click', () => {
      const id = parseInt(row.dataset.taskId);
      state.selectedTaskId = id;
      renderTasks();
      loadTaskDetail(id);
    });
  });
}

const TASK_ICON_PAUSE = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1" fill="currentColor"/><rect x="14" y="5" width="4" height="14" rx="1" fill="currentColor"/></svg>';
const TASK_ICON_PLAY = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M8 5v14l11-7L8 5z" fill="currentColor"/></svg>';
const TASK_ICON_RETRY = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 12a8 8 0 0 1 13.66-5.66M20 4v5h-5M20 12a8 8 0 0 1-13.66 5.66M4 20v-5h5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const TASK_ICON_DELETE = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M6 7h12M9 7V5h6v2M10 11v5M14 11v5M8 7l1 12h6l1-12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function taskActions(task) {
  let actions = '';
  if (task.can_pause) {
    actions += '<button class="task-icon-btn" data-task-action="pause" data-task-id="' + task.id + '" title="' + t('tasks.pause') + '">' + TASK_ICON_PAUSE + '</button>';
  }
  if (task.can_resume) {
    actions += '<button class="task-icon-btn btn-primary" data-task-action="resume" data-task-id="' + task.id + '" title="' + t('tasks.resume') + '">' + TASK_ICON_PLAY + '</button>';
  }
  if (task.can_retry) {
    actions += '<button class="task-icon-btn btn-danger" data-task-action="retry" data-task-id="' + task.id + '" title="' + t('tasks.retryFailed') + '">' + TASK_ICON_RETRY + '</button>';
  }
  if (task.can_delete) {
    actions += '<button class="task-icon-btn btn-danger" data-task-action="delete" data-task-id="' + task.id + '" title="' + t('tasks.delete') + '">' + TASK_ICON_DELETE + '</button>';
  }
  return actions;
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
      const resp = await fetch('/api/tasks/' + taskId, { method: 'DELETE' });
      if (!resp.ok) {
        let data = {};
        try { data = await resp.json(); } catch(e) {}
        alert(data.detail || data.error || data.message || '删除失败');
        return;
      }
      state.tasks = state.tasks.filter(t => t.id !== taskId);
      if (state.selectedTaskId === taskId) state.selectedTaskId = null;
      renderTasks();
      $('#task-detail').innerHTML = '<div class="p-8 text-center text-muted text-sm">' + t('items.selectTask') + '</div>';
    } catch(e) {
      alert('删除失败');
    }
    return;
  }

  const actionMap = { pause: 'pause', resume: 'resume', retry: 'retry-failed' };
  try {
    await postJson('/api/tasks/' + taskId + '/' + actionMap[action], {});
    await loadTasks();
  } catch(e) { /* ignore */ }
});

/* ====== Task Detail ====== */
function selectedTaskStillVisible(taskId) {
  return state.activeView === 'transfers' && Number(state.selectedTaskId) === Number(taskId);
}

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

async function loadTaskItems(taskId, status, options) {
  options = options || {};
  const silent = Boolean(options.silent);
  const page = state.itemPages[status] || 1;
  const body = $('#task-items-body');
  const pagEl = $('#task-items-pagination');
  if (!body || !pagEl) return;
  if (!silent) {
    body.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';
  }

  try {
    const data = await fetchJson('/api/tasks/' + taskId + '?items_limit=50&items_offset=' + ((page - 1) * 50) + '&item_status=' + encodeURIComponent(status));
    if (silent && !selectedTaskStillVisible(taskId)) return;
    const items = data.items || [];
    state.itemData[taskId] = data;

    if (!items.length) {
      body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + t('items.empty.' + status) + '</div>';
    } else {
      body.innerHTML = '<table class="data-table task-items-table"><colgroup>' +
        '<col class="task-item-col-file"><col class="task-item-col-size"><col class="task-item-col-progress"><col class="task-item-col-source"><col class="task-item-col-status">' +
        '</colgroup><thead><tr>' +
        '<th class="task-item-file">文件</th><th class="task-item-size">大小</th><th class="task-item-progress">进度/速度</th><th class="task-item-source">来源</th><th class="task-item-status">状态</th>' +
        '</tr></thead><tbody>' +
        items.map(item => '<tr>' +
          '<td class="task-item-file text-xs" title="' + esc(item.file_name || item.local_path || '-') + '">' + esc(item.file_name || item.local_path || '-') + '</td>' +
          '<td class="task-item-size text-xs">' + fmtSize(item.file_size) + '</td>' +
          '<td class="task-item-progress text-xs" title="' + esc(itemTransferSummary(item)) + '">' + esc(itemTransferSummary(item)) + '</td>' +
          '<td class="task-item-source text-xs" title="' + esc(item.source_link || '-') + '">' + esc(item.source_link || '-') + '</td>' +
          '<td class="task-item-status">' + statusBadge(item.status) + '</td>' +
          '</tr>').join('') +
        '</tbody></table>';
    }

    const statusToSummaryKey = { running: 'running', success: 'success', skipped: 'skipped', failure: 'failed' };
    const summaryKey = statusToSummaryKey[status] || status;
    const totalItems = state.itemData[taskId] ? (state.itemData[taskId].summary || {})[summaryKey] || 0 : 0;
    const totalPages = Math.max(1, Math.ceil(totalItems / 50));
    pagEl.innerHTML = renderPaginationBar({
      prefix: 'items',
      page: page,
      pageSize: 50,
      total: totalItems
    });
    bindPaginationBar('items', page, totalPages, function(newPage) {
      state.itemPages[state.activeItemStatus] = newPage;
      loadTaskItems(taskId, state.activeItemStatus);
    });
  } catch(e) {
    if (!silent) {
      body.innerHTML = '<div class="p-8 text-center text-muted text-sm">加载失败</div>';
    }
  }
}

async function refreshSelectedTaskDetail() {
  if (state.activeView !== 'transfers' || !state.selectedTaskId) return;
  const taskId = state.selectedTaskId;
  const detailEl = $('#task-detail');
  const body = $('#task-items-body');
  if (!detailEl || !body) return;
  try {
    const data = await fetchJson('/api/tasks/' + taskId + '/summary');
    if (!selectedTaskStillVisible(taskId)) return;
    state.itemData[taskId] = data;
    renderTaskDetailTabs(data.summary || {});
    await loadTaskItems(taskId, state.activeItemStatus || 'running', { silent: true });
  } catch(e) {}
}

function renderTaskDetailTabs(summary) {
  const tabs = {
    running: summary.running || 0,
    success: summary.success || 0,
    skipped: summary.skipped || 0,
    failure: summary.failed || 0,
  };
  Object.keys(tabs).forEach(status => {
    const btn = $('#task-detail [data-item-tab="' + status + '"]');
    if (!btn) return;
    btn.textContent = t('items.tab.' + status) + ' (' + tabs[status] + ')';
  });
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
    resolve_deep_link: Boolean(fd.get('resolve_deep_link')),
  };

  try {
    const data = await postJson('/api/tasks', payload);
    state.selectedTaskId = data.task_id;
    notice.className = 'text-xs text-success mt-2';
    notice.textContent = t('form.createSuccess');
    await loadTasks();
    resetTaskPolling();
    setTimeout(function() { refreshTransferData().catch(function() {}); }, 800);
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

async function refreshTransferData() {
  await loadTasks();
  await loadWatches();
  await refreshSelectedTaskDetail();
}

function resetTaskPolling() {
  if (state.taskPollTimer) {
    clearTimeout(state.taskPollTimer);
    state.taskPollTimer = null;
  }
  startPolling();
}

function startPolling() {
  if (state.taskPollTimer) return;
  const fast = 3000, slow = 15000;
  let interval = hasActiveTasks() ? fast : slow;
  let lastPoll = 0;

  async function poll() {
    if (document.hidden) { state.taskPollTimer = setTimeout(poll, interval); return; }
    const now = Date.now();
    if (now - lastPoll < interval - 500) { state.taskPollTimer = setTimeout(poll, interval); return; }
    lastPoll = now;
    try {
      await refreshTransferData();
    } catch(e) {}
    interval = hasActiveTasks() ? fast : slow;
    state.taskPollTimer = setTimeout(poll, interval);
  }
  poll();
}

document.addEventListener('visibilitychange', () => {
  if (!document.hidden && state.taskPollTimer) {
    clearTimeout(state.taskPollTimer);
    state.taskPollTimer = null;
    refreshTransferData().catch(() => {});
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
    if (resp.status === 401) { redirectToLoginPage(); return; }
    const state = await resp.json();
    if (!state || !state.step) return;
    switch (state.step) {
      case 'pending':
        hideLogin();
        await refreshTransferData();
        startPolling();
        return;
      case 'done': case 'none':
        hideLogin();
        await refreshTransferData();
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
  loadWatches();
  if (state.activeView === 'records') loadRecords();
  if (state.activeView === 'settings') loadSettings();
  if (state.activeView === 'statistics') loadStatistics();
  if (state.activeView === 'downloads-uploads') loadOperations();
  if (state.activeView === 'system-logs') loadSystemLogs();
});

/* ====== Logout ====== */
$('#btn-logout').addEventListener('click', async () => {
  await fetch('/api/auth/logout', { method: 'POST' });
  window.location.reload();
});

/* ====== Records ====== */
const RECORDS_PAGE_SIZE = 50;

async function loadRecords(page) {
  if (page !== undefined) state.recordsPage = page;
  const currentPage = state.recordsPage || 1;
  const tbody = $('#records-tbody');
  const empty = $('#records-empty');
  const pagEl = $('#records-pagination');
  const clearBtn = $('#records-clear-btn');
  try {
    const offset = (currentPage - 1) * RECORDS_PAGE_SIZE;
    const data = await fetchJson('/api/download-records?limit=' + RECORDS_PAGE_SIZE + '&offset=' + offset);
    const records = data.records || [];
    const total = Number(data.total || 0);
    state.records = records;
    state.recordsTotal = total;
    const totalPages = Math.max(1, Math.ceil(total / RECORDS_PAGE_SIZE) || 1);

    if (currentPage > totalPages && total > 0) {
      state.recordsPage = totalPages;
      return loadRecords(totalPages);
    }

    if (clearBtn) clearBtn.disabled = total === 0;

    if (!records.length) {
      tbody.innerHTML = '';
      empty.style.display = '';
      if (pagEl) pagEl.innerHTML = '';
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

    if (pagEl) {
      pagEl.innerHTML = renderPaginationBar({
        prefix: 'records',
        page: currentPage,
        pageSize: RECORDS_PAGE_SIZE,
        total: total
      });
      bindPaginationBar('records', currentPage, totalPages, function(newPage) {
        loadRecords(newPage);
      });
    }
  } catch(e) {}
}

$('#records-clear-btn')?.addEventListener('click', async function() {
  if (!confirm(t('records.confirmClear'))) return;
  try {
    const resp = await fetch('/api/download-records', { method: 'DELETE' });
    if (resp.status === 401) { redirectToLoginPage(); return; }
    if (!resp.ok) {
      let data = {};
      try { data = await resp.json(); } catch(e) {}
      throw data;
    }
    state.recordsPage = 1;
    await loadRecords();
  } catch(e) {
    alert(translateApiError(e, 'form.requestFailed'));
  }
});

/* ====== System Logs ====== */
const SYSTEM_LOGS_PAGE_SIZE = 50;

function systemLogLevelClass(level) {
  const value = String(level || 'info').toLowerCase();
  if (value === 'error') return 'system-log-level-error';
  if (value === 'warning') return 'system-log-level-warning';
  return 'system-log-level-info';
}

function formatSystemLogContext(entry) {
  const parts = [];
  if (entry.trace_id) parts.push(t('systemLogs.trace') + ': ' + entry.trace_id);
  if (entry.watch_id) parts.push(t('systemLogs.watch') + ': ' + entry.watch_id);
  if (entry.source_chat_id) parts.push('chat: ' + entry.source_chat_id);
  if (entry.source_message_id) parts.push('msg: ' + entry.source_message_id);
  if (entry.target_link) parts.push('target: ' + entry.target_link);
  if (entry.details) {
    try {
      const parsed = typeof entry.details === 'string' ? JSON.parse(entry.details) : entry.details;
      parts.push(JSON.stringify(parsed));
    } catch (e) {
      parts.push(String(entry.details));
    }
  }
  return parts.join(' | ');
}

function formatSystemLogCopyLine(entry) {
  const time = entry.created_at ? new Date(entry.created_at).toISOString() : '-';
  const context = formatSystemLogContext(entry);
  return '[' + time + '] [' + (entry.level || 'info').toUpperCase() + '] '
    + '[' + (entry.category || '-') + '/' + (entry.stage || '-') + '] '
    + (entry.message || '') + (context ? ' | ' + context : '');
}

async function loadSystemLogs(page) {
  if (page !== undefined) state.systemLogsPage = page;
  const currentPage = state.systemLogsPage || 1;
  const tbody = $('#system-logs-tbody');
  const empty = $('#system-logs-empty');
  const pagEl = $('#system-logs-pagination');
  const retentionEl = $('#system-logs-retention');
  const category = $('#system-logs-category')?.value || '';
  const level = $('#system-logs-level')?.value || '';
  const todayOnly = $('#system-logs-today')?.checked ? '1' : '0';
  try {
    const offset = (currentPage - 1) * SYSTEM_LOGS_PAGE_SIZE;
    const query = '/api/system-logs?limit=' + SYSTEM_LOGS_PAGE_SIZE + '&offset=' + offset
      + '&today=' + todayOnly
      + (category ? '&category=' + encodeURIComponent(category) : '')
      + (level ? '&level=' + encodeURIComponent(level) : '');
    const data = await fetchJson(withClientTzQuery(query));
    const logs = data.logs || [];
    const total = Number(data.total || 0);
    state.systemLogs = logs;
    state.systemLogsTotal = total;
    if (retentionEl) {
      retentionEl.textContent = t('systemLogs.retentionHint').replace('{days}', data.retention_days || 2);
    }
    const totalPages = Math.max(1, Math.ceil(total / SYSTEM_LOGS_PAGE_SIZE) || 1);
    if (currentPage > totalPages && total > 0) {
      state.systemLogsPage = totalPages;
      return loadSystemLogs(totalPages);
    }
    if (!logs.length) {
      tbody.innerHTML = '';
      empty.classList.remove('hidden');
      if (pagEl) pagEl.innerHTML = '';
      return;
    }
    empty.classList.add('hidden');
    tbody.innerHTML = logs.map(function(entry) {
      const timeText = entry.created_at ? new Date(entry.created_at).toLocaleString() : '-';
      const context = formatSystemLogContext(entry);
      return '<tr class="system-log-row" data-log-id="' + esc(String(entry.id || '')) + '">' +
        '<td class="whitespace-nowrap text-xs">' + esc(timeText) + '</td>' +
        '<td><span class="system-log-level ' + systemLogLevelClass(entry.level) + '">' + esc((entry.level || 'info').toUpperCase()) + '</span></td>' +
        '<td class="text-xs">' + esc(entry.category || '-') + '</td>' +
        '<td class="text-xs font-mono">' + esc(entry.stage || '-') + '</td>' +
        '<td class="text-sm">' + esc(entry.message || '') + '</td>' +
        '<td class="text-xs text-muted font-mono system-log-context" title="' + esc(context) + '">' + esc(context) + '</td>' +
      '</tr>';
    }).join('');
    if (pagEl) {
      pagEl.innerHTML = renderPaginationBar({
        prefix: 'system-logs',
        page: currentPage,
        pageSize: SYSTEM_LOGS_PAGE_SIZE,
        total: total
      });
      bindPaginationBar('system-logs', currentPage, totalPages, function(nextPage) {
        state.systemLogsPage = nextPage;
        loadSystemLogs(nextPage);
      });
    }
  } catch (e) {
    if (e.error_code === 'auth_required') redirectToLoginPage();
  }
}

function copySystemLogsPage() {
  const logs = state.systemLogs || [];
  if (!logs.length) return;
  const text = logs.map(formatSystemLogCopyLine).join('\n');
  navigator.clipboard.writeText(text).then(function() {
    alert(t('systemLogs.copied'));
  }).catch(function() {
    prompt(t('systemLogs.copyPage'), text);
  });
}

$('#system-logs-refresh-btn')?.addEventListener('click', function() { loadSystemLogs(); });
$('#system-logs-copy-btn')?.addEventListener('click', copySystemLogsPage);
$('#system-logs-category')?.addEventListener('change', function() { state.systemLogsPage = 1; loadSystemLogs(1); });
$('#system-logs-level')?.addEventListener('change', function() { state.systemLogsPage = 1; loadSystemLogs(1); });
$('#system-logs-today')?.addEventListener('change', function() { state.systemLogsPage = 1; loadSystemLogs(1); });

/* ====== Watches ====== */
async function loadWatches() {
  try {
    const data = await fetchJson(withClientTzQuery('/api/watches'));
    state.watches = data.watches || [];
    renderWatches();
    updateWatchBadge();
  } catch(e) {}
}

function updateWatchBadge() {
  const watches = state.watches || [];
  const activeWatches = watches.filter(w => w.status !== 'paused');
  const todayTotal = activeWatches.reduce(function(sum, w) {
    return sum + (Number(w.today_count) || 0);
  }, 0);
  const count = todayTotal > 0 ? todayTotal : activeWatches.length;
  const badge = $('#badge-watches');
  if (!badge) return;
  badge.textContent = count || '';
  badge.style.display = count ? '' : 'none';
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
    const todayCount = w.today_count || 0;
    const sanitized = sanitizeWatchId(w.id);
    const deferredCount = w.deferred_comment_count || 0;
    const rowAttrs = w.type === 'forward' ? ' class="watch-row" data-watch-id="' + esc(w.id) + '"' : '';
    const eventsRow = w.type === 'forward' ?
      '<tr class="watch-events-row" id="watch-events-' + sanitized + '">' +
      '<td colspan="6"><div class="watch-events-panel" id="watch-events-panel-' + sanitized + '"></div>' +
      '<div class="watch-deferred-panel hidden" id="watch-deferred-panel-' + sanitized + '"></div></td>' +
      '</tr>' : '';
    return '<tr' + rowAttrs + '>' +
      '<td><span class="badge ' + typeCls + '">' + typeLabel + '</span></td>' +
      '<td class="text-xs max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap font-mono text-muted">' + esc(w.source_link || '-') + '</td>' +
      '<td class="text-xs">' + esc(w.target_link || '本地') + '</td>' +
      '<td><span class="badge ' + statusCls + '">' + statusLabel + '</span></td>' +
      '<td class="text-xs font-semibold">' + todayCount + '</td>' +
      '<td><div class="table-actions flex gap-1">' +
        (w.type === 'forward' ? '<button class="btn btn-sm" data-edit-watch="' + esc(w.id) + '">✎</button>' : '') +
        (w.type === 'forward' ? '<button class="btn btn-sm" data-watch-history="' + esc(w.id) + '">' + esc(t('watches.history')) + (eventCount ? ' ' + eventCount : '') + '</button>' : '') +
        (w.type === 'forward' && w.include_comment ? '<button class="btn btn-sm" data-watch-deferred="' + esc(w.id) + '">' + esc(t('watches.deferredComments')) + (deferredCount ? ' ' + deferredCount : '') + '</button>' : '') +
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

function setWatchExpandMode(sanitized, mode) {
  const eventsPanel = document.getElementById('watch-events-panel-' + sanitized);
  const deferredPanel = document.getElementById('watch-deferred-panel-' + sanitized);
  if (eventsPanel) eventsPanel.classList.toggle('hidden', mode !== 'events');
  if (deferredPanel) deferredPanel.classList.toggle('hidden', mode !== 'deferred');
}

function watchExpandShell(title, bodyHtml) {
  return '<div class="watch-expand-header">' + esc(title) + '</div>' +
    '<div class="watch-expand-body">' + bodyHtml + '</div>';
}

function watchExpandEmpty(message) {
  return '<div class="watch-expand-empty">' + esc(message) + '</div>';
}

function toggleWatchEvents(watchId) {
  const sanitized = sanitizeWatchId(watchId);
  const row = document.getElementById('watch-events-' + sanitized);
  if (!row) return;
  const eventsPanel = document.getElementById('watch-events-panel-' + sanitized);
  const isOpen = row.classList.contains('open') && eventsPanel && !eventsPanel.classList.contains('hidden');
  if (isOpen) {
    row.classList.remove('open');
    setWatchExpandMode(sanitized, null);
    return;
  }
  row.classList.add('open');
  setWatchExpandMode(sanitized, 'events');
  loadWatchEvents(watchId, 0, true);
}

async function loadWatchEvents(watchId, offset, todayOnly) {
  const sanitized = sanitizeWatchId(watchId);
  const panel = document.getElementById('watch-events-panel-' + sanitized);
  if (!panel) return;
  const title = todayOnly ? t('watches.todayEvents') : t('watches.events');
  if (offset === 0) panel.innerHTML = watchExpandShell(title, watchExpandEmpty(t('watches.eventLoading')));
  try {
    const todayQuery = todayOnly ? '&today=1' : '';
    const res = await fetch(withClientTzQuery('/api/watches/' + encodeURIComponent(watchId) + '/events?limit=50&offset=' + offset + todayQuery));
    const data = await res.json();
    if (!res.ok) {
      panel.innerHTML = watchExpandShell(title, watchExpandEmpty(data.error || t('form.requestFailed')));
      return;
    }
    const items = data.events || [];
    if (!items.length && offset === 0) {
      panel.innerHTML = watchExpandShell(title, watchExpandEmpty(t('watches.noEvents')));
      return;
    }
    panel.querySelector('.watch-events-load-more')?.remove();
    if (offset === 0) {
      panel.innerHTML = watchExpandShell(title,
        '<div class="watch-expand-scroll">' + renderWatchEventTable(items) + '</div>');
    } else {
      const tbody = panel.querySelector('tbody');
      if (tbody) tbody.insertAdjacentHTML('beforeend', renderWatchEventTbodyRows(items));
    }
    if (data.has_more) {
      const body = panel.querySelector('.watch-expand-body');
      if (body) {
        const btn = document.createElement('button');
        btn.className = 'watch-events-load-more btn btn-sm';
        btn.textContent = t('watches.loadMore');
        btn.onclick = function() { loadWatchEvents(watchId, offset + items.length, todayOnly); };
        body.appendChild(btn);
      }
    }
  } catch (e) {
    panel.innerHTML = watchExpandShell(title, watchExpandEmpty(t('form.requestFailed')));
  }
}

function renderWatchEventTbodyRows(items) {
  return items.map(evt => {
    const statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
    const badgeCls = evt.status === 'success' ? 'badge-success' : 'badge-warning';
    return '<tr>' +
      '<td class="text-xs max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(evt.message || '') + '">' + esc(evt.message || '-') + '</td>' +
      '<td><span class="badge ' + badgeCls + '">' + esc(statusLabel) + '</span></td>' +
      '<td class="text-xs font-mono text-muted">#' + esc(String(evt.source_message_id || '-')) + '</td>' +
      '<td class="text-xs max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(evt.target_link || evt.target_chat_id || '') + '">' + esc(evt.target_link || evt.target_chat_id || '-') + '</td>' +
      '<td class="text-xs text-muted">' + fmtTime(evt.created_at) + '</td>' +
    '</tr>';
  }).join('');
}

function renderWatchEventTable(items, tableClass) {
  return '<table class="data-table ' + (tableClass || 'watch-expand-table') + '"><thead><tr>' +
    '<th>' + esc(t('events.title')) + '</th>' +
    '<th>' + esc(t('tasks.status')) + '</th>' +
    '<th>' + esc(t('watches.source')) + '</th>' +
    '<th>' + esc(t('watches.target')) + '</th>' +
    '<th>' + esc(t('records.updated')) + '</th>' +
    '</tr></thead><tbody>' +
    renderWatchEventTbodyRows(items) +
    '</tbody></table>';
}

function renderWatchEventRows(items) {
  if (!items.length) {
    return '<div class="p-8 text-center text-muted text-sm">' + esc(t('watches.noEvents')) + '</div>';
  }
  return renderWatchEventTable(items, 'watch-history-table');
}

async function openWatchHistoryModal(watchId, page) {
  state.watchHistory = { watchId: watchId, page: page || 1, pageSize: 20, total: 0 };
  const overlay = $('#watch-history-overlay');
  const body = $('#watch-history-body');
  if (!overlay || !body) return;
  overlay.classList.add('open');
  await loadWatchHistoryPage();
}

async function loadWatchHistoryPage() {
  const body = $('#watch-history-body');
  const pagination = $('#watch-history-pagination');
  if (!body || !pagination || !state.watchHistory.watchId) return;
  const page = state.watchHistory.page || 1;
  const pageSize = state.watchHistory.pageSize || 20;
  const offset = (page - 1) * pageSize;
  body.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';
  pagination.innerHTML = '';
  try {
    const data = await fetchJson('/api/watches/' + encodeURIComponent(state.watchHistory.watchId) + '/events?limit=' + pageSize + '&offset=' + offset);
    const items = data.events || [];
    const total = Number(data.total || 0);
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    state.watchHistory.total = total;
    body.innerHTML = renderWatchEventRows(items);
    pagination.innerHTML = renderPaginationBar({
      prefix: 'watch-history',
      page: page,
      pageSize: pageSize,
      total: total,
      pageInfoKey: 'watches.pageInfo'
    });
    bindPaginationBar('watch-history', page, totalPages, function(newPage) {
      state.watchHistory.page = newPage;
      loadWatchHistoryPage();
    });
  } catch(e) {
    body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + esc(t('form.requestFailed')) + '</div>';
  }
}

function closeWatchHistoryModal() {
  $('#watch-history-overlay')?.classList.remove('open');
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
      resolve_deep_link: Boolean(fd.get('resolve_deep_link')),
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
  const historyBtn = e.target.closest('[data-watch-history]');
  if (historyBtn) {
    openWatchHistoryModal(historyBtn.dataset.watchHistory, 1);
  }
  const deferredBtn = e.target.closest('[data-watch-deferred]');
  if (deferredBtn) {
    toggleWatchDeferred(deferredBtn.dataset.watchDeferred);
  }
  const runNowBtn = e.target.closest('[data-deferred-run-now]');
  if (runNowBtn) {
    await postDeferredAction(runNowBtn.dataset.watchId, runNowBtn.dataset.deferredRunNow, 'run-now');
  }
  const cancelDeferredBtn = e.target.closest('[data-deferred-cancel]');
  if (cancelDeferredBtn) {
    await postDeferredAction(cancelDeferredBtn.dataset.watchId, cancelDeferredBtn.dataset.deferredCancel, 'cancel');
  }
});

function deferredStatusLabel(status) {
  const map = {
    pending: 'watches.deferredPending',
    running: 'watches.deferredRunning',
    done: 'watches.deferredDone',
    cancelled: 'watches.deferredCancelled',
    failure: 'watches.deferredFailure',
  };
  return t(map[status] || 'watches.deferredPending');
}

function toggleWatchDeferred(watchId) {
  const sanitized = sanitizeWatchId(watchId);
  const row = document.getElementById('watch-events-' + sanitized);
  const panel = document.getElementById('watch-deferred-panel-' + sanitized);
  if (!row || !panel) return;
  const isOpen = row.classList.contains('open') && !panel.classList.contains('hidden');
  if (isOpen) {
    row.classList.remove('open');
    setWatchExpandMode(sanitized, null);
    return;
  }
  // Close other watches' expand rows, then show deferred for this one.
  document.querySelectorAll('.watch-events-row.open').forEach(el => {
    if (el.id !== 'watch-events-' + sanitized) el.classList.remove('open');
  });
  document.querySelectorAll('.watch-events-panel, .watch-deferred-panel').forEach(el => el.classList.add('hidden'));
  row.classList.add('open');
  setWatchExpandMode(sanitized, 'deferred');
  loadWatchDeferred(watchId);
}

function renderDeferredCommentRows(watchId, items) {
  return '<table class="data-table watch-expand-table"><thead><tr>' +
    '<th>' + esc(t('records.message')) + '</th>' +
    '<th>' + esc(t('tasks.status')) + '</th>' +
    '<th>' + esc(t('watches.deferredDue')) + '</th>' +
    '<th>' + esc(t('tasks.actions')) + '</th>' +
    '</tr></thead><tbody>' +
    items.map(item => {
      const due = item.due_at ? new Date(Number(item.due_at) * 1000).toLocaleString() : '-';
      const actions = item.status === 'pending'
        ? '<div class="table-actions flex gap-1">' +
          '<button class="btn btn-sm" data-watch-id="' + esc(watchId) + '" data-deferred-run-now="' + esc(String(item.id)) + '">' + esc(t('watches.deferredRunNow')) + '</button>' +
          '<button class="btn btn-sm btn-danger" data-watch-id="' + esc(watchId) + '" data-deferred-cancel="' + esc(String(item.id)) + '">' + esc(t('watches.deferredCancel')) + '</button>' +
          '</div>'
        : '<span class="text-xs text-muted">—</span>';
      const statusCls = item.status === 'pending' ? 'badge-warning'
        : item.status === 'running' ? 'badge-running'
        : item.status === 'done' ? 'badge-success'
        : item.status === 'failure' ? 'badge-failed'
        : 'badge-paused';
      return '<tr>' +
        '<td class="text-xs font-mono text-muted">#' + esc(String(item.source_message_id || '-')) + '</td>' +
        '<td><span class="badge ' + statusCls + '">' + esc(deferredStatusLabel(item.status)) + '</span></td>' +
        '<td class="text-xs text-muted">' + esc(due) + '</td>' +
        '<td>' + actions + '</td>' +
      '</tr>';
    }).join('') +
    '</tbody></table>';
}

async function loadWatchDeferred(watchId) {
  const sanitized = sanitizeWatchId(watchId);
  const panel = document.getElementById('watch-deferred-panel-' + sanitized);
  if (!panel) return;
  const title = t('watches.deferredComments');
  panel.innerHTML = watchExpandShell(title, watchExpandEmpty(t('watches.eventLoading')));
  try {
    const res = await fetch('/api/watches/' + encodeURIComponent(watchId) + '/deferred-comments');
    const data = await res.json();
    if (!res.ok) {
      panel.innerHTML = watchExpandShell(title, watchExpandEmpty(data.error || t('form.requestFailed')));
      return;
    }
    const items = data.captures || [];
    if (!items.length) {
      panel.innerHTML = watchExpandShell(title, watchExpandEmpty(t('watches.noDeferredComments')));
      return;
    }
    panel.innerHTML = watchExpandShell(title,
      '<div class="watch-expand-scroll">' + renderDeferredCommentRows(watchId, items) + '</div>');
  } catch (err) {
    panel.innerHTML = watchExpandShell(title, watchExpandEmpty(t('form.requestFailed')));
  }
}

async function postDeferredAction(watchId, captureId, action) {
  try {
    const res = await fetch(
      '/api/watches/' + encodeURIComponent(watchId) + '/deferred-comments/' + encodeURIComponent(captureId) + '/' + action,
      { method: 'POST' }
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      alert(data.error || t('form.requestFailed'));
      return;
    }
    await loadWatchDeferred(watchId);
    await loadWatches();
  } catch (err) {
    alert(t('form.requestFailed'));
  }
}

function openEditWatchModal(watchId) {
  const watch = (state.watches || []).find(w => w.id === watchId);
  if (!watch) return;
  $('#edit-watch-id').value = watch.id;
  $('#edit-watch-source').value = watch.source_link || '';
  $('#edit-watch-target').value = watch.target_link || '';
  $('#edit-watch-comment').checked = watch.include_comment || false;
  $('#edit-watch-deep-link').checked = watch.resolve_deep_link || false;
  $('#watch-edit-overlay').classList.add('open');
}

function closeEditWatchModal() {
  $('#watch-edit-overlay').classList.remove('open');
}

$('#watch-edit-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeEditWatchModal();
});

$('#watch-history-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeWatchHistoryModal();
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
        resolve_deep_link: Boolean(fd.get('resolve_deep_link')),
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
function renderStatisticsKpis(data) {
  const summary = data.summary || {};
  const channelsEl = $('#stats-kpi-channels');
  const downloadsEl = $('#stats-kpi-downloads');
  const successRateEl = $('#stats-kpi-success-rate');
  const issuesEl = $('#stats-kpi-issues');
  if (!channelsEl) return;

  channelsEl.textContent = summary.channels || 0;
  downloadsEl.textContent = summary.downloads_total || 0;
  if (successRateEl) successRateEl.textContent = (summary.success_rate || 0) + '%';
  issuesEl.textContent = (summary.failure_count || 0) + ' / ' + (summary.skip_count || 0);
}

function renderStatisticsMediaChart(data) {
  const container = $('#stats-media-chart');
  if (!container) return;
  const rows = (data.chart_by_channel || data.count_by_channel || []).filter(row => row.total > 0);
  if (!rows.length) {
    container.innerHTML = '<div class="text-sm text-muted text-center py-10">' + esc(t('statistics.empty')) + '</div>';
    return;
  }
  const maxTotal = Math.max(...rows.map(row => row.total), 1);
  container.innerHTML = rows.map(row => {
    const width = Math.max(4, Math.round((row.total / maxTotal) * 100));
    const successW = row.total ? Math.round((row.success / row.total) * 100) : 0;
    const failureW = row.total ? Math.round((row.failure / row.total) * 100) : 0;
    const skipW = Math.max(0, 100 - successW - failureW);
    const label = row.is_other ? t('statistics.otherChannel') : (row.channel || 'unknown');
    return '<div class="stats-hbar-row" title="' + esc(label + ' · ' + row.total) + '">' +
      '<span class="stats-hbar-label">' + esc(label) + '</span>' +
      '<div class="stats-hbar-track" style="width:' + width + '%">' +
        (successW ? '<div class="stats-hbar-seg-success" style="width:' + successW + '%"></div>' : '') +
        (failureW ? '<div class="stats-hbar-seg-failure" style="width:' + failureW + '%"></div>' : '') +
        (skipW ? '<div class="stats-hbar-seg-skip" style="width:' + skipW + '%"></div>' : '') +
      '</div>' +
      '<span class="stats-hbar-total">' + esc(row.total) + '</span>' +
    '</div>';
  }).join('');
}

function renderStatisticsDetailTable(data) {
  const thead = $('#statistics-detail-thead');
  const tbody = $('#statistics-detail-tbody');
  const emptyEl = $('#statistics-empty');
  const tableEl = $('#statistics-detail-table');
  const exportBtn = $('#statistics-export-btn');
  if (!thead || !tbody) return;

  const available = !!(data.tables && data.tables.channel && data.tables.channel.available);
  if (exportBtn) {
    exportBtn.dataset.export = 'channel';
    exportBtn.disabled = !available;
    exportBtn.classList.toggle('opacity-50', exportBtn.disabled);
    exportBtn.style.cursor = exportBtn.disabled ? 'not-allowed' : 'pointer';
  }

  const headers = [
    'statistics.colChannel',
    'statistics.colSuccess',
    'statistics.colFailure',
    'statistics.colSkip',
    'statistics.colTotal',
    'statistics.colSuccessRate',
  ];
  const rows = data.channels || data.count_by_channel || [];
  let rowsHtml = rows.map(row =>
    '<tr>' +
      '<td class="link">' + esc(row.channel || 'unknown') + '</td>' +
      '<td class="num">' + esc(row.success || 0) + '</td>' +
      '<td class="num">' + esc(row.failure || 0) + '</td>' +
      '<td class="num">' + esc(row.skip || 0) + '</td>' +
      '<td class="num font-semibold">' + esc(row.total || 0) + '</td>' +
      '<td class="num">' + esc((row.success_rate || 0) + '%') + '</td>' +
    '</tr>'
  ).join('');
  if (!available) rowsHtml = '';

  thead.innerHTML = '<tr>' + headers.map(key => '<th data-i18n="' + key + '">' + esc(t(key)) + '</th>').join('') + '</tr>';
  tbody.innerHTML = rowsHtml;
  const showEmpty = !rowsHtml;
  emptyEl?.classList.toggle('hidden', !showEmpty);
  tableEl?.classList.toggle('hidden', showEmpty);
}

function renderStatisticsDashboard(data) {
  renderStatisticsKpis(data);
  renderStatisticsMediaChart(data);
  renderStatisticsDetailTable(data);
}

async function loadStatistics() {
  try {
    const data = await fetchJson(withClientTzQuery('/api/statistics'));
    state.statistics = data;
    if (state.activeView === 'statistics') renderStatisticsDashboard(data);
  } catch (e) {}
}

$('#statistics-export-btn')?.addEventListener('click', async () => {
  const btn = $('#statistics-export-btn');
  if (!btn || btn.disabled) return;
  try {
    await postJson('/api/tables/export', { table_type: btn.dataset.export || 'channel' });
    alert(t('statistics.exported'));
  } catch (err) {
    alert(translateApiError(err, 'form.requestFailed'));
  }
});

document.addEventListener('click', async function(e) {
  const exportBtn = e.target.closest('[data-export]');
  if (!exportBtn || exportBtn.id === 'statistics-export-btn') return;
  try {
    await postJson('/api/tables/export', { table_type: exportBtn.dataset.export });
    alert(t('statistics.exported'));
  } catch(err) {
    alert(translateApiError(err, 'form.requestFailed'));
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
  setFieldVal('global.live_watch.comment_delay_minutes', sg.live_watch?.comment_delay_minutes ?? 20);
  const deepLinkWhitelist = sg.deep_link?.bot_whitelist;
  setFieldVal(
    'global.deep_link.bot_whitelist',
    Array.isArray(deepLinkWhitelist) ? deepLinkWhitelist.join('\n') : (deepLinkWhitelist || '')
  );
  setFieldVal('global.deep_link.timeout_seconds', sg.deep_link?.timeout_seconds ?? 60);

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

  /* global settings — skip bot_whitelist textarea; collected explicitly as array below */
  $$('[name^="global."]').forEach(el => {
    if (!el.name) return;
    if (el.name === 'global.forward_type' || el.name === 'global.message_filter.media_types') return;
    if (el.name === 'global.deep_link.bot_whitelist') return;
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

  /* deep link bot whitelist — textarea may arrive as newline/comma-separated string */
  const whitelistInput = document.querySelector('[name="global.deep_link.bot_whitelist"]');
  if (whitelistInput) {
    const lines = String(whitelistInput.value || '')
      .split(/[\n,]+/)
      .map(function(s) { return s.trim(); })
      .filter(Boolean);
    setNested(payload, ['global', 'deep_link', 'bot_whitelist'], lines);
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
let mediaItemsPage = 0;
let mediaOrphansPage = 0;
const MEDIA_PAGE_SIZE = 50;

function showMediaElement(el, visible) {
  if (!el) return;
  el.classList.toggle('hidden', !visible);
  el.style.display = visible ? '' : 'none';
}

function setMediaScanButtonLoading(isLoading) {
  const btn = $('#media-scan-btn');
  if (!btn) return;
  const label = btn.querySelector('[data-i18n]');
  btn.disabled = Boolean(isLoading);
  btn.setAttribute('aria-busy', isLoading ? 'true' : 'false');
  if (label) label.textContent = isLoading ? t('media.scanning') : t('media.scan');
}

function updateMediaCleanupButton() {
  const btn = $('#media-cleanup-btn');
  if (!btn) return;
  btn.disabled = $$('.media-cb:checked').length === 0;
}

function mediaScanUrl() {
  var itemsOffset = mediaItemsPage * MEDIA_PAGE_SIZE;
  var orphansOffset = mediaOrphansPage * MEDIA_PAGE_SIZE;
  return '/api/media/scan?items_limit=' + MEDIA_PAGE_SIZE + '&items_offset=' + itemsOffset +
    '&orphans_limit=' + MEDIA_PAGE_SIZE + '&orphans_offset=' + orphansOffset;
}

async function loadMediaCleanupLogs() {
  try {
    return await fetchJson('/api/media/cleanup-logs');
  } catch (e) {
    return { logs: [] };
  }
}

async function loadMedia() {
  const container = $('#media-result');
  try {
    setMediaScanButtonLoading(true);
    updateMediaCleanupButton();
    if (container) {
      container.classList.remove('hidden');
      container.style.display = '';
      container.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div><div class="text-xs text-muted mt-2">' + t('media.scanning') + '</div></div>';
      updateMediaCleanupButton();
    }
    const data = await fetchJson(mediaScanUrl());
    mediaScanResult = data;
    await loadMediaCleanupLogs();
    renderMediaResult(data);
  } catch(e) {
    renderMediaError(e);
  } finally {
    setMediaScanButtonLoading(false);
  }
}

function renderMediaPagination(prefix, page, totalPages, totalCount) {
  if (totalPages <= 1) return '';
  return renderPaginationBar({
    prefix: prefix,
    page: page + 1,
    pageSize: MEDIA_PAGE_SIZE,
    total: totalCount
  });
}

function bindMediaPagination(prefix, currentPage, totalPages, onChange) {
  bindPaginationBar(prefix, currentPage + 1, totalPages, function(newPage) {
    onChange(newPage - 1);
  });
}

function renderMediaResult(data) {
  const container = $('#media-result');
  if (!container) return;
  if (!data) {
    container.classList.add('hidden');
    container.style.display = 'none';
    return;
  }

  container.classList.remove('hidden');
  container.style.display = '';
  container.innerHTML =
    '<div id="media-summary" class="flex gap-5 flex-wrap p-4 bg-surface-alt rounded-lg mb-4"></div>' +
    '<div id="media-items-section" class="mb-4 hidden">' +
      '<h4 class="text-base font-semibold mb-2">' + t('media.transferItems') + '</h4>' +
      '<div class="overflow-x-auto rounded-lg border border-line">' +
        '<table class="data-table min-w-[600px]"><thead><tr>' +
          '<th class="w-10"><input type="checkbox" id="media-select-all-items"></th>' +
          '<th>' + t('media.file') + '</th>' +
          '<th class="text-right">' + t('media.size') + '</th>' +
          '<th class="text-center">' + t('media.status') + '</th>' +
          '<th>' + t('media.source') + '</th>' +
        '</tr></thead><tbody id="media-items-tbody"></tbody></table>' +
      '</div>' +
      '<div id="media-items-pagination"></div>' +
    '</div>' +
    '<div id="media-orphans-section" class="mb-4 hidden">' +
      '<h4 class="text-base font-semibold mb-2">' + t('media.orphanFiles') + '</h4>' +
      '<div class="overflow-x-auto rounded-lg border border-line">' +
        '<table class="data-table min-w-[600px]"><thead><tr>' +
          '<th class="w-10"><input type="checkbox" id="media-select-all-orphans"></th>' +
          '<th>' + t('media.path') + '</th>' +
          '<th class="text-right">' + t('media.size') + '</th>' +
          '<th>' + t('media.mtime') + '</th>' +
        '</tr></thead><tbody id="media-orphans-tbody"></tbody></table>' +
      '</div>' +
      '<div id="media-orphans-pagination"></div>' +
    '</div>';

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
  const totalItemsPages = Math.max(1, Math.ceil((ti.total_count || 0) / MEDIA_PAGE_SIZE));
  if (ti.total_count > 0) {
    showMediaElement(itemsSection, true);
    if (items.length) {
      $('#media-items-tbody').innerHTML = items.map(item => '<tr>' +
        '<td><input type="checkbox" class="media-cb" data-type="item" data-id="' + item.item_id + '"></td>' +
        '<td class="text-xs max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc((item.paths || []).join('\\n') || item.local_path || '') + '">' + esc(item.file_name || item.local_path || '-') + '</td>' +
        '<td class="text-xs text-right">' + fmtSize(item.file_size) + '</td>' +
        '<td class="text-center">' + statusBadge(item.status || '') + '</td>' +
        '<td class="text-xs max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(item.source_link || '-') + '">' + esc(item.source_link || '-') + '</td>' +
        '</tr>').join('');
    } else {
      $('#media-items-tbody').innerHTML = '<tr><td colspan="5" class="text-center text-muted text-xs py-4">暂无数据</td></tr>';
    }
    $('#media-items-pagination').innerHTML = renderMediaPagination('media-items', mediaItemsPage, totalItemsPages, ti.total_count || 0);
    bindMediaPagination('media-items', mediaItemsPage, totalItemsPages, function(newPage) {
      mediaItemsPage = newPage;
      loadMedia();
    });
  } else {
    showMediaElement(itemsSection, false);
  }

  /* orphans */
  const files = orph.files || [];
  const orphansSection = $('#media-orphans-section');
  const totalOrphansPages = Math.max(1, Math.ceil((orph.total_count || 0) / MEDIA_PAGE_SIZE));
  if (orph.total_count > 0) {
    showMediaElement(orphansSection, true);
    if (files.length) {
      $('#media-orphans-tbody').innerHTML = files.map(f => '<tr>' +
        '<td><input type="checkbox" class="media-cb" data-type="orphan" data-path="' + esc(f.path) + '"></td>' +
        '<td class="text-xs max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(f.path) + '">' + esc(f.path) + '</td>' +
        '<td class="text-xs text-right">' + fmtSize(f.size) + '</td>' +
        '<td class="text-xs text-muted">' + fmtTimestamp(f.mtime) + '</td>' +
        '</tr>').join('');
    } else {
      $('#media-orphans-tbody').innerHTML = '<tr><td colspan="4" class="text-center text-muted text-xs py-4">暂无数据</td></tr>';
    }
    $('#media-orphans-pagination').innerHTML = renderMediaPagination('media-orphans', mediaOrphansPage, totalOrphansPages, orph.total_count || 0);
    bindMediaPagination('media-orphans', mediaOrphansPage, totalOrphansPages, function(newPage) {
      mediaOrphansPage = newPage;
      loadMedia();
    });
  } else {
    showMediaElement(orphansSection, false);
  }

  if (!ti.total_count && !orph.total_count) {
    container.insertAdjacentHTML('beforeend', '<div class="p-6 text-center text-muted text-sm">' + t('media.empty') + '</div>');
  }

  /* select-all */
  const selectAllItems = $('#media-select-all-items');
  if (selectAllItems) selectAllItems.onclick = function() {
    $$('#media-items-tbody .media-cb').forEach(cb => cb.checked = this.checked);
    updateMediaCleanupButton();
  };
  const selectAllOrphans = $('#media-select-all-orphans');
  if (selectAllOrphans) selectAllOrphans.onclick = function() {
    $$('#media-orphans-tbody .media-cb').forEach(cb => cb.checked = this.checked);
    updateMediaCleanupButton();
  };
  updateMediaCleanupButton();
}


function renderMediaError(error) {
  const container = $('#media-result');
  if (!container) return;
  container.classList.remove('hidden');
  container.style.display = '';
  container.innerHTML =
    '<div class="p-6 rounded-lg border border-line bg-danger-bg text-danger text-sm">' +
      esc(translateApiError(error, 'form.requestFailed')) +
    '</div>';
  updateMediaCleanupButton();
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
    mediaItemsPage = 0;
    mediaOrphansPage = 0;
    loadMedia();
  } catch(e) {
    alert(translateApiError(e, 'form.requestFailed'));
  }
}

$('#media-scan-btn')?.addEventListener('click', function() {
  mediaItemsPage = 0;
  mediaOrphansPage = 0;
  loadMedia();
});
$('#media-cleanup-btn')?.addEventListener('click', doMediaCleanup);
document.addEventListener('change', function(e) {
  if (e.target && e.target.classList && e.target.classList.contains('media-cb')) {
    updateMediaCleanupButton();
  }
});

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
