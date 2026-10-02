# coding=UTF-8
r"""Extra A1 metrics + two executable proofs (read-only).

Proofs:
  P1  `bot.downloader = self` is write-only (no reader in the repo).
  P2  TrmdCompositionRoot._require_watch_manager() on a bare host leaves the
      host aliases (listen_download_chat / listen_forward_chat) absent, while
      WebOperationsMixin.restore_live_transfer_watches reads them directly.
Run:  .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\extra_metrics.py
"""
from __future__ import annotations

import ast
import collections
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
MOD = REPO / "module"
sys.path.insert(0, str(REPO))


def ports_fields(path: pathlib.Path, func_name: str, ctor: str) -> list[str]:
    t = ast.parse(path.read_text(encoding="utf-8"))
    for fn in ast.walk(t):
        if isinstance(fn, ast.FunctionDef) and fn.name == func_name:
            for n in ast.walk(fn):
                if isinstance(n, ast.Call) and ast.unparse(n.func) == ctor:
                    return [k.arg for k in n.keywords if k.arg]
    return []


def nest_fields(path: pathlib.Path, func_name: str, outer: str, inner: str) -> dict:
    t = ast.parse(path.read_text(encoding="utf-8"))
    res = {}
    for fn in ast.walk(t):
        if isinstance(fn, ast.FunctionDef) and fn.name == func_name:
            for n in ast.walk(fn):
                if isinstance(n, ast.Call) and ast.unparse(n.func) == outer:
                    for k in n.keywords:
                        if k.arg and isinstance(k.value, ast.Call) and ast.unparse(k.value.func) == inner:
                            res[k.arg] = [kk.arg for kk in k.value.keywords if kk.arg]
    return res


def method_idioms(path: pathlib.Path, cls: str, attrs: list[str]) -> dict:
    t = ast.parse(path.read_text(encoding="utf-8"))
    for c in ast.walk(t):
        if isinstance(c, ast.ClassDef) and c.name == cls:
            cnt = collections.Counter()
            for n in ast.walk(c):
                if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self":
                    if n.attr in attrs:
                        cnt[n.attr] += 1
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                    s = ast.unparse(n.func)
                    if s.startswith("self._require_") or s.startswith("self._ensure_"):
                        cnt[s.split(".")[1]] += 1
            return cnt
    return {}


def main() -> None:
    cr = MOD / "composition_root.py"
    print("== [M1] TransferPorts wiring written twice ==")
    main_ports = nest_fields(cr, "_build_transfer_ports", "TransferPorts", "TransferPathPorts")
    # collect all groups
    def groups(func_name):
        t = ast.parse(cr.read_text(encoding="utf-8"))
        out = {}
        for fn in ast.walk(t):
            if isinstance(fn, ast.FunctionDef) and fn.name == func_name:
                for n in ast.walk(fn):
                    if isinstance(n, ast.Call) and ast.unparse(n.func) == "TransferPorts":
                        for k in n.keywords:
                            if k.arg and isinstance(k.value, ast.Call) and ast.unparse(k.value.func).startswith("Transfer"):
                                out[k.arg] = [kk.arg for kk in k.value.keywords if kk.arg]
        return out
    a = groups("_build_transfer_ports")
    b = groups("_create_standalone_transfer_engine")
    for g in sorted(set(a) | set(b)):
        fa, fb = a.get(g, []), b.get(g, [])
        print(f"   {g:10s} build={len(fa):2d} standalone={len(fb):2d} same_fields={fa == fb}")
        if fa != fb:
            print(f"      only in build      : {sorted(set(fa) - set(fb))}")
            print(f"      only in standalone : {sorted(set(fb) - set(fa))}")
    print(f"   total port fields: build={sum(len(v) for v in a.values())} standalone={sum(len(v) for v in b.values())}")

    print("\n== [M2] composition_root wiring surface ==")
    t = ast.parse(cr.read_text(encoding="utf-8"))
    kw_all, kw_getter, kw_none = 0, 0, 0
    for n in ast.walk(t):
        if isinstance(n, ast.Call):
            for k in n.keywords:
                if k.arg is None:
                    continue
                kw_all += 1
                if k.arg.endswith("_getter"):
                    kw_getter += 1
                if isinstance(k.value, ast.Constant) and k.value.value is None:
                    kw_none += 1
    print(f"   total keyword args in CR __init__ : {kw_all}")
    print(f"   ... ending in _getter             : {kw_getter}")
    print(f"   ... literally None (disabled)      : {kw_none}")

    print("\n== [M3] access idioms for the same dependency ==")
    for rel, cls, attrs in [
        ("adapters/webui/operations.py", "WebOperationsMixin", ["watch_manager", "transfer_store", "media_manager", "web_task_manager", "uploader", "transfer_engine"]),
        ("composition_root.py", "TrmdCompositionRoot", ["watch_manager", "transfer_store", "transfer_engine", "progress_tracker"]),
    ]:
        cnt = method_idioms(MOD / rel, cls, attrs)
        print(f"   {cls}: " + ", ".join(f"{k}={v}" for k, v in sorted(cnt.items())))

    print("\n== [M4] self.__dict__.get(...) probes ==")
    hits = []
    for p in sorted(MOD.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "__dict__.get(" in line:
                hits.append((p.relative_to(REPO).as_posix(), i, line.strip()))
    for f, i, s in hits:
        print(f"   {f}:{i}  {s}")

    print("\n== [P1] bot.downloader write-only ==")
    writers, readers = [], []
    for p in list(MOD.rglob("*.py")) + list((REPO / "unit_tests").rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if ".downloader" in line:
                if ".downloader =" in line:
                    writers.append(f"{p.relative_to(REPO).as_posix()}:{i}: {line.strip()}")
                else:
                    readers.append(f"{p.relative_to(REPO).as_posix()}:{i}: {line.strip()}")
    print("   writers:", writers or "none")
    print("   readers:", [r for r in readers if "downloader.py" not in r and "transfer/live_transfer.py" not in r] or "none")

    print("\n== [P2] _require_watch_manager on a bare host vs alias readers ==")
    from module.composition_root import TrmdCompositionRoot  # noqa: E402
    host = object.__new__(TrmdCompositionRoot)  # skip __init__
    print("   before: has listen_download_chat :", hasattr(host, "listen_download_chat"))
    wm = host._require_watch_manager()
    print("   host.watch_manager is manager    :", host.watch_manager is wm)
    print("   after : has listen_download_chat :", hasattr(host, "listen_download_chat"))
    print("   manager.listen_download_chat len :", len(wm.listen_download_chat))
    print("   manager dict is host dict        :", getattr(host, "listen_download_chat", None) is wm.listen_download_chat)
    print("   -> WebOperationsMixin L1610 reads `self.listen_download_chat` directly:")
    try:
        host.listen_download_chat
        print("      OK")
    except AttributeError as e:
        print("      AttributeError:", e)


if __name__ == "__main__":
    sys.exit(main())
