# coding=UTF-8
"""HTTP 层安全加固回归测试。

逐条覆盖渗透测试报告中的 F-01 ~ F-07：

- F-01 畸形/非对象 JSON 不再逃逸到 socketserver（502 / 连接重置）
- F-02 HSTS 只在确认 HTTPS（或非 loopback 生产姿态 + 反代）时下发
- F-03 所有响应带防嵌套 / 防嗅探 / referrer 收紧头
- F-04 会话 Cookie 在生产姿态下带 Secure，本地明文开发不被误伤
- F-05 登录失败按 IP + 用户名双维度限流，且不构成管理员锁死
- F-06 logout 必须带会话且拒绝跨站 Origin
- F-07 404/401 路由预言机与 Python http.server 指纹被消除
"""
import http.client
import json
import os
import socket
import sys
import unittest
from unittest.mock import MagicMock, patch

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]

from module.adapters.webui.security import LoginThrottle, is_cross_origin_request
from module.adapters.webui.server import WebUiServer

sys.argv = _ORIGINAL_ARGV


class _StubHandler:
    """Minimal handler stand-in for header-only security helpers."""

    def __init__(self, headers):
        self.headers = headers


class WebUiHttpHardeningCase(unittest.TestCase):
    def _server(self, **kwargs) -> WebUiServer:
        server = WebUiServer(
            store=MagicMock(),
            username='admin',
            password='pass',
            **kwargs,
        )
        server.start(open_browser=False)
        self.addCleanup(server.stop)
        return server

    def _request(self, server, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', server.port, timeout=10)
        try:
            payload = body.encode('utf-8') if isinstance(body, str) else body
            conn.request(method, path, body=payload, headers=headers or {})
            response = conn.getresponse()
            raw = response.read().decode('utf-8', 'replace')
            header_map = {k.lower(): v for k, v in response.getheaders()}
            return response.status, header_map, raw
        finally:
            conn.close()

    def _login(self, server, username='admin', password='pass', headers=None):
        return self._request(
            server,
            'POST',
            '/api/auth/login',
            body=json.dumps(
                {'username': username, 'password': password, 'remember_me': True}
            ),
            headers={'Content-Type': 'application/json', **(headers or {})},
        )

    def _cookie(self, response_headers) -> str:
        set_cookie = response_headers.get('set-cookie')
        self.assertIsNotNone(set_cookie, 'login must return a session cookie')
        return set_cookie.split(';', 1)[0]

    # ---- F-01 未捕获异常 -------------------------------------------------

    def test_malformed_json_bodies_never_crash_the_backend(self):
        server = self._server()
        for body in (
            '[]',
            '123',
            'null',
            'true',
            '"a"',
            'not json at all',
            '{',
            '{"a":}',
            '[1, 2]',
        ):
            with self.subTest(body=body):
                status, _, raw = self._request(
                    server,
                    'POST',
                    '/api/auth/login',
                    body=body,
                    headers={'Content-Type': 'application/json'},
                )
                self.assertEqual(400, status, raw)
                self.assertEqual('invalid_json_body', json.loads(raw)['error_code'])
        # 畸形请求风暴之后服务仍然正常
        status, _, raw = self._login(server)
        self.assertEqual(200, status, raw)

    def test_oversized_body_is_rejected_without_reading_it(self):
        server = self._server()
        status, _, raw = self._request(
            server,
            'POST',
            '/api/auth/login',
            body='{}',
            headers={
                'Content-Type': 'application/json',
                'Content-Length': str(64 * 1024 * 1024),
            },
        )
        self.assertEqual(413, status, raw)
        self.assertEqual('request_body_too_large', json.loads(raw)['error_code'])

    def test_unhandled_route_error_returns_structured_500(self):
        server = self._server()
        cookie = self._cookie(self._login(server)[1])

        def boom():
            raise RuntimeError('boom')

        server.list_operations = boom
        status, _, raw = self._request(
            server, 'GET', '/api/operations', headers={'Cookie': cookie}
        )
        self.assertEqual(500, status, raw)
        body = json.loads(raw)
        self.assertEqual('internal_error', body['error_code'])
        self.assertNotIn('boom', raw)

    # ---- F-03 安全响应头 -------------------------------------------------

    def test_security_headers_present_on_pages_and_errors(self):
        server = self._server()
        for method, path, expected_status in (
            ('GET', '/', 200),
            ('GET', '/api/tasks', 401),
            ('GET', '/api/definitely-missing', 401),
        ):
            with self.subTest(path=path):
                status, headers, _ = self._request(server, method, path)
                self.assertEqual(expected_status, status)
                self.assertEqual('nosniff', headers.get('x-content-type-options'))
                self.assertEqual('DENY', headers.get('x-frame-options'))
                self.assertEqual(
                    "frame-ancestors 'none'; base-uri 'self'; "
                    "form-action 'self'; object-src 'none'",
                    headers.get('content-security-policy'),
                )
                self.assertEqual('no-referrer', headers.get('referrer-policy'))
                self.assertIn('geolocation=()', headers.get('permissions-policy', ''))

    # ---- F-02 HSTS -------------------------------------------------------

    def test_hsts_only_when_https_terminated(self):
        server = self._server()
        _, headers, _ = self._request(server, 'GET', '/')
        self.assertIsNone(
            headers.get('strict-transport-security'),
            '本地明文直连不应下发 HSTS',
        )

        _, headers, _ = self._request(
            server, 'GET', '/', headers={'X-Forwarded-Proto': 'https'}
        )
        self.assertIn('max-age=31536000', headers.get('strict-transport-security', ''))

        _, headers, _ = self._request(
            server, 'GET', '/api/tasks', headers={'X-Forwarded-Proto': 'https'}
        )
        self.assertIn('includeSubDomains', headers.get('strict-transport-security', ''))

        # 非 loopback 监听 + 反代跳 = 生产姿态，同样下发 HSTS
        prod = self._server(host='0.0.0.0')
        _, headers, _ = self._request(
            prod, 'GET', '/', headers={'X-Forwarded-For': '203.0.113.7'}
        )
        self.assertIn('max-age=31536000', headers.get('strict-transport-security', ''))

    # ---- F-04 会话 Cookie ------------------------------------------------

    def test_session_cookie_secure_flags(self):
        server = self._server()
        status, headers, raw = self._login(server)
        self.assertEqual(200, status, raw)
        local_cookie = headers['set-cookie']
        self.assertIn('HttpOnly', local_cookie)
        self.assertIn('SameSite=Lax', local_cookie)
        self.assertNotIn('Secure', local_cookie)

        status, headers, raw = self._login(
            server, headers={'X-Forwarded-Proto': 'https'}
        )
        self.assertIn('Secure', headers['set-cookie'])

        prod = self._server(host='0.0.0.0')
        status, headers, raw = self._login(
            prod, headers={'X-Forwarded-For': '203.0.113.7'}
        )
        self.assertEqual(200, status, raw)
        self.assertIn('Secure', headers['set-cookie'])

    # ---- F-05 登录限流 ---------------------------------------------------

    def test_login_rate_limit_blocks_bad_credentials_only(self):
        with patch.dict(
            os.environ,
            {
                'TRMD_WEB_LOGIN_MAX_FAILURES': '3',
                'TRMD_WEB_LOGIN_WINDOW_SECONDS': '60',
                'TRMD_WEB_LOGIN_LOCKOUT_SECONDS': '60',
            },
        ):
            server = self._server()
        self.assertIsNotNone(server.login_throttle)

        self.assertEqual(401, self._login(server, password='wrong')[0])
        self.assertEqual(401, self._login(server, password='wrong')[0])
        status, headers, raw = self._login(server, password='wrong')
        self.assertEqual(429, status, raw)
        self.assertEqual('too_many_attempts', json.loads(raw)['error_code'])
        self.assertGreaterEqual(int(headers['retry-after']), 1)
        self.assertEqual(429, self._login(server, password='wrong')[0])

        # 正确口令始终放行：限流不能被用来把管理员锁在门外
        status, _, raw = self._login(server)
        self.assertEqual(200, status, raw)
        # 成功登录后计数清零
        self.assertEqual(401, self._login(server, password='wrong')[0])

    def test_login_throttle_keys_are_independent(self):
        clock = {'now': 1000.0}
        throttle = LoginThrottle(
            max_failures=2, lockout_seconds=60, clock=lambda: clock['now']
        )
        throttle.record_failure('10.0.0.1', 'admin')
        throttle.record_failure('10.0.0.1', 'admin')
        # 该 IP 维度生效：同一 IP 的其它用户名也被限
        self.assertGreater(throttle.retry_after('10.0.0.1', 'other'), 0)
        # 用户名维度生效：换 IP 仍用被限用户名同样受限
        self.assertGreater(throttle.retry_after('10.0.0.2', 'admin'), 0)
        # 两个维度都干净时才放行
        self.assertEqual(0, throttle.retry_after('10.0.0.2', 'other'))
        # 成功登录清空该 IP + 用户名两个维度
        throttle.record_success('10.0.0.1', 'admin')
        self.assertEqual(0, throttle.retry_after('10.0.0.1', 'admin'))

    def test_login_throttle_backoff_doubles_and_caps(self):
        clock = {'now': 0.0}
        throttle = LoginThrottle(
            max_failures=2,
            window_seconds=30,
            lockout_seconds=10,
            max_lockout_seconds=100,
            clock=lambda: clock['now'],
        )
        observed = []
        for wait in (0, 11, 21, 41, 81):
            clock['now'] += wait
            throttle.record_failure('203.0.113.9', 'admin')
            observed.append(throttle.record_failure('203.0.113.9', 'admin'))
        self.assertEqual([10, 20, 40, 80, 100], observed)

    def test_login_rate_limit_can_be_disabled(self):
        with patch.dict(os.environ, {'TRMD_WEB_LOGIN_RATELIMIT': 'off'}):
            server = self._server()
        self.assertIsNone(server.login_throttle)
        statuses = [self._login(server, password='wrong')[0] for _ in range(6)]
        self.assertEqual([401] * 6, statuses)

    # ---- F-06 logout 与会话边界 -----------------------------------------

    def test_logout_requires_session_and_same_origin(self):
        server = self._server()

        status, headers, raw = self._request(server, 'POST', '/api/auth/logout')
        self.assertEqual(401, status, raw)
        self.assertEqual('auth_required', json.loads(raw)['error_code'])
        self.assertNotIn('set-cookie', headers)

        cookie = self._cookie(self._login(server)[1])
        status, _, raw = self._request(
            server,
            'POST',
            '/api/auth/logout',
            headers={
                'Cookie': cookie,
                # 反代改写 Host 为回环地址时应用无法判断真实站点（见 security.py 说明），
                # 这里显式给出真实站点域名来验证跨站拒绝。
                'Host': 'tgbot.example.com',
                'Origin': 'https://evil.example',
            },
        )
        self.assertEqual(403, status, raw)
        self.assertEqual('cross_origin_forbidden', json.loads(raw)['error_code'])
        # 跨站请求没有清掉会话
        status, _, _ = self._request(
            server, 'GET', '/api/auth/status', headers={'Cookie': cookie}
        )
        self.assertEqual(200, status)

        status, headers, raw = self._request(
            server,
            'POST',
            '/api/auth/logout',
            headers={'Cookie': cookie, 'Origin': f'http://127.0.0.1:{server.port}'},
        )
        self.assertEqual(200, status, raw)
        self.assertIn('Max-Age=0', headers['set-cookie'])

    def test_cross_origin_state_changing_post_is_rejected(self):
        server = self._server()
        cookie = self._cookie(self._login(server)[1])
        status, _, raw = self._request(
            server,
            'POST',
            '/api/tasks',
            body=json.dumps({'source_link': 'https://t.me/example/1'}),
            headers={
                'Cookie': cookie,
                'Content-Type': 'application/json',
                'Host': 'tgbot.example.com',
                'Origin': 'https://evil.example',
            },
        )
        self.assertEqual(403, status, raw)
        self.assertEqual('cross_origin_forbidden', json.loads(raw)['error_code'])

    def test_cross_origin_matrix(self):
        def check(headers):
            return is_cross_origin_request(_StubHandler(headers))

        # 非浏览器客户端（无 Origin / Referer）放行
        self.assertFalse(check({'host': 'tgbot.example.com'}))
        # 同源（含默认端口归一化）
        self.assertFalse(
            check({'host': 'tgbot.example.com', 'origin': 'https://tgbot.example.com'})
        )
        self.assertFalse(
            check(
                {
                    'host': 'tgbot.example.com',
                    'origin': 'https://tgbot.example.com:443',
                }
            )
        )
        self.assertFalse(
            check({'host': '127.0.0.1:3921', 'origin': 'http://127.0.0.1:3921'})
        )
        # 跨站（Origin 与 Referer 两条路径）
        self.assertTrue(
            check({'host': 'tgbot.example.com', 'origin': 'https://evil.example'})
        )
        self.assertTrue(
            check({'host': 'tgbot.example.com', 'referer': 'https://evil.example/x'})
        )
        self.assertTrue(check({'host': 'tgbot.example.com', 'origin': 'null'}))
        # 反代改写 Host 为回环地址：无法判断真实站点 → 放行，避免把正常登录 403 掉
        self.assertFalse(
            check({'host': '127.0.0.1:2921', 'origin': 'https://tgbot.example.com'})
        )
        # 反代转发 X-Forwarded-Host 时按真实站点判定
        self.assertTrue(
            check(
                {
                    'host': '127.0.0.1:2921',
                    'x-forwarded-host': 'tgbot.example.com',
                    'origin': 'https://evil.example',
                }
            )
        )
        self.assertFalse(
            check(
                {
                    'host': '127.0.0.1:2921',
                    'x-forwarded-host': 'tgbot.example.com',
                    'origin': 'https://tgbot.example.com',
                }
            )
        )
        # 排障 / 特殊反代：可显式关闭该校验
        with patch.dict(os.environ, {'TRMD_WEB_CSRF_ORIGIN_CHECK': 'off'}):
            self.assertFalse(
                check({'host': 'tgbot.example.com', 'origin': 'https://evil.example'})
            )

    # ---- F-07 路由预言机与指纹 -------------------------------------------

    def test_route_oracle_is_gone(self):
        server = self._server()
        for method, path in (
            ('GET', '/api/auth/login'),
            ('GET', '/api/auth/logout'),
            ('POST', '/api/auth/logout'),
            ('POST', '/api/auth/me'),
            ('GET', '/api/definitely-missing'),
        ):
            with self.subTest(method=method, path=path):
                status, _, raw = self._request(server, method, path)
                self.assertEqual(401, status, raw)
                self.assertEqual('auth_required', json.loads(raw)['error_code'])

        # 有会话时才区分「不存在」，且形状与未授权响应不同也无妨（此时已认证）
        cookie = self._cookie(self._login(server)[1])
        status, _, raw = self._request(
            server, 'GET', '/api/definitely-missing', headers={'Cookie': cookie}
        )
        self.assertEqual(404, status)
        self.assertEqual('not_found', json.loads(raw)['error_code'])

    def test_fingerprint_is_not_leaked(self):
        server = self._server()

        status, headers, raw = self._request(server, 'OPTIONS', '/api/auth/login')
        self.assertEqual(405, status, raw)
        self.assertIn('GET', headers.get('allow', ''))
        self.assertNotIn('Unsupported method', raw)
        self.assertNotIn('Python', raw)
        self.assertNotIn('Python', headers.get('server', ''))

        status, _, raw = self._request(server, 'TRACE', '/')
        self.assertEqual(501, status)
        self.assertNotIn('Python', raw)
        self.assertNotIn('TRACE', raw)

        status, _, raw = self._request(server, 'HEAD', '/api/auth/login')
        self.assertEqual(405, status)
        self.assertEqual('', raw)

        with socket.create_connection(('127.0.0.1', server.port), timeout=10) as sock:
            sock.sendall(b'BAD-REQUEST-LINE\r\n\r\n')
            data = sock.recv(4096).decode('utf-8', 'replace')
        self.assertIn('http_', data)
        self.assertNotIn('Python', data)

    # ---- 回归：监听备份仍接受数组载荷 -------------------------------------

    def test_forward_watch_import_still_accepts_array_payload(self):
        server = self._server()
        cookie = self._cookie(self._login(server)[1])
        seen = []

        def fake_import(payload):
            seen.append(payload)
            return {'created': 0, 'skipped': 0, 'failed': 0, 'errors': [], 'watches': []}

        server.import_forward_watches = fake_import
        for body in ('[]', '{"watches": []}'):
            with self.subTest(body=body):
                status, _, raw = self._request(
                    server,
                    'POST',
                    '/api/watches/forward/import',
                    body=body,
                    headers={'Cookie': cookie, 'Content-Type': 'application/json'},
                )
                self.assertEqual(200, status, raw)
        self.assertEqual([[], {'watches': []}], seen)


if __name__ == '__main__':
    unittest.main()
