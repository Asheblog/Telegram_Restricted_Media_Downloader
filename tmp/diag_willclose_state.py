# coding=UTF-8
"""看清 will_close / sock 状态，定位"下一请求发向半关闭连接"。

逐步打印：response.version、will_close、conn.sock、以及 close() 调用后的状态。
"""
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

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    server = WebUiServer(store=TransferStore(directory=d), username="admin", password="pass")
    server.start(open_browser=False)
    port = server.port
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=4)

    def state(tag):
        print(f"  [{tag}] sock={conn.sock!r}")

    state("init")
    # 1) 未鉴权 submit
    conn.request("POST", "/api/auth/submit",
                 body=json.dumps({"phone": "+8615000000000"}),
                 headers={"Content-Type": "application/json"})
    r1 = conn.getresponse()
    print(f"  [submit] version={r1.version} will_close={r1.will_close} status={r1.status}")
    r1.read()
    state("after submit read")
    print(f"  [submit] response.closed={r1.isclosed()}")

    # 手动 close 连接后看状态
    conn.close()
    state("after conn.close()")

    # 2) login —— 同一连接对象（close 后应自动重连）
    t0 = time.time()
    try:
        conn.request("POST", "/api/auth/login",
                     body=json.dumps({"username": "admin", "password": "pass", "remember_me": True}),
                     headers={"Content-Type": "application/json"})
        r2 = conn.getresponse()
        print(f"  [login same-obj] status={r2.status} in {time.time()-t0:.2f}s")
        r2.read()
    except Exception as exc:
        print(f"  [login same-obj] {type(exc).__name__}: {exc} after {time.time()-t0:.2f}s")
    state("after login")
    conn.close()

    # 3) login —— 全新连接对象
    conn2 = http.client.HTTPConnection("127.0.0.1", port, timeout=4)
    t0 = time.time()
    try:
        conn2.request("POST", "/api/auth/login",
                      body=json.dumps({"username": "admin", "password": "pass", "remember_me": True}),
                      headers={"Content-Type": "application/json"})
        r3 = conn2.getresponse()
        print(f"  [login fresh-obj] status={r3.status} in {time.time()-t0:.2f}s")
        r3.read()
    except Exception as exc:
        print(f"  [login fresh-obj] {type(exc).__name__}: {exc} after {time.time()-t0:.2f}s")
    conn2.close()
    server.stop()
