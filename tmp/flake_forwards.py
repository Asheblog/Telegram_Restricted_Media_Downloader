# coding=UTF-8
"""Reproduce /api/forwards responses repeatedly to characterize the flake.

Starts a real WebUiServer with the same test fake and prints status/body for
N iterations. Read-only: no repository files are modified.
"""
import http.client
import json
import pathlib
import sys
import tempfile

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 5

import importlib  # noqa: E402

# 被导入的测试模块会调用 module 的 argparse，必须先清干净 argv 再导入。
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]
mod = importlib.import_module("unit_tests.transfer_store_webui_case")
sys.argv = _ORIGINAL_ARGV

from module.adapters.webui.server import WebUiServer  # noqa: E402
from module.persistence.transfer_store import TransferStore  # noqa: E402

Fake = mod.FakeWebUiOperations

for i in range(iterations):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        store = TransferStore(directory=directory)
        server = WebUiServer(
            store=store, operations=Fake(), username="admin", password="pass"
        )
        server.start(open_browser=False)
        try:
            conn = http.client.HTTPConnection(server.host, server.port, timeout=5)
            # login
            conn.request(
                "POST", "/api/auth/login",
                body=json.dumps({"username": "admin", "password": "pass", "remember_me": True}),
                headers={"Content-Type": "application/json"},
            )
            login = conn.getresponse()
            login_body = login.read().decode("utf-8")
            cookie = login.getheader("Set-Cookie")
            # target request
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
            tag = "OK " if resp.status == 404 else "FAIL"
            print(f"[{i}] {tag} login={login.status} forwards={resp.status} body={body[:160]!r} login_body={login_body[:120]!r}")
            conn.close()
        finally:
            server.stop()
