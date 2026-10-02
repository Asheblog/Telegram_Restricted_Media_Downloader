# coding=UTF-8
"""Probe: can TrmdCompositionRoot be constructed in-process for an integration test?

Read-only exploration. Uses a temp XDG_CONFIG_HOME/appdata so nothing lands in the
real user profile. Prints what construction does and what breaks.
"""
import os
import pathlib
import sys
import tempfile
import traceback

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

# Isolate config/log dirs BEFORE importing module.constants (it reads env at import).
sandbox = tempfile.mkdtemp(prefix="trmd-int-")
os.environ["XDG_CONFIG_HOME"] = sandbox
os.environ["APPDATA"] = sandbox

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]

print("=== 1. import composition root ===")
try:
    from module.composition_root import TrmdCompositionRoot
    print("   import OK")
except Exception:
    traceback.print_exc()
    raise SystemExit(1)

print("\n=== 2. construct (no --web arg) ===")
try:
    root = TrmdCompositionRoot()
    print(f"   constructed: {type(root).__name__}")
except Exception:
    print("   construction raised:")
    traceback.print_exc()
    raise SystemExit(1)

print("\n=== 3. what got wired ===")
attrs = [
    "gc", "app", "bot", "diagnostic", "system_log", "watch_manager",
    "pikpak_manager", "progress_tracker", "callback_handler",
    "web_task_manager", "web_ui", "transfer_store", "ctx",
]
for name in attrs:
    value = getattr(root, name, "<absent>")
    print(f"   {name:20s} = {type(value).__name__ if value is not None else 'None'}")

print(f"\n   transfer_engine  = {type(root.transfer_engine).__name__}")
print(f"   te.ctx is root.ctx = {root.transfer_engine.ctx is root.ctx}")
print(f"   te.transfer_store  = {root.transfer_engine.transfer_store!r}")

print("\n=== 4. dirs created under sandbox ===")
for p in sorted(pathlib.Path(sandbox).rglob("*")):
    rel = p.relative_to(sandbox)
    print(f"   {'D' if p.is_dir() else 'F'} {rel}")

print("\n=== 5. threads ===")
import threading  # noqa: E402

for t in threading.enumerate():
    print(f"   {t.name} daemon={t.daemon}")

print("\n=== 6. live state probes ===")
from module.adapters.webui.operations import _ensure_transfer_store  # noqa: E402

# exercise the real lazy store creation against the real host
try:
    op = root._web_ui_operations
    print(f"   _web_ui_operations = {type(op).__name__}")
except Exception as exc:
    print(f"   _web_ui_operations failed: {type(exc).__name__}: {exc}")

try:
    root.app.temp_directory = os.path.join(sandbox, "temp")
    store = root._ensure_transfer_store()
    print(f"   _ensure_transfer_store -> {type(store).__name__} at {store.directory!r}")
    print(f"   root.transfer_store is store   : {root.transfer_store is store}")
    print(f"   root.ctx.transfer_store is store: {root.ctx.transfer_store is store}")
    print(f"   engine.transfer_store is store : {root.transfer_engine.transfer_store is store}")
except Exception:
    print("   _ensure_transfer_store raised:")
    traceback.print_exc()

print("\n=== 7. can the store round-trip a task+item? ===")
try:
    store = root.transfer_store
    task_id = store.create_task("https://t.me/source", "https://t.me/pikpak_bot", start_id=1, end_id=2)
    print(f"   create_task -> {task_id}")
    item_id = store.add_item(
        task_id=task_id, source_chat_id=-100123, source_message_id=1,
        source_link="https://t.me/source/1",
    )
    print(f"   add_item    -> {item_id}")
    task = store.get_task(task_id)
    print(f"   get_task    -> status={task.get('status')!r} total={task.get('total_items')!r}")
    item = store.get_item(item_id)
    print(f"   get_item    -> status={item.get('status')!r}")
except Exception:
    print("   store round-trip raised:")
    traceback.print_exc()

print("\n=== 8. WebUI server construction (no bind) ===")
env_host = os.environ.get("TRMD_WEB_HOST")
print(f"   TRMD_WEB_HOST={env_host!r} web_ui={root.web_ui!r}")
print(f"   PARSE_ARGS.web={getattr(sys.modules['module.utils.parser'].PARSE_ARGS, 'web', '<no attr>')!r}")

print("\n=== 9. teardown probe ===")
try:
    if root.transfer_store is not None:
        root.transfer_store.close()
        print("   transfer_store.close() OK")
except Exception as exc:
    print(f"   close failed: {type(exc).__name__}: {exc}")
print("   done")
