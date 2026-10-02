"""对抗性抽查：独立复现 A3（03-build/evidence.md）的关键数字。只读。"""
from __future__ import annotations

import ast
import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MOD = os.path.join(ROOT, "module")

# --- module/ 总字节 与 assets 占比
total = 0
files = []
for dp, dn, fn in os.walk(MOD):
    dn[:] = [d for d in dn if d not in {"__pycache__", ".ruff_cache"}]
    for f in fn:
        if f.endswith(".py"):
            p = os.path.join(dp, f)
            files.append(p)
            total += os.path.getsize(p)
assets = os.path.join(MOD, "adapters", "webui", "assets.py")
asz = os.path.getsize(assets)
print(f"module/ .py 文件数      A3=145   我={len(files)}")
print(f"module/ .py 总字节      A3=2,909,765  我={total:,}")
print(f"assets.py 字节          A3=1,203,917  我={asz:,}")
print(f"占比                    A3=41.4%      我={asz/total*100:.1f}%")

src = open(assets, encoding="utf-8").read()
# 顶层常量
tree = ast.parse(src)
assigns = [n for n in tree.body if isinstance(n, ast.Assign)]
print(f"\nassets.py 顶层赋值常量数 A3=4  我={len(assigns)} -> {[ast.unparse(a.targets[0]) for a in assigns]}")
for a in assigns:
    name = ast.unparse(a.targets[0])
    v = a.value
    if isinstance(v, ast.Constant) and isinstance(v.value, str):
        print(f"   {name}: {len(v.value):,} 字符, {v.value.count(chr(10))+1:,} 行(str)")
    elif isinstance(v, ast.Dict):
        print(f"   {name}: dict, {len(v.keys)} 项, 源码段 {len(ast.get_source_segment(src, v) or ''):,} 字符")


def top_const(name):
    for a in assigns:
        if ast.unparse(a.targets[0]) == name:
            v = a.value
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                return v.value
            seg = ast.get_source_segment(src, v) or ""
            return seg
    return None


html = top_const("WEB_UI_HTML")
print(f"\nWEB_UI_HTML 字符数       A3=447,549  我={len(html):,}  行数={html.count(chr(10))+1:,} (A3 说 8,750 行)")

# tailwind.min.css / fonts.css 出现次数
tw = src.count("/*! tailwindcss")
print(f"\ntailwind 内联份数: 我数 '/*! tailwindcss' 出现 {tw} 次 (A3 说 3 份)")
tw_len = None
m = re.search(r"/\*! tailwindcss.*?(?=\*/)", src, re.S)
if m:
    print(f"   片段起点长度参考: {len(m.group(0)):,} 字符")
# 用 dist/tailwind.min.css 长度比对
dist = os.path.join(MOD, "adapters", "webui", "dist", "tailwind.min.css")
if os.path.exists(dist):
    dl = os.path.getsize(dist)
    print(f"   dist/tailwind.min.css = {dl:,} B  (A3 说单份 100,891 B)")
fonts_src = os.path.join(MOD, "adapters", "webui", "static", "fonts.css")
if not os.path.exists(fonts_src):
    cands = glob.glob(os.path.join(MOD, "adapters", "webui", "**", "fonts.css"), recursive=True)
    fonts_src = cands[0] if cands else None
if fonts_src:
    print(f"   {os.path.relpath(fonts_src, ROOT)} = {os.path.getsize(fonts_src):,} B (A3 说 9,234 B)")

# --- 顶层 shim / 真实现
top_py = sorted(f for f in os.listdir(MOD) if f.endswith(".py"))
shims = [f for f in top_py if "Compatibility shim" in open(os.path.join(MOD, f), encoding="utf-8").read()]
real = [f for f in top_py if f not in shims]
print(f"\n顶层 .py 总数 我={len(top_py)}")
print(f"shim(注释判据)  A3=39  我={len(shims)}")
print(f"真实现          A3=5   我={len(real)} -> {real}")
star = []
for f in shims:
    s = open(os.path.join(MOD, f), encoding="utf-8").read()
    if re.search(r"^from .* import \*", s, re.M):
        star.append(f)
print(f"shim 用 import *  A3=24/39  我={len(star)}/{len(shims)}")

allpy = []
for dp, dn, fn in os.walk(MOD):
    dn[:] = [d for d in dn if d not in {"__pycache__", ".ruff_cache"}]
    allpy += [os.path.join(dp, f) for f in fn if f.endswith(".py")]
has_all = [p for p in allpy if re.search(r"^__all__\s*=", open(p, encoding="utf-8").read(), re.M)]
print(f"定义 __all__ 的模块  A3=10/145  我={len(has_all)}/{len(allpy)}")

# --- shim 的引用
shim_names = {f[:-3] for f in shims}
prod_hits, test_hits = [], []
prod_dirs = [os.path.join(ROOT, "module"), os.path.join(ROOT, "main.py")]
for p in allpy + ([os.path.join(ROOT, "main.py")] if os.path.exists(os.path.join(ROOT, "main.py")) else []):
    rel = os.path.relpath(p, ROOT)
    if rel.startswith("module" + os.sep):
        # 只统计指向顶层 shim 的 import（排除 shim 文件自身）
        if os.path.dirname(p) == MOD:
            continue
    txt = open(p, encoding="utf-8").read()
    for i, line in enumerate(txt.splitlines(), 1):
        mm = re.match(r"\s*(?:from module\.([\w]+)|from module import ([\w, ]+))", line)
        if mm:
            names = [mm.group(1)] if mm.group(1) else [x.strip() for x in mm.group(2).split(",")]
            for n in names:
                if n in shim_names:
                    prod_hits.append((rel, i, n))
scr = glob.glob(os.path.join(ROOT, "scripts", "**", "*.py"), recursive=True)
for p in scr:
    txt = open(p, encoding="utf-8").read()
    for i, line in enumerate(txt.splitlines(), 1):
        mm = re.match(r"\s*(?:from module\.([\w]+)|from module import ([\w, ]+))", line)
        if mm:
            names = [mm.group(1)] if mm.group(1) else [x.strip() for x in mm.group(2).split(",")]
            for n in names:
                if n in shim_names:
                    prod_hits.append((os.path.relpath(p, ROOT), i, n))
print(f"\n生产代码(main.py/scripts/module 非顶层)引用 shim  A3=2 处  我={len(prod_hits)}")
for h in prod_hits:
    print("   ", h[0], h[1], "-> module." + h[2])

tests = glob.glob(os.path.join(ROOT, "unit_tests", "*.py"))
cov = set()
n = 0
for p in tests:
    txt = open(p, encoding="utf-8").read()
    for line in txt.splitlines():
        mm = re.match(r"\s*(?:from module\.([\w]+)|from module import ([\w, ]+))", line)
        if mm:
            names = [mm.group(1)] if mm.group(1) else [x.strip() for x in mm.group(2).split(",")]
            for x in names:
                if x in shim_names:
                    n += 1
                    cov.add(x)
print(f"测试引用 shim  A3=160 处/29 个  我={n} 处/{len(cov)} 个")

# --- F8 pyrogram stub
case_files = glob.glob(os.path.join(ROOT, "unit_tests", "*_case.py"))
stub = [p for p in case_files if "install_pyrogram_stub" in open(p, encoding="utf-8").read()]
print(f"\n用 pyrogram_stub 的测试文件  A3=60/66  我={len(stub)}/{len(case_files)}")
