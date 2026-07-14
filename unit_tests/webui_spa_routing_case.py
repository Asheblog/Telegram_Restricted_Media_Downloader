# coding=UTF-8
import http.client
import json
import sys
import unittest
from unittest.mock import MagicMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]

from module.adapters.webui.server import WebUiServer, is_spa_page_path

sys.argv = _ORIGINAL_ARGV


class WebUiSpaRoutingCase(unittest.TestCase):
    def test_is_spa_page_path_allowlist_and_catchall(self):
        for path in (
            '/',
            '/index.html',
            '/transfers',
            '/watches',
            '/downloads-uploads',
            '/statistics',
            '/records',
            '/media',
            '/system-logs',
            '/settings',
            '/profile',
            '/unknown-view',
            '/watches/',
        ):
            self.assertTrue(is_spa_page_path(path), path)

        for path in (
            '/api/tasks',
            '/api/auth/status',
            '/fonts/inter.woff2',
            '/static/app.js',
            '/favicon.ico',
        ):
            self.assertFalse(is_spa_page_path(path), path)

    def _server(self) -> WebUiServer:
        return WebUiServer(
            store=MagicMock(),
            username='admin',
            password='pass',
        )

    def _login_cookie(self, server: WebUiServer) -> str:
        conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
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
        self.assertEqual(200, response.status)
        set_cookie = response.getheader('Set-Cookie')
        self.assertIsNotNone(set_cookie)
        cookie = set_cookie.split(';', 1)[0]
        conn.close()
        return cookie

    def test_spa_view_path_serves_html_when_authed(self):
        server = self._server()
        server.start(open_browser=False)
        try:
            cookie = self._login_cookie(server)
            conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
            conn.request('GET', '/watches', headers={'Cookie': cookie})
            response = conn.getresponse()
            body = response.read().decode('utf-8')
            self.assertEqual(200, response.status)
            self.assertIn('text/html', response.getheader('Content-Type', ''))
            self.assertIn('TRMD', body)
            self.assertIn('data-nav="watches"', body)
            conn.close()
        finally:
            server.stop()

    def test_spa_view_path_shows_login_when_unauthorized(self):
        server = self._server()
        server.start(open_browser=False)
        try:
            conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
            conn.request('GET', '/settings')
            response = conn.getresponse()
            body = response.read().decode('utf-8')
            self.assertEqual(200, response.status)
            self.assertIn('login', body.lower())
            self.assertNotIn('data-nav="settings"', body)
            conn.close()
        finally:
            server.stop()

    def test_api_path_still_404_for_unknown(self):
        server = self._server()
        server.start(open_browser=False)
        try:
            cookie = self._login_cookie(server)
            conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
            conn.request('GET', '/api/does-not-exist', headers={'Cookie': cookie})
            response = conn.getresponse()
            body = json.loads(response.read().decode('utf-8'))
            self.assertEqual(404, response.status)
            self.assertEqual('not_found', body.get('error_code'))
            conn.close()
        finally:
            server.stop()


if __name__ == '__main__':
    unittest.main()
