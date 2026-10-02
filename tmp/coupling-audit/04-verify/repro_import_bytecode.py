"""A4 第三种独立方法：从 CPython 字节码 (IMPORT_NAME/IMPORT_FROM) 重建 import 图。
不使用 ast 模块，避免任何 AST 解析口径偏差。只编译不执行。
"""
from __future__ import annotations

import dis
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


def longest(t):
    if not t:
        return None
    best = None
    for c in names:
        if t == c or t.startswith(c + "."):
            if best is None or len(c) > len(best):
                best = c
    return best


def walk_code(co, out):
    yield co
    for c in co.co_consts:
        if hasattr(c, "co_code"):
            yield from walk_code(c, out)


edges = defaultdict(set)
ev = defaultdict(list)
for m, f in mods.items():
    src = open(f, "rb").read()
    co = compile(src, f, "exec")
    for c in walk_code(co, None):
        instrs = list(dis.get_instructions(c))
        for i, ins in enumerate(instrs):
            if ins.opname != "IMPORT_NAME":
                continue
            base = ins.argval
            # 紧随其后的 IMPORT_FROM 序列 = 从该模块导入的名字
            subs = []
            for j in range(i + 1, min(i + 40, len(instrs))):
                if instrs[j].opname == "IMPORT_FROM":
                    subs.append(instrs[j].argval)
                elif instrs[j].opname in ("IMPORT_NAME", "POP_TOP") and subs:
                    break
            t0 = longest(base)
            if t0 and t0 != m:
                edges[m].add(t0)
                ev[m].append((ins.offset, f"IMPORT_NAME {base}", t0))
            for s in subs:
                ts = longest(base + "." + s)
                if ts and ts != m and ts != t0:
                    edges[m].add(ts)
                    ev[m].append((ins.offset, f"IMPORT_NAME {base} + IMPORT_FROM {s}", ts))

# SCC (iterative Kosaraju —— 第三种算法)
g = {m: set(v) for m, v in edges.items()}
for m in mods:
    g.setdefault(m, set())
rg = defaultdict(set)
for u, vs in g.items():
    for v in vs:
        rg[v].add(u)

seen = set()
order = []
for s in sorted(g):
    if s in seen:
        continue
    st = [(s, iter(sorted(g[s])))]
    seen.add(s)
    while st:
        n, it = st[-1]
        adv = False
        for w in it:
            if w not in seen:
                seen.add(w)
                st.append((w, iter(sorted(g[w]))))
                adv = True
                break
        if not adv:
            order.append(n)
            st.pop()

comp = {}
sccs = []
for s in reversed(order):
    if s in comp:
        continue
    c = []
    st = [s]
    comp[s] = len(sccs)
    while st:
        n = st.pop()
        c.append(n)
        for w in rg[n]:
            if w not in comp:
                comp[w] = len(sccs)
                st.append(w)
    sccs.append(c)

cyc = [c for c in sccs if len(c) > 1]
print("[bytecode] 模块数:", len(mods), "边数:", sum(len(v) for v in edges.values()))
print("[bytecode] 非平凡 SCC:", len(cyc))
for c in cyc:
    print("   循环:", sorted(c))
print("[bytecode] 结论:", "无环" if not cyc else "有环")

# 层级别
lay = defaultdict(set)
layer_of = lambda m: m.split(".")[1] if len(m.split(".")) > 1 else m
for m, vs in edges.items():
    for v in vs:
        if layer_of(m) != layer_of(v):
            lay[layer_of(m)].add(layer_of(v))
print()
print("[bytecode] 层间邻接:")
for k in sorted(lay):
    print(f"   {k} -> {sorted(lay[k])}")
# 层级别环
seenl, orderl = set(), []
gl = {k: set(v) for k, v in lay.items()}
for k in sorted(gl):
    gl.setdefault(k, set())
for s in sorted(set(gl) | {v for vs in gl.values() for v in vs}):
    gl.setdefault(s, set())
    if s in seenl:
        continue
    seenl.add(s)
    st = [s]
    while st:
        n = st.pop()
        orderl.append(n)
        for w in gl[n]:
            if w not in seenl:
                seenl.add(w)
                st.append(w)
# 用 DFS 找层环
color = {}
cyc_l = []
stack = []


def dfs(u):
    color[u] = 1
    stack.append(u)
    for v in sorted(gl[u]):
        if color.get(v) == 1:
            cyc_l.append(stack[stack.index(v):] + [v])
        elif color.get(v, 0) == 0:
            dfs(v)
    stack.pop()
    color[u] = 2


for s in sorted(gl):
    if color.get(s, 0) == 0:
        dfs(s)
print("[bytecode] 层级别环:", cyc_l if cyc_l else "无")
print()
print("[bytecode] module.downloader 出边:", len(edges["module.downloader"]))
print("[bytecode] module.composition_root 出边:", len(edges["module.composition_root"]))
print("[bytecode] handlers 出边证据:")
for off, txt, t in ev["module.adapters.webui.handlers"]:
    print(f"   __init__.py @bytecode+{off}  {txt} -> {t}")
print("[bytecode] handlers.tasks 出边:", sorted(edges["module.adapters.webui.handlers.tasks"]))
print("[bytecode] core.filter 出边:", sorted(edges["module.core.filter"]))
print("[bytecode] core.media_types 出边:", sorted(edges["module.core.media_types"]))
print("[bytecode] module.app 出边:", sorted(edges["module.app"]))
print("[bytecode] core.app 出边:", sorted(edges["module.core.app"]))
