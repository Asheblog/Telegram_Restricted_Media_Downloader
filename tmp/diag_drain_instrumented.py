# coding=UTF-8
"""插桩：记录每次 _drain_request_body 的请求路径、声明长度、实读字节、耗时。

用真实 WebUiServer + 同一连接上的「未鉴权 POST(submit) → POST(login)」序列。
"""
import http.client
import json
import os
import sys
import tempfile
import threading
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.argv = [sys.argv[0]]

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()

import module.adapters.webui.server as srv_mod  # noqa: E402
from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.transfer_store import TransferStore  # noqa: E402

# handler 类是 WebUiServer.start() 里的嵌套类；直接给基类打桩即可被继承。
from http.server import BaseHTTPRequestHandler  # noqa: E402

handler_cls = BaseHTTPRequestHandler
print("patched base class:", handler_cls)
orig = handler_cls._drain_request_body


def patched(self):
    t0 = time.time()
    raw_len = (self.headers.get("content-length") if self.headers else None)
    # 复制原逻辑但记录实读
    read_total = 0
    if self.command and self.headers and raw_len:
        try:
            rem = int(raw_len)
        except (TypeError, ValueError):
            rem = 0
        while rem > 0:
            try:
                chunk = self.rfile.read(min(rem, 65536))
            except OSError as exc:
                print(f"  [drain] {self.command} {self.path} declared={raw_len} "
                      f"read={read_total} OSError={type(exc).__name__} t={time.time()-t0:.2f}s")
                self.close_connection = True
                return
            if not chunk:
                break
            read_total += len(chunk)
            rem -= len(chunk)
    print(f"  [drain] {self.command} {self.path} declared={raw_len} read={read_total} "
          f"t={time.time()-t0:.2f}s")
    return orig(self)


handler_cls._drain_request_body = patched

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    server = WebUiServer(store=TransferStore(directory=d), username="admin", password="pass")
    server.start(open_browser=False)
    port = server.port
    print(f"server on {port}\n")

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=8)
    steps = [
        ("POST", "/api/auth/submit", {"phone": "+8615000000000"}),
        ("GET", "/api/auth/status", None),
        ("POST", "/api/auth/login", {"username": "admin", "password": "pass", "remember_me": True}),
        ("GET", "/api/auth/status", None),
    ]
    for method, path, payload in steps:
        body = json.dumps(payload) if payload is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        t0 = time.time()
        try:
            conn.request(method, path, body=body, headers=headers)
            resp = conn.getresponse()
            resp.read()
            print(f"-> {method} {path}: {resp.status} in {time.time()-t0:.2f}s")
        except Exception as exc:
            print(f"-> {method} {path}: {type(exc).__name__}: {exc} after {time.time()-t0:.2f}s")
            break
    conn.close()
    print("\nthreads:", [t.name for t in threading.enumerate()])
    server.stop()
