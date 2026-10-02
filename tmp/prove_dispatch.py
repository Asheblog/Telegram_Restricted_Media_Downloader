# coding=UTF-8
"""Runtime check: does the string-keyed dispatch chain really work, and what
does a typo look like from the outside?

Read-only: builds objects in memory, starts no HTTP server, writes nothing.
"""
import sys
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.adapters.webui.operations import (  # noqa: E402
    WebOperationsFacade,
    _WEB_UI_DELEGATE_METHODS,
)
from module.adapters.webui.server import WebUiApiError, WebUiServer  # noqa: E402

print("=== 1. facade surface is generated, not written ===")
src = (REPO / "module/adapters/webui/operations.py").read_text(encoding="utf-8")
print(f"  _WEB_UI_DELEGATE_METHODS length          : {len(_WEB_UI_DELEGATE_METHODS)}")
body = src.split("class WebOperationsFacade:")[1].split("def _bind_web_delegate")[0]
print(f"  explicit 'def ' inside facade class body : {body.count('def ')}  (only __init__)")
defined = [m for m in _WEB_UI_DELEGATE_METHODS if hasattr(WebOperationsFacade, m)]
print(f"  methods actually attached via setattr    : {len(defined)}/{len(_WEB_UI_DELEGATE_METHODS)}")

print()
print("=== 2. protocol coverage vs real surface ===")
from module.ports import IWebUiOperations  # noqa: E402

proto = [m for m in dir(IWebUiOperations) if not m.startswith("_")]
surface = set(_WEB_UI_DELEGATE_METHODS)
covered = sorted(set(proto) & surface)
print(f"  Protocol declared members                : {len(proto)}")
print(f"  facade real surface                      : {len(surface)}")
print(f"  declared AND implemented                 : {len(covered)}")
print(f"  implemented but NOT declared             : {len(surface - set(proto))}")
print(f"    -> {sorted(surface - set(proto))}")

print()
print("=== 3. a typo in a dispatch string is invisible until runtime ===")


class FakeHost:
    """Stands in for the God host; only the surface the facade touches."""

    def __init__(self):
        self.called = []

    def __getattr__(self, name):
        def _recorder(*a, **kw):
            self.called.append(name)
            return {"ok": name}
        return _recorder


host = FakeHost()
facade = WebOperationsFacade(host)
result = facade.create_upload({"x": 1})
print(f"  facade.create_upload(...)                -> {result}")
print(f"  host method actually invoked             : {host.called}")

server = WebUiServer(store=None, operations=facade)
print(f"  server._operation('create_upload')       -> {server._operation('create_upload')}")
print(f"  server._operation('create_uploadX')      -> {server._operation('create_uploadX')}  (typo -> None, no error)")

print()
print("=== 4. what the HTTP layer reports for a wiring typo ===")
try:
    server.create_upload({"path": "/tmp/x", "target_link": "https://t.me/x"})
except WebUiApiError as exc:
    print(f"  raises WebUiApiError code={exc.code!r} status={exc.status}")
    print(f"  message={exc.message!r}")
    print("  -> the caller is told 'operations unavailable' (503), not 'misconfigured'")

print()
print("=== 5. protocol enforcement: is anything checked anywhere? ===")
import ast  # noqa: E402

hits = 0
for p in (REPO / "module").rglob("*.py"):
    if "__pycache__" in p.parts:
        continue
    tree = ast.parse(p.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("isinstance", "issubclass") and node.args:
                arg = node.args[1]
                name = getattr(arg, "id", None) or getattr(arg, "attr", None) or ""
                if name.startswith("I") and name[1:2].isupper():
                    hits += 1
print(f"  isinstance/issubclass against an I* Protocol across module/: {hits}")
print("  => the Protocol classes are documentation only; nothing verifies the host")
