# coding=UTF-8
import sys
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.web_ui_assets import WEB_UI_HTML, WEB_UI_MOBILE_HTML, LOGIN_PAGE_HTML


class WebUiAssetsCase(unittest.TestCase):
    def test_desktop_html_has_correct_structure(self):
        self.assertIn('<!doctype html>', WEB_UI_HTML.lower())
        self.assertIn('<html lang="zh-CN">', WEB_UI_HTML)
        self.assertIn('TRMD', WEB_UI_HTML)
        # Sidebar nav items
        self.assertIn('data-nav="transfers"', WEB_UI_HTML)
        self.assertIn('data-nav="watches"', WEB_UI_HTML)
        self.assertIn('data-nav="downloads-uploads"', WEB_UI_HTML)
        self.assertIn('data-nav="statistics"', WEB_UI_HTML)
        self.assertIn('data-nav="settings"', WEB_UI_HTML)
        self.assertIn('data-nav="records"', WEB_UI_HTML)
        self.assertIn('data-nav="media"', WEB_UI_HTML)
        # Language selector
        self.assertIn('id="language-select"', WEB_UI_HTML)
        # i18n
        self.assertIn('data-i18n="nav.transfers"', WEB_UI_HTML)
        self.assertIn('data-i18n="nav.settings"', WEB_UI_HTML)
        # Views
        self.assertIn('id="view-transfers"', WEB_UI_HTML)
        self.assertIn('id="view-watches"', WEB_UI_HTML)
        self.assertIn('id="view-settings"', WEB_UI_HTML)
        # Forms
        self.assertIn('id="transfer-form"', WEB_UI_HTML)
        self.assertIn('id="watch-download-form"', WEB_UI_HTML)
        self.assertIn('id="watch-forward-form"', WEB_UI_HTML)
        self.assertIn('id="channel-download-form"', WEB_UI_HTML)
        self.assertIn('id="upload-form"', WEB_UI_HTML)
        # Task list
        self.assertIn('id="tasks-list"', WEB_UI_HTML)
        # Logout
        self.assertIn('id="btn-logout"', WEB_UI_HTML)
        # Tailwind
        self.assertIn('tailwindcss', WEB_UI_HTML)

    def test_desktop_html_has_api_endpoints(self):
        for endpoint in (
            '/api/tasks',
            '/api/watches',
            '/api/settings',
            '/api/auth/status',
            '/api/auth/logout',
            '/api/auth/submit',
            '/api/channel-downloads',
            '/api/uploads',
            '/api/statistics',
            '/api/download-records',
            '/api/media/scan',
            '/api/media/cleanup',
            '/api/media/cleanup-logs',
            '/api/tables/export',
            '/api/system-logs/export',
        ):
            self.assertIn(endpoint, WEB_UI_HTML)
        # /api/auth/login is only in the standalone login page
        self.assertIn('/api/auth/login', LOGIN_PAGE_HTML)

    def test_i18n_complete_coverage(self):
        for key in (
            'nav.transfers', 'nav.watches', 'nav.settings',
            'new.title', 'new.source', 'new.target', 'new.create',
            'tasks.title', 'tasks.empty', 'tasks.pause', 'tasks.resume',
            'watches.title', 'watches.download', 'watches.forward',
            'nav.downloadsUploads', 'dl.title', 'dl.uploadTitle',
            'statistics.title', 'records.title', 'media.title',
            'settings.title', 'settings.save', 'settings.saved',
            'form.createFailed', 'form.createSuccess', 'form.creatingTransfer',
            'status.pending', 'status.running', 'status.success', 'status.failure',
            'action.refresh', 'nav.logout',
            'side.failed', 'side.status',
        ):
            self.assertIn(key, WEB_UI_HTML)

    def test_login_page_has_blue_theme(self):
        self.assertIn('<!doctype html>', LOGIN_PAGE_HTML.lower())
        self.assertIn('登录控制台', LOGIN_PAGE_HTML)
        self.assertIn('#2563eb', LOGIN_PAGE_HTML.lower())
        self.assertIn('id="login-form"', LOGIN_PAGE_HTML)
        self.assertIn('id="username"', LOGIN_PAGE_HTML)
        self.assertIn('id="password"', LOGIN_PAGE_HTML)
        self.assertIn('/api/auth/login', LOGIN_PAGE_HTML)

    def test_login_page_layout_prevents_mobile_shrink(self):
        self.assertIn('.login-page{background-color:var(--color-bg);width:100%;', LOGIN_PAGE_HTML)
        self.assertIn('flex:1;justify-content:center;align-items:center;display:flex', LOGIN_PAGE_HTML)
        self.assertIn('.login-page{min-height:100svh}', LOGIN_PAGE_HTML)
        self.assertIn('.login-card{', LOGIN_PAGE_HTML)
        self.assertIn('width:100%;max-width:420px', LOGIN_PAGE_HTML)
        self.assertIn('login-page login-overlay hidden', WEB_UI_HTML)
        self.assertIn('.login-overlay{', WEB_UI_HTML)
        self.assertIn('position:fixed', WEB_UI_HTML)

    def test_mobile_login_layout_has_stable_touch_controls(self):
        self.assertIn('--safe-bottom:env(safe-area-inset-bottom,0px)', WEB_UI_MOBILE_HTML)
        self.assertIn('.mob-login-card{', WEB_UI_MOBILE_HTML)
        self.assertIn('width:100%;max-width:400px', WEB_UI_MOBILE_HTML)
        self.assertIn(
            '.mob-login-actions{grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;display:grid',
            WEB_UI_MOBILE_HTML
        )
        self.assertIn(
            '.mob-login-submit svg{flex-shrink:0;width:18px;height:18px}',
            WEB_UI_MOBILE_HTML
        )

    def test_mobile_html_preserved(self):
        self.assertIn('<!doctype html>', WEB_UI_MOBILE_HTML.lower())
        self.assertIn('mob-topbar', WEB_UI_MOBILE_HTML)
        self.assertIn('mob-tabbar', WEB_UI_MOBILE_HTML)
        # Blue color should be present
        self.assertIn('#2563eb', WEB_UI_MOBILE_HTML.lower())

    def test_mobile_layout_has_stable_full_width_panels(self):
        for fragment in (
            '.mob-body{font-family:var(--font-mob);',
            'width:100%;min-height:100svh;',
            'display:block;overflow-x:hidden',
            '.mob-content{box-sizing:border-box;flex-direction:column;gap:10px;width:100%;min-width:0;max-width:100%',
            '.mob-collapse{border:1px solid var(--color-line);background:var(--color-surface);box-sizing:border-box;border-radius:10px;width:100%;min-width:0;max-width:100%',
            '.mob-card{background:var(--color-surface);border:1px solid var(--color-line);border-left:3px solid var(--color-line);box-sizing:border-box;cursor:pointer;border-radius:10px;width:100%;max-width:100%',
            '#mob-tasks-list,#mob-watches-list,#mob-operations-list,#mob-statistics-list,#mob-records-list,#mob-media-result,#mob-profile-menu{width:100%;min-width:0;max-width:100%',
        ):
            self.assertIn(fragment, WEB_UI_MOBILE_HTML)

    def test_mobile_uses_api_loading_instead_of_persistent_loading_placeholders(self):
        for fragment in (
            'window.state = state;',
            "if (id === 'mob-view-transfers') {",
            "await loadMobileTasks();",
            "await refreshOpenTaskSheet();",
            "else if (id === 'mob-view-watches') { await loadMobileWatches(); }",
            "else if (id === 'mob-view-downloads-uploads') { await loadMobileDownloadsUploads(); }",
            "if (view === 'transfers') { loadMobileTasks(); }",
            "else if (view === 'watches') { loadMobileWatches(); }",
            "else if (view === 'downloads-uploads') { loadMobileDownloadsUploads(); }",
            "var data = await fetchJson('/api/tasks');",
            "var data = await fetchJson('/api/watches');",
            "mobileSettingsLoadPromise = fetchJson('/api/settings').then(function(data)",
            "container.innerHTML = mobEmptyHtml('还没有转存任务。', 'tasks.empty');",
            "container.innerHTML = mobEmptyHtml('还没有实时监听。', 'watches.empty');",
        ):
            self.assertIn(fragment, WEB_UI_MOBILE_HTML)

    def test_settings_view_exposes_pikpak_archive(self):
        for fragment in (
            'global.target_profiles.pikpak.archive.enable',
            'global.target_profiles.pikpak.archive.remote',
            'settings.pikpakArchive',
            'settings.pikpakArchiveEnable',
        ):
            self.assertIn(fragment, WEB_UI_HTML)

    def test_include_comment_checkboxes_present(self):
        self.assertIn('name="include_comment"', WEB_UI_HTML)
        # At least 3 appearances: transfer form, watch forward form, channel download
        count = WEB_UI_HTML.count('name="include_comment"')
        self.assertGreaterEqual(count, 3)

    def test_watch_create_buttons_are_default_aligned(self):
        self.assertIn('form-input watch-download-sources', WEB_UI_HTML)
        self.assertIn('.watch-download-sources{', WEB_UI_HTML)
        self.assertIn('min-height:124px', WEB_UI_HTML)
        self.assertIn('resize:vertical', WEB_UI_HTML)

    def test_download_upload_create_buttons_are_default_aligned(self):
        self.assertIn('download-upload-align-spacer', WEB_UI_HTML)
        self.assertIn('data-i18n="dl.uploadPlaceholder"', WEB_UI_HTML)
        self.assertIn('占位区，待后续开发', WEB_UI_HTML)
        self.assertIn('--tw-border-style:dashed;border-style:dashed', WEB_UI_HTML)
        self.assertIn('@media (min-width:64rem){.download-upload-align-spacer{min-height:184px}', WEB_UI_HTML)

    def test_message_filter_settings_present(self):
        for fragment in (
            'global.message_filter.enabled',
            'global.message_filter.date_range',
            'global.message_filter.keywords',
            'settings.messageFilter',
            'settings.mediaTypes',
        ):
            self.assertIn(fragment, WEB_UI_HTML)

    def test_export_tables_present(self):
        for fragment in (
            'global.export_table.link',
            'global.export_table.count',
            'global.export_table.upload',
        ):
            self.assertIn(fragment, WEB_UI_HTML)

    def test_no_old_green_accent_in_desktop(self):
        # Desktop uses new blue theme
        self.assertNotIn('#0f8f72', WEB_UI_HTML)

    def test_stat_cards_present(self):
        self.assertIn('stat-total', WEB_UI_HTML)
        self.assertIn('stat-success', WEB_UI_HTML)
        self.assertIn('stat-running', WEB_UI_HTML)
        self.assertIn('stat-failed', WEB_UI_HTML)

    def test_statistics_dashboard_present(self):
        for fragment in (
            'stats-kpi-grid',
            'stats-chart-grid',
            'statistics-tabs',
            'statistics-export-btn',
            'renderStatisticsDashboard',
        ):
            self.assertIn(fragment, WEB_UI_HTML)

    def test_refresh_and_language_controls(self):
        self.assertIn('id="refresh"', WEB_UI_HTML)
        self.assertIn('id="language-select"', WEB_UI_HTML)

    def test_view_switching_js(self):
        self.assertIn('function switchView', WEB_UI_HTML)

    def test_polling_js(self):
        self.assertIn('function startPolling', WEB_UI_HTML)
        self.assertIn('hasActiveTasks', WEB_UI_HTML)

    def test_task_detail_progress_refreshes_without_manual_page_reload(self):
        self.assertIn('function refreshSelectedTaskDetail', WEB_UI_HTML)
        self.assertIn('function refreshTransferData', WEB_UI_HTML)
        self.assertIn('refreshTransferData();', WEB_UI_HTML)
        self.assertIn('case \'pending\':', WEB_UI_HTML)
        self.assertIn('startPolling();', WEB_UI_HTML)
        self.assertIn('refreshSelectedTaskDetail();', WEB_UI_HTML)
        self.assertIn("{ silent: true })", WEB_UI_HTML)
        self.assertIn("return t.status === 'pending' || t.status === 'running';", WEB_UI_MOBILE_HTML)
        self.assertIn('function refreshOpenTaskSheet', WEB_UI_MOBILE_HTML)
        self.assertIn('refreshOpenTaskSheet();', WEB_UI_MOBILE_HTML)

    def test_task_items_table_uses_single_line_columns_except_file(self):
        header = (
            '<th class="task-item-file">文件</th><th class="task-item-size">大小</th>'
            '<th class="task-item-progress">进度/速度</th><th class="task-item-source">来源</th>'
            '<th class="task-item-status">状态</th>'
        )
        self.assertIn(header, WEB_UI_HTML)
        self.assertNotIn('<th>文件</th><th>大小</th><th>进度/速度</th><th>来源</th><th>目标</th><th>状态</th>', WEB_UI_HTML)
        self.assertIn('.task-items-table{', WEB_UI_HTML)
        self.assertIn('min-width:840px', WEB_UI_HTML)
        self.assertIn('table-layout:fixed', WEB_UI_HTML)
        self.assertIn('.task-items-table .task-item-col-size{width:112px}', WEB_UI_HTML)
        self.assertIn('.task-items-table .task-item-col-status{width:118px}', WEB_UI_HTML)
        self.assertIn('overflow-wrap:anywhere', WEB_UI_HTML)

    def test_auth_flow_js(self):
        self.assertIn('function checkAuthStatus', WEB_UI_HTML)
        self.assertIn('showLoginStep', WEB_UI_HTML)

    def test_media_scan_has_visible_feedback(self):
        self.assertIn("setMediaScanButtonLoading(true);", WEB_UI_HTML)
        self.assertIn("container.classList.remove('hidden');", WEB_UI_HTML)
        self.assertIn("container.classList.add('hidden');", WEB_UI_HTML)
        self.assertIn("renderMediaError", WEB_UI_HTML)
        self.assertIn("t('media.scanning')", WEB_UI_HTML)

    def test_media_cleanup_button_stays_in_header(self):
        self.assertIn('id="media-actions"', WEB_UI_HTML)
        self.assertIn('id="media-cleanup-btn"', WEB_UI_HTML)
        self.assertIn('disabled data-i18n="media.cleanup"', WEB_UI_HTML)
        self.assertIn("function updateMediaCleanupButton", WEB_UI_HTML)
        self.assertIn("document.addEventListener('change', function(e) {", WEB_UI_HTML)
        self.assertNotIn('id="media-cleanup-actions"', WEB_UI_HTML)

    def test_webui_session_expiry_redirects_to_login_page(self):
        combined = WEB_UI_HTML + WEB_UI_MOBILE_HTML
        self.assertIn('function redirectToLoginPage', combined)
        self.assertIn("if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }", combined)
        self.assertNotIn("if (e.error_code === 'auth_required') checkAuthStatus();", combined)
        self.assertIn("if (resp.status === 401) { redirectToLoginPage(); return; }", combined)

    def test_watches_detail_shell_present(self):
        self.assertIn('id="watch-detail-overlay"', WEB_UI_HTML)
        self.assertIn('id="watch-detail-body"', WEB_UI_HTML)
        self.assertIn('watch-detail-dialog', WEB_UI_HTML)
        self.assertIn('watch-detail-summary', WEB_UI_HTML)
        self.assertIn('WatchUiHelpers', WEB_UI_HTML)
        self.assertNotIn('id="watch-download-overlay"', WEB_UI_HTML)

    def test_watches_table_compact_headers(self):
        self.assertIn('data-i18n="watches.type"', WEB_UI_HTML)
        self.assertIn('data-i18n="watches.source"', WEB_UI_HTML)
        self.assertIn('data-i18n="watches.target"', WEB_UI_HTML)
        self.assertIn('data-i18n="watches.todayEvents"', WEB_UI_HTML)
        self.assertIn('data-i18n="watches.totalEvents"', WEB_UI_HTML)
        self.assertIn('data-watch-menu', WEB_UI_HTML)
        self.assertIn('watches.badgeSuccess', WEB_UI_HTML)

    def test_desktop_and_mobile_use_unified_webui_contract(self):
        combined = WEB_UI_HTML + WEB_UI_MOBILE_HTML
        self.assertIn('completed_items', WEB_UI_HTML)
        self.assertIn('completed_items', WEB_UI_MOBILE_HTML)
        self.assertIn('progress_percent', WEB_UI_HTML)
        self.assertIn('progress_percent', WEB_UI_MOBILE_HTML)
        self.assertIn('/api/tasks/', WEB_UI_HTML)
        self.assertIn('/api/tasks/', WEB_UI_MOBILE_HTML)
        for stale_field in ('success_count', 'failed_count', 'skipped_count'):
            self.assertNotIn(stale_field, combined)
        self.assertNotIn('global.download.types', combined)
        self.assertNotIn('global.forward.types', combined)
        self.assertNotIn('settings.downloadTypes ||', combined)


if __name__ == '__main__':
    unittest.main()
