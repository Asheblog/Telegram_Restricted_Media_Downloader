# coding=UTF-8
"""Find duplicate method definitions + service-locator style access patterns."""
import ast
import collections
import pathlib
import re

ROOT = pathlib.Path(r"E:\codebase\tgbot\module")

print("=== duplicate method names in the same class ===")
hits = 0
for p in sorted(ROOT.rglob("*.py")):
    if "__pycache__" in p.parts:
        continue
    tree = ast.parse(p.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            seen = collections.Counter(
                c.name for c in node.body
                if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
            dup = {k: v for k, v in seen.items() if v > 1}
            if dup:
                hits += 1
                print(f"  {p.relative_to(ROOT)}  class {node.name}: {dup}")
print(f"  total: {hits}")

print()
print("=== transfer context resolve()/build() usage ===")
for name in ("resolve(", "downloader_callbacks", ".build()", "_getter("):
    rows = []
    for p in sorted(ROOT.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if name in line and "def " not in line:
                rows.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:100]}")
    print(f"-- {name}: {len(rows)} refs")
    for r in rows[:8]:
        print("   ", r)

print()
print("=== ctx.<service> attribute reads (transfer layer) ===")
ctx_attrs = collections.Counter()
for p in sorted(ROOT.rglob("*.py")):
    if "__pycache__" in p.parts:
        continue
    for m in re.finditer(r"\bctx\.(\w+)", p.read_text(encoding="utf-8")):
        ctx_attrs[m.group(1)] += 1
for attr, n in ctx_attrs.most_common(30):
    print(f"  {n:4d}  ctx.{attr}")

print()
print("=== getattr(...) defensive fallbacks in module/ (count per file) ===")
for p in sorted(ROOT.rglob("*.py")):
    if "__pycache__" in p.parts:
        continue
    src = p.read_text(encoding="utf-8")
    n = src.count("getattr(")
    if n >= 8:
        print(f"  {n:4d}  {p.relative_to(ROOT)}")

print()
print("=== *args/**kwargs pass-through methods (per file) ===")
for p in sorted(ROOT.rglob("*.py")):
    if "__pycache__" in p.parts:
        continue
    tree = ast.parse(p.read_text(encoding="utf-8"))
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            if args.vararg or args.kwarg:
                n += 1
    if n >= 10:
        print(f"  {n:4d}  {p.relative_to(ROOT)}")
