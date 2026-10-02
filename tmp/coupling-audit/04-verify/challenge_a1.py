"""对抗性抽查：独立复现 A1（01-host/evidence.md）的关键数字。只读。"""
from __future__ import annotations

import ast
import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MOD = os.path.join(ROOT, "module")


def parse(p):
    return ast.parse(open(p, "rb").read(), filename=p)


def src(p):
    return open(p, encoding="utf-8").read()


# ---------- H-01: LiveTransferService __getattr__ 代理
lt = os.path.join(MOD, "transfer", "live_transfer.py")
t = parse(lt)
cls = next(n for n in ast.walk(t) if isinstance(n, ast.ClassDef) and n.name == "LiveTransferService")
local = {m.name for m in cls.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
local |= {n.target.id for n in cls.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}
local |= {tg.id for n in cls.body if isinstance(n, ast.Assign) for tg in n.targets if isinstance(tg, ast.Name)}
has_getattr = any(m.name == "__getattr__" for m in cls.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)))
reads = {}
for n in ast.walk(cls):
    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self":
        reads.setdefault(n.attr, []).append(n.lineno)
proxied = {k: v for k, v in reads.items() if k not in local and not k.startswith("__")}
private = {k: v for k, v in proxied.items() if k.startswith("_")}
print("=== H-01 LiveTransferService ===")
print(f"  定义 __getattr__ : {has_getattr}  (A1 说用 __getattr__ 透明代理)")
print(f"  本地定义名字数   : {len(local)}")
print(f"  self.<attr> 不同名字总数: {len(reads)}")
print(f"  需代理的不同名字数 A1=33  我={len(proxied)}")
print(f"  代理读点总数       A1=125 我={sum(len(v) for v in proxied.values())}")
print(f"  其中宿主私有方法(下划线开头) A1=5 我={len(private)} -> {sorted(private)}")
print(f"  被代理名字 Top12: {sorted(((k, len(v)) for k, v in proxied.items()), key=lambda x: -x[1])[:12]}")

# ---------- H-05: composition_root.py *args/**kwargs 透传 shim
cr = os.path.join(MOD, "composition_root.py")
t2 = parse(cr)
shims = []
for n in ast.walk(t2):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if n.args.vararg or n.args.kwarg:
            shims.append((n.lineno, n.name, bool(n.args.vararg), bool(n.args.kwarg)))
print("\n=== H-05 composition_root.py *args/**kwargs shim ===")
print(f"  含 *args 或 **kwargs 的函数 A1=17  我={len(shims)}")
for s in shims:
    print(f"    L{s[0]} {s[1]}  vararg={s[2]} kwarg={s[3]}")

# 这些 shim 是否只做透传（return self.<something>(*args, **kwargs)）
pure = 0
for n in ast.walk(t2):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and (n.args.vararg or n.args.kwarg):
        body = [b for b in n.body if not (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant))]
        if len(body) == 1 and isinstance(body[0], ast.Return):
            r = body[0].value
            if isinstance(r, ast.Call) and r.args and isinstance(r.args[0], ast.Starred) and r.keywords and any(k.arg is None for k in r.keywords):
                pure += 1
print(f"  其中纯透传形态 return f(*args, **kwargs): {pure}")

# ---------- H-08: self.__dict__.get 处数
cnt = []
for p in glob.glob(os.path.join(MOD, "**", "*.py"), recursive=True):
    for i, line in enumerate(src(p).splitlines(), 1):
        if "self.__dict__.get" in line:
            cnt.append((os.path.relpath(p, ROOT), i, line.strip()))
print("\n=== H-08 self.__dict__.get 处数 ===")
print(f"  A1=12  我={len(cnt)}")
for c in cnt:
    print(f"    {c[0]}:{c[1]}  {c[2][:80]}")

# ---------- H-09: 测试里的 __new__ 骨架
tests = glob.glob(os.path.join(ROOT, "unit_tests", "*_case.py"))
skeleton = []
for p in tests:
    s = src(p)
    for m in re.finditer(r"(\w+)\.__new__\(\s*(\w+)\s*\)", s):
        skeleton.append((os.path.basename(p), m.group(1)))
print("\n=== H-09 __new__ 骨架 ===")
print(f"  __new__(...) 调用次数 A1=92  我={len(skeleton)}")
from collections import Counter
print("  按被构造类:", Counter(c for _, c in skeleton).most_common(8))

# ---------- H-10: WebTransferHost 静态声明
wh = os.path.join(MOD, "transfer", "ports.py")
cands = [p for p in glob.glob(os.path.join(MOD, "**", "*.py"), recursive=True) if "WebTransferHost" in src(p)]
print("\n=== H-10 WebTransferHost ===")
for p in cands:
    s = src(p)
    print(f"  {os.path.relpath(p, ROOT)}: 提及 {s.count('WebTransferHost')} 次")
    for i, line in enumerate(s.splitlines(), 1):
        if "WebTransferHost" in line and ("class " in line or "getattr" in line or "hasattr" in line or "isinstance" in line):
            print(f"     L{i}: {line.strip()[:100]}")
# isinstance/hasattr 针对 WebTransferHost 的运行期检查
rt = 0
for p in glob.glob(os.path.join(MOD, "**", "*.py"), recursive=True):
    s = src(p)
    for m in re.finditer(r"(isinstance|hasattr|issubclass)\([^)]*WebTransferHost", s):
        rt += 1
print(f"  针对 WebTransferHost 的 isinstance/hasattr/issubclass 运行期检查: {rt}")
