# coding=UTF-8
r"""Ordered-token similarity between downloader.py's big orchestration methods.

Token stream is built by a SOURCE-ORDER pre-order walk: one token per statement,
calls recorded as `call:<dotted-func>`, attributes as `attr:<name>`, controls as
`for/if/try/with/while`. This keeps ordering meaningful (unlike ast.walk).

Run:  .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\method_similarity.py
"""
from __future__ import annotations

import ast
import difflib
import pathlib
import sys

DL = pathlib.Path(r"E:\codebase\tgbot\module\downloader.py")
SRC = DL.read_text(encoding="utf-8")


def tokens(node: ast.AST) -> list[str]:
    out: list[str] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Call):
            out.append("call:" + ast.unparse(child.func))
            out += tokens(child)
        elif isinstance(child, ast.Attribute):
            out.append("attr:" + child.attr)
            out += tokens(child)
        elif isinstance(child, (ast.For, ast.AsyncFor)):
            out.append("for")
            out += tokens(child)
        elif isinstance(child, ast.If):
            out.append("if")
            out += tokens(child)
        elif isinstance(child, ast.Try):
            out.append("try")
            out += tokens(child)
        elif isinstance(child, (ast.With, ast.AsyncWith)):
            out.append("with")
            out += tokens(child)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append("def:" + child.name)
        else:
            out += tokens(child)
    return out


def main() -> None:
    t = ast.parse(SRC)
    cls = None
    for c in ast.walk(t):
        if isinstance(c, ast.ClassDef) and c.name == "TelegramRestrictedMediaDownloader":
            cls = c
    fns = {n.name: n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    names = ["__add_task", "resume_download", "create_download_task", "get_forward_link_from_bot", "__download_media_from_links"]
    toks = {}
    for n in names:
        f = fns[n]
        toks[n] = tokens(f)
        print(f"{n:32s} L{f.lineno:4d}-{f.end_lineno:4d} src_lines={f.end_lineno - f.lineno + 1:4d} ordered_tokens={len(toks[n]):4d}")
    print("\n== difflib ratio on ordered token streams ==")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            r = difflib.SequenceMatcher(None, toks[a], toks[b], autojunk=False).ratio()
            blk = difflib.SequenceMatcher(None, toks[a], toks[b], autojunk=False).find_longest_match(0, len(toks[a]), 0, len(toks[b]))
            print(f"  {a:26s} vs {b:26s} ratio={r:.3f} longest_common_run={blk.size} tokens")


if __name__ == "__main__":
    sys.exit(main())
