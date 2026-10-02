# coding=UTF-8
"""复现 / 验证脚本：带 body 的请求被服务器「未读 body 就关闭」时的 TCP 竞态。

用法：
    .venv313\\Scripts\\python.exe tmp/flake-fix/repro_login_reuse.py [key=value ...]

参数（脚本会清空 sys.argv，故用 key=value）：
    rounds=<N>        轮数（默认 30），每轮启动一个全新的 WebUiServer
    variant=<name>    same-conn（默认，同一连接串联请求，等同测试文件写法）
                      fresh-conn（每次请求新建 HTTPConnection，用于证明「换连接」无用）
    loops=<K>         每轮先重复 K 次「带 body 的 POST /api/auth/submit 期望 401」（默认 1）
                      —— 这是竞态的放大器：每多一次机会就多一次掷骰子
    body=<0|1>        该 POST 是否携带 JSON body（默认 1；body=0 是机理对照）
    sleep=<seconds>   每个请求之间 sleep（默认 0）
    delay-read=<sec>  在 request() 与 getresponse() 之间 sleep —— 确定性放大器：
                      服务器发完响应后立刻 RST，延迟读取必然让 RST 先到并冲掉响应字节
    fix=<0|1>         是否复用 unit_tests/transfer_store_webui_case.py 里的连接工厂
                      （fix=1 用于验证修复后的代码路径）
    verbose           打印每轮 socket 状态迁移

每轮的请求序列：
    1) K 次 POST /api/auth/submit（带 body，未鉴权）  -> 401   <- 竞态发生点
    2) GET  /api/auth/status                          -> 401
    3) POST /api/auth/login（同一个连接）              -> 200
    4) GET  /api/auth/status（同一个连接 + cookie）    -> 200
"""
import http.client
import json
import os
import sys
import tempfile
import time
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
CLI_ARGS = list(sys.argv[1:])
sys.argv = [sys.argv[0]]

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()

from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.transfer_store import TransferStore  # noqa: E402

CONNECTION_ERRORS = (
    ConnectionError,
    http.client.BadStatusLine,
    http.client.RemoteDisconnected,
)


def parse_cli():
    options = {
        "rounds": 30,
        "variant": "same-conn",
        "loops": 1,
        "body": 1,
        "sleep": 0.0,
        "delay_read": 0.0,
        "fix": 0,
        "verbose": False,
    }
    for raw in CLI_ARGS:
        if raw == "verbose":
            options["verbose"] = True
        elif "=" in raw:
            key, value = raw.split("=", 1)
            if key in ("rounds", "loops", "body", "fix"):
                options[key] = int(value)
            elif key == "sleep":
                options[key] = float(value)
            elif key == "delay-read":
                options["delay_read"] = float(value)
            elif key == "variant":
                options[key] = value
    return options


def sock_state(conn):
    sock = conn.sock
    if sock is None:
        return "None"
    try:
        return f"{sock.getsockname()[1]}"
    except OSError:
        return "closed"


def build_connection_factory(use_fix):
    if use_fix:
        from unit_tests.transfer_store_webui_case import connect_webui

        return connect_webui

    def plain_factory(server, timeout=5):
        return http.client.HTTPConnection(server.host, server.port, timeout=timeout)

    return plain_factory


class Client:
    """按 variant 决定复用同一个 HTTPConnection，还是每次请求新建。"""

    def __init__(self, server, options):
        self.server = server
        self.options = options
        self.factory = build_connection_factory(options["fix"])
        self.fresh_per_request = options["variant"].startswith("fresh-conn")
        self.conn = self.factory(server, timeout=5)

    def _connection(self):
        if self.fresh_per_request:
            self.conn = self.factory(self.server, timeout=5)
        return self.conn

    def send(self, name, method, path, body=None, headers=None, trace=None):
        conn = self._connection()
        record = {
            "step": name,
            "method": method,
            "path": path,
            "sock_before": None,
            "local_port": None,
        }
        if trace is not None:
            trace.append(record)
        record["sock_before"] = sock_state(conn)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            record["local_port"] = sock_state(conn)
            if self.options["delay_read"]:
                time.sleep(self.options["delay_read"])
            response = conn.getresponse()
            raw = response.read()
        except Exception as exc:  # noqa: BLE001 - 记录失败步骤后原样抛出
            exc.flake_step = name
            exc.flake_record = record
            raise
        record["status"] = response.status
        return response, json.loads(raw.decode("utf-8"))

    def close(self):
        self.conn.close()


def run_round(index, options):
    trace = [] if options["verbose"] else None
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        store = TransferStore(directory=directory)
        server = WebUiServer(store=store, username="admin", password="pass")
        server.start(open_browser=False)
        client = Client(server, options)
        try:
            post_body = json.dumps({"phone": "+8615000000000"}) if options["body"] else None
            for loop in range(options["loops"]):
                response, payload = client.send(
                    f"unauth_submit#{loop + 1}",
                    "POST",
                    "/api/auth/submit",
                    body=post_body,
                    headers={"Content-Type": "application/json"},
                    trace=trace,
                )
                if response.status != 401:
                    raise AssertionError(
                        f"[unauth_submit] 期望 401，实际 {response.status}: {payload}"
                    )
                if payload.get("error_code") != "auth_required":
                    raise AssertionError(f"[unauth_submit] error_code={payload}")
                if options["sleep"]:
                    time.sleep(options["sleep"])
            response, payload = client.send(
                "unauth_status", "GET", "/api/auth/status", headers={}, trace=trace
            )
            if response.status != 401:
                raise AssertionError(
                    f"[unauth_status] 期望 401，实际 {response.status}: {payload}"
                )
            if payload.get("error_code") != "auth_required":
                raise AssertionError(f"[unauth_status] error_code={payload}")
            response, payload = client.send(
                "login",
                "POST",
                "/api/auth/login",
                body=json.dumps(
                    {"username": "admin", "password": "pass", "remember_me": True}
                ),
                headers={"Content-Type": "application/json"},
                trace=trace,
            )
            if response.status != 200:
                raise AssertionError(f"[login] HTTP {response.status}: {payload}")
            cookie = response.getheader("Set-Cookie")
            if not cookie:
                raise AssertionError("[login] 缺少 Set-Cookie")
            response, payload = client.send(
                "auth_status_after_login",
                "GET",
                "/api/auth/status",
                headers={"Cookie": cookie.split(";", 1)[0]},
                trace=trace,
            )
            if response.status != 200:
                raise AssertionError(
                    f"[auth_status] 期望 200，实际 {response.status}: {payload}"
                )
            if payload.get("step") != "none":
                raise AssertionError(f"[auth_status] step={payload}")
        finally:
            client.close()
            server.stop()
    return trace


def main():
    options = parse_cli()
    failures = []
    traces = []
    for index in range(1, options["rounds"] + 1):
        try:
            trace = run_round(index, options)
            if trace:
                traces.append(trace)
            print(f"[round {index:03d}] ok", flush=True)
        except Exception as exc:  # noqa: BLE001
            failures.append((index, exc))
            kind = "CONNECTION-FLAKE" if isinstance(exc, CONNECTION_ERRORS) else "FAIL"
            step = getattr(exc, "flake_step", "?")
            record = getattr(exc, "flake_record", {})
            print(
                f"[round {index:03d}] {kind} step={step} {type(exc).__name__}: {exc}",
                flush=True,
            )
            print(f"    record={record}", flush=True)
            print(traceback.format_exc(), flush=True)

    if options["verbose"]:
        print(
            "\n=== socket 状态迁移样本（sock_before=请求前 sock；local_port=本次连接本地端口）==="
        )
        for trace in traces[:3]:
            for record in trace:
                print(
                    f"  {record['step']:24s} {record['method']:6s} {record['path']:22s} "
                    f"sock_before={record['sock_before']:>6s} "
                    f"local_port={record['local_port']:>6s} status={record.get('status')}"
                )
            print("  ---")

    attempts = options["rounds"] * (options["loops"] + 3)
    connection_flakes = sum(
        1 for _, exc in failures if isinstance(exc, CONNECTION_ERRORS)
    )
    print(
        f"\n=== fix={options['fix']} variant={options['variant']} body={options['body']} "
        f"sleep={options['sleep']} delay_read={options['delay_read']} "
        f"rounds={options['rounds']} loops={options['loops']} "
        f"requests≈{attempts} failures={len(failures)} "
        f"connection_flakes={connection_flakes} "
        f"rate={len(failures) / options['rounds']:.2%} ==="
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
