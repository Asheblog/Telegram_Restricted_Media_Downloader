# coding=UTF-8
"""隔离：全新 server 上直接 login，以及 submit 之后 login，定位服务器行为。"""
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.argv = [sys.argv[0]]

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()

import http.client  # noqa: E402

from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.transfer_store import TransferStore  # noqa: E402

LOGIN = {"username": "admin", "password": "pass", "remember_me": True}


def call(port, method, path, payload=None, cookie=None, timeout=4):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    headers = {}
    body = None
    if payload is not None:
        body = json.dumps(payload)
        headers["Content-Type"] = "application/json"
    if cookie:
        headers["Cookie"] = cookie
    t0 = time.time()
    try:
        conn.request(method, path, body=body, headers=headers)
        r = conn.getresponse()
        data = r.read()
        return f"{r.status} in {time.time()-t0:.2f}s body={data[:60]!r}"
    except Exception as exc:
        return f"{type(exc).__name__}: {exc} after {time.time()-t0:.2f}s"
    finally:
        conn.close()


print("=== A) 全新 server，直接 login（无前置 submit）===")
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    s = WebUiServer(store=TransferStore(directory=d), username="admin", password="pass")
    s.start(open_browser=False)
    print("  login:", call(s.port, "POST", "/api/auth/login", LOGIN))
    s.stop()

print("\n=== B) 先 submit（未鉴权），再 login ===")
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    s = WebUiServer(store=TransferStore(directory=d), username="admin", password="pass")
    s.start(open_browser=False)
    print("  submit:", call(s.port, "POST", "/api/auth/submit", {"phone": "+8615000000000"}))
    print("  login :", call(s.port, "POST", "/api/auth/login", LOGIN))
    s.stop()

print("\n=== C) 先 GET 未鉴权，再 login（不带 body 的前置请求）===")
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    s = WebUiServer(store=TransferStore(directory=d), username="admin", password="pass")
    s.start(open_browser=False)
    print("  get   :", call(s.port, "GET", "/api/auth/status"))
    print("  login :", call(s.port, "POST", "/api/auth/login", LOGIN))
    s.stop()

print("\n=== D) 连续 3 次 login（正确口令）===")
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    s = WebUiServer(store=TransferStore(directory=d), username="admin", password="pass")
    s.start(open_browser=False)
    for i in range(3):
        print(f"  login#{i+1}:", call(s.port, "POST", "/api/auth/login", LOGIN))
    s.stop()
