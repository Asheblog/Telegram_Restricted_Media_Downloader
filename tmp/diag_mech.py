# coding=UTF-8
"""确定性对照：带 body 的未鉴权 POST + 延迟读取，统计客户端丢响应的次数。

用法（不修改仓库文件，由外部用 git stash 控制 server.py 版本）：
    python tmp/diag_mech.py <label>
"""
import http.client
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
LABEL = sys.argv[1] if len(sys.argv) > 1 else "unknown"
sys.argv = [sys.argv[0]]

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()

from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.transfer_store import TransferStore  # noqa: E402

ROUNDS = 15
DELAY = 0.05

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
    server = WebUiServer(
        store=TransferStore(directory=d), username="admin", password="pass"
    )
    server.start(open_browser=False)
    port = server.port
    body = json.dumps({"phone": "+8615000000000"}).encode()
    ok = fail = 0
    kinds = {}
    for _ in range(ROUNDS):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=6)
        try:
            conn.request(
                "POST", "/api/auth/submit", body=body,
                headers={"Content-Type": "application/json"},
            )
            time.sleep(DELAY)  # 让服务端关闭连接/RST 先于我们读取
            resp = conn.getresponse()
            resp.read()
            ok += 1
        except Exception as exc:
            fail += 1
            kinds[type(exc).__name__] = kinds.get(type(exc).__name__, 0) + 1
        finally:
            conn.close()
    server.stop()

print(f"[{LABEL}] rounds={ROUNDS} delay={DELAY}s ok={ok} fail={fail} "
      f"rate={100*fail/ROUNDS:.1f}% kinds={kinds}")
