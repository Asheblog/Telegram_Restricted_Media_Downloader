# coding=UTF-8
"""A3: 量化「改一行前端代码」的重建代价（纯内存，不写任何文件）。"""
import ast
import difflib
import importlib.util
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"E:\codebase\tgbot")
WEBUI = ROOT / "module" / "adapters" / "webui"

spec = importlib.util.spec_from_file_location("bf_readonly2", WEBUI / "build_frontend.py")
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)

TW = (WEBUI / "dist" / "tailwind.min.css").read_text(encoding="utf-8")
FONTS_CSS, FONT_FILES = bf._load_font_data()

src = (WEBUI / "assets.py").read_text(encoding="utf-8")
tree = ast.parse(src)
actual = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            actual[node.targets[0].id] = node.value.value

print("== tailwind.min.css 形态 ==")
print(f"  bytes={len(TW.encode('utf-8'))} lines={len(TW.splitlines())} "
      f"max_line={max(len(l) for l in TW.splitlines())} "
      f"newline_count={TW.count(chr(10))}")
src_tw = (WEBUI / "static" / "tailwind.css").read_text(encoding="utf-8")
print(f"  static/tailwind.css bytes={len(src_tw.encode('utf-8'))} lines={len(src_tw.splitlines())}")

print()
print("== 场景A: static/shared.js 改 1 个字符 ==")
shared = (WEBUI / "static" / "shared.js").read_text(encoding="utf-8")
d = bf.build_desktop_html(TW, FONTS_CSS)
m = bf.build_mobile_html(TW, FONTS_CSS)
shared_mut = shared.replace("function", "function ", 1)
orig_read = bf.read_text


def fake_read(p):
    if p.name == "shared.js":
        return shared_mut
    return orig_read(p)


bf.read_text = fake_read
d2 = bf.build_desktop_html(TW, FONTS_CSS)
m2 = bf.build_mobile_html(TW, FONTS_CSS)
bf.read_text = orig_read

for name, before, after in (("WEB_UI_HTML", d, d2), ("WEB_UI_MOBILE_HTML", m, m2)):
    dl = list(difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0))
    adds = sum(1 for l in dl if l.startswith("+") and not l.startswith("+++"))
    dels = sum(1 for l in dl if l.startswith("-") and not l.startswith("---"))
    hunk_ctx = sum(1 for l in dl if l.startswith("@@"))
    print(f"  {name}: asset_lines_changed=+{adds}/-{dels} hunks={hunk_ctx} "
          f"bytes_delta={len(after)-len(before)}")
print("  -> 同一个 shared.js 被 desktop 与 mobile 各内联一次，1 处 JS 改动 = 2 个常量区域")

print()
print("== 场景B: 新增 1 个 Tailwind 工具类（需重跑 tailwind CLI，dist/tailwind.min.css 变化）==")
# 模拟 tailwind 输出变化：在 min css 末尾追加一条新工具类
tw_mut = TW + "\n.new-utility-x{color:#123456}\n"
d3 = bf.build_desktop_html(tw_mut, FONTS_CSS)
m3 = bf.build_mobile_html(tw_mut, FONTS_CSS)
l3 = bf.build_login_page(tw_mut, FONTS_CSS)
total_delta = 0
for name, before, after in (("WEB_UI_HTML", d, d3), ("WEB_UI_MOBILE_HTML", m, m3),
                            ("LOGIN_PAGE_HTML", actual["LOGIN_PAGE_HTML"], l3)):
    dl = list(difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0))
    adds = sum(1 for l in dl if l.startswith("+") and not l.startswith("+++"))
    dels = sum(1 for l in dl if l.startswith("-") and not l.startswith("---"))
    total_delta += max(adds, dels) * 0
    print(f"  {name}: changed_lines=+{adds}/-{dels} bytes_delta={len(after)-len(before)}")
print(f"  -> tailwind CSS 被内联进全部 3 个常量；tailwind.min.css 是 "
      f"{len(TW.splitlines())} 行、单行最长 {max(len(l) for l in TW.splitlines())} 字符")

print()
print("== 场景C: 只改 desktop.js（仅 desktop 常量）==")
desktop = (WEBUI / "static" / "desktop.js").read_text(encoding="utf-8")


def fake_read2(p):
    if p.name == "desktop.js":
        return desktop.replace("function", "function ", 1)
    return orig_read(p)


bf.read_text = fake_read2
d4 = bf.build_desktop_html(TW, FONTS_CSS)
bf.read_text = orig_read
dl = list(difflib.unified_diff(d.splitlines(), d4.splitlines(), lineterm="", n=0))
print(f"  WEB_UI_HTML: changed_lines=+{sum(1 for l in dl if l.startswith('+') and not l.startswith('+++'))} "
      f"/-{sum(1 for l in dl if l.startswith('-') and not l.startswith('---'))}")

print()
print("== 生成物体量 ==")
gen = {
    "WEB_UI_HTML": d,
    "WEB_UI_MOBILE_HTML": m,
    "LOGIN_PAGE_HTML": bf.build_login_page(TW, FONTS_CSS),
}
b64 = sum(len(v) for v in FONT_FILES.values())
print(f"  单次重建输出 = {sum(len(v.encode('utf-8')) for v in gen.values()) + b64} bytes "
      f"(HTML {sum(len(v.encode('utf-8')) for v in gen.values())} + FONTS b64 {b64})")
print(f"  tailwind 3 份 = {3*len(TW.encode('utf-8'))} bytes "
      f"({3*len(TW.encode('utf-8'))/1203917*100:.1f}% of assets.py)")
print(f"  fonts.css 3 份 = {3*len(FONTS_CSS.encode('utf-8'))} bytes")
print(f"  fonts base64 1 份 = {b64} bytes ({b64/1203917*100:.1f}% of assets.py)")

print()
print("== 进程代价: 解析/导入 assets.py ==")
t0 = time.perf_counter()
code = compile(src, str(WEBUI / "assets.py"), "exec")
t1 = time.perf_counter()
ns = {}
exec(code, ns)
t2 = time.perf_counter()
print(f"  compile(1.2MB, 15679行) = {(t1-t0)*1000:.1f} ms ; exec = {(t2-t1)*1000:.1f} ms ; "
      f"total = {(t2-t0)*1000:.1f} ms")
try:
    import tracemalloc
    tracemalloc.start()
    exec(code, {})
    cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"  peak_python_heap_delta = {cur/1024/1024:.2f} MiB retained / {peak/1024/1024:.2f} MiB peak")
except Exception as e:  # pragma: no cover
    print("  tracemalloc failed:", e)
