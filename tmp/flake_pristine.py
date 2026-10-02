# coding=UTF-8
"""Run the pristine-worktree equivalent of the /api/forwards probe.

Usage: python tmp/flake_pristine.py <worktree-root> <iterations>
"""
import http.client
import importlib
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(sys.argv[1]).resolve()
iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 12
sys.path.insert(0, str(ROOT))

_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
mod = importlib.import_module("unit_tests.transfer_store_webui_case")
from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.persistence.transfer_store import TransferStore  # noqa: E402
sys.argv = _ORIGINAL_ARGV

fails = 0
for i in range(iterations):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        store = TransferStore(directory=directory)
        server = WebUiServer(
            store=store, operations=mod.FakeWebUiOperations(),
            username="admin", password="pass",
        )
        server.start(open_browser=False)
        try:
            conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
            conn.request(
                "POST", "/api/auth/login",
                body=json.dumps({"username": "admin", "password": "pass", "remember_me": True}),
                headers={"Content-Type": "application/json"},
            )
            login = conn.getresponse()
            login.read()
            cookie = login.getheader("Set-Cookie")
            conn.request(
                "POST", "/api/forwards",
                body=json.dumps({
                    "source_link": "https://t.me/source",
                    "target_link": "https://t.me/target",
                    "start_id": 1, "end_id": 3,
                }),
                headers={"Cookie": cookie.split(";", 1)[0], "Content-Type": "application/json"},
            )
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            status = resp.status
            conn.close()
            ok = status == 404 and '"not_found"' in body
            if not ok:
                fails += 1
            print(f"[{i}] {'OK ' if ok else 'FAIL'} login={login.status} forwards={status} {body[:100]!r}", flush=True)
        except Exception as exc:
            fails += 1
            print(f"[{i}] FAIL exception {type(exc).__name__}: {exc}", flush=True)
        finally:
            try:
                server.stop()
            except Exception:
                pass

print(f"\nRESULT root={ROOT.name} iterations={iterations} failures={fails}")
