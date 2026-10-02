"""运行时取证 v2：只调用真实方法，不跑 initialize()（避免写盘副作用）。

用 .venv313 运行。
"""
from __future__ import annotations

import os
import sys
import tempfile
from types import SimpleNamespace

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]
os.chdir(ROOT)

from module.downloader import TelegramRestrictedMediaDownloader as Host  # noqa: E402
from module.transfer.context import TransferContext  # noqa: E402
from module.transfer.engine import TransferEngine  # noqa: E402


def bare():
    return Host.__new__(Host)


def line(*a):
    print(*a)


line("=" * 74)
line("取证 A: CLI 模式（PARSE_ARGS.web is None）—— start_web_ui() 提前返回")
line("=" * 74)
from module.utils.parser import PARSE_ARGS  # noqa: E402

line(f"  PARSE_ARGS.web = {PARSE_ARGS.web!r}")
h = bare()
h.transfer_store = None          # 等价 composition_root.py:81
h.start_web_ui()                 # 真实方法; operations.py:1113-1115
line(f"  调用 host.start_web_ui() 后 host.transfer_store = {h.transfer_store!r}")
line("  -> CLI 模式下 start_web_ui() 是空操作，transfer_store 不会被赋值")

line()
line("=" * 74)
line("取证 B: __init__ 的值捕获 —— TransferContext(transfer_store=self.transfer_store)")
line("=" * 74)
h2 = bare()
h2.transfer_store = None                                   # composition_root.py:81
ctx = TransferContext(app=None, gc=None, diagnostic=None, loop=None, my_id=0,
                      download_upload_window=None, local_storage_guard=None,
                      transfer_store=h2.transfer_store,           # <-- composition_root.py:193 值捕获
                      progress_tracker=None, pikpak_manager=None,
                      watch_manager=None, web_task_manager=None)
h2.ctx = ctx
h2._te = TransferEngine(ctx=ctx)
line(f"  构造后 ctx.transfer_store            = {h2.ctx.transfer_store!r}")
line(f"  构造后 host._te.transfer_store       = {h2._te.transfer_store!r}")

# 真实 lazy 修复路径
tmp = tempfile.mkdtemp(prefix="a4probe-")
h2.app = SimpleNamespace(temp_directory=tmp)
store = h2._ensure_transfer_store()                        # operations.py:108
line(f"  _ensure_transfer_store() 返回        = {type(store).__name__}")
line(f"  修复后 host.transfer_store           = {type(h2.transfer_store).__name__}")
line(f"  修复后 ctx.transfer_store (同步过)   = {type(h2.ctx.transfer_store).__name__}")
line(f"  修复后 _te.transfer_store            = {type(h2._te.transfer_store).__name__}")
line("  -> 因为 _te.ctx is host.ctx（共享同一 ctx 对象），operations.py:120 的同步能修好引擎")

line()
line("=" * 74)
line("取证 C: 无 protect 的 engine 消费者在 ctx.transfer_store is None 时的行为")
line("=" * 74)
h3 = bare()
h3.transfer_store = None
ctx3 = TransferContext(transfer_store=None)
h3.ctx = ctx3
h3._te = TransferEngine(ctx=ctx3, ports=None)
import traceback  # noqa: E402

msg = SimpleNamespace(id=9)
for name, args in [
    ("skip_transfer_item_for_target_limit",
     ({'id': 1, 'target_link': 't'}, msg, 'link', 1, {'message': 'x'})),
    ("skip_transfer_item_for_media_type",
     ({'id': 1, 'target_link': 't'}, msg, 'link', 1, 'reason')),
    ("skip_missing_web_transfer_range_message",
     ({'id': 1, 'target_link': 't'}, 1, 'link', 9)),
    ("refresh_transfer_task_counts", (1,)),
]:
    fn = getattr(h3.transfer_engine, name, None)
    if fn is None:
        line(f"  {name}: <不存在>")
        continue
    try:
        r = fn(*args)
        line(f"  {name}: 正常返回 {r!r}")
    except Exception as e:
        tb = [f for f in traceback.extract_tb(sys.exc_info()[2]) if f.filename.endswith("engine.py")]
        loc = f"engine.py:{tb[-1].lineno}" if tb else "?"
        line(f"  {name}: {type(e).__name__}: {e}   @ {loc}")

line()
line("=" * 74)
line("取证 D: standalone fallback 引擎的 ctx 无法被后续赋值修复")
line("=" * 74)
h4 = bare()
h4.transfer_store = None
h4.app = SimpleNamespace(temp_directory=tmp)
h4.diagnostic = None
try:
    eng4 = h4._create_standalone_transfer_engine()          # composition_root.py:492
    line(f"  standalone engine.ctx is h4.__dict__.get('ctx') = {eng4.ctx is h4.__dict__.get('ctx')}")
    line(f"  standalone engine.transfer_store (构造当时)      = {eng4.transfer_store!r}")
    h4.__dict__['ctx'] = TransferContext(transfer_store=None)
    store4 = h4._ensure_transfer_store()                    # 真实修复路径
    line(f"  修复后 h4.transfer_store                          = {type(h4.transfer_store).__name__}")
    line(f"  修复后 h4.__dict__['ctx'].transfer_store          = {h4.__dict__['ctx'].transfer_store!r}")
    line(f"  修复后 standalone engine.transfer_store          = {eng4.transfer_store!r}  <- 仍旧 None")
except Exception as e:
    line(f"  <构造 standalone engine 失败> {type(e).__name__}: {e}")

line()
line("=" * 74)
line("取证 E: transfer_store 的写入点全集（AST 确认）")
line("=" * 74)
import ast  # noqa: E402

hits = []
for dp, dn, fn in os.walk(os.path.join(ROOT, "module")):
    dn[:] = [d for d in dn if d not in {"__pycache__", ".ruff_cache"}]
    for f in fn:
        if not f.endswith(".py"):
            continue
        p = os.path.join(dp, f)
        t = ast.parse(open(p, "rb").read(), filename=p)
        for n in ast.walk(t):
            tgts = []
            if isinstance(n, ast.Assign):
                tgts = n.targets
            elif isinstance(n, ast.AnnAssign):
                tgts = [n.target]
            for tg in tgts:
                if isinstance(tg, ast.Attribute) and tg.attr == "transfer_store":
                    hits.append((os.path.relpath(p, ROOT), n.lineno, ast.unparse(tg)))
for p, ln, tg in sorted(hits):
    line(f"  {p}:{ln}  {tg} = ...")
line(f"  合计写入点: {len(hits)}")
