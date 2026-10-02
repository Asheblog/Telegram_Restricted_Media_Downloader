# coding=UTF-8
"""Classify facade methods into: real impl / passthrough delegation / thin glue.

Read-only. Prints counts + per-method evidence (line, source slice).
"""
from __future__ import annotations

import ast
import collections
import pathlib
import sys

MOD = pathlib.Path(r"E:\codebase\tgbot\module")
TARGETS = [
    ("downloader.py", "TelegramRestrictedMediaDownloader"),
    ("adapters/webui/operations.py", "WebOperationsMixin"),
    ("adapters/bot/host.py", "BotHostMixin"),
    ("composition_root.py", "TrmdCompositionRoot"),
]

SERVICE_ATTRS = {
    "transfer_engine", "_te", "watch_manager", "pikpak_manager",
    "progress_tracker", "web_task_manager", "bot", "ctx",
    "live_transfer", "_transfer_runner", "_watch_applicator",
    "gc", "app", "local_storage_guard", "download_upload_window",
    "setup_coordinator", "system_log", "diagnostic", "web_ui",
}


def body(fn):
    b = list(fn.body)
    if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
        b = b[1:]
    return b


def single_call(fn):
    """Return the single Call node if the whole body is exactly one call/return-call/await-call."""
    b = body(fn)
    if len(b) != 1:
        return None
    s = b[0]
    if isinstance(s, ast.Await):
        return None
    if isinstance(s, ast.Return) and isinstance(s.value, ast.Call):
        return s.value
    if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call):
        return s.value
    return None


def call_stmts(fn):
    """count statements that are only a delegating call (return/expr) anywhere in body, and total stmts."""
    total = 0
    deleg = 0
    for s in body(fn):
        total += 1
        c = None
        if isinstance(s, ast.Return) and isinstance(s.value, ast.Call):
            c = s.value
        elif isinstance(s, ast.Expr) and isinstance(s.value, ast.Call):
            c = s.value
        if c is not None and isinstance(c.func, ast.Attribute):
            deleg += 1
    return total, deleg


def target_of(call: ast.Call) -> str:
    f = call.func
    if isinstance(f, ast.Attribute):
        return ast.unparse(f.value) + "." + f.attr
    if isinstance(f, ast.Name):
        return f.id
    return "?"


def main() -> None:
    grand = collections.Counter()
    for rel, cname in TARGETS:
        p = MOD / rel
        src = p.read_text(encoding="utf-8")
        lines = src.splitlines()
        t = ast.parse(src)
        cls = [n for n in ast.walk(t) if isinstance(n, ast.ClassDef) and n.name == cname]
        if not cls:
            print(f"!! {cname} not in {rel}")
            continue
        c = cls[0]
        ms = [n for n in c.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        passthrough, glue, real = [], [], []
        for f in ms:
            total, deleg = call_stmts(f)
            c1 = single_call(f)
            if c1 is not None:
                tgt = target_of(c1)
                # single call -> classify by callee
                if tgt.startswith("self.") and "." in tgt[len("self."):]:
                    passthrough.append((f, tgt))
                elif tgt.startswith("_require") or tgt.startswith("self._require") or tgt.startswith("self._ensure"):
                    passthrough.append((f, tgt))
                elif tgt.startswith("self."):
                    glue.append((f, tgt))
                else:
                    passthrough.append((f, tgt))
            elif total <= 2:
                glue.append((f, f"{total} stmts"))
            else:
                real.append((f, f"{total} stmts"))
        print(f"\n===== {rel} :: {cname} (L{c.lineno}-{c.end_lineno}) =====")
        print(f"methods={len(ms)}  single-call-passthrough={len(passthrough)}  thin-glue(<=2 stmts)={len(glue)}  multi-stmt-impl={len(real)}")
        grand["methods"] += len(ms)
        grand["passthrough"] += len(passthrough)
        grand["glue"] += len(glue)
        grand["real"] += len(real)
        print("  -- passthrough (1 statement, forwarding to another object) --")
        for f, tgt in passthrough:
            print(f"    L{f.lineno:4d}  {f.name:46s} -> {tgt}")
    print("\n== totals ==")
    print(dict(grand))


if __name__ == "__main__":
    sys.exit(main())
