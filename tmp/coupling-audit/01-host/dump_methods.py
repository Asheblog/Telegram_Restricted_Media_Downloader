# coding=UTF-8
"""dump method index + shim classification for downloader.py / mixins (read-only)."""
from __future__ import annotations
import ast
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
MOD = REPO / "module"
TARGETS = [
    ("downloader.py", "TelegramRestrictedMediaDownloader"),
    ("adapters/webui/operations.py", "WebOperationsMixin"),
    ("adapters/bot/host.py", "BotHostMixin"),
]


def body(fn):
    b = fn.body
    if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
        b = b[1:]
    return b


def classify(fn):
    b = body(fn)
    if len(b) != 1:
        return "multi"
    s = b[0]
    call = None
    if isinstance(s, ast.Return) and isinstance(s.value, ast.Call):
        call = s.value
    elif isinstance(s, ast.Expr) and isinstance(s.value, ast.Call):
        call = s.value
    elif isinstance(s, ast.Raise):
        return "raise"
    elif isinstance(s, ast.Pass):
        return "pass"
    if call is None:
        return "one-stmt"
    f = call.func
    if isinstance(f, ast.Attribute):
        try:
            owner = ast.unparse(f.value)
        except Exception:
            owner = "?"
        return f"deleg:{owner}.{f.attr}"
    if isinstance(f, ast.Name):
        return f"call:{f.id}"
    return "one-stmt"


def main() -> None:
    for rel, cname in TARGETS:
        p = MOD / rel
        if not p.exists():
            print(f"!! missing {rel}")
            continue
        src = p.read_text(encoding="utf-8")
        t = ast.parse(src)
        for c in [n for n in ast.walk(t) if isinstance(n, ast.ClassDef) and n.name == cname]:
            ms = [n for n in c.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            print(f"\n===== {rel} :: class {cname}  L{c.lineno}-{c.end_lineno}  methods={len(ms)} =====")
            for f in ms:
                kind = classify(f)
                print(f"  L{f.lineno:4d}-{f.end_lineno:4d}  {f.name:44s} stmts={len(body(f)):3d}  {kind}")


if __name__ == "__main__":
    sys.exit(main())
