# coding=UTF-8
"""量化：真实测试用的连接模式（复用连接 + helper 重放）在修复后的失败率。

不依赖 flake-fixer 的脚本假设，直接照 transfer_store_webui_case 的写法：
login 后在同一连接继续发请求；统计连接层异常次数。
"""
import http.client
import json
import os
import sys
import tempfile
import time
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.argv = [sys.argv[0]]

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()

from unit_tests.transfer_store_webui_case import connect_webui  # noqa: E402
from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.transfer_store import TransferStore  # noqa: E402

LABEL = sys.argv[1] if len(sys.argv) > 1 else "?"
ROUNDS = int(os.environ.get("ROUNDS", "40"))

conn_errors = 0
other_errors = 0
first_failure = ""
step_failures = {}
for i in range(ROUNDS):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        server = WebUiServer(
            store=TransferStore(directory=d), username="admin", password="pass"
        )
        server.start(open_browser=False)
        step = "start"
        try:
            conn = connect_webui(server)
            try:
                # 1) 未鉴权 POST（带 body）—— 竞态触发点
                step = "submit"
                t0 = time.time()
                conn.request(
                    "POST", "/api/auth/submit",
                    body=json.dumps({"phone": "+8615000000000"}),
                    headers={"Content-Type": "application/json"},
                )
                r = conn.getresponse(); r.read()
                assert r.status == 401, r.status
                print(f"  [r{i}] submit {r.status} {time.time()-t0:.2f}s", flush=True)
                # 2) 同一连接登录
                step = "login"
                t0 = time.time()
                conn.request(
                    "POST", "/api/auth/login",
                    body=json.dumps(
                        {"username": "admin", "password": "pass", "remember_me": True}
                    ),
                    headers={"Content-Type": "application/json"},
                )
                r = conn.getresponse(); r.read()
                assert r.status == 200, r.status
                print(f"  [r{i}] login  {r.status} {time.time()-t0:.2f}s", flush=True)
                # 3) 同一连接带 cookie 访问
                step = "status"
                cookie = r.getheader("Set-Cookie")
                t0 = time.time()
                conn.request("GET", "/api/auth/status", headers={"Cookie": cookie.split(";", 1)[0]})
                r = conn.getresponse(); r.read()
                assert r.status == 200, r.status
                print(f"  [r{i}] status {r.status} {time.time()-t0:.2f}s", flush=True)
            finally:
                conn.close()
        except ConnectionError as exc:
            conn_errors += 1
            step_failures[step] = step_failures.get(step, 0) + 1
            if not first_failure:
                first_failure = f"{step}: {type(exc).__name__}: {exc}"
        except Exception as exc:
            other_errors += 1
            step_failures[step] = step_failures.get(step, 0) + 1
            if not first_failure:
                first_failure = f"{step}: {type(exc).__name__}: {exc}"
        finally:
            server.stop()

print(f"[{LABEL}] rounds={ROUNDS} connection_errors={conn_errors} other_errors={other_errors} "
      f"rate={100*conn_errors/ROUNDS:.1f}% steps={step_failures} first={first_failure[:110]}")
