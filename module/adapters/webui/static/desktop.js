/* TRMD WebUI - Desktop SPA Logic */

/* ====== View Switching ====== */
function switchView(view, options) {
  options = options || {};
  if (!SPA_VIEW_PATHS[view] || view === 'profile') {
    view = 'transfers';
  }
  state.activeView = view;
  $$('.sidebar-nav-item').forEach(b => b.classList.remove('active'));
  const navBtn = document.querySelector('.sidebar-nav-item[data-nav="' + view + '"]');
  if (navBtn) navBtn.classList.add('active');

  $$('.view').forEach(v => v.classList.remove('active'));
  const viewEl = document.getElementById('view-' + view);
  if (viewEl) viewEl.classList.add('active');

  if (options.syncUrl !== false) {
    syncSpaUrl(view, { replace: !!options.replaceUrl });
  }

  if (view === 'transfers') renderTasks();
  if (view === 'watches') loadWatches();
  if (view === 'downloads-uploads') { loadDownloadTypes(); loadOperations(); }
  if (view === 'settings') loadSettings();
  if (view === 'records') loadRecords();
  if (view === 'statistics') loadStatistics();
  if (view === 'media') loadMedia();
  if (view === 'archive-organize') loadArchiveOrganize();
  if (view === 'system-logs') {
    loadSystemLogs();
    startSystemLogsAutoRefresh();
  } else {
    stopSystemLogsAutoRefresh();
  }
}

function applyDesktopRouteFromLocation(options) {
  options = options || {};
  var view = viewFromPath(window.location.pathname);
  var path = normalizeSpaPathname(window.location.pathname);
  if (!view) {
    switchView('transfers', { replaceUrl: true });
    return;
  }
  if (path === '/' || path === '/index.html') {
    switchView('transfers', { replaceUrl: true });
    return;
  }
  switchView(view, { syncUrl: false, replaceUrl: false });
}

$$('[data-nav]').forEach(btn => btn.addEventListener('click', () => switchView(btn.dataset.nav)));
window.addEventListener('popstate', function() {
  applyDesktopRouteFromLocation();
});

/* ====== Task List ====== */
async function loadTasks() {
  try {
    const data = await fetchJson('/api/tasks');
    state.tasks = data.tasks || [];
    state.taskStats = data.task_stats || {};
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
  const taskStats = state.taskStats || {};
  const totalTasks = Number(taskStats.total_tasks || 0);
  const completedTasks = Number(taskStats.completed_tasks || 0);
  const runningTasks = Number(taskStats.running_tasks || 0);
  const failedTasks = Number(taskStats.failed_tasks || 0);
  const failedItems = Number(taskStats.failed_items || 0);
  $('#stat-total').textContent = totalTasks;
  $('#stat-success').textContent = completedTasks;
  $('#stat-running').textContent = runningTasks;
  const failedEl = $('#stat-failed');
  failedEl.textContent = failedTasks;
  failedEl.title = t('stats.failedItemsDetail', { count: failedItems });
  failedEl.setAttribute('aria-label', t('stats.failed') + ' ' + failedTasks + '. ' + t('stats.failedItemsDetail', { count: failedItems }));
  $('#metric-failed').textContent = failedItems;
  $('#badge-transfers').textContent = runningTasks || '';
  $('#badge-transfers').style.display = runningTasks ? '' : 'none';

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
    state.itemPages = { active: 1, success: 1, skipped: 1, failure: 1 };
    state.activeItemStatus = 'active';
    renderTaskDetail(taskId, data);
  } catch(e) {
    container.innerHTML = '<div class="p-8 text-center text-muted text-sm">加载失败</div>';
  }
}

function taskItemTabCount(summary, status) {
  summary = summary || {};
  if (status === 'active') return (summary.running || 0) + (summary.pending || 0);
  if (status === 'failure') return summary.failed || 0;
  return summary[status] || 0;
}

function taskItemTabLabel(status) {
  if (status === 'active') return t('items.tab.running');
  return t('items.tab.' + status);
}

function renderTaskDetail(taskId, data) {
  const task = state.tasks.find(t => t.id === taskId);
  const summary = data.summary || {};
  const detailEl = $('#task-detail');

  let html = '<div class="panel-header">' +
    '<h3>任务 #' + taskId + ' · ' + esc(task ? (task.source_link || '') : '') + ' → ' + esc(task ? (task.target_profile || task.target_link || '') : '') + '</h3>' +
    '<div class="panel-tabs">' +
      '<button class="panel-tab active" data-item-tab="active">' + taskItemTabLabel('active') + ' (' + taskItemTabCount(summary, 'active') + ')</button>' +
      '<button class="panel-tab" data-item-tab="success">' + taskItemTabLabel('success') + ' (' + taskItemTabCount(summary, 'success') + ')</button>' +
      '<button class="panel-tab" data-item-tab="skipped">' + taskItemTabLabel('skipped') + ' (' + taskItemTabCount(summary, 'skipped') + ')</button>' +
      '<button class="panel-tab" data-item-tab="failure">' + taskItemTabLabel('failure') + ' (' + taskItemTabCount(summary, 'failure') + ')</button>' +
    '</div>' +
    '</div>' +
    '<div id="task-items-body" class="overflow-auto max-h-[300px]"></div>' +
    '<div class="flex items-center justify-between px-[18px] py-2 pb-[14px] gap-3 flex-wrap" id="task-items-pagination"></div>';

  detailEl.innerHTML = html;
  loadTaskItems(taskId, 'active');

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
      const emptyStatus = status === 'active' ? 'running' : status;
      body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + t('items.empty.' + emptyStatus) + '</div>';
    } else {
      body.innerHTML = '<table class="data-table task-items-table"><colgroup>' +
        '<col class="task-item-col-file"><col class="task-item-col-size"><col class="task-item-col-progress"><col class="task-item-col-source"><col class="task-item-col-error"><col class="task-item-col-status">' +
        '</colgroup><thead><tr>' +
        '<th class="task-item-file">' + t('items.colFile') + '</th>' +
        '<th class="task-item-size">' + t('items.colSize') + '</th>' +
        '<th class="task-item-progress">' + t('items.colProgress') + '</th>' +
        '<th class="task-item-source">' + t('items.colSource') + '</th>' +
        '<th class="task-item-error">' + t('items.colError') + '</th>' +
        '<th class="task-item-status">' + t('items.colStatus') + '</th>' +
        '</tr></thead><tbody>' +
        items.map(item => {
          const errorText = item.error_message || '';
          return '<tr>' +
          '<td class="task-item-file" title="' + esc(item.file_name || item.local_path || '-') + '">' + esc(item.file_name || item.local_path || '-') + '</td>' +
          '<td class="task-item-size">' + fmtSize(item.file_size) + '</td>' +
          '<td class="task-item-progress" title="' + esc(itemTransferSummary(item)) + '">' + esc(itemTransferSummary(item)) + '</td>' +
          '<td class="task-item-source" title="' + esc(item.source_link || '-') + '">' + esc(item.source_link || '-') + '</td>' +
          '<td class="task-item-error' + (errorText ? ' text-danger' : '') + '" title="' + esc(errorText || '-') + '">' + esc(errorText || '-') + '</td>' +
          '<td class="task-item-status">' + statusBadge(item.status) + '</td>' +
          '</tr>';
        }).join('') +
        '</tbody></table>';
    }

    const totalItems = taskItemTabCount(state.itemData[taskId] ? state.itemData[taskId].summary : {}, status);
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
    await loadTaskItems(taskId, state.activeItemStatus || 'active', { silent: true });
  } catch(e) {}
}

function renderTaskDetailTabs(summary) {
  ['active', 'success', 'skipped', 'failure'].forEach(status => {
    const btn = $('#task-detail [data-item-tab="' + status + '"]');
    if (!btn) return;
    btn.textContent = taskItemTabLabel(status) + ' (' + taskItemTabCount(summary, status) + ')';
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
    media_types: readMediaTypesOverride(this),
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
  return state.tasks.some(t => t.status === 'pending' || t.status === 'running' || t.status === 'pausing');
}

async function refreshTransferData() {
  await loadTasks();
  if (!hasExpandedWatch()) {
    await loadWatches();
  }
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
  const fast = 1000, slow = 15000;
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
  ['login-form-preparing','login-form-phone','login-form-code','login-form-password','login-form-recovery','login-form-signup','login-form-done'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.add('hidden');
    el.style.display = 'none';
  });
  const el = document.getElementById('login-form-' + step);
  if (el) {
    el.classList.remove('hidden');
    el.style.display = '';
  }
  const container = document.getElementById('login-container');
  if (container) {
    container.classList.remove('hidden');
    container.style.display = 'flex';
  }
  const errEl = document.getElementById('login-error');
  if (errEl) errEl.classList.remove('visible');
}

function hideLogin() {
  const container = document.getElementById('login-container');
  if (container) {
    container.classList.add('hidden');
    container.style.display = 'none';
  }
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
    if (typeof checkSetupStatus === 'function') {
      const setup = await checkSetupStatus();
      if (setup && setup.wizard_active && setup.current_step === 'api') {
        hideLogin();
        return;
      }
    }
    const resp = await fetch('/api/auth/status');
    if (resp.status === 401) { redirectToLoginPage(); return; }
    const state = await resp.json();
    if (!state || !state.step) return;
    switch (state.step) {
      case 'pending':
        // After API credentials: keep login overlay visible while Telegram client starts.
        if (lastSetupStatus && lastSetupStatus.current_step === 'telegram') {
          showLoginStep('preparing');
          return;
        }
        if (lastSetupStatus && !lastSetupStatus.ready) {
          hideLogin();
          return;
        }
        hideLogin();
        await refreshTransferData();
        startPolling();
        return;
      case 'done': case 'none':
        if (lastSetupStatus && lastSetupStatus.current_step === 'telegram') {
          showLoginStep('preparing');
          return;
        }
        if (lastSetupStatus && !lastSetupStatus.ready) {
          hideLogin();
          return;
        }
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
  if (state.activeView === 'system-logs') loadSystemLogs(1);
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
      '<td class="font-mono text-muted">' + esc(String(r.source_chat_id || '-')) + '</td>' +
      '<td class="font-mono text-muted">' + esc(String(r.source_message_id || '-')) + '</td>' +
      '<td class="max-w-[200px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(r.file_path || r.file_name || '-') + '</td>' +
      '<td>' + fmtSize(r.file_size) + '</td>' +
      '<td class="text-muted">' + fmtTime(r.updated_at) + '</td>' +
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
const SYSTEM_LOGS_AUTO_REFRESH_KEY = 'trmd-system-logs-auto-refresh';
const SYSTEM_LOGS_AUTO_REFRESH_MS = 5000;
let systemLogsAutoRefreshTimer = null;

function systemLogLevelClass(level) {
  const value = String(level || 'info').toLowerCase();
  if (value === 'error') return 'system-log-level-error';
  if (value === 'warning') return 'system-log-level-warning';
  return 'system-log-level-info';
}

function isSystemLogsAutoRefreshEnabled() {
  return localStorage.getItem(SYSTEM_LOGS_AUTO_REFRESH_KEY) === '1';
}

function setSystemLogsAutoRefreshEnabled(enabled) {
  localStorage.setItem(SYSTEM_LOGS_AUTO_REFRESH_KEY, enabled ? '1' : '0');
}

function stopSystemLogsAutoRefresh() {
  if (systemLogsAutoRefreshTimer) {
    clearInterval(systemLogsAutoRefreshTimer);
    systemLogsAutoRefreshTimer = null;
  }
}

function startSystemLogsAutoRefresh() {
  stopSystemLogsAutoRefresh();
  if (!isSystemLogsAutoRefreshEnabled()) return;
  if (state.activeView !== 'system-logs') return;
  systemLogsAutoRefreshTimer = setInterval(function() {
    if (state.activeView !== 'system-logs') {
      stopSystemLogsAutoRefresh();
      return;
    }
    loadSystemLogs(1);
  }, SYSTEM_LOGS_AUTO_REFRESH_MS);
}

function syncSystemLogsAutoRefreshUI() {
  const checkbox = $('#system-logs-auto-refresh');
  if (checkbox) checkbox.checked = isSystemLogsAutoRefreshEnabled();
}

function formatSystemLogDetails(entry) {
  if (entry.details == null || entry.details === '') return '';
  try {
    const parsed = typeof entry.details === 'string' ? JSON.parse(entry.details) : entry.details;
    return typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2);
  } catch (e) {
    return String(entry.details);
  }
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

function renderSystemLogDetailRow(label, valueHtml, mono) {
  return '<div class="system-log-detail-row">' +
    '<div class="system-log-detail-label">' + esc(label) + '</div>' +
    '<div class="system-log-detail-value' + (mono ? ' font-mono' : '') + '">' + valueHtml + '</div>' +
  '</div>';
}

function openSystemLogDetailModal(entry) {
  const overlay = $('#system-log-detail-overlay');
  const body = $('#system-log-detail-body');
  if (!overlay || !body || !entry) return;
  const timeText = entry.created_at ? new Date(entry.created_at).toLocaleString() : '-';
  const detailsText = formatSystemLogDetails(entry);
  let html = '';
  html += renderSystemLogDetailRow(t('systemLogs.time'), esc(timeText));
  html += renderSystemLogDetailRow(
    t('systemLogs.level'),
    '<span class="system-log-level ' + systemLogLevelClass(entry.level) + '">' +
      esc((entry.level || 'info').toUpperCase()) + '</span>'
  );
  html += renderSystemLogDetailRow(t('systemLogs.category'), esc(entry.category || '-'));
  html += renderSystemLogDetailRow(t('systemLogs.stage'), esc(entry.stage || '-'), true);
  html += renderSystemLogDetailRow(t('systemLogs.message'), esc(entry.message || '-'));
  if (entry.trace_id) {
    html += renderSystemLogDetailRow(t('systemLogs.trace'), esc(entry.trace_id), true);
  }
  if (entry.watch_id) {
    html += renderSystemLogDetailRow(t('systemLogs.watch'), esc(entry.watch_id), true);
  }
  if (entry.source_chat_id) {
    html += renderSystemLogDetailRow(t('systemLogs.sourceChat'), esc(String(entry.source_chat_id)), true);
  }
  if (entry.source_message_id != null && entry.source_message_id !== '') {
    html += renderSystemLogDetailRow(t('systemLogs.sourceMessage'), esc(String(entry.source_message_id)), true);
  }
  if (entry.target_link) {
    html += renderSystemLogDetailRow(t('systemLogs.target'), esc(entry.target_link), true);
  }
  if (detailsText) {
    html += renderSystemLogDetailRow(
      t('systemLogs.details'),
      '<pre class="system-log-detail-json">' + esc(detailsText) + '</pre>'
    );
  }
  body.innerHTML = html;
  overlay.classList.add('open');
}

function closeSystemLogDetailModal() {
  $('#system-log-detail-overlay')?.classList.remove('open');
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
        '<td class="whitespace-nowrap">' + esc(timeText) + '</td>' +
        '<td><span class="system-log-level ' + systemLogLevelClass(entry.level) + '">' + esc((entry.level || 'info').toUpperCase()) + '</span></td>' +
        '<td>' + esc(entry.category || '-') + '</td>' +
        '<td class="font-mono">' + esc(entry.stage || '-') + '</td>' +
        '<td>' + esc(entry.message || '') + '</td>' +
        '<td class="text-muted font-mono system-log-context" title="' + esc(context) + '">' + esc(context) + '</td>' +
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

function systemLogsFilterQuery() {
  const category = $('#system-logs-category')?.value || '';
  const level = $('#system-logs-level')?.value || '';
  const todayOnly = $('#system-logs-today')?.checked ? '1' : '0';
  return '?today=' + todayOnly
    + (category ? '&category=' + encodeURIComponent(category) : '')
    + (level ? '&level=' + encodeURIComponent(level) : '');
}

async function downloadSystemLogsAll() {
  const btn = $('#system-logs-download-btn');
  if (btn && btn.disabled) return;
  const originalLabel = btn ? btn.textContent : '';
  if (btn) {
    btn.disabled = true;
    btn.textContent = t('systemLogs.downloading');
  }
  try {
    const query = withClientTzQuery('/api/system-logs/export' + systemLogsFilterQuery());
    const resp = await fetch(query, { credentials: 'same-origin' });
    if (resp.status === 401) {
      redirectToLoginPage();
      return;
    }
    if (!resp.ok) throw new Error('download_failed');
    const text = await resp.text();
    if (!text.trim()) {
      alert(t('systemLogs.downloadEmpty'));
      return;
    }
    const disposition = resp.headers.get('content-disposition') || '';
    const match = disposition.match(/filename=\"([^\"]+)\"/);
    const filename = match ? match[1] : ('system-logs-' + Date.now() + '.txt');
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    if (e && e.error_code === 'auth_required') redirectToLoginPage();
    else alert(t('systemLogs.downloadFailed'));
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalLabel || t('systemLogs.downloadAll');
    }
  }
}

syncSystemLogsAutoRefreshUI();

$('#system-logs-refresh-btn')?.addEventListener('click', function() { loadSystemLogs(1); });
$('#system-logs-copy-btn')?.addEventListener('click', copySystemLogsPage);
$('#system-logs-download-btn')?.addEventListener('click', downloadSystemLogsAll);
$('#system-logs-category')?.addEventListener('change', function() { state.systemLogsPage = 1; loadSystemLogs(1); });
$('#system-logs-level')?.addEventListener('change', function() { state.systemLogsPage = 1; loadSystemLogs(1); });
$('#system-logs-today')?.addEventListener('change', function() { state.systemLogsPage = 1; loadSystemLogs(1); });
$('#system-logs-auto-refresh')?.addEventListener('change', function() {
  setSystemLogsAutoRefreshEnabled(this.checked);
  if (this.checked) startSystemLogsAutoRefresh();
  else stopSystemLogsAutoRefresh();
});
$('#system-logs-tbody')?.addEventListener('click', function(e) {
  const row = e.target.closest('.system-log-row');
  if (!row) return;
  const logId = row.dataset.logId;
  const entry = (state.systemLogs || []).find(function(item) {
    return String(item.id) === String(logId);
  });
  if (entry) openSystemLogDetailModal(entry);
});
$('#system-log-detail-close')?.addEventListener('click', closeSystemLogDetailModal);
$('#system-log-detail-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeSystemLogDetailModal();
});

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

function buildWatchRowHtml(w) {
  const typeLabel = w.type === 'download' ? t('watches.download') : t('watches.forward');
  const typeCls = w.type === 'download' ? 'badge-success' : 'badge-running';
  const statusCls = w.status === 'paused' ? 'paused' : 'running';
  const statusLabel = w.status === 'paused' ? t('status.paused') : t('status.running');
  const eventCount = Number(w.event_count || 0);
  const todayCount = w.today_count || 0;
  const deferredCount = Number(w.deferred_comment_count || 0);
  const source = w.source_link || '-';
  const target = w.target_link || '本地';
  const sourceShort = globalThis.WatchUiHelpers && typeof globalThis.WatchUiHelpers.shortTelegramLink === 'function'
    ? globalThis.WatchUiHelpers.shortTelegramLink(source)
    : source;
  const targetShort = globalThis.WatchUiHelpers && typeof globalThis.WatchUiHelpers.shortTelegramLink === 'function'
    ? globalThis.WatchUiHelpers.shortTelegramLink(target)
    : target;
  const deferredBadge = w.type === 'forward' && w.include_comment && deferredCount > 0
    ? '<button class="watch-deferred-badge" data-watch-detail="' + esc(w.id) + '" data-watch-detail-mode="deferred">' +
        esc(t('watches.deferredComments')) + ' ' + deferredCount +
      '</button>'
    : '';
  const historyLabel = t('watches.historyTitle');
  const downloadLabel = t('watches.downloadRecordsTitle');
  const queueCount = Number(w.download_queue_count || 0);
  const completedDownloadCount = Number(w.download_completed_count || 0);
  const queueCell = w.type === 'forward'
    ? (queueCount > 0
      ? '<button type="button" class="watch-count-btn" data-watch-detail="' + esc(w.id) + '" data-watch-detail-mode="downloads" title="' + esc(downloadLabel) + '" aria-label="' + esc(t('watches.downloadQueueCount') + ': ' + queueCount) + '">' + esc(String(queueCount)) + '</button>'
      : esc(String(queueCount)))
    : '—';
  const completedDownloadCell = w.type === 'forward'
    ? (completedDownloadCount > 0
      ? '<button type="button" class="watch-count-btn watch-count-btn--primary" data-watch-detail="' + esc(w.id) + '" data-watch-detail-mode="downloads" title="' + esc(downloadLabel) + '" aria-label="' + esc(t('watches.downloadCompletedCount') + ': ' + completedDownloadCount) + '">' + esc(String(completedDownloadCount)) + '</button>'
      : esc(String(completedDownloadCount)))
    : '—';
  const todayCell = w.type === 'forward'
    ? '<button type="button" class="watch-count-btn" data-watch-detail="' + esc(w.id) + '" data-watch-detail-mode="history" data-watch-detail-today="1" title="' + esc(historyLabel) + '" aria-label="' + esc(t('watches.todayEvents') + ': ' + todayCount) + '">' + esc(String(todayCount)) + '</button>'
    : esc(String(todayCount));
  const totalCell = w.type === 'forward'
    ? '<button type="button" class="watch-count-btn watch-count-btn--primary" data-watch-detail="' + esc(w.id) + '" data-watch-detail-mode="history" data-watch-detail-today="0" title="' + esc(historyLabel) + '" aria-label="' + esc(t('watches.totalEvents') + ': ' + eventCount) + '">' + esc(String(eventCount)) + '</button>'
    : esc(String(eventCount));
  return '<tr class="watch-row" data-watch-id="' + esc(w.id) + '">' +
    '<td class="watch-col-text"><span class="badge ' + typeCls + '">' + typeLabel + '</span></td>' +
    '<td class="watch-col-text font-mono max-w-[200px]" title="' + esc(source) + '"><span class="watch-cell-text">' + esc(sourceShort) + '</span></td>' +
    '<td class="watch-col-text font-mono max-w-[160px]" title="' + esc(target) + '"><span class="watch-cell-text">' + esc(targetShort) + '</span></td>' +
    '<td class="watch-col-metric"><span class="watch-status-cell"><span class="watch-status-dot ' + statusCls + '" aria-hidden="true"></span>' + esc(statusLabel) + '</span></td>' +
    '<td class="watch-col-metric font-semibold tabular-nums">' + queueCell + '</td>' +
    '<td class="watch-col-metric font-semibold tabular-nums">' + completedDownloadCell + '</td>' +
    '<td class="watch-col-metric font-semibold tabular-nums">' + todayCell + '</td>' +
    '<td class="watch-col-metric font-semibold tabular-nums text-primary">' + totalCell + '</td>' +
    '<td class="watch-col-actions">' +
      '<div class="table-actions">' +
        deferredBadge +
        '<button class="btn btn-sm btn-icon" data-watch-menu="' + esc(w.id) + '" aria-haspopup="menu" aria-label="' + esc(t('watches.moreActions')) + '">⋯</button>' +
      '</div>' +
    '</td>' +
    '</tr>';
}

function fillWatchTable(tbody, empty, watches) {
  if (!tbody || !empty) return;
  if (!watches.length) {
    tbody.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';
  tbody.innerHTML = watches.map(buildWatchRowHtml).join('');
}

function renderWatches() {
  if (state.activeView !== 'watches') return;
  closeWatchOverflowMenu();
  const helpers = globalThis.WatchUiHelpers || {};
  const groups = typeof helpers.partitionWatchesByComment === 'function'
    ? helpers.partitionWatchesByComment(state.watches || [])
    : { withoutComment: state.watches || [], withComment: [] };
  fillWatchTable($('#watches-tbody'), $('#watches-empty'), groups.withoutComment || []);
  fillWatchTable($('#watches-tbody-comment'), $('#watches-empty-comment'), groups.withComment || []);
}

function hasExpandedWatch() {
  return Boolean(state.watchDetail);
}

function buildWatchMenuItems(watch) {
  const items = [];
  const deferredCount = Number(watch && watch.deferred_comment_count || 0);
  if (watch && watch.type === 'forward') {
    items.push({ action: 'edit', label: t('watches.edit') });
    items.push({ action: 'downloads', label: t('watches.downloadRecords') });
    if (watch.include_comment) {
      items.push({ action: 'deferred', label: t('watches.deferredComments') + (deferredCount ? ' ' + deferredCount : '') });
    }
  }
  items.push({ action: 'delete', label: t('tasks.delete'), danger: true });
  return items;
}

function closeWatchOverflowMenu() {
  const menu = document.querySelector('.watch-overflow-menu');
  if (menu) menu.remove();
  state.watchOverflowMenu = null;
  $$('[data-watch-menu][aria-expanded="true"]').forEach(function(btn) {
    btn.setAttribute('aria-expanded', 'false');
  });
}

function openWatchOverflowMenu(watchId, anchor) {
  const watch = (state.watches || []).find(function(item) { return item.id === watchId; });
  if (!watch || !anchor) return;
  if (state.watchOverflowMenu && state.watchOverflowMenu.watchId === watchId) {
    closeWatchOverflowMenu();
    return;
  }
  closeWatchOverflowMenu();
  const menu = document.createElement('div');
  menu.className = 'watch-overflow-menu';
  menu.setAttribute('role', 'menu');
  menu.dataset.watchId = watchId;
  menu.innerHTML = buildWatchMenuItems(watch).map(function(item) {
    return '<button class="watch-overflow-item' + (item.danger ? ' danger' : '') + '" role="menuitem" data-watch-menu-action="' + item.action + '" data-watch-id="' + esc(watchId) + '">' +
      esc(item.label) +
      '</button>';
  }).join('');
  document.body.appendChild(menu);

  const rect = anchor.getBoundingClientRect();
  const menuRect = menu.getBoundingClientRect();
  const viewportPadding = 8;
  const left = Math.min(
    Math.max(viewportPadding, rect.right - menuRect.width),
    window.innerWidth - menuRect.width - viewportPadding
  );
  const below = rect.bottom + 6;
  const above = rect.top - menuRect.height - 6;
  const top = below + menuRect.height <= window.innerHeight - viewportPadding
    ? below
    : Math.max(viewportPadding, above);
  menu.style.left = left + 'px';
  menu.style.top = top + 'px';
  anchor.setAttribute('aria-expanded', 'true');
  state.watchOverflowMenu = { watchId: watchId };
}

async function openWatchDetail(watchId, mode, options) {
  closeWatchOverflowMenu();
  const overlay = $('#watch-detail-overlay');
  const body = $('#watch-detail-body');
  if (!overlay || !body) return;
  stopWatchDownloadPolling();
  const watch = findWatchById(watchId);
  const detailMode = mode || 'history';
  const opts = options || {};
  state.watchDetail = {
    watchId: watchId,
    mode: detailMode,
    page: 1,
    pageSize: 20,
    total: 0,
    filter: 'all',
    todayOnly: detailMode === 'history' ? Boolean(opts.todayOnly) : false,
    items: [],
    statusCounts: null,
  };
  if (detailMode === 'downloads') {
    state.watchDownload = { watchId: watchId, tasks: [], counts: {} };
  }
  renderWatchDetailShell(watch, detailMode);
  overlay.classList.add('open');
  document.body.dataset.watchDetailScrollLock = document.body.style.overflow || '';
  document.body.style.overflow = 'hidden';
  await loadWatchDetail(false);
  if (detailMode === 'downloads') startWatchDownloadPolling();
}

function findWatchById(watchId) {
  return (state.watches || []).find(function(watch) {
    return String(watch.id) === String(watchId);
  }) || null;
}

function watchDetailHelpers() {
  return globalThis.WatchUiHelpers || {};
}

function formatWatchRouteForDetail(source, target) {
  const helpers = watchDetailHelpers();
  if (typeof helpers.formatWatchRoute === 'function') {
    return helpers.formatWatchRoute(source, target);
  }
  return (source || '-') + ' → ' + (target || '本地');
}

function summarizeWatchEventForDetail(evt) {
  const helpers = watchDetailHelpers();
  if (typeof helpers.summarizeWatchEvent === 'function') {
    return helpers.summarizeWatchEvent(evt);
  }
  if (evt && evt.status === 'success') return { kind: 'success', titleKey: 'watches.eventForwarded', detail: '' };
  if (evt && evt.status === 'skipped') return { kind: 'filtered', titleKey: 'watches.eventSkipped', detail: evt.message || '' };
  return { kind: 'failure', titleKey: 'watches.eventFailed', detail: evt && evt.message || '' };
}

function filterWatchEventsForDetail(items, filter) {
  const helpers = watchDetailHelpers();
  if (typeof helpers.filterWatchEventsByStatus === 'function') {
    return helpers.filterWatchEventsByStatus(items, filter);
  }
  if (!filter || filter === 'all') return (items || []).slice();
  return (items || []).filter(function(evt) {
    return summarizeWatchEventForDetail(evt).kind === filter;
  });
}

function watchHistoryStatusQuery(filter) {
  if (filter === 'success') return 'success';
  if (filter === 'filtered') return 'skipped';
  if (filter === 'failure') return 'failure';
  return '';
}

function watchDetailModeTitle(mode) {
  if (mode === 'downloads') return t('watches.downloadRecordsTitle');
  if (mode === 'deferred') return t('watches.deferredComments');
  return t('watches.historyTitle');
}

function renderWatchDetailShell(watch, mode) {
  const source = watch && watch.source_link || '-';
  const target = watch && (watch.target_link || '本地') || '本地';
  const title = $('#watch-detail-title');
  const subtitle = $('#watch-detail-subtitle');
  const summary = $('#watch-detail-summary');
  const filters = $('#watch-detail-filters');
  const body = $('#watch-detail-body');
  const footer = $('#watch-detail-footer');
  if (title) title.textContent = watchDetailModeTitle(mode);
  if (subtitle) subtitle.textContent = formatWatchRouteForDetail(source, target);
  if (summary) summary.textContent = '';
  if (filters) filters.innerHTML = '';
  if (body) body.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';
  if (footer) footer.innerHTML = '';
}

async function loadWatchDetail(silent) {
  const detail = state.watchDetail;
  if (!detail || !detail.watchId) return;
  if (detail.mode === 'downloads') {
    await loadWatchDownloadRecords(silent);
    return;
  }
  if (detail.mode === 'deferred') {
    await loadWatchDeferred(detail.watchId, silent);
    return;
  }
  await loadWatchDetailHistory(silent);
}

async function loadWatchDetailHistory(silent) {
  const detail = state.watchDetail;
  const body = $('#watch-detail-body');
  const footer = $('#watch-detail-footer');
  if (!body || !footer || !detail || !detail.watchId) return;
  const page = detail.page || 1;
  const pageSize = detail.pageSize || 20;
  const offset = (page - 1) * pageSize;
  if (!silent) body.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';
  footer.innerHTML = '';
  try {
    const status = watchHistoryStatusQuery(detail.filter);
    let url = '/api/watches/' + encodeURIComponent(detail.watchId) + '/events?limit=' + pageSize + '&offset=' + offset;
    if (status) url += '&status=' + encodeURIComponent(status);
    if (detail.todayOnly) url += '&today=1';
    const data = await fetchJson(withClientTzQuery(url));
    const items = data.events || [];
    const total = Number(data.total || 0);
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const statusCounts = data.status_counts || {
      all: total,
      success: 0,
      skipped: 0,
      failure: 0,
    };
    detail.items = items;
    detail.total = total;
    detail.statusCounts = statusCounts;
    renderWatchDetailHistorySummary();
    renderWatchDetailHistoryFilters(statusCounts);
    body.innerHTML = renderWatchHistoryList(items);
    footer.innerHTML = renderPaginationBar({
      prefix: 'watch-detail-history',
      page: page,
      pageSize: pageSize,
      total: total,
      pageInfoKey: 'watches.pageInfo'
    });
    bindPaginationBar('watch-detail-history', page, totalPages, function(newPage) {
      if (!state.watchDetail) return;
      state.watchDetail.page = newPage;
      loadWatchDetailHistory(false);
    });
  } catch(e) {
    body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + esc(t('form.requestFailed')) + '</div>';
  }
}

function renderWatchDetailHistorySummary() {
  const summary = $('#watch-detail-summary');
  const detail = state.watchDetail;
  if (!summary || !detail || detail.mode !== 'history') return;
  const watch = findWatchById(detail.watchId);
  const today = watch ? Number(watch.today_count || 0) : 0;
  const total = watch ? Number(watch.event_count || 0) : 0;
  summary.innerHTML =
    '<div class="watch-range-tabs" role="tablist" aria-label="' + esc(t('watches.historyTitle')) + '">' +
      '<button type="button" class="panel-tab' + (detail.todayOnly ? ' active' : '') + '" role="tab" aria-selected="' + (detail.todayOnly ? 'true' : 'false') + '" data-watch-detail-range="today">' +
        esc(t('watches.todayEvents')) + ' (' + today + ')' +
      '</button>' +
      '<button type="button" class="panel-tab' + (!detail.todayOnly ? ' active' : '') + '" role="tab" aria-selected="' + (!detail.todayOnly ? 'true' : 'false') + '" data-watch-detail-range="all">' +
        esc(t('watches.totalEvents')) + ' (' + total + ')' +
      '</button>' +
    '</div>';
}

function renderWatchDetailHistoryFilters(statusCounts) {
  const filters = $('#watch-detail-filters');
  const detail = state.watchDetail;
  if (!filters || !detail) return;
  const counts = statusCounts || {};
  const chips = [
    { key: 'all', label: t('watches.filterAll'), count: Number(counts.all || 0) },
    { key: 'success', label: t('watches.filterSuccess'), count: Number(counts.success || 0) },
    { key: 'filtered', label: t('watches.filterFiltered'), count: Number(counts.skipped || 0) },
    { key: 'failure', label: t('watches.filterFailure'), count: Number(counts.failure || 0) },
  ];
  filters.innerHTML = chips.map(function(chip) {
    return '<button type="button" class="panel-tab' + (detail.filter === chip.key ? ' active' : '') + '" data-watch-detail-filter="' + chip.key + '">' +
      esc(chip.label) + ' (' + chip.count + ')' +
      '</button>';
  }).join('');
}

function renderWatchHistoryList(items) {
  if (!items.length) {
    return '<div class="p-8 text-center text-muted text-sm">' + esc(t('watches.noEvents')) + '</div>';
  }
  return '<div class="watch-detail-list">' + items.map(function(evt, idx) {
    const sum = summarizeWatchEventForDetail(evt);
    const badgeCls = sum.kind === 'success' ? 'badge-success'
      : sum.kind === 'filtered' ? 'badge-warning'
      : 'badge-failed';
    const badgeText = sum.badgeKey ? t(sum.badgeKey) : (sum.titleKey ? t(sum.titleKey) : '');
    const title = (sum.title != null && sum.title !== '')
      ? sum.title
      : (sum.titleKey ? t(sum.titleKey) : '');
    const meta = '#' + (evt.source_message_id || '-') + ' · ' + fmtTime(evt.created_at);
    const detailId = 'watch-evt-detail-' + idx;
    const canExpand = Boolean(sum.detail);
    return '<div class="watch-detail-row"' + (canExpand ? ' data-expand-detail="' + detailId + '"' : '') + '>' +
      '<span class="badge ' + badgeCls + '">' + esc(badgeText) + '</span>' +
      '<div class="watch-detail-row-main">' +
        (title ? '<div class="font-medium">' + esc(title) + '</div>' : '') +
        '<div class="text-xs text-muted">' + esc(meta) +
          (canExpand ? ' · ' + esc(t('watches.detailExpandReason')) : '') +
        '</div>' +
        (canExpand ? '<div id="' + detailId + '" class="watch-detail-reason hidden text-xs text-muted mt-1">' + esc(sum.detail) + '</div>' : '') +
      '</div>' +
    '</div>';
  }).join('') + '</div>';
}

function closeWatchDetail() {
  stopWatchDownloadPolling();
  state.watchDetail = null;
  state.watchDownload = { watchId: null, tasks: [], counts: {} };
  $('#watch-detail-overlay')?.classList.remove('open');
  if (Object.prototype.hasOwnProperty.call(document.body.dataset, 'watchDetailScrollLock')) {
    document.body.style.overflow = document.body.dataset.watchDetailScrollLock;
    delete document.body.dataset.watchDetailScrollLock;
  }
  const body = $('#watch-detail-body');
  const filters = $('#watch-detail-filters');
  const footer = $('#watch-detail-footer');
  if (body) body.innerHTML = '';
  if (filters) filters.innerHTML = '';
  if (footer) footer.innerHTML = '';
}

/* ====== Watch Download Records Modal ====== */
let watchDownloadPollTimer = null;

function watchDownloadBucket(status) {
  if (status === 'failure') return 'failed';
  if (status === 'success' || status === 'skipped') return 'completed';
  return 'active';
}

function renderWatchDownloadTaskRow(task) {
  const progressPct = watchDownloadProgressPercent(task);
  const title = watchDownloadTitle(task);
  const route = formatWatchRouteForDetail(task.source_link || '-', task.target_profile || task.target_link || '-');
  const fileDetail = taskFileTransferDetail(task);
  const activeSummary = activeTransferSummary(task);
  const showProgress = task.uses_range_progress || task.total_items > 0 ||
    Boolean(fileDetail) || Number(task.active_progress_total || 0) > 0;
  let progressHtml = '';
  if (showProgress) {
    progressHtml =
      '<div class="task-row-progress">' +
        '<span class="task-row-progress-pct">' + progressPct + '%</span>' +
        '<div class="task-row-progress-bar">' +
          '<div class="progress-fill" style="width:' + progressPct + '%"></div>' +
        '</div>' +
        '<span class="task-row-progress-count">' + taskCompletedLabel(task) + '</span>' +
      '</div>';
    if (fileDetail) {
      progressHtml +=
        '<div class="task-row-progress-summary task-row-progress-file" title="' + esc(fileDetail) + '">' +
          esc(fileDetail) +
        '</div>';
    } else if (activeSummary) {
      progressHtml +=
        '<div class="task-row-progress-summary" title="' + esc(activeSummary) + '">' +
          esc(activeSummary) +
        '</div>';
    }
  }
  const retryBtn = task.can_retry
    ? '<button class="task-icon-btn btn-danger" data-watch-download-retry="' + task.id + '" title="' + t('tasks.retryFailed') + '">' + TASK_ICON_RETRY + '</button>'
    : '';
  const deleteBtn = task.can_delete
    ? '<button class="task-icon-btn btn-danger" data-watch-download-delete="' + task.id + '" title="' + t('tasks.delete') + '">' + TASK_ICON_DELETE + '</button>'
    : '';
  return '<div class="task-row watch-download-row" data-task-id="' + task.id + '">' +
    '<div class="task-row-id">#' + task.id + '</div>' +
    '<div class="task-row-status">' + statusBadge(task.status) + '</div>' +
    '<div class="task-row-main" title="' + esc(title) + ' · ' + esc(route) + '">' +
      '<div class="task-row-title">' + esc(title) + '</div>' +
      '<div class="task-row-route">' + esc(route) + '</div>' +
    '</div>' +
    '<div class="task-row-actions"><div class="task-row-actions-inner">' + retryBtn + deleteBtn + '</div></div>' +
    progressHtml +
  '</div>';
}

function renderWatchDownloadSections(tasks) {
  const groups = { active: [], completed: [], failed: [] };
  (tasks || []).forEach(function(task) {
    groups[watchDownloadBucket(task.status)].push(task);
  });
  const sections = [
    { key: 'active', label: t('watches.downloadActive') },
    { key: 'completed', label: t('watches.downloadCompleted') },
    { key: 'failed', label: t('watches.downloadFailed') },
  ];
  let html = '';
  sections.forEach(function(section) {
    const items = groups[section.key] || [];
    html += '<div class="watch-download-section">' +
      '<div class="watch-download-section-title">' + esc(section.label) + ' (' + items.length + ')</div>';
    if (!items.length) {
      html += '<div class="watch-expand-empty">' + esc(t('watches.downloadRecordsEmpty')) + '</div>';
    } else {
      html += '<div class="watch-download-list">' + items.map(renderWatchDownloadTaskRow).join('') + '</div>';
    }
    html += '</div>';
  });
  return html;
}

async function loadWatchDownloadRecords(silent) {
  const body = $('#watch-detail-body');
  if (!body || !state.watchDownload || !state.watchDownload.watchId) return;
  if (!silent) {
    body.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';
  }
  try {
    const data = await fetchJson('/api/watches/' + encodeURIComponent(state.watchDownload.watchId) + '/download-tasks');
    state.watchDownload.tasks = data.tasks || [];
    state.watchDownload.counts = data.counts || {};
    renderWatchDownloadSummary(state.watchDownload.tasks, state.watchDownload.counts);
    body.innerHTML = renderWatchDownloadSections(state.watchDownload.tasks);
  } catch (e) {
    if (!silent) {
      body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + esc(t('form.requestFailed')) + '</div>';
    }
  }
}

function startWatchDownloadPolling() {
  stopWatchDownloadPolling();
  watchDownloadPollTimer = setInterval(function() {
    const overlay = $('#watch-detail-overlay');
    if (!overlay || !overlay.classList.contains('open') || !state.watchDetail || state.watchDetail.mode !== 'downloads') {
      stopWatchDownloadPolling();
      return;
    }
    loadWatchDownloadRecords(true).catch(function() {});
  }, 3000);
}

function stopWatchDownloadPolling() {
  if (watchDownloadPollTimer) {
    clearInterval(watchDownloadPollTimer);
    watchDownloadPollTimer = null;
  }
}

function renderWatchDownloadSummary(tasks, counts) {
  const summary = $('#watch-detail-summary');
  if (!summary) return;
  const bucketCounts = { active: 0, completed: 0, failed: 0 };
  (tasks || []).forEach(function(task) {
    bucketCounts[watchDownloadBucket(task.status)] += 1;
  });
  counts = counts || {};
  const active = Number(counts.active != null ? counts.active : bucketCounts.active);
  const completed = Number(counts.completed != null ? counts.completed : bucketCounts.completed);
  const failed = Number(counts.failed != null ? counts.failed : bucketCounts.failed);
  summary.textContent = t('watches.downloadActive') + ' ' + active +
    ' · ' + t('watches.downloadCompleted') + ' ' + completed +
    ' · ' + t('watches.downloadFailed') + ' ' + failed;
}

/* watch form */
$('#watch-download-form')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fd = new FormData(this);
  const links = fd.get('source_links').split('\n').map(l => l.trim()).filter(Boolean);
  try {
    await postJson('/api/watches', {
      type: 'download',
      source_links: links,
      media_types: readMediaTypesOverride(this),
    });
    await loadWatches();
    this.reset();
    setMediaTypesPicker(this.querySelector('[data-media-types-picker]'), null);
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
      media_types: readMediaTypesOverride(this),
    });
    await loadWatches();
    this.reset();
    setMediaTypesPicker(this.querySelector('[data-media-types-picker]'), null);
  } catch(err) {
    alert(translateApiError(err, 'form.createFailed'));
  }
});

document.addEventListener('click', async function(e) {
  const menuBtn = e.target.closest('[data-watch-menu]');
  if (menuBtn) {
    e.stopPropagation();
    openWatchOverflowMenu(menuBtn.dataset.watchMenu, menuBtn);
    return;
  }

  const menuActionBtn = e.target.closest('[data-watch-menu-action]');
  if (menuActionBtn) {
    e.stopPropagation();
    const watchId = menuActionBtn.dataset.watchId;
    const action = menuActionBtn.dataset.watchMenuAction;
    if (action === 'edit') {
      closeWatchOverflowMenu();
      openEditWatchModal(watchId);
      return;
    }
    if (action === 'downloads' || action === 'deferred') {
      await openWatchDetail(watchId, action);
      return;
    }
    if (action === 'delete') {
      closeWatchOverflowMenu();
      if (!confirm('确定移除这个监听？')) return;
      try {
        const resp = await fetch('/api/watches/' + encodeURIComponent(watchId), { method: 'DELETE' });
        if (!resp.ok) {
          let data = {};
          try { data = await resp.json(); } catch(err) {}
          alert(data.detail || data.error || data.message || t('form.requestFailed'));
          return;
        }
        await loadWatches();
      } catch(err) {}
      return;
    }
  }

  const detailBtn = e.target.closest('[data-watch-detail]');
  if (detailBtn) {
    e.stopPropagation();
    const todayAttr = detailBtn.dataset.watchDetailToday;
    const options = {};
    if (todayAttr === '1') options.todayOnly = true;
    if (todayAttr === '0') options.todayOnly = false;
    await openWatchDetail(detailBtn.dataset.watchDetail, detailBtn.dataset.watchDetailMode, options);
    return;
  }

  if (!e.target.closest('.watch-overflow-menu')) {
    closeWatchOverflowMenu();
  }

  const delBtn = e.target.closest('[data-delete-watch]');
  if (delBtn) {
    closeWatchOverflowMenu();
    if (!confirm('确定移除这个监听？')) return;
    try {
      await fetch('/api/watches/' + encodeURIComponent(delBtn.dataset.deleteWatch), { method: 'DELETE' });
      await loadWatches();
    } catch(err) {}
  }
  const editBtn = e.target.closest('[data-edit-watch]');
  if (editBtn) {
    closeWatchOverflowMenu();
    openEditWatchModal(editBtn.dataset.editWatch);
  }
  const historyBtn = e.target.closest('[data-watch-history]');
  if (historyBtn) {
    await openWatchDetail(historyBtn.dataset.watchHistory, 'history');
  }
  const downloadsBtn = e.target.closest('[data-watch-downloads]');
  if (downloadsBtn) {
    await openWatchDetail(downloadsBtn.dataset.watchDownloads, 'downloads');
  }
  const deferredBtn = e.target.closest('[data-watch-deferred]');
  if (deferredBtn) {
    await openWatchDetail(deferredBtn.dataset.watchDeferred, 'deferred');
  }
  const runNowBtn = e.target.closest('[data-deferred-run-now]');
  if (runNowBtn) {
    await postDeferredAction(runNowBtn.dataset.watchId, runNowBtn.dataset.deferredRunNow, 'run-now');
  }
  const cancelDeferredBtn = e.target.closest('[data-deferred-cancel]');
  if (cancelDeferredBtn) {
    await postDeferredAction(cancelDeferredBtn.dataset.watchId, cancelDeferredBtn.dataset.deferredCancel, 'cancel');
  }
  const retryDeferredBtn = e.target.closest('[data-deferred-retry]');
  if (retryDeferredBtn) {
    await postDeferredAction(retryDeferredBtn.dataset.watchId, retryDeferredBtn.dataset.deferredRetry, 'retry');
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
  return openWatchDetail(watchId, 'deferred');
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
      let actions = '<span class="text-xs text-muted">—</span>';
      if (item.status === 'pending') {
        actions = '<div class="table-actions flex gap-1">' +
          '<button class="btn btn-sm" data-watch-id="' + esc(watchId) + '" data-deferred-run-now="' + esc(String(item.id)) + '">' + esc(t('watches.deferredRunNow')) + '</button>' +
          '<button class="btn btn-sm btn-danger" data-watch-id="' + esc(watchId) + '" data-deferred-cancel="' + esc(String(item.id)) + '">' + esc(t('watches.deferredCancel')) + '</button>' +
          '</div>';
      } else if (item.status === 'running') {
        actions = '<div class="table-actions flex gap-1">' +
          '<button class="btn btn-sm btn-danger" data-watch-id="' + esc(watchId) + '" data-deferred-cancel="' + esc(String(item.id)) + '">' + esc(t('watches.deferredCancel')) + '</button>' +
          '</div>';
      } else if (item.status === 'failure' || item.status === 'cancelled') {
        actions = '<div class="table-actions flex gap-1">' +
          '<button class="btn btn-sm" data-watch-id="' + esc(watchId) + '" data-deferred-retry="' + esc(String(item.id)) + '">' + esc(t('watches.deferredRetry')) + '</button>' +
          '</div>';
      }
      const statusCls = item.status === 'pending' ? 'badge-warning'
        : item.status === 'running' ? 'badge-running'
        : item.status === 'done' ? 'badge-success'
        : item.status === 'failure' ? 'badge-failed'
        : 'badge-paused';
      return '<tr>' +
        '<td class="font-mono text-muted">#' + esc(String(item.source_message_id || '-')) + '</td>' +
        '<td><span class="badge ' + statusCls + '">' + esc(deferredStatusLabel(item.status)) + '</span></td>' +
        '<td class="text-muted">' + esc(due) + '</td>' +
        '<td>' + actions + '</td>' +
      '</tr>';
    }).join('') +
    '</tbody></table>';
}

async function loadWatchDeferred(watchId, silent) {
  const body = $('#watch-detail-body');
  const filters = $('#watch-detail-filters');
  const footer = $('#watch-detail-footer');
  if (!body) return;
  if (filters) filters.innerHTML = '';
  if (footer) footer.innerHTML = '';
  if (!silent) body.innerHTML = '<div class="p-8 text-center"><div class="spinner mx-auto"></div></div>';
  try {
    const res = await fetch('/api/watches/' + encodeURIComponent(watchId) + '/deferred-comments');
    const data = await res.json();
    if (!res.ok) {
      body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + esc(data.error || t('form.requestFailed')) + '</div>';
      return;
    }
    const items = data.captures || [];
    renderWatchDeferredSummary(items);
    if (!items.length) {
      body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + esc(t('watches.noDeferredComments')) + '</div>';
      return;
    }
    body.innerHTML = '<div class="watch-expand-scroll">' + renderDeferredCommentRows(watchId, items) + '</div>';
  } catch (err) {
    body.innerHTML = '<div class="p-8 text-center text-muted text-sm">' + esc(t('form.requestFailed')) + '</div>';
  }
}

function renderWatchDeferredSummary(items) {
  const summary = $('#watch-detail-summary');
  if (!summary) return;
  const counts = { pending: 0, running: 0, done: 0, cancelled: 0, failure: 0 };
  (items || []).forEach(function(item) {
    if (counts[item.status] === undefined) counts[item.status] = 0;
    counts[item.status] += 1;
  });
  summary.textContent = '全部 ' + (items || []).length +
    ' · ' + t('watches.deferredPending') + ' ' + counts.pending +
    ' · ' + t('watches.deferredRunning') + ' ' + counts.running +
    ' · ' + t('watches.deferredFailure') + ' ' + counts.failure;
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
    if (state.watchDetail && String(state.watchDetail.watchId) === String(watchId) && state.watchDetail.mode === 'deferred') {
      await loadWatchDeferred(watchId, true);
    }
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
  ensureOverrideMediaTypeGrids();
  setMediaTypesPicker($('#watch-edit-media-types-picker'), watch.media_types);
  $('#watch-edit-overlay').classList.add('open');
}

function closeEditWatchModal() {
  $('#watch-edit-overlay').classList.remove('open');
}

$('#watch-edit-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeEditWatchModal();
});

$('#watch-detail-close')?.addEventListener('click', closeWatchDetail);
$('#watch-detail-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeWatchDetail();
});
$('#watch-detail-summary')?.addEventListener('click', function(e) {
  const btn = e.target.closest('[data-watch-detail-range]');
  if (!btn || !state.watchDetail || state.watchDetail.mode !== 'history') return;
  const nextTodayOnly = btn.dataset.watchDetailRange === 'today';
  if (Boolean(state.watchDetail.todayOnly) === nextTodayOnly) return;
  state.watchDetail.todayOnly = nextTodayOnly;
  state.watchDetail.filter = 'all';
  state.watchDetail.page = 1;
  loadWatchDetailHistory(false);
});
$('#watch-detail-filters')?.addEventListener('click', function(e) {
  const btn = e.target.closest('[data-watch-detail-filter]');
  if (!btn || !state.watchDetail || state.watchDetail.mode !== 'history') return;
  const nextFilter = btn.dataset.watchDetailFilter || 'all';
  if (state.watchDetail.filter === nextFilter) return;
  state.watchDetail.filter = nextFilter;
  state.watchDetail.page = 1;
  loadWatchDetailHistory(false);
});
$('#watch-detail-body')?.addEventListener('click', async function(e) {
  const expandRow = e.target.closest('[data-expand-detail]');
  if (expandRow) {
    const detailId = expandRow.dataset.expandDetail;
    const detailEl = detailId ? document.getElementById(detailId) : null;
    if (detailEl) {
      const willOpen = detailEl.classList.contains('hidden');
      detailEl.classList.toggle('hidden', !willOpen);
      expandRow.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    }
    return;
  }

  const runNowBtn = e.target.closest('[data-deferred-run-now]');
  if (runNowBtn) {
    e.stopPropagation();
    await postDeferredAction(runNowBtn.dataset.watchId, runNowBtn.dataset.deferredRunNow, 'run-now');
    return;
  }
  const cancelDeferredBtn = e.target.closest('[data-deferred-cancel]');
  if (cancelDeferredBtn) {
    e.stopPropagation();
    await postDeferredAction(cancelDeferredBtn.dataset.watchId, cancelDeferredBtn.dataset.deferredCancel, 'cancel');
    return;
  }
  const retryDeferredBtn = e.target.closest('[data-deferred-retry]');
  if (retryDeferredBtn) {
    e.stopPropagation();
    await postDeferredAction(retryDeferredBtn.dataset.watchId, retryDeferredBtn.dataset.deferredRetry, 'retry');
    return;
  }

  const btn = e.target.closest('[data-watch-download-delete]');
  if (btn) {
    e.stopPropagation();
    const taskId = parseInt(btn.dataset.watchDownloadDelete, 10);
    if (!confirm('确定删除任务 #' + taskId + '？')) return;
    try {
      const resp = await fetch('/api/tasks/' + taskId, { method: 'DELETE' });
      if (!resp.ok) {
        let data = {};
        try { data = await resp.json(); } catch (err) {}
        alert(data.detail || data.error || data.message || '删除失败');
        return;
      }
      await loadWatchDownloadRecords(true);
    } catch (err) {
      alert('删除失败');
    }
    return;
  }

  const retryBtn = e.target.closest('[data-watch-download-retry]');
  if (!retryBtn) return;
  e.stopPropagation();
  const retryTaskId = parseInt(retryBtn.dataset.watchDownloadRetry, 10);
  try {
    const resp = await fetch('/api/tasks/' + retryTaskId + '/retry-failed', { method: 'POST' });
    if (!resp.ok) {
      let data = {};
      try { data = await resp.json(); } catch (err) {}
      alert(data.detail || data.error || data.message || '重试失败');
      return;
    }
    await loadWatchDownloadRecords(true);
  } catch (err) {
    alert('重试失败');
  }
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
        media_types: readMediaTypesOverride(this),
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
        '<td class="font-mono text-muted">' + esc(String(op.id || '-')) + '</td>' +
        '<td><span class="badge ' + (op.type === 'channel_download' ? 'badge-running' : 'badge-success') + '">' + esc(typeLabel) + '</span></td>' +
        '<td class="max-w-[220px] overflow-hidden text-ellipsis whitespace-nowrap">' + esc(detail) + '</td>' +
        '<td>' + statusBadge(op.status) + '</td>' +
        '<td class="text-danger max-w-[180px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(op.error_message || '') + '">' + esc(op.error_message || '-') + '</td>' +
        '<td class="text-muted">' + fmtTime(op.created_at) + '</td>' +
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
    ensureOverrideMediaTypeGrids();
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
  setFieldVal('global.deep_link.min_interval_seconds', sg.deep_link?.min_interval_seconds ?? 30);
  setFieldVal('global.deep_link.settle_seconds', sg.deep_link?.settle_seconds ?? 3);
  setFieldVal('global.deep_link.max_pages', sg.deep_link?.max_pages ?? 20);
  setFieldVal('global.deep_link.page_click_interval_seconds', sg.deep_link?.page_click_interval_seconds ?? 1);

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

  /* message filter + unified media type allowlist */
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
  const types = normalizeOptionList(options || MEDIA_TYPE_KEYS);
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

function ensureOverrideMediaTypeGrids() {
  const options = (state.settingsModel && state.settingsModel.options && state.settingsModel.options.message_filter_media_types)
    || (state.settingsSchema && state.settingsSchema.message_filter && state.settingsSchema.message_filter.media_types)
    || MEDIA_TYPE_KEYS;
  [
    'transfer-media-types-grid',
    'watch-download-media-types-grid',
    'watch-forward-media-types-grid',
    'watch-edit-media-types-grid',
  ].forEach(function(id) {
    const el = document.getElementById(id);
    if (!el || el.childElementCount) return;
    renderCheckboxGrid(id, 'override_media_types', MEDIA_TYPE_KEYS, options);
    el.querySelectorAll('input[type="checkbox"]').forEach(function(cb) { cb.checked = true; });
  });
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

$('#forward-watch-export-btn')?.addEventListener('click', async function() {
  const btn = this;
  if (btn.disabled) return;
  btn.disabled = true;
  try {
    await downloadForwardWatchBackup();
  } catch (e) {
    if (e && e.error_code === 'auth_required') redirectToLoginPage();
    else alert(t('settings.forwardWatchExportFailed'));
  } finally {
    btn.disabled = false;
  }
});

$('#forward-watch-import-input')?.addEventListener('change', async function() {
  const file = this.files && this.files[0];
  this.value = '';
  if (!file) return;
  const notice = $('#forward-watch-import-notice');
  try {
    const result = await importForwardWatchBackupFile(file);
    if (notice) {
      notice.className = 'text-xs text-success mt-2';
      notice.textContent = formatForwardWatchImportResult(result);
      notice.style.display = '';
    }
    if (typeof loadWatches === 'function') loadWatches();
  } catch (e) {
    if (e && e.error_code === 'auth_required') {
      redirectToLoginPage();
      return;
    }
    if (notice) {
      notice.className = 'text-xs text-danger mt-2';
      notice.textContent = translateApiError(e, 'settings.forwardWatchImportFailed');
      notice.style.display = '';
    }
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

  /* unified media type allowlist — dual-write forward_type + user.download_type */
  const mediaTypeOptions = normalizeOptionList((state.settingsModel.options || {}).message_filter_media_types || (state.settingsSchema.message_filter || {}).media_types || MEDIA_TYPE_KEYS);
  const allMediaTypes = mediaTypeOptions.length ? mediaTypeOptions.map(function(option) { return option.value; }) : MEDIA_TYPE_KEYS.slice();
  const checkedMedia = Array.from($$('input[name="global.message_filter.media_types"]:checked')).map(function(cb) { return cb.value; });
  const mediaTypesDict = {};
  allMediaTypes.forEach(function(t) { mediaTypesDict[t] = checkedMedia.indexOf(t) >= 0; });
  MEDIA_TYPE_KEYS.forEach(function(t) {
    if (mediaTypesDict[t] === undefined) mediaTypesDict[t] = false;
  });
  setNested(payload, ['global', 'message_filter', 'media_types'], mediaTypesDict);
  setNested(payload, ['global', 'forward_type'], completeMediaTypesDict(mediaTypesDict));
  setNested(payload, ['user', 'download_type'], mediaTypesToDownloadTypeList(mediaTypesDict));

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
        '<td class="max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc((item.paths || []).join('\\n') || item.local_path || '') + '">' + esc(item.file_name || item.local_path || '-') + '</td>' +
        '<td class="text-right">' + fmtSize(item.file_size) + '</td>' +
        '<td class="text-center">' + statusBadge(item.status || '') + '</td>' +
        '<td class="max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(item.source_link || '-') + '">' + esc(item.source_link || '-') + '</td>' +
        '</tr>').join('');
    } else {
      $('#media-items-tbody').innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">暂无数据</td></tr>';
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
        '<td class="max-w-[240px] overflow-hidden text-ellipsis whitespace-nowrap" title="' + esc(f.path) + '">' + esc(f.path) + '</td>' +
        '<td class="text-right">' + fmtSize(f.size) + '</td>' +
        '<td class="text-muted">' + fmtTimestamp(f.mtime) + '</td>' +
        '</tr>').join('');
    } else {
      $('#media-orphans-tbody').innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">暂无数据</td></tr>';
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

/* ====== Archive Organize (by Post Author) ====== */
var archiveOrganizePlan = null;
var archiveOrganizePollTimer = null;
var ARCHIVE_AUTHOR_JOB_KEY = 'trmd-archive-author-job';

function saveArchiveOrganizeJob(job) {
  try {
    if (!job || !job.id) {
      localStorage.removeItem(ARCHIVE_AUTHOR_JOB_KEY);
      return;
    }
    localStorage.setItem(ARCHIVE_AUTHOR_JOB_KEY, JSON.stringify({
      id: job.id,
      channel_folder: job.channel_folder || '',
      kind: job.kind || ''
    }));
  } catch (e) {}
}

function loadSavedArchiveOrganizeJob() {
  try {
    var raw = localStorage.getItem(ARCHIVE_AUTHOR_JOB_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

function clearSavedArchiveOrganizeJob() {
  try { localStorage.removeItem(ARCHIVE_AUTHOR_JOB_KEY); } catch (e) {}
}

function setArchiveOrganizeBusy(busy, labelKey) {
  const scanBtn = $('#archive-organize-scan-btn');
  const runBtn = $('#archive-organize-run-btn');
  if (scanBtn) {
    scanBtn.disabled = !!busy;
    scanBtn.textContent = busy && labelKey === 'scan'
      ? t('archiveOrganize.scanning')
      : t('archiveOrganize.scan');
  }
  if (runBtn) {
    if (busy && labelKey === 'run') {
      runBtn.disabled = true;
      runBtn.textContent = t('archiveOrganize.running');
    } else if (!busy) {
      runBtn.textContent = t('archiveOrganize.run');
      runBtn.disabled = !(archiveOrganizePlan && archiveOrganizePlan.move_count > 0);
    } else {
      runBtn.disabled = true;
    }
  }
}

function showArchiveOrganizeProgress(job) {
  const box = $('#archive-organize-progress');
  const message = $('#archive-organize-progress-message');
  const pctEl = $('#archive-organize-progress-pct');
  const fill = $('#archive-organize-progress-fill');
  const count = $('#archive-organize-progress-count');
  if (!box) return;
  box.classList.remove('hidden');
  const percent = Math.max(0, Math.min(100, Number(job && job.percent || 0)));
  const current = Number(job && job.current || 0);
  const total = Number(job && job.total || 0);
  if (message) message.textContent = (job && job.message) || t('archiveOrganize.progress');
  if (pctEl) pctEl.textContent = percent + '%';
  if (fill) fill.style.width = percent + '%';
  if (count) {
    count.textContent = total > 0
      ? (current + ' / ' + total)
      : (job && job.phase === 'listing' ? t('archiveOrganize.scanning') : '-');
  }
}

function hideArchiveOrganizeProgress() {
  const box = $('#archive-organize-progress');
  if (box) box.classList.add('hidden');
}

function stopArchiveOrganizePoll() {
  if (archiveOrganizePollTimer) {
    clearTimeout(archiveOrganizePollTimer);
    archiveOrganizePollTimer = null;
  }
}

function sleepMs(ms) {
  return new Promise(function(resolve) { setTimeout(resolve, ms); });
}

async function pollArchiveOrganizeJob(jobId) {
  while (true) {
    const job = await fetchJson('/api/archive/author-job?id=' + encodeURIComponent(jobId));
    showArchiveOrganizeProgress(job);
    saveArchiveOrganizeJob(job);
    if (job.status === 'success' || job.status === 'failure') {
      return job;
    }
    // Slow poll — long-running jobs; avoid hammering the API.
    await sleepMs(2000);
  }
}

async function resumeArchiveOrganizeJobIfAny() {
  const select = $('#archive-organize-channel');
  const saved = loadSavedArchiveOrganizeJob();
  let job = null;
  try {
    if (saved && saved.id) {
      job = await fetchJson('/api/archive/author-job?id=' + encodeURIComponent(saved.id));
    }
  } catch (e) {
    job = null;
  }
  if (!job || !job.id) {
    const channel = (select && select.value) || (saved && saved.channel_folder) || '';
    const url = '/api/archive/author-job?active=1' +
      (channel ? ('&channel_folder=' + encodeURIComponent(channel)) : '');
    try {
      job = await fetchJson(url);
    } catch (e) {
      job = null;
    }
  }
  if (!job || !job.id) return;
  if (select && job.channel_folder) {
    select.value = job.channel_folder;
  }
  if (job.status === 'running') {
    const busyKey = job.kind === 'reorganize' ? 'run' : 'scan';
    setArchiveOrganizeBusy(true, busyKey);
    showArchiveOrganizeProgress(job);
    try {
      const finished = await pollArchiveOrganizeJob(job.id);
      if (finished.status === 'failure') {
        throw new Error(finished.error || finished.message || 'job failed');
      }
      if (finished.result) {
        renderArchiveOrganizePlan(finished.result);
      }
    } catch (e) {
      const msg = translateApiError(e, 'form.requestFailed');
      showArchiveOrganizeProgress({ percent: 0, current: 0, total: 0, phase: 'error', message: msg });
    } finally {
      setArchiveOrganizeBusy(false);
      clearSavedArchiveOrganizeJob();
    }
    return;
  }
  if (job.status === 'success' && job.result) {
    showArchiveOrganizeProgress(job);
    renderArchiveOrganizePlan(job.result);
    clearSavedArchiveOrganizeJob();
  } else if (job.status === 'failure') {
    showArchiveOrganizeProgress(job);
    clearSavedArchiveOrganizeJob();
  }
}

async function loadArchiveOrganizeChannels() {
  const select = $('#archive-organize-channel');
  if (!select) return;
  const previous = select.value;
  try {
    const data = await fetchJson('/api/archive/author-channels');
    const channels = (data && data.channels) || [];
    if (!channels.length) {
      select.innerHTML = '<option value="">' + esc(t('archiveOrganize.emptyChannels')) + '</option>';
      return;
    }
    select.innerHTML = channels.map(function(name) {
      return '<option value="' + esc(name) + '">' + esc(name) + '</option>';
    }).join('');
    if (previous && channels.indexOf(previous) >= 0) {
      select.value = previous;
    }
  } catch (e) {
    select.innerHTML = '<option value="">' + esc(translateApiError(e, 'form.requestFailed')) + '</option>';
  }
}

async function loadArchiveOrganize() {
  await loadArchiveOrganizeChannels();
  await resumeArchiveOrganizeJobIfAny();
}

function renderArchiveOrganizePlan(data) {
  archiveOrganizePlan = data;
  const result = $('#archive-organize-result');
  const summary = $('#archive-organize-summary');
  const tbody = $('#archive-organize-tbody');
  const runBtn = $('#archive-organize-run-btn');
  if (!result || !summary || !tbody) return;
  result.classList.remove('hidden');
  const moves = data.moves || [];
  const movesTotal = data.moves_total || moves.length;
  summary.innerHTML = [
    '<div><div class="text-xs text-muted">' + t('archiveOrganize.authors') + '</div><div class="text-lg font-semibold">' + (data.author_count || 0) + '</div></div>',
    '<div><div class="text-xs text-muted">' + t('archiveOrganize.moves') + '</div><div class="text-lg font-semibold">' + (data.move_count || 0) + '</div></div>',
    '<div><div class="text-xs text-muted">' + t('archiveOrganize.skips') + '</div><div class="text-lg font-semibold">' + (data.skip_count || 0) + '</div></div>',
    '<div><div class="text-xs text-muted">' + t('archiveOrganize.author') + '</div><div class="text-sm">' + esc(((data.authors || []).slice(0, 8).join('、')) || '-') + '</div></div>'
  ].join('');
  if (data.moves_truncated) {
    summary.innerHTML += '<div class="w-full text-xs text-muted mt-1">' +
      t('archiveOrganize.truncatedMoves')
        .replace('{total}', String(movesTotal))
        .replace('{shown}', String(moves.length)) +
      '</div>';
  }
  tbody.innerHTML = moves.map(function(item) {
    return '<tr>' +
      '<td>' + esc(item.message_id == null ? '-' : String(item.message_id)) + '</td>' +
      '<td>' + esc(item.author || '-') + '</td>' +
      '<td class="text-xs">' + esc(item.from_relative || '') + '</td>' +
      '<td class="text-xs">' + esc(item.to_relative || '') + '</td>' +
      '<td>' + esc(item.action || '') + '</td>' +
      '</tr>';
  }).join('') || '<tr><td colspan="5" class="text-center text-muted">-</td></tr>';
  if (runBtn) runBtn.disabled = !(data.move_count > 0);
}

async function scanArchiveOrganize() {
  const channel = ($('#archive-organize-channel') || {}).value || '';
  if (!channel) {
    alert(t('archiveOrganize.pickChannel'));
    return;
  }
  stopArchiveOrganizePoll();
  setArchiveOrganizeBusy(true, 'scan');
  showArchiveOrganizeProgress({
    percent: 0,
    current: 0,
    total: 0,
    phase: 'listing',
    message: t('archiveOrganize.scanning')
  });
  try {
    const started = await postJson('/api/archive/author-scan', { channel_folder: channel });
    saveArchiveOrganizeJob(started);
    const job = await pollArchiveOrganizeJob(started.id);
    if (job.status === 'failure') {
      throw new Error(job.error || job.message || 'scan failed');
    }
    renderArchiveOrganizePlan(job.result || {});
    clearSavedArchiveOrganizeJob();
  } catch (e) {
    const msg = translateApiError(e, 'form.requestFailed');
    showArchiveOrganizeProgress({
      percent: 0,
      current: 0,
      total: 0,
      phase: 'error',
      message: msg
    });
  } finally {
    setArchiveOrganizeBusy(false);
  }
}

async function runArchiveOrganize() {
  const channel = ($('#archive-organize-channel') || {}).value || '';
  if (!channel) {
    alert(t('archiveOrganize.pickChannel'));
    return;
  }
  if (!archiveOrganizePlan || !(archiveOrganizePlan.move_count > 0)) {
    showArchiveOrganizeProgress({
      percent: 0,
      current: 0,
      total: 0,
      phase: 'error',
      message: t('archiveOrganize.needScan')
    });
    return;
  }
  if (!confirm(t('archiveOrganize.run') + ' — ' + channel + ' (' + archiveOrganizePlan.move_count + ')')) {
    return;
  }
  stopArchiveOrganizePoll();
  setArchiveOrganizeBusy(true, 'run');
  showArchiveOrganizeProgress({
    percent: 0,
    current: 0,
    total: archiveOrganizePlan.move_count || 0,
    phase: 'moving',
    message: t('archiveOrganize.running')
  });
  try {
    const started = await postJson('/api/archive/author-reorganize', { channel_folder: channel });
    saveArchiveOrganizeJob(started);
    const job = await pollArchiveOrganizeJob(started.id);
    if (job.status === 'failure') {
      throw new Error(job.error || job.message || 'reorganize failed');
    }
    const data = job.result || {};
    showArchiveOrganizeProgress({
      percent: 100,
      current: data.moved_count || 0,
      total: data.planned_moves || archiveOrganizePlan.move_count || 0,
      phase: 'done',
      message: (job.message || '') +
        ' · ' + t('archiveOrganize.moved') + ': ' + (data.moved_count || 0) +
        ' / ' + t('archiveOrganize.errors') + ': ' + (data.error_count || 0)
    });
    // Do not auto-rescan after reorganize (rate-limit safe). Clear plan until next scan.
    archiveOrganizePlan = null;
    const runBtn = $('#archive-organize-run-btn');
    if (runBtn) runBtn.disabled = true;
    clearSavedArchiveOrganizeJob();
  } catch (e) {
    const msg = translateApiError(e, 'form.requestFailed');
    showArchiveOrganizeProgress({
      percent: 0,
      current: 0,
      total: 0,
      phase: 'error',
      message: msg
    });
  } finally {
    setArchiveOrganizeBusy(false);
  }
}

$('#archive-organize-scan-btn')?.addEventListener('click', scanArchiveOrganize);
$('#archive-organize-run-btn')?.addEventListener('click', runArchiveOrganize);

/* ====== Init ====== */
(function init() {
  applyLanguage();
  ensureOverrideMediaTypeGrids();
  bindAllMediaTypesPickers(document);
  applyDesktopRouteFromLocation();
  if (typeof startSetupPolling === 'function') startSetupPolling();
  checkAuthStatus();
  authPollTimer = setInterval(() => {
    if (typeof checkSetupStatus === 'function') checkSetupStatus();
    if (authStep === 'done' || authStep === 'none') {
      clearInterval(authPollTimer);
      authPollTimer = null;
      return;
    }
    checkAuthStatus();
  }, 2000);
})();
