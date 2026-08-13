# coding=UTF-8
"""PikPak 多账号绑定/切换（rclone remote 切换）——后端账号管理逻辑。"""
import sys
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.core.target_profiles import DEFAULT_TARGET_PROFILES, PIKPAK_MAX_ACCOUNTS
from module.web_operations import WebOperationsMixin


class _FakeGc:
    def __init__(self):
        self.config = {
            'target_profiles': {
                'pikpak': {
                    'max_file_size': DEFAULT_TARGET_PROFILES['pikpak']['max_file_size'],
                    'accounts': [],
                    'archive': {
                        'enable': False,
                        'remote': '',
                        'source_directory': 'My Telegram',
                        'root_directory': 'Telegram',
                    },
                }
            }
        }
        self.target_profiles = self.config['target_profiles']

    def save_config(self, config):
        self.config = config
        self.target_profiles = config.get('target_profiles', {})


class _FakeCoordinator:
    def __init__(self):
        self.remotes = set()
        self.deleted = []
        self.dismissed = 0

    def list_remotes(self):
        return sorted(self.remotes)

    def configure_pikpak_remote(self, *, remote, username, password, overwrite=True):
        remote = (remote or '').strip().rstrip(':')
        if remote in self.remotes and not overwrite:
            raise ValueError(f'remote「{remote}」已存在。')
        self.remotes.add(remote)
        return {'ok': True, 'remote': remote, 'remotes': sorted(self.remotes), 'message': 'ok'}

    def probe_rclone(self, remote):
        remote = (remote or '').strip().rstrip(':')
        return {'ok': remote in self.remotes, 'remote': remote, 'remotes': sorted(self.remotes)}

    def delete_remote(self, remote):
        remote = (remote or '').strip().rstrip(':')
        self.remotes.discard(remote)
        self.deleted.append(remote)

    def dismiss_rclone(self):
        self.dismissed += 1


class _FakeManager:
    def __init__(self):
        self.invalidated = 0

    def invalidate_archive_client(self):
        self.invalidated += 1


class _FakeApp:
    def __init__(self):
        self.config = {'api_id': None, 'api_hash': None, 'bot_token': None}
        self.client = None


def _make_host():
    class Host(WebOperationsMixin):
        pass

    host = Host()
    host.gc = _FakeGc()
    host.setup_coordinator = _FakeCoordinator()
    host.pikpak_manager = _FakeManager()
    host.app = _FakeApp()
    host.get_setup_status = lambda: {}
    return host


class PikpakAccountSwitchCase(unittest.TestCase):
    def test_default_profile_has_empty_accounts_and_limit(self):
        self.assertIn('accounts', DEFAULT_TARGET_PROFILES['pikpak'])
        self.assertEqual([], DEFAULT_TARGET_PROFILES['pikpak']['accounts'])
        self.assertEqual(5, PIKPAK_MAX_ACCOUNTS)

    def test_next_remote_name_autonumbers(self):
        self.assertEqual('pikpak', WebOperationsMixin._next_pikpak_remote_name(set()))
        self.assertEqual('pikpak2', WebOperationsMixin._next_pikpak_remote_name({'pikpak'}))
        self.assertEqual('pikpak5', WebOperationsMixin._next_pikpak_remote_name({'pikpak', 'pikpak2', 'pikpak3', 'pikpak4'}))
        with self.assertRaises(ValueError):
            WebOperationsMixin._next_pikpak_remote_name({'pikpak', 'pikpak2', 'pikpak3', 'pikpak4', 'pikpak5'})

    def test_add_account_autonames_and_activates(self):
        host = _make_host()
        result = host.add_pikpak_account( {'username': 'a@b.c', 'password': 'secret'})
        self.assertEqual(1, len(result['accounts']))
        self.assertEqual('pikpak', result['accounts'][0]['remote'])
        self.assertTrue(result['accounts'][0]['active'])
        self.assertEqual('pikpak', result['active'])
        self.assertEqual('pikpak', host.gc.config['target_profiles']['pikpak']['archive']['remote'])
        # Adding an account only points the active-remote pointer; it must NOT
        # force-enable the archive (ADR-0016 switch semantics).
        self.assertFalse(host.gc.config['target_profiles']['pikpak']['archive']['enable'])
        self.assertEqual(1, host.pikpak_manager.invalidated)

    def test_add_second_account_names_pikpak2(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        host.add_pikpak_account( {'username': 'b', 'password': 'p'})
        accounts = host.gc.config['target_profiles']['pikpak']['accounts']
        self.assertEqual(['pikpak', 'pikpak2'], [a['remote'] for a in accounts])

    def test_add_sixth_account_rejected(self):
        host = _make_host()
        for i in range(5):
            host.add_pikpak_account( {'username': f'u{i}', 'password': 'p'})
        with self.assertRaises(ValueError):
            host.add_pikpak_account( {'username': 'u6', 'password': 'p'})

    def test_switch_updates_active_and_invalidates(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        host.add_pikpak_account( {'username': 'b', 'password': 'p'})
        before = host.pikpak_manager.invalidated
        result = host.switch_pikpak_account( {'remote': 'pikpak2'})
        self.assertEqual('pikpak2', result['active'])
        self.assertEqual('pikpak2', host.gc.config['target_profiles']['pikpak']['archive']['remote'])
        self.assertEqual(before + 1, host.pikpak_manager.invalidated)

    def test_switch_back_to_original(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        host.add_pikpak_account( {'username': 'b', 'password': 'p'})
        host.switch_pikpak_account( {'remote': 'pikpak2'})
        result = host.switch_pikpak_account( {'remote': 'pikpak'})
        self.assertEqual('pikpak', result['active'])
        self.assertEqual('pikpak', host.gc.config['target_profiles']['pikpak']['archive']['remote'])

    def test_switch_unbound_remote_rejected(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        with self.assertRaises(ValueError):
            host.switch_pikpak_account( {'remote': 'nope'})

    def test_switch_missing_remote_rejected(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        # Simulate the rclone.conf entry being deleted behind the app's back.
        host.setup_coordinator.remotes.discard('pikpak')
        with self.assertRaises(ValueError):
            host.switch_pikpak_account( {'remote': 'pikpak'})

    def test_switch_preserves_archive_enable_flag(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        host.add_pikpak_account( {'username': 'b', 'password': 'p'})
        # User disables archive, then switches account: enable must stay False.
        host.gc.config['target_profiles']['pikpak']['archive']['enable'] = False
        host.switch_pikpak_account( {'remote': 'pikpak2'})
        self.assertFalse(host.gc.config['target_profiles']['pikpak']['archive']['enable'])
        self.assertEqual('pikpak2', host.gc.config['target_profiles']['pikpak']['archive']['remote'])

    def test_add_account_ignores_payload_remote_and_autonames(self):
        host = _make_host()
        result = host.add_pikpak_account( {'username': 'a', 'password': 'p', 'remote': 'custom'})
        self.assertEqual('pikpak', result['accounts'][0]['remote'])

    def test_remove_non_active_account_succeeds(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        host.add_pikpak_account( {'username': 'b', 'password': 'p'})
        host.switch_pikpak_account( {'remote': 'pikpak2'})
        result = host.remove_pikpak_account( {'remote': 'pikpak'})
        self.assertEqual(1, len(result['accounts']))
        self.assertEqual('pikpak2', result['accounts'][0]['remote'])
        self.assertIn('pikpak', host.setup_coordinator.deleted)

    def test_remove_active_account_rejected(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        with self.assertRaises(ValueError):
            host.remove_pikpak_account( {'remote': 'pikpak'})

    def test_configure_setup_rclone_registers_account(self):
        host = _make_host()
        host.configure_setup_rclone(
            {'remote': 'pikpak', 'username': 'a@b.c', 'password': 'secret', 'overwrite': True},
        )
        accounts = host.gc.config['target_profiles']['pikpak']['accounts']
        self.assertEqual(['pikpak'], [a['remote'] for a in accounts])
        self.assertEqual('pikpak', host.gc.config['target_profiles']['pikpak']['archive']['remote'])
        self.assertEqual(1, host.setup_coordinator.dismissed)
        self.assertGreaterEqual(host.pikpak_manager.invalidated, 1)

    def test_configure_setup_rclone_enforces_cap(self):
        host = _make_host()
        for i in range(5):
            host.add_pikpak_account( {'username': f'u{i}', 'password': 'p'})
        with self.assertRaises(ValueError):
            host.configure_setup_rclone(
                {'remote': 'pikpak6', 'username': 'x', 'password': 'p', 'overwrite': True},
            )

    def test_upgrade_backfills_accounts_key(self):
        from module.core.config import GlobalConfig

        gc = GlobalConfig.__new__(GlobalConfig)
        config = {
            'target_profiles': {
                'pikpak': {
                    'max_file_size': 123,
                    'archive': {'enable': True, 'remote': 'pikpak'},
                }
            }
        }
        gc.process_target_profiles(config)
        self.assertIn('accounts', config['target_profiles']['pikpak'])
        self.assertEqual([], config['target_profiles']['pikpak']['accounts'])

    def test_invalidate_archive_client_resets_cache(self):
        from module.adapters.pikpak.integration import PikpakIntegrationManager

        class StubClient:
            pass

        manager = object.__new__(PikpakIntegrationManager)
        manager._pikpak_archive_client = None
        manager._pikpak_archive_client_getter = lambda: StubClient()
        first = manager.get_pikpak_archive_client()
        self.assertIsInstance(first, StubClient)
        manager.invalidate_archive_client()
        self.assertIsNone(manager._pikpak_archive_client)

    # --- 修复回归测试（ADR-0016 语义收紧） ---

    def test_add_account_preserves_disabled_archive(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        # User deliberately disables archive, then adds another account:
        # adding must not silently re-enable it.
        host.gc.config['target_profiles']['pikpak']['archive']['enable'] = False
        host.add_pikpak_account( {'username': 'b', 'password': 'p'})
        self.assertFalse(host.gc.config['target_profiles']['pikpak']['archive']['enable'])
        self.assertEqual('pikpak2', host.gc.config['target_profiles']['pikpak']['archive']['remote'])

    def test_configure_setup_rclone_cap_rejection_leaves_no_side_effects(self):
        host = _make_host()
        for i in range(5):
            host.add_pikpak_account( {'username': f'u{i}', 'password': 'p'})
        host.gc.config['target_profiles']['pikpak']['archive']['enable'] = False
        with self.assertRaises(ValueError):
            host.configure_setup_rclone(
                {'remote': 'pikpak6', 'username': 'x', 'password': 'p', 'overwrite': True},
            )
        # The cap must be enforced BEFORE creating the rclone remote / writing
        # config: no orphaned credentials, no flipped archive, no dismiss.
        archive = host.gc.config['target_profiles']['pikpak']['archive']
        self.assertFalse(archive['enable'])
        self.assertEqual('pikpak5', archive['remote'])
        self.assertNotIn('pikpak6', host.setup_coordinator.remotes)
        self.assertEqual(0, host.setup_coordinator.dismissed)

    def test_list_accounts_rclone_error_marks_no_missing(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})

        class _Broken(_FakeCoordinator):
            def list_remotes(self):
                raise RuntimeError('rclone unavailable')

        host.setup_coordinator = _Broken()
        result = host.list_pikpak_accounts()
        self.assertEqual(1, len(result['accounts']))
        # Unknown status must not be mislabelled as "missing".
        self.assertFalse(result['accounts'][0]['missing'])
        self.assertIsNotNone(result['rclone_error'])
        self.assertEqual([], result['remotes'])

    def test_switch_rejects_when_rclone_unreadable(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})

        class _Broken(_FakeCoordinator):
            def list_remotes(self):
                raise RuntimeError('rclone unavailable')

        host.setup_coordinator = _Broken()
        with self.assertRaises(ValueError):
            host.switch_pikpak_account( {'remote': 'pikpak'})

    def test_remove_rejects_when_rclone_unreadable(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        host.add_pikpak_account( {'username': 'b', 'password': 'p'})
        host.switch_pikpak_account( {'remote': 'pikpak2'})

        class _Broken(_FakeCoordinator):
            def list_remotes(self):
                raise RuntimeError('rclone unavailable')

        host.setup_coordinator = _Broken()
        with self.assertRaises(ValueError):
            host.remove_pikpak_account( {'remote': 'pikpak'})
        # Binding must survive a refused delete.
        self.assertEqual(2, len(host._pikpak_accounts()))

    def test_remove_truly_missing_account_skips_delete(self):
        host = _make_host()
        host.add_pikpak_account( {'username': 'a', 'password': 'p'})
        host.add_pikpak_account( {'username': 'b', 'password': 'p'})
        host.switch_pikpak_account( {'remote': 'pikpak2'})
        # rclone.conf entry removed behind the app's back: genuinely missing.
        host.setup_coordinator.remotes.discard('pikpak')
        result = host.remove_pikpak_account( {'remote': 'pikpak'})
        self.assertEqual(['pikpak2'], [a['remote'] for a in result['accounts']])
        self.assertEqual([], host.setup_coordinator.deleted)


if __name__ == '__main__':
    unittest.main()
