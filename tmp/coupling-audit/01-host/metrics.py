# coding=UTF-8
"""A1 host/facade coupling metrics (read-only). Prints reproducible counters."""
from __future__ import annotations

import ast
import collections
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
MOD = REPO / "module"


def tree(rel: str) -> ast.Module:
    return ast.parse((MOD / rel).read_text(encoding="utf-8"))


def cls(tree_: ast.Module, name: str):
    for n in ast.walk(tree_):
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None


def funcs(node: ast.ClassDef):
    return [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def kw_ends_with(call: ast.Call, suffix: str):
    return [k for k in call.keywords if k.arg and k.arg.endswith(suffix)]


def self_attrs(node: ast.AST, mode: str):
    """mode='store' -> self.X = / annotated; mode='read' -> self.X loads"""
    stored, read = set(), set()
    for n in ast.walk(node):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                    stored.add(t.attr)
        elif isinstance(n, ast.AnnAssign):
            t = n.target
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                stored.add(t.attr)
        elif isinstance(n, ast.AugAssign):
            t = n.target
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                stored.add(t.attr)
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self":
            if n.attr not in stored:
                read.add(n.attr)
    return (stored if mode == "store" else read)


def is_pure_shim(fn: ast.FunctionDef) -> bool:
    """fn body == single `return <expr>(*args, **kwargs)` / `...(...)` call, args are *args/**kwargs."""
    body = [b for b in fn.body if not (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str))]
    if len(body) != 1:
        return False
    stmt = body[0]
    call = None
    if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
        call = stmt.value
    elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        call = stmt.value
    if call is None:
        return False
    if not any(isinstance(a, ast.Starred) and isinstance(a.value, ast.Name) and a.value.id == "args" for a in call.args):
        return False
    if not any(k.arg is None and isinstance(k.value, ast.Name) and k.value.id == "kwargs" for k in call.keywords):
        return False
    return True


def report_composition_root() -> None:
    t = tree("composition_root.py")
    c = cls(t, "TrmdCompositionRoot")
    print("== [CR] composition_root.py ==")
    print(f"CR methods            : {len(funcs(c))}")
    print(f"CR total lines        : {len((MOD / 'composition_root.py').read_text(encoding='utf-8').splitlines())}")
    stored = self_attrs(c, "store")
    print(f"CR self.<attr> stores : {len(stored)}")
    print(f"   {sorted(stored)}")
    # getter keyword args passed into collaborator constructors
    getters = collections.Counter()
    for n in ast.walk(c):
        if isinstance(n, ast.Call):
            for k in kw_ends_with(n, "_getter"):
                getters[k.arg] += 1
    print(f"getter= call sites    : {sum(getters.values())} kwarg bindings, {len(getters)} distinct kwarg names")
    for name, cnt in getters.most_common():
        print(f"   {cnt:3d}  {name}")
    print(f"suffix _getter (all)  : {sum(1 for n in ast.walk(c) if isinstance(n, ast.keyword) and n.arg and n.arg.endswith('_getter'))}")
    # _require_* helpers
    req = [f.name for f in funcs(c) if f.name.startswith("_require_")]
    print(f"_require_* helpers    : {len(req)} -> {req}")
    # forwarding shims in CR
    shims = [f.name for f in funcs(c) if is_pure_shim(f)]
    print(f"pure *args/**kwargs shims in CR : {len(shims)}")
    for s in shims:
        print(f"   L{next(f.lineno for f in funcs(c) if f.name == s):4d}  {s}")
    # self.<attr> reads in CR
    read = self_attrs(c, "read")
    print(f"CR self.<attr> reads  : {len(read)}")
    # reverse injection
    print("alias/injection lines:")
    for i, line in enumerate((MOD / "composition_root.py").read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if s.startswith("self.bot.") or s.startswith("self.listen_") or s.startswith("self.web_pending") or s.startswith("self.web_watch") or s.startswith("self.handle_media_groups"):
            print(f"   L{i:4d}  {s}")


def report_downloader() -> None:
    src = (MOD / "downloader.py").read_text(encoding="utf-8")
    t = ast.parse(src)
    print("\n== [DL] downloader.py ==")
    print(f"lines                 : {len(src.splitlines())}")
    classes = [n for n in t.body if isinstance(n, ast.ClassDef)]
    for c in classes:
        bases = [ast.unparse(b) for b in c.bases]
        ms = funcs(c)
        shims = [f for f in ms if is_pure_shim(f)]
        print(f"class {c.name} L{c.lineno}-{c.end_lineno} bases={bases}")
        print(f"   methods             : {len(ms)}")
        print(f"   pure shims          : {len(shims)} -> {[ (f.name, f.lineno) for f in shims ]}")
        print(f"   self.<attr> stores  : {len(self_attrs(c, 'store'))}")
    # all methods anywhere
    allf = [n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    print(f"module functions (all): {len(allf)}")
    # *args/**kwargs anywhere
    star = [f for f in allf if f.args.vararg and f.args.kwarg]
    print(f"funcs with *args+**kwargs : {len(star)} -> {sorted((f.name, f.lineno) for f in star)}")
    # getattr(self.<x>) dynamic dispatch
    dyn = []
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "getattr":
            s = ast.unparse(n)
            if len(s) < 120:
                dyn.append((n.lineno, s))
    print(f"getattr(...) call sites: {len(dyn)}")


def report_runner() -> None:
    src = (MOD / "transfer" / "runner.py").read_text(encoding="utf-8")
    t = ast.parse(src)
    print("\n== [RT] transfer/runner.py ==")
    print(f"lines                 : {len(src.splitlines())}")
    for c in [n for n in t.body if isinstance(n, ast.ClassDef)]:
        bases = [ast.unparse(b) for b in c.bases]
        ms = funcs(c)
        print(f"class {c.name} L{c.lineno}-{c.end_lineno} bases={bases} methods={len(ms)}")
    # protocol members
    proto = cls(t, "WebTransferHost")
    if proto is not None:
        ms = funcs(proto)
        print(f"WebTransferHost members: {len(ms)}")
        print("   " + ", ".join(f.name for f in ms))
    # _resolve_method
    for f in [n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        if f.name == "_resolve_method":
            print(f"_resolve_method at L{f.lineno}-{f.end_lineno}")
    # count getattr(host,...) / hasattr(host,...) call sites per function
    per_func = collections.Counter()
    lines = collections.defaultdict(list)
    for f in [n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for n in ast.walk(f):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"getattr", "hasattr", "callable"}:
                s = ast.unparse(n)
                if "host" in s:
                    per_func[f.name] += 1
                    lines[f.name].append((n.lineno, s))
    total = sum(per_func.values())
    print(f"functions touching host via getattr/hasattr/callable: {len(per_func)}")
    print(f"total getattr/hasattr/callable(host...) sites        : {total}")
    for name, cnt in per_func.most_common():
        print(f"   {cnt:3d}  {name}  L{lines[name][0][0]}")


def report_live_transfer() -> None:
    src = (MOD / "transfer" / "live_transfer.py").read_text(encoding="utf-8")
    t = ast.parse(src)
    print("\n== [LT] transfer/live_transfer.py ==")
    print(f"lines                 : {len(src.splitlines())}")
    for c in [n for n in t.body if isinstance(n, ast.ClassDef)]:
        bases = [ast.unparse(b) for b in c.bases]
        print(f"class {c.name} L{c.lineno}-{c.end_lineno} bases={bases} methods={len(funcs(c))}")
    hits = []
    for n in ast.walk(t):
        if not hasattr(n, "lineno"):
            continue
        s = ast.unparse(n)
        if "__dict__" in s:
            hits.append((n.lineno, n.end_lineno, type(n).__name__, s))
    # keep only smallest enclosing nodes: drop nodes fully contained in another hit
    top = []
    for ln, el, kind, s in hits:
        if not any(o[0] <= ln and el <= o[1] and (o[0], o[1]) != (ln, el) for o in hits):
            top.append((ln, el, kind, s))
    print(f"__dict__ access sites (ast nodes): {len(hits)}, top-level: {len(top)}")
    for ln, el, kind, s in sorted(set(top), key=lambda x: x[0]):
        print(f"   L{ln}  [{kind}] {s[:200]}")
    req = []
    for n in ast.walk(t):
        if not hasattr(n, "lineno"):
            continue
        s = ast.unparse(n)
        if "_require_" in s:
            req.append((n.lineno, s))
    print(f"_require_* refs (all nodes): {len(req)}")
    for ln, s in sorted(set(req))[:20]:
        print(f"   L{ln}  {s[:160]}")


def report_module_paths() -> None:
    print("\n== module layout ==")
    for rel in ["bot_host.py", "web_operations.py", "downloader.py"]:
        print(f"{rel}: lines={len((MOD / rel).read_text(encoding='utf-8').splitlines())}")


def main() -> None:
    report_module_paths()
    report_composition_root()
    report_downloader()
    report_runner()
    report_live_transfer()


if __name__ == "__main__":
    sys.exit(main())
