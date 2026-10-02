# coding=UTF-8
"""Inventory of every "ask the host, else fall back locally" site.

Detects: getattr(host|self._host, '<name>', ...) / hasattr(...) / host.__dict__ probes,
and pairs them with the runner's own same-named method (double implementation).

Read-only. Run with .venv313 python (no third-party deps needed).
"""
from __future__ import annotations

import ast
import collections
import pathlib
import sys

MOD = pathlib.Path(r"E:\codebase\tgbot\module")
FILES = [
    "transfer/runner.py",
    "transfer/live_transfer.py",
    "transfer/watch_applicator.py",
]


def host_attr_probes(path: pathlib.Path):
    src = path.read_text(encoding="utf-8")
    t = ast.parse(src)
    out = []
    for fn in [n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for n in ast.walk(fn):
            if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Name):
                continue
            if n.func.id not in {"getattr", "hasattr", "callable"}:
                continue
            if not n.args:
                continue
            a0 = n.args[0]
            recv = ast.unparse(a0) if not isinstance(a0, ast.Call) else ast.unparse(a0)
            if recv not in {"host", "self._host"}:
                continue
            name = None
            if len(n.args) >= 2 and isinstance(n.args[1], ast.Constant):
                name = n.args[1].value
            out.append((fn.name, fn.lineno, n.lineno, n.func.id, recv, name,
                        len(n.args) >= 3))
    return out


def runner_methods(path: pathlib.Path, cls_name: str) -> dict[str, int]:
    src = path.read_text(encoding="utf-8")
    t = ast.parse(src)
    for c in ast.walk(t):
        if isinstance(c, ast.ClassDef) and c.name == cls_name:
            return {n.name: n.lineno for n in c.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return {}


def protocol_members(path: pathlib.Path, cls_name: str) -> set[str]:
    src = path.read_text(encoding="utf-8")
    t = ast.parse(src)
    for c in ast.walk(t):
        if isinstance(c, ast.ClassDef) and c.name == cls_name:
            return {n.name for n in c.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return set()


def main() -> None:
    for rel in FILES:
        p = MOD / rel
        probes = host_attr_probes(p)
        print(f"\n===== {rel} : {len(probes)} host probes =====")
        grouped = collections.defaultdict(list)
        for fn, fnline, ln, kind, recv, name, has_default in probes:
            grouped[(fn, fnline)].append((ln, kind, recv, name, has_default))
        for (fn, fnline), items in sorted(grouped.items(), key=lambda kv: kv[0][1]):
            names = sorted({i[3] for i in items if i[3]})
            print(f"  L{fnline:4d} {fn:46s} probes={len(items):3d} names={names}")

    runner = runner_methods(MOD / "transfer" / "runner.py", "WebTransferRunner")
    proto = protocol_members(MOD / "transfer" / "runner.py", "WebTransferHost")
    print(f"\nWebTransferRunner own methods ({len(runner)}): {sorted(runner)}")
    print(f"WebTransferHost protocol members ({len(proto)}): {sorted(proto)}")
    both = sorted(set(runner) & proto)
    print(f"\n[name exists BOTH on runner and on protocol] {len(both)}: {both}")
    # Which of those runner methods contain a host probe -> true "host-first, local fallback"
    probes = host_attr_probes(MOD / "transfer" / "runner.py")
    probed_names = sorted({p[5] for p in probes if p[5]})
    print(f"\ndistinct attribute names probed on host ({len(probed_names)}): {probed_names}")
    dual = sorted(set(probed_names) & set(runner))
    print(f"[probed on host AND locally implemented by runner] {len(dual)}: {dual}")
    only_proto = sorted(set(probed_names) - set(runner))
    print(f"[probed on host, no runner-local twin] {len(only_proto)}: {only_proto}")


if __name__ == "__main__":
    sys.exit(main())
