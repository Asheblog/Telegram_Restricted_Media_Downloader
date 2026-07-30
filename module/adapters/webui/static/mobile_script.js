// ================================================================
// mobile_script.js v2 — 4-tab clean navigation, no FAB/Drawer
// ($ already defined in shared.js)
// ================================================================

// ---------------------------------------------------------------------------
// Login helpers (delegates to shared.js utilities)
// ---------------------------------------------------------------------------
function showLoginStep(step) {
  var steps = ['preparing', 'phone', 'code', 'password', 'recovery', 'signup', 'done'];
  steps.forEach(function(id) {
    var el = document.getElementById('login-form-' + id);
    if (!el) return;
    el.classList.add('hidden');
    el.style.display = 'none';
  });
  var el = document.getElementById('login-form-' + step);
  if (el) {
    el.classList.remove('hidden');
    el.style.display = '';
  }
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
    if (typeof checkSetupStatus === 'function') {
      var setup = await checkSetupStatus();
      if (setup && setup.wizard_active && setup.current_step === 'api') {
        hideLogin();
        return;
      }
    }
    var resp = await fetch('/api/auth/status');
    if (resp.status === 401) { redirectToLoginPage(); return; }
    var state = await resp.json();
    if (!state || !state.step) return;
    switch (state.step) {
      case 'pending':
        if (typeof lastSetupStatus !== 'undefined' && lastSetupStatus && lastSetupStatus.current_step === 'telegram') {
          showLoginStep('preparing');
          return;
        }
        if (typeof lastSetupStatus !== 'undefined' && lastSetupStatus && !lastSetupStatus.ready) {
          hideLogin();
          return;
        }
        var container = document.getElementById('login-container');
        if (container) container.classList.remove('active');
        await loadCurrentView();
        startPolling();
        return;
      case 'done': case 'none':
        if (typeof lastSetupStatus !== 'undefined' && lastSetupStatus && lastSetupStatus.current_step === 'telegram') {
          showLoginStep('preparing');
          return;
        }
        if (typeof lastSetupStatus !== 'undefined' && lastSetupStatus && !lastSetupStatus.ready) {
          hideLogin();
          return;
        }
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
    if (phone.charAt(0) !== '+') { showLoginError('电话号码需以 +地区号开头'); return; }
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
var mobWatchDownloadPollTimer = null;
var mobWatchDownloadState = { watchId: null };

function hasActiveTasks() {
  return (window.state && Array.isArray(window.state.tasks) && window.state.tasks.some(function(t) {
    return t.status === 'pending' || t.status === 'running' || t.status === 'pausing';
  }));
}

function resetTaskPolling() {
  stopPolling();
  startPolling();
}

function startPolling() {
  stopPolling();
  initialLoadDone = true;

  async function poll() {
    if (document.hidden) {
      pollTimer = setTimeout(poll, hasActiveTasks() ? 1000 : 10000);
      return;
    }
    await loadCurrentView();
    pollTimer = setTimeout(poll, hasActiveTasks() ? 1000 : 10000);
  }

  poll();
}

document.addEventListener('visibilitychange', function() {
  if (document.hidden) return;
  loadCurrentView();
  startPolling();
});

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
  else if (id === 'mob-view-watches') {
    await loadMobileWatches();
  }
  else if (id === 'mob-view-downloads-uploads') { await loadMobileDownloadsUploads(); }
  // profile sub-pages load on demand
  var subActive = document.querySelector('.mob-subpage.active');
  if (subActive) {
    if (subActive.id === 'mob-subpage-statistics') { await loadMobileStatistics(); }
    else if (subActive.id === 'mob-subpage-records') { await loadMobileRecords(); }
    else if (subActive.id === 'mob-subpage-system-logs') {
      syncMobileSystemLogsFiltersUI();
      await loadMobileSystemLogs();
    }
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
  'archive-organize': '归档整理',
  settings: '系统设置',
  'system-logs': '系统日志'
};

var MOBILE_MAIN_TABS = {
  transfers: true,
  watches: true,
  'downloads-uploads': true,
  profile: true
};

var MOBILE_PROFILE_SUBPAGES = {
  statistics: true,
  records: true,
  media: true,
  'archive-organize': true,
  settings: true,
  'system-logs': true
};

function mobSwitchView(view, options) {
  options = options || {};
  if (!MOBILE_MAIN_TABS[view]) {
    view = 'transfers';
  }

  stopMobileSystemLogsAutoRefresh();

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

  // Hide all subpages and restore profile menu when leaving a subpage
  var subs = document.querySelectorAll('.mob-subpage');
  subs.forEach(function(s) { s.classList.remove('active'); });
  var menu = document.getElementById('mob-profile-menu');
  if (menu) menu.style.display = '';
  currentProfileSub = null;

  currentMainTab = view;

  if (options.syncUrl !== false) {
    syncSpaUrl(view, { replace: !!options.replaceUrl });
  }

  // Load content
  if (view === 'transfers') { loadMobileTasks(); }
  else if (view === 'watches') { loadMobileWatches(); }
  else if (view === 'downloads-uploads') { loadMobileDownloadsUploads(); }
  else if (view === 'profile') { /* menu is static, sub-pages load on demand */ }
}

function mobNavigateTo(subpage, options) {
  options = options || {};
  if (!MOBILE_PROFILE_SUBPAGES[subpage]) {
    mobSwitchView('profile', options);
    return;
  }

  // Ensure profile tab is active without rewriting URL yet
  if (currentMainTab !== 'profile') {
    mobSwitchView('profile', { syncUrl: false });
  } else {
    // Hide other main-view active state already on profile
    exitSubPage();
  }

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
  currentMainTab = 'profile';

  if (options.syncUrl !== false) {
    syncSpaUrl(subpage, { replace: !!options.replaceUrl });
  }

  // Load content
  if (subpage === 'statistics') { loadMobileStatistics(); }
  else if (subpage === 'records') { loadMobileRecords(); }
  else if (subpage === 'media') { loadMediaMobile(); }
  else if (subpage === 'archive-organize') { loadArchiveOrganizeMobile(); }
  else if (subpage === 'settings') { loadMobileSettings(); }
  else if (subpage === 'system-logs') {
    syncMobileSystemLogsFiltersUI();
    loadMobileSystemLogs();
    startMobileSystemLogsAutoRefresh();
  }
}

function mobNavigateBack(options) {
  options = options || {};
  stopMobileSystemLogsAutoRefresh();
  exitSubPage();

  // Hide all subpages
  var subs = document.querySelectorAll('.mob-subpage');
  subs.forEach(function(s) { s.classList.remove('active'); });

  // Show profile menu
  var menu = document.getElementById('mob-profile-menu');
  if (menu) menu.style.display = '';

  currentProfileSub = null;

  if (options.syncUrl !== false) {
    syncSpaUrl('profile', { replace: !!options.replaceUrl });
  }
}

function applyMobileRouteFromLocation() {
  var path = normalizeSpaPathname(window.location.pathname);
  var view = viewFromPath(path);

  if (path === '/' || path === '/index.html') {
    mobSwitchView('transfers', { replaceUrl: true });
    return;
  }
  if (view === 'system-logs') {
    mobNavigateTo('system-logs', { syncUrl: false });
    return;
  }
  if (!view) {
    mobSwitchView('transfers', { replaceUrl: true });
    return;
  }
  if (MOBILE_PROFILE_SUBPAGES[view]) {
    mobNavigateTo(view, { syncUrl: false });
    return;
  }
  if (MOBILE_MAIN_TABS[view]) {
    mobSwitchView(view, { syncUrl: false });
    return;
  }
  mobSwitchView('transfers', { replaceUrl: true });
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
  el.style.whiteSpace = 'normal';
  el.style.maxWidth = '90vw';
  el.style.textAlign = 'center';
  el.classList.add('show');
  clearTimeout(el._timeout);
  el._timeout = setTimeout(function() { el.classList.remove('show'); }, duration || 2000);
}

function showMobFormError(noticeEl, err, fallbackKey) {
  var msg = typeof translateApiError === 'function'
    ? translateApiError(err, fallbackKey || 'form.createFailed')
    : ((err && (err.error || err.message)) || '请求失败');
  if (noticeEl) {
    noticeEl.classList.remove('hidden');
    noticeEl.classList.add('is-error');
    noticeEl.classList.remove('is-success');
    noticeEl.textContent = msg;
    noticeEl.style.color = '';
  }
  showToast(msg, 4500);
  return msg;
}

function showMobFormSuccess(noticeEl, message) {
  if (noticeEl) {
    noticeEl.classList.remove('hidden');
    noticeEl.classList.add('is-success');
    noticeEl.classList.remove('is-error');
    noticeEl.textContent = message;
    noticeEl.style.color = '';
  }
}

// ---------------------------------------------------------------------------
// Badge helper
// ---------------------------------------------------------------------------
function mobBadge(status) {
  var map = {
    pending: '<span class="mob-card__badge pending">等待中</span>',
    running: '<span class="mob-card__badge running">运行中</span>',
    pausing: '<span class="mob-card__badge paused">暂停中…</span>',
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
  var commentContainer = document.getElementById('mob-watches-list-comment');
  if (!container && !commentContainer) return;
  if (!window.state) window.state = {};
  if (!Array.isArray(window.state.watches)) {
    if (container) container.innerHTML = mobEmptyHtml('加载中...');
    if (commentContainer) commentContainer.innerHTML = '';
  }
  try {
    var data = await fetchJson(withClientTzQuery('/api/watches'));
    window.state.watches = Array.isArray(data.watches) ? data.watches : [];
    renderMobWatches();
  } catch (e) {
    window.state.watches = [];
    if (container) container.innerHTML = mobEmptyHtml('加载失败');
    if (commentContainer) commentContainer.innerHTML = mobEmptyHtml('加载失败');
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
    var rangeDetail = taskRangeDetailSummary(t);
    var fileDetail = taskFileTransferDetail(t);
    html += '<div class="mob-card status-' + esc(t.status) + '" data-task-id="' + t.id + '">' +
      '<div class="mob-card__head">' +
        '<span class="mob-card__title">' + esc(t.title || t.source_link || '#' + t.id) + '</span>' +
        mobBadge(t.status) +
      '</div>' +
      '<div class="mob-card__row"><span class="label">来源</span><span>' + esc(t.source_link || '-') + '</span></div>' +
      '<div class="mob-card__row"><span class="label">进度</span><span>' + esc(taskCompletedLabel(t)) + (taskFailedCount(t) ? ' · 失败 ' + taskFailedCount(t) : '') + '</span></div>' +
      (rangeDetail ? '<div class="mob-card__row mob-card__row--stack"><span class="label">当前 ID</span><span>' + esc(rangeDetail) + '</span></div>' : '') +
      (fileDetail ? '<div class="mob-card__row mob-card__row--stack"><span class="label">文件</span><span>' + esc(fileDetail) + '</span></div>' : '') +
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
function mobFindWatchById(watchId) {
  return (window.state && Array.isArray(window.state.watches) ? window.state.watches : []).find(function(watch) {
    return String(watch.id) === String(watchId);
  }) || null;
}

function mobWatchHelpers() {
  return globalThis.WatchUiHelpers || {};
}

function mobWatchSource(watch) {
  if (!watch) return '-';
  if (watch.source_link) return watch.source_link;
  if (Array.isArray(watch.source_links) && watch.source_links.length) return watch.source_links[0];
  return '-';
}

function mobWatchRoute(watch) {
  var source = mobWatchSource(watch);
  var target = watch && (watch.target_link || '本地') || '本地';
  var helpers = mobWatchHelpers();
  var route = typeof helpers.formatWatchRoute === 'function'
    ? helpers.formatWatchRoute(source, target)
    : source + ' → ' + target;
  var extraSources = watch && Array.isArray(watch.source_links) ? watch.source_links.length - 1 : 0;
  return extraSources > 0 ? route + ' +' + extraSources : route;
}

function mobWatchShortLink(link) {
  var helpers = mobWatchHelpers();
  if (typeof helpers.shortTelegramLink === 'function') {
    return helpers.shortTelegramLink(link);
  }
  return link || '-';
}

function mobSummarizeWatchEvent(evt) {
  var helpers = mobWatchHelpers();
  if (typeof helpers.summarizeWatchEvent === 'function') return helpers.summarizeWatchEvent(evt);
  if (evt && evt.status === 'success') return { kind: 'success', titleKey: 'watches.eventForwarded', detail: '' };
  if (evt && evt.status === 'skipped') return { kind: 'filtered', titleKey: 'watches.eventSkipped', detail: evt.message || '' };
  return { kind: 'failure', titleKey: 'watches.eventFailed', detail: evt && evt.message || '' };
}

function mobFilterWatchEvents(items, filter) {
  var helpers = mobWatchHelpers();
  if (typeof helpers.filterWatchEventsByStatus === 'function') return helpers.filterWatchEventsByStatus(items, filter);
  if (!filter || filter === 'all') return (items || []).slice();
  return (items || []).filter(function(evt) { return mobSummarizeWatchEvent(evt).kind === filter; });
}

function mobWatchHistoryStatusQuery(filter) {
  if (filter === 'success') return 'success';
  if (filter === 'filtered') return 'skipped';
  if (filter === 'failure') return 'failure';
  return '';
}

function mobWatchModeTitle(mode) {
  if (mode === 'downloads') return t('watches.downloadRecordsTitle');
  if (mode === 'deferred') return t('watches.deferredComments');
  return t('watches.historyTitle');
}

function buildMobWatchCardHtml(w) {
  var statusClass = w.status === 'paused' ? 'paused' : 'running';
  var statusLabel = w.status === 'paused' ? t('status.paused') : t('status.running');
  var typeLabel = w.type === 'download' ? t('watches.download') : t('watches.forward');
  var typeClass = w.type === 'download' ? 'completed' : 'running';
  var eventCount = Number(w.event_count || 0);
  var todayCount = Number(w.today_count || 0);
  var deferredCount = Number(w.deferred_comment_count || 0);
  var queueCount = Number(w.download_queue_count || 0);
  var completedDownloadCount = Number(w.download_completed_count || 0);
  var downloadLabel = t('watches.downloadRecordsTitle');
  var sourceFull = mobWatchSource(w) || '-';
  var targetFull = (w.target_link || '本地');
  var sourceShort = mobWatchShortLink(sourceFull);
  var targetShort = mobWatchShortLink(targetFull);
  var historyLabel = t('watches.historyTitle');
  var deferredBadge = w.type === 'forward' && w.include_comment && deferredCount > 0
    ? '<button class="watch-deferred-badge watch-touch-btn" data-mob-watch-detail="' + esc(w.id) + '" data-mob-watch-detail-mode="deferred">' +
        esc(t('watches.deferredComments')) + ' ' + deferredCount +
      '</button>'
    : '';
  var statsHtml = '';
  if (w.type === 'forward') {
    statsHtml =
      '<div class="mob-watch-stats">' +
        '<button type="button" class="mob-watch-stat watch-touch-btn" data-mob-watch-detail="' + esc(w.id) + '" data-mob-watch-detail-mode="downloads" title="' + esc(downloadLabel) + '" aria-label="' + esc(t('watches.downloadQueueCount') + ': ' + queueCount) + '">' +
          '<span class="mob-watch-stat__label">' + esc(t('watches.downloadQueueCount')) + '</span>' +
          '<span class="mob-watch-stat__value">' + esc(String(queueCount)) + '</span>' +
        '</button>' +
        '<button type="button" class="mob-watch-stat watch-touch-btn" data-mob-watch-detail="' + esc(w.id) + '" data-mob-watch-detail-mode="downloads" title="' + esc(downloadLabel) + '" aria-label="' + esc(t('watches.downloadCompletedCount') + ': ' + completedDownloadCount) + '">' +
          '<span class="mob-watch-stat__label">' + esc(t('watches.downloadCompletedCount')) + '</span>' +
          '<span class="mob-watch-stat__value">' + esc(String(completedDownloadCount)) + '</span>' +
        '</button>' +
        '<button type="button" class="mob-watch-stat watch-touch-btn" data-mob-watch-detail="' + esc(w.id) + '" data-mob-watch-detail-mode="history" data-mob-watch-detail-today="1" title="' + esc(historyLabel) + '" aria-label="' + esc(t('watches.todayEvents') + ': ' + todayCount) + '">' +
          '<span class="mob-watch-stat__label">' + esc(t('watches.todayEvents')) + '</span>' +
          '<span class="mob-watch-stat__value">' + esc(String(todayCount)) + '</span>' +
        '</button>' +
        '<button type="button" class="mob-watch-stat mob-watch-stat--primary watch-touch-btn" data-mob-watch-detail="' + esc(w.id) + '" data-mob-watch-detail-mode="history" data-mob-watch-detail-today="0" title="' + esc(historyLabel) + '" aria-label="' + esc(t('watches.totalEvents') + ': ' + eventCount) + '">' +
          '<span class="mob-watch-stat__label">' + esc(t('watches.totalEvents')) + '</span>' +
          '<span class="mob-watch-stat__value">' + esc(String(eventCount)) + '</span>' +
        '</button>' +
      '</div>';
  } else {
    statsHtml =
      '<div class="mob-watch-stats mob-watch-stats--readonly">' +
        '<div class="mob-watch-stat">' +
          '<span class="mob-watch-stat__label">' + esc(t('watches.todayEvents')) + '</span>' +
          '<span class="mob-watch-stat__value">' + esc(String(todayCount)) + '</span>' +
        '</div>' +
        '<div class="mob-watch-stat">' +
          '<span class="mob-watch-stat__label">' + esc(t('watches.totalEvents')) + '</span>' +
          '<span class="mob-watch-stat__value">' + esc(String(eventCount)) + '</span>' +
        '</div>' +
      '</div>';
  }
  var actionsHtml = '';
  if (w.type === 'forward') {
    actionsHtml =
      '<button type="button" class="mob-btn mob-btn-sm mob-btn-muted watch-touch-btn" data-mob-watch-action="edit" data-watch-id="' + esc(w.id) + '">' + esc(t('watches.edit')) + '</button>' +
      '<button type="button" class="mob-btn mob-btn-sm mob-btn-muted watch-touch-btn" data-mob-watch-action="downloads" data-watch-id="' + esc(w.id) + '">' + esc(t('watches.downloadRecords')) + '</button>' +
      '<button type="button" class="mob-btn mob-btn-sm mob-btn-danger watch-touch-btn" data-mob-watch-action="delete" data-watch-id="' + esc(w.id) + '">' + esc(t('tasks.delete')) + '</button>';
  } else {
    actionsHtml =
      '<button type="button" class="mob-btn mob-btn-sm mob-btn-danger watch-touch-btn" data-mob-watch-action="delete" data-watch-id="' + esc(w.id) + '">' + esc(t('tasks.delete')) + '</button>';
  }
  return '<div class="mob-card status-' + statusClass + ' mob-watch-card" data-watch-id="' + esc(w.id) + '">' +
    '<div class="mob-watch-card__head">' +
      '<div class="watch-task-head">' +
        '<span class="watch-status-dot ' + statusClass + '" aria-hidden="true"></span>' +
        '<span class="mob-card__badge ' + typeClass + '">' + esc(typeLabel) + '</span>' +
        '<span class="text-xs text-muted">' + esc(statusLabel) + '</span>' +
        deferredBadge +
      '</div>' +
    '</div>' +
    '<div class="mob-watch-meta" role="table" aria-label="' + esc(typeLabel) + '">' +
      '<div class="mob-watch-meta__row" role="row">' +
        '<span class="mob-watch-meta__label" role="rowheader">' + esc(t('watches.source')) + '</span>' +
        '<span class="mob-watch-meta__value" role="cell" title="' + esc(sourceFull) + '">' + esc(sourceShort) + '</span>' +
      '</div>' +
      '<div class="mob-watch-meta__row" role="row">' +
        '<span class="mob-watch-meta__label" role="rowheader">' + esc(t('watches.target')) + '</span>' +
        '<span class="mob-watch-meta__value" role="cell" title="' + esc(targetFull) + '">' + esc(targetShort) + '</span>' +
      '</div>' +
    '</div>' +
    statsHtml +
    '<div class="mob-card__actions mob-watch-card__actions' + (w.type === 'forward' ? '' : ' mob-watch-card__actions--single') + '">' +
      actionsHtml +
    '</div>' +
  '</div>';
}

function fillMobWatchList(container, watches) {
  if (!container) return;
  if (!watches.length) {
    container.innerHTML = mobEmptyHtml('还没有实时监听。', 'watches.empty');
    return;
  }
  container.innerHTML = watches.map(buildMobWatchCardHtml).join('');
  bindMobWatchCardEvents(container);
}

function renderMobWatches() {
  var container = document.getElementById('mob-watches-list');
  var commentContainer = document.getElementById('mob-watches-list-comment');
  if (!container && !commentContainer) return;
  var watches = (window.state && Array.isArray(window.state.watches)) ? window.state.watches : [];
  var helpers = mobWatchHelpers();
  var groups = typeof helpers.partitionWatchesByComment === 'function'
    ? helpers.partitionWatchesByComment(watches)
    : { withoutComment: watches, withComment: [] };
  fillMobWatchList(container, groups.withoutComment || []);
  fillMobWatchList(commentContainer, groups.withComment || []);
}

function bindMobWatchCardEvents(container) {
  container.querySelectorAll('[data-mob-watch-detail]').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      var todayAttr = btn.dataset.mobWatchDetailToday;
      var options = {};
      if (todayAttr === '1') options.todayOnly = true;
      if (todayAttr === '0') options.todayOnly = false;
      openMobileWatchDetail(btn.dataset.mobWatchDetail, btn.dataset.mobWatchDetailMode || 'history', options);
    });
  });
  container.querySelectorAll('[data-mob-watch-action]').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      handleMobileWatchMenuAction(btn.dataset.watchId, btn.dataset.mobWatchAction);
    });
  });
}

async function handleMobileWatchMenuAction(watchId, action) {
  if (action === 'edit') {
    openMobileWatchEditSheet(watchId);
    return;
  }
  if (action === 'downloads' || action === 'deferred') {
    await openMobileWatchDetail(watchId, action);
    return;
  }
  if (action === 'delete') {
    closeSheet();
    try {
      await deleteWatch(watchId);
    } catch (e) {
      alert(typeof translateApiError === 'function' ? translateApiError(e, 'form.requestFailed') : '删除失败');
    }
  }
}

function openMobileWatchEditSheet(watchId) {
  var watch = mobFindWatchById(watchId);
  var overlay = document.getElementById('mob-sheet-overlay');
  var sheet = document.getElementById('mob-sheet');
  if (!overlay || !sheet || !watch) return;
  sheetState.sheetType = 'watch-edit';
  sheetState.watchId = watchId;
  sheet.className = 'mob-sheet';
  sheet.innerHTML = '<div class="mob-sheet__title">' + esc(t('watches.edit')) + '</div>' +
    '<form id="mob-watch-edit-form">' +
      '<label><span>' + esc(t('watches.source')) + '</span><input name="source_link" required value="' + escAttr(watch.source_link || '') + '"></label>' +
      '<label><span>' + esc(t('watches.target')) + '</span><input name="target_link" required value="' + escAttr(watch.target_link || '') + '"></label>' +
      '<label><input type="checkbox" name="include_comment"' + (watch.include_comment ? ' checked' : '') + '><span>' + esc(t('watches.includeComment')) + '</span></label>' +
      '<label><input type="checkbox" name="resolve_deep_link"' + (watch.resolve_deep_link ? ' checked' : '') + '><span>' + esc(t('watches.resolveDeepLink')) + '</span></label>' +
      '<label><input type="checkbox" name="archive_by_author"' + (watch.archive_by_author ? ' checked' : '') + '><span>' + esc(t('watches.archiveByAuthor')) + '</span></label>' +
      '<div' + (watch.include_comment ? '' : ' class="hidden"') + ' data-comment-delay-field>' +
        '<label><span>' + esc(t('watches.commentDelayMinutes')) + '</span>' +
          '<input type="number" name="comment_delay_minutes" min="0" max="1440" value="' +
            (watch.comment_delay_minutes == null ? '' : escAttr(String(watch.comment_delay_minutes))) +
            '" placeholder="' + escAttr(t('watches.commentDelayPlaceholder')) + '">' +
        '</label>' +
        '<p class="mob-form-hint">' + esc(t('watches.commentDelayHint')) + '</p>' +
      '</div>' +
      mediaTypesPickerMarkup({ compact: true, selected: watch.media_types }) +
      '<div style="display:flex;gap:8px;margin-top:6px;">' +
        '<button class="mob-btn watch-touch-btn" type="submit">' + esc(t('action.save')) + '</button>' +
        '<button class="mob-btn mob-btn-muted watch-touch-btn" type="button" id="mob-watch-edit-cancel">' + esc(t('action.cancel')) + '</button>' +
      '</div>' +
    '</form>';
  overlay.classList.add('open');
  bindAllMediaTypesPickers(sheet);
  bindCommentDelayField(document.getElementById('mob-watch-edit-form'));
  document.getElementById('mob-watch-edit-cancel')?.addEventListener('click', closeSheet);
  document.getElementById('mob-watch-edit-form')?.addEventListener('submit', async function(event) {
    event.preventDefault();
    var form = event.currentTarget;
    var payload = {
      source_link: form.querySelector('[name="source_link"]').value.trim(),
      target_link: form.querySelector('[name="target_link"]').value.trim(),
      include_comment: form.querySelector('[name="include_comment"]').checked,
      resolve_deep_link: form.querySelector('[name="resolve_deep_link"]').checked,
      archive_by_author: form.querySelector('[name="archive_by_author"]') ? form.querySelector('[name="archive_by_author"]').checked : false,
      comment_delay_minutes: readOptionalCommentDelayMinutes(form),
      media_types: readMediaTypesOverride(form)
    };
    try {
      var resp = await fetch('/api/watches/' + encodeURIComponent(watchId), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!resp.ok) {
        var data = {};
        try { data = await resp.json(); } catch (e) {}
        showMobFormError(null, data, 'form.requestFailed');
        return;
      }
      closeSheet();
      await loadMobileWatches();
      if (typeof loadWatches === 'function') loadWatches();
    } catch (e) {
      showMobFormError(null, e, 'form.requestFailed');
    }
  });
}

async function openMobileWatchDetail(watchId, mode, options) {
  stopMobWatchDownloadPolling();
  var detailMode = mode || 'history';
  var opts = options || {};
  sheetState.sheetType = 'watch-detail';
  state.watchDetail = {
    watchId: watchId,
    mode: detailMode,
    page: 1,
    pageSize: 20,
    total: 0,
    filter: 'all',
    todayOnly: detailMode === 'history' ? Boolean(opts.todayOnly) : false,
    items: [],
    statusCounts: null
  };
  if (detailMode === 'downloads') mobWatchDownloadState = { watchId: watchId };
  var overlay = document.getElementById('mob-sheet-overlay');
  var sheet = document.getElementById('mob-sheet');
  if (!overlay || !sheet) return;
  sheet.className = 'mob-sheet mob-sheet--task-detail mob-sheet--watch-detail';
  renderMobileWatchDetailShell(mobFindWatchById(watchId), detailMode);
  overlay.classList.add('open');
  await loadMobileWatchDetail(false);
  if (detailMode === 'downloads') startMobWatchDownloadPolling();
}

function renderMobileWatchDetailShell(watch, mode) {
  var sheet = document.getElementById('mob-sheet');
  if (!sheet) return;
  sheet.innerHTML = '<div class="mob-sheet__sticky">' +
      '<div class="mob-sheet__title">' + esc(mobWatchModeTitle(mode)) + '</div>' +
      '<div class="mob-sheet__task-header">' +
        '<div class="task-title">' + esc(mobWatchRoute(watch || {})) + '</div>' +
        '<div class="task-meta" id="mob-watch-detail-summary"></div>' +
      '</div>' +
      '<div class="mob-sheet-tabs" id="mob-watch-detail-filters"></div>' +
    '</div>' +
    '<div class="mob-sheet__scroll-body" id="mob-watch-detail-body"><div class="mob-empty">加载中...</div></div>' +
    '<div class="mob-sheet__footer">' +
      '<div id="mob-watch-detail-pagination"></div>' +
      '<button class="mob-btn mob-btn-muted mob-btn-sm watch-touch-btn" style="align-self:flex-end;" id="mob-watch-detail-close">关闭</button>' +
    '</div>';
  document.getElementById('mob-watch-detail-close')?.addEventListener('click', closeSheet);
}

async function loadMobileWatchDetail(silent) {
  var detail = state.watchDetail;
  if (!detail || !detail.watchId) return;
  if (detail.mode === 'downloads') return loadMobileWatchDownloads(silent);
  if (detail.mode === 'deferred') return loadMobileWatchDeferred(detail.watchId, silent);
  return loadMobileWatchHistoryPage(silent);
}

function renderMobileWatchHistoryRange() {
  var summary = document.getElementById('mob-watch-detail-summary');
  var detail = state.watchDetail;
  if (!summary || !detail || detail.mode !== 'history') return;
  var watch = mobFindWatchById(detail.watchId);
  var today = Number(watch && watch.today_count || 0);
  var total = Number(watch && watch.event_count || 0);
  summary.innerHTML =
    '<div class="mob-watch-range" role="tablist" aria-label="' + esc(t('watches.historyTitle')) + '">' +
      '<button type="button" class="mob-sheet-tab' + (detail.todayOnly ? ' active' : '') + '" role="tab" aria-selected="' + (detail.todayOnly ? 'true' : 'false') + '" data-mob-watch-range="today">' +
        esc(t('watches.todayEvents')) + '<span class="count">' + today + '</span>' +
      '</button>' +
      '<button type="button" class="mob-sheet-tab' + (!detail.todayOnly ? ' active' : '') + '" role="tab" aria-selected="' + (!detail.todayOnly ? 'true' : 'false') + '" data-mob-watch-range="all">' +
        esc(t('watches.totalEvents')) + '<span class="count">' + total + '</span>' +
      '</button>' +
    '</div>';
  summary.querySelectorAll('[data-mob-watch-range]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var nextTodayOnly = btn.dataset.mobWatchRange === 'today';
      if (Boolean(state.watchDetail.todayOnly) === nextTodayOnly) return;
      state.watchDetail.todayOnly = nextTodayOnly;
      state.watchDetail.filter = 'all';
      state.watchDetail.page = 1;
      loadMobileWatchHistoryPage(false);
    });
  });
}

function renderMobileWatchHistoryFilters(statusCounts) {
  var filters = document.getElementById('mob-watch-detail-filters');
  var detail = state.watchDetail;
  if (!filters || !detail) return;
  var counts = statusCounts || {};
  var chips = [
    { key: 'all', label: t('watches.filterAll'), count: Number(counts.all || 0) },
    { key: 'success', label: t('watches.filterSuccess'), count: Number(counts.success || 0) },
    { key: 'filtered', label: t('watches.filterFiltered'), count: Number(counts.skipped || 0) },
    { key: 'failure', label: t('watches.filterFailure'), count: Number(counts.failure || 0) }
  ];
  filters.innerHTML = chips.map(function(chip) {
    return '<button type="button" class="mob-sheet-tab' + (detail.filter === chip.key ? ' active' : '') + '" data-mob-watch-filter="' + chip.key + '">' +
      esc(chip.label) + '<span class="count">' + chip.count + '</span>' +
    '</button>';
  }).join('');
  filters.querySelectorAll('[data-mob-watch-filter]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var nextFilter = btn.dataset.mobWatchFilter || 'all';
      if (state.watchDetail.filter === nextFilter) return;
      state.watchDetail.filter = nextFilter;
      state.watchDetail.page = 1;
      loadMobileWatchHistoryPage(false);
    });
  });
}

function renderMobileWatchHistoryList(items) {
  if (!items.length) return '<div class="mob-empty">' + esc(t('watches.noEvents')) + '</div>';
  return items.map(function(ev, idx) {
    var sum = mobSummarizeWatchEvent(ev);
    var badgeClass = sum.kind === 'success' ? 'completed' : (sum.kind === 'filtered' ? 'pending' : 'failure');
    var badgeText = sum.badgeKey ? t(sum.badgeKey) : (sum.titleKey ? t(sum.titleKey) : '');
    var title = (sum.title != null && sum.title !== '')
      ? sum.title
      : (sum.titleKey ? t(sum.titleKey) : '');
    var detailId = 'mob-watch-evt-detail-' + idx;
    var canExpand = Boolean(sum.detail);
    return '<div class="mob-event-row mob-watch-detail-row"' + (canExpand ? ' data-mob-expand-detail="' + detailId + '"' : '') + '>' +
      '<span class="mob-card__badge ' + badgeClass + '">' + esc(badgeText) + '</span>' +
      '<div class="mob-watch-detail-row-main">' +
        (title ? '<div style="font-weight:600;">' + esc(title) + '</div>' : '') +
        '<div class="text-xs text-muted">#' + esc(String(ev.source_message_id || '-')) + ' · ' + esc(fmtTime(ev.created_at)) + (canExpand ? ' · ' + esc(t('watches.detailExpandReason')) : '') + '</div>' +
        (canExpand ? '<div id="' + detailId + '" class="hidden text-xs text-muted mt-1" style="word-break:break-all;">' + esc(sum.detail) + '</div>' : '') +
      '</div>' +
    '</div>';
  }).join('');
}

function bindMobileWatchHistoryRows() {
  var body = document.getElementById('mob-watch-detail-body');
  if (!body) return;
  body.querySelectorAll('[data-mob-expand-detail]').forEach(function(row) {
    row.addEventListener('click', function() {
      var detail = document.getElementById(row.dataset.mobExpandDetail);
      if (detail) detail.classList.toggle('hidden');
    });
  });
}

async function loadMobileWatchHistoryPage(silent) {
  var detail = state.watchDetail || state.watchHistory;
  var body = document.getElementById('mob-watch-detail-body');
  var pagination = document.getElementById('mob-watch-detail-pagination');
  if (!detail || !detail.watchId || !body) return;
  var page = detail.page || 1;
  var pageSize = detail.pageSize || 20;
  var offset = (page - 1) * pageSize;
  if (!silent) body.innerHTML = '<div class="mob-empty">加载中...</div>';
  if (pagination) pagination.innerHTML = '';
  try {
    var status = mobWatchHistoryStatusQuery(detail.filter);
    var url = '/api/watches/' + encodeURIComponent(detail.watchId) + '/events?limit=' + pageSize + '&offset=' + offset;
    if (status) url += '&status=' + encodeURIComponent(status);
    if (detail.todayOnly) url += '&today=1';
    var data = await fetchJson(withClientTzQuery(url));
    var items = data.events || [];
    var total = Number(data.total || 0);
    var totalPages = Math.max(1, Math.ceil(total / pageSize));
    var statusCounts = data.status_counts || {
      all: total,
      success: 0,
      skipped: 0,
      failure: 0
    };
    detail.items = items;
    detail.total = total;
    detail.statusCounts = statusCounts;
    renderMobileWatchHistoryRange();
    renderMobileWatchHistoryFilters(statusCounts);
    body.innerHTML = renderMobileWatchHistoryList(items);
    bindMobileWatchHistoryRows();
    if (pagination) {
      pagination.innerHTML = renderPaginationBar({
        prefix: 'mob-watch-history',
        page: page,
        pageSize: pageSize,
        total: total,
        variant: 'mobile',
        pageInfoKey: 'watches.pageInfo'
      });
      bindPaginationBar('mob-watch-history', page, totalPages, function(newPage) {
        state.watchDetail.page = newPage;
        loadMobileWatchHistoryPage(false);
      });
    }
  } catch (e) {
    body.innerHTML = '<div class="mob-empty">加载失败</div>';
  }
}

function mobWatchDownloadBucket(status) {
  if (status === 'failure') return 'failed';
  if (status === 'success' || status === 'skipped') return 'completed';
  return 'active';
}

async function openMobileWatchDownloads(watchId) {
  return openMobileWatchDetail(watchId, 'downloads');
}

async function openMobileWatchHistory(watchId, page) {
  await openMobileWatchDetail(watchId, 'history');
  if (state.watchDetail && page && page > 1) {
    state.watchDetail.page = page;
    await loadMobileWatchHistoryPage(false);
  }
}

async function loadMobileWatchDownloads(silent) {
  var body = document.getElementById('mob-watch-detail-body');
  var summary = document.getElementById('mob-watch-detail-summary');
  var filters = document.getElementById('mob-watch-detail-filters');
  var pagination = document.getElementById('mob-watch-detail-pagination');
  if (!body || !mobWatchDownloadState.watchId || !state.watchDetail || state.watchDetail.mode !== 'downloads') return;
  if (filters) filters.innerHTML = '';
  if (pagination) pagination.innerHTML = '';
  if (!silent) body.innerHTML = '<div class="mob-empty">加载中...</div>';
  try {
    var data = await fetchJson('/api/watches/' + encodeURIComponent(mobWatchDownloadState.watchId) + '/download-tasks');
    var tasks = data.tasks || [];
    var groups = { active: [], completed: [], failed: [] };
    tasks.forEach(function(task) { groups[mobWatchDownloadBucket(task.status)].push(task); });
    var activeCount = data.counts && data.counts.active != null ? Number(data.counts.active) : groups.active.length;
    var completedCount = data.counts && data.counts.completed != null ? Number(data.counts.completed) : groups.completed.length;
    var failedCount = data.counts && data.counts.failed != null ? Number(data.counts.failed) : groups.failed.length;
    if (summary) summary.textContent = t('watches.downloadActive') + ' ' + activeCount + ' · ' + t('watches.downloadCompleted') + ' ' + completedCount + ' · ' + t('watches.downloadFailed') + ' ' + failedCount;
    body.innerHTML = renderMobileWatchDownloadSections(groups);
    bindMobileWatchDownloadActions(body);
  } catch (e) {
    if (!silent) body.innerHTML = '<div class="mob-empty">加载失败</div>';
  }
}

function renderMobileWatchDownloadSections(groups) {
  var sections = [
    { key: 'active', label: t('watches.downloadActive') },
    { key: 'completed', label: t('watches.downloadCompleted') },
    { key: 'failed', label: t('watches.downloadFailed') }
  ];
  var html = '';
  sections.forEach(function(section) {
    var items = groups[section.key] || [];
    html += '<div class="watch-download-section">' +
      '<div class="watch-download-section-title">' + esc(section.label) + ' (' + items.length + ')</div>';
    if (!items.length) {
      html += '<div class="mob-empty" style="padding:12px;">' + esc(t('watches.downloadRecordsEmpty')) + '</div>';
    } else {
      items.forEach(function(task) {
        var pct = typeof watchDownloadProgressPercent === 'function' ? watchDownloadProgressPercent(task) : (typeof taskProgressPercent === 'function' ? taskProgressPercent(task) : (task.progress_percent || 0));
        var title = typeof watchDownloadTitle === 'function' ? watchDownloadTitle(task) : ('#' + task.id);
        var route = mobWatchHelpers().formatWatchRoute ? mobWatchHelpers().formatWatchRoute(task.source_link || '-', task.target_profile || task.target_link || '-') : (task.source_link || '-') + ' → ' + (task.target_profile || task.target_link || '-');
        var fileDetail = typeof taskFileTransferDetail === 'function' ? taskFileTransferDetail(task) : '';
        html += '<div class="mob-event-row mob-watch-detail-row" data-task-id="' + task.id + '">' +
          '<span class="mob-card__badge ' + (task.status === 'success' ? 'completed' : task.status === 'failure' ? 'failure' : 'running') + '">' + esc(task.status || '-') + '</span>' +
          '<div class="mob-watch-detail-row-main">' +
            '<div style="font-weight:600;">' + esc(title) + ' <span class="text-muted">#' + esc(String(task.id)) + '</span></div>' +
            (fileDetail ? '<div class="text-xs" style="word-break:break-all;">' + esc(fileDetail) + '</div>' : '') +
            '<div class="text-xs text-muted" style="word-break:break-all;">' + esc(route) + '</div>' +
            '<div class="text-xs text-muted">' + pct + '% · ' + esc(taskCompletedLabel(task)) + '</div>' +
            (task.error_message ? '<div class="text-xs text-danger" style="word-break:break-word;margin-top:4px;">' + esc(task.error_message) + '</div>' : '') +
            ((task.can_retry || task.can_delete)
              ? '<div class="mob-watch-download-actions">' +
                  (task.can_retry
                    ? '<button type="button" class="mob-btn mob-btn-sm mob-btn-danger watch-touch-btn" data-mob-watch-download-retry="' + task.id + '">' + esc(t('tasks.retryFailed')) + '</button>'
                    : '') +
                  (task.can_delete
                    ? '<button type="button" class="mob-btn mob-btn-sm mob-btn-danger watch-touch-btn" data-mob-watch-download-delete="' + task.id + '">' + esc(t('tasks.delete')) + '</button>'
                    : '') +
                '</div>'
              : '') +
          '</div>' +
        '</div>';
      });
    }
    html += '</div>';
  });
  return html;
}

function bindMobileWatchDownloadActions(body) {
  body.querySelectorAll('[data-mob-watch-download-delete]').forEach(function(btn) {
    btn.addEventListener('click', async function(e) {
      e.stopPropagation();
      var taskId = parseInt(btn.dataset.mobWatchDownloadDelete, 10);
      if (!confirm('确定删除任务 #' + taskId + '？')) return;
      try {
        var resp = await fetch('/api/tasks/' + taskId, { method: 'DELETE' });
        if (!resp.ok) {
          var errData = {};
          try { errData = await resp.json(); } catch (err) {}
          alert(errData.detail || errData.error || errData.message || '删除失败');
          return;
        }
        await loadMobileWatchDownloads(true);
      } catch (err) {
        alert('删除失败');
      }
    });
  });
  body.querySelectorAll('[data-mob-watch-download-retry]').forEach(function(btn) {
    btn.addEventListener('click', async function(e) {
      e.stopPropagation();
      var taskId = parseInt(btn.dataset.mobWatchDownloadRetry, 10);
      try {
        var resp = await fetch('/api/tasks/' + taskId + '/retry-failed', { method: 'POST' });
        if (!resp.ok) {
          var errData = {};
          try { errData = await resp.json(); } catch (err) {}
          alert(errData.detail || errData.error || errData.message || '重试失败');
          return;
        }
        await loadMobileWatchDownloads(true);
      } catch (err) {
        alert('重试失败');
      }
    });
  });
}

function startMobWatchDownloadPolling() {
  stopMobWatchDownloadPolling();
  mobWatchDownloadPollTimer = setInterval(function() {
    var overlay = document.getElementById('mob-sheet-overlay');
    if (!overlay || !overlay.classList.contains('open') || !state.watchDetail || state.watchDetail.mode !== 'downloads') {
      stopMobWatchDownloadPolling();
      return;
    }
    loadMobileWatchDownloads(true);
  }, 3000);
}

function stopMobWatchDownloadPolling() {
  if (mobWatchDownloadPollTimer) {
    clearInterval(mobWatchDownloadPollTimer);
    mobWatchDownloadPollTimer = null;
  }
}

function mobileDeferredStatusLabel(status) {
  var map = {
    pending: 'watches.deferredPending',
    running: 'watches.deferredRunning',
    done: 'watches.deferredDone',
    cancelled: 'watches.deferredCancelled',
    failure: 'watches.deferredFailure'
  };
  return t(map[status] || 'watches.deferredPending');
}

function mobileDeferredStatusClass(status) {
  if (status === 'pending') return 'pending';
  if (status === 'running') return 'running';
  if (status === 'done') return 'completed';
  if (status === 'failure') return 'failure';
  return 'cancelled';
}

async function loadMobileWatchDeferred(watchId, silent) {
  var body = document.getElementById('mob-watch-detail-body');
  var summary = document.getElementById('mob-watch-detail-summary');
  var filters = document.getElementById('mob-watch-detail-filters');
  var pagination = document.getElementById('mob-watch-detail-pagination');
  if (!body) return;
  if (filters) filters.innerHTML = '';
  if (pagination) pagination.innerHTML = '';
  if (!silent) body.innerHTML = '<div class="mob-empty">加载中...</div>';
  try {
    var data = await fetchJson('/api/watches/' + encodeURIComponent(watchId) + '/deferred-comments');
    var items = data.captures || [];
    var counts = { pending: 0, running: 0, done: 0, cancelled: 0, failure: 0 };
    items.forEach(function(item) {
      if (counts[item.status] === undefined) counts[item.status] = 0;
      counts[item.status] += 1;
    });
    if (summary) summary.textContent = '全部 ' + items.length + ' · ' + t('watches.deferredPending') + ' ' + counts.pending + ' · ' + t('watches.deferredRunning') + ' ' + counts.running + ' · ' + t('watches.deferredFailure') + ' ' + counts.failure;
    if (!items.length) {
      body.innerHTML = '<div class="mob-empty">' + esc(t('watches.noDeferredComments')) + '</div>';
      return;
    }
    body.innerHTML = items.map(function(item) {
      var due = item.due_at ? new Date(Number(item.due_at) * 1000).toLocaleString() : '-';
      var actions = '';
      if (item.status === 'pending') {
        actions = '<button class="mob-btn mob-btn-sm watch-touch-btn" data-watch-id="' + esc(watchId) + '" data-deferred-run-now="' + esc(String(item.id)) + '">' + esc(t('watches.deferredRunNow')) + '</button>' +
          '<button class="mob-btn mob-btn-sm mob-btn-danger watch-touch-btn" data-watch-id="' + esc(watchId) + '" data-deferred-cancel="' + esc(String(item.id)) + '">' + esc(t('watches.deferredCancel')) + '</button>';
      } else if (item.status === 'running') {
        actions = '<button class="mob-btn mob-btn-sm mob-btn-danger watch-touch-btn" data-watch-id="' + esc(watchId) + '" data-deferred-cancel="' + esc(String(item.id)) + '">' + esc(t('watches.deferredCancel')) + '</button>';
      } else if (item.status === 'failure' || item.status === 'cancelled') {
        actions = '<button class="mob-btn mob-btn-sm watch-touch-btn" data-watch-id="' + esc(watchId) + '" data-deferred-retry="' + esc(String(item.id)) + '">' + esc(t('watches.deferredRetry')) + '</button>';
      }
      return '<div class="mob-event-row mob-watch-detail-row">' +
        '<span class="mob-card__badge ' + mobileDeferredStatusClass(item.status) + '">' + esc(mobileDeferredStatusLabel(item.status)) + '</span>' +
        '<div class="mob-watch-detail-row-main">' +
          '<div style="font-weight:600;">#' + esc(String(item.source_message_id || '-')) + '</div>' +
          '<div class="text-xs text-muted">' + esc(t('watches.deferredDue')) + ': ' + esc(due) + '</div>' +
          (actions ? '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;">' + actions + '</div>' : '') +
        '</div>' +
      '</div>';
    }).join('');
    bindMobileDeferredActions(body);
  } catch (e) {
    body.innerHTML = '<div class="mob-empty">加载失败</div>';
  }
}

function bindMobileDeferredActions(body) {
  body.querySelectorAll('[data-deferred-run-now]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); postMobileDeferredAction(btn.dataset.watchId, btn.dataset.deferredRunNow, 'run-now'); });
  });
  body.querySelectorAll('[data-deferred-cancel]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); postMobileDeferredAction(btn.dataset.watchId, btn.dataset.deferredCancel, 'cancel'); });
  });
  body.querySelectorAll('[data-deferred-retry]').forEach(function(btn) {
    btn.addEventListener('click', function(e) { e.stopPropagation(); postMobileDeferredAction(btn.dataset.watchId, btn.dataset.deferredRetry, 'retry'); });
  });
}

async function postMobileDeferredAction(watchId, captureId, action) {
  try {
    await postJson('/api/watches/' + encodeURIComponent(watchId) + '/deferred-comments/' + encodeURIComponent(captureId) + '/' + action, {});
    await loadMobileWatchDeferred(watchId, true);
    await loadMobileWatches();
    if (typeof loadWatches === 'function') loadWatches();
  } catch (e) {
    alert(t('form.requestFailed'));
  }
}

// ---------------------------------------------------------------------------
// Task detail sheet
// ---------------------------------------------------------------------------
var sheetState = { sheetType: '', taskId: null, items: [], events: [], summary: {}, currentTab: 'all', currentPage: 1, pageSize: 20 };

function sheetTabApiStatus(tab) {
  if (tab === 'all') return '';
  if (tab === 'active') return 'active';
  if (tab === 'failure') return 'failure';
  return tab;
}

function sheetTabCount(summary, tab) {
  summary = summary || {};
  if (tab === 'all') return summary.total || 0;
  if (tab === 'active') return (summary.running || 0) + (summary.pending || 0);
  if (tab === 'failure') return summary.failed || 0;
  return summary[tab] || 0;
}

function sheetTabLabel(tab) {
  if (tab === 'all') return '全部';
  if (tab === 'active') return '进行中';
  if (tab === 'success') return '成功';
  if (tab === 'failure') return '失败';
  return '跳过';
}

function sheetTabs(summary) {
  return [
    { key: 'all', label: '全部', count: sheetTabCount(summary, 'all') },
    { key: 'active', label: '进行中', count: sheetTabCount(summary, 'active') },
    { key: 'success', label: '成功', count: sheetTabCount(summary, 'success') },
    { key: 'failure', label: '失败', count: sheetTabCount(summary, 'failure') },
    { key: 'skipped', label: '跳过', count: sheetTabCount(summary, 'skipped') }
  ];
}

async function openTaskDetail(taskId) {
  sheetState = { sheetType: 'task-detail', taskId: taskId, items: [], events: [], summary: {}, currentTab: 'all', currentPage: 1, pageSize: 20 };
  var overlay = document.getElementById('mob-sheet-overlay');
  var sheet = document.getElementById('mob-sheet');
  if (!overlay || !sheet) return;
  sheet.className = 'mob-sheet mob-sheet--task-detail';
  sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-muted);">加载中...</div>';
  overlay.classList.add('open');

  try {
    var data = await fetchJson('/api/tasks/' + taskId + '/summary');
    sheetState.summary = data.summary || {};
    sheetState.events = data.recent_events || data.events || [];
    renderSheetContent(data);
    await loadSheetItemPage();
  } catch (e) {
    sheet.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-danger);">加载失败</div>';
  }
}

async function refreshOpenTaskSheet() {
  var overlay = document.getElementById('mob-sheet-overlay');
  if (!overlay || !overlay.classList.contains('open') || sheetState.sheetType !== 'task-detail' || !sheetState.taskId) return;
  try {
    var data = await fetchJson('/api/tasks/' + sheetState.taskId + '/summary');
    sheetState.summary = data.summary || sheetState.summary || {};
    sheetState.events = data.recent_events || data.events || sheetState.events || [];
    updateSheetContent(data);
    await loadSheetItemPage({ silent: true });
  } catch (e) {}
}

function renderSheetContent(data) {
  var sheet = document.getElementById('mob-sheet');
  if (!sheet) return;

  var task = data.task || {};
  var summary = data.summary || sheetState.summary || {};
  sheetState.summary = summary;

  var tabsHtml = '';
  sheetTabs(summary).forEach(function(tab) {
    tabsHtml += '<button class="mob-sheet-tab' + (sheetState.currentTab === tab.key ? ' active' : '') + '" data-sheet-tab="' + tab.key + '">' +
      tab.label + '<span class="count">' + tab.count + '</span></button>';
  });

  sheet.innerHTML =
    '<div class="mob-sheet__title">任务详情 #' + task.id + '</div>' +
    '<div class="mob-sheet__sticky">' +
      '<div class="mob-sheet__task-header" id="mob-sheet-task-header">' +
        '<div class="task-title">' + esc(task.title || task.source_link || '任务 #' + task.id) + '</div>' +
        '<div class="task-meta">状态: ' + esc(task.status || '-') + ' · 进度: ' + esc(taskCompletedLabel(task)) + '</div>' +
        (activeTransferSummary(task) ? '<div class="task-meta">' + esc(activeTransferSummary(task)) + '</div>' : '') +
      '</div>' +
      '<div class="mob-sheet-tabs" id="mob-sheet-item-tabs">' + tabsHtml + '</div>' +
    '</div>' +
    '<div class="mob-sheet__scroll-body" id="mob-sheet-item-list"></div>' +
    '<div class="mob-sheet__footer">' +
      '<div id="mob-sheet-item-pagination"></div>' +
      '<button class="mob-btn mob-btn-muted mob-btn-sm" style="align-self:flex-end;" id="mob-sheet-close">关闭</button>' +
    '</div>';

  bindSheetTabClicks();
  document.getElementById('mob-sheet-close').addEventListener('click', closeSheet);
}

function updateSheetContent(data) {
  var task = data.task || {};
  var summary = data.summary || sheetState.summary || {};
  sheetState.summary = summary;
  var header = document.getElementById('mob-sheet-task-header');
  if (header) {
    header.innerHTML =
      '<div class="task-title">' + esc(task.title || task.source_link || '任务 #' + task.id) + '</div>' +
      '<div class="task-meta">状态: ' + esc(task.status || '-') + ' · 进度: ' + esc(taskCompletedLabel(task)) + '</div>' +
      (activeTransferSummary(task) ? '<div class="task-meta">' + esc(activeTransferSummary(task)) + '</div>' : '');
  }
  document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab').forEach(function(tab) {
    var key = tab.dataset.sheetTab;
    tab.innerHTML = sheetTabLabel(key) + '<span class="count">' + sheetTabCount(summary, key) + '</span>';
  });
}

function closeSheet() {
  stopMobWatchDownloadPolling();
  mobWatchDownloadState = { watchId: null };
  var overlay = document.getElementById('mob-sheet-overlay');
  if (overlay) overlay.classList.remove('open');
  var sheet = document.getElementById('mob-sheet');
  if (sheet) sheet.className = 'mob-sheet';
  sheetState.sheetType = '';
}

function bindSheetTabClicks() {
  var tabs = document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab');
  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      tabs.forEach(function(t) { t.classList.remove('active'); });
      tab.classList.add('active');
      sheetState.currentTab = tab.dataset.sheetTab;
      sheetState.currentPage = 1;
      loadSheetItemPage();
    });
  });
}

async function loadSheetItemPage(options) {
  options = options || {};
  var silent = Boolean(options.silent);
  var container = document.getElementById('mob-sheet-item-list');
  var pagination = document.getElementById('mob-sheet-item-pagination');
  if (!container || !sheetState.taskId) return;

  if (!silent) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--color-muted);">加载中...</div>';
  }

  var status = sheetTabApiStatus(sheetState.currentTab);
  var offset = (sheetState.currentPage - 1) * sheetState.pageSize;
  var url = '/api/tasks/' + sheetState.taskId + '?items_limit=' + sheetState.pageSize + '&items_offset=' + offset;
  if (status) url += '&item_status=' + encodeURIComponent(status);

  try {
    var data = await fetchJson(url);
    sheetState.items = data.items || [];
    if (data.summary) sheetState.summary = data.summary;

    var totalItems = sheetTabCount(sheetState.summary, sheetState.currentTab);
    var meta = paginationMeta(totalItems, sheetState.pageSize, sheetState.currentPage);
    sheetState.currentPage = meta.page;
    var page = sheetState.items;

    if (page.length === 0) {
      container.innerHTML = '<div class="mob-empty">暂无数据</div>';
    } else {
      var html = '';
      page.forEach(function(item) {
        var summary = itemTransferSummary(item);
        var errorText = item.error_message || '';
        html += '<div class="mob-item-row">' +
          '<span class="mob-item-row__name">' + esc(item.file_name || item.message_id || '#' + item.id) +
            '<small class="mob-item-row__progress">' + esc(summary) + '</small>' +
            (errorText ? '<small class="mob-item-row__error">' + esc(errorText) + '</small>' : '') +
          '</span>' +
          '<span class="mob-card__badge ' + (item.status === 'success' ? 'completed' : item.status === 'failure' ? 'failure' : 'pending') + '">' + esc(item.status || '-') + '</span>' +
        '</div>';
      });
      container.innerHTML = html;
    }

    if (pagination) {
      pagination.innerHTML = renderPaginationBar({
        total: totalItems,
        pageSize: sheetState.pageSize,
        page: meta.page,
        prefix: 'mob-sheet-items',
        variant: 'mobile'
      });
      bindSheetItemPagination(meta.page, meta.totalPages);
    }

    if (!silent) container.scrollTop = 0;
  } catch (e) {
    if (!silent) {
      container.innerHTML = '<div class="mob-empty">加载失败</div>';
    }
  }
}

function bindSheetItemPagination(currentPage, totalPages) {
  document.getElementById('mob-sheet-items-prev')?.addEventListener('click', function() {
    sheetState.currentPage = Math.max(1, currentPage - 1);
    loadSheetItemPage();
  });
  document.getElementById('mob-sheet-items-next')?.addEventListener('click', function() {
    sheetState.currentPage = Math.min(totalPages, currentPage + 1);
    loadSheetItemPage();
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
    '<label style="margin-top:10px;"><span>下载后上传队列</span><input name="global.upload.pending_limit" type="number" min="1" max="5" value="' + (getSettingLeafKey(glob, 'upload.pending_limit') || '') + '"></label>' +
    '<label style="margin-top:10px;"><span>评论区延迟抓取（分钟）</span><input name="global.live_watch.comment_delay_minutes" type="number" min="0" max="1440" value="' + (getSettingLeafKey(glob, 'live_watch.comment_delay_minutes') ?? 20) + '"></label>' +
    '<p class="text-xs text-muted" style="margin-top:4px;">系统默认：任务未单独设置时生效。主贴立刻转发，评论区延迟后再抓一次。0=立刻。</p>' +
    '<h4 class="type-title" style="margin-top:16px;">深链取片</h4>' +
    '<label><span>资源 bot 白名单</span><textarea name="global.deep_link.bot_whitelist" rows="3" placeholder="每行一个，例如：&#10;123456">' + escAttr(Array.isArray(getSettingLeafKey(glob, 'deep_link.bot_whitelist')) ? getSettingLeafKey(glob, 'deep_link.bot_whitelist').join('\n') : (getSettingLeafKey(glob, 'deep_link.bot_whitelist') || '')) + '</textarea></label>' +
    '<p class="text-xs text-muted" style="margin-top:4px;">每行一个 bot 用户名（可带 @）。仅名单内的 t.me/&lt;bot&gt;?start= 会触发取片。</p>' +
    '<label style="margin-top:10px;"><span>取片超时（秒）</span><input name="global.deep_link.timeout_seconds" type="number" min="1" max="600" value="' + (getSettingLeafKey(glob, 'deep_link.timeout_seconds') ?? 60) + '"></label>' +
    '<label style="margin-top:10px;"><span>取片最小间隔（秒）</span><input name="global.deep_link.min_interval_seconds" type="number" min="0" max="600" value="' + (getSettingLeafKey(glob, 'deep_link.min_interval_seconds') ?? 30) + '"></label>' +
    '<label style="margin-top:10px;"><span>收齐静默（秒）</span><input name="global.deep_link.settle_seconds" type="number" min="0" max="60" value="' + (getSettingLeafKey(glob, 'deep_link.settle_seconds') ?? 3) + '"></label>' +
    '<label style="margin-top:10px;"><span>翻页最大页数</span><input name="global.deep_link.max_pages" type="number" min="1" max="100" value="' + (getSettingLeafKey(glob, 'deep_link.max_pages') ?? 20) + '"></label>' +
    '<label style="margin-top:10px;"><span>翻页点击间隔（秒）</span><input name="global.deep_link.page_click_interval_seconds" type="number" min="0" max="30" value="' + (getSettingLeafKey(glob, 'deep_link.page_click_interval_seconds') ?? 1) + '"></label>' +
    '<p class="text-xs text-muted" style="margin-top:4px;">首条媒体后再等该秒数无新消息则结束收齐；0 表示收到首条即结束。</p>' +
    '<p class="text-xs text-muted" style="margin-top:4px;">两次 StartBot 之间的最小冷却，降低限流。0=不主动冷却。</p>';

  // Archive
  var archiveFields = document.getElementById('mob-settings-archive-fields');
  if (archiveFields) {
    var arch = getSettingLeafKey(glob, 'target_profiles.pikpak.archive') || {};
    archiveFields.innerHTML =
      '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;">' +
        '<button type="button" class="mob-btn" id="settings-btn-setup-rclone">配置 rclone</button>' +
        '<button type="button" class="mob-btn mob-btn-muted" id="settings-btn-test-rclone">验证 remote</button>' +
        '<button type="button" class="mob-btn mob-btn-muted" id="settings-btn-relogin-telegram">重新登录 Telegram</button>' +
      '</div>' +
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
    if (typeof bindSetupWizardHandlers === 'function') bindSetupWizardHandlers();
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

  // Message filter + unified media type allowlist
  var mf = glob.message_filter || {};
  var mfFields = document.getElementById('mob-settings-message-filter-fields');
  if (mfFields) mfFields.innerHTML =
    '<div><span class="text-sm font-medium text-text-secondary">' + esc(t('settings.mediaTypes')) + '</span>' +
      '<span class="text-xs text-muted ml-1">' + esc(t('settings.mediaTypesHint')) + '</span>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;margin-top:4px;">' +
        renderCheckCards('global.message_filter.media_types', model.options.message_filter_media_types || MEDIA_TYPE_KEYS, selectedMediaTypes(glob), false) +
      '</div>' +
    '</div>' +
    '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;margin-top:10px;"><input type="checkbox" name="global.message_filter.enabled"' + (mf.enabled ? ' checked' : '') + '><span>' + esc(t('settings.enabled')) + '</span></label>' +
    '<p class="text-xs text-muted" style="margin:2px 0 8px;">' + esc(t('settings.filterEnabledHint')) + '</p>' +
    '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;margin-top:10px;"><input type="checkbox" name="global.message_filter.date_range.enabled"' + (getSettingLeafKey(mf, 'date_range.enabled') ? ' checked' : '') + '><span>' + esc(t('settings.dateRange')) + '</span></label>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' +
      '<label><span>' + esc(t('settings.startDate')) + '</span><input name="global.message_filter.date_range.start_date" type="datetime-local" value="' + escAttr(getSettingLeafKey(mf, 'date_range.start_date') || '') + '"></label>' +
      '<label><span>' + esc(t('settings.endDate')) + '</span><input name="global.message_filter.date_range.end_date" type="datetime-local" value="' + escAttr(getSettingLeafKey(mf, 'date_range.end_date') || '') + '"></label>' +
    '</div>' +
    '<label style="display:flex;flex-direction:row;align-items:center;gap:8px;margin-top:10px;"><input type="checkbox" name="global.message_filter.keywords.enabled"' + (getSettingLeafKey(mf, 'keywords.enabled') ? ' checked' : '') + '><span>' + esc(t('settings.keywords')) + '</span></label>' +
    '<label><span>' + esc(t('settings.keywordList')) + '</span><input name="global.message_filter.keywords.words" value="' + escAttr((Array.isArray(getSettingLeafKey(mf, 'keywords.words')) ? getSettingLeafKey(mf, 'keywords.words').join(',') : (getSettingLeafKey(mf, 'keywords.words') || '')) || '') + '" placeholder="' + escAttr(t('settings.keywordPlaceholder')) + '"></label>';

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
    html += '<label class="text-sm" style="display:flex;align-items:center;gap:6px;padding:4px 0;">' +
      '<input type="checkbox" name="' + (repeatName ? baseName : baseName + '.' + key) + '" value="' + escAttr(key) + '"' + (selSet[key] ? ' checked' : '') + '>' +
      '<span>' + esc(label || key) + '</span></label>';
  });
  return html || '<span class="text-sm text-muted">无可用选项</span>';
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
    html += '<label class="text-sm" style="display:flex;align-items:center;gap:6px;padding:3px 0;">' +
      '<input type="checkbox" name="download_types" value="' + escAttr(key) + '"' + (selSet[key] ? ' checked' : '') + '>' +
      '<span>' + esc(label || key) + '</span></label>';
  });
  grid.innerHTML = html || '<span class="text-sm text-muted">无可用类型</span>';
}

function mobEnsureOverrideMediaTypeGrids() {
  [
    'mob-transfer-media-types-grid',
    'mob-watch-media-types-grid'
  ].forEach(function(id) {
    var el = document.getElementById(id);
    if (!el || el.childElementCount) return;
    el.innerHTML = renderMediaTypesCheckboxHtml('override_media_types', defaultMediaTypesDict(true), { compact: true });
  });
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
const MOBILE_RECORDS_PAGE_SIZE = 50;

async function loadMobileRecords(page) {
  if (page !== undefined) state.recordsPage = page;
  var currentPage = state.recordsPage || 1;
  var container = document.getElementById('mob-records-list');
  var pagEl = document.getElementById('mob-records-pagination');
  var clearBtn = document.getElementById('mob-records-clear-btn');
  if (!container) return;
  try {
    var offset = (currentPage - 1) * MOBILE_RECORDS_PAGE_SIZE;
    var data = await fetchJson('/api/download-records?limit=' + MOBILE_RECORDS_PAGE_SIZE + '&offset=' + offset);
    var records = data && Array.isArray(data.records) ? data.records : [];
    var total = Number(data && data.total || 0);
    var totalPages = Math.max(1, Math.ceil(total / MOBILE_RECORDS_PAGE_SIZE) || 1);
    state.recordsTotal = total;

    if (currentPage > totalPages && total > 0) {
      state.recordsPage = totalPages;
      return loadMobileRecords(totalPages);
    }

    if (clearBtn) clearBtn.disabled = total === 0;

    if (!records.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="records.empty">还没有下载成功记录。</div>';
      if (pagEl) pagEl.innerHTML = '';
      return;
    }
    var html = '';
    records.forEach(function(r) {
      html += '<div class="mob-card">' +
        '<div class="mob-card__row"><span class="label">频道</span><span>' + esc(r.source_chat_id || r.chat_id || r.chat_title || '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">消息</span><span>' + esc(r.source_message_id || r.message_id || '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">文件</span><span>' + esc(r.file_name || r.file_path || '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">大小</span><span>' + (r.file_size ? formatBytes(r.file_size) : '-') + '</span></div>' +
        '<div class="mob-card__row"><span class="label">时间</span><span>' + esc(r.updated_at || '') + '</span></div>' +
      '</div>';
    });
    container.innerHTML = html;
    if (pagEl) {
      pagEl.innerHTML = renderPaginationBar({
        prefix: 'mob-records',
        page: currentPage,
        pageSize: MOBILE_RECORDS_PAGE_SIZE,
        total: total,
        variant: 'mobile'
      });
      bindPaginationBar('mob-records', currentPage, totalPages, function(newPage) {
        loadMobileRecords(newPage);
      });
    }
  } catch (e) {
    container.innerHTML = '<div class="mob-empty">加载失败</div>';
    if (pagEl) pagEl.innerHTML = '';
  }
}

document.getElementById('mob-records-clear-btn')?.addEventListener('click', async function() {
  if (!confirm(t('records.confirmClear'))) return;
  try {
    var resp = await fetch('/api/download-records', { method: 'DELETE' });
    if (resp.status === 401) { redirectToLoginPage(); return; }
    if (!resp.ok) {
      var data = {};
      try { data = await resp.json(); } catch (e) {}
      throw data;
    }
    state.recordsPage = 1;
    await loadMobileRecords();
  } catch (e) {
    alert(translateApiError(e, 'form.requestFailed'));
  }
});

// ---------------------------------------------------------------------------
// System Logs (profile subpage)
// ---------------------------------------------------------------------------
var MOBILE_SYSTEM_LOGS_PAGE_SIZE = 50;
var MOBILE_SYSTEM_LOGS_AUTO_REFRESH_KEY = 'trmd-system-logs-auto-refresh';
var MOBILE_SYSTEM_LOGS_CATEGORY_KEY = 'trmd-system-logs-category';
var MOBILE_SYSTEM_LOGS_LEVEL_KEY = 'trmd-system-logs-level';
var MOBILE_SYSTEM_LOGS_TODAY_KEY = 'trmd-system-logs-today';
var MOBILE_SYSTEM_LOGS_CATEGORY_VALUES = ['', 'watch', 'filter', 'forward', 'transfer', 'archive'];
var MOBILE_SYSTEM_LOGS_LEVEL_VALUES = ['', 'info', 'warning', 'error'];
var MOBILE_SYSTEM_LOGS_AUTO_REFRESH_MS = 5000;
var mobileSystemLogsAutoRefreshTimer = null;

function mobSystemLogLevelClass(level) {
  var value = String(level || 'info').toLowerCase();
  if (value === 'error') return 'system-log-level-error';
  if (value === 'warning') return 'system-log-level-warning';
  return 'system-log-level-info';
}

function mobSystemLogCategoryLabel(category) {
  var key = {
    watch: 'systemLogs.categoryWatch',
    filter: 'systemLogs.categoryFilter',
    forward: 'systemLogs.categoryForward',
    transfer: 'systemLogs.categoryTransfer',
    archive: 'systemLogs.categoryArchive'
  }[category];
  return key ? t(key) : (category || '-');
}

function isMobileSystemLogsAutoRefreshEnabled() {
  return localStorage.getItem(MOBILE_SYSTEM_LOGS_AUTO_REFRESH_KEY) === '1';
}

function setMobileSystemLogsAutoRefreshEnabled(enabled) {
  localStorage.setItem(MOBILE_SYSTEM_LOGS_AUTO_REFRESH_KEY, enabled ? '1' : '0');
}

function getMobileSystemLogsCategory() {
  var value = localStorage.getItem(MOBILE_SYSTEM_LOGS_CATEGORY_KEY);
  if (value == null) return '';
  return MOBILE_SYSTEM_LOGS_CATEGORY_VALUES.indexOf(value) >= 0 ? value : '';
}

function setMobileSystemLogsCategory(value) {
  var next = MOBILE_SYSTEM_LOGS_CATEGORY_VALUES.indexOf(value) >= 0 ? value : '';
  localStorage.setItem(MOBILE_SYSTEM_LOGS_CATEGORY_KEY, next);
}

function getMobileSystemLogsLevel() {
  var value = localStorage.getItem(MOBILE_SYSTEM_LOGS_LEVEL_KEY);
  if (value == null) return '';
  return MOBILE_SYSTEM_LOGS_LEVEL_VALUES.indexOf(value) >= 0 ? value : '';
}

function setMobileSystemLogsLevel(value) {
  var next = MOBILE_SYSTEM_LOGS_LEVEL_VALUES.indexOf(value) >= 0 ? value : '';
  localStorage.setItem(MOBILE_SYSTEM_LOGS_LEVEL_KEY, next);
}

function isMobileSystemLogsTodayOnlyEnabled() {
  return localStorage.getItem(MOBILE_SYSTEM_LOGS_TODAY_KEY) === '1';
}

function setMobileSystemLogsTodayOnlyEnabled(enabled) {
  localStorage.setItem(MOBILE_SYSTEM_LOGS_TODAY_KEY, enabled ? '1' : '0');
}

function syncMobileSystemLogsFiltersUI() {
  var category = document.getElementById('mob-system-logs-category');
  if (category) category.value = getMobileSystemLogsCategory();
  var level = document.getElementById('mob-system-logs-level');
  if (level) level.value = getMobileSystemLogsLevel();
  var today = document.getElementById('mob-system-logs-today');
  if (today) today.checked = isMobileSystemLogsTodayOnlyEnabled();
  syncMobileSystemLogsAutoRefreshUI();
}

function stopMobileSystemLogsAutoRefresh() {
  if (mobileSystemLogsAutoRefreshTimer) {
    clearInterval(mobileSystemLogsAutoRefreshTimer);
    mobileSystemLogsAutoRefreshTimer = null;
  }
}

function startMobileSystemLogsAutoRefresh() {
  stopMobileSystemLogsAutoRefresh();
  if (!isMobileSystemLogsAutoRefreshEnabled()) return;
  if (currentProfileSub !== 'system-logs') return;
  mobileSystemLogsAutoRefreshTimer = setInterval(function() {
    if (currentProfileSub !== 'system-logs') {
      stopMobileSystemLogsAutoRefresh();
      return;
    }
    loadMobileSystemLogs(1);
  }, MOBILE_SYSTEM_LOGS_AUTO_REFRESH_MS);
}

function syncMobileSystemLogsAutoRefreshUI() {
  var checkbox = document.getElementById('mob-system-logs-auto-refresh');
  if (checkbox) checkbox.checked = isMobileSystemLogsAutoRefreshEnabled();
}

function formatMobileSystemLogDetails(entry) {
  if (entry.details == null || entry.details === '') return '';
  try {
    var parsed = typeof entry.details === 'string' ? JSON.parse(entry.details) : entry.details;
    return typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2);
  } catch (e) {
    return String(entry.details);
  }
}

function formatMobileSystemLogContext(entry) {
  var parts = [];
  if (entry.trace_id) parts.push(t('systemLogs.trace') + ': ' + entry.trace_id);
  if (entry.watch_id) parts.push(t('systemLogs.watch') + ': ' + entry.watch_id);
  if (entry.source_chat_id) parts.push('chat: ' + entry.source_chat_id);
  if (entry.source_message_id) parts.push('msg: ' + entry.source_message_id);
  if (entry.target_link) parts.push('target: ' + entry.target_link);
  if (entry.details) {
    try {
      var parsed = typeof entry.details === 'string' ? JSON.parse(entry.details) : entry.details;
      parts.push(JSON.stringify(parsed));
    } catch (e) {
      parts.push(String(entry.details));
    }
  }
  return parts.join(' · ');
}

function formatMobileSystemLogCopyLine(entry) {
  var time = entry.created_at ? new Date(entry.created_at).toISOString() : '-';
  var context = formatMobileSystemLogContext(entry);
  return '[' + time + '] [' + (entry.level || 'info').toUpperCase() + '] '
    + '[' + (entry.category || '-') + '/' + (entry.stage || '-') + '] '
    + (entry.message || '') + (context ? ' | ' + context : '');
}

function mobileSystemLogsFilterQuery() {
  var category = document.getElementById('mob-system-logs-category');
  var level = document.getElementById('mob-system-logs-level');
  var today = document.getElementById('mob-system-logs-today');
  var categoryVal = category ? category.value : '';
  var levelVal = level ? level.value : '';
  var todayOnly = today && today.checked ? '1' : '0';
  return '?today=' + todayOnly
    + (categoryVal ? '&category=' + encodeURIComponent(categoryVal) : '')
    + (levelVal ? '&level=' + encodeURIComponent(levelVal) : '');
}

function renderMobileSystemLogDetailRow(label, valueHtml, mono) {
  return '<div class="system-log-detail-row">' +
    '<div class="system-log-detail-label">' + esc(label) + '</div>' +
    '<div class="system-log-detail-value' + (mono ? ' font-mono' : '') + '">' + valueHtml + '</div>' +
  '</div>';
}

function openMobileSystemLogDetail(entry) {
  var overlay = document.getElementById('mob-sheet-overlay');
  var sheet = document.getElementById('mob-sheet');
  if (!overlay || !sheet || !entry) return;
  sheetState.sheetType = 'system-log-detail';
  var timeText = entry.created_at ? new Date(entry.created_at).toLocaleString() : '-';
  var detailsText = formatMobileSystemLogDetails(entry);
  var html = '<div class="mob-sheet__title">' + esc(t('systemLogs.detailTitle')) + '</div>' +
    '<div class="mob-system-log-detail">' +
      renderMobileSystemLogDetailRow(t('systemLogs.time'), esc(timeText)) +
      renderMobileSystemLogDetailRow(
        t('systemLogs.level'),
        '<span class="system-log-level ' + mobSystemLogLevelClass(entry.level) + '">' +
          esc((entry.level || 'info').toUpperCase()) + '</span>'
      ) +
      renderMobileSystemLogDetailRow(t('systemLogs.category'), esc(mobSystemLogCategoryLabel(entry.category))) +
      renderMobileSystemLogDetailRow(t('systemLogs.stage'), esc(entry.stage || '-'), true) +
      renderMobileSystemLogDetailRow(t('systemLogs.message'), esc(entry.message || '-'));
  if (entry.trace_id) {
    html += renderMobileSystemLogDetailRow(t('systemLogs.trace'), esc(entry.trace_id), true);
  }
  if (entry.watch_id) {
    html += renderMobileSystemLogDetailRow(t('systemLogs.watch'), esc(entry.watch_id), true);
  }
  if (entry.source_chat_id) {
    html += renderMobileSystemLogDetailRow(t('systemLogs.sourceChat'), esc(String(entry.source_chat_id)), true);
  }
  if (entry.source_message_id != null && entry.source_message_id !== '') {
    html += renderMobileSystemLogDetailRow(t('systemLogs.sourceMessage'), esc(String(entry.source_message_id)), true);
  }
  if (entry.target_link) {
    html += renderMobileSystemLogDetailRow(t('systemLogs.target'), esc(entry.target_link), true);
  }
  if (detailsText) {
    html += renderMobileSystemLogDetailRow(
      t('systemLogs.details'),
      '<pre class="system-log-detail-json">' + esc(detailsText) + '</pre>'
    );
  }
  html += '</div>' +
    '<div class="mob-sheet__footer">' +
      '<button type="button" class="mob-btn mob-btn-muted" id="mob-system-log-detail-close">' + esc(t('action.cancel')) + '</button>' +
    '</div>';
  sheet.className = 'mob-sheet mob-sheet--system-log';
  sheet.innerHTML = html;
  var closeBtn = document.getElementById('mob-system-log-detail-close');
  if (closeBtn) closeBtn.addEventListener('click', closeSheet);
  overlay.classList.add('open');
}

async function loadMobileSystemLogs(page) {
  if (page !== undefined) state.systemLogsPage = page;
  var currentPage = state.systemLogsPage || 1;
  var container = document.getElementById('mob-system-logs-list');
  var pagEl = document.getElementById('mob-system-logs-pagination');
  var retentionEl = document.getElementById('mob-system-logs-retention');
  if (!container) return;
  syncMobileSystemLogsAutoRefreshUI();
  var category = document.getElementById('mob-system-logs-category');
  var level = document.getElementById('mob-system-logs-level');
  var today = document.getElementById('mob-system-logs-today');
  var categoryVal = category ? category.value : '';
  var levelVal = level ? level.value : '';
  var todayOnly = today && today.checked ? '1' : '0';
  try {
    var offset = (currentPage - 1) * MOBILE_SYSTEM_LOGS_PAGE_SIZE;
    var query = '/api/system-logs?limit=' + MOBILE_SYSTEM_LOGS_PAGE_SIZE + '&offset=' + offset
      + '&today=' + todayOnly
      + (categoryVal ? '&category=' + encodeURIComponent(categoryVal) : '')
      + (levelVal ? '&level=' + encodeURIComponent(levelVal) : '');
    var data = await fetchJson(withClientTzQuery(query));
    var logs = data.logs || [];
    var total = Number(data.total || 0);
    state.systemLogs = logs;
    state.systemLogsTotal = total;
    if (retentionEl) {
      retentionEl.textContent = t('systemLogs.retentionHint').replace('{days}', data.retention_days || 2);
    }
    var totalPages = Math.max(1, Math.ceil(total / MOBILE_SYSTEM_LOGS_PAGE_SIZE) || 1);
    if (currentPage > totalPages && total > 0) {
      state.systemLogsPage = totalPages;
      return loadMobileSystemLogs(totalPages);
    }
    if (!logs.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="systemLogs.empty">' + esc(t('systemLogs.empty')) + '</div>';
      if (pagEl) pagEl.innerHTML = '';
      return;
    }
    var html = '';
    logs.forEach(function(entry) {
      var timeText = entry.created_at ? new Date(entry.created_at).toLocaleString() : '-';
      var context = formatMobileSystemLogContext(entry);
      var summary = [entry.stage || '-', context].filter(Boolean).join(' · ');
      html += '<button type="button" class="mob-card mob-system-log-card" data-log-id="' + esc(String(entry.id || '')) + '">' +
        '<div class="mob-card__head">' +
          '<span class="system-log-level ' + mobSystemLogLevelClass(entry.level) + '">' +
            esc((entry.level || 'info').toUpperCase()) +
          '</span>' +
          '<span class="mob-system-log-card__category">' + esc(mobSystemLogCategoryLabel(entry.category)) + '</span>' +
          '<span class="mob-system-log-card__time">' + esc(timeText) + '</span>' +
        '</div>' +
        '<div class="mob-system-log-card__message">' + esc(entry.message || '-') + '</div>' +
        (summary ? '<div class="mob-system-log-card__meta">' + esc(summary) + '</div>' : '') +
      '</button>';
    });
    container.innerHTML = html;
    container.querySelectorAll('.mob-system-log-card').forEach(function(card) {
      card.addEventListener('click', function() {
        var logId = card.dataset.logId;
        var entry = (state.systemLogs || []).find(function(item) {
          return String(item.id) === String(logId);
        });
        if (entry) openMobileSystemLogDetail(entry);
      });
    });
    if (pagEl) {
      pagEl.innerHTML = renderPaginationBar({
        prefix: 'mob-system-logs',
        page: currentPage,
        pageSize: MOBILE_SYSTEM_LOGS_PAGE_SIZE,
        total: total,
        variant: 'mobile'
      });
      bindPaginationBar('mob-system-logs', currentPage, totalPages, async function(newPage) {
        state.systemLogsPage = newPage;
        await loadMobileSystemLogs(newPage);
        var list = document.getElementById('mob-system-logs-list');
        var subpage = document.getElementById('mob-subpage-system-logs');
        scrollPaginationContentToTop(list || subpage);
      });
    }
  } catch (e) {
    if (e && e.error_code === 'auth_required') {
      redirectToLoginPage();
      return;
    }
    container.innerHTML = '<div class="mob-empty">加载失败</div>';
    if (pagEl) pagEl.innerHTML = '';
  }
}

function copyMobileSystemLogsPage() {
  var logs = state.systemLogs || [];
  if (!logs.length) return;
  var text = logs.map(formatMobileSystemLogCopyLine).join('\n');
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function() {
      showToast(t('systemLogs.copied'));
    }).catch(function() {
      prompt(t('systemLogs.copyPage'), text);
    });
  } else {
    prompt(t('systemLogs.copyPage'), text);
  }
}

async function downloadMobileSystemLogsAll() {
  var btn = document.getElementById('mob-system-logs-download-btn');
  if (btn && btn.disabled) return;
  var originalLabel = btn ? btn.textContent : '';
  if (btn) {
    btn.disabled = true;
    btn.textContent = t('systemLogs.downloading');
  }
  try {
    var query = withClientTzQuery('/api/system-logs/export' + mobileSystemLogsFilterQuery());
    var resp = await fetch(query, { credentials: 'same-origin' });
    if (resp.status === 401) {
      redirectToLoginPage();
      return;
    }
    if (!resp.ok) throw new Error('download_failed');
    var text = await resp.text();
    if (!text.trim()) {
      showToast(t('systemLogs.downloadEmpty'));
      return;
    }
    var disposition = resp.headers.get('content-disposition') || '';
    var match = disposition.match(/filename=\"([^\"]+)\"/);
    var filename = match ? match[1] : ('system-logs-' + Date.now() + '.txt');
    var blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    if (e && e.error_code === 'auth_required') redirectToLoginPage();
    else showToast(t('systemLogs.downloadFailed'));
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalLabel || t('systemLogs.downloadAll');
    }
  }
}

function bindMobileSystemLogsControls() {
  var refreshBtn = document.getElementById('mob-system-logs-refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', function() { loadMobileSystemLogs(1); });
  }
  var copyBtn = document.getElementById('mob-system-logs-copy-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', copyMobileSystemLogsPage);
  }
  var downloadBtn = document.getElementById('mob-system-logs-download-btn');
  if (downloadBtn) {
    downloadBtn.addEventListener('click', downloadMobileSystemLogsAll);
  }
  var category = document.getElementById('mob-system-logs-category');
  if (category) {
    category.addEventListener('change', function() {
      setMobileSystemLogsCategory(this.value || '');
      state.systemLogsPage = 1;
      loadMobileSystemLogs(1);
    });
  }
  var level = document.getElementById('mob-system-logs-level');
  if (level) {
    level.addEventListener('change', function() {
      setMobileSystemLogsLevel(this.value || '');
      state.systemLogsPage = 1;
      loadMobileSystemLogs(1);
    });
  }
  var today = document.getElementById('mob-system-logs-today');
  if (today) {
    today.addEventListener('change', function() {
      setMobileSystemLogsTodayOnlyEnabled(this.checked);
      state.systemLogsPage = 1;
      loadMobileSystemLogs(1);
    });
  }
  var autoRefresh = document.getElementById('mob-system-logs-auto-refresh');
  if (autoRefresh) {
    autoRefresh.addEventListener('change', function() {
      setMobileSystemLogsAutoRefreshEnabled(this.checked);
      if (this.checked) startMobileSystemLogsAutoRefresh();
      else stopMobileSystemLogsAutoRefresh();
    });
  }
  syncMobileSystemLogsFiltersUI();
}

// ---------------------------------------------------------------------------
// Statistics
// ---------------------------------------------------------------------------
async function loadMobileStatistics() {
  var container = document.getElementById('mob-statistics-list');
  if (!container) return;
  try {
    var data = await fetchJson(withClientTzQuery('/api/statistics'));
    var tables = data && data.tables ? data.tables : null;
    var summary = data && data.summary ? data.summary : {};
    if (!tables) {
      container.innerHTML = '<div class="mob-empty">暂无统计数据</div>';
      return;
    }
    var channelTable = tables.channel || {};
    var html = '';
    html += '<div class="mob-card">' +
      '<div class="mob-card__head"><span class="mob-card__title">近 7 天概览</span></div>' +
      '<div class="mob-card__row"><span class="label">频道数</span><span>' + (summary.channels || 0) + '</span></div>' +
      '<div class="mob-card__row"><span class="label">条目总数</span><span>' + (summary.downloads_total || 0) + '</span></div>' +
      '<div class="mob-card__row"><span class="label">成功率</span><span>' + (summary.success_rate || 0) + '%</span></div>' +
      '<div class="mob-card__row"><span class="label">失败 / 跳过</span><span>' +
        (summary.failure_count || 0) + ' / ' + (summary.skip_count || 0) + '</span></div>' +
    '</div>';
    html += '<div class="mob-card">' +
      '<div class="mob-card__head"><span class="mob-card__title">按频道</span></div>' +
      '<div class="mob-card__row"><span class="label">行数</span><span>' + (channelTable.rows || 0) + '</span></div>' +
      '<div class="mob-card__row"><span class="label">可用</span><span>' + (channelTable.available ? '是' : '否') + '</span></div>' +
      (channelTable.available
        ? '<button class="mob-btn mob-btn--primary" type="button" data-export="channel">导出</button>'
        : '') +
    '</div>';
    container.innerHTML = html;
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

    var html = '<div class="text-sm">' +
      '<div style="display:flex;gap:16px;flex-wrap:wrap;padding:12px;background:var(--color-surface-muted);border-radius:8px;margin-bottom:12px;">' +
        '<div><strong>总文件</strong><br>' + (data.total_count || 0) + '</div>' +
        '<div><strong>总大小</strong><br>' + formatBytes(data.total_size || 0) + '</div>' +
        '<div><strong>遗留文件</strong><br>' + orphanFiles.length + ' 个</div>' +
      '</div></div>';

    if (transferItems.length > 0) {
      html += '<div style="margin-top:12px;"><strong class="type-title">转存任务文件</strong></div>';
      transferItems.forEach(function(item) {
        html += '<div class="text-xs" style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--color-line);">' +
          '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc(item.file_name || item.local_path || '') + '</span>' +
          '<span style="flex-shrink:0;margin-left:8px;">' + formatBytes(item.file_size || 0) + '</span>' +
        '</div>';
      });
    }

    if (orphanFiles.length > 0) {
      html += '<div style="margin-top:12px;"><strong class="type-title">遗留文件</strong></div>';
      orphanFiles.forEach(function(f) {
        html += '<div class="text-xs" style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--color-line);">' +
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

var mobArchiveOrganizePlan = null;
var mobArchiveOrganizeJobId = null;
var mobArchiveOrganizeBucket = 'executable';
var MOB_ARCHIVE_PAGE_SIZE = 30;

function mobArchiveExecutableCount(data) {
  if (!data) return 0;
  if (data.executable_count != null) return Number(data.executable_count) || 0;
  var summary = data.summary || {};
  if (summary.executable != null) return Number(summary.executable) || 0;
  return (Number(data.move_count) || 0) + (Number(data.confirm_count) || 0);
}
var MOB_ARCHIVE_AUTHOR_JOB_KEY = 'trmd-archive-author-job';

function saveMobArchiveOrganizeJob(job) {
  try {
    if (!job || !job.id) {
      localStorage.removeItem(MOB_ARCHIVE_AUTHOR_JOB_KEY);
      return;
    }
    localStorage.setItem(MOB_ARCHIVE_AUTHOR_JOB_KEY, JSON.stringify({
      id: job.id,
      channel_folder: job.channel_folder || '',
      kind: job.kind || ''
    }));
  } catch (e) {}
}

function loadSavedMobArchiveOrganizeJob() {
  try {
    var raw = localStorage.getItem(MOB_ARCHIVE_AUTHOR_JOB_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

function clearSavedMobArchiveOrganizeJob() {
  try { localStorage.removeItem(MOB_ARCHIVE_AUTHOR_JOB_KEY); } catch (e) {}
}

function showMobArchiveOrganizeProgress(job) {
  var box = document.getElementById('mob-archive-organize-progress');
  var message = document.getElementById('mob-archive-organize-progress-message');
  var pctEl = document.getElementById('mob-archive-organize-progress-pct');
  var fill = document.getElementById('mob-archive-organize-progress-fill');
  var count = document.getElementById('mob-archive-organize-progress-count');
  if (!box) return;
  box.classList.remove('hidden');
  box.hidden = false;
  box.style.display = 'block';
  var percent = Math.max(0, Math.min(100, Number(job && job.percent || 0)));
  var current = Number(job && job.current || 0);
  var total = Number(job && job.total || 0);
  if (message) message.textContent = (job && job.message) || t('archiveOrganize.progress');
  if (pctEl) pctEl.textContent = percent + '%';
  if (fill) fill.style.width = percent + '%';
  if (count) {
    count.textContent = total > 0
      ? (current + ' / ' + total)
      : (job && job.phase === 'listing' ? t('archiveOrganize.scanning') : '-');
  }
}

function setMobArchiveOrganizeBusy(busy, labelKey) {
  var scanBtn = document.getElementById('mob-archive-organize-scan-btn');
  var resolveBtn = document.getElementById('mob-archive-organize-resolve-btn');
  var resolveUnresolvedBtn = document.getElementById('mob-archive-organize-resolve-unresolved-btn');
  var runBtn = document.getElementById('mob-archive-organize-run-btn');
  var runReviewBtn = document.getElementById('mob-archive-organize-run-review-btn');
  if (scanBtn) {
    scanBtn.disabled = !!busy;
    scanBtn.textContent = busy && labelKey === 'scan'
      ? t('archiveOrganize.scanning')
      : t('archiveOrganize.scan');
  }
  if (resolveBtn) {
    resolveBtn.disabled = !!busy;
    resolveBtn.textContent = busy && labelKey === 'resolve'
      ? t('archiveOrganize.resolving')
      : t('archiveOrganize.resolve');
  }
  if (resolveUnresolvedBtn) {
    resolveUnresolvedBtn.disabled = !!busy;
    resolveUnresolvedBtn.textContent = busy && labelKey === 'resolveUnresolved'
      ? t('archiveOrganize.resolvingUnresolved')
      : t('archiveOrganize.resolveUnresolved');
  }
  if (runBtn) {
    if (busy && labelKey === 'run') {
      runBtn.disabled = true;
      runBtn.textContent = t('archiveOrganize.running');
    } else if (!busy) {
      runBtn.textContent = t('archiveOrganize.runAll');
      runBtn.disabled = !(mobArchiveExecutableCount(mobArchiveOrganizePlan) > 0);
    } else {
      runBtn.disabled = true;
    }
  }
  if (runReviewBtn) {
    if (busy && (labelKey === 'run' || labelKey === 'runReview')) {
      runReviewBtn.disabled = true;
      runReviewBtn.textContent = t('archiveOrganize.running');
    } else if (!busy) {
      runReviewBtn.textContent = t('archiveOrganize.runReview');
      var reviewCount = 0;
      if (typeof mobArchiveReviewCount === 'function') {
        reviewCount = mobArchiveReviewCount(mobArchiveOrganizePlan);
      } else if (mobArchiveOrganizePlan) {
        reviewCount = Number(mobArchiveOrganizePlan.review_count || 0);
      }
      runReviewBtn.disabled = !(reviewCount > 0);
    } else {
      runReviewBtn.disabled = true;
    }
  }
  setMobArchiveOrganizeStopVisible(!!(busy && (labelKey === 'run' || labelKey === 'runReview')));
}

function sleepMs(ms) {
  return new Promise(function(resolve) { setTimeout(resolve, ms); });
}

async function fetchActiveMobArchiveOrganizeJob(channel) {
  var lastError = null;
  var globalJob = null;
  // Prefer any live running job first so desktop-started tasks appear on mobile
  // even when the channel select has not yet matched the running folder.
  try {
    globalJob = await fetchJson('/api/archive/author-job?active=1');
    if (globalJob && globalJob.id && globalJob.status === 'running') {
      return globalJob;
    }
  } catch (e) {
    lastError = e;
    globalJob = null;
  }
  var folder = String(channel || '').trim();
  if (folder) {
    try {
      var scoped = await fetchJson(
        '/api/archive/author-job?active=1&channel_folder=' + encodeURIComponent(folder)
      );
      if (scoped && scoped.id) return scoped;
    } catch (e) {
      lastError = e;
    }
  }
  if (globalJob && globalJob.id) return globalJob;
  if (lastError) throw lastError;
  return null;
}

async function pollMobArchiveOrganizeJob(jobId) {
  while (true) {
    var job = await fetchJson('/api/archive/author-job?id=' + encodeURIComponent(jobId));
    showMobArchiveOrganizeProgress(job);
    saveMobArchiveOrganizeJob(job);
    if (job.status === 'success' || job.status === 'failure' || job.status === 'stopped') return job;
    await sleepMs(2000);
  }
}

function setMobArchiveOrganizeStopVisible(visible) {
  var stopBtn = document.getElementById('mob-archive-organize-stop-btn');
  if (!stopBtn) return;
  if (visible) {
    stopBtn.classList.remove('hidden');
    stopBtn.hidden = false;
    stopBtn.style.display = '';
    stopBtn.disabled = false;
    stopBtn.textContent = t('archiveOrganize.stop');
  } else {
    stopBtn.classList.add('hidden');
    stopBtn.disabled = true;
  }
}

async function stopArchiveOrganizeMobile() {
  var jobId = mobArchiveOrganizeJobId;
  if (!jobId) {
    var saved = loadSavedMobArchiveOrganizeJob();
    if (saved && saved.id) jobId = saved.id;
  }
  if (!jobId) return;
  var stopBtn = document.getElementById('mob-archive-organize-stop-btn');
  if (stopBtn) {
    stopBtn.disabled = true;
    stopBtn.textContent = t('archiveOrganize.stopping');
  }
  try {
    await postJson('/api/archive/author-job/stop', { id: jobId });
  } catch (e) {
    showToast(translateApiError(e, 'form.requestFailed'));
    if (stopBtn) {
      stopBtn.disabled = false;
      stopBtn.textContent = t('archiveOrganize.stop');
    }
  }
}

async function loadArchiveOrganizeMobile() {
  var select = document.getElementById('mob-archive-organize-channel');
  if (!select) return;
  var channelsError = null;
  try {
    var data = await fetchJson('/api/archive/author-channels');
    var channels = (data && data.channels) || [];
    if (!channels.length) {
      select.innerHTML = '<option value="">' + esc(t('archiveOrganize.emptyChannels')) + '</option>';
    } else {
      select.innerHTML = channels.map(function(name) {
        return '<option value="' + esc(name) + '">' + esc(name) + '</option>';
      }).join('');
    }
  } catch (e) {
    channelsError = e;
    select.innerHTML = '<option value="">' + esc(translateApiError(e, 'form.requestFailed')) + '</option>';
  }
  var saved = loadSavedMobArchiveOrganizeJob();
  var job = null;
  var resumeError = null;
  try {
    if (saved && saved.id) {
      job = await fetchJson('/api/archive/author-job?id=' + encodeURIComponent(saved.id));
    }
  } catch (e) {
    resumeError = e;
    job = null;
  }
  if (!job || !job.id) {
    try {
      var channel = select.value || (saved && saved.channel_folder) || '';
      job = await fetchActiveMobArchiveOrganizeJob(channel);
      resumeError = null;
    } catch (e) {
      resumeError = e;
      job = null;
    }
  }
  if (!job || !job.id) {
    if (resumeError) {
      showToast(translateApiError(resumeError, 'form.requestFailed'));
    } else if (channelsError) {
      showToast(translateApiError(channelsError, 'form.requestFailed'));
    }
    return;
  }
  if (job.channel_folder) select.value = job.channel_folder;
  if (job.status === 'running') {
    mobArchiveOrganizeJobId = job.id;
    saveMobArchiveOrganizeJob(job);
    var busyKey = job.kind === 'reorganize'
      ? 'run'
      : (job.kind === 'resolve'
        ? ((job.phase === 'resolving_unresolved' || /未识别/.test(String(job.message || '')))
          ? 'resolveUnresolved'
          : 'resolve')
        : 'scan');
    setMobArchiveOrganizeBusy(true, busyKey);
    showMobArchiveOrganizeProgress(job);
    try {
      var finished = await pollMobArchiveOrganizeJob(job.id);
      if (finished.status === 'failure') {
        showMobArchiveOrganizeProgress({
          percent: 0, current: 0, total: 0, phase: 'error',
          message: finished.error || finished.message || t('form.requestFailed')
        });
        clearSavedMobArchiveOrganizeJob();
        return;
      }
      if (finished.kind === 'scan' || finished.kind === 'resolve') {
        if (finished.result) renderMobArchiveOrganizePlan(finished.result, finished.id);
      } else if (finished.kind === 'reorganize') {
        mobArchiveOrganizePlan = null;
        mobArchiveOrganizeJobId = null;
        var runBtn = document.getElementById('mob-archive-organize-run-btn');
        var runReviewBtn = document.getElementById('mob-archive-organize-run-review-btn');
        if (runBtn) runBtn.disabled = true;
        if (runReviewBtn) runReviewBtn.disabled = true;
      }
      clearSavedMobArchiveOrganizeJob();
    } catch (e) {
      showMobArchiveOrganizeProgress({
        percent: 0, current: 0, total: 0, phase: 'error',
        message: translateApiError(e, 'form.requestFailed')
      });
      showToast(translateApiError(e, 'form.requestFailed'));
      clearSavedMobArchiveOrganizeJob();
    } finally {
      setMobArchiveOrganizeBusy(false);
    }
    return;
  }
  if (job.status === 'success' && job.result && (job.kind === 'scan' || job.kind === 'resolve')) {
    showMobArchiveOrganizeProgress(job);
    renderMobArchiveOrganizePlan(job.result, job.id);
    clearSavedMobArchiveOrganizeJob();
  } else if (job.status === 'failure') {
    showMobArchiveOrganizeProgress(job);
    clearSavedMobArchiveOrganizeJob();
  }
}

function mobArchiveMethodLabel(item) {
  var method = (item && item.resolution_method) || '';
  var map = {
    signature: 'archiveOrganize.methodSignature',
    media_group: 'archiveOrganize.methodMediaGroup',
    neighbor: 'archiveOrganize.methodNeighbor',
    hashtag_exact: 'archiveOrganize.methodHashtagExact',
    hashtag_substring: 'archiveOrganize.methodHashtagFuzzy',
    hashtag_candidate: 'archiveOrganize.methodHashtagCandidate',
    none: 'archiveOrganize.methodNone'
  };
  var label = t(map[method] || 'archiveOrganize.methodNone');
  if (item && item.matched_tag) label += ' · #' + item.matched_tag;
  return label;
}

async function loadMobArchiveOrganizeMoves() {
  var result = document.getElementById('mob-archive-organize-result');
  var runBtn = document.getElementById('mob-archive-organize-run-btn');
  if (!result || !mobArchiveOrganizePlan) return;
  var summary = mobArchiveOrganizePlan.summary || {};
  var html = '<div class="text-sm" style="display:flex;gap:8px;flex-wrap:wrap;padding:12px;background:var(--color-surface-muted);border-radius:8px;margin-bottom:12px;">' +
    '<button type="button" class="mob-btn mob-btn-sm" data-mob-archive-bucket="executable"><strong>' + t('archiveOrganize.executable') + '</strong><br>' + mobArchiveExecutableCount(mobArchiveOrganizePlan) + '</button>' +
    '<button type="button" class="mob-btn mob-btn-sm" data-mob-archive-bucket="move"><strong>' + t('archiveOrganize.moves') + '</strong><br>' + (summary.move || mobArchiveOrganizePlan.move_count || 0) + '</button>' +
    '<button type="button" class="mob-btn mob-btn-sm" data-mob-archive-bucket="needs_confirm"><strong>' + t('archiveOrganize.confirm') + '</strong><br>' + (summary.needs_confirm || mobArchiveOrganizePlan.confirm_count || 0) + '</button>' +
    '<button type="button" class="mob-btn mob-btn-sm" data-mob-archive-bucket="needs_review"><strong>' + t('archiveOrganize.review') + '</strong><br>' + (summary.needs_review || mobArchiveOrganizePlan.review_count || 0) + '</button>' +
    '</div>';
  var channel = (document.getElementById('mob-archive-organize-channel') || {}).value || mobArchiveOrganizePlan.channel_folder || '';
  var params = new URLSearchParams();
  if (mobArchiveOrganizeJobId) params.set('job_id', mobArchiveOrganizeJobId);
  if (channel) params.set('channel_folder', channel);
  params.set('bucket', mobArchiveOrganizeBucket || 'executable');
  params.set('offset', '0');
  params.set('limit', String(MOB_ARCHIVE_PAGE_SIZE));
  try {
    var page = await fetchJson('/api/archive/author-plan-moves?' + params.toString());
    var items = page.items || [];
    html += '<div class="text-xs text-muted" style="margin-bottom:8px;">' +
      t('archiveOrganize.pageInfo')
        .replace('{bucket}', t('archiveOrganize.bucket.' + (mobArchiveOrganizeBucket || 'executable')))
        .replace('{from}', items.length ? '1' : '0')
        .replace('{to}', String(items.length))
        .replace('{total}', String(page.total || 0)) +
      '</div>';
    items.forEach(function(item) {
      html += '<div class="text-xs" style="padding:10px 0;border-bottom:1px solid var(--color-line);">' +
        '<div><strong>' + esc(item.author || '-') + '</strong> · ' + esc(item.action || '') + '</div>' +
        '<div class="text-muted">' + esc(mobArchiveMethodLabel(item)) + '</div>' +
        '<div class="text-muted">' + esc(item.from_relative || '') + ' → ' + esc(item.to_relative || '') + '</div>' +
        '</div>';
    });
  } catch (e) {
    html += '<div class="text-xs text-muted">' + esc(translateApiError(e, 'form.requestFailed')) + '</div>';
  }
  result.innerHTML = html;
  if (runBtn) runBtn.disabled = !(mobArchiveExecutableCount(mobArchiveOrganizePlan) > 0);
  result.querySelectorAll('[data-mob-archive-bucket]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      mobArchiveOrganizeBucket = btn.getAttribute('data-mob-archive-bucket') || 'executable';
      loadMobArchiveOrganizeMoves();
    });
  });
}

function renderMobArchiveOrganizePlan(data, jobId) {
  mobArchiveOrganizePlan = data;
  if (jobId) mobArchiveOrganizeJobId = jobId;
  mobArchiveOrganizeBucket = 'executable';
  loadMobArchiveOrganizeMoves();
}

async function scanArchiveOrganizeMobile() {
  var select = document.getElementById('mob-archive-organize-channel');
  var channel = select ? select.value : '';
  if (!channel) {
    showToast(t('archiveOrganize.pickChannel'));
    return;
  }
  setMobArchiveOrganizeBusy(true, 'scan');
  showMobArchiveOrganizeProgress({
    percent: 0, current: 0, total: 0, phase: 'listing', message: t('archiveOrganize.scanning')
  });
  try {
    var started = await postJson('/api/archive/author-scan', { channel_folder: channel });
    saveMobArchiveOrganizeJob(started);
    var job = await pollMobArchiveOrganizeJob(started.id);
    if (job.status === 'failure') throw new Error(job.error || job.message || 'scan failed');
    renderMobArchiveOrganizePlan(job.result || {}, job.id);
    clearSavedMobArchiveOrganizeJob();
  } catch (e) {
    var msg = translateApiError(e, 'form.requestFailed');
    showMobArchiveOrganizeProgress({
      percent: 0, current: 0, total: 0, phase: 'error', message: msg
    });
    showToast(msg);
  } finally {
    setMobArchiveOrganizeBusy(false);
  }
}

async function resolveArchiveOrganizeMobile(scope) {
  var select = document.getElementById('mob-archive-organize-channel');
  var channel = select ? select.value : '';
  if (!channel) {
    showToast(t('archiveOrganize.pickChannel'));
    return;
  }
  var resolveScope = scope || 'all';
  var busyKey = resolveScope === 'unresolved' ? 'resolveUnresolved' : 'resolve';
  setMobArchiveOrganizeBusy(true, busyKey);
  showMobArchiveOrganizeProgress({
    percent: 0,
    current: 0,
    total: 0,
    phase: 'resolving',
    message: resolveScope === 'unresolved'
      ? t('archiveOrganize.resolvingUnresolved')
      : t('archiveOrganize.resolving')
  });
  try {
    var started = await postJson('/api/archive/author-resolve', {
      channel_folder: channel,
      scope: resolveScope
    });
    saveMobArchiveOrganizeJob(started);
    var job = await pollMobArchiveOrganizeJob(started.id);
    if (job.status === 'failure') throw new Error(job.error || job.message || 'resolve failed');
    renderMobArchiveOrganizePlan(job.result || {}, job.id);
    clearSavedMobArchiveOrganizeJob();
  } catch (e) {
    var msg = translateApiError(e, 'form.requestFailed');
    showMobArchiveOrganizeProgress({
      percent: 0, current: 0, total: 0, phase: 'error', message: msg
    });
    showToast(msg);
  } finally {
    setMobArchiveOrganizeBusy(false);
  }
}

async function runArchiveOrganizeMobile() {
  var select = document.getElementById('mob-archive-organize-channel');
  var channel = select ? select.value : '';
  if (!channel) {
    showToast(t('archiveOrganize.pickChannel'));
    return;
  }
  var executable = mobArchiveExecutableCount(mobArchiveOrganizePlan);
  if (!mobArchiveOrganizePlan || !(executable > 0)) {
    showMobArchiveOrganizeProgress({
      percent: 0, current: 0, total: 0, phase: 'error',
      message: t('archiveOrganize.needScan')
    });
    showToast(t('archiveOrganize.needScan'));
    return;
  }
  if (!confirm(t('archiveOrganize.runAllConfirm')
    .replace('{channel}', channel)
    .replace('{count}', String(executable)))) return;
  setMobArchiveOrganizeBusy(true, 'run');
  showMobArchiveOrganizeProgress({
    percent: 0,
    current: 0,
    total: executable,
    phase: 'moving',
    message: t('archiveOrganize.running')
  });
  try {
    var started = await postJson('/api/archive/author-reorganize', {
      channel_folder: channel,
      mode: 'all'
    });
    saveMobArchiveOrganizeJob(started);
    mobArchiveOrganizeJobId = started.id;
    var job = await pollMobArchiveOrganizeJob(started.id);
    if (job.status === 'failure') throw new Error(job.error || job.message || 'reorganize failed');
    var data = job.result || {};
    var stopped = job.status === 'stopped' || data.stopped;
    showMobArchiveOrganizeProgress({
      percent: stopped ? (job.percent || 0) : 100,
      current: job.current || data.moved_count || 0,
      total: job.total || data.planned_moves || executable,
      phase: stopped ? 'stopped' : 'done',
      message: (job.message || '') +
        (stopped ? (' · ' + t('archiveOrganize.stopped')) : '') +
        ' · ' + t('archiveOrganize.moved') + ': ' + (data.moved_count || 0) +
        ' / ' + t('archiveOrganize.errors') + ': ' + (data.error_count || 0)
    });
    showToast(
      stopped
        ? t('archiveOrganize.stopped')
        : (
          t('archiveOrganize.moved') + ': ' + (data.moved_count || 0) +
          ' / ' + t('archiveOrganize.errors') + ': ' + (data.error_count || 0)
        )
    );
    if (!stopped) {
      mobArchiveOrganizePlan = null;
      mobArchiveOrganizeJobId = null;
      var runBtn = document.getElementById('mob-archive-organize-run-btn');
      if (runBtn) runBtn.disabled = true;
      clearSavedMobArchiveOrganizeJob();
    } else {
      saveMobArchiveOrganizeJob(job);
    }
  } catch (e) {
    var msg = translateApiError(e, 'form.requestFailed');
    showMobArchiveOrganizeProgress({
      percent: 0, current: 0, total: 0, phase: 'error', message: msg
    });
    showToast(msg);
  } finally {
    setMobArchiveOrganizeBusy(false);
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

  bindMobileSystemLogsControls();

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
        if (commentGroup) {
          bindCommentDelayField(commentGroup);
          syncCommentDelayFieldVisibility(commentGroup);
        }
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
      formData.forEach(function(v, k) {
        if (k === 'media_types_mode' || k === 'override_media_types') return;
        payload[k] = v;
      });
      if (payload.start_id) payload.start_id = Number(payload.start_id);
      if (payload.end_id) payload.end_id = Number(payload.end_id);
      payload.include_comment = transferForm.querySelector('[name="include_comment"]').checked;
      payload.resolve_deep_link = transferForm.querySelector('[name="resolve_deep_link"]').checked;
      payload.archive_by_author = transferForm.querySelector('[name="archive_by_author"]') ? transferForm.querySelector('[name="archive_by_author"]').checked : false;
      payload.media_types = readMediaTypesOverride(transferForm);
      var notice = document.getElementById('mob-form-notice');
      try {
        await postJson('/api/tasks', payload);
        showMobFormSuccess(notice, t('form.createSuccess'));
        transferForm.reset();
        setMediaTypesPicker(transferForm.querySelector('[data-media-types-picker]'), null);
        await loadMobileTasks();
        resetTaskPolling();
        setTimeout(function() { loadMobileTasks(); }, 800);
        setTimeout(function() { if (notice) notice.classList.add('hidden'); }, 1000);
      } catch (e) {
        showMobFormError(notice, e, 'form.createFailed');
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
        payload.resolve_deep_link = watchForm.querySelector('[name="resolve_deep_link"]') ? watchForm.querySelector('[name="resolve_deep_link"]').checked : false;
        payload.comment_delay_minutes = readOptionalCommentDelayMinutes(watchForm);
      }
      payload.archive_by_author = watchForm.querySelector('[name="archive_by_author"]') ? watchForm.querySelector('[name="archive_by_author"]').checked : false;
      payload.media_types = readMediaTypesOverride(watchForm);
      var notice = document.getElementById('mob-watch-notice');
      try {
        await postJson('/api/watches', payload);
        showMobFormSuccess(notice, t('form.createSuccess'));
        watchForm.reset();
        setMediaTypesPicker(watchForm.querySelector('[data-media-types-picker]'), null);
        syncCommentDelayFieldVisibility(watchForm);
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileWatches(); }, 1000);
      } catch (e) {
        showMobFormError(notice, e, 'form.createFailed');
      }
    });
    bindCommentDelayField(watchForm);
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
        showMobFormSuccess(notice, t('form.createSuccess'));
        channelForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileOperations(); }, 1000);
      } catch (e) {
        showMobFormError(notice, e, 'form.createFailed');
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
        showMobFormSuccess(notice, t('form.createSuccess'));
        uploadForm.reset();
        setTimeout(function() { if (notice) notice.classList.add('hidden'); loadMobileOperations(); }, 1000);
      } catch (e) {
        showMobFormError(notice, e, 'form.createFailed');
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
      var inputs = settingsContainer.querySelectorAll('input[name], select[name], textarea[name]');
      var payload = {};
      inputs.forEach(function(input) {
        if (input.name === 'user.download_type') return;
        if (input.name === 'global.deep_link.bot_whitelist') return;
        if (input.name === 'override_media_types' || input.name === 'media_types_mode') return;
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

      var whitelistEl = settingsContainer.querySelector('[name="global.deep_link.bot_whitelist"]');
      if (whitelistEl) {
        payload.global = payload.global || {};
        payload.global.deep_link = payload.global.deep_link || {};
        payload.global.deep_link.bot_whitelist = String(whitelistEl.value || '')
          .split(/[\n,]+/)
          .map(function(s) { return s.trim(); })
          .filter(Boolean);
      }

      // Dual-write unified media allowlist → forward_type + download_type
      var mediaTypesDict = payload.global && payload.global.message_filter && payload.global.message_filter.media_types;
      if (mediaTypesDict && typeof mediaTypesDict === 'object') {
        mediaTypesDict = completeMediaTypesDict(mediaTypesDict);
        payload.global.message_filter.media_types = mediaTypesDict;
        payload.global.forward_type = completeMediaTypesDict(mediaTypesDict);
        payload.user = payload.user || {};
        payload.user.download_type = mediaTypesToDownloadTypeList(mediaTypesDict);
      }

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
        showMobFormSuccess(notice, t('settings.saved'));
        setTimeout(function() { if (notice) notice.classList.add('hidden'); }, 2000);
      } catch (e) {
        showMobFormError(notice, e, 'form.requestFailed');
      }
    });
  }

  var mobForwardExportBtn = document.getElementById('mob-forward-watch-export-btn');
  if (mobForwardExportBtn) {
    mobForwardExportBtn.addEventListener('click', async function() {
      if (mobForwardExportBtn.disabled) return;
      mobForwardExportBtn.disabled = true;
      try {
        await downloadForwardWatchBackup();
      } catch (e) {
        if (e && e.error_code === 'auth_required') redirectToLoginPage();
        else alert(t('settings.forwardWatchExportFailed'));
      } finally {
        mobForwardExportBtn.disabled = false;
      }
    });
  }

  var mobForwardImportInput = document.getElementById('mob-forward-watch-import-input');
  if (mobForwardImportInput) {
    mobForwardImportInput.addEventListener('change', async function() {
      var file = mobForwardImportInput.files && mobForwardImportInput.files[0];
      mobForwardImportInput.value = '';
      if (!file) return;
      var notice = document.getElementById('mob-forward-watch-import-notice');
      try {
        var result = await importForwardWatchBackupFile(file);
        if (notice) {
          showMobFormSuccess(notice, formatForwardWatchImportResult(result));
        }
        if (typeof loadMobileWatches === 'function') loadMobileWatches();
      } catch (e) {
        if (e && e.error_code === 'auth_required') {
          redirectToLoginPage();
          return;
        }
        showMobFormError(notice, e, 'settings.forwardWatchImportFailed');
      }
    });
  }

  // Media scan button
  var mediaBtn = document.getElementById('mob-media-scan-btn');
  if (mediaBtn) mediaBtn.addEventListener('click', loadMediaMobile);

  var archiveScanBtn = document.getElementById('mob-archive-organize-scan-btn');
  if (archiveScanBtn) archiveScanBtn.addEventListener('click', scanArchiveOrganizeMobile);
  var archiveResolveBtn = document.getElementById('mob-archive-organize-resolve-btn');
  if (archiveResolveBtn) {
    archiveResolveBtn.addEventListener('click', function() {
      resolveArchiveOrganizeMobile('all');
    });
  }
  var archiveResolveUnresolvedBtn = document.getElementById('mob-archive-organize-resolve-unresolved-btn');
  if (archiveResolveUnresolvedBtn) {
    archiveResolveUnresolvedBtn.addEventListener('click', function() {
      resolveArchiveOrganizeMobile('unresolved');
    });
  }
  var archiveRunBtn = document.getElementById('mob-archive-organize-run-btn');
  if (archiveRunBtn) archiveRunBtn.addEventListener('click', runArchiveOrganizeMobile);
  var archiveStopBtn = document.getElementById('mob-archive-organize-stop-btn');
  if (archiveStopBtn) archiveStopBtn.addEventListener('click', stopArchiveOrganizeMobile);

  mobEnsureOverrideMediaTypeGrids();
  bindAllMediaTypesPickers(document);

  applyMobileRouteFromLocation();
  window.addEventListener('popstate', function() {
    applyMobileRouteFromLocation();
  });

  // Kickoff
  if (typeof startSetupPolling === 'function') startSetupPolling();
  checkAuthStatus();
})();
