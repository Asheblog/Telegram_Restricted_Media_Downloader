# coding=UTF-8
r"""Wiring matrix: WebUITaskManager.__init__ parameters vs the two wiring sites.

Run:  .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\wiring_matrix.py
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

from module.adapters.webui.task_manager import WebUITaskManager  # noqa: E402


def kw_at(path: pathlib.Path, lineno: int, callee: str) -> set[str]:
    t = ast.parse(path.read_text(encoding="utf-8"))
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and ast.unparse(n.func) == callee and n.lineno == lineno:
            return {k.arg for k in n.keywords if k.arg}
    return set()


def main() -> None:
    params = [p for p in inspect.signature(WebUITaskManager.__init__).parameters if p != "self"]
    a = kw_at(REPO / "module" / "composition_root.py", 156, "WebUITaskManager")
    b = kw_at(REPO / "module" / "adapters" / "webui" / "operations.py", 73, "WebUITaskManager")
    print(f"WebUITaskManager.__init__ params        : {len(params)}")
    print(f"wired at composition_root.py:156        : {len(a)}")
    print(f"wired at operations.py:73 (fallback)    : {len(b)}")
    never = [p for p in params if p not in a and p not in b]
    only_a = [p for p in params if p in a and p not in b]
    both = [p for p in params if p in a and p in b]
    print(f"\nwired in BOTH        ({len(both)})")
    print(f"wired only in A      ({len(only_a)}): {only_a}")
    print(f"NEVER wired by either({len(never)}): {never}")
    print("\nusage of the never-wired getters inside WebUITaskManager:")
    src = (REPO / "module" / "adapters" / "webui" / "task_manager.py").read_text(encoding="utf-8").splitlines()
    attr = {
        "cancel_task_uploads_getter": "_cancel_task_uploads",
        "pause_task_uploads_getter": "_pause_task_uploads",
        "cancel_task_downloads_getter": "_cancel_task_downloads",
    }
    for p in never:
        an = attr.get(p, p)
        for i, line in enumerate(src, 1):
            if an in line and "self." in line:
                print(f"   L{i:4d}  {line.strip()}")


if __name__ == "__main__":
    sys.exit(main())
