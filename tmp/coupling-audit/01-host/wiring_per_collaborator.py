# coding=UTF-8
r"""Per-collaborator wiring cost in composition_root.__init__ (read-only).

Run:  .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\wiring_per_collaborator.py
"""
from __future__ import annotations

import ast
import pathlib
import sys

CR = pathlib.Path(r"E:\codebase\tgbot\module\composition_root.py")


def main() -> None:
    t = ast.parse(CR.read_text(encoding="utf-8"))
    for c in ast.walk(t):
        if isinstance(c, ast.ClassDef) and c.name == "TrmdCompositionRoot":
            for n in c.body:
                if isinstance(n, ast.FunctionDef) and n.name == "__init__":
                    rows = []
                    for s in ast.walk(n):
                        if isinstance(s, ast.Call):
                            name = ast.unparse(s.func)
                            if "." in name:
                                continue
                            kw = [k.arg for k in s.keywords if k.arg]
                            rows.append((s.lineno, name, len(kw), sum(1 for k in kw if k.endswith("_getter")), kw))
                    rows.sort()
                    print(f"{'line':>5} {'collaborator':28s} {'kwargs':>6} {'_getter':>7}")
                    for ln, name, cnt, g, kw in rows:
                        print(f"{ln:5d} {name:28s} {cnt:6d} {g:7d}")
                    print("\n  with >5 kwargs:")
                    for ln, name, cnt, g, kw in rows:
                        if cnt > 5:
                            print(f"   L{ln} {name}: {kw}")


if __name__ == "__main__":
    sys.exit(main())
