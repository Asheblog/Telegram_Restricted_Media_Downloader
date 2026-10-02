# coding=UTF-8
"""Audit: `from module import <name>` where <name> is a legacy top-level shim.

The architecture guard only blocks `module.<shim>` in an import statement of the
form `import module.X` / `from module.X import ...`. A statement written as
`from module import X` produces alias "module" and is silently ignored.
"""
import ast
import pathlib
import re

MODULE = pathlib.Path(r"E:\codebase\tgbot\module")
SHIMS = {
    p.stem for p in MODULE.glob("*.py")
    if "Compatibility shim" in p.read_text(encoding="utf-8")
}
print(f"legacy top-level shims found: {len(SHIMS)}")
print(f"  {sorted(SHIMS)}")
print()

violations = []
for path in sorted(MODULE.rglob("*.py")):
    if "__pycache__" in path.parts:
        continue
    rel = path.relative_to(MODULE).as_posix()
    if "/" not in rel:  # the shims themselves may legitimately import
        continue
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "module":
            for alias in node.names:
                if alias.name in SHIMS:
                    # is it a submodule or a shim attribute? `from module import app`
                    # binds the submodule module.app (a shim) when one exists.
                    violations.append((rel, node.lineno, alias.name, path))

print("=== violations of 'subpackages must not import top-level shims' ===")
for rel, lineno, name, path in violations:
    print(f"  module/{rel}:{lineno}  from module import {name}  -> module.{name} (shim)")

print()
print(f"total: {len(violations)}")
if violations:
    print()
    print("=== were they inside a function body (invisible to the guard's intent)? ===")
    for rel, lineno, name, path in violations:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        scope = "module level"
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.lineno <= lineno <= (node.end_lineno or node.lineno):
                    scope = f"inside {type(node).__name__} {node.name} (line {node.lineno})"
                    break
        print(f"  module/{rel}:{lineno} -> {scope}")
