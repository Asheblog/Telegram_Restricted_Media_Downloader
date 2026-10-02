"""A4：runner.py 对 host 的属性访问 —— 别名感知的精确计数（多口径）。"""
from __future__ import annotations

import ast
import os
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RUNNER = os.path.join(ROOT, "module", "transfer", "runner.py")


def parse(p):
    with open(p, "rb") as f:
        return ast.parse(f.read(), filename=p)


tree = parse(RUNNER)

# --- 1) 找出所有指向 self._host 的局部别名
alias_assign = []  # (lineno, varname)
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Attribute):
        v = node.value
        if isinstance(v.value, ast.Name) and v.value.id == "self" and v.attr == "_host":
            for t in node.targets:
                if isinstance(t, ast.Name):
                    alias_assign.append((node.lineno, t.id))
    if isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Attribute):
        v = node.value
        if isinstance(v.value, ast.Name) and v.value.id == "self" and v.attr == "_host" and isinstance(node.target, ast.Name):
            alias_assign.append((node.lineno, node.target.id))

alias_names = {n for _, n in alias_assign}
print("alias assignments (lineno, var):", alias_assign)
print("alias names:", sorted(alias_names))

# 别名是否在方法内被重新赋值成别的东西（保守：只看是否被赋成非 self._host）
reassigned = Counter()
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        v = node.value
        is_host = (
            isinstance(v, ast.Attribute)
            and isinstance(v.value, ast.Name)
            and v.value.id == "self"
            and v.attr == "_host"
        )
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in alias_names and not is_host:
                reassigned[t.id] += 1
print("alias reassigned to non-host:", dict(reassigned))

# --- 2) 计数
bare_self_host = 0          # self._host
self_host_dot = 0           # self._host.X
alias_dot = 0               # host.X   (host 是别名)
alias_bare = 0              # host
alias_dot_detail = Counter()
self_host_dot_detail = Counter()
alias_attr_linenos = []

for node in ast.walk(tree):
    if isinstance(node, ast.Attribute):
        # self._host.X
        if isinstance(node.value, ast.Attribute):
            iv = node.value
            if isinstance(iv.value, ast.Name) and iv.value.id == "self" and iv.attr == "_host":
                self_host_dot += 1
                self_host_dot_detail[node.attr] += 1
        # self._host
        if isinstance(node.value, ast.Name) and node.value.id == "self" and node.attr == "_host":
            bare_self_host += 1
        # host.X
        if isinstance(node.value, ast.Name) and node.value.id in alias_names:
            alias_dot += 1
            alias_dot_detail[node.attr] += 1
            alias_attr_linenos.append((node.lineno, node.attr))
        # bare use of alias name
        if isinstance(node.value, ast.Name) and node.attr in alias_names:
            pass

# bare alias uses (as Name node, not attribute base)
alias_bare_uses = []
for node in ast.walk(tree):
    if isinstance(node, ast.Name) and node.id in alias_names:
        alias_bare_uses.append(node.lineno)

print()
print("=== 口径 ===")
print(f"A. self._host 裸出现次数              : {bare_self_host}")
print(f"B. self._host.<attr> 属性访问次数      : {self_host_dot}  detail={dict(self_host_dot_detail)}")
print(f"C. 别名 host.<attr> 属性访问次数       : {alias_dot}")
print(f"D. 别名 host 作为 Name 出现(含 Attribute 基) : {len(alias_bare_uses)}")
print(f"E. 对 host 的属性访问总数 B+C          : {self_host_dot + alias_dot}")
print(f"F. A + C (bare self._host + alias attr) : {bare_self_host + alias_dot}")
print(f"G. B + C + (别名作为参数传递处即 Attribute 基之外) : {self_host_dot + alias_dot}")
print()
print("别名 host 访问的属性名 Top 25:")
for k, v in alias_dot_detail.most_common(25):
    print(f"   {k}: {v}")
print()
print("不同属性名数 (别名口径):", len(alias_dot_detail), " (self._host 口径):", len(self_host_dot_detail))
print("不同属性名总数:", len(set(alias_dot_detail) | set(self_host_dot_detail)))

# 有多少行同时存在多次访问
lines = Counter(l for l, _ in alias_attr_linenos)
print("访问最密集的行 Top10:", lines.most_common(10))

# 方法级分布：每个函数的 host 属性访问数
func_ranges = []
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        func_ranges.append((node.lineno, node.end_lineno or node.lineno, node.name))
func_ranges.sort()
per_func = Counter()
for l, _ in alias_attr_linenos:
    for s, e, n in func_ranges:
        if s <= l <= e:
            per_func[n] += 1
            break
print()
print("host 属性访问按函数分布 Top15:", per_func.most_common(15))
print("涉及函数数:", len(per_func))

# 是否真的有 128 这个数可能来自哪里
total_ast_attribute_nodes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Attribute))
total_attribute_nodes_with_alias_or_selfhost = self_host_dot + alias_dot
print()
print("runner.py 全部 Attribute 节点数:", total_ast_attribute_nodes)
print("runner.py 全部 Name 节点数:", sum(1 for n in ast.walk(tree) if isinstance(n, ast.Name)))
print("runner.py 总行数:", len(open(RUNNER, encoding="utf-8").read().splitlines()))
