# coding=UTF-8
"""最小实验：确认 Windows 上「服务器发完响应后立刻 RST」对客户端读响应的影响。

三个子实验，各跑 N 次：
  LINGER0_NOW   服务端读掉 headers、**不读 body**，发完响应后 SO_LINGER(0) 强制 RST；
                客户端立刻读响应。
  LINGER0_DELAY 同上，但客户端 sleep 50ms 再读。
  FIN           服务端读掉 headers、不读 body，正常 close（不强制 RST）；
                客户端立刻读响应。

用途：判断「服务器带未读 body 关闭」是否会让客户端**丢掉已经写出的响应**，
以及延迟读取是否能稳定触发失败。
"""
import http.client
import json
import socket
import sys
import threading
import time
import traceback

ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
DELAY = 0.05


def serve_once(listener, mode):
    """accept 一个连接：读完 headers（保留 body 未读），回 401，按 mode 关闭。"""
    conn, _ = listener.accept()
    try:
        conn.settimeout(5)
        buffer = b""
        while b"\r\n\r\n" not in buffer:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buffer += chunk
        # 注意：故意不去读 Content-Length 指定的 body，模拟服务器「未读 body 就回应」。
        response = (
            b"HTTP/1.0 401 Unauthorized\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: 38\r\n"
            b"\r\n"
            b'{"error_code": "auth_required", "error": ""}'
        )
        conn.sendall(response)
        if mode.startswith("LINGER0"):
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b"\x01\x00\x00\x00\x00\x00\x00\x00")
        time.sleep(0.001)
    finally:
        conn.close()


def run_case(mode, delay):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)
    port = listener.getsockname()[1]
    thread = threading.Thread(target=serve_once, args=(listener, mode), daemon=True)
    thread.start()

    outcome = {"ok": 0, "error": 0}
    details = []
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request(
            "POST",
            "/api/auth/submit",
            body=json.dumps({"phone": "+8615000000000"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        if delay:
            time.sleep(delay)
        try:
            response = conn.getresponse()
            raw = response.read()
            outcome["ok"] += 1
            details.append(f"ok status={response.status} body={raw[:40]!r}")
        except Exception as exc:  # noqa: BLE001
            outcome["error"] += 1
            details.append(f"{type(exc).__name__}: {exc}")
        finally:
            conn.close()
    finally:
        listener.close()
        thread.join(timeout=2)
    return outcome, details


def main():
    for mode, delay in (
        ("LINGER0_NOW", 0),
        ("LINGER0_DELAY", DELAY),
        ("FIN", 0),
        ("FIN_DELAY", DELAY),
    ):
        ok = errors = 0
        samples = []
        for _ in range(ROUNDS):
            outcome, details = run_case("LINGER0" if mode.startswith("LINGER0") else "FIN", delay)
            ok += outcome["ok"]
            errors += outcome["error"]
            if len(samples) < 3:
                samples.extend(details)
        print(f"{mode:14s} rounds={ROUNDS} ok={ok} errors={errors} samples={samples}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
