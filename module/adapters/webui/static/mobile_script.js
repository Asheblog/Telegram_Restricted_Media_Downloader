// ================================================================
// mobile_script.js v2 — 4-tab clean navigation, no FAB/Drawer
// ($ already defined in shared.js)
// ================================================================

// ---------------------------------------------------------------------------
// Login helpers (delegates to shared.js utilities)
// ---------------------------------------------------------------------------
function showLoginStep(step) {
  var steps = ['phone', 'code', 'password', 'recovery', 'signup', 'done'];
  steps.forEach(function(id) { var el = document.getElementById('login-form-' + id); if (el) el.style.display = 'none'; });
  var el = document.getElementById('login-form-' + step);
  if (el) el.style.display = '';
  var container = document.getElementById('login-container');
  if (container && !container.classList.contains('active')) container.classList.add('active');
  var loginError = document.getElementById('login-error');
  if (loginError) loginError.classList.remove('visible');
}

function hideLogin() {
  var container = document.getElementById('login-container');
  if (container) container.classList.remove('active');
}

function showLoginError(msg) {
  var el = document.getElementById('login-error');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
}

async function checkAuthStatus() {
  try {
    var resp = await fetch('/api/auth/status');
    if (resp.status === 401) { redirectToLoginPage(); return; }
    var state = await resp.json();
    if (!state || !state.step) return;
    switch (state.step) {
      case 'pending':
        var container = document.getElementById('login-container');
        if (container) container.classList.remove('active');
        return;
      case 'done': case 'none':
        hideLogin();
        startPolling();
        return;
      case 'phone':
        showLoginStep('phone');
        if (state.error) showLoginError(state.error);
        break;
      case 'code':
        showLoginStep('code');
        if (state.code_type) {
          var desc = document.getElementById('login-code-desc');
          if (desc) desc.textContent = '验证码已通过「' + state.code_type + '」发送';
        }
        if (state.error) showLoginError(state.error);
        break;
      case 'password':
        showLoginStep('password');
        var hintEl = document.getElementById('login-password-hint-text');
        if (hintEl && state.hint) hintEl.textContent = state.hint;
        if (state.error) showLoginError(state.error);
        break;
      case 'recovery_code':
        showLoginStep('recovery');
        var rDesc = document.getElementById('login-recovery-desc');
        if (rDesc && state.message) rDesc.textContent = state.message;
        if (state.error) showLoginError(state.error);
        break;
      case 'signup':
        showLoginStep('signup');
        if (state.error) showLoginError(state.error);
        break;
      case 'error':
        if (state.error) showLoginError(state.error);
        break;
      default:
        break;
    }
  } catch (e) { /* ignore */ }
}

async function submitAuth(payload) {
  var btns = document.querySelectorAll('.mob-login-submit');
  btns.forEach(function(b) { b.disabled = true; });
  showLoginError('');
  try {
    await fetch('/api/auth/submit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    await new Promise(function(r) { setTimeout(r, 500); });
    await checkAuthStatus();
  } catch (e) {
    showLoginError('提交失败，请重试');
  } finally {
    btns.forEach(function(b) { b.disabled = false; });
  }
}

// ---------------------------------------------------------------------------
// Login button bindings
// ---------------------------------------------------------------------------
(function() {
  var phoneBtn = document.getElementById('login-btn-phone');
  if (phoneBtn) phoneBtn.addEventListener('click', function() {
    var phone = document.getElementById('login-phone').value.trim();
    if (!phone) { showLoginError('请输入电话号码'); return; }
    submitAuth({ phone: phone });
  });

  var codeBtn = document.getElementById('login-btn-code');
  if (codeBtn) codeBtn.addEventListener('click', function() {
    var code = document.getElementById('login-code').value.trim();
    if (!code) { showLoginError('请输入验证码'); return; }
    submitAuth({ code: code });
  });

  var backBtn = document.getElementById('login-btn-back');
  if (backBtn) backBtn.addEventListener('click', function() {
    document.getElementById('login-code').value = '';
    showLoginStep('phone');
  });

  var pwdBtn = document.getElementById('login-btn-password');
  if (pwdBtn) pwdBtn.addEventListener('click', function() {
    var pwd = document.getElementById('login-password').value;
    if (!pwd) { showLoginError('请输入两步验证密码'); return; }
    submitAuth({ password: pwd });
  });

  var pwdBackBtn = document.getElementById('login-btn-back-pwd');
  if (pwdBackBtn) pwdBackBtn.addEventListener('click', function() {
    document.getElementById('login-password').value = '';
    showLoginStep('phone');
  });

  var recBtn = document.getElementById('login-btn-recovery');
  if (recBtn) recBtn.addEventListener('click', function() {
    var code = document.getElementById('login-recovery').value.trim();
    if (!code) { showLoginError('请输入恢复代码'); return; }
    submitAuth({ recovery_code: code });
  });

  var recBackBtn = document.getElementById('login-btn-back-recovery');
  if (recBackBtn) recBackBtn.addEventListener('click', function() {
    document.getElementById('login-recovery').value = '';
    showLoginStep('phone');
  });

  var signupBtn = document.getElementById('login-btn-signup');
  if (signupBtn) signupBtn.addEventListener('click', function() {
    var first = document.getElementById('login-first-name').value.trim();
    if (!first) { showLoginError('请输入名字'); return; }
    submitAuth({ first_name: first, last_name: document.getElementById('login-last-name').value.trim() });
  });
})();

// ---------------------------------------------------------------------------
// Polling
// ---------------------------------------------------------------------------
var pollTimer = null;
var initialLoadDone = false;
var mobileSettingsLoadPromise = null;

function hasActiveTasks() { return (window.state && Array.isArray(window.state.tasks) && window.state.tasks.some(function(t) { return t.status === 'running'; })); }

function startPolling() {
  stopPolling();
  initialLoadDone = true;

  async function poll() {
    await loadCurrentView();
    pollTimer = setTimeout(poll, hasActiveTasks() ? 3000 : 10000);
  }

  poll();
}

function stopPolling() {
  if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
}

async function loadCurrentView() {
  var active = document.querySelector('.mob-view.active');
  if (!active) return;
  var id = active.id;
  if (id === 'mob-view-transfers') {
    await loadMobileTasks();
    await refreshOpenTaskSheet();
  }
  else if (id === 'mob-view-watches') { await loadMobileWatches(); }
  else if (id === 'mob-view-downloads-uploads') { await loadMobileDownloadsUploads(); }
  // profile sub-pages load on demand
  var subActive = document.querySelector('.mob-subpage.active');
  if (subActive) {
    if (subActive.id === 'mob-subpage-statistics') { await loadMobileStatistics(); }
    else if (subActive.id === 'mob-subpage-records') { await loadMobileRecords(); }
  }
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
var currentMainTab = 'transfers';
var currentProfileSub = null;
var profileTitles = {
  statistics: '统计面板',
  records: '下载记录',
  media: '媒体管理',
  settings: '系统设置'
};

function mobSwitchView(view) {
  // Hide all main views
  var views = document.querySelectorAll('.mob-view');
  views.forEach(function(v) { v.classList.remove('active'); });

  // Show target view
  var target = document.getElementById('mob-view-' + view);
  if (target) target.classList.add('active');

  // Update tab bar
  var tabs = document.querySelectorAll('#mob-tabbar .mob-tab');
  tabs.forEach(function(t) { t.classList.remove('active'); });
  var tab = document.querySelector('#mob-tabbar [data-mob-tab="' + view + '"]');
  if (tab) tab.classList.add('active');

  // Reset top bar (exit sub-page mode)
  exitSubPage();

  currentMainTab = view;

  // Load content
  if (view === 'transfers') { loadMobileTasks(); }
  else if (view === 'watches') { loadMobileWatches(); }
  else if (view === 'downloads-uploads') { loadMobileDownloadsUploads(); }
  else if (view === 'profile') { /* menu is static, sub-pages load on demand */ }
}

function mobNavigateTo(subpage) {
  // Hide profile menu
  var menu = document.getElementById('mob-profile-menu');
  if (menu) menu.style.display = 'none';

  // Hide all subpages
  var subs = document.querySelectorAll('.mob-subpage');
  subs.forEach(function(s) { s.classList.remove('active'); });

  // Show target subpage
  var target = document.getElementById('mob-subpage-' + subpage);
  if (target) target.classList.add('active');

  // Update top bar
  enterSubPage(profileTitles[subpage] || subpage);

  currentProfileSub = subpage;

  // Load content
  if (subpage === 'statistics') { loadMobileStatistics(); }
  else if (subpage === 'records') { loadMobileRecords(); }
  else if (subpage === 'media') { loadMediaMobile(); }
  else if (subpage === 'settings') { loadMobileSettings(); }
}

function mobNavigateBack() {
  exitSubPage();

  // Hide all subpages
  var subs = document.querySelectorAll('.mob-subpage');
  subs.forEach(function(s) { s.classList.remove('active'); });

  // Show profile menu
  var menu = document.getElementById('mob-profile-menu');
  if (menu) menu.style.display = '';

  currentProfileSub = null;
}

function enterSubPage(title) {
  var topbar = document.getElementById('mob-topbar');
  var titleEl = document.getElementById('mob-topbar-title');
  if (topbar) topbar.classList.add('sub');
  if (titleEl) titleEl.textContent = title;
}

function exitSubPage() {
  var topbar = document.getElementById('mob-topbar');
  var titleEl = document.getElementById('mob-topbar-title');
  if (topbar) topbar.classList.remove('sub');
  if (titleEl) titleEl.textContent = 'TRMD';
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function showToast(message, duration) {
  var el = document.getElementById('mob-toast');
  if (!el) return;
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(el._timeout);
  el._timeout = setTimeout(function() { el.classList.remove('show'); }, duration || 2000);
}

// ---------------------------------------------------------------------------
// Badge helper
// ---------------------------------------------------------------------------
function mobBadge(status) {
  var map = {
    pending: '<span class="mob-card__badge pending">等待中</span>',
    running: '<span class="mob-card__badge running">运行中</span>',
    paused: '<span class="mob-card__badge paused">已暂停</span>',
    completed: '<span class="mob-card__badge completed">已完成</span>',
    success: '<span class="mob-card__badge completed">已完成</span>',
    failure: '<span class="mob-card__badge failure">失败</span>',
    cancelled: '<span class="mob-card__badge cancelled">已取消</span>',
    skipped: '<span class="mob-card__badge cancelled">已跳过</span>'
  };
  return map[status] || '<span class="mob-card__badge pending">' + esc(status) + '</span>';
}

// ---------------------------------------------------------------------------
// Collapse toggle
// ---------------------------------------------------------------------------
function toggleCollapse(head) {
  var parent = head.closest('.mob-collapse');
  if (!parent) return;
  parent.classList.toggle('open');
}

function mobEmptyHtml(message, i18nKey) {
  var attr = i18nKey ? ' data-i18n="' + escAttr(i18nKey) + '"' : '';
  return '<div class="mob-empty"' + attr + '>' + esc(message) + '</div>';
}

async function loadMobileTasks() {
  var container = document.getElementById('mob-tasks-list');
  if (!container) return;
  if (!window.state) window.state = {};
  if (!Array.isArray(window.state.tasks)) {
    container.innerHTML = mobEmptyHtml('加载中...');
  }
  try {
    var data = await fetchJson('/api/tasks');
    window.state.tasks = Array.isArray(data.tasks) ? data.tasks : [];
    window.state.lastSync = new Date().toLocaleTimeString();
    renderMobTasks();
  } catch (e) {
    window.state.tasks = [];
    container.innerHTML = mobEmptyHtml('加载失败');
  }
}

async function loadMobileWatches() {
  var container = document.getElementById('mob-watches-list');
  if (!container) return;
  if (!window.state) window.state = {};
  if (!Array.isArray(window.state.watches)) {
    container.innerHTML = mobEmptyHtml('加载中...');
  }
  try {
    var data = await fetchJson('/api/watches');
    window.state.watches = Array.isArray(data.watches) ? data.watches : [];
    renderMobWatches();
  } catch (e) {
    window.state.watches = [];
    container.innerHTML = mobEmptyHtml('加载失败');
  }
}

async function ensureMobileSettingsData() {
  if (!window.state) window.state = {};
  if (window.state.settings) return true;
  if (!mobileSettingsLoadPromise) {
    mobileSettingsLoadPromise = fetchJson('/api/settings').then(function(data) {
      window.state.settings = data.settings || {};
      window.state.schema = data.schema || {};
      window.state.settingsSchema = data.schema || {};
      window.state.settingsModel = data.settings_model || {};
      return true;
    }).catch(function(e) {
      mobileSettingsLoadPromise = null;
      throw e;
    });
  }
  return mobileSettingsLoadPromise;
}

async function loadMobileSettings() {
  try {
    await ensureMobileSettingsData();
    settingsRendered = false;
    ensureSettingsForm();
  } catch (e) {
    var notice = document.getElementById('mob-settings-notice');
    if (notice) {
      notice.classList.remove('hidden');
      notice.textContent = '加载失败';
      notice.style.color = 'var(--color-danger)';
    }
  }
}

async function loadMobileDownloadsUploads() {
  try {
    await ensureMobileSettingsData();
  } catch (e) {
    // Keep operations history usable even when settings cannot be loaded.
  }
  mobInitDownloadTypes();
  loadMobileOperations();
}

// ---------------------------------------------------------------------------
// Task rendering
// ---------------------------------------------------------------------------
function renderMobTasks() {
  var container = document.getElementById('mob-tasks-list');
  if (!container) return;
  if (!window.state || !Array.isArray(window.state.tasks)) {
    container.innerHTML = mobEmptyHtml('还没有转存任务。', 'tasks.empty');
    return;
  }
  if (window.state.tasks.length === 0) {
    container.innerHTML = mobEmptyHtml('还没有转存任务。', 'tasks.empty');
    return;
  }

  var html = '';
  window.state.tasks.forEach(function(t) {
    var progressPct = taskProgressPercent(t);
    var activeSummary = activeTransferSummary(t);
    html += '<div class="mob-card status-' + esc(t.status) + '" data-task-id="' + t.id + '">' +
      '<div class="mob-card__head">' +
        '<span class="mob-card__title">' + esc(t.title || t.source_link || '#' + t.id) + '</span>' +
        mobBadge(t.status) +
      '</div>' +
      '<div class="mob-card__row"><span class="label">来源</span><span>' + esc(t.source_link || '-') + '</span></div>' +
      '<div class="mob-card__row"><span class="label">进度</span><span>' + taskCompletedLabel(t) + (taskFailedCount(t) ? ' · 失败 ' + taskFailedCount(t) : '') + '</span></div>' +
      (activeSummary ? '<div class="mob-card__row"><span class="label">当前</span><span>' + esc(activeSummary) + '</span></div>' : '') +
      '<div class="mob-card__progress"><div class="mob-card__progress-fill" style="width:' + progressPct + '%"></div></div>' +
      '<div class="mob-card__actions">' +
        (t.can_pause ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-pause="' + t.id + '">暂停</button>' : '') +
        (t.can_resume ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-resume="' + t.id + '">继续</button>' : '') +
        (t.can_retry ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-retry="' + t.id + '">重试</button>' : '') +
        (t.can_delete ? '<button class="mob-btn mob-btn-sm mob-btn-danger" data-delete="' + t.id + '">删除</button>' : '') +
      '</div>' +
    '</div>';
  });
  container.innerHTML = html || mobEmptyHtml('还没有转存任务。', 'tasks.empty');
  bindTaskCardEvents(container);
}

function bindTaskCardEvents(container) {
  container.querySelectorAll('[data-pause]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); runTaskAction(e, Number(btn.dataset.pause), 'pause'); });
  });
  container.querySelectorAll('[data-resume]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); runTaskAction(e, Number(btn.dataset.resume), 'resume'); });
  });
  container.querySelectorAll('[data-retry]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); runTaskAction(e, Number(btn.dataset.retry), 'retry-failed'); });
  });
  container.querySelectorAll('[data-delete]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); deleteTask(e, Number(btn.dataset.delete)); });
  });
  container.querySelectorAll('.mob-card').forEach(function(card) {
    card.addEventListener('click', function(e) {
      if (e.target.closest('button')) return;
      openTaskDetail(Number(card.dataset.taskId));
    });
  });
}

// ---------------------------------------------------------------------------
// Watch rendering
// ---------------------------------------------------------------------------
function renderMobWatches() {
  var container = document.getElementById('mob-watches-list');
  if (!container) return;
  if (!window.state || !Array.isArray(window.state.watches)) {
    container.innerHTML = mobEmptyHtml('还没有实时监听。', 'watches.empty');
    return;
  }
  if (window.state.watches.length === 0) {
    container.innerHTML = mobEmptyHtml('还没有实时监听。', 'watches.empty');
    return;
  }

  var typeLabels = { download: '下载监听', forward: '转发监听' };
  var html = '';
  window.state.watches.forEach(function(w) {
    var statusClass = w.status === 'paused' ? 'paused' : 'running';
    var statusLabel = w.status === 'paused' ? '已暂停' : '运行中';
    var sanitized = esc(w.id).replace(/[^a-zA-Z0-9_-]/g, '_');
    var eventCount = Number(w.event_count || 0);
    html += '<div class="mob-card status-' + statusClass + '">' +
      '<div class="mob-card__head">' +
        '<span class="mob-card__title">' + esc(typeLabels[w.type] || w.type || '监听') + '</span>' +
        '<span class="mob-card__badge ' + statusClass + '">' + statusLabel + '</span>' +
      '</div>' +
      '<div class="mob-card__row"><span class="label">来源</span><span>' + esc(Array.isArray(w.source_links) ? w.source_links.join(', ') : (w.source_link || '-')) + '</span></div>' +
      (w.target_link ? '<div class="mob-card__row"><span class="label">目标</span><span>' + esc(w.target_link) + '</span></div>' : '') +
      '<div class="mob-card__row"><span class="label">今日</span><span>' + (w.today_count || 0) + '</span></div>' +
      '<div class="mob-card__actions">' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" data-delete-watch="' + esc(w.id) + '">删除</button>' +
        (w.type === 'forward' ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-events-watch="' + esc(w.id) + '" data-sanitized="' + sanitized + '">今日</button>' : '') +
        (w.type === 'forward' ? '<button class="mob-btn mob-btn-sm mob-btn-muted" data-watch-history="' + esc(w.id) + '">记录' + (eventCount ? ' ' + eventCount : '') + '</button>' : '') +
      '</div>' +
      '<div class="mob-watch-events hidden" id="mob-watch-events-' + sanitized + '"></div>' +
    '</div>';
  });
  container.innerHTML = html || mobEmptyHtml('还没有实时监听。', 'watches.empty');

  container.querySelectorAll('[data-delete-watch]').forEach(function(btn) {
    btn.addEventListener('click', function() { deleteWatch(btn.dataset.deleteWatch); });
  });
  container.querySelectorAll('[data-events-watch]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var panel = document.getElementById('mob-watch-events-' + btn.dataset.sanitized);
      if (!panel) return;
      var isHidden = panel.classList.contains('hidden');
      panel.classList.toggle('hidden');
      if (isHidden) loadMobileWatchEvents(btn.dataset.eventsWatch, btn.dataset.sanitized);
    });
  });
  container.querySelectorAll('[data-watch-history]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      openMobileWatchHistory(btn.dataset.watchHistory, 1);
    });
  });
}

async function loadMobileWatchEvents(watchId, sanitized) {
  var panel = document.getElementById('mob-watch-events-' + sanitized);
  if (!panel) return;
  panel.innerHTML = '<div style="padding:8px;color:var(--color-muted);">加载中...</div>';
  try {
    var data = await fetchJson('/api/watches/' + encodeURIComponent(watchId) + '/events?limit=20&today=1');
    if (!data || !data.events || data.events.length === 0) {
      panel.innerHTML = '<div style="padding:8px;color:var(--color-muted);">暂无事件</div>';
      return;
    }
    var html = '';
    data.events.forEach(function(ev) {
      var statusLabel = ev.status === 'success' ? '转发成功' : '已过滤';
      html += '<div class="watch-event-item">' +
        '<span class="watch-event-time">' + esc(fmtTime(ev.created_at)) + '</span>' +
        '<span class="watch-event-badge badge ' + (ev.status === 'success' ? 'badge-success' : 'badge-warning') + '">' + esc(statusLabel) + '</span>' +
        '<span class="watch-event-info">' + esc(ev.message || '') + '</span>' +
      '</div>';
    });
    panel.innerHTML = html;
  } catch (e) {
    panel.innerHTML = '<div style="padding:8px;color:var(--color-danger);">加载失败</div>';
  }
}

async function openMobileWatchHistory(watchId, page) {
  sheetState.sheetType = 'watch-history';
  state.watchHistory = { watchId: watchId, page: page || 1, pageSize: 20, total: 0 };
  var overlay = document.getElementById('mob-sheet-overlay');
  var sheet = document.getElementById('mob-sheet');
  if (!overlay || !sheet) return;
  sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-muted);">加载中...</div>';
  overlay.classList.add('open');
  await loadMobileWatchHistoryPage();
}

async function loadMobileWatchHistoryPage() {
  var sheet = document.getElementById('mob-sheet');
  if (!sheet || !state.watchHistory.watchId) return;
  var page = state.watchHistory.page || 1;
  var pageSize = state.watchHistory.pageSize || 20;
  var offset = (page - 1) * pageSize;
  try {
    var data = await fetchJson('/api/watches/' + encodeURIComponent(state.watchHistory.watchId) + '/events?limit=' + pageSize + '&offset=' + offset);
    var items = data.events || [];
    var total = Number(data.total || 0);
    var totalPages = Math.max(1, Math.ceil(total / pageSize));
    var html = '<div class="mob-sheet__title">' + esc(t('watches.historyTitle')) + '</div>';
    if (!items.length) {
      html += '<div class="mob-empty">' + esc(t('watches.noEvents')) + '</div>';
    } else {
      items.forEach(function(ev) {
        var statusLabel = ev.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
        html += '<div class="mob-event-row">' +
          '<time>' + esc(fmtTime(ev.created_at)) + '</time>' +
          '<span class="mob-card__badge ' + (ev.status === 'success' ? 'completed' : 'pending') + '">' + esc(statusLabel) + '</span>' +
          '<div style="margin-top:4px;word-break:break-all;">' + esc(ev.message || '-') + '</div>' +
        '</div>';
      });
    }
    html += '<div class="mob-sheet-pagination">' +
      '<span>' + esc(t('watches.pageInfo').replace('{page}', page).replace('{pages}', totalPages).replace('{total}', total)) + '</span>' +
      '<div style="display:flex;gap:8px;">' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="mob-watch-history-prev" ' + (page <= 1 ? 'disabled' : '') + '>' + esc(t('items.page.previous')) + '</button>' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="mob-watch-history-next" ' + (page >= totalPages ? 'disabled' : '') + '>' + esc(t('items.page.next')) + '</button>' +
      '</div>' +
    '</div>' +
    '<button class="mob-btn mob-btn-muted mob-btn-sm" style="align-self:flex-end;margin-top:4px;" id="mob-watch-history-close">关闭</button>';
    sheet.innerHTML = html;
    document.getElementById('mob-watch-history-close')?.addEventListener('click', closeSheet);
    document.getElementById('mob-watch-history-prev')?.addEventListener('click', function() {
      state.watchHistory.page = Math.max(1, page - 1);
      loadMobileWatchHistoryPage();
    });
    document.getElementById('mob-watch-history-next')?.addEventListener('click', function() {
      state.watchHistory.page = page + 1;
      loadMobileWatchHistoryPage();
    });
  } catch (e) {
    sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-danger);">加载失败</div>';
  }
}

// ---------------------------------------------------------------------------
// Task detail sheet
// ---------------------------------------------------------------------------
var sheetState = { sheetType: '', taskId: null, items: [], events: [], currentTab: 'all', currentPage: 0, pageSize: 30, loading: false, hasMore: false };

async function openTaskDetail(taskId) {
  sheetState = { sheetType: 'task-detail', taskId: taskId, items: [], events: [], currentTab: 'all', currentPage: 0, pageSize: 30, loading: false, hasMore: false };
  var overlay = document.getElementById('mob-sheet-overlay');
  var sheet = document.getElementById('mob-sheet');
  if (!overlay || !sheet) return;
  sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-muted);">加载中...</div>';
  overlay.classList.add('open');

  try {
    var data = await fetchJson('/api/tasks/' + taskId);
    sheetState.items = data.items || [];
    sheetState.events = data.events || [];
    renderSheetContent(data);
  } catch (e) {
    sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-danger);">加载失败</div>';
  }
}

async function refreshOpenTaskSheet() {
  var overlay = document.getElementById('mob-sheet-overlay');
  if (!overlay || !overlay.classList.contains('open') || sheetState.sheetType !== 'task-detail' || !sheetState.taskId) return;
  var sheet = document.getElementById('mob-sheet');
  if (!sheet) return;
  try {
    var data = await fetchJson('/api/tasks/' + sheetState.taskId);
    sheetState.items = data.items || [];
    sheetState.events = data.events || [];
    updateSheetContent(data);
  } catch (e) {}
}

function renderSheetContent(data) {
  var sheet = document.getElementById('mob-sheet');
  if (!sheet) return;

  var task = data.task || {};
  var summary = data.summary || {};
  var totalItems = summary.total || sheetState.items.length || 0;
  var successCount = summary.success || 0;
  var failedCount = summary.failed || 0;
  var skippedCount = summary.skipped || 0;

  var tabsHtml = '';
  var tabs = [
    { key: 'all', label: '全部', count: totalItems },
    { key: 'success', label: '成功', count: successCount },
    { key: 'failure', label: '失败', count: failedCount },
    { key: 'skipped', label: '跳过', count: skippedCount }
  ];
  tabs.forEach(function(tab) {
    tabsHtml += '<button class="mob-sheet-tab' + (sheetState.currentTab === tab.key ? ' active' : '') + '" data-sheet-tab="' + tab.key + '">' +
      tab.label + '<span class="count">' + tab.count + '</span></button>';
  });

  sheet.innerHTML =
    '<div class="mob-sheet__title">任务详情 #' + task.id + '</div>' +
    '<div class="mob-sheet__task-header" id="mob-sheet-task-header">' +
      '<div class="task-title">' + esc(task.title || task.source_link || '任务 #' + task.id) + '</div>' +
      '<div class="task-meta">状态: ' + esc(task.status || '-') + ' · 进度: ' + esc(taskCompletedLabel(task)) + '</div>' +
      (activeTransferSummary(task) ? '<div class="task-meta">' + esc(activeTransferSummary(task)) + '</div>' : '') +
    '</div>' +
    '<div class="mob-sheet-tabs" id="mob-sheet-item-tabs">' + tabsHtml + '</div>' +
    '<div id="mob-sheet-item-list"></div>' +
    '<button class="mob-btn mob-btn-muted mob-btn-sm" style="align-self:flex-end;margin-top:4px;" id="mob-sheet-close">关闭</button>';

  bindSheetTabClicks();
  renderSheetItemPage();
  document.getElementById('mob-sheet-close').addEventListener('click', closeSheet);
}

function updateSheetContent(data) {
  var task = data.task || {};
  var summary = data.summary || {};
  var header = document.getElementById('mob-sheet-task-header');
  if (header) {
    header.innerHTML =
      '<div class="task-title">' + esc(task.title || task.source_link || '任务 #' + task.id) + '</div>' +
      '<div class="task-meta">状态: ' + esc(task.status || '-') + ' · 进度: ' + esc(taskCompletedLabel(task)) + '</div>' +
      (activeTransferSummary(task) ? '<div class="task-meta">' + esc(activeTransferSummary(task)) + '</div>' : '');
  }
  var counts = {
    all: summary.total || sheetState.items.length || 0,
    success: summary.success || 0,
    failure: summary.failed || 0,
    skipped: summary.skipped || 0
  };
  document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab').forEach(function(tab) {
    var key = tab.dataset.sheetTab;
    var count = counts[key] || 0;
    var label = key === 'all' ? '全部' : key === 'success' ? '成功' : key === 'failure' ? '失败' : '跳过';
    tab.innerHTML = label + '<span class="count">' + count + '</span>';
  });
  renderSheetItemPage();
}

function closeSheet() {
  var overlay = document.getElementById('mob-sheet-overlay');
  if (overlay) overlay.classList.remove('open');
  sheetState.sheetType = '';
}

function bindSheetTabClicks() {
  var tabs = document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab');
  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      tabs.forEach(function(t) { t.classList.remove('active'); });
      tab.classList.add('active');
      sheetState.currentTab = tab.dataset.sheetTab;
      sheetState.currentPage = 0;
      renderSheetItemPage();
    });
  });
}

function renderSheetItemPage() {
  var container = document.getElementById('mob-sheet-item-list');
  if (!container) return;

  var filtered = sheetState.items;
  if (sheetState.currentTab !== 'all') {
    filtered = sheetState.items.filter(function(item) { return item.status === sheetState.currentTab; });
  }

  var start = sheetState.currentPage * sheetState.pageSize;
  var page = filtered.slice(start, start + sheetState.pageSize);
  sheetState.hasMore = start + sheetState.pageSize < filtered.length;

  if (page.length === 0) {
    container.innerHTML = '<div class="mob-empty">暂无数据</div>';
    return;
  }

  var html = '';
  page.forEach(function(item) {
    var summary = itemTransferSummary(item);
    html += '<div class="mob-item-row">' +
      '<span class="mob-item-row__name">' + esc(item.file_name || item.message_id || '#' + item.id) +
        '<small class="mob-item-row__progress">' + esc(summary) + '</small>' +
      '</span>' +
      '<span class="mob-card__badge ' + (item.status === 'success' ? 'completed' : item.status === 'failure' ? 'failure' : 'pending') + '">' + esc(item.status || '-') + '</span>' +
    '</div>';
  });

  if (sheetState.hasMore) {
    html += '<div style="text-align:center;padding:8px;">' +
      '<button class="mob-btn mob-btn-sm mob-btn-muted" id="mob-sheet-load-more">加载更多</button>' +
    '</div>';
  }

  container.innerHTML = html;

  var loadMoreBtn = document.getElementById('mob-sheet-load-more');
  if (loadMoreBtn) loadMoreBtn.addEventListener('click', function() {
    sheetState.currentPage++;
    renderSheetItemPage();
  });
}

// ---------------------------------------------------------------------------
// Task actions — defined in shared.js; this file only refreshes
// mobile-specific rendering (renderMobTasks/renderMobWatches/showToast)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------
var settingsRendered = false;
function ensureSettingsForm() {
  if (!settingsRendered) { renderMobSettingsForm(); settingsRendered = true; }
}

function renderMobSettingsForm() {
  if (!window.state || !window.state.settings) return;
  var settings = window.state.settings;
  var model = window.state.settingsModel || {options: {}, selections: {}};
  var glob = settings.global || {};
  var user = settings.user || {};

  // Paths
  var pathFields = document.getElementById('mob-settings-path-fields');
  if (pathFields) pathFields.innerHTML =
    '<label><span>保存目录</span><input name="user.save_directory" value="' + escAttr(user.save_directory || '') + '"></label>' +
    '<label><span>临时目录</span><input name="user.temp_directory" value="' + escAttr(user.temp_directory || '') + '"></label>' +
    '<label><span>会话目录</span><input name="user.session_directory" value="' + escAttr(user.session_directory || '') + '"></label>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>最大下载</span><input name="user.max_tasks.download" type="number" min="1" value="' + (getSettingLeafKey(user, 'max_tasks.download') || '') + '"></label>' +
      '<label><span>最大上传</span><input name="user.max_tasks.upload" type="number" min="1" value="' + (getSettingLeafKey(user, 'max_tasks.upload') || '') + '"></label>' +
    '</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>下载重试</span><input name="user.max_retries.download" type="number" min="0" value="' + (getSettingLeafKey(user, 'max_retries.download') || '') + '"></label>' +
      '<label><span>上传重试</span><input name="user.max_retries.upload" type="number" min="0" value="' + (getSettingLeafKey(user, 'max_retries.upload') || '') + '"></label>' +
    '</div>' +
    '<label><span>PikPak大小上限(字节)</span><input name="global.target_profiles.pikpak.max_file_size" type="number" min="1" value="' + (getSettingLeafKey(glob, 'target_profiles.pikpak.max_file_size') || '') + '"></label>';

  // Behavior
  var behFields = document.getElementById('mob-settings-behavior-fields');
  if (behFields) behFields.innerHTML =
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">' +
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.notice" ' + (glob.notice ? ' checked' : '') + '><span>机器人通知</span></label>' +
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="user.is_shutdown"' + (user.is_shutdown ? ' checked' : '') + '><span>退出后关机</span></label>' +
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.download_upload"' + (getSettingLeafKey(glob, 'upload.download_upload') ? ' checked' : '') + '><span>受限转发时下载后上传</span></label>' +
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.delete"' + (getSettingLeafKey(glob, 'upload.delete') ? ' checked' : '') + '><span>上传完成删除本地文件</span></label>' +
    '</div>' +
    '<label style="margin-top:10px;"><span>下载后上传队列</span><input name="global.upload.pending_limit" type="number" min="1" max="5" value="' + (getSettingLeafKey(glob, 'upload.pending_limit') || '') + '"></label>';

  // Archive
  var archiveFields = document.getElementById('mob-settings-archive-fields');
  if (archiveFields) {
    var arch = getSettingLeafKey(glob, 'target_profiles.pikpak.archive') || {};
    archiveFields.innerHTML =
      '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.target_profiles.pikpak.archive.enable"' + (arch.enable ? ' checked' : '') + '><span>PikPak按来源频道归档</span></label>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
        '<label><span>PikPak rclone remote</span><input name="global.target_profiles.pikpak.archive.remote" value="' + escAttr(arch.remote || '') + '"></label>' +
        '<label><span>入库目录</span><input name="global.target_profiles.pikpak.archive.source_directory" value="' + escAttr(arch.source_directory || '') + '"></label>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
        '<label><span>归档根目录</span><input name="global.target_profiles.pikpak.archive.root_directory" value="' + escAttr(arch.root_directory || '') + '"></label>' +
        '<label><span>入库轮询秒数</span><input name="global.target_profiles.pikpak.archive.poll_seconds" type="number" min="0" value="' + (arch.poll_seconds || '') + '"></label>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
        '<label><span>轮询间隔秒数</span><input name="global.target_profiles.pikpak.archive.poll_interval_seconds" type="number" min="0" value="' + (arch.poll_interval_seconds || '') + '"></label>' +
        '<label><span>匹配时间窗口秒数</span><input name="global.target_profiles.pikpak.archive.match_window_seconds" type="number" min="0" value="' + (arch.match_window_seconds || '') + '"></label>' +
      '</div>';
  }

  // Sensitive
  var sensFields = document.getElementById('mob-settings-sensitive-fields');
  if (sensFields) sensFields.innerHTML =
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>API ID</span><input name="user.api_id" value="' + escAttr(user.api_id || '') + '"></label>' +
      '<label><span>API Hash</span><input name="user.api_hash" type="password" placeholder="已配置"></label>' +
    '</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>Bot Token</span><input name="user.bot_token" type="password" placeholder="已配置"></label>' +
      '<label><span>代理密码</span><input name="user.proxy.password" type="password" placeholder="已配置"></label>' +
    '</div>';

  // Download types
  var dlFields = document.getElementById('mob-settings-download-types-fields');
  if (dlFields) dlFields.innerHTML = renderCheckCards('user.download_type', model.options.download_type || [], selectedDownloadTypes(user), true);

  // Forward types
  var fwFields = document.getElementById('mob-settings-forward-types-fields');
  if (fwFields) fwFields.innerHTML = renderCheckCards('global.forward_type', model.options.forward_type || [], selectedForward(glob), false);

  // Message filter
  var mf = glob.message_filter || {};
  var mfFields = document.getElementById('mob-settings-message-filter-fields');
  if (mfFields) mfFields.innerHTML =
    '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.enabled"' + (mf.enabled ? ' checked' : '') + '><span>启用消息过滤</span></label>' +
      '<div style="margin-top:10px;"><span style="font-size:13px;font-weight:500;color:var(--color-text-secondary);">媒体类型</span><span style="font-size:11px;color:var(--color-muted);margin-left:4px;">（勾选 = 允许处理，未勾选的类型将被过滤）</span>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;margin-top:4px;">' + renderCheckCards('global.message_filter.media_types', model.options.message_filter_media_types || [], selectedMediaTypes(glob), false) + '</div>' +
    '</div>' +
    '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;margin-top:10px;"><input type="checkbox" name="global.message_filter.date_range.enabled"' + (getSettingLeafKey(mf, 'date_range.enabled') ? ' checked' : '') + '><span>日期范围过滤</span></label>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>起始日期</span><input name="global.message_filter.date_range.start_date" type="datetime-local" value="' + escAttr(getSettingLeafKey(mf, 'date_range.start_date') || '') + '"></label>' +
      '<label><span>结束日期</span><input name="global.message_filter.date_range.end_date" type="datetime-local" value="' + escAttr(getSettingLeafKey(mf, 'date_range.end_date') || '') + '"></label>' +
    '</div>' +
    '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;margin-top:10px;"><input type="checkbox" name="global.message_filter.keywords.enabled"' + (getSettingLeafKey(mf, 'keywords.enabled') ? ' checked' : '') + '><span>关键词过滤</span></label>' +
    '<label><span>关键词列表（逗号分隔）</span><input name="global.message_filter.keywords.words" value="' + escAttr(getSettingLeafKey(mf, 'keywords.words') || '') + '" placeholder="广告,推广,赞助"></label>';

  // Exports
  var expFields = document.getElementById('mob-settings-exports-fields');
  if (expFields) {
    var et = glob.export_table || {};
    expFields.innerHTML =
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;">' +
        '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.link"' + (et.link ? ' checked' : '') + '><span>链接统计表</span></label>' +
        '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.count"' + (et.count ? ' checked' : '') + '><span>计数统计表</span></label>' +
        '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.upload"' + (et.upload ? ' checked' : '') + '><span>上传统计表</span></label>' +
      '</div>';
  }
}

function getSettingLeafKey(obj, key) {
  if (!obj) return '';
  var parts = key.split('.');
  var cur = obj;
  for (var i = 0; i < parts.length; i++) { if (cur == null) return ''; cur = cur[parts[i]]; }
  return cur;
}

function selectedForward(glob) {
  var types = getSettingLeafKey(glob, 'forward_type');
  if (!types || typeof types !== 'object') return [];
  return Object.keys(types).filter(function(k) { return types[k]; });
}

function selectedMediaTypes(glob) {
  var types = getSettingLeafKey(glob, 'message_filter.media_types');
  if (!types || typeof types !== 'object') return [];
  return Object.keys(types).filter(function(k) { return types[k]; });
}

function selectedDownloadTypes(user) {
  return Array.isArray(user && user.download_type) ? user.download_type : [];
}

function escAttr(value) { return String(value || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

function renderCheckCards(baseName, types, selected, repeatName) {
  var html = '';
  var selSet = {};
  (selected || []).forEach(function(k) { selSet[k] = true; });
  var options = Array.isArray(types) ? types : Object.keys(types || {}).map(function(key) { return {value: key, label: types[key] || key}; });
  options.forEach(function(option) {
    var key = typeof option === 'string' ? option : option.value;
    var label = typeof option === 'string' ? option : (option.label || option.value);
    html += '<label style="display:flex;align-items:center;gap:6px;font-size:13px;padding:4px 0;">' +
      '<input type="checkbox" name="' + (repeatName ? baseName : baseName + '.' + key) + '" value="' + escAttr(key) + '"' + (selSet[key] ? ' checked' : '') + '>' +
      '<span>' + esc(label || key) + '</span></label>';
  });
  return html || '<span style="font-size:13px;color:var(--color-muted);">无可用选项</span>';
}

// ---------------------------------------------------------------------------
// Operations history
// ---------------------------------------------------------------------------
function mobInitDownloadTypes() {
  var grid = document.getElementById('mob-channel-download-types');
  if (!grid) return;
  var model = (window.state && window.state.settingsModel) || {options: {}};
  var types = model.options.download_type || [];
  var selected = (window.state && window.state.settings && window.state.settings.user && selectedDownloadTypes(window.state.settings.user)) || [];
  var selSet = {};
  selected.forEach(function(k) { selSet[k] = true; });
  var html = '';
  types.forEach(function(option) {
    var key = typeof option === 'string' ? option : option.value;
    var label = typeof option === 'string' ? option : (option.label || option.value);
    html += '<label style="display:flex;align-items:center;gap:6px;font-size:13px;padding:3px 0;">' +
      '<input type="checkbox" name="download_types" value="' + escAttr(key) + '"' + (selSet[key] ? ' checked' : '') + '>' +
      '<span>' + esc(label || key) + '</span></label>';
  });
  grid.innerHTML = html || '<span style="font-size:13px;color:var(--color-muted);">无可用类型</span>';
}

async function loadMobileOperations() {
  var container = document.getElementById('mob-operations-list');
  if (!container) return;
  try {
    var data = await fetchJson('/api/operations?limit=30');
    if (!data || !data.operations || data.operations.length === 0) {
      container.innerHTML = '<div class="mob-empty">暂无操作记录</div>';
      return;
    }
    var html = '';
    data.operations.forEach(function(op) {
      var payload = op.payload || {};
      var isChannelDownload = op.type === 'channel_download';
      var typeLabel = isChannelDownload ? '频道下载' : op.type === 'upload' ? '本地上传' : esc(op.type || '');
      var detail = isChannelDownload ? (payload.chat_link || '-') : (payload.path || op.detail || op.file || '#' + op.id);
      var statusClass = op.status === 'success' ? 'completed' : op.status === 'failure' ? 'failure' : 'pending';
      html += '<div class="mob-card status-' + esc(op.status || 'pending') + '">' +
        '<div class="mob-card__head">' +
          '<span class="mob-card__title">' + esc(detail) + '</span>' +
          '<span class="mob-card__badge ' + statusClass + '">' + typeLabel + '</span>' +
        '</div>' +
        '<div class="mob-card__row"><span class="label">状态</span><span>' + esc(op.status || '-') + '</span></div>' +
        (op.error_message || op.error ? '<div class="mob-card__row"><span class="label">错误</span><span>' + esc(op.error_message || op.error) + '</span></div>' : '') +
        '<div class="mob-card__row"><span class="label">时间</span><span>' + esc(op.created_at || '') + '</span></div>' +
      '</div>';
    });
    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<div class="mob-empty">加载失败</div>';
  }
}

// ---------------------------------------------------------------------------
// Records
// ---------------------------------------------------------------------------
async function loadMobileRecords() {
  var container = document.getElementById('mob-records-list');
  if (!container) return;
  try {
    var data = await fetchJson('/api/download-records?limit=50');
    if (!data || !Array.isArray(data.records) || data.records.length === 0) {
      container.innerHTML = '<div class="mob-empty" data-i18n="records.empty">还没有下载成功记录。</div>';
      return;
    }
    var html = '';
    data.records.forEach(function(r) {
      html += '<div class="mob-card">' +
        '<div class="mob-card__row"><span class="label">频道</span><span>' + esc(r.chat_id || r.chat_title || '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">消息</span><span>' + esc(r.message_id || '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">文件</span><span>' + esc(r.file_name || '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">大小</span><span>' + (r.file_size ? formatBytes(r.file_size) : '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">时间</span><span>' + esc(r.updated_at || '') + '</span></div>' +
      '</div>';
    });
    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<div class="mob-empty">加载失败</div>';
  }
}

// ---------------------------------------------------------------------------
// Statistics
// ---------------------------------------------------------------------------
async function loadMobileStatistics() {
  var container = document.getElementById('mob-statistics-list');
  if (!container) return;
  try {
    var data = await fetchJson('/api/statistics');
    var tables = data && data.tables ? data.tables : null;
    if (!tables) {
      container.innerHTML = '<div class="mob-empty">暂无统计数据</div>';
      return;
    }
    var rows = [
      { key: 'link', label: '链接统计表' },
      { key: 'count', label: '计数统计表' },
      { key: 'upload', label: '上传统计表' }
    ];
    var html = '';
    rows.forEach(function(row) {
      var t = tables[row.key] || {};
      html += '<div class="mob-card">' +
        '<div class="mob-card__head"><span class="mob-card__title">' + esc(row.label) + '</span></div>' +
        '<div class="mob-card__row"><span class="label">行数</span><span>' + (t.row_count || t.rows || 0) + '</span></div>' +
        '<div class="mob-card__row"><span class="label">可用</span><span>' + (t.available ? '是' : '否') + '</span></div>' +
      '</div>';
    });
    container.innerHTML = html || '<div class="mob-empty">暂无统计数据</div>';
  } catch (e) {
    container.innerHTML = '<div class="mob-empty">加载失败</div>';
  }
}

// ---------------------------------------------------------------------------
// Media management
// ---------------------------------------------------------------------------
async function loadMediaMobile() {
  var container = document.getElementById('mob-media-result');
  if (!container) return;
  container.innerHTML = '<div class="mob-empty">扫描中...</div>';
  try {
    var data = await fetchJson('/api/media/scan');
    if (!data) { container.innerHTML = '<div class="mob-empty">扫描失败</div>'; return; }
    var transferItems = ((data.transfer_items || {}).items || []);
    var orphanFiles = ((data.orphan_files || {}).files || []);

    var html = '<div style="font-size:13px;">' +
      '<div style="display:flex;gap:16px;flex-wrap:wrap;padding:12px;background:var(--color-surface-muted);border-radius:8px;margin-bottom:12px;">' +
        '<div><strong>总文件</strong><br>' + (data.total_count || 0) + '</div>' +
        '<div><strong>总大小</strong><br>' + formatBytes(data.total_size || 0) + '</div>' +
        '<div><strong>遗留文件</strong><br>' + orphanFiles.length + ' 个</div>' +
      '</div></div>';

    if (transferItems.length > 0) {
      html += '<div style="margin-top:12px;"><strong style="font-size:14px;">转存任务文件</strong></div>';
      transferItems.forEach(function(item) {
        html += '<div style="display:flex;justify-content:space-between;padding:6px 0;font-size:13px;border-bottom:1px solid var(--color-line);">' +
          '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc(item.file_name || item.local_path || '') + '</span>' +
          '<span style="flex-shrink:0;margin-left:8px;">' + formatBytes(item.file_size || 0) + '</span>' +
        '</div>';
      });
    }

    if (orphanFiles.length > 0) {
      html += '<div style="margin-top:12px;"><strong style="font-size:14px;">遗留文件</strong></div>';
      orphanFiles.forEach(function(f) {
        html += '<div style="display:flex;justify-content:space-between;padding:6px 0;font-size:13px;border-bottom:1px solid var(--color-line);">' +
          '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc(f.path || '') + '</span>' +
          '<span style="flex-shrink:0;margin-left:8px;">' + formatBytes(f.size || 0) + '</span>' +
        '</div>';
      });
    }

    if (!transferItems.length && !orphanFiles.length) {
      html += '<div class="mob-empty">没有可清理文件</div>';
    } else {
      html += '<div class="mob-empty">请在桌面端选择并执行清理</div>';
    }

    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<div class="mob-empty">加载失败: ' + esc(e.message || '') + '</div>';
  }
}

// ---------------------------------------------------------------------------
// Event bindings (init)
// ---------------------------------------------------------------------------
(function() {
  // Tab bar clicks
  var tabbar = document.getElementById('mob-tabbar');
  if (tabbar) {
    tabbar.querySelectorAll('.mob-tab').forEach(function(tab) {
      tab.addEventListener('click', function() {
        mobSwitchView(tab.dataset.mobTab);
      });
    });
  }

  // Top bar back button
  var backBtn = document.getElementById('mob-topbar-back');
  if (backBtn) {
    backBtn.addEventListener('click', function() {
      mobNavigateBack();
    });
  }

  // Profile menu items
  var menu = document.getElementById('mob-profile-menu');
  if (menu) {
    menu.querySelectorAll('[data-profile-nav]').forEach(function(item) {
      item.addEventListener('click', function() {
        mobNavigateTo(item.dataset.profileNav);
      });
    });
  }

  // Language button (toggle zh/en)
  var langBtn = document.getElementById('mob-btn-language');
  if (langBtn) {
    langBtn.addEventListener('click', function() {
      var current = (window.state && window.state.lang) || 'zh';
      var next = current === 'zh' ? 'en' : 'zh';
      if (window.state) window.state.lang = next;
      localStorage.setItem('trmd-lang', next);
      var label = document.getElementById('mob-lang-label');
      if (label) label.textContent = next === 'zh' ? '中文' : 'English';
      if (typeof setLang === 'function') setLang(next);
      showToast(next === 'zh' ? '已切换为中文' : 'Switched to English');
      loadCurrentView();
    });
  }

  // Logout button
  var logoutBtn = document.getElementById('mob-btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async function() {
      if (!confirm('确认退出登录？')) return;
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
        stopPolling();
        if (window.state) { window.state.tasks = []; window.state.watches = []; }
        document.querySelectorAll('.mob-view,.mob-subpage').forEach(function(v) { v.classList.remove('active'); });
        var transfers = document.getElementById('mob-view-transfers');
        if (transfers) transfers.classList.add('active');
        mobSwitchView('transfers');
        checkAuthStatus();
      } catch (e) { showToast('退出失败'); }
    });
  }

  // Collapse toggles (delegated only — avoid double-fire with inline handlers)
  document.addEventListener('click', function(e) {
    var head = e.target.closest('.mob-collapse__head');
    if (head && !e.target.closest('button, input, select, textarea, label')) {
      toggleCollapse(head);
    }
  });

  // Sheet overlay close
  var sheetOverlay = document.getElementById('mob-sheet-overlay');
  if (sheetOverlay) {
    sheetOverlay.addEventListener('click', function(e) {
      if (e.target === sheetOverlay) closeSheet();
    });
  }

  // Watch type toggle
  var watchTypeSelect = document.getElementById('mob-watch-type');
  if (watchTypeSelect) {
    watchTypeSelect.addEventListener('change', function() {
      var val = watchTypeSelect.value;
      var targetGroup = document.getElementById('mob-watch-target-group');
      var commentGroup = document.getElementById('mob-watch-comment-group');
      var sourceLabel = document.getElementById('mob-watch-source-label');
      var sourceTextarea = document.querySelector('#mob-watch-source-group textarea[name="source_links"]');
      var sourceInput = document.querySelector('#mob-watch-source-group input[name="source_link"]');

      if (val === 'download') {
        if (targetGroup) targetGroup.classList.add('hidden');
        if (commentGroup) commentGroup.classList.add('hidden');
        if (sourceLabel) sourceLabel.querySelector('span').textContent = '来源频道';
        if (sourceTextarea) { sourceTextarea.classList.remove('hidden'); sourceTextarea.required = true; }
        if (sourceInput) { sourceInput.classList.add('hidden'); sourceInput.required = false; }
      } else {
        if (targetGroup) targetGroup.classList.remove('hidden');
        if (commentGroup) commentGroup.classList.remove('hidden');
        if (sourceLabel) sourceLabel.querySelector('span').textContent = '来源频道';
        if (sourceTextarea) { sourceTextarea.classList.add('hidden'); sourceTextarea.required = false; }
        if (sourceInput) { sourceInput.classList.remove('hidden'); sourceInput.required = true; }
      }
    });
  }

  // Transfer form
  var transferForm = document.getElementById('mob-transfer-form');
  if (transferForm) {
    transferForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var formData = new FormData(transferForm);
      var payload = {};
      formData.forEach(function(v, k) { payload[k] = v; });
      if (payload.start_id) payload.start_id = Number(payload.start_id);
      if (payload.end_id) payload.end_id = Number(payload.end_id);
      payload.include_comment = transferForm.querySelector('[name="include_comment"]').checked;
      var notice = document.getElementById('mob-form-notice');
      try {
        await postJson('/api/tasks', payload);
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建成功'; notice.style.color = 'var(--color-success)'; }
        transferForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileTasks(); }, 1000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Watch form
  var watchForm = document.getElementById('mob-watch-form');
  if (watchForm) {
    watchForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var formData = new FormData(watchForm);
      var payload = { type: formData.get('type') };
      if (payload.type === 'download') {
        payload.source_links = (formData.get('source_links') || '').split('\n').map(function(s) { return s.trim(); }).filter(Boolean);
        payload.include_comment = watchForm.querySelector('[name="include_comment"]') ? watchForm.querySelector('[name="include_comment"]').checked : false;
      } else {
        payload.source_link = formData.get('source_link');
        payload.target_link = formData.get('target_link');
        payload.include_comment = watchForm.querySelector('[name="include_comment"]') ? watchForm.querySelector('[name="include_comment"]').checked : false;
      }
      var notice = document.getElementById('mob-watch-notice');
      try {
        await postJson('/api/watches', payload);
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建成功'; notice.style.color = 'var(--color-success)'; }
        watchForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileWatches(); }, 1000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Channel download form
  var channelForm = document.getElementById('mob-channel-form');
  if (channelForm) {
    channelForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var formData = new FormData(channelForm);
      var payload = { chat_link: formData.get('chat_link') };
      if (formData.get('start_date')) payload.start_date = formData.get('start_date');
      if (formData.get('end_date')) payload.end_date = formData.get('end_date');
      if (formData.get('keywords')) payload.keywords = formData.get('keywords');
      payload.include_comment = channelForm.querySelector('[name="include_comment"]').checked;
      var checkboxes = channelForm.querySelectorAll('[name="download_types"]:checked');
      if (checkboxes.length > 0) payload.download_type = Array.from(checkboxes).map(function(cb) { return cb.value; });

      var notice = document.getElementById('mob-channel-notice');
      try {
        await postJson('/api/channel-downloads', payload);
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建成功'; notice.style.color = 'var(--color-success)'; }
        channelForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileOperations(); }, 1000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Upload form
  var uploadForm = document.getElementById('mob-upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var formData = new FormData(uploadForm);
      var payload = { path: formData.get('path'), target_link: formData.get('target_link'), recursive: uploadForm.querySelector('[name="recursive"]').checked };
      var notice = document.getElementById('mob-upload-notice');
      try {
        await postJson('/api/uploads', payload);
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建成功'; notice.style.color = 'var(--color-success)'; }
        uploadForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileOperations(); }, 1000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '创建失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Settings save
  var saveBtn = document.getElementById('mob-save-settings');
  if (saveBtn) {
    saveBtn.addEventListener('click', async function() {
      var notice = document.getElementById('mob-settings-notice');
      var settingsContainer = document.getElementById('mob-subpage-settings');
      if (!settingsContainer) return;

      // Collect form data from all inputs in settings subpage
      var inputs = settingsContainer.querySelectorAll('input[name], select[name]');
      var payload = {};
      var downloadTypes = Array.from(settingsContainer.querySelectorAll('input[name="user.download_type"]:checked')).map(function(input) { return input.value; });
      payload.user = payload.user || {};
      payload.user.download_type = downloadTypes;
      inputs.forEach(function(input) {
        if (input.name === 'user.download_type') return;
        var keys = input.name.split('.');
        var cur = payload;
        for (var i = 0; i < keys.length - 1; i++) {
          if (!cur[keys[i]]) cur[keys[i]] = {};
          cur = cur[keys[i]];
        }
        var lastKey = keys[keys.length - 1];
        if (input.type === 'checkbox') {
          cur[lastKey] = input.checked;
        } else if (input.type === 'number') {
          cur[lastKey] = input.value !== '' ? Number(input.value) : undefined;
        } else {
          cur[lastKey] = input.value || undefined;
        }
      });

      // Clean undefined values
      function clean(obj) {
        Object.keys(obj).forEach(function(k) {
          if (obj[k] === undefined) delete obj[k];
          else if (typeof obj[k] === 'object' && obj[k] !== null) clean(obj[k]);
        });
      }
      clean(payload);

      try {
        await postJson('/api/settings', payload, 'PATCH');
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '保存成功'; notice.style.color = 'var(--color-success)'; }
        setTimeout(function() { if (notice) notice.classList.add('hidden'); }, 2000);
      } catch (e) {
        if (notice) { notice.classList.remove('hidden'); notice.textContent = '保存失败: ' + (e.message || ''); notice.style.color = 'var(--color-danger)'; }
      }
    });
  }

  // Media scan button
  var mediaBtn = document.getElementById('mob-media-scan-btn');
  if (mediaBtn) mediaBtn.addEventListener('click', loadMediaMobile);

  // Kickoff
  checkAuthStatus();
})();
