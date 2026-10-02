# coding=UTF-8
"""确定性验证 WebUiTestConnection 的重放语义（不依赖 OS 竞态概率）。

用一个「按脚本逐连接处理」的裸 TCP 服务器精确制造各种客户端可见状况。
服务器总是先读完整个请求（含 body，保证客户端 write 一定成功，与真实服务器一致），
再按脚本动作收尾：
  respond:STATUS:PAYLOAD  回一个完整响应
  close                   不回任何响应、优雅关闭 -> 客户端 getresponse 抛 RemoteDisconnected
  reset                   等 2ms 后 SO_LINGER(0) 强制 RST -> ConnectionAborted/ResetError
  garbage                 回畸形状态行 -> BadStatusLine
  partial                 回半个状态行后 RST

断言：
  1. close 一次后恢复正常    -> 透明重放并拿到真实 401，共 accept 2 次，replayed=1
  2. close 到底              -> 抛 ConnectionError（不吞），恰好 accept MAX_REPLAYS+1 次
  3. reset 一次后恢复正常    -> 同样透明重放（真实竞态里客户端看到的就是这一类异常）
  4. 完整 404/500 响应       -> 原样返回，只 accept 1 次、replayed=0（HTTP 层绝不重放）
  5. 不带 body 的请求失败    -> 立即抛错，只 accept 1 次（不重放）
  6. 畸形状态行              -> BadStatusLine 抛出，只 accept 1 次（不重放）

用法：.venv313\\Scripts\\python.exe tmp/flake-fix/verify_helper.py
"""
import json
import socket
import struct
import sys
import threading
import time
from types import SimpleNamespace

REPO = r"E:\codebase\tgbot"
sys.path.insert(0, REPO)
sys.argv = [sys.argv[0]]

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()

from unit_tests.transfer_store_webui_case import (  # noqa: E402
    WebUiTestConnection,
    connect_webui,
)

BODY = json.dumps({"phone": "+8615000000000"})


class ScriptedServer:
    """按脚本逐连接服务；脚本用尽后一直重复最后一条。"""

    def __init__(self, script):
        self.script = list(script)
        self.connections = []
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(8)
        self.host, self.port = self.listener.getsockname()
        self._stop = False
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    @staticmethod
    def _read_request(conn):
        """读完整个请求（head + Content-Length 指定的 body）。"""
        buffer = b""
        while b"\r\n\r\n" not in buffer:
            chunk = conn.recv(65536)
            if not chunk:
                break
            buffer += chunk
        head, _, rest = buffer.partition(b"\r\n\r\n")
        content_length = 0
        for line in head.split(b"\r\n")[1:]:
            if line.lower().startswith(b"content-length:"):
                content_length = int(line.split(b":", 1)[1].strip())
        while len(rest) < content_length:
            chunk = conn.recv(65536)
            if not chunk:
                break
            rest += chunk
        return head, rest

    def _serve(self):
        index = 0
        while not self._stop:
            try:
                conn, _ = self.listener.accept()
            except OSError:
                return
            try:
                head, _body = self._read_request(conn)
                action = self.script[min(index, len(self.script) - 1)]
                self.connections.append((index, action, head.split(b"\r\n")[0]))
                index += 1
                if action == "reset":
                    # 等客户端 write 落地（真实服务器也是先读完 head 才回应/关闭）
                    time.sleep(0.002)
                    conn.setsockopt(
                        socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("hh", 1, 0)
                    )
                elif action == "garbage":
                    conn.sendall(b"THIS IS NOT HTTP\r\n\r\n")
                elif action == "partial":
                    conn.sendall(b"HTTP/1.0 4")
                    conn.setsockopt(
                        socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("hh", 1, 0)
                    )
                elif action.startswith("respond|"):
                    _, status, payload = action.split("|", 2)
                    data = payload.encode("utf-8")
                    conn.sendall(
                        f"HTTP/1.0 {status} X\r\n".encode()
                        + b"Content-Type: application/json\r\n"
                        + f"Content-Length: {len(data)}\r\n\r\n".encode()
                        + data
                    )
            finally:
                conn.close()

    def stop(self):
        self._stop = True
        self.listener.close()
        self.thread.join(timeout=2)


def scenario(name, script, method, path, body, expect):
    server = ScriptedServer(script)
    conn = connect_webui(SimpleNamespace(host=server.host, port=server.port))
    result = None
    error = None
    try:
        conn.request(
            method,
            path,
            body=body,
            headers={"Content-Type": "application/json"} if body else {},
        )
        response = conn.getresponse()
        payload = response.read().decode("utf-8")
        result = (response.status, payload)
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    finally:
        conn.close()
        server.stop()
    accepts = len(server.connections)
    replayed = conn.replayed_requests
    match = (
        (expect.get("accepts") is None or expect["accepts"] == accepts)
        and (expect.get("replayed") is None or expect["replayed"] == replayed)
        and (expect.get("status") is None or (result or (None,))[0] == expect["status"])
        and (
            expect.get("error_type") is None
            or (error or "").startswith(expect["error_type"])
        )
        and (expect.get("no_error") is None or (error is None) == expect["no_error"])
    )
    print(f"--- {name}")
    print(f"    accepts={accepts} replayed={replayed} result={result} error={error}")
    print(f"    expected: {expect}")
    print(f"    => {'PASS' if match else 'FAIL'}")
    return match


def main():
    max_replays = WebUiTestConnection.MAX_REPLAYS
    results = []
    results.append(
        scenario(
            "1) close 一次后正常：透明重放并拿到真实 401",
            ["close", 'respond|401|{"error_code": "auth_required"}'],
            "POST",
            "/api/auth/submit",
            BODY,
            {"accepts": 2, "replayed": 1, "status": 401, "no_error": True},
        )
    )
    results.append(
        scenario(
            "2) 一直失败：必须在 MAX_REPLAYS 次后把 ConnectionError 抛给测试",
            ["close"],
            "POST",
            "/api/auth/submit",
            BODY,
            {"accepts": max_replays + 1, "replayed": max_replays,
             "error_type": "RemoteDisconnected"},
        )
    )
    results.append(
        scenario(
            "3) RST 一次后正常：真实竞态同类异常同样透明重放",
            ["reset", 'respond|401|{"error_code": "auth_required"}'],
            "POST",
            "/api/auth/submit",
            BODY,
            {"accepts": 2, "replayed": 1, "status": 401, "no_error": True},
        )
    )
    results.append(
        scenario(
            "4a) 完整 404：原样返回、不重放（真实 HTTP 错误不被吞）",
            ['respond|404|{"error_code": "not_found"}'],
            "POST",
            "/api/forwards",
            BODY,
            {"accepts": 1, "replayed": 0, "status": 404, "no_error": True},
        )
    )
    results.append(
        scenario(
            "4b) 完整 500：原样返回、不重放",
            ['respond|500|{"error_code": "internal_error"}'],
            "POST",
            "/api/tasks",
            BODY,
            {"accepts": 1, "replayed": 0, "status": 500, "no_error": True},
        )
    )
    results.append(
        scenario(
            "4c) 完整 401：原样返回、不重放（鉴权失败照旧失败）",
            ['respond|401|{"error_code": "auth_required"}'],
            "POST",
            "/api/auth/submit",
            BODY,
            {"accepts": 1, "replayed": 0, "status": 401, "no_error": True},
        )
    )
    results.append(
        scenario(
            "5) 不带 body 的请求失败：不重放，直接抛错",
            ["close"],
            "GET",
            "/api/auth/status",
            None,
            {"accepts": 1, "replayed": 0, "error_type": "RemoteDisconnected"},
        )
    )
    results.append(
        scenario(
            "6) 畸形状态行：不重放，抛 BadStatusLine",
            ["garbage"],
            "POST",
            "/api/auth/submit",
            BODY,
            {"accepts": 1, "replayed": 0, "error_type": "BadStatusLine"},
        )
    )
    results.append(
        scenario(
            "7) 半个状态行后 RST：响应不完整，允许重放；脚本用尽后仍抛错",
            ["partial"],
            "POST",
            "/api/auth/submit",
            BODY,
            {"accepts": max_replays + 1, "replayed": max_replays,
             "error_type": "Connection"},
        )
    )
    print(f"\n=== {sum(1 for r in results if r)}/{len(results)} PASS ===")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
