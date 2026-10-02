"""时序耦合取证：统计 module/transfer/engine.py 中 self.transfer_store 的访问点，
按所在函数归类，并判断该函数内是否存在 None 保护（提前 return / if 判断）。

engine.py:58-59 `transfer_store` property 直接读 self.ctx.transfer_store，
而 composition_root.py:193 在构造期以值捕获方式写入 None。
"""
from __future__ import annotations

import ast
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def analyse(path: str, target_attr: str = "transfer_store"):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src, filename=path)
    lines = src.splitlines()

    funcs = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(n)

    def enclosing(lineno):
        best = None
        for f in funcs:
            if f.lineno <= lineno <= (f.end_lineno or f.lineno):
                if best is None or f.lineno > best.lineno:
                    # 最内层，但如果 lineno 落在嵌套函数内则取嵌套的
                    best = f
        return best

    # 每个函数内的 None-guard 行
    guards = defaultdict(list)
    for f in funcs:
        for node in ast.walk(f):
            if isinstance(node, ast.If):
                t = ast.unparse(node.test)
                if target_attr in t and ("not " in t or " is None" in t or "None" in t):
                    guards[f.lineno].append((node.lineno, t))
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and node.value.value is None:
                t = ast.unparse(node.targets[0])
                if target_attr in t:
                    guards[f.lineno].append((node.lineno, f"= None ({t})"))

    access = []  # (lineno, enclosing func, kind, text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == target_attr:
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                f = enclosing(node.lineno)
                access.append((node.lineno, f, lines[node.lineno - 1].strip()))
        if isinstance(node, ast.Subscript) or isinstance(node, ast.Call):
            pass
    return access, guards, funcs, lines


path = os.path.join(ROOT, "module", "transfer", "engine.py")
access, guards, funcs, lines = analyse(path)

print("=" * 74)
print("module/transfer/engine.py —— self.transfer_store 访问点与保护分析")
print("=" * 74)
by_func = defaultdict(list)
for lineno, f, text in access:
    by_func[(f.lineno, f.name) if f else (0, "<module-level>")].append((lineno, text))

total = 0
for (fl, fname), items in sorted(by_func.items()):
    g = guards.get(fl, [])
    prot = "已保护" if g else "★无保护"
    print(f"\n[{fl}] {fname}()  —— {prot}, 访问 {len(items)} 处")
    for gl, gt in g:
        print(f"    guard L{gl}: {gt}")
    for lineno, text in items:
        total += 1
        print(f"    L{lineno}: {text[:100]}")
print(f"\n合计访问点: {total}")

print("\n" + "=" * 74)
print("property 定义处 (engine.py:57-59)")
print("=" * 74)
for i in range(56, 60):
    print(f"  L{i+1}: {lines[i]}")

# runner.py: host.transfer_store 的对应分析（host 是值/属性读取，非 getter）
print("\n" + "=" * 74)
print("module/transfer/runner.py —— host.transfer_store / self._host.transfer_store")
print("=" * 74)
rp = os.path.join(ROOT, "module", "transfer", "runner.py")
rsrc = open(rp, encoding="utf-8").read()
rtree = ast.parse(rsrc, filename=rp)
rlines = rsrc.splitlines()
rfuncs = [n for n in ast.walk(rtree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def encl(lineno):
    best = None
    for f in rfuncs:
        if f.lineno <= lineno <= (f.end_lineno or f.lineno):
            if best is None or f.lineno > best.lineno:
                best = f
    return best


cnt = defaultdict(int)
guardcnt = defaultdict(int)
for node in ast.walk(rtree):
    if isinstance(node, ast.Attribute) and node.attr == "transfer_store":
        f = encl(node.lineno)
        key = (f.lineno, f.name) if f else (0, "<module>")
        cnt[key] += 1
rg = defaultdict(list)
for f in rfuncs:
    for node in ast.walk(f):
        if isinstance(node, ast.If):
            t = ast.unparse(node.test)
            if "transfer_store" in t:
                rg[f.lineno].append((node.lineno, t))
for (fl, fname), c in sorted(cnt.items(), key=lambda kv: -kv[1]):
    g = rg.get(fl, [])
    print(f"  [{fl}] {fname}(): {c} 处, guards={[ (a,b) for a,b in g ][:3]}")
print("  合计:", sum(cnt.values()))
