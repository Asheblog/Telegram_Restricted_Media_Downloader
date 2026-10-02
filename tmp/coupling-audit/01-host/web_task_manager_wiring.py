# coding=UTF-8
r"""Divergence between the two WebUITaskManager wirings.

  A: module/composition_root.py:156-184   (primary, inside TrmdCompositionRoot.__init__)
  B: module/adapters/webui/operations.py:73-99 (_require_web_task_manager fallback)

Run:  .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\web_task_manager_wiring.py
"""
from __future__ import annotations

import ast
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
MOD = REPO / "module"
sys.path.insert(0, str(REPO))


def kw_at(path: pathlib.Path, lineno: int, callee: str) -> list[str]:
    t = ast.parse(path.read_text(encoding="utf-8"))
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and ast.unparse(n.func) == callee and n.lineno == lineno:
            return [k.arg for k in n.keywords if k.arg]
    return []


def main() -> None:
    a = kw_at(MOD / "composition_root.py", 156, "WebUITaskManager")
    b = kw_at(MOD / "adapters" / "webui" / "operations.py", 73, "WebUITaskManager")
    print(f"A composition_root.py:156  kwargs={len(a)}")
    print(f"B operations.py:73         kwargs={len(b)}")
    sa, sb = set(a), set(b)
    print(f"\nonly in A ({len(sa - sb)}): {sorted(sa - sb)}")
    print(f"only in B ({len(sb - sa)}): {sorted(sb - sa)}")
    print(f"common   ({len(sa & sb)}): {sorted(sa & sb)}")

    from module.adapters.webui.task_manager import WebUITaskManager
    import inspect
    sig = inspect.signature(WebUITaskManager.__init__)
    print("\ndefaults of the parameters only wired in A:")
    for name in sorted(sa - sb):
        p = sig.parameters.get(name)
        print(f"   {name:46s} default={p.default!r}" if p else f"   {name} (absent)")


if __name__ == "__main__":
    sys.exit(main())
