# coding=UTF-8
"""A3: source_folders.py 垃圾桶判定 + 生产代码 vs 测试的 shim 使用（只读）。"""
import ast
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"E:\codebase\tgbot")
SKIP_DIRS = {".git", ".venv", ".venv313", "node_modules", "__pycache__", ".ruff_cache",
             ".pytest_cache", "tmp", ".worktrees"}

TARGET_REAL = "module.domain.archive_naming.source_folders"
TARGET_SHIM = "module.source_folders"

importers_prod = []
importers_test = []
for p in ROOT.rglob("*.py"):
    if set(p.parts) & SKIP_DIRS:
        continue
    try:
        src = p.read_text(encoding="utf-8")
    except Exception:
        continue
    rel = str(p.relative_to(ROOT))
    is_test = rel.startswith("unit_tests") or rel.startswith("tests")
    for m in re.finditer(r"^\s*(?:from|import)\s+(module\.source_folders|module\.domain\.archive_naming\.source_folders)\b",
                         src, re.M):
        entry = f"{rel}:{src[:m.start()].count(chr(10))+1} [{m.group(1)}]"
        (importers_test if is_test else importers_prod).append(entry)

print(f"== source_folders fan-in ==")
print(f"  生产代码 import 点 = {len(importers_prod)}")
for e in importers_prod:
    print(f"    {e}")
print(f"  测试代码 import 点 = {len(importers_test)}")
for e in importers_test:
    print(f"    {e}")
prod_files = {e.split(':')[0] for e in importers_prod}
test_files = {e.split(':')[0] for e in importers_test}
print(f"  去重: 生产文件 {len(prod_files)} 个, 测试文件 {len(test_files)} 个, 合计 {len(prod_files|test_files)}")

sf = ROOT / "module/domain/archive_naming/source_folders.py"
src = sf.read_text(encoding="utf-8")
tree = ast.parse(src)
print()
print(f"== {sf.relative_to(ROOT)} ==")
print(f"  bytes={sf.stat().st_size} lines={len(src.splitlines())} "
      f"imports_at_top={sum(1 for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)))}")
defs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
print(f"  顶层定义数 = {len(defs)}")
for n in defs:
    kind = "class" if isinstance(n, ast.ClassDef) else "def"
    span = n.end_lineno - n.lineno + 1
    args = ""
    if kind == "def":
        a = [x.arg for x in n.args.args]
        args = f"({', '.join(a)})"
    doc = ast.get_docstring(n) or ""
    doc = doc.strip().splitlines()[0][:60] if doc else ""
    print(f"    L{n.lineno:>4}-{n.end_lineno:<4} {span:>3}行 {kind} {n.name}{args}  {doc}")

print()
print("== 顶层 import 依赖（source_folders 依赖了多少其它模块）==")
for n in tree.body:
    if isinstance(n, ast.ImportFrom):
        print(f"    from {n.module} import {', '.join(a.name for a in n.names)}")
    elif isinstance(n, ast.Import):
        print(f"    import {', '.join(a.name for a in n.names)}")

print()
print("== 各生产文件的 shim 依赖统计 ==")
shim_names = {p.stem for p in (ROOT / "module").glob("*.py") if p.stem != "__init__"}
prod_shim_sites = defaultdict(list)
for p in ROOT.rglob("*.py"):
    if set(p.parts) & SKIP_DIRS:
        continue
    rel = str(p.relative_to(ROOT))
    if rel.startswith("unit_tests") or rel.startswith("tests"):
        continue
    if p.parent == ROOT / "module":
        continue
    try:
        src = p.read_text(encoding="utf-8")
    except Exception:
        continue
    for m in re.finditer(r"^\s*(?:from|import)\s+module\.(\w+)\b", src, re.M):
        if m.group(1) in shim_names:
            prod_shim_sites[rel].append((src[:m.start()].count(chr(10)) + 1, m.group(1)))
tot = sum(len(v) for v in prod_shim_sites.values())
print(f"  生产代码中 import 顶层 shim 的位置 = {tot} 处，涉及 {len(prod_shim_sites)} 个文件")
for rel, items in sorted(prod_shim_sites.items()):
    print(f"    {rel}: {len(items)} 处 -> " + ", ".join(f"L{l}:module.{n}" for l, n in items[:8]))
