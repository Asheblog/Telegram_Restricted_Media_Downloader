# coding=UTF-8
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.adapters.webui.setup import (
    SetupCoordinator,
    apply_web_safe_user_defaults,
    has_telegram_api_credentials,
)
from module.core.target_profiles import DEFAULT_TARGET_PROFILES


class _FakeCompleted:
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class SetupWizardCase(unittest.TestCase):
    def test_has_telegram_api_credentials(self):
        self.assertFalse(has_telegram_api_credentials(None))
        self.assertFalse(has_telegram_api_credentials({'api_id': None, 'api_hash': None}))
        self.assertFalse(has_telegram_api_credentials({'api_id': 1, 'api_hash': 'short'}))
        self.assertTrue(has_telegram_api_credentials({
            'api_id': 12345,
            'api_hash': '0123456789abcdef0123456789abcdef',
        }))

    def test_apply_web_safe_user_defaults_fills_paths(self):
        config = apply_web_safe_user_defaults({})
        self.assertTrue(config.get('save_directory'))
        self.assertTrue(config.get('session_directory'))
        self.assertTrue(config.get('temp_directory'))
        self.assertIsInstance(config.get('download_type'), list)
        self.assertFalse(config['proxy']['enable_proxy'])
        self.assertEqual(config['max_retries']['download'], 5)

    def test_upgrade_ready_does_not_force_wizard(self):
        coord = SetupCoordinator(runner=lambda *a, **k: _FakeCompleted(stdout='pikpak:\n'))
        with patch.object(coord, 'probe_rclone', return_value={'ok': False, 'message': 'missing', 'remotes': []}):
            status = coord.build_status(
                api_done=True,
                telegram_done=True,
                telegram_step='done',
                archive_enable=True,
                archive_remote='pikpak',
            )
        self.assertTrue(status['ready'])
        self.assertFalse(status['wizard_active'])
        self.assertFalse(status['steps']['rclone']['prompt'])

    def test_new_install_guides_then_prompts_rclone(self):
        coord = SetupCoordinator(runner=lambda *a, **k: _FakeCompleted(stdout=''))
        with patch.object(coord, 'probe_rclone', return_value={'ok': False, 'message': 'missing', 'remotes': []}):
            incomplete = coord.build_status(
                api_done=False,
                telegram_done=False,
                telegram_step='pending',
            )
            self.assertTrue(incomplete['wizard_active'])
            self.assertEqual(incomplete['current_step'], 'api')
            self.assertTrue(coord.guided)

            after_tg = coord.build_status(
                api_done=True,
                telegram_done=True,
                telegram_step='done',
            )
        self.assertTrue(after_tg['ready'])
        self.assertTrue(after_tg['wizard_active'])
        self.assertEqual(after_tg['current_step'], 'rclone')
        self.assertTrue(after_tg['steps']['rclone']['prompt'])

    def test_skip_rclone_no_longer_dismisses_wizard(self):
        coord = SetupCoordinator(runner=lambda *a, **k: _FakeCompleted(stdout=''))
        with patch.object(coord, 'probe_rclone', return_value={'ok': False, 'message': 'missing', 'remotes': []}):
            coord.build_status(api_done=False, telegram_done=False)
            coord.dismiss_rclone()
            status = coord.build_status(api_done=True, telegram_done=True, telegram_step='done')
        self.assertTrue(status['ready'])
        self.assertTrue(status['wizard_active'])
        self.assertEqual('rclone', status['current_step'])
        self.assertTrue(status['steps']['rclone']['required'])

    def test_guided_rclone_ok_completes_wizard(self):
        coord = SetupCoordinator(runner=lambda *a, **k: _FakeCompleted(stdout='pikpak:\n'))
        with patch.object(coord, 'probe_rclone', return_value={'ok': False, 'message': 'missing', 'remotes': []}):
            coord.build_status(api_done=False, telegram_done=False)
        with patch.object(coord, 'probe_rclone', return_value={'ok': True, 'message': 'ok', 'remotes': ['pikpak']}):
            status = coord.build_status(api_done=True, telegram_done=True, telegram_step='done')
        self.assertTrue(status['ready'])
        self.assertFalse(status['wizard_active'])
        self.assertEqual('done', status['current_step'])
        self.assertTrue(status['steps']['rclone']['done'])

    def test_configure_pikpak_remote_uses_rclone_noninteractive(self):
        calls = []
        created = {'ok': False}

        def runner(cmd, **kwargs):
            calls.append(cmd)
            if cmd[1] == 'listremotes':
                return _FakeCompleted(stdout='pikpak:\n' if created['ok'] else '')
            if cmd[1] == 'obscure':
                return _FakeCompleted(stdout='obscured-pass\n')
            if cmd[1:3] == ['config', 'create']:
                created['ok'] = True
                return _FakeCompleted()
            if cmd[1] == 'lsd':
                return _FakeCompleted()
            return _FakeCompleted()

        with tempfile.TemporaryDirectory() as tmp:
            conf = os.path.join(tmp, 'rclone.conf')
            with patch.dict(os.environ, {'RCLONE_CONFIG': conf}):
                coord = SetupCoordinator(runner=runner, rclone_bin='rclone')
                with patch('module.adapters.webui.setup.shutil.which', return_value='rclone'):
                    probe = coord.configure_pikpak_remote(
                        remote='pikpak',
                        username='user@example.com',
                        password='secret',
                    )
        self.assertTrue(probe['ok'])
        create_cmds = [c for c in calls if len(c) > 2 and c[1:3] == ['config', 'create']]
        self.assertEqual(len(create_cmds), 1)
        self.assertIn('user=user@example.com', create_cmds[0])
        self.assertIn('pass=obscured-pass', create_cmds[0])
        self.assertNotIn('secret', ' '.join(create_cmds[0]))

    def test_default_archive_enable_is_false_for_new_profiles(self):
        archive = DEFAULT_TARGET_PROFILES['pikpak']['archive']
        self.assertFalse(archive['enable'])

    def test_web_config_guide_skips_stdin(self):
        from module.parser import PARSE_ARGS
        from module.core.config import UserConfig

        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, 'config.yaml')
            with patch.object(PARSE_ARGS, 'web', 2921), \
                    patch.object(PARSE_ARGS, 'session', None), \
                    patch.object(PARSE_ARGS, 'temp', None), \
                    patch.object(PARSE_ARGS, 'quiet', True):
                cfg = UserConfig.__new__(UserConfig)
                cfg.config_path = config_path
                cfg.platform = 'Windows'
                cfg.history_timestamp = {}
                cfg.input_link = []
                cfg.last_record = {}
                cfg.difference_timestamp = {}
                cfg.download_type = []
                cfg.record_dtype = set()
                cfg.record_flag = False
                cfg.modified = False
                cfg.is_change_account = True
                cfg.re_config = False
                with patch.object(UserConfig, 'load_config', return_value={
                    'api_id': None,
                    'api_hash': None,
                    'proxy': {},
                    'max_tasks': {},
                    'max_retries': {},
                }), patch.object(UserConfig, 'save_config') as save_mock, \
                        patch('module.core.config.console.input', side_effect=AssertionError('stdin should not be used')):
                    cfg.config_guide()
                self.assertTrue(save_mock.called)
                saved = save_mock.call_args[0][0]
                self.assertTrue(saved.get('save_directory'))
                self.assertIsNone(saved.get('api_id'))


if __name__ == '__main__':
    unittest.main()
