"""用 architecture_guard_case.py 自己的函数证明它的盲区。

不修改被测文件；只 import 其纯 AST 辅助函数并对比"守卫图"与"正确图"。
"""
from __future__ import annotations

import ast
import os
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from unit_tests import architecture_guard_case as ag  # noqa: E402

modules = ag._modules()
print(f"守卫 _modules() 模块数: {len(modules)}")

g = ag._import_graph(modules)
print(f"守卫图边数: {sum(len(v) for v in g.values())}")


def tarjan(graph):
    num, low, stk, on, out = {}, {}, [], set(), []
    t = [0]

    def strong(v):
        t[0] += 1
        num[v] = low[v] = t[0]
        stk.append(v)
        on.add(v)
        for w in graph.get(v, ()):
            if w not in num:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], num[w])
        if low[v] == num[v]:
            c = []
            while True:
                x = stk.pop()
                on.discard(x)
                c.append(x)
                if x == v:
                    break
            if len(c) > 1:
                out.append(c)

    sys.setrecursionlimit(100000)
    for n in sorted(graph):
        if n not in num:
            strong(n)
    return out


cyc_guard = tarjan(g)
print(f"守卫图非平凡 SCC 数: {len(cyc_guard)} -> {cyc_guard}")
print("守卫 test_module_import_graph_has_no_cycles 结果:",
      "PASS（因为它的图里确实没有环）")

# ---- 正确图：枚举 from-import 的被导入名字
names = set(modules)


def longest(t):
    if not t:
        return None
    best = None
    for c in names:
        if t == c or t.startswith(c + "."):
            if best is None or len(c) > len(best):
                best = c
    return best


correct = {m: set() for m in modules}
missed = []
for name, path in modules.items():
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for it in node.names:
                t = longest(it.name)
                if t and t != name:
                    correct[name].add(t)
        elif isinstance(node, ast.ImportFrom):
            # 用守卫自己的 _resolve 解析基名，保证对比公平
            alias = (("." * node.level) + (node.module or "")) if node.level else (node.module or "")
            base = ag._resolve(alias, name) if alias else None
            if base and base != name:
                # 守卫只加 base；正确做法还要加 base.<imported>
                if base not in modules and base not in correct[name]:
                    pass
                if base in modules:
                    pass
                else:
                    correct[name].add(base)
            for it in node.names:
                if it.name == "*":
                    continue
                sub = f"{base}.{it.name}" if base else None
                if sub and sub in modules and sub != name:
                    correct[name].add(sub)
                    if sub not in g.get(name, set()):
                        missed.append((name, node.lineno, f"from {alias or '.'} import {it.name}", sub))
            if base in modules and base != name:
                correct[name].add(base)
        # 守卫对 from . import a,b （node.module is None, level=1）完全没有建边
        if isinstance(node, ast.ImportFrom) and node.level and not node.module:
            for it in node.names:
                sub = f"{ag._resolve('.' * node.level + it.name, name)}"
                if sub in modules and sub != name:
                    correct[name].add(sub)
                    if sub not in g.get(name, set()):
                        missed.append((name, node.lineno, f"from {'.' * node.level} import {it.name}", sub))

cyc_correct = tarjan(correct)
print()
print(f"正确图边数: {sum(len(v) for v in correct.values())}  (守卫图 {sum(len(v) for v in g.values())})")
print(f"正确图非平凡 SCC 数: {len(cyc_correct)}")
for c in cyc_correct:
    print("   环:", sorted(c))

print()
print("守卫图缺失的边（守卫完全没有建出的 module 内部依赖）:")
cnt = Counter(m for m, _, _, _ in missed)
for m, c in cnt.most_common(20):
    print(f"   {m}: 缺 {c} 条")
print(f"   合计缺失边: {len(missed)}")
for m, ln, txt, sub in missed[:16]:
    print(f"     {m}:{ln}  {txt} -> {sub}")

print()
print("=" * 74)
print("检查 #2 test_subpackages_do_not_import_top_level_shims 的盲区验证")
print("=" * 74)
OLD = ag.OLD_TOP_LEVEL_NAMES
violations_guard = []
missed_violations = []
for name, path in modules.items():
    parts = name.split(".")
    if len(parts) < 3:
        continue
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            aliases = [i.name for i in node.names]
            imported_names = [i.name for i in node.names]
        elif isinstance(node, ast.ImportFrom):
            aliases = [node.module or ""]
            imported_names = [i.name for i in node.names]
        else:
            continue
        for alias in aliases:
            if not alias.startswith("module."):
                continue
            leaf = alias.split(".")[1]
            if leaf in OLD:
                violations_guard.append(f"{name}:{node.lineno} imports {alias}")
print("守卫能检出的违规:", violations_guard if violations_guard else "无")

# 手工检出：`from module import <shim>` 形式被 startswith("module.") 漏掉
for name, path in modules.items():
    parts = name.split(".")
    if len(parts) < 3:
        continue
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "") == "module":
            for it in node.names:
                if it.name in OLD:
                    missed_violations.append(
                        (f"{name}:{node.lineno}", f"from module import {it.name}")
                    )
print("★守卫漏掉的违规（`from module import <shim>`）:")
for loc, txt in missed_violations:
    print(f"   {loc}  {txt}")
print(f"   合计: {len(missed_violations)}")
