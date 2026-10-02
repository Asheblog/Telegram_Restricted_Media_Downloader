# coding=UTF-8
"""Runtime proof of the string-keyed dispatch chain + a live consistency audit.

Read-only: in-memory objects only, no HTTP server, no writes.
"""
import ast
import pathlib
import re
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.adapters.webui.operations import (  # noqa: E402
    WebOperationsFacade,
    _WEB_UI_DELEGATE_METHODS,
)
from module.adapters.webui.server import WebUiApiError, WebUiServer  # noqa: E402
from module.ports import IWebUiOperations  # noqa: E402

SRC = (REPO / "module/adapters/webui/server.py").read_text(encoding="utf-8")

print("=== 1. the facade surface is generated, not written ===")
body = SRC_ops = (REPO / "module/adapters/webui/operations.py").read_text(encoding="utf-8")
facade_body = SRC_ops.split("class WebOperationsFacade:")[1].split("def _bind_web_delegate")[0]
print(f"  _WEB_UI_DELEGATE_METHODS            : {len(_WEB_UI_DELEGATE_METHODS)} names")
print(f"  'def ' statements in facade body    : {facade_body.count('def ')} (__init__ only)")
print(f"  attached via setattr at import time : {sum(hasattr(WebOperationsFacade, m) for m in _WEB_UI_DELEGATE_METHODS)}")

print()
print("=== 2. Protocol coverage of the real surface ===")
proto = {m for m in dir(IWebUiOperations) if not m.startswith("_")}
surface = set(_WEB_UI_DELEGATE_METHODS)
print(f"  declared in IWebUiOperations        : {len(proto)}")
print(f"  real facade surface                 : {len(surface)}")
print(f"  implemented but NOT declared        : {len(surface - proto)}")
print(f"    {sorted(surface - proto)}")

print()
print("=== 3. LIVE CONSISTENCY AUDIT of every _operation(\"...\") call site ===")
names = re.findall(r"_operation\(\s*[\"']([^\"']+)[\"']\s*\)", SRC)
print(f"  call sites found in server.py       : {len(names)}")
missing = sorted({n for n in names if n not in surface})
print(f"  names with NO facade implementation : {len(missing)} {missing if missing else '(none)'}")
# also: does the host actually define them? check the mixin source
mixin_methods = set(re.findall(r"\n    (?:async )?def (\w+)\(", SRC_ops.split("class WebOperationsFacade:")[0]))
not_in_mixin = sorted({n for n in names if n not in mixin_methods})
print(f"  names absent from WebOperationsMixin: {len(not_in_mixin)} {not_in_mixin if not_in_mixin else '(none)'}")

print()
print("=== 4. a typo in a dispatch string is invisible until runtime ===")


class FakeHost:
    def __init__(self):
        self.called = []

    def __getattr__(self, name):
        def _recorder(*a, **kw):
            self.called.append(name)
            return {"ok": name}
        return _recorder


host = FakeHost()
facade = WebOperationsFacade(host)
print(f"  facade.create_upload(...)      -> {facade.create_upload({'x': 1})}  (host saw {host.called})")

server = WebUiServer(store=None, operations=facade)
good = server._operation("create_upload")
bad = server._operation("create_upload_typo")
print(f"  _operation('create_upload')    -> {type(good).__name__}")
print(f"  _operation('create_upload_typo')-> {bad}   <-- typo yields None, raises nothing")

print()
print("=== 5. what the HTTP layer tells the user about a wiring typo ===")
import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    try:
        server.create_upload({"path": tmp, "target_link": "https://t.me/x"})
    except WebUiApiError as exc:
        # facade delegates to FakeHost, so this path succeeds; force the typo case:
        pass
    server.operations = None  # same observable outcome as a typo: _operation -> None
    try:
        server.create_upload({"path": tmp, "target_link": "https://t.me/x"})
    except WebUiApiError as exc:
        print(f"  error_code={exc.error_code!r} status={exc.status} message={exc.message!r}")
        print("  -> indistinguishable from a naming mistake: 503 'operations unavailable'")

print()
print("=== 6. is any Protocol enforced anywhere at runtime? ===")
hits = 0
for p in (REPO / "module").rglob("*.py"):
    if "__pycache__" in p.parts:
        continue
    tree = ast.parse(p.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.args:
            if node.func.id in ("isinstance", "issubclass"):
                arg = node.args[1]
                nm = getattr(arg, "id", None) or getattr(arg, "attr", None) or ""
                if nm.startswith("I") and nm[1:2].isupper():
                    hits += 1
    del tree
print(f"  isinstance/issubclass against an I* Protocol in module/: {hits}")
print("  => Protocol classes are documentation; the host is never checked against them")
