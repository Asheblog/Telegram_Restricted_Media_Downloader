# coding=UTF-8
"""精确计量：真实 WebUiServer 上连续请求的失败率、本地端口复用、以及服务器是否已处理。

关键问题：
  Q1 失败是否只发生在「带 body 的 POST」上？
  Q2 失败时服务器是否已经回应/处理过该请求？（决定重试是否会重复执行副作用）
  Q3 失败是否与客户端本地端口被复用（同一 4 元组再次 connect）相关？

用法：.venv313\\Scripts\\python.exe tmp/flake-fix/probe_rate.py [N]
"""
import http.client
import json
import sys
import tempfile
import traceback

sys.path.insert(0, r"E:\codebase\tgbot")
sys.argv = [sys.argv[0]]

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()

from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.transfer_store import TransferStore  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
BODY = json.dumps({"phone": "+8615000000000"})


class CountingDiagnostic:
    def __init__(self):
        self.lines = []

    def info(self, message, *args):
        self.lines.append(("info", message % args if args else message))

    def warning(self, message, *args):
        self.lines.append(("warning", message % args if args else message))

    def exception(self, message, *args):
        self.lines.append(("exception", message % args if args else message))

    def status(self, message, *args):
        self.lines.append(("status", message % args if args else message))

    def count_responses(self):
        return sum(1 for _, line in self.lines if line.startswith("[WebUI] \""))


def run_phase(name, method, path, body, headers=None, iterations=N, quiet=False):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        store = TransferStore(directory=directory)
        diagnostic = CountingDiagnostic()
        server = WebUiServer(
            store=store, username="admin", password="pass", diagnostic=diagnostic
        )
        server.start(open_browser=False)
        conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
        used_ports = {}
        failures = []
        try:
            for index in range(iterations):
                before = diagnostic.count_responses()
                local_port = None
                try:
                    conn.request(method, path, body=body, headers=headers or {})
                    sock = conn.sock
                    local_port = sock.getsockname()[1] if sock else None
                    response = conn.getresponse()
                    response.read()
                    if response.status != 401:
                        failures.append(
                            (index, "unexpected_status", response.status, None, None)
                        )
                except Exception as exc:  # noqa: BLE001
                    served = diagnostic.count_responses() > before
                    failures.append(
                        (
                            index,
                            f"{type(exc).__name__}: {exc}",
                            None,
                            local_port,
                            served,
                        )
                    )
                    if not quiet:
                        print(f"    [{name}] #{index} FAIL port={local_port} "
                              f"server_responded={served} {type(exc).__name__}: {exc}",
                              flush=True)
                        traceback.print_exc()
                finally:
                    used_ports.setdefault(local_port, []).append(index)
            port_reuse = {
                port: indexes
                for port, indexes in used_ports.items()
                if port is not None and len(indexes) > 1
            }
            print(
                f"  {name:34s} iterations={iterations} failures={len(failures)} "
                f"distinct_local_ports={len(used_ports)} "
                f"reused_ports={len(port_reuse)}"
            )
            for index, message, status, local_port, served in failures:
                reuse = port_reuse.get(local_port, [])
                print(
                    f"      failure#{index} port={local_port} "
                    f"port_also_used_at={reuse} server_responded={served} "
                    f"status={status} {message}"
                )
            if not quiet and port_reuse:
                sample = list(port_reuse.items())[:5]
                print(f"      port reuse sample: {sample}")
            return used_ports, failures
        finally:
            conn.close()
            server.stop()


def main():
    print(f"iterations per phase = {N}")
    run_phase(
        "POST /api/auth/submit +body",
        "POST",
        "/api/auth/submit",
        BODY,
        {"Content-Type": "application/json"},
    )
    run_phase(
        "POST /api/auth/submit no-body",
        "POST",
        "/api/auth/submit",
        None,
        {"Content-Type": "application/json"},
    )
    run_phase("GET /api/auth/status", "GET", "/api/auth/status", None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
