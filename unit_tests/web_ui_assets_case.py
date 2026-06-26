# coding=UTF-8
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()

from module.web_ui_assets import WEB_UI_BODY, WEB_UI_HTML, panel_head


class WebUiAssetsCase(unittest.TestCase):
    def test_webui_has_bilingual_language_selector_settings_and_task_actions(self):
        self.assertIn('<html lang="zh-CN">', WEB_UI_HTML)
        self.assertIn('<title>TRMD 转存控制台</title>', WEB_UI_HTML)
        self.assertIn('aria-label="主导航"', WEB_UI_HTML)
        self.assertIn('id="language-select"', WEB_UI_HTML)
        self.assertIn('data-i18n="nav.settings"', WEB_UI_HTML)
        self.assertIn('data-view="settings"', WEB_UI_HTML)
        self.assertIn('data-i18n="tasks.delete"', WEB_UI_HTML)
        self.assertIn('deleteTask(', WEB_UI_HTML)
        self.assertIn('download_current', WEB_UI_HTML)
        self.assertIn('upload_current', WEB_UI_HTML)
        self.assertIn('PikPak 转存队列', WEB_UI_HTML)
        self.assertIn('PikPak transfer queue', WEB_UI_HTML)

    def test_webui_language_switch_covers_dynamic_ui_copy(self):
        for key in (
                'settings.secretConfigured',
                'settings.secretNotConfigured',
                'form.createFailed',
                'form.requestFailed',
                'form.creatingTransfer',
                'form.creatingTransferShort',
                'form.createSuccess',
                'new.optional',
                'language.label',
                'event.fileReady',
                'event.uploadFailed',
                'event.reusedDownload'
        ):
            self.assertIn(key, WEB_UI_HTML)

        for hardcoded_text in (
                "placeholder=\"configured / replace\"",
                "placeholder=\"optional\"",
                "data.error || 'Create task failed.'",
                "'configured / replace'",
                "'not configured'"
        ):
            self.assertNotIn(hardcoded_text, WEB_UI_HTML)

        self.assertIn('translateApiError(data,', WEB_UI_HTML)
        self.assertIn('localizeEventMessage(event)', WEB_UI_HTML)

    def test_transfer_form_shows_loading_and_success_feedback(self):
        for fragment in (
                "showFormMessage(t('form.creatingTransfer'), true);",
                "showFormMessage(t('form.createSuccess'), true);",
                "submitButton.disabled = true;",
                "submitLabel.textContent = t('form.creatingTransferShort');",
                "submitButton.disabled = false;",
                "submitLabel.textContent = previousLabel;",
                "formNotice.classList.add('is-visible');",
                "formNotice.classList.toggle('ok', ok);",
                ".form-error.ok,"
        ):
            self.assertIn(fragment, WEB_UI_HTML)

    def test_panel_heads_use_shared_component_and_stable_styles(self):
        expected_header = (
            '            <div class="panel-head" data-component="panel-head">\n'
            '              <h3 class="panel-head__title" data-i18n="tasks.title">转存任务</h3>\n'
            '              <div class="panel-head__meta" id="last-sync" data-i18n="tasks.notSynced">尚未同步</div>\n'
            '            </div>'
        )
        self.assertEqual(
            expected_header,
            panel_head(
                title_i18n='tasks.title',
                title_text='转存任务',
                meta_i18n='tasks.notSynced',
                meta_text='尚未同步',
                meta_id='last-sync',
                indent=12
            )
        )
        self.assertEqual(
            WEB_UI_BODY.count('class="panel-head"'),
            WEB_UI_BODY.count('data-component="panel-head"')
        )

        for css_fragment in (
                '--panel-head-min-height:',
                '.panel-head__title',
                '.panel-head__meta'
        ):
            self.assertIn(css_fragment, WEB_UI_HTML)

        self.assertNotIn('.panel-head h3', WEB_UI_HTML)
        self.assertNotIn('.panel-head span', WEB_UI_HTML)

    def test_settings_view_uses_unified_component_layout(self):
        for fragment in (
                'class="settings-layout"',
                'class="settings-section"',
                'class="settings-section__head"',
                'class="settings-section__body"',
                'class="field-grid"',
                'class="field"',
                'class="check-card"',
                'class="settings-actions"',
                'role="alert" aria-live="polite"'
        ):
            self.assertIn(fragment, WEB_UI_HTML)

        self.assertEqual(WEB_UI_BODY.count('class="settings-form"'), 1)
        self.assertNotIn('form, .settings-form', WEB_UI_HTML)
        self.assertIn('.settings-form {', WEB_UI_HTML)
        self.assertIn('min-height: var(--control-height);', WEB_UI_HTML)

    def test_webui_exposes_pikpak_archive_settings(self):
        for fragment in (
                'global.target_profiles.pikpak.archive.enable',
                'global.target_profiles.pikpak.archive.remote',
                'global.target_profiles.pikpak.archive.root_directory',
                'settings.pikpakArchiveEnable',
                'settings.pikpakArchiveRemote',
                'settings.pikpakArchiveRoot'
        ):
            self.assertIn(fragment, WEB_UI_HTML)

    def test_file_progress_has_status_tabs_and_independent_pagination(self):
        for fragment in (
                'role="tablist"',
                'data-item-tab="running"',
                'data-item-tab="success"',
                'data-item-tab="skipped"',
                'data-item-tab="failure"',
                'id="items-page-prev"',
                'id="items-page-next"',
                'id="items-page-summary"',
                'itemPages:',
                'activeItemStatus:',
                'function categorizedItems(',
                'function itemPageState(',
                'function switchItemTab(',
                'ITEMS_PAGE_SIZE = 10'
        ):
            self.assertIn(fragment, WEB_UI_HTML)

        for key in (
                'items.tab.running',
                'items.tab.success',
                'items.tab.skipped',
                'items.tab.failure',
                'items.empty.running',
                'items.empty.success',
                'items.empty.skipped',
                'items.empty.failure',
                'items.page.previous',
                'items.page.next',
                'items.page.status',
                'items.page.range'
        ):
            self.assertIn(key, WEB_UI_HTML)

        self.assertIn("['pending', 'running'].includes(status)", WEB_UI_HTML)
        self.assertIn("state.itemPages[state.activeItemStatus]", WEB_UI_HTML)

    def test_transfer_view_removes_legacy_forward_range_entry(self):
        for removed_fragment in (
                '原生转发范围',
                'id="forward-form"',
                'function createForward(',
                "'/api/forwards'",
                'data-i18n="forward.title"',
                'forward.accepted'
        ):
            self.assertNotIn(removed_fragment, WEB_UI_HTML)

        self.assertNotIn('<th data-i18n="tasks.updated">', WEB_UI_HTML)
        self.assertNotIn('<td class="mono">${esc(task.updated_at)}</td>', WEB_UI_HTML)
        self.assertIn('class="task-progress"', WEB_UI_HTML)
        self.assertIn('aria-label="${esc(progressLabel)}"', WEB_UI_HTML)

    def test_webui_integrates_help_command_workflows_as_structured_views(self):
        for fragment in (
                'data-nav="watches"',
                'data-nav="channel-downloads"',
                'data-nav="uploads"',
                'data-nav="statistics"',
                'id="watch-download-form"',
                'id="watch-forward-form"',
                'id="channel-download-form"',
                'id="upload-form"',
                'id="statistics"',
                'function loadWatches(',
                'function createDownloadWatch(',
                'function createForwardWatch(',
                'function deleteWatch(',
                'function createChannelDownload(',
                'function createUpload(',
                'function loadStatistics(',
                'function exportTable(',
                "fetch('/api/watches'",
                "fetch('/api/statistics'",
                "'/api/channel-downloads'",
                "'/api/uploads'",
                "'/api/tables/export'"
        ):
            self.assertIn(fragment, WEB_UI_HTML)

        for key in (
                'nav.watches',
                'nav.channelDownloads',
                'nav.uploads',
                'nav.statistics',
                'watches.title',
                'watches.downloadTitle',
                'watches.forwardTitle',
                'channel.title',
                'uploads.title',
                'uploads.serverPathHint',
                'statistics.title',
                'statistics.exportLink',
                'statistics.exportCount',
                'statistics.exportUpload',
                'error.watch_source_conflict',
                'error.upload_path_not_found',
                'error.invalid_table_type'
        ):
            self.assertIn(key, WEB_UI_HTML)

        self.assertNotIn('/exit', WEB_UI_HTML)
        self.assertNotIn('send bot command', WEB_UI_HTML.lower())

    def test_webui_exposes_discussion_reply_options_for_transfers_and_forward_watches(self):
        for fragment in (
                'name="include_comment"',
                'id="transfer-include-comment"',
                'id="watch-forward-include-comment"',
                'new.includeComment',
                'watches.includeComment',
                'include_comment: Boolean(form.get',
                'include_comment: Boolean(form.get(\'include_comment\'))'
        ):
            self.assertIn(fragment, WEB_UI_HTML)

        self.assertGreaterEqual(WEB_UI_HTML.count('name="include_comment"'), 3)

    def test_live_watch_forms_use_equal_height_panels_and_compact_checks(self):
        for fragment in (
                '.operation-grid {\n    display: grid;\n'
                '    grid-template-columns: repeat(2, minmax(0, 1fr));\n'
                '    gap: 18px;\n'
                '    align-items: stretch;',
                '.operation-grid > section,\n  .workspace > section {\n'
                '    display: flex;\n'
                '    flex-direction: column;',
                '.operation-grid > section > form {\n    flex: 1;',
                '.operation-grid > section > form > .actions {\n'
                '    margin-top: auto;',
                'id="watch-forward-include-comment"',
                '.check {\n    min-height: 24px;\n'
                '    display: inline-flex;',
                'min-height: 24px;',
                '.check input {\n    width: 16px;\n'
                '    height: 16px;\n'
                '    min-height: 0;\n'
                '    padding: 0;\n'
                '    margin: 0;'
        ):
            self.assertIn(fragment, WEB_UI_HTML)

        check_rule = WEB_UI_HTML[
            WEB_UI_HTML.index('  .check {'):
            WEB_UI_HTML.index('  .check-card {')
        ]
        self.assertNotIn('border:', check_rule)
        self.assertNotIn('background:', check_rule)
        self.assertNotIn('padding: 9px 10px;', check_rule)


if __name__ == '__main__':
    unittest.main()
