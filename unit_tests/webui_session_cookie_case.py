# coding=UTF-8
import http.client
import json
import sys
import unittest
from unittest.mock import MagicMock, patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]

from module.adapters.webui.server import WebUiServer

sys.argv = _ORIGINAL_ARGV


class WebUiSessionCookieCase(unittest.TestCase):
    def _server(self, username='admin', password='pass') -> WebUiServer:
        return WebUiServer(
            store=MagicMock(),
            username=username,
            password=password,
        )

    def test_remember_me_token_survives_process_restart(self):
        before = self._server()
        token = before._generate_session_token()
        self.assertTrue(before.validate_session_token(token))

        after = self._server()
        self.assertTrue(
            after.validate_session_token(token),
            '重启后相同凭据应仍能校验 remember-me session cookie',
        )

    def test_password_change_invalidates_old_token(self):
        before = self._server(password='old-pass')
        token = before._generate_session_token()
        self.assertTrue(before.validate_session_token(token))

        after = self._server(password='new-pass')
        self.assertFalse(after.validate_session_token(token))

    def test_expired_token_is_rejected(self):
        server = self._server()
        with patch('module.adapters.webui.server.time.time', return_value=1_000_000):
            token = server._generate_session_token()
        with patch(
            'module.adapters.webui.server.time.time',
            return_value=1_000_000 + server.SESSION_MAX_AGE + 1,
        ):
            self.assertFalse(server.validate_session_token(token))

    def test_remember_me_cookie_sets_max_age(self):
        server = self._server()
        token = server._generate_session_token()
        cookie = server._create_session_cookie(token, remember_me=True)
        self.assertIn(f'Max-Age={server.SESSION_MAX_AGE}', cookie)
        session_cookie = server._create_session_cookie(token, remember_me=False)
        self.assertNotIn('Max-Age=', session_cookie)

    def test_login_cookie_works_after_server_restart(self):
        first = self._server()
        first.start(open_browser=False)
        try:
            conn = http.client.HTTPConnection(first.host, first.port, timeout=5)
            conn.request(
                'POST',
                '/api/auth/login',
                body=json.dumps({
                    'username': 'admin',
                    'password': 'pass',
                    'remember_me': True,
                }),
                headers={'Content-Type': 'application/json'},
            )
            response = conn.getresponse()
            body = json.loads(response.read().decode('utf-8'))
            self.assertEqual(200, response.status)
            self.assertTrue(body['success'])
            set_cookie = response.getheader('Set-Cookie')
            self.assertIsNotNone(set_cookie)
            cookie_header = set_cookie.split(';', 1)[0]
            conn.close()
        finally:
            first.stop()

        second = self._server()
        second.start(open_browser=False)
        try:
            conn = http.client.HTTPConnection(second.host, second.port, timeout=5)
            conn.request('GET', '/api/auth/status', headers={'Cookie': cookie_header})
            response = conn.getresponse()
            body = json.loads(response.read().decode('utf-8'))
            self.assertEqual(200, response.status)
            self.assertEqual('none', body['step'])
            conn.close()
        finally:
            second.stop()


if __name__ == '__main__':
    unittest.main()
