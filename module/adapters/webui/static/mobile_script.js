
  /* ====== 登录流程（移动端） ====== */
  var authPollTimer = null;
  var authStep = '';

  function showLoginStep(step) {
    authStep = step;
    var steps = ['login-form-phone', 'login-form-code', 'login-form-password', 'login-form-recovery', 'login-form-signup', 'login-form-done'];
    steps.forEach(function(id) { var el = document.getElementById(id); if (el) el.style.display = 'none'; });
    var el = document.getElementById('login-form-' + step);
    if (el) el.style.display = '';
    var container = document.getElementById('login-container');
    if (container) container.classList.add('active');
    var loginError = document.getElementById('login-error');
    if (loginError) loginError.classList.remove('visible');
  }

  function hideLogin() {
    var container = document.getElementById('login-container');
    if (container) container.classList.remove('active');
    if (authPollTimer) { clearInterval(authPollTimer); authPollTimer = null; }
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
      if (resp.status === 401) return;
      var state = await resp.json();
      if (!state || !state.step) return;
      switch (state.step) {
        case 'pending':
          var container = document.getElementById('login-container');
          if (container) container.classList.remove('active');
          return;
        case 'done': case 'none':
          hideLogin();
          loadTasks();
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
            if (desc) desc.textContent = '\u9a8c\u8bc1\u7801\u5df2\u901a\u8fc7\u300c' + state.code_type + '\u300d\u53d1\u9001';
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
    var btn = document.querySelector('.login-submit');
    if (btn) btn.disabled = true;
    showLoginError('');
    try {
      await fetch('/api/auth/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      await new Promise(function(r) { setTimeout(r, 500); });
      await checkAuthStatus();
    } catch (e) {
      showLoginError('\u63d0\u4ea4\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5');
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  /* phone submit */
  var phoneBtn = document.getElementById('login-btn-phone');
  if (phoneBtn) {
    phoneBtn.addEventListener('click', function() {
      var phone = document.getElementById('login-phone').value.trim();
      if (!phone) { showLoginError('\u8bf7\u8f93\u5165\u7535\u8bdd\u53f7\u7801'); return; }
      if (!phone.startsWith('+')) { showLoginError('\u7535\u8bdd\u53f7\u7801\u9700\u4ee5 +\u5730\u533a\u53f7\u5f00\u5934'); return; }
      submitAuth({ phone: phone });
    });
  }

  var codeBtn = document.getElementById('login-btn-code');
  if (codeBtn) {
    codeBtn.addEventListener('click', function() {
      var code = document.getElementById('login-code').value.trim();
      if (!code) { showLoginError('\u8bf7\u8f93\u5165\u9a8c\u8bc1\u7801'); return; }
      submitAuth({ code: code });
    });
  }

  var backBtn = document.getElementById('login-btn-back');
  if (backBtn) {
    backBtn.addEventListener('click', function() {
      showLoginStep('phone');
      document.getElementById('login-code').value = '';
    });
  }

  var pwdBtn = document.getElementById('login-btn-password');
  if (pwdBtn) {
    pwdBtn.addEventListener('click', function() {
      var pwd = document.getElementById('login-password').value;
      submitAuth({ password: pwd });
    });
  }

  var pwdBackBtn = document.getElementById('login-btn-back-pwd');
  if (pwdBackBtn) {
    pwdBackBtn.addEventListener('click', function() {
      showLoginStep('code');
      document.getElementById('login-password').value = '';
    });
  }

  var recBtn = document.getElementById('login-btn-recovery');
  if (recBtn) {
    recBtn.addEventListener('click', function() {
      var code = document.getElementById('login-recovery').value.trim();
      if (!code) { showLoginError('\u8bf7\u8f93\u5165\u6062\u590d\u4ee3\u7801'); return; }
      submitAuth({ recovery_code: code });
    });
  }

  var recBackBtn = document.getElementById('login-btn-back-recovery');
  if (recBackBtn) {
    recBackBtn.addEventListener('click', function() {
      showLoginStep('password');
      document.getElementById('login-recovery').value = '';
    });
  }

  var signupBtn = document.getElementById('login-btn-signup');
  if (signupBtn) {
    signupBtn.addEventListener('click', function() {
      var first = document.getElementById('login-first-name').value.trim();
      if (!first) { showLoginError('\u8bf7\u8f93\u5165\u540d\u5b57'); return; }
      submitAuth({ first_name: first, last_name: document.getElementById('login-last-name').value.trim() });
    });
  }

  (function() {
    checkAuthStatus();
    authPollTimer = setInterval(function() {
      if (authStep === 'done' || authStep === 'none') {
        clearInterval(authPollTimer);
        authPollTimer = null;
        return;
      }
      checkAuthStatus();
    }, 2000);
  })();

  /* ====== 移动端初始化 ====== */
  function hasActiveTasks() {
    return state.tasks.some(function(t) { return t.status === 'pending' || t.status === 'running'; });
  }

  function startPolling() {
    if (state.taskPollTimer) return;
    var fastInterval = 3000;
    var slowInterval = 15000;
    var currentInterval = fastInterval;
    var lastPollTime = 0;

    async function poll() {
      if (document.hidden) { scheduleNext(currentInterval); return; }
      var now = Date.now();
      var minGap = currentInterval - 500;
      if (now - lastPollTime < minGap) { scheduleNext(currentInterval); return; }
      lastPollTime = now;
      try { await loadTasks(); } catch (e) { console.warn('Poll failed:', e); }
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
    if (view === 'media') loadMediaMobile();
  }

  async function loadMediaMobile() {
    var info = $('#mob-media-result');
    info.innerHTML = '<p>' + t('media.scanning') + '</p>';
    try {
      var data = await fetchJson('/api/media/scan');
      var ti = data.transfer_items || {};
      var orph = data.orphan_files || {};
      var totalCount = data.total_count || 0;
      var totalSize = data.total_size || 0;
      info.innerHTML =
        '<p><strong>' + t('media.totalFiles') + ':</strong> ' + totalCount + '</p>' +
        '<p><strong>' + t('media.totalSize') + ':</strong> ' + formatBytes(totalSize) + '</p>';
    } catch (err) {
      info.innerHTML = '<p>' + translateApiError(err, 'form.requestFailed') + '</p>';
    }
  }

  // mobile media scan button
  var mobMediaBtn = $('#mob-media-scan-btn');
  if (mobMediaBtn) mobMediaBtn.addEventListener('click', loadMediaMobile);

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
  function showToast(message, duration) {
    if (duration === void 0) duration = 2500;
    const toast = $('#mob-toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(mobToastTimer);
    mobToastTimer = setTimeout(function() { toast.classList.remove('show'); }, duration);
  }

  /* ====== 卡片状态徽章 ====== */
  function mobBadge(status) {
    var cls;
    if (status === 'running') cls = 'running';
    else if (status === 'success') cls = 'completed';
    else if (status === 'paused') cls = 'paused';
    else if (status === 'failure') cls = 'failure';
    else if (status === 'cancelled') cls = 'cancelled';
    else cls = 'pending';
    return '<span class="mob-card__badge ' + cls + '">' + esc(t('status.' + status)) + '</span>';
  }

  /* ====== 渲染转存任务卡片列表 ====== */
  function renderMobTasks() {
    var tasks = state.tasks || [];
    var container = $('#mob-tasks-list');
    if (!tasks.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="tasks.empty">' + t('tasks.empty') + '</div>';
      return;
    }
    container.innerHTML = tasks.map(function(task) {
      var total = Number(task.total_items || 0);
      var done = Number(task.completed_items || 0);
      var failed = Number(task.failed_items || 0);
      var percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
      var actions = '';
      if (task.status === 'running') actions += '<button class="secondary small" data-pause="' + task.id + '">' + t('tasks.pause') + '</button>';
      if (task.status === 'paused') actions += '<button class="secondary small" data-resume="' + task.id + '">' + t('tasks.resume') + '</button>';
      if (task.failed_items > 0) actions += '<button class="secondary small" data-retry="' + task.id + '">' + t('tasks.retryFailed') + '</button>';
      actions += '<button class="danger small" data-delete="' + task.id + '">' + t('tasks.delete') + '</button>';
      return '<div class="mob-card status-' + task.status + '">'
        + '<div class="mob-card__head">'
        + '<span class="mob-card__title">' + esc(task.source_link) + '</span>'
        + mobBadge(task.status)
        + '</div>'
        + '<div class="mob-card__row"><span class="label">' + t('tasks.target') + '</span><span>' + esc(task.target_link) + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('tasks.progress') + '</span><span>' + done + '/' + total + (failed ? ' (' + failed + ' ' + t('side.failed') + ')' : '') + '</span></div>'
        + '<div class="mob-card__progress"><div class="mob-card__progress-fill" style="width:' + percent + '%"></div></div>'
        + '<div class="mob-card__actions">' + actions + '</div>'
        + '</div>';
    }).join('');

    container.querySelectorAll('[data-pause]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { runTaskAction(e, Number(btn.dataset.pause), 'pause'); });
    });
    container.querySelectorAll('[data-resume]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { runTaskAction(e, Number(btn.dataset.resume), 'resume'); });
    });
    container.querySelectorAll('[data-retry]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { runTaskAction(e, Number(btn.dataset.retry), 'retry-failed'); });
    });
    container.querySelectorAll('[data-delete]').forEach(function(btn) {
      btn.addEventListener('click', function(e) { deleteTask(e, Number(btn.dataset.delete)); });
    });

    // 点击卡片打开详情
    container.querySelectorAll('.mob-card').forEach(function(card, idx) {
      card.addEventListener('click', function(e) {
        if (e.target.closest('button')) return;
        openTaskDetail(tasks[idx].id);
      });
    });
  }

  /* ====== 渲染监听卡片列表 ====== */
  function renderMobWatches() {
    var watches = state.watches || [];
    var container = $('#mob-watches-list');
    if (!watches.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="watches.empty">' + t('watches.empty') + '</div>';
      return;
    }
    container.innerHTML = watches.map(function(w) {
      var typeLabel = w.type === 'download' ? t('watches.download') : t('watches.forward');
      var sourceHtml = '';
      if (w.source_links) {
        sourceHtml = '<div class="mob-card__row"><span class="label">' + t('watches.sources') + '</span><span>' + esc((w.source_links || []).join(', ')) + '</span></div>';
      } else if (w.source_link) {
        sourceHtml = '<div class="mob-card__row"><span class="label">' + t('watches.source') + '</span><span>' + esc(w.source_link) + '</span></div>';
      }
      var targetHtml = '';
      if (w.target_link) {
        targetHtml = '<div class="mob-card__row"><span class="label">' + t('watches.target') + '</span><span>' + esc(w.target_link) + '</span></div>';
      }
      var watchId = w.encoded_id || w.id;
      var sanitized = (watchId || '').replace(/:/g, '_');
      var eventsBtn = '';
      var eventsPanel = '';
      if (w.type === 'forward') {
        var ec = w.event_count || 0;
        eventsBtn = '<button class="small" data-watch-events="' + watchId + '">' + t('watches.events') + (ec ? ' (' + ec + ')' : '') + '</button>';
        eventsPanel = '<div class="mob-watch-events" id="mob-watch-events-' + sanitized + '" style="display:none;"></div>';
      }
      return '<div class="mob-card status-' + (w.status || 'running') + '">'
        + '<div class="mob-card__head">'
        + '<span class="mob-card__title">' + typeLabel + '</span>'
        + '<span class="mob-card__badge running">' + esc(w.type) + '</span>'
        + '</div>'
        + sourceHtml + targetHtml
        + '<div class="mob-card__actions">'
        + '<button class="danger small" data-delete-watch="' + watchId + '">' + t('watches.delete') + '</button>'
        + eventsBtn
        + '</div>'
        + eventsPanel
        + '</div>';
    }).join('');

    container.querySelectorAll('[data-delete-watch]').forEach(function(btn) {
      btn.addEventListener('click', function() { deleteWatch(btn.dataset.deleteWatch); });
    });

    container.querySelectorAll('[data-watch-events]').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var watchId = btn.dataset.watchEvents;
        var sanitized = watchId.replace(/:/g, '_');
        var panel = document.getElementById('mob-watch-events-' + sanitized);
        if (!panel) return;
        if (panel.style.display === 'none' || panel.style.display === '') {
          panel.style.display = 'block';
          loadMobileWatchEvents(watchId, sanitized);
        } else {
          panel.style.display = 'none';
        }
      });
    });
  }

  async function loadMobileWatchEvents(watchId, sanitized) {
    var panel = document.getElementById('mob-watch-events-' + sanitized);
    if (!panel) return;
    panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.eventLoading')) + '</div>';
    try {
      var res = await fetch('/api/watches/' + encodeURIComponent(watchId) + '/events?limit=50&offset=0');
      var data = await res.json();
      if (!res.ok) { panel.innerHTML = '<div class="watch-event-item">' + esc(data.error || 'Load failed') + '</div>'; return; }
      var items = data.events || [];
      if (!items.length) {
        panel.innerHTML = '<div class="watch-event-item">' + esc(t('watches.noEvents')) + '</div>';
        return;
      }
      panel.innerHTML = '';
      items.forEach(function(evt) {
        var time = new Date(evt.created_at + 'Z').toLocaleString();
        var statusClass = evt.status === 'success' ? 'success' : 'warning';
        var statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
        var div = document.createElement('div');
        div.className = 'watch-event-item';
        div.innerHTML = '<span class="watch-event-time">' + esc(time) + '</span>'
          + '<span class="watch-event-badge"><span class="badge ' + statusClass + '">' + esc(statusLabel) + '</span></span>'
          + '<span class="watch-event-info">' + esc(evt.message) + ' #' + esc(String(evt.source_message_id || '')) + '</span>';
        panel.appendChild(div);
      });
    } catch (e) {
      panel.innerHTML = '<div class="watch-event-item">' + esc(t('form.requestFailed')) + '</div>';
    }
  }

  /* ====== 任务详情 Sheet ====== */
  var sheetTaskId = null;
  var sheetItems = [];
  var sheetEvents = [];
  var sheetItemTotal = 0;
  var sheetEventTotal = 0;
  var sheetItemOffset = 0;
  var sheetEventOffset = 0;
  var sheetHasMoreItems = false;
  var sheetHasMoreEvents = false;
  var sheetActiveTab = 'running';
  var sheetItemPage = 1;
  var sheetItemPageSize = 10;

  async function openTaskDetail(taskId) {
    sheetTaskId = taskId;
    state.selectedTaskId = taskId;
    sheetItems = [];
    sheetEvents = [];
    sheetActiveTab = 'running';
    sheetItemPage = 1;
    sheetItemOffset = 0;
    sheetEventOffset = 0;
    try {
      var res = await fetch('/api/tasks/' + taskId + '?items_limit=200&items_offset=0&events_limit=100&events_offset=0');
      if (!res.ok) { showToast(translateApiError(await res.json())); return; }
      var data = await res.json();
      sheetItems = data.items || [];
      sheetEvents = data.events || [];
      sheetItemTotal = data.item_count || 0;
      sheetEventTotal = data.event_count || 0;
      sheetItemOffset = data.items_offset || 0;
      sheetEventOffset = data.events_offset || 0;
      sheetHasMoreItems = data.has_more_items || false;
      sheetHasMoreEvents = data.has_more_events || false;
    } catch (e) { showToast(t('form.requestFailed')); return; }

    var task = state.tasks.find(function(t) { return t.id === taskId; });
    var total = Number((task && task.total_items) || 0);
    var done = Number((task && task.completed_items) || 0);
    var failed = Number((task && task.failed_items) || 0);
    var percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;

    var groups = categorizeSheetItems();
    var html = '<h3 class="mob-sheet__title">#' + taskId + ' ' + esc((task && task.source_link) || '') + '</h3>'
      + '<div class="mob-sheet__task-header">'
      + '<div class="task-title">' + esc((task && task.source_link) || '') + '</div>'
      + '<div class="task-meta">' + (task ? (mobBadge(task.status) + ' ' + esc(task.target_link || '')) : '') + '</div>'
      + '<div class="mob-card__row"><span class="label">' + t('tasks.progress') + '</span><span>' + done + '/' + total + (failed ? ' (' + failed + ' ' + t('side.failed') + ')' : '') + '</span></div>'
      + '<div class="mob-card__progress"><div class="mob-card__progress-fill" style="width:' + percent + '%"></div></div>'
      + '</div>'
      + '<div class="mob-sheet-tabs" id="mob-sheet-item-tabs">'
      + renderSheetTab('running', groups.running.length)
      + renderSheetTab('success', groups.success.length)
      + renderSheetTab('skipped', groups.skipped.length)
      + renderSheetTab('failure', groups.failure.length)
      + '</div>'
      + '<div id="mob-sheet-items"></div>'
      + '<div id="mob-sheet-items-pagination"></div>'
      + '<div class="mob-section-title" style="margin-top:6px;">' + t('events.title') + ' (' + String(sheetEvents.length) + (sheetEventTotal > sheetEvents.length ? ' / ' + sheetEventTotal : '') + ')</div>'
      + '<div id="mob-sheet-events"></div>';

    var sheet = $('#mob-sheet');
    sheet.innerHTML = html;
    $('#mob-sheet-overlay').classList.add('open');

    bindSheetTabClicks();
    renderSheetItemPage();
    renderSheetEvents();

    // Sheet overlay 点击关闭
    $('#mob-sheet-overlay').onclick = function(e) {
      if (e.target === this) closeSheet();
    };
  }

  function closeSheet() {
    $('#mob-sheet-overlay').classList.remove('open');
    sheetTaskId = null;
  }

  function renderSheetTab(status, count) {
    var labelKey = 'items.tab.' + status;
    var active = sheetActiveTab === status ? ' active' : '';
    return '<button class="mob-sheet-tab' + active + '" data-sheet-tab="' + status + '">' + t(labelKey) + '<span class="count">' + count + '</span></button>';
  }

  function bindSheetTabClicks() {
    var tabs = document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab');
    tabs.forEach(function(tab) {
      tab.addEventListener('click', function() {
        sheetActiveTab = this.dataset.sheetTab;
        sheetItemPage = 1;
        var allTabs = document.querySelectorAll('#mob-sheet-item-tabs .mob-sheet-tab');
        allTabs.forEach(function(t) { t.classList.remove('active'); });
        this.classList.add('active');
        renderSheetItemPage();
      });
    });
  }

  function categorizeSheetItems() {
    var groups = { running: [], success: [], skipped: [], failure: [] };
    (sheetItems || []).forEach(function(item) {
      var status = String((item && item.status) || 'pending');
      if (status === 'success' || status === 'skipped' || status === 'failure') {
        groups[status].push(item);
      } else {
        groups.running.push(item);
      }
    });
    return groups;
  }

  function renderSheetItemPage() {
    var groups = categorizeSheetItems();
    var activeItems = groups[sheetActiveTab] || [];
    var total = activeItems.length;
    var pages = Math.max(1, Math.ceil(total / sheetItemPageSize));
    if (sheetItemPage > pages) sheetItemPage = pages;
    var start = (sheetItemPage - 1) * sheetItemPageSize;
    var end = Math.min(start + sheetItemPageSize, total);
    var pageItems = activeItems.slice(start, end);

    var container = $('#mob-sheet-items');
    if (!pageItems.length) {
      container.innerHTML = '<div class="mob-empty">' + t('items.empty.' + sheetActiveTab) + '</div>';
    } else {
      container.innerHTML = pageItems.map(function(item) {
        var dlPct = pct(item.download_current, item.download_total);
        var ulPct = pct(item.upload_current, item.upload_total);
        return '<div class="mob-item-row">'
          + '<div class="mob-item-row__name">' + esc(item.file_name || item.local_path || '#' + (item.source_message_id || item.id)) + '</div>'
          + '<div style="text-align:right;font-size:var(--font-xs);color:var(--muted);flex-shrink:0;">'
          + '<div>' + t('items.download') + ' ' + dlPct + '%</div>'
          + '<div>' + t('items.upload') + ' ' + ulPct + '%</div>'
          + '</div>'
          + '</div>';
      }).join('');
    }

    var pagEl = $('#mob-sheet-items-pagination');
    var pagHtml = '';
    if (pages > 1) {
      pagHtml += '<div class="mob-sheet-pagination">'
        + '<button class="secondary small" ' + (sheetItemPage <= 1 ? 'disabled' : '') + ' onclick="sheetPrevPage()">' + t('items.page.previous') + '</button>'
        + '<span>' + interpolate(t('items.page.range'), { start: start + 1, end: end, total: total }) + '</span>'
        + '<button class="secondary small" ' + (sheetItemPage >= pages ? 'disabled' : '') + ' onclick="sheetNextPage()">' + t('items.page.next') + '</button>'
        + '</div>';
    }
    if (sheetHasMoreItems && sheetItems.length < sheetItemTotal) {
      pagHtml += '<div class="mob-load-more"><button class="secondary small" onclick="loadMoreSheetItems()">' + t('items.loadMore') + ' (' + (sheetItemTotal - sheetItems.length) + ' ' + t('items.remaining') + ')</button></div>';
    }
    pagEl.innerHTML = pagHtml;
  }

  function renderSheetEvents() {
    var container = $('#mob-sheet-events');
    if (!sheetEvents.length) {
      container.innerHTML = '<div class="mob-empty">' + t('events.empty') + '</div>';
      return;
    }
    var html = sheetEvents.map(function(event) {
      return '<div class="mob-event-row">'
        + '<time>' + esc(event.created_at) + '</time>'
        + '<span style="color:var(--accent);">[' + esc(localizeEventLevel(event.level)) + ']</span> '
        + esc(localizeEventMessage(event))
        + '</div>';
    }).join('');
    if (sheetHasMoreEvents && sheetEvents.length < sheetEventTotal) {
      html += '<div class="mob-load-more"><button class="secondary small" onclick="loadMoreSheetEvents()">' + t('events.loadMore') + ' (' + (sheetEventTotal - sheetEvents.length) + ' ' + t('events.remaining') + ')</button></div>';
    }
    container.innerHTML = html;
  }

  function sheetPrevPage() {
    if (sheetItemPage > 1) { sheetItemPage--; renderSheetItemPage(); }
  }
  function sheetNextPage() {
    sheetItemPage++;
    renderSheetItemPage();
  }
  window.sheetPrevPage = sheetPrevPage;
  window.sheetNextPage = sheetNextPage;

  async function loadMoreSheetItems() {
    if (!sheetTaskId) return;
    var offset = sheetItemOffset + 200;
    try {
      var res = await fetch('/api/tasks/' + sheetTaskId + '?items_limit=200&items_offset=' + offset + '&events_limit=0&events_offset=0');
      if (!res.ok) return;
      var data = await res.json();
      sheetItems = sheetItems.concat(data.items || []);
      sheetItemTotal = data.item_count || sheetItemTotal;
      sheetItemOffset = offset;
      sheetHasMoreItems = data.has_more_items || false;
      renderSheetItemPage();
    } catch (e) { /* ignore */ }
  }
  window.loadMoreSheetItems = loadMoreSheetItems;

  async function loadMoreSheetEvents() {
    if (!sheetTaskId) return;
    var offset = sheetEventOffset + 100;
    try {
      var res = await fetch('/api/tasks/' + sheetTaskId + '?items_limit=0&items_offset=0&events_limit=100&events_offset=' + offset);
      if (!res.ok) return;
      var data = await res.json();
      sheetEvents = sheetEvents.concat(data.events || []);
      sheetEventTotal = data.event_count || sheetEventTotal;
      sheetEventOffset = offset;
      sheetHasMoreEvents = data.has_more_events || false;
      renderSheetEvents();
    } catch (e) { /* ignore */ }
  }
  window.loadMoreSheetEvents = loadMoreSheetEvents;

  /* ====== 渲染设置表单 ====== */
  function renderMobSettingsForm() {
    if (!state.settings || !state.schema) return;
    var s = state.settings;
    var schema = state.schema;
    var user = s.user || {};
    var glob = s.global || {};
    var tp = (glob.target_profiles || {});
    var pikpak = tp.pikpak || {};
    var archive = pikpak.archive || {};
    var upload = glob.upload || {};
    var sensitiveKeys = schema.sensitive_keys || [];
    var downloadTypes = schema.download_type || [];
    var forwardTypes = schema.forward_type || [];
    var selectedDownload = user.download_type || [];
    var exportTable = glob.export_table || {};

    // Path & Task
    var maxTasks = user.max_tasks || {};
    var maxRetries = user.max_retries || {};
    $('#mob-settings-path-fields').innerHTML =
      '<label><span>' + t('settings.saveDirectory') + '</span><input type="text" name="user.save_directory" value="' + esc(user.save_directory || '') + '"></label>'
      + '<label><span>' + t('settings.tempDirectory') + '</span><input type="text" name="user.temp_directory" value="' + esc(user.temp_directory || '') + '"></label>'
      + '<label><span>' + t('settings.sessionDirectory') + '</span><input type="text" name="user.session_directory" value="' + esc(user.session_directory || '') + '"></label>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
      + '<label><span>' + t('settings.maxDownload') + '</span><input type="number" name="user.max_tasks.download" value="' + esc(maxTasks.download || '') + '" min="1"></label>'
      + '<label><span>' + t('settings.maxUpload') + '</span><input type="number" name="user.max_tasks.upload" value="' + esc(maxTasks.upload || '') + '" min="1"></label>'
      + '</div>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
      + '<label><span>' + t('settings.retryDownload') + '</span><input type="number" name="user.max_retries.download" value="' + esc(maxRetries.download || '') + '" min="0"></label>'
      + '<label><span>' + t('settings.retryUpload') + '</span><input type="number" name="user.max_retries.upload" value="' + esc(maxRetries.upload || '') + '" min="0"></label>'
      + '</div>'
      + '<label><span>' + t('settings.pikpakMaxFileSize') + '</span><input type="number" name="global.target_profiles.pikpak.max_file_size" value="' + esc(pikpak.max_file_size || '') + '" min="1"></label>';

    // Behavior
    $('#mob-settings-behavior-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.notice" style="width:auto;min-height:auto;"' + (glob.notice ? ' checked' : '') + '><span>' + t('settings.notice') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="user.is_shutdown" style="width:auto;min-height:auto;"' + (user.is_shutdown ? ' checked' : '') + '><span>' + t('settings.shutdown') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.download_upload" style="width:auto;min-height:auto;"' + (upload.download_upload ? ' checked' : '') + '><span>' + t('settings.downloadUpload') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.upload.delete" style="width:auto;min-height:auto;"' + (upload.delete ? ' checked' : '') + '><span>' + t('settings.uploadDelete') + '</span></label>'
      + '<label><span>' + t('settings.pendingLimit') + '</span><input type="number" name="global.upload.pending_limit" value="' + esc(upload.pending_limit || '') + '" min="1" max="5"></label>';

    // PikPak Archive
    $('#mob-settings-archive-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.target_profiles.pikpak.archive.enable" style="width:auto;min-height:auto;"' + (archive.enable ? ' checked' : '') + '><span>' + t('settings.pikpakArchiveEnable') + '</span></label>'
      + '<label><span>' + t('settings.pikpakArchiveRemote') + '</span><input type="text" name="global.target_profiles.pikpak.archive.remote" value="' + esc(archive.remote || '') + '"></label>'
      + '<label><span>' + t('settings.pikpakArchiveSource') + '</span><input type="text" name="global.target_profiles.pikpak.archive.source_directory" value="' + esc(archive.source_directory || '') + '"></label>'
      + '<label><span>' + t('settings.pikpakArchiveRoot') + '</span><input type="text" name="global.target_profiles.pikpak.archive.root_directory" value="' + esc(archive.root_directory || '') + '"></label>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">'
      + '<label><span>' + t('settings.pikpakArchivePoll') + '</span><input type="number" name="global.target_profiles.pikpak.archive.poll_seconds" value="' + esc(archive.poll_seconds || '') + '" min="0"></label>'
      + '<label><span>' + t('settings.pikpakArchiveInterval') + '</span><input type="number" name="global.target_profiles.pikpak.archive.poll_interval_seconds" value="' + esc(archive.poll_interval_seconds || '') + '" min="0"></label>'
      + '</div>'
      + '<label><span>' + t('settings.pikpakArchiveWindow') + '</span><input type="number" name="global.target_profiles.pikpak.archive.match_window_seconds" value="' + esc(archive.match_window_seconds || '') + '" min="0"></label>';

    // Account & Proxy
    $('#mob-settings-sensitive-fields').innerHTML =
      '<label><span>API ID</span><input type="text" name="user.api_id" value="' + esc(user.api_id || '') + '"></label>'
      + sensitiveKeys.map(function(k) {
        var v = getPath(user, getSettingLeafKey(k));
        return '<label><span>' + esc(k) + '</span><input type="password" name="user.' + esc(k) + '" placeholder="' + (v && v.configured ? t('settings.secretConfigured') : t('settings.secretNotConfigured')) + '" autocomplete="new-password"></label>';
      }).join('');

    // Download Types
    $('#mob-settings-download-types-fields').innerHTML = renderCheckCards('user.download_type', downloadTypes, selectedDownload);

    // Forward Types
    $('#mob-settings-forward-types-fields').innerHTML = renderCheckCards('global.forward_type', forwardTypes, selectedForward(glob));

    // Message Filter
    var mf = glob.message_filter || {};
    var mfMediaTypes = (state.schema.message_filter && state.schema.message_filter.media_types) || forwardTypes;
    var mfDateRange = mf.date_range || {};
    var mfKeywords = mf.keywords || {};
    var mfDateStart = mfDateRange.start_date ? new Date(mfDateRange.start_date * 1000).toISOString().slice(0, 16) : '';
    var mfDateEnd = mfDateRange.end_date ? new Date(mfDateRange.end_date * 1000).toISOString().slice(0, 16) : '';
    var mfKwStr = Array.isArray(mfKeywords.words) ? mfKeywords.words.join(', ') : '';
    $('#mob-settings-message-filter-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.enabled" style="width:auto;min-height:auto;"' + (mf.enabled !== false ? ' checked' : '') + '><span>' + t('settings.enabled') + '</span></label>'
      + '<div class="mob-subsection"><h4>' + t('settings.mediaTypes') + '</h4>'
      + renderCheckCards('global.message_filter.media_types', mfMediaTypes, selectedMediaTypes(glob))
      + '</div>'
      + '<div class="mob-subsection"><h4>' + t('settings.dateRange') + '</h4>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.date_range.enabled" style="width:auto;min-height:auto;"' + (mfDateRange.enabled ? ' checked' : '') + '><span>' + t('settings.enabled') + '</span></label>'
      + '<div class="field-grid field-grid--two" style="margin-top:8px">'
      + '<label class="field"><span>' + t('settings.startDate') + '</span><input name="global.message_filter.date_range.start_date" type="datetime-local" value="' + escAttr(mfDateStart) + '"></label>'
      + '<label class="field"><span>' + t('settings.endDate') + '</span><input name="global.message_filter.date_range.end_date" type="datetime-local" value="' + escAttr(mfDateEnd) + '"></label>'
      + '</div></div>'
      + '<div class="mob-subsection"><h4>' + t('settings.keywords') + '</h4>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.message_filter.keywords.enabled" style="width:auto;min-height:auto;"' + (mfKeywords.enabled ? ' checked' : '') + '><span>' + t('settings.enabled') + '</span></label>'
      + '<label class="field" style="margin-top:8px"><span>' + t('settings.keywordList') + '</span><input name="global.message_filter.keywords.words" value="' + escAttr(mfKwStr) + '" placeholder="' + t('settings.keywordPlaceholder') + '"></label>'
      + '</div>';

    // Export Tables
    $('#mob-settings-exports-fields').innerHTML =
      '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.link" style="width:auto;min-height:auto;"' + (exportTable.link ? ' checked' : '') + '><span>' + t('settings.exportLink') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.count" style="width:auto;min-height:auto;"' + (exportTable.count ? ' checked' : '') + '><span>' + t('settings.exportCount') + '</span></label>'
      + '<label style="flex-direction:row;align-items:center;gap:8px;"><input type="checkbox" name="global.export_table.upload" style="width:auto;min-height:auto;"' + (exportTable.upload ? ' checked' : '') + '><span>' + t('settings.exportUpload') + '</span></label>';
  }

  function getSettingLeafKey(key) {
    return key;
  }

  function selectedForward(glob) {
    var ft = glob.forward_type || {};
    var result = [];
    for (var k in ft) { if (ft[k]) result.push(k); }
    return result;
  }

  function selectedMediaTypes(glob) {
    var mf = glob.message_filter || {};
    var mt = mf.media_types || glob.forward_type || {};
    var result = [];
    for (var k in mt) { if (mt[k]) result.push(k); }
    return result;
  }

  function escAttr(value) {
    return String(value || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function renderCheckCards(baseName, types, selected) {
    return types.map(function(type) {
      return '<label style="flex-direction:row;align-items:center;gap:8px;padding:6px 0;"><input type="checkbox" name="' + baseName + '" value="' + esc(type) + '" style="width:auto;min-height:auto;"' + (selected.indexOf(type) >= 0 ? ' checked' : '') + '><span>' + esc(type) + '</span></label>';
    }).join('');
  }

  /* ====== 覆盖：renderTasks / loadTasks / loadWatches / loadSettings ====== */
  var _origRenderTasks = renderTasks;
  renderTasks = function() {
    try { _origRenderTasks(); } catch(e) {}
    if (state.tasks) renderMobTasks();
  };
  var _origLoadTasks = loadTasks;
  loadTasks = async function() {
    try { await _origLoadTasks(); } catch(e) {}
    if (state.tasks) renderMobTasks();
  };

  var _origLoadWatches = loadWatches;
  loadWatches = async function() {
    try { await _origLoadWatches(); } catch(e) {}
    if (state.watches) renderMobWatches();
  };
  var _origRenderWatches = renderWatches;
  renderWatches = function() {
    try { _origRenderWatches(); } catch(e) {}
    if (state.watches) renderMobWatches();
  };

  var _origLoadSettings = loadSettings;
  loadSettings = async function() {
    try { await _origLoadSettings(); } catch(e) {}
    renderMobSettingsForm();
  };

  /* ====== 事件绑定 ====== */
  $('#language-select').addEventListener('change', function(event) {
    state.lang = event.target.value;
    localStorage.setItem('trmd-lang', state.lang);
    applyLanguageAndRefresh();
    renderMobTasks();
    renderMobWatches();
    renderMobRecords();
    renderMobStatistics();
    renderMobSettingsForm();
  });

  $('#refresh').addEventListener('click', function() {
    loadTasks();
    var activeView = document.querySelector('.mob-view.active');
    if (activeView) {
      var viewId = activeView.id.replace('mob-view-', '');
      if (viewId === 'settings') loadSettings();
      if (viewId === 'watches') loadWatches();
    }
    showToast(t('action.refresh') + ' OK');
  });

  /* Tab 栏点击 */
  $$('.mob-tab').forEach(function(tab) {
    tab.addEventListener('click', function() { mobSwitchView(tab.dataset.mobNav); });
  });

  /* "更多"按钮 -> 打开 Drawer */
  var moreTab = document.querySelector('.mob-tab[data-mob-nav="more"]');
  if (moreTab) moreTab.addEventListener('click', openDrawer);

  /* Drawer 内菜单项点击 */
  $$('[data-mob-drawer-nav]').forEach(function(item) {
    item.addEventListener('click', function() { mobSwitchView(item.dataset.mobDrawerNav); });
  });

  /* Drawer overlay 点击关闭 */
  $('#mob-drawer-overlay').addEventListener('click', function(e) {
    if (e.target === this) closeDrawer();
  });

  /* FAB 点击 */
  $('#mob-fab').addEventListener('click', toggleFabMenu);

  /* FAB 菜单项 */
  $('#mob-fab-new-transfer').addEventListener('click', function() {
    closeFabMenu();
    var collapse = $('#collapse-transfer-form');
    collapse.classList.add('open');
    collapse.scrollIntoView({ behavior: 'smooth' });
  });
  $('#mob-fab-new-watch').addEventListener('click', function() {
    closeFabMenu();
    mobSwitchView('watches');
    var collapse = $('#collapse-watch-form');
    collapse.classList.add('open');
    collapse.scrollIntoView({ behavior: 'smooth' });
  });

  /* 折叠面板切换 */
  $$('.mob-collapse__head').forEach(function(head) {
    head.addEventListener('click', function() { toggleCollapse(head); });
  });

  /* 点击外部关闭 FAB 菜单 */
  document.addEventListener('click', function(e) {
    if (!e.target.closest('#mob-fab') && !e.target.closest('#mob-fab-menu')) {
      closeFabMenu();
    }
  });

  /* 监听类型切换 */
  var watchTypeSelect = $('#mob-watch-type');
  if (watchTypeSelect) {
    watchTypeSelect.addEventListener('change', function() {
      var isForward = this.value === 'forward';
      var textarea = document.querySelector('#mob-watch-source-group textarea[name="source_links"]');
      var input = document.querySelector('#mob-watch-source-group input[name="source_link"]');
      var sourceLabel = $('#mob-watch-source-label').querySelector('span');
      if (isForward) {
        if (textarea) { textarea.style.display = 'none'; textarea.required = false; }
        if (input) { input.style.display = ''; input.required = true; }
        if (sourceLabel) sourceLabel.textContent = t('watches.source');
      } else {
        if (textarea) { textarea.style.display = ''; textarea.required = true; }
        if (input) { input.style.display = 'none'; input.required = false; }
        if (sourceLabel) sourceLabel.textContent = t('watches.sources');
      }
      $('#mob-watch-target-group').style.display = isForward ? '' : 'none';
      $('#mob-watch-comment-group').style.display = isForward ? '' : 'none';
    });
  }

  /* 新建转存表单提交 */
  var transferForm = $('#mob-transfer-form');
  if (transferForm) {
    transferForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
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
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 新建监听表单提交 */
  var watchForm = $('#mob-watch-form');
  if (watchForm) {
    watchForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      var isForward = payload.type === 'forward';
      if (isForward) {
        delete payload.source_links;
        payload.include_comment = !!payload.include_comment;
      } else {
        delete payload.source_link;
        delete payload.target_link;
        delete payload.include_comment;
        payload.source_links = String(payload.source_links || '').split('\n').map(function(s) { return s.trim(); }).filter(Boolean);
      }
      try {
        await postJson('/api/watches', payload);
        showToast(t('watches.created'));
        this.reset();
        $('#collapse-watch-form').classList.remove('open');
        loadWatches();
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 保存设置 */
  var saveBtn = $('#mob-save-settings');
  if (saveBtn) {
    saveBtn.addEventListener('click', async function() {
      var userPayload = {};
      var globalPayload = {};
      var downloadTypes = [];

      // 收集所有设置区域的 input
      var allInputs = document.querySelectorAll('#mob-settings-path-fields input, #mob-settings-behavior-fields input, #mob-settings-sensitive-fields input, #mob-settings-archive-fields input, #mob-settings-download-types-fields input, #mob-settings-forward-types-fields input, #mob-settings-message-filter-fields input, #mob-settings-exports-fields input');

      allInputs.forEach(function(input) {
        var name = input.name || '';
        if (!name) return;
        var value;
        if (input.type === 'checkbox') {
          value = input.checked;
        } else if (input.type === 'number') {
          value = input.value === '' ? null : Number(input.value);
        } else if (input.type === 'password' && input.value === '') {
          return;
        } else {
          value = input.value;
        }

        // 收集 download_type 多选
        if (name === 'user.download_type' && input.type === 'checkbox' && input.checked) {
          downloadTypes.push(input.value);
          return;
        }
        // 收集 forward_type 多选
        if (name === 'global.forward_type' && input.type === 'checkbox') {
          setPath(globalPayload, 'forward_type.' + input.value, input.checked);
          return;
        }
        // 消息过滤 — 日期范围：datetime-local → timestamp
        if (name === 'global.message_filter.date_range.start_date' || name === 'global.message_filter.date_range.end_date') {
          var ts = input.value ? (new Date(input.value).getTime() / 1000) : null;
          setPath(globalPayload, name.substring(7), ts);
          return;
        }
        // 消息过滤 — 关键词：逗号分隔字符串 → 数组
        if (name === 'global.message_filter.keywords.words') {
          var words = input.value ? input.value.split(',').map(function(s) { return s.trim(); }).filter(Boolean) : [];
          setPath(globalPayload, name.substring(7), words);
          return;
        }

        if (name.startsWith('user.')) {
          setPath(userPayload, name.substring(5), value);
        } else if (name.startsWith('global.')) {
          setPath(globalPayload, name.substring(7), value);
        }
      });

      setPath(userPayload, 'download_type', downloadTypes);

      try {
        await postJson('/api/settings', { user: userPayload, global: globalPayload });
        showToast(t('settings.saved'));
        loadSettings();
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* ====== Phase 2: 频道下载 ====== */
  function renderMobRecords() {
    var records = state.records || [];
    var container = $('#mob-records-list');
    if (!records.length) {
      container.innerHTML = '<div class="mob-empty" data-i18n="records.empty">' + t('records.empty') + '</div>';
      return;
    }
    container.innerHTML = records.map(function(r) {
      return '<div class="mob-card">'
        + '<div class="mob-card__head"><span class="mob-card__title">' + esc(r.file_name || r.local_path || '') + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.chat') + '</span><span>' + esc(r.source_chat_id || '-') + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.message') + '</span><span>' + esc(r.source_message_id || '-') + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.size') + '</span><span>' + formatBytes(r.file_size) + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('records.updated') + '</span><span>' + esc(r.updated_at || r.downloaded_at || '') + '</span></div>'
        + '</div>';
    }).join('');
  }

  /* ====== Phase 2: 统计表格 ====== */
  function renderMobStatistics() {
    var stats = state.statistics;
    var container = $('#mob-statistics-list');
    if (!stats || !stats.tables) {
      container.innerHTML = '<div class="mob-empty">' + t('tasks.empty') + '</div>';
      return;
    }
    var tables = stats.tables;
    var html = '';
    var tableNames = { link: t('statistics.link'), count: t('statistics.count'), upload: t('statistics.upload') };
    for (var key in tables) {
      if (!tables.hasOwnProperty(key)) continue;
      var tbl = tables[key];
      html += '<div class="mob-card" style="margin-bottom:10px;">'
        + '<div class="mob-card__row"><span class="label">' + (tableNames[key] || key) + '</span><span>' + t('statistics.available') + ': ' + (tbl.available ? t('statistics.yes') : t('statistics.no')) + '</span></div>'
        + '<div class="mob-card__row"><span class="label">' + t('statistics.rows') + '</span><span>' + (tbl.rows || 0) + '</span></div>'
        + '</div>';
    }
    container.innerHTML = html || '<div class="mob-empty">' + t('tasks.empty') + '</div>';
  }

  /* ====== 覆盖 loadRecords / renderRecords / loadStatistics ====== */
  var _origLoadRecords = loadRecords;
  loadRecords = async function() {
    try { await _origLoadRecords(); } catch(e) {}
    renderMobRecords();
  };
  var _origRenderRecords = renderRecords;
  renderRecords = function() {
    try { _origRenderRecords(); } catch(e) {}
    renderMobRecords();
  };
  var _origLoadStatistics = loadStatistics;
  loadStatistics = async function() {
    try { await _origLoadStatistics(); } catch(e) {}
    renderMobStatistics();
  };

  /* ====== Phase 2 事件绑定 ====== */

  /* 频道下载表单 */
  var channelForm = $('#mob-channel-form');
  if (channelForm) {
    channelForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      payload.include_comment = !!payload.include_comment;
      if (payload.start_date) {
        payload.date_range = { start_date: new Date(payload.start_date).getTime() / 1000 };
        delete payload.start_date;
      }
      if (payload.end_date) {
        payload.date_range = payload.date_range || {};
        payload.date_range.end_date = new Date(payload.end_date).getTime() / 1000;
        delete payload.end_date;
      }
      if (payload.keywords) {
        payload.keywords = String(payload.keywords).split(',').map(function(s) { return s.trim(); }).filter(Boolean);
      } else {
        payload.keywords = [];
      }
      payload.download_type = Array.from(document.querySelectorAll('#mob-channel-download-types input[name="download_type"]:checked')).map(function(el) { return el.value; });
      try {
        await postJson('/api/channel-downloads', payload);
        showToast(t('channel.accepted'));
        this.reset();
        $('#collapse-channel-form').classList.remove('open');
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 本地上传表单 */
  var uploadForm = $('#mob-upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      var form = new FormData(this);
      var payload = Object.fromEntries(form.entries());
      payload.recursive = !!payload.recursive;
      try {
        await postJson('/api/uploads', payload);
        showToast(t('uploads.accepted'));
        this.reset();
        $('#collapse-upload-form').classList.remove('open');
      } catch (err) {
        showToast(translateApiError(err, 'form.requestFailed'));
      }
    });
  }

  /* 统计导出 */
  /* 已通过 loadStatistics 覆盖自动渲染 */

  /* ====== 初始加载（由 checkAuthStatus 驱动） ====== */
