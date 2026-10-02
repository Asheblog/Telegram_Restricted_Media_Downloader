# coding=UTF-8
"""A3: module/ 顶层 shim 识别 + 引用者统计（只读）。"""
import ast
import re
from pathlib import Path

ROOT = Path(r"E:\codebase\tgbot")
MOD = ROOT / "module"
SKIP_DIRS = {".git", ".venv", ".venv313", "node_modules", "__pycache__", ".ruff_cache",
             ".pytest_cache", "tmp", ".worktrees", ".venv314"}

shims = {}
for p in sorted(MOD.glob("*.py")):
    if p.name == "__init__.py":
        continue
    src = p.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    body = [n for n in tree.body
            if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                    and isinstance(n.value.value, str))]
    only_imports = all(isinstance(n, (ast.Import, ast.ImportFrom)) for n in body)
    names = []
    for n in body:
        if isinstance(n, ast.ImportFrom) and n.module:
            names.append(f"from {n.module} import {', '.join(a.name for a in n.names)}")
        elif isinstance(n, ast.Import):
            names.append("import " + ", ".join(a.name for a in n.names))
    if only_imports and body:
        shims[p.name] = (p.stat().st_size, p.read_text(encoding='utf-8').count("\n") + 1, names)

print(f"[shims] module/ 顶层纯 re-export 文件数 = {len(shims)} / "
      f"module/ 顶层非 __init__ 文件数 = {len(list(MOD.glob('*.py'))) - 1}")
for name, (size, lines, names) in sorted(shims.items()):
    print(f"  {name:32s} {size:>5d}B {lines:>2d}行  -> {'; '.join(names)}")

print()
print("== 引用者统计（全仓，排除自身/测试/临时目录）==")
targets = {f"module.{n[:-3]}" for n in shims} | {n[:-3] for n in shims}
hits = {}
for p in ROOT.rglob("*.py"):
    parts = set(p.parts)
    if parts & SKIP_DIRS:
        continue
    if p.parent == MOD:  # 只统计 shim 自身之外的 module 顶层
        continue
    try:
        src = p.read_text(encoding="utf-8")
    except Exception:
        continue
    for m in re.finditer(r"^\s*(?:from|import)\s+([\w\.]+)", src, re.M):
        mod = m.group(1)
        base = mod.split(".")[0]
        if mod in targets or (base == "module" and mod.count(".") >= 1 and mod.split(".")[1] in
                              {n[:-3] for n in shims}):
            hits.setdefault(mod, []).append(str(p.relative_to(ROOT)) + f":{src[:m.start()].count(chr(10))+1}")

print(f"[shim import] 全仓仍有 {sum(len(v) for v in hits.values())} 处 import 指向顶层 shim，"
       f"涉及 {len(hits)} 个 shim 模块名")
for mod, locs in sorted(hits.items(), key=lambda x: -len(x[1])):
    print(f"  {mod}  x{len(locs)}")
    for l in locs[:6]:
        print(f"      {l}")
    if len(locs) > 6:
        print(f"      ... +{len(locs)-6}")

print()
print("== shim 对应的真实现位置（module/<name>/ 子包）==")
for n in sorted(shims):
    stem = n[:-3]
    cands = [str(q.relative_to(ROOT)) for q in MOD.rglob(f"{stem}/__init__.py")]
    cands += [str(q.relative_to(ROOT)) for q in MOD.rglob(f"{stem}.py") if q.parent != MOD]
    print(f"  {n:32s} -> {cands if cands else '未找到子包同名实现'}")
