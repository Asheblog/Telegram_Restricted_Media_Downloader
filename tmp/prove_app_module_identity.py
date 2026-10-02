# coding=UTF-8
"""Identify which object `from module import app as app_module` actually binds,
and where the wrapper's '.unknown' sentinel comes from."""
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

import module as module_pkg  # noqa: E402
from module.core import app as core_app  # noqa: E402

print("=== what does the wrapper body actually bind? ===")
# Reproduce the wrapper body verbatim:
from module import app as app_module  # noqa: E402

print(f"  app_module                      = {app_module!r}")
print(f"  app_module.__name__             = {app_module.__name__}")
print(f"  app_module.__file__             = {getattr(app_module, '__file__', None)}")
print(f"  hasattr(app_module,'get_extension') = {hasattr(app_module, 'get_extension')}")
if hasattr(app_module, 'get_extension'):
    ge = app_module.get_extension
    print(f"    -> {ge!r}")
    print(f"    -> module={ge.__module__!r} file={sys.modules[ge.__module__].__file__ if ge.__module__ in sys.modules else '?'}")

print()
print("=== sys.modules identity check ===")
print(f"  sys.modules['module']            is module_pkg : {sys.modules['module'] is module_pkg}")
print(f"  sys.modules['module'].app        = {sys.modules['module'].app!r}")
print(f"  sys.modules['module.app']        = {sys.modules.get('module.app')!r}")

print()
print("=== compare the two get_extension implementations ===")
from module.utils.path_tool import get_extension as real_ge  # noqa: E402

print(f"  real (path_tool).get_extension('AQADenglishId','image/jpeg') = {real_ge('AQADenglishId','image/jpeg')!r}")
if hasattr(app_module, 'get_extension'):
    other = app_module.get_extension
    print(f"  shim/legacy get_extension(...)                              = {other('AQADenglishId','image/jpeg')!r}")
    import inspect
    try:
        print("  --- source ---")
        print(inspect.getsource(other))
    except Exception as exc:
        print(f"  (source unavailable: {exc})")

print()
print("=== who is the wrapper forwarding to, and does the test patch matter? ===")
import inspect  # noqa: E402

print(inspect.getsource(core_app.get_extension))
