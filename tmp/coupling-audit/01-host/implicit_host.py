# coding=UTF-8
"""Quantify implicit host surface reached through `__getattr__` / `self._host`.

For LiveTransferService: `self.<name>` where <name> is not defined on the class
  -> LiveTransferService.__getattr__ (live_transfer.py:91-92) forwards to the host.
For WebTransferRunner: distinct attribute names read off `self._host` / `host`.

Read-only.
"""
from __future__ import annotations

import ast
import collections
import pathlib
import sys

MOD = pathlib.Path(r"E:\codebase\tgbot\module")


def class_node(path: pathlib.Path, name: str):
    t = ast.parse(path.read_text(encoding="utf-8"))
    for c in ast.walk(t):
        if isinstance(c, ast.ClassDef) and c.name == name:
            return c
    return None


def own_members(c: ast.ClassDef) -> set[str]:
    out = set()
    for n in c.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(n.name)
        elif isinstance(n, ast.Assign):
            for tgt in n.targets:
                if isinstance(tgt, ast.Name):
                    out.add(tgt.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
    # names *bound* on self (self.x = ...), plus object.__setattr__(self, 'x', ...)
    for n in ast.walk(c):
        if isinstance(n, ast.Assign):
            for tgt in n.targets:
                if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == 'self':
                    out.add(tgt.attr)
                elif isinstance(tgt, ast.Name):
                    out.add(tgt.id)
        elif isinstance(n, ast.AnnAssign):
            tgt = n.target
            if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == 'self':
                out.add(tgt.attr)
            elif isinstance(tgt, ast.Name):
                out.add(tgt.id)
        elif isinstance(n, ast.For):
            for tgt in ast.walk(n.target):
                if isinstance(tgt, ast.Name):
                    out.add(tgt.id)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == '__setattr__':
            if len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                out.add(n.args[1].value)
    return out


def self_reads(c: ast.ClassDef) -> dict[str, list[int]]:
    out = collections.defaultdict(list)
    for n in ast.walk(c):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == 'self':
            out[n.attr].append(n.lineno)
    return out


def host_reads(c: ast.ClassDef, recv: set[str]) -> dict[str, list[int]]:
    out = collections.defaultdict(list)
    for n in ast.walk(c):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in recv:
            out[n.attr].append(n.lineno)
    return out


def main() -> None:
    lt = class_node(MOD / 'transfer' / 'live_transfer.py', 'LiveTransferService')
    own = own_members(lt)
    reads = self_reads(lt)
    proxied = {k: v for k, v in reads.items() if k not in own and k != '_host'}
    print('== LiveTransferService ==')
    print(f'own members                         : {len(own)}')
    print(f'distinct self.<attr> read           : {len(reads)}')
    print(f'-> resolved via __getattr__ to host : {len(proxied)}  (proxy at L91-92)')
    print(f'-> total self.<attr> read sites      : {sum(len(v) for v in reads.values())}')
    print(f'-> proxied read sites               : {sum(len(v) for v in proxied.values())}')
    for k in sorted(proxied, key=lambda k: -len(proxied[k])):
        print(f'   {len(proxied[k]):3d}x  self.{k:42s} L{proxied[k][:6]}')

    rt = class_node(MOD / 'transfer' / 'runner.py', 'WebTransferRunner')
    hr = host_reads(rt, {'host', '_host'})
    print('\n== WebTransferRunner ==')
    print(f'distinct host.<attr> read names      : {len(hr)}')
    print(f'total host.<attr> read sites         : {sum(len(v) for v in hr.values())}')
    for k in sorted(hr, key=lambda k: -len(hr[k])):
        print(f'   {len(hr[k]):3d}x  host.{k:42s} L{hr[k][:6]}')

    wa = class_node(MOD / 'transfer' / 'watch_applicator.py', 'LiveWatchApplicator')
    if wa is not None:
        wr = host_reads(wa, {'host', '_host'})
        ownw = own_members(wa)
        print('\n== LiveWatchApplicator ==')
        print(f'distinct host.<attr> read names      : {len(wr)}')
        for k in sorted(wr, key=lambda k: -len(wr[k])):
            print(f'   {len(wr[k]):3d}x  host.{k:42s} L{wr[k][:6]}')
        print(f'_host accessed via self._host sites  : {len(wr.get("_host", []))}')


if __name__ == '__main__':
    sys.exit(main())
