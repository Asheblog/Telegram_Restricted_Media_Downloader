# coding=UTF-8
"""Runtime verification of two suspected defects found during the coupling audit.

1) module.core.app.get_extension() calls `from module import app as app_module`
   then `app_module.get_extension` — but `module` never exports that name.
2) unit_tests/app_filename_case.py patches 'module.app.get_extension', which is a
   different object than the one the code path actually resolves.

Read-only: no writes, no server, no network.
"""
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

print("=== A. is the wrapper reachable and what does it resolve to? ===")
from module import app as module_app_attr  # noqa: E402
import module as module_pkg  # noqa: E402
from module.core import app as core_app  # noqa: E402

print(f"  `import module` -> module.app            = {module_app_attr!r}")
print(f"  hasattr(module_pkg, 'get_extension')     = {hasattr(module_pkg, 'get_extension')}")
print(f"  'get_extension' in module.__all__        = {'get_extension' in getattr(module_pkg, '__all__', [])}")
print(f"  module.core.app.get_extension is wrapper : {core_app.get_extension.__module__}.{core_app.get_extension.__qualname__}")
print(f"  module.app.get_extension (real, path_tool): {module_app_attr.get_extension.__module__}")

print()
print("=== B. call the wrapper ===")
try:
    out = core_app.get_extension("AQADenglishId", "image/jpeg")
    print(f"  get_extension(...) -> {out!r}   (no crash)")
except Exception as exc:
    print(f"  get_extension(...) -> {type(exc).__name__}: {exc}")
    print("  ^ the wrapper is broken: it reads a name the package does not export")

print()
print("=== C. is it reachable from a real code path? ===")
import inspect  # noqa: E402

for name in ("get_temp_filename", "get_temp_file_path", "get_final_file_path", "get_download_file_name"):
    fn = getattr(core_app.Application, name, None)
    if fn is None:
        continue
    src_uses = "get_extension(" in inspect.getsource(fn)
    print(f"  Application.{name:24s} calls get_extension: {src_uses}")

print()
print("=== D. what the test patches vs what the code calls ===")
from unittest.mock import patch  # noqa: E402

with patch("module.app.get_extension", return_value="PATCHED"):
    patched = module_app_attr.get_extension
    print(f"  patched target module.app.get_extension -> {patched!r}")
    print(f"  core_app.get_extension is the same object? {core_app.get_extension is patched}")
    try:
        got = core_app.get_extension("x", "y")
        print(f"  core_app.get_extension('x','y') -> {got!r}")
    except Exception as exc:
        print(f"  core_app.get_extension('x','y') -> {type(exc).__name__}: {exc}")

print()
print("=== E. Application.get_temp_filename end-to-end (uses the wrapper at core/app.py:330) ===")
app = core_app.Application.__new__(core_app.Application)
app.title_override = None
from types import SimpleNamespace  # noqa: E402

msg = SimpleNamespace(
    id=12,
    caption="title",
    chat=SimpleNamespace(id=-1007),
    photo=SimpleNamespace(file_id="fid", file_unique_id="AQADenglishId"),
)
try:
    print(f"  -> {app.get_temp_filename('photo', msg)!r}")
except Exception as exc:
    print(f"  -> {type(exc).__name__}: {exc}")
    import traceback  # noqa: E402

    tb = traceback.format_exc().strip().splitlines()
    for line in tb[-6:]:
        print(f"     {line}")
