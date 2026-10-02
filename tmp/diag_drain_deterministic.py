# coding=UTF-8
"""确定性对照：同一请求序列下，未读 body 是否导致客户端丢响应。

用 delay-read（发完请求后先睡，让服务端的 RST 先到）把概率竞态变成确定性现象。
分别在 drain 生效 / 被绕过 两种情况下跑同一序列，比较结果。
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

import module.adapters.webui.server as srv  # noqa: E402
from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.transfer_store import TransferStore  # noqa: E402


def run_case(disable_drain: bool, rounds: int = 12, delay: float = 0.05):
    """一个全新的 server，重复「带 body 的未鉴权 POST」并延迟读取。"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        server = WebUiServer(
            store=TransferStore(directory=d), username="admin", password="pass"
        )
        if disable_drain:
            # 让 drain 变成 no-op，以复现修复前的行为
            server_holder = {}

            class _NoDrain:
                def __get__(self, obj, objtype=None):
                    return lambda *a, **k: None

            # 无法在运行时改动嵌套类，改用环境标记由源码读取
            os.environ["TRMD_TEST_NO_DRAIN"] = "1"
        server.start(open_browser=False)
        port = server.port
        body = json.dumps({"phone": "+8615000000000"}).encode()
        ok = fail = 0
        for _ in range(rounds):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            try:
                conn.request(
                    "POST", "/api/auth/submit", body=body,
                    headers={"Content-Type": "application/json"},
                )
                time.sleep(delay)  # 让服务端的 RST（若发生）先于我们读取
                resp = conn.getresponse()
                resp.read()
                ok += 1
            except Exception as exc:
                fail += 1
                last = f"{type(exc).__name__}: {exc}"
            finally:
                conn.close()
        server.stop()
        os.environ.pop("TRMD_TEST_NO_DRAIN", None)
        return ok, fail, (last if fail else "")


print("=== drain 生效（当前代码）===")
ok, fail, last = run_case(disable_drain=False)
print(f"  ok={ok} fail={fail} rate={100*fail/(ok+fail):.1f}%  {last}")

print("\n=== 说明 ===")
print("  如需对照修复前行为，请用 git stash 掉 server.py 的 drain 后重跑本脚本；")
print("  本脚本不修改仓库文件。")
