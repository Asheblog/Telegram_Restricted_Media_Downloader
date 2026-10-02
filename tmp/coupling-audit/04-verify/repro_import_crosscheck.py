"""A4 交叉验证：用与 Tarjan 完全不同的方法（正则抽取 + DFS 递归栈）复核 import 图无环，
并统计动态 import 等静态分析盲区。"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODULE = os.path.join(ROOT, "module")

py_re = re.compile(r"^\s*(?:from\s+([.\w]+)\s+import|import\s+([\w.,\s]+))", re.M)

files = []
for dp, dn, fn in os.walk(MODULE):
    dn[:] = [d for d in dn if d not in {"__pycache__", ".ruff_cache"}]
    for f in fn:
        if f.endswith(".py"):
            files.append(os.path.join(dp, f))


def modname(pth):
    r = os.path.relpath(pth, ROOT).replace("\\", "/")[:-3]
    if r.endswith("/__init__"):
        r = r[: -len("/__init__")]
    return r.replace("/", ".")


mods = {modname(f): f for f in files}
names = set(mods)


def resolve(target: str, owner: str, owner_is_pkg: bool, level: int):
    """返回 module 内部模块名（最长前缀），否则 None。"""
    if level > 0:
        parts = owner.split(".")
        if not owner_is_pkg:
            parts = parts[:-1]
        up = level - 1
        if up > 0:
            parts = parts[:-up] if up <= len(parts) else []
        base = ".".join(parts)
        target = (base + "." + target) if (base and target) else (base or target)
    if not target:
        return None
    best = None
    for c in names:
        if target == c or target.startswith(c + "."):
            if best is None or len(c) > len(best):
                best = c
    return best


edges = defaultdict(set)
edge_evidence = defaultdict(list)
dyn = []

for m, f in mods.items():
    src = open(f, encoding="utf-8", errors="replace").read()
    is_pkg = os.path.basename(f) == "__init__.py"
    # 逐行解析（比正则块更准）：手工扫描 import 行
    for i, line in enumerate(src.splitlines(), 1):
        s = line.strip()
        if s.startswith("#"):
            continue
        mm = re.match(r"from\s+([.\w]+)\s+import\s+(.+)", s)
        if mm:
            raw = mm.group(1)
            level = len(raw) - len(raw.lstrip("."))
            name = raw.lstrip(".")
            tgt = resolve(name, m, is_pkg, level)
            if tgt and tgt != m:
                edges[m].add(tgt)
                edge_evidence[m].append((i, s))
            elif tgt == m:
                edges[m].add(tgt)
                edge_evidence[m].append((i, s + "   # self"))
        mm2 = re.match(r"import\s+(.+)", s)
        if mm2 and not s.startswith("from"):
            for part in mm2.group(1).split(","):
                nm = part.strip().split(" as ")[0].strip()
                tgt = resolve(nm, m, is_pkg, 0)
                if tgt:
                    edges[m].add(tgt)
                    edge_evidence[m].append((i, s))
        if "import_module" in s or "__import__" in s:
            dyn.append((m, i, s))

# DFS 递归栈找环（与 Tarjan 不同的算法）
WHITE, GRAY, BLACK = 0, 1, 2
color = defaultdict(int)
cycles = []
stack = []


def dfs(u):
    color[u] = GRAY
    stack.append(u)
    for v in sorted(edges.get(u, ())):
        if color[v] == GRAY:
            idx = stack.index(v)
            cycles.append(stack[idx:] + [v])
        elif color[v] == WHITE:
            dfs(v)
    stack.pop()
    color[u] = BLACK


sys.setrecursionlimit(100000)
for n in sorted(mods):
    if color[n] == WHITE:
        dfs(n)

print("[DFS 递归栈复核]")
print("  模块数:", len(mods))
print("  边数:", sum(len(v) for v in edges.values()))
print("  发现的环数:", len(cycles))
for c in cycles[:10]:
    print("   环:", " -> ".join(c))
print("  结论: import 图", "无环" if not cycles else "有环")

print()
print("[动态 import 盲区（静态图看不到的依赖）]")
for m, i, s in dyn:
    print(f"  {m}:{i}  {s.strip()[:110]}")
print("  计:", len(dyn))

print()
print("[自环]")
selfloops = [(m, [e for e in ev if '# self' in e[1]]) for m, ev in edge_evidence.items() if m in edges.get(m, set())]
print("  ", [(m, len(ev)) for m, ev in selfloops])

print()
print("[每模块出边数 Top12]")
for m, v in sorted(edges.items(), key=lambda kv: -len(kv[1]))[:12]:
    print(f"  {m}: {len(v)}")

print()
print("[被依赖最多 Top12 (入度)]")
indeg = defaultdict(int)
for m, vs in edges.items():
    for v in vs:
        indeg[v] += 1
for m, c in sorted(indeg.items(), key=lambda kv: -kv[1])[:12]:
    print(f"  {m}: {c}")

print()
print("[module/downloader.py 的内部 import 证据行]")
for i, s in edge_evidence["module.downloader"]:
    print(f"  downloader.py:{i}  {s}")
