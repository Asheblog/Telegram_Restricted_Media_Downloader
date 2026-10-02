# coding=UTF-8
"""A3: 双份真相检测 —— 只读调用 build_frontend 的纯函数，重建 HTML 并与 assets.py 常量逐字节比对。

不调用 build_frontend.main()（那会写 assets.py）。
"""
import difflib
import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(r"E:\codebase\tgbot")
WEBUI = ROOT / "module" / "adapters" / "webui"

spec = importlib.util.spec_from_file_location("bf_readonly", WEBUI / "build_frontend.py")
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)  # 只执行定义，不执行 main()

TW = (WEBUI / "dist" / "tailwind.min.css").read_text(encoding="utf-8")
FONTS_CSS, FONT_FILES = bf._load_font_data()

built = {
    "WEB_UI_HTML": bf.build_desktop_html(TW, FONTS_CSS),
    "WEB_UI_MOBILE_HTML": bf.build_mobile_html(TW, FONTS_CSS),
    "LOGIN_PAGE_HTML": bf.build_login_page(TW, FONTS_CSS),
}

# 读取 assets.py 的常量（不 import module 包，避免副作用）
import ast
src = (WEBUI / "assets.py").read_text(encoding="utf-8")
tree = ast.parse(src)
actual = {}
actual_fonts = None
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        n = node.targets[0].id
        if n in built and isinstance(node.value, ast.Constant):
            actual[n] = node.value.value
        if n == "FONTS":
            actual_fonts = {
                k.value: v.value for k, v in zip(node.value.keys, node.value.values)
            }

print(f"[source sizes] tailwind.min.css={len(TW)} fonts.css={len(FONTS_CSS)} "
      f"font_files={len(FONT_FILES)}")
print(f"[rebuilt] " + ", ".join(f"{k}={len(v.encode('utf-8'))}B" for k, v in built.items()))
print(f"[assets]  " + ", ".join(f"{k}={len(v.encode('utf-8'))}B" for k, v in actual.items()))
print()

stale = False
for name in built:
    if name not in actual:
        print(f"[MISSING] assets.py 无 {name}")
        stale = True
        continue
    a = hashlib.sha256(built[name].encode("utf-8")).hexdigest()[:16]
    b = hashlib.sha256(actual[name].encode("utf-8")).hexdigest()[:16]
    same = built[name] == actual[name]
    stale = stale or not same
    print(f"[compare] {name:22s} rebuilt_sha={a} assets_sha={b} IDENTICAL={same} "
          f"len_diff={len(built[name]) - len(actual[name])}")
    if not same:
        d = list(difflib.unified_diff(
            actual[name].splitlines(), built[name].splitlines(),
            fromfile="assets.py:" + name, tofile="REBUILT", lineterm="", n=1))
        print(f"          diff hunks lines={len(d)}; first 40:")
        for line in d[:40]:
            print("          " + line[:200])

print()
print(f"[fonts dict] assets_keys={len(actual_fonts)} source_files={len(FONT_FILES)} "
      f"keys_equal={set(actual_fonts or {}) == set(FONT_FILES)}")
if actual_fonts is not None:
    for k in sorted(set(actual_fonts) | set(FONT_FILES)):
        same = actual_fonts.get(k) == FONT_FILES.get(k)
        if not same:
            print(f"  FONT DIFF {k}: assets_chars={len(actual_fonts.get(k) or '')} "
                  f"file_chars={len(FONT_FILES.get(k) or '')}")
    print(f"  fonts_all_identical={all(actual_fonts.get(k) == FONT_FILES.get(k) for k in FONT_FILES)}")

print()
print(f"OVERALL_STALE={stale}")
