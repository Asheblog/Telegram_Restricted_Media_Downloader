"""运行时取证：构造 TrmdCompositionRoot，观测 ctx.transfer_store 的值捕获后果。

用 .venv313 运行（.venv 3.14.0a5 import yaml 即崩）。
不修改仓库、不联网（仅构造对象）。
"""
from __future__ import annotations

import os
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

print("=" * 74)
print("运行时取证 1: 构造 TrmdCompositionRoot 并观测 transfer_store")
print("=" * 74)

from module.composition_root import TrmdCompositionRoot  # noqa: E402

root = TrmdCompositionRoot()

print(f"root.transfer_store                       = {root.transfer_store!r}")
print(f"root.ctx.transfer_store                   = {root.ctx.transfer_store!r}")
print(f"root.transfer_engine is root._te          = {root.transfer_engine is getattr(root, '_te', None)}")
print(f"root.transfer_engine.ctx is root.ctx      = {root.transfer_engine.ctx is root.ctx}")
print(f"root.transfer_engine.transfer_store       = {root.transfer_engine.transfer_store!r}")

# getter 式（安全）vs 值捕获（危险）对照
print()
print("getter 延迟取值对照:")
root.transfer_store = object()          # 模拟 start_web_ui 晚赋值
print(f"  赋值后 root.transfer_store              = {root.transfer_store!r}")
print(f"  赋值后 root._transfer_store() (getter)  = {root._transfer_store()!r}")
print(f"  赋值后 root.ctx.transfer_store (值捕获) = {root.ctx.transfer_store!r}  <- 仍是构造期捕获的 None")
print(f"  赋值后 root.transfer_engine.transfer_store = {root.transfer_engine.transfer_store!r}  <- 仍是 None")
root.transfer_store = None

print()
print("=" * 74)
print("运行时取证 2: 直接调用 engine 的无保护消费者（ctx.transfer_store is None）")
print("=" * 74)
eng = root.transfer_engine
for name, args in [
    ("skip_transfer_item_for_target_limit",
     ({'id': 1, 'target_link': 't'}, type('M', (), {'id': 9})(), 'link', 1, {'message': 'x'})),
    ("skip_transfer_item_for_media_type",
     ({'id': 1, 'target_link': 't'}, type('M', (), {'id': 9})(), 'link', 1, 'reason')),
    ("skip_missing_web_transfer_range_message",
     ({'id': 1, 'target_link': 't'}, 1, 'link', 9)),
]:
    fn = getattr(eng, name, None)
    if fn is None:
        print(f"  {name}: 不存在")
        continue
    try:
        fn(*args)
        print(f"  {name}: 未抛异常")
    except Exception as e:
        tb = traceback.extract_tb(sys.exc_info()[2])
        frame = [f for f in tb if "engine.py" in (f.filename or "")]
        loc = f"{os.path.basename(frame[-1].filename)}:{frame[-1].lineno}" if frame else "?"
        print(f"  {name}: {type(e).__name__}: {e}   @ {loc}")

print()
print("对照组（有保护的调用）:")
try:
    print("  refresh_transfer_task_counts(1) ->", eng.refresh_transfer_task_counts(1), "(guard L167 生效, 无异常)")
except Exception as e:
    print(f"  refresh_transfer_task_counts: {type(e).__name__}: {e}")

print()
print("=" * 74)
print("运行时取证 3: standalone fallback 引擎的 ctx 是否可被后续赋值修复")
print("=" * 74)
fake = object.__new__(TrmdCompositionRoot)   # 半构造 host（无 __init__ 产物）
fake.app = root.app
fake.diagnostic = getattr(root, "diagnostic", None)
fake.loop = root.loop
fake.gc = root.gc
fake.my_id = 1
fake.download_upload_window = root.download_upload_window
fake.local_storage_guard = root.local_storage_guard
fake.progress_tracker = root.progress_tracker
fake.pikpak_manager = root.pikpak_manager
fake.watch_manager = root.watch_manager
fake.web_task_manager = root.web_task_manager
fake.transfer_store = None
e2 = fake._create_standalone_transfer_engine()
print(f"  standalone engine.ctx is host.ctx      = {e2.ctx is getattr(fake, 'ctx', None)}  (host 无 ctx -> False)")
print(f"  standalone engine.transfer_store (now) = {e2.transfer_store!r}")
sentinel = object()
fake.transfer_store = sentinel
print(f"  host.transfer_store 被晚期赋值         = {fake.transfer_store!r}")
print(f"  standalone engine.transfer_store (after) = {e2.transfer_store!r}  <- 未同步（值捕获冻结）")
print(f"  修复点 operations.py:1122-1124 只写 host.__dict__['ctx']，触及不到 standalone ctx = {e2.ctx is not fake.__dict__.get('ctx')}")
