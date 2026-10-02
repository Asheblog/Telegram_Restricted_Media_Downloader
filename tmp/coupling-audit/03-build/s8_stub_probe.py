# coding=UTF-8
"""A3: pyrogram_stub 作用与宽松度实测。"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"E:\codebase\tgbot")))
from unit_tests.pyrogram_stub import install_pyrogram_stub

src = Path(r"E:\codebase\tgbot\unit_tests\pyrogram_stub.py").read_text(encoding="utf-8")

result = install_pyrogram_stub()
import pyrogram  # 被桩替换后的假包

print(f"install_pyrogram_stub() 返回 = {result}")
print(f"pyrogram.__file__ = {getattr(pyrogram, '__file__', None)}")
print(f"pyrogram.__version__ = {pyrogram.__version__}")
print(f"pyrogram.__path__ = {getattr(pyrogram, '__path__', None)}")
print()
print("--- 桩的宽松面在『模块属性』而不是『实例方法』 ---")
client = pyrogram.Client("x", "y")
try:
    client.this_method_does_not_exist_in_real_pyrogram()
    print("  实例方法属性：静默通过")
except AttributeError as e:
    print(f"  实例方法属性：AttributeError -> {e} (严格, 好)")
missing = pyrogram.types.SomeTypeThatDoesNotExistInRealPyrogram
print(f"  pyrogram.types.SomeTypeThatDoesNotExistInRealPyrogram -> {missing!r}")
print("  ^ 真实 pyrogram 会 ImportError/AttributeError；桩动态造类 -> 假阴性")
from pyrogram.enums import SomeEnumThatDoesNotExistEither
print(f"  from pyrogram.enums import SomeEnumThatDoesNotExistEither -> {SomeEnumThatDoesNotExistEither!r}")
print("  ^ 同上：模块级符号名写错，测试不会红")
print()
print("--- 桩的内部不一致：sys.modules 里有、父模块属性上没有 ---")
try:
    pyrogram.enums.ParseMode
    print("  pyrogram.enums.ParseMode -> OK（属性链可用）")
except AttributeError as e:
    print(f"  pyrogram.enums.ParseMode -> AttributeError: {e}")
    print("  但 from pyrogram.enums import ParseMode 可用（见上）")
for attr in ("types", "enums", "errors", "raw", "utils", "file_id", "handlers",
             "session", "crypto", "qrlogin"):
    has_attr = hasattr(pyrogram, attr)
    in_sys = f"pyrogram.{attr}" in sys.modules
    print(f"    pyrogram.{attr:10s} 属性={'yes' if has_attr else 'NO ':3s} "
          f"sys.modules={'yes' if in_sys else 'no'}")
print()
print("--- 桩显式建模的 API 名称 ---")
names = set(re.findall(r"^[ ]{0,8}(?:[\w\.]+\.)?([A-Za-z_][A-Za-z0-9_]*) = ", src, re.M))
names |= set(re.findall(r"setattr\([^,]+,\s*'([A-Za-z_][A-Za-z0-9_]*)'", src))
names |= set(re.findall(r"'([A-Z][A-Za-z0-9_]+)'", src))
names = {n for n in names if n not in {"UTF-8"}}
print(f"  显式建模名称数 = {len(names)}")
print(f"  pyrogram_stub.py 行数 = {len(src.splitlines())} / "
      f"{Path(r'E:\codebase\tgbot\unit_tests\pyrogram_stub.py').stat().st_size} B")
print(f"  DummyModule 实例 = {src.count('DummyModule(')}")
print(f"  type(...) 动态类构造 = {src.count('type(')}")
print()
print("--- 短路行为 ---")
print(f"  已 import pyrogram 后再调一次 -> 返回 {install_pyrogram_stub()} (sys.modules 命中即 return, L75-76)")
