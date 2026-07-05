# coding=UTF-8
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.web_ui_assets import WEB_UI_HTML, WEB_UI_MOBILE_HTML, LOGIN_PAGE_HTML, panel_head


class WebUiAssetsCase(unittest.TestCase):
    def test_desktop_html_has_correct_structure(self):
        self.assertIn('<!doctype html>', WEB_UI_HTML.lower())
        self.assertIn('<html lang="zh-CN">', WEB_UI_HTML)
        self.assertIn('TRMD', WEB_UI_HTML)
        # Sidebar nav items
        self.assertIn('data-nav="transfers"', WEB_UI_HTML)
        self.assertIn('data-nav="watches"', WEB_UI_HTML)
        self.assertIn('data-nav="channel-downloads"', WEB_UI_HTML)
        self.assertIn('data-nav="uploads"', WEB_UI_HTML)
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
        self.assertIn('id="tasks-tbody"', WEB_UI_HTML)
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
            'channel.title', 'uploads.title',
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
        self.assertIn('#2563EB', LOGIN_PAGE_HTML)
        self.assertIn('id="login-form"', LOGIN_PAGE_HTML)
        self.assertIn('id="username"', LOGIN_PAGE_HTML)
        self.assertIn('id="password"', LOGIN_PAGE_HTML)
        self.assertIn('/api/auth/login', LOGIN_PAGE_HTML)

    def test_mobile_html_preserved(self):
        self.assertIn('<!doctype html>', WEB_UI_MOBILE_HTML.lower())
        self.assertIn('mob-topbar', WEB_UI_MOBILE_HTML)
        self.assertIn('mob-tabbar', WEB_UI_MOBILE_HTML)
        # Blue color should be present
        self.assertIn('#2563EB', WEB_UI_MOBILE_HTML)

    def test_panel_head_function_still_works(self):
        result = panel_head(
            title_i18n='test.title',
            title_text='Test Title',
            meta_i18n='test.meta',
            meta_text='Test Meta',
            meta_id='test-id',
            indent=12
        )
        self.assertIn('data-component="panel-head"', result)
        self.assertIn('data-i18n="test.title"', result)
        self.assertIn('Test Title', result)
        self.assertIn('id="test-id"', result)

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

    def test_refresh_and_language_controls(self):
        self.assertIn('id="refresh"', WEB_UI_HTML)
        self.assertIn('id="language-select"', WEB_UI_HTML)

    def test_view_switching_js(self):
        self.assertIn('function switchView', WEB_UI_HTML)

    def test_polling_js(self):
        self.assertIn('function startPolling', WEB_UI_HTML)
        self.assertIn('hasActiveTasks', WEB_UI_HTML)

    def test_auth_flow_js(self):
        self.assertIn('function checkAuthStatus', WEB_UI_HTML)
        self.assertIn('showLoginStep', WEB_UI_HTML)


if __name__ == '__main__':
    unittest.main()
