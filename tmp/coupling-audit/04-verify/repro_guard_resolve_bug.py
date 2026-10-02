"""量化 architecture_guard_case._resolve 对 __init__.py（包）相对导入的解析错误。"""
from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from unit_tests import architecture_guard_case as ag  # noqa: E402

modules = ag._modules()


def correct_resolve(level: int, mod_part: str | None, owner: str) -> str:
    """正确语义：owner 若是包（__init__.py），level=1 指向 owner 自身。"""
    is_pkg = owner in {n for n, p in modules.items() if p.name == "__init__.py"}
    parts = owner.split(".") if is_pkg else owner.split(".")[:-1]
    up = level - 1
    if up > 0:
        parts = parts[:-up] if up <= len(parts) else []
    base = ".".join(parts)
    if mod_part:
        base = (base + "." + mod_part) if base else mod_part
    return base


bad = []
tot = 0
for name, path in modules.items():
    if path.name != "__init__.py":
        continue
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or not node.level:
            continue
        tot += 1
        alias = "." * node.level + (node.module or "")
        guard = ag._resolve(alias, name)
        real = correct_resolve(node.level, node.module, name)
        sub_guard = guard
        sub_real = f"{real}.{node.names[0].name}" if node.names else real
        if guard != real:
            bad.append((name, node.lineno, alias, guard, real, [n.name for n in node.names][:4]))

print(f"__init__.py 中的相对导入语句总数: {tot}")
print(f"守卫 _resolve 解析出错的: {len(bad)}")
for name, ln, alias, g, r, names in bad:
    print(f"  {name}:{ln}  '{alias}' import {names}")
    print(f"      守卫 -> {g!r}   (不在 modules 中: {g not in modules})")
    print(f"      正确 -> {r!r}")
print()
pkg_names = {n for n, p in modules.items() if p.name == "__init__.py"}
print(f"包(__init__.py)模块数: {len(pkg_names)}")
print(f"样例: {sorted(pkg_names)[:12]}")
