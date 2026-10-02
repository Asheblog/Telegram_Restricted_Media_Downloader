"""对抗性抽查：独立复现 A2（02-adapters/evidence.md）的关键数字。只读。"""
from __future__ import annotations

import ast
import os
import re
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def parse(rel):
    p = os.path.join(ROOT, rel)
    return ast.parse(open(p, "rb").read(), filename=p), open(p, encoding="utf-8").read()


def methods_of(cls_node):
    return [n for n in cls_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


ops_t, ops_s = parse("module/adapters/webui/operations.py")
srv_t, srv_s = parse("module/adapters/webui/server.py")

ops_cls = next(n for n in ast.walk(ops_t) if isinstance(n, ast.ClassDef) and n.name == "WebOperationsMixin")
srv_cls = next(n for n in ast.walk(srv_t) if isinstance(n, ast.ClassDef) and n.name == "WebUiServer")
fac_cls = [n for n in ast.walk(ops_t) if isinstance(n, ast.ClassDef) and n.name == "WebOperationsFacade"]

ops_m = {m.name for m in methods_of(ops_cls)}
srv_m = [m for m in methods_of(srv_cls)]
srv_names = {m.name for m in srv_m}

print("=== A2 声明值 vs 我的复现值 ===")
print(f"WebOperationsMixin 方法数      A2=114  我={len(ops_m)}  {'一致' if len(ops_m)==114 else '不一致'}")

print(f"WebUiServer 方法数             A2=67   我={len(srv_m)}  {'一致' if len(srv_m)==67 else '不一致'}")

coll = sorted(ops_m & srv_names)
print(f"同名方法数                     A2=32   我={len(coll)}  {'一致' if len(coll)==32 else '不一致'}")

start = [m for m in srv_m if m.name == "start"]
if start:
    s = start[0]
    span = (s.end_lineno or s.lineno) - s.lineno + 1
    print(f"WebUiServer.start 行跨度       A2=463 (L440-902)  我={span} (L{s.lineno}-{s.end_lineno})  "
          f"{'一致' if span == 463 else '不一致'}")
    # 去重后的行数（含空行/注释）
    body_lines = srv_s.splitlines()[s.lineno - 1:s.end_lineno]
    nonblank = [l for l in body_lines if l.strip()]
    print(f"   其中非空行={len(nonblank)}  空行={len(body_lines)-len(nonblank)}")

# facade 代理表
m = re.search(r"_WEB_UI_DELEGATE_METHODS\s*=\s*[\(\[]([^\)\]]*)[\)\]]", ops_s, re.S)
if m:
    items = [x for x in re.findall(r"['\"]([\w_]+)['\"]", m.group(1))]
    print(f"facade 代理方法数              A2=40   我={len(items)} (去重 {len(set(items))})")
else:
    print("未找到 _WEB_UI_DELEGATE_METHODS 字面量（可能动态生成）")
if fac_cls:
    print(f"WebOperationsFacade 直接方法数 我={len(methods_of(fac_cls[0]))}  (A2 说 40 由 setattr 动态绑定)")

# ports.py
ports_t, ports_s = parse("module/ports.py")
protos = [n for n in ast.walk(ports_t) if isinstance(n, ast.ClassDef) and any(
    (isinstance(b, ast.Name) and b.id == "Protocol") or (isinstance(b, ast.Attribute) and b.attr == "Protocol")
    for b in n.bases)]
print(f"ports.py 行数                  A2=121  我={len(ports_s.splitlines())}")
print(f"ports.py Protocol 类数         A2=7    我={len(protos)}  -> {[p.name for p in protos]}")

# 全仓 isinstance/issubclass/cast 针对 Protocol
allpy = []
for dp, dn, fn in os.walk(os.path.join(ROOT, "module")):
    dn[:] = [d for d in dn if d not in {"__pycache__", ".ruff_cache"}]
    allpy += [os.path.join(dp, f) for f in fn if f.endswith(".py")]
proto_names = {p.name for p in protos}
hits = Counter()
for p in allpy:
    src = open(p, encoding="utf-8").read()
    t = ast.parse(src, filename=p)
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"isinstance", "issubclass", "cast"}:
            for a in n.args:
                if isinstance(a, ast.Name) and a.id in proto_names:
                    hits[f"{ast.unparse(n.func)}({a.id})"] += 1
                elif isinstance(a, ast.Tuple):
                    for e in a.elts:
                        if isinstance(e, ast.Name) and e.id in proto_names:
                            hits[f"{ast.unparse(n.func)}({e.id})"] += 1
print(f"针对 Protocol 的 isinstance/issubclass/cast  A2=0  我={sum(hits.values())}  {dict(hits)}")

# IWebUiOperations 注解使用处
uses = []
for p in allpy:
    src = open(p, encoding="utf-8").read()
    for i, line in enumerate(src.splitlines(), 1):
        if "IWebUiOperations" in line and "class " not in line:
            uses.append((os.path.relpath(p, ROOT), i, line.strip()))
print(f"IWebUiOperations 注解使用处     A2=1 (server.py:198)  我={len(uses)}")
for u in uses:
    print("   ", u)

# 从未被 import 的 Protocol
imported = set()
for p in allpy:
    t = ast.parse(open(p, "rb").read(), filename=p)
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                imported.add(a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                imported.add(a.name.split(".")[-1])
never = sorted(proto_names - imported)
print(f"从未被 import 的 Protocol      A2=5   我={len(never)} -> {never}")

# 继承闭包成员数
def members(cls):
    out = set()
    for b in cls.body:
        if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(b.name)
    return out


by_name = {p.name: p for p in protos}
def closure(name, seen=None):
    seen = seen or set()
    out = set()
    cls = by_name.get(name)
    if cls is None:
        return out
    out |= members(cls)
    for b in cls.bases:
        bn = ast.unparse(b)
        if bn in by_name and bn not in seen:
            seen.add(bn)
            out |= closure(bn, seen)
    return out


if "IWebUiOperations" in by_name:
    print(f"IWebUiOperations 继承闭包成员数 A2=19   我={len(closure('IWebUiOperations'))}")

print()
print("=== 同名方法清单核对 ===")
a2 = """cancel_deferred_discussion_capture cleanup_media_files create_channel_download create_upload
create_watch delete_watch detect_transfer_range execute_archive_author_reorganize
export_diagnostic_bundle export_forward_watches export_system_logs export_table
get_active_archive_author_job get_archive_author_job is_setup_ready
list_archive_author_channels list_archive_author_plan_moves list_cleanup_logs
list_deferred_discussion_captures list_operations list_system_logs list_watch_events
list_watches resolve_archive_author_reorganize retry_archive_from_system_log
retry_deferred_discussion_capture run_deferred_discussion_capture_now
scan_archive_author_reorganize scan_media_for_cleanup statistics
stop_archive_author_job update_watch""".split()
print("A2 列表条数:", len(a2), " 去重:", len(set(a2)))
print("我算出但 A2 未列:", sorted(set(coll) - set(a2)))
print("A2 列出但我未算出:", sorted(set(a2) - set(coll)))

# 31 个转发 / 1 个真实实现
delegate, real = [], []
for mm in srv_m:
    if mm.name not in ops_m:
        continue
    src = ast.get_source_segment(srv_s, mm) or ""
    if "_operation(" in src or "self.operations" in src:
        delegate.append(mm.name)
    else:
        real.append(mm.name)
print(f"server 中同名方法的转发数         A2=31   我={len(delegate)}")
print(f"server 中同名方法的真实实现数     A2=1    我={len(real)} -> {real}")
