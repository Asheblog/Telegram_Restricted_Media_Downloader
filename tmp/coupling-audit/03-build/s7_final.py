# coding=UTF-8
"""A3: 收尾量化 —— 生产代码对 shim 的真实依赖、测试对压缩产物的脆弱断言。"""
import re
from pathlib import Path

ROOT = Path(r"E:\codebase\tgbot")
MOD = ROOT / "module"
SKIP = {".git", ".venv", ".venv313", "node_modules", "__pycache__", ".ruff_cache",
        ".pytest_cache", "tmp", ".worktrees"}

shims = {p.stem: p for p in MOD.glob("*.py")
         if p.name != "__init__.py" and "Compatibility shim" in p.read_text(encoding="utf-8")}
real_top = {p.stem for p in MOD.glob("*.py") if p.name != "__init__.py"} - set(shims)
print(f"顶层 shim={len(shims)}  顶层真实模块={len(real_top)} -> {sorted(real_top)}")

print()
print("== 生产代码（module/ 子包 + main.py + scripts/）引用顶层 shim 的位置 ==")
rows = []
for p in ROOT.rglob("*.py"):
    if set(p.parts) & SKIP:
        continue
    rel = str(p.relative_to(ROOT))
    if rel.startswith("unit_tests") or rel.startswith("tests"):
        continue
    if p.parent == MOD:
        continue
    src = p.read_text(encoding="utf-8")
    for m in re.finditer(r"^\s*(?:from|import)\s+module\.(\w+)\b", src, re.M):
        if m.group(1) in shims:
            rows.append((rel, src[:m.start()].count(chr(10)) + 1, m.group(1)))
for r in rows:
    print(f"  {r[0]}:{r[1]}  module.{r[2]}")
print(f"  生产引用 shim 总数 = {len(rows)} 处")

print()
print("== 测试代码引用顶层 shim 的位置（按 shim 汇总）==")
from collections import Counter
c = Counter()
for p in (ROOT / "unit_tests").glob("*.py"):
    src = p.read_text(encoding="utf-8")
    for m in re.finditer(r"^\s*(?:from|import)\s+module\.(\w+)\b", src, re.M):
        if m.group(1) in shims:
            c[m.group(1)] += 1
print(f"  测试引用 shim 总数 = {sum(c.values())} 处, 覆盖 {len(c)} 个 shim")
for k, v in c.most_common():
    print(f"    module.{k:30s} x{v}")

print()
print("== shim 是否真的一行都不能删：只看生产（不含测试）==")
prod_used = {r[2] for r in rows}
dead = sorted(set(shims) - prod_used)
print(f"  生产代码完全没引用的 shim = {len(dead)}/{len(shims)}")
print(f"    {dead}")

print()
print("== web_ui_assets_case.py 断言对『压缩 CSS 产物细节』的耦合 ==")
t = (ROOT / "unit_tests/web_ui_assets_case.py").read_text(encoding="utf-8")
asserts = re.findall(r"self\.assert(?:Not)?In\(\s*(.*?)\s*,\s*(WEB_UI_HTML|WEB_UI_MOBILE_HTML|"
                     r"LOGIN_PAGE_HTML|combined)", t)
css_like = 0
minified = 0
for lit, _tgt in asserts:
    if lit.startswith(("'", '"')) and ("{" in lit or "}" in lit or ";" in lit):
        css_like += 1
        if re.search(r"[a-z-]+:[^ ,;)']+[;}]", lit) and " {" not in lit:
            minified += 1
print(f"  对 HTML 常量的 assertIn 数 = {len(asserts)}")
print(f"  其中断言串含 CSS 块/分号 = {css_like}")
print(f"  其中形似『压缩后 CSS』（选择器{...} 无空格） = {minified}")
for lit, tgt in asserts:
    if lit.startswith(("'", '"')) and "{" in lit and len(lit) < 90:
        print(f"    {lit[:86]}  ->  {tgt}")
