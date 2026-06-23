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


if __name__ == '__main__':
    unittest.main()
