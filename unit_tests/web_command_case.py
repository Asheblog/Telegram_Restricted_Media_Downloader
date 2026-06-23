import tempfile
import unittest
import importlib.util
import json
import sys
import types
import urllib.request
import socket
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / 'module' / 'transfer_store.py'
SPEC = importlib.util.spec_from_file_location('transfer_store', MODULE_PATH)
transfer_store = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transfer_store)
TransferStore = transfer_store.TransferStore
TransferStatus = transfer_store.TransferStatus

COMMANDS_PATH = Path(__file__).resolve().parents[1] / 'module' / 'web_commands.py'
COMMANDS_SPEC = importlib.util.spec_from_file_location('web_commands', COMMANDS_PATH)
web_commands = importlib.util.module_from_spec(COMMANDS_SPEC)
COMMANDS_SPEC.loader.exec_module(web_commands)

WEB_UI_PATH = Path(__file__).resolve().parents[1] / 'module' / 'web_ui.py'
WEB_UI_SPEC = importlib.util.spec_from_file_location('web_ui', WEB_UI_PATH)
web_ui = importlib.util.module_from_spec(WEB_UI_SPEC)
module_stub = types.ModuleType('module')
module_stub.log = types.SimpleNamespace(
    info=lambda *args, **kwargs: None,
    warning=lambda *args, **kwargs: None,
    exception=lambda *args, **kwargs: None,
)
enums_stub = types.ModuleType('module.enums')
enums_stub.ENVIRON = types.SimpleNamespace(
    TRMD_WEB_PORT='TRMD_WEB_PORT',
    TRMD_WEB_HOST='TRMD_WEB_HOST',
    TRMD_WEB_USERNAME='TRMD_WEB_USERNAME',
    TRMD_WEB_PASSWORD='TRMD_WEB_PASSWORD',
)
assets_stub = types.ModuleType('module.web_ui_assets')
assets_stub.WEB_UI_HTML = '<!doctype html><html><body>TRMD</body></html>'
sys.modules.setdefault('module', module_stub)
sys.modules.setdefault('module.enums', enums_stub)
sys.modules.setdefault('module.transfer_store', transfer_store)
sys.modules.setdefault('module.web_ui_assets', assets_stub)
sys.modules.setdefault('module.web_commands', web_commands)
WEB_UI_SPEC.loader.exec_module(web_ui)
WebUiServer = web_ui.WebUiServer


class WebCommandTaskTest(unittest.TestCase):
    def test_creates_command_task_with_payload_and_events(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)

            task_id = store.create_task(
                command='forward',
                payload={
                    'origin_link': 'https://t.me/source',
                    'target_link': 'https://t.me/target',
                    'start_id': 1,
                    'end_id': 3,
                },
            )

            task = store.get_task(task_id)
            payload = store.task_payload(task_id)

            self.assertEqual(task['command'], 'forward')
            self.assertEqual(task['status'], TransferStatus.PENDING)
            self.assertEqual(task['payload']['origin_link'], 'https://t.me/source')
            self.assertEqual(task['payload']['end_id'], 3)
            self.assertEqual(payload['events'][0]['message'], 'forward task created.')

    def test_web_api_creates_command_task(self):
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            probe.close()
        except PermissionError:
            self.skipTest('sandbox does not allow opening local sockets')
        with tempfile.TemporaryDirectory() as directory:
            store = TransferStore(directory=directory)
            server = WebUiServer(store=store, host='127.0.0.1', port=0)
            server.start(open_browser=False)
            try:
                body = json.dumps({
                    'command': 'upload',
                    'payload': {
                        'file_path': '/tmp/video.mp4',
                        'target_link': 'me',
                    },
                }).encode('utf-8')
                request = urllib.request.Request(
                    f'{server.url}/api/tasks',
                    data=body,
                    headers={'content-type': 'application/json'},
                    method='POST',
                )

                with urllib.request.urlopen(request, timeout=2) as response:
                    data = json.loads(response.read().decode('utf-8'))

                task = store.get_task(data['task_id'])
                self.assertEqual(response.status, 201)
                self.assertEqual(task['command'], 'upload')
                self.assertEqual(task['payload']['file_path'], '/tmp/video.mp4')
                self.assertEqual(task['target_link'], 'me')
            finally:
                server.stop()

    def test_normalizes_download_chat_payload(self):
        payload = web_commands.normalize_command_payload(
            'download_chat',
            {
                'chat_link': 'https://t.me/source',
                'start_date': '2026-01-01',
                'end_date': '',
                'download_type': ['video', 'photo'],
                'keywords': 'alpha beta',
                'include_comment': True,
            }
        )

        self.assertTrue(payload['download_type']['video'])
        self.assertTrue(payload['download_type']['photo'])
        self.assertFalse(payload['download_type']['document'])
        self.assertEqual(payload['keywords'], ['alpha', 'beta'])

    def test_html_contains_all_command_entries(self):
        assets_path = Path(__file__).resolve().parents[1] / 'module' / 'web_ui_assets.py'
        text = assets_path.read_text(encoding='UTF-8')

        for command in (
                'download',
                'forward',
                'listen_download',
                'listen_forward',
                'listen_info',
                'upload',
                'upload_r',
                'download_chat',
                'table',
                'help',
                'exit',
        ):
            self.assertIn(command, text)
        self.assertIn('/api/listeners/', text)

    def test_download_primary_links_preserve_target_profile(self):
        payload = web_commands.normalize_command_payload(
            'download',
            {
                'links': 'https://t.me/source/1',
                'target_link': 'https://t.me/pikpak_bot',
                'target_profile': 'pikpak',
            }
        )
        primary = web_commands.primary_links_for_task('download', payload)

        self.assertEqual(primary['target_link'], 'https://t.me/pikpak_bot')
        self.assertEqual(primary['target_profile'], 'pikpak')

    def test_string_false_does_not_enable_boolean_options(self):
        upload_payload = web_commands.normalize_command_payload(
            'upload',
            {
                'file_path': '/tmp/video.mp4',
                'target_link': 'me',
                'delete_after_upload': 'false',
            }
        )
        chat_payload = web_commands.normalize_command_payload(
            'download_chat',
            {
                'chat_link': 'https://t.me/source',
                'include_comment': 'false',
            }
        )

        self.assertFalse(upload_payload['delete_after_upload'])
        self.assertFalse(chat_payload['include_comment'])
