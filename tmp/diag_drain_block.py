# coding=UTF-8
"""诊断：_drain_request_body 为什么阻塞。

用真实 WebUiServer，手动在裸 socket 上发一个"带 body 的未鉴权 POST"，
把服务端读了多少、卡在哪打印出来。
"""
import json
import os
import socket
import sys
import tempfile
import threading
import time
import traceback

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
    print(f"server on {port}")

    body = json.dumps({"phone": "+8615000000000"}).encode()
    print(f"body len = {len(body)}")

    # 1) 裸 socket：把请求头 + body 一次性发出去，观察服务器是否回 401
    raw = socket.create_connection(("127.0.0.1", port), timeout=10)
    raw.settimeout(10)
    req = (
        b"POST /api/auth/submit HTTP/1.1\r\n"
        b"Host: 127.0.0.1\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: " + str(len(body)).encode() + b"\r\n"
        b"\r\n" + body
    )
    raw.sendall(req)
    try:
        data = raw.recv(4096)
        print(f"[raw] got {len(data)} bytes: {data[:120]!r}")
    except Exception as exc:
        print(f"[raw] recv failed: {type(exc).__name__}: {exc}")
    raw.close()

    # 2) http.client：分两步，先 request 再 getresponse，测量耗时
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    t0 = time.time()
    conn.request(
        "POST", "/api/auth/submit", body=body,
        headers={"Content-Type": "application/json"},
    )
    t1 = time.time()
    try:
        resp = conn.getresponse()
        print(f"[client] status={resp.status} request={t1-t0:.2f}s getresponse={time.time()-t1:.2f}s")
    except Exception as exc:
        print(f"[client] FAILED after {time.time()-t0:.2f}s: {type(exc).__name__}: {exc}")
    conn.close()

    # 3) 再发一次，看服务器线程是否已被前一次卡死
    conn2 = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    t0 = time.time()
    try:
        conn2.request("GET", "/api/auth/status")
        resp = conn2.getresponse()
        print(f"[client2] status={resp.status} in {time.time()-t0:.2f}s")
    except Exception as exc:
        print(f"[client2] FAILED after {time.time()-t0:.2f}s: {type(exc).__name__}: {exc}")
    conn2.close()

    print("threads:", [t.name for t in threading.enumerate()])
    server.stop()
