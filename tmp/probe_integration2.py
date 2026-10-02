# coding=UTF-8
"""Probe 2: end-to-end with the REAL facade — construct, start WebUI, submit task.

Read-only exploration; uses a sandbox config dir and a free port.
"""
import json
import os
import pathlib
import socket
import sys
import tempfile
import traceback

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

sandbox = tempfile.mkdtemp(prefix="trmd-int2-")
os.environ["XDG_CONFIG_HOME"] = sandbox
os.environ["APPDATA"] = sandbox
os.environ["TRMD_WEB_HOST"] = "127.0.0.1"

with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    free_port = s.getsockname()[1]
os.environ["TRMD_WEB_PORT"] = str(free_port)

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()

_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0], "--web", str(free_port)]
print(f"sandbox={sandbox} port={free_port}")

print("\n=== 1. import facade (PARSE_ARGS now sees --web) ===")
from module.downloader import TelegramRestrictedMediaDownloader  # noqa: E402
from module.utils.parser import PARSE_ARGS  # noqa: E402
print(f"   PARSE_ARGS.web = {PARSE_ARGS.web!r}")

sys.argv = _ORIGINAL_ARGV  # restore so pytest-ish tooling is unaffected

print("\n=== 2. real construction ===")
try:
    dl = TelegramRestrictedMediaDownloader()
    print("   constructed OK")
except Exception:
    traceback.print_exc()
    raise SystemExit(1)

print(f"   web_ui (before start) = {dl.web_ui!r}")
print(f"   transfer_store (before) = {dl.transfer_store!r}")

print("\n=== 3. real start_web_ui ===")
try:
    dl.start_web_ui(with_auth_provider=False, defer_runtime_recovery=False)
    print(f"   web_ui = {dl.web_ui!r}")
    print(f"   url    = {dl.web_ui.url!r}")
    print(f"   store  = {dl.transfer_store!r}")
except Exception:
    traceback.print_exc()
    raise SystemExit(1)

print("\n=== 4. HTTP: does the real server answer? ===")
import http.client  # noqa: E402

try:
    conn = http.client.HTTPConnection("127.0.0.1", dl.web_ui.port, timeout=5)
    conn.request("GET", "/api/auth/status")
    resp = conn.getresponse()
    body = resp.read().decode("utf-8")
    print(f"   GET /api/auth/status -> {resp.status} {body[:120]}")
    conn.close()
except Exception:
    traceback.print_exc()

print("\n=== 5. HTTP: submit a real transfer task ===")
task_id = None
try:
    conn = http.client.HTTPConnection("127.0.0.1", dl.web_ui.port, timeout=5)
    payload = {
        "source_link": "https://t.me/example_channel/1",
        "target_link": "https://t.me/pikpak_bot",
        "start_id": 1,
        "end_id": 2,
    }
    conn.request(
        "POST", "/api/tasks",
        body=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    body = resp.read().decode("utf-8")
    print(f"   POST /api/tasks -> {resp.status} {body[:300]}")
    conn.close()
    if resp.status in (200, 201):
        task_id = json.loads(body).get("id") or json.loads(body).get("task_id")
except Exception:
    traceback.print_exc()

print("\n=== 6. is it persisted to SQLite on disk? ===")
try:
    store = dl.transfer_store
    tasks = store.list_tasks()
    print(f"   list_tasks() -> {len(tasks)} row(s)")
    for t in tasks[-3:]:
        print(f"      id={t.get('id')} status={t.get('status')!r} src={str(t.get('source_link'))[:50]!r}")
    db_files = list(pathlib.Path(store.directory).glob("*.db")) + list(pathlib.Path(store.directory).glob("*.sqlite*"))
    print(f"   db files: {[p.name for p in db_files]}")
except Exception:
    traceback.print_exc()

print("\n=== 7. teardown ===")
for step, fn in (
    ("web_ui.stop()", lambda: dl.web_ui and dl.web_ui.stop()),
    ("transfer_store.close()", lambda: dl.transfer_store and dl.transfer_store.close()),
):
    try:
        fn()
        print(f"   {step} OK")
    except Exception as exc:
        print(f"   {step} failed: {type(exc).__name__}: {exc}")
print("   done")
