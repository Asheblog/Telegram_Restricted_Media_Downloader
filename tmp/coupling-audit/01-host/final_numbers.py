# coding=UTF-8
r"""A1 headline numbers in one run (read-only).

Run:  .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\final_numbers.py
"""
from __future__ import annotations

import ast
import collections
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
MOD = REPO / "module"
sys.path.insert(0, str(REPO))


def cls_in(path: pathlib.Path, name: str) -> ast.ClassDef:
    t = ast.parse(path.read_text(encoding="utf-8"))
    for c in ast.walk(t):
        if isinstance(c, ast.ClassDef) and c.name == name:
            return c
    raise SystemExit(f"{name} not in {path}")


def stmts(fn):
    b = list(fn.body)
    if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
        b = b[1:]
    return b


def single_call(fn):
    b = stmts(fn)
    if len(b) != 1:
        return None
    s = b[0]
    if isinstance(s, ast.Return) and isinstance(s.value, ast.Call):
        return s.value
    if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call):
        return s.value
    return None


def main() -> None:
    cr = cls_in(MOD / "composition_root.py", "TrmdCompositionRoot")
    dl = cls_in(MOD / "downloader.py", "TelegramRestrictedMediaDownloader")
    ops = cls_in(MOD / "adapters" / "webui" / "operations.py", "WebOperationsMixin")
    bh = cls_in(MOD / "adapters" / "bot" / "host.py", "BotHostMixin")

    print("### composition_root.TrmdCompositionRoot")
    print("methods                       :", len([n for n in cr.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]))
    stored = set()
    for n in ast.walk(cr):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                    stored.add(t.attr)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Attribute):
            stored.add(n.target.attr)
    print("self.<attr> state slots       :", len(stored))
    kw = [k.arg for n in ast.walk(cr) if isinstance(n, ast.Call) for k in n.keywords if k.arg]
    print("keyword args total            :", len(kw))
    print("... ending in _getter         :", sum(1 for k in kw if k.endswith("_getter")))
    print("_require_* helpers            :", [n.name for n in cr.body if isinstance(n, ast.FunctionDef) and n.name.startswith("_require_")])
    print("*args/**kwargs shims          :", len([n for n in cr.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.args.vararg and n.args.kwarg]))

    print("\n### downloader.TelegramRestrictedMediaDownloader")
    ms = [n for n in dl.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    print("methods                       :", len(ms))
    pt = [f for f in ms if single_call(f) is not None]
    lazy = collections.defaultdict(set)
    for f in ms:
        for n in ast.walk(f):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                s = ast.unparse(n.func)
                for h in ("self._ensure_live_transfer", "self._ensure_transfer_runner", "self._require_pikpak_manager", "self._require_progress_tracker", "self._ensure_watch_applicator"):
                    if s.startswith(h):
                        lazy[h].add(f.name)
    print("single-statement passthrough  :", len(pt))
    for h, names in sorted(lazy.items()):
        print(f"methods forwarding to {h:32s}: {len(names)}")

    print("\n### adapters/webui/operations.WebOperationsMixin")
    ms2 = [n for n in ops.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    print("methods                       :", len(ms2))
    print("single-statement passthrough  :", len([f for f in ms2 if single_call(f) is not None]))
    print("self.__dict__.get(...) probes :", sum(1 for n in ast.walk(ops) if isinstance(n, ast.Call) and ast.unparse(n.func) == "self.__dict__.get"))

    print("\n### adapters/bot/host.BotHostMixin")
    ms3 = [n for n in bh.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    print("methods                       :", len(ms3))
    print("single-statement passthrough  :", len([f for f in ms3 if single_call(f) is not None]))
    print("bodies <=2 statements         :", len([f for f in ms3 if len(stmts(f)) <= 2]))

    print("\n### transfer/live_transfer.LiveTransferService")
    from module.transfer.live_transfer import LiveTransferService as S
    lt = cls_in(MOD / "transfer" / "live_transfer.py", "LiveTransferService")
    own = set(S.__dict__)
    reads = collections.defaultdict(list)
    for n in ast.walk(lt):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self":
            reads[n.attr].append(n.lineno)
    prox = {k: v for k, v in reads.items() if k not in own}
    priv = {k: v for k, v in prox.items() if k.startswith("_")}
    print("own class members             :", len(own))
    print("self.<attr> read distinct     :", len(reads), "sites:", sum(len(v) for v in reads.values()))
    print("-> forwarded to host by __getattr__ :", len(prox), "names /", sum(len(v) for v in prox.values()), "sites")
    print("-> of which facade PRIVATE helpers  :", len(priv), "names /", sum(len(v) for v in priv.values()), "sites", sorted(priv))

    print("\n### transfer/runner.WebTransferRunner")
    from module.transfer.runner import WebTransferHost
    rt = cls_in(MOD / "transfer" / "runner.py", "WebTransferRunner")
    proto = [m for m in WebTransferHost.__dict__ if not m.startswith("_")]
    print("protocol members              :", len(proto))
    print("runner own methods            :", len([n for n in rt.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]))
    probes = collections.defaultdict(set)
    for f in [n for n in rt.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for n in ast.walk(f):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"getattr", "hasattr", "callable"} and n.args:
                recv = ast.unparse(n.args[0])
                if recv in {"host", "self._host"} and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant):
                    probes[n.args[1].value].add(f.name)
    print("distinct names probed on host  :", len(probes))
    print("... with a same-named runner impl:", sorted(set(probes) & {n.name for n in rt.body if isinstance(n, ast.FunctionDef)}))


if __name__ == "__main__":
    sys.exit(main())
