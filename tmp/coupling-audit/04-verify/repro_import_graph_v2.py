"""A4：import 图 v2 —— 正确处理 `from . import a, b` / `from pkg import submod` 子模块边。

v1 的两个实现都有缺陷：
  - AST 版: `from . import a,b` 解析为指向自身包，被 `if best != m` 丢弃 → 丢边
  - 正则版: 同一条被记为自环 → 假环
本脚本对每条 import 枚举被导入的**名字**，若名字对应真实子模块则建边。
"""
from __future__ import annotations

import ast
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODULE = os.path.join(ROOT, "module")


def modname(pth):
    r = os.path.relpath(pth, ROOT).replace("\\", "/")[:-3]
    if r.endswith("/__init__"):
        r = r[: -len("/__init__")]
    return r.replace("/", ".")


files = []
for dp, dn, fn in os.walk(MODULE):
    dn[:] = [d for d in dn if d not in {"__pycache__", ".ruff_cache"}]
    for f in fn:
        if f.endswith(".py"):
            files.append(os.path.join(dp, f))
mods = {modname(f): f for f in files}
names = set(mods)


def longest(target):
    best = None
    if not target:
        return None
    for c in names:
        if target == c or target.startswith(c + "."):
            if best is None or len(c) > len(best):
                best = c
    return best


def owner_pkg(owner, is_pkg):
    parts = owner.split(".")
    return parts if is_pkg else parts[:-1]


edges = defaultdict(set)
evidence = defaultdict(list)
unresolved = []
star = []
total_names = 0

for m, f in mods.items():
    tree = ast.parse(open(f, "rb").read(), filename=f)
    is_pkg = os.path.basename(f) == "__init__.py"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                total_names += 1
                t = longest(a.name)
                if t:
                    if t != m:
                        edges[m].add(t)
                    evidence[m].append((node.lineno, f"import {a.name}", t))
                elif a.name.startswith("module"):
                    unresolved.append((m, node.lineno, a.name))
        elif isinstance(node, ast.ImportFrom):
            base_parts = owner_pkg(m, is_pkg)
            lvl = node.level
            if lvl > 0:
                up = lvl - 1
                if up > 0:
                    base_parts = base_parts[:-up] if up <= len(base_parts) else []
                base = ".".join(base_parts)
                if node.module:
                    base = (base + "." + node.module) if base else node.module
            else:
                base = node.module or ""
            if not base:
                continue
            # (a) 包/模块本身
            t0 = longest(base)
            if t0 and t0 != m:
                edges[m].add(t0)
                evidence[m].append((node.lineno, f"from {base} import ...", t0))
            for alias in node.names:
                total_names += 1
                if alias.name == "*":
                    star.append((m, node.lineno, base))
                    continue
                sub = base + "." + alias.name
                ts = longest(sub)
                if ts and ts != m and ts != t0:
                    edges[m].add(ts)
                    evidence[m].append((node.lineno, f"from {base} import {alias.name}", ts))
                elif ts is None and alias.name[0].isupper() is False and base.startswith("module"):
                    pass

# 自环（真正 import 自身模块名）
selfloops = {m: vs for m, vs in edges.items() if m in vs}

# Tarjan
sys.setrecursionlimit(200000)
idx, low, on, stk, sccs = {}, {}, {}, [], []
cnt = [0]


def strong(v):
    idx[v] = low[v] = cnt[0]
    cnt[0] += 1
    stk.append(v)
    on[v] = True
    for w in edges.get(v, ()):
        if w not in idx:
            strong(w)
            low[v] = min(low[v], low[w])
        elif on.get(w):
            low[v] = min(low[v], idx[w])
    if low[v] == idx[v]:
        c = []
        while True:
            w = stk.pop()
            on[w] = False
            c.append(w)
            if w == v:
                break
        sccs.append(c)


for n in sorted(mods):
    if n not in idx:
        strong(n)

cycles = [c for c in sccs if len(c) > 1]
print("=" * 70)
print("[v2] 模块数:", len(mods), " 边数:", sum(len(v) for v in edges.values()),
      " import 名总数:", total_names)
print("[v2] 自环:", list(selfloops))
print("[v2] 非平凡 SCC:", len(cycles))
for c in cycles:
    print("   循环:", sorted(c))
    for m in sorted(c):
        for ln, txt, t in evidence[m]:
            if t in c:
                print(f"     {m}:{ln}  {txt}  -> {t}")
print("[v2] 结论: import 图", "无环 ✔" if not cycles and not selfloops else "有环 ✘")
print("[v2] SCC 规模分布:", dict(Counter(len(c) for c in sccs)))
print("[v2] 未解析的内部 import:", unresolved[:20], "计", len(unresolved))
print("[v2] 星号导入:", star)

print()
print("[v2] 出边 Top15:")
for m, v in sorted(edges.items(), key=lambda kv: -len(kv[1]))[:15]:
    print(f"   {m}: {len(v)}")

indeg = defaultdict(int)
for m, vs in edges.items():
    for v in vs:
        indeg[v] += 1
print()
print("[v2] 入度 Top10:")
for m, c in sorted(indeg.items(), key=lambda kv: -kv[1])[:10]:
    print(f"   {m}: {c}")

print()
print("[v2] 跨层边(层->层) Top12:")
lay = Counter()
for m, vs in edges.items():
    a = m.split(".")[1] if len(m.split(".")) > 1 else m
    for v in vs:
        b = v.split(".")[1] if len(v.split(".")) > 1 else v
        lay[(a, b)] += 1
for k, c in lay.most_common(12):
    print(f"   {k[0]} -> {k[1]}: {c}")
print("   反向边(下层->上层)明细:")
for k, c in sorted(lay.items()):
    if k[1] == "module" or (k[0], k[1]) in {("core", "adapters"), ("core", "transfer"), ("core", "persistence"), ("domain", "adapters"), ("domain", "transfer"), ("domain", "persistence"), ("utils", "adapters"), ("utils", "transfer")}:
        print(f"     {k[0]} -> {k[1]}: {c}")

print()
print("[v2] handlers 包出边证据:")
for ln, txt, t in evidence["module.adapters.webui.handlers"]:
    print(f"   handlers/__init__.py:{ln}  {txt} -> {t}")

print()
print("[v2] module.downloader 出边数:", len(edges["module.downloader"]))
print("[v2] module.composition_root 出边数:", len(edges["module.composition_root"]))
