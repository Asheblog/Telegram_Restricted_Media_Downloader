# coding=UTF-8
r"""MRO / name-collision audit for the facade bases (read-only).

Run:  .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\mro_collisions.py
"""
from __future__ import annotations

import ast
import collections
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
MOD = REPO / "module"
sys.path.insert(0, str(REPO))

BASES = [
    ("TrmdCompositionRoot", "composition_root.py"),
    ("WebOperationsMixin", "adapters/webui/operations.py"),
    ("BotHostMixin", "adapters/bot/host.py"),
    ("TelegramRestrictedMediaDownloader (facade body)", "downloader.py"),
]


def members(rel: str, cls_name: str):
    p = MOD / rel
    t = ast.parse(p.read_text(encoding="utf-8"))
    for c in ast.walk(t):
        if isinstance(c, ast.ClassDef) and c.name == cls_name:
            out = {}
            for n in c.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[n.name] = n.lineno
                elif isinstance(n, ast.Assign):
                    for tgt in n.targets:
                        if isinstance(tgt, ast.Name):
                            out[tgt.id] = n.lineno
            return out, c
    return {}, None


def main() -> None:
    tables = []
    for name, rel in BASES:
        cls = name.split(" ")[0]
        m, node = members(rel, cls)
        tables.append((name, rel, m))
        print(f"{name:48s} {rel:38s} members={len(m)}")

    print("\n== name collisions across bases (C3 silently picks the leftmost) ==")
    owners = collections.defaultdict(list)
    for name, rel, m in tables:
        for k, ln in m.items():
            owners[k].append((name, rel, ln))
    coll = {k: v for k, v in owners.items() if len(v) > 1}
    for k in sorted(coll, key=lambda k: (len(coll[k]), k), reverse=True):
        print(f"  {len(coll[k])}x  {k}")
        for name, rel, ln in coll[k]:
            print(f"        {name:48s} {rel}:{ln}")
    print(f"\ntotal colliding names: {len(coll)}")

    print("\n== real MRO ==")
    from module.downloader import TelegramRestrictedMediaDownloader as F  # noqa: E402
    for i, c in enumerate(F.__mro__):
        print(f"  [{i}] {c.__module__}.{c.__name__}")
    print("\n== method resolution for every colliding name (via MRO) ==")
    for k in sorted(coll):
        owner = None
        for c in F.__mro__:
            if k in c.__dict__:
                owner = c
                break
        print(f"  {k:52s} -> {owner.__module__}.{owner.__name__}")


if __name__ == "__main__":
    sys.exit(main())
