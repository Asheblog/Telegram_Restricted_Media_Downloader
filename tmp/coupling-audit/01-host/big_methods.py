# coding=UTF-8
r"""Similarity between the three big download-orchestration methods in downloader.py,
and the implementation shape of the 15 WebTransferHost protocol members on the facade.

Run:  .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\big_methods.py
"""
from __future__ import annotations

import ast
import difflib
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))
DL = REPO / "module" / "downloader.py"
SRC = DL.read_text(encoding="utf-8")
LINES = SRC.splitlines()


def fn_range(tree, cls, name):
    for c in ast.walk(tree):
        if isinstance(c, ast.ClassDef) and c.name == cls:
            for n in c.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
                    return n
    return None


def norm(node: ast.AST) -> list[str]:
    """token stream of AST with identifiers/constants normalised"""
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.append("NAME")
        elif isinstance(n, ast.Attribute):
            out.append("ATTR" + "." + n.attr)
        elif isinstance(n, ast.Constant):
            out.append("CONST")
        elif isinstance(n, ast.Call):
            out.append("CALL")
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.For, ast.While, ast.If, ast.Try, ast.With)):
            out.append(type(n).__name__)
    return out


def main() -> None:
    t = ast.parse(SRC)
    cls = "TelegramRestrictedMediaDownloader"
    names = ["__add_task", "resume_download", "create_download_task", "get_forward_link_from_bot", "run"]
    nodes = {}
    print("== method sizes ==")
    for n in names:
        f = fn_range(t, cls, n)
        body = "\n".join(LINES[f.lineno - 1:f.end_lineno])
        nodes[n] = f
        print(f"  {n:28s} L{f.lineno}-{f.end_lineno}  lines={f.end_lineno - f.lineno + 1:4d}  stmts={len(f.body)}")

    print("\n== normalised-AST similarity (difflib ratio on token stream) ==")
    toks = {n: norm(f) for n, f in nodes.items()}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            r = difflib.SequenceMatcher(None, toks[a], toks[b]).ratio()
            print(f"  {a:24s} vs {b:24s} ratio={r:.3f}  tokens={len(toks[a])}/{len(toks[b])}")

    def body_of(node):
        b = list(node.body)
        if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
            b = b[1:]
        return b

    print("\n== WebTransferHost protocol members: how the facade implements each ==")
    from module.transfer.runner import WebTransferHost
    import inspect
    proto = [m for m in WebTransferHost.__dict__ if not m.startswith("_")]
    print(f"  protocol members: {len(proto)}")
    for m in proto:
        owner = None
        for c in type(sys.modules["module.downloader"]).__mro__ if False else []:
            pass
        from module.downloader import TelegramRestrictedMediaDownloader as F
        for c in F.__mro__:
            if m in c.__dict__:
                owner = c
                break
        obj = getattr(F, m)
        target = obj.fget if isinstance(obj, property) else obj
        fnode = None
        for c in ast.walk(ast.parse(pathlib.Path(target.__code__.co_filename).read_text(encoding="utf-8"))):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)) and c.name == target.__name__ and c.lineno == target.__code__.co_firstlineno:
                fnode = c
                break
        kind = "?"
        sig = "(*args, **kwargs)" if "kwargs" in inspect.signature(target).parameters and any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in inspect.signature(target).parameters.values()
        ) else ""
        if fnode is not None:
            b = body_of(fnode)
            if len(b) == 1 and isinstance(b[0], (ast.Return, ast.Expr)):
                kind = "PASSTHROUGH(1 stmt)"
            elif len(b) <= 2:
                kind = f"glue({len(b)} stmts)"
            else:
                kind = f"impl({len(b)} stmts)"
        owner_name = f"{owner.__module__.split('.')[-1]}.{owner.__name__}" if owner else "-"
        print(f"  {m:44s} {kind:20s} defined in {owner_name:34s} {sig}")


if __name__ == "__main__":
    sys.exit(main())
