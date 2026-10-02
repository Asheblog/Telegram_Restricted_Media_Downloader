# coding=UTF-8
"""用裸 socket 逐步复现「未鉴权 POST → 再发 login」序列，短超时定位卡点。

每一步都显式打印：发出去多少、收到多少。客户端用 2s 超时，卡住就立刻暴露。
"""
import json
import os
import socket
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


def read_response(sock, label, timeout=2.0):
    sock.settimeout(timeout)
    t0 = time.time()
    buf = b""
    try:
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
        head, _, rest = buf.partition(b"\r\n\r\n")
        status_line = head.split(b"\r\n", 1)[0]
        clen = 0
        for line in head.split(b"\r\n")[1:]:
            if line.lower().startswith(b"content-length:"):
                clen = int(line.split(b":", 1)[1].strip())
        while len(rest) < clen:
            chunk = sock.recv(65536)
            if not chunk:
                break
            rest += chunk
        print(f"  [{label}] {status_line.decode()} body={len(rest)}B in {time.time()-t0:.2f}s")
        return True
    except Exception as exc:
        print(f"  [{label}] {type(exc).__name__}: {exc} after {time.time()-t0:.2f}s")
        return False


with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    server = WebUiServer(store=TransferStore(directory=d), username="admin", password="pass")
    server.start(open_browser=False)
    port = server.port
    print(f"server on {port}\n")

    submit_body = json.dumps({"phone": "+8615000000000"}).encode()
    login_body = json.dumps(
        {"username": "admin", "password": "pass", "remember_me": True}
    ).encode()

    # ── A. 独立连接：每个请求一条全新 TCP 连接（最干净的对照） ──
    print("A) 每请求独立连接")
    for label, path, body in (
        ("submit#1", "/api/auth/submit", submit_body),
        ("submit#2", "/api/auth/submit", submit_body),
    ):
        s = socket.create_connection(("127.0.0.1", port), timeout=5)
        s.sendall(
            b"POST " + path.encode() + b" HTTP/1.1\r\nHost: x\r\n"
            b"Content-Type: application/json\r\nContent-Length: "
            + str(len(body)).encode() + b"\r\n\r\n" + body
        )
        read_response(s, label)
        s.close()

    # ── B. 同一连接：submit → login（这是复现脚本的序列） ──
    print("\nB) 同一连接：submit → login")
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    for label, path, body in (
        ("submit", "/api/auth/submit", submit_body),
        ("login", "/api/auth/login", login_body),
    ):
        s.sendall(
            b"POST " + path.encode() + b" HTTP/1.1\r\nHost: x\r\n"
            b"Content-Type: application/json\r\nContent-Length: "
            + str(len(body)).encode() + b"\r\n\r\n" + body
        )
        if not read_response(s, label):
            break
    s.close()

    server.stop()
    print("\ndone")
