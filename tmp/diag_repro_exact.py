# coding=UTF-8
"""精确重放 repro 的「同连接 + delay-read」序列，逐步打印服务端到底回了什么。

序列（每轮一个全新 server）：
  K 次 POST /api/auth/submit（带 body，未鉴权）-> 期望 401
  GET  /api/auth/status                        -> 期望 401
  POST /api/auth/login                         -> 期望 200
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


def send_and_read(sock, method, path, body=None, delay=0.0, label="", keep_alive=False):
    """发一个请求；若 delay>0 先睡再读（复刻 repro 的 delay-read）。

    keep_alive=False：不声明 Connection（HTTP/1.0 语义 = 应答后关闭，客户端应重连）。
    keep_alive=True ：声明 Connection: keep-alive（要求服务器复用连接）。
    """
    payload = json.dumps(body).encode() if body is not None else b""
    headers = f"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n"
    if keep_alive:
        headers += "Connection: keep-alive\r\n"
    if payload:
        headers += f"Content-Type: application/json\r\nContent-Length: {len(payload)}\r\n"
    raw = headers.encode() + b"\r\n" + payload
    sock.sendall(raw)
    if delay:
        time.sleep(delay)
    sock.settimeout(3)
    buf = b""
    try:
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                print(f"    [{label}] peer closed, got {len(buf)}B")
                return None
            buf += chunk
    except Exception as exc:
        print(f"    [{label}] recv FAILED: {type(exc).__name__}: {exc} (got {len(buf)}B)")
        return None
    head, _, rest = buf.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    status = lines[0].decode("latin-1")
    conn_hdr = [l.decode() for l in lines if l.lower().startswith(b"connection:")]
    clen = 0
    for l in lines:
        if l.lower().startswith(b"content-length:"):
            clen = int(l.split(b":", 1)[1])
    while len(rest) < clen:
        chunk = sock.recv(65536)
        if not chunk:
            break
        rest += chunk
    print(f"    [{label}] {status} | {conn_hdr} | body={len(rest)}B")
    if label == "submit#1":
        print("    ---- 完整响应头 ----")
        for line in lines:
            print("      " + line.decode("latin-1"))
    return status


for delay in (0.0, 0.05):
    print(f"\n===== delay-read={delay}（不声明 keep-alive，符合 HTTP/1.0 语义）=====")
    for ka in (False, True):
        print(f"  --- keep_alive_header={ka} ---")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            server = WebUiServer(
                store=TransferStore(directory=d), username="admin", password="pass"
            )
            server.start(open_browser=False)
            port = server.port
            s = socket.create_connection(("127.0.0.1", port), timeout=5)
            for i in range(2):
                r = send_and_read(
                    s, "POST", "/api/auth/submit",
                    {"phone": "+8615000000000"}, delay, f"submit#{i+1}", keep_alive=ka,
                )
                if r is None:
                    break
            else:
                if send_and_read(s, "GET", "/api/auth/status", None, delay, "status", ka) is not None:
                    send_and_read(
                        s, "POST", "/api/auth/login",
                        {"username": "admin", "password": "pass", "remember_me": True},
                        delay, "login", ka,
                    )
            s.close()
            server.stop()
print("\ndone")
