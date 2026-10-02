# coding=UTF-8
"""超限声明（Content-Length > 上限）时，客户端能否稳定拿到 413？

该分支刻意不预读 body（避免吃巨量内存），因此套接字里仍留未读字节 ——
本脚本用延迟读取放大，检查是否仍会丢响应。
"""
import http.client
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

from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.transfer_store import TransferStore  # noqa: E402

ROUNDS = 10
OVERSIZED = 9 * 1024 * 1024


def login(port):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request(
            "POST", "/api/auth/login",
            body=json.dumps({"username": "admin", "password": "pass", "remember_me": True}),
            headers={"Content-Type": "application/json"},
        )
        r = conn.getresponse()
        r.read()
        return r.getheader("Set-Cookie").split(";", 1)[0]
    finally:
        conn.close()


with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    server = WebUiServer(store=TransferStore(directory=d), username="admin", password="pass")
    server.start(open_browser=False)
    port = server.port
    cookie = login(port)

    ok = fail = 0
    for i in range(ROUNDS):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
        try:
            conn.putrequest("POST", "/api/tasks")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", str(OVERSIZED))
            conn.putheader("Cookie", cookie)
            conn.endheaders()
            conn.send(b"x" * 1024)  # 只发 1KB
            time.sleep(0.05)        # 放大：若会丢响应，这里必现
            r = conn.getresponse()
            body = r.read()
            if r.status == 413:
                ok += 1
            else:
                fail += 1
                print(f"  [{i}] unexpected status={r.status} {body[:60]!r}")
        except Exception as exc:
            fail += 1
            print(f"  [{i}] {type(exc).__name__}: {exc}")
        finally:
            conn.close()
    server.stop()

print(f"oversized: rounds={ROUNDS} got_413={ok} failed={fail}")
