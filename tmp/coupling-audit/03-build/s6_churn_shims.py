# coding=UTF-8
"""A3: git churn 量化 + shim star-import 泄漏 + 漂移检测能力核查（只读）。"""
import ast
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"E:\codebase\tgbot")
WEBUI = ROOT / "module/adapters/webui"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


print("== 1) assets.py 在近 200 次提交中的改动量占比 ==")
numstat = git("log", "-200", "--numstat", "--pretty=format:C")
tot_a = tot_d = 0
repo_a = repo_d = 0
file_tot = defaultdict(lambda: [0, 0])
for line in numstat.splitlines():
    parts = line.split("\t")
    if len(parts) != 3:
        continue
    a, d, f = parts
    if a == "-" or d == "-":
        continue
    a, d = int(a), int(d)
    repo_a += a
    repo_d += d
    if f == "module/adapters/webui/assets.py":
        tot_a += a
        tot_d += d
print(f"  近200次提交 全仓新增行={repo_a} 删除行={repo_d} (合计 {repo_a+repo_d})")
print(f"  assets.py 新增行={tot_a} 删除行={tot_d} (合计 {tot_a+tot_d})")
print(f"  assets.py 占全仓改动行比 = {(tot_a+tot_d)/(repo_a+repo_d)*100:.1f}%")

# 全仓 churn top10
numstat2 = git("log", "-200", "--numstat", "--pretty=format:C")
for line in numstat2.splitlines():
    parts = line.split("\t")
    if len(parts) != 3 or parts[0] == "-":
        continue
    file_tot[parts[2]][0] += int(parts[0])
    file_tot[parts[2]][1] += int(parts[1])
print("  近200次提交 churn top10 (文件: +新增/-删除):")
for f, (a, d) in sorted(file_tot.items(), key=lambda x: -(x[1][0] + x[1][1]))[:10]:
    print(f"    {a:>7d}/-{d:<7d} {f}")

print()
print("== 2) 单次前端源码改动对应的 assets.py diff 行数（近 12 次提交实测）==")
log = git("log", "-12", "--numstat", "--pretty=format:C|%h|%s", "--",
          "module/adapters/webui/assets.py")
cur = None
for line in log.splitlines():
    parts = line.split("\t")
    if len(parts) != 3:
        if line.startswith("C|"):
            cur = line[2:]
        continue
    a, d, f = parts
    tot = int(a) + int(d) if a != "-" else 0
    print(f"  {cur[:60]:60s} assets.py +{a}/-{d} = {tot} 行")
    cur = None

print()
print("== 3) web_ui_assets_case.py 是否引用前端源文件（能否检出漂移）==")
t = (ROOT / "unit_tests/web_ui_assets_case.py").read_text(encoding="utf-8")
for pat in ["static/", "static\\\\", "templates/", "desktop.js", "shared.js",
            "mobile_script.js", "views.html", "mobile_body.html", "base.html",
            "login.html", "build_frontend", "tailwind.css", "dist/"]:
    n = t.count(pat)
    print(f"  '{pat}': {n} 次")
print(f"  assertIn/assertNotIn 次数 = {len(re.findall(r'assert(?:Not)?In', t))}")
print(f"  测试方法数 = {len(re.findall(r'    def test_', t))}")
print("  导入行:")
for line in t.splitlines()[:14]:
    if line.strip():
        print("    " + line[:110])

print()
print("== 4) shim `from X import *` 名称泄漏 ==")
MOD = ROOT / "module"
shim_files = [p for p in MOD.glob("*.py") if p.name != "__init__.py"
              and "Compatibility shim" in p.read_text(encoding="utf-8")]
print(f"  带 'Compatibility shim' 标记的 shim = {len(shim_files)}")
star = 0
leak_report = []
for p in sorted(shim_files):
    src = p.read_text(encoding="utf-8")
    if "import *" not in src:
        continue
    star += 1
    explicit = set()
    for m in re.finditer(r"^from [\w\.]+ import (.+)$", src, re.M):
        if "*" in m.group(1):
            continue
        explicit |= {x.strip().split(" as ")[0] for x in m.group(1).split(",")}
    mods = re.findall(r"^import ([\w\.]+)$", src, re.M)
    targets = re.findall(r"^from ([\w\.]+) import \*", src, re.M)
    tgt_all = []
    for tm in targets:
        tp = ROOT / (tm.replace(".", "/") + ".py")
        if tp.exists():
            try:
                tt = ast.parse(tp.read_text(encoding="utf-8"))
                has_all = any(isinstance(n, ast.Assign) and
                              any(getattr(x, "id", None) == "__all__" for x in n.targets)
                              for n in tt.body)
                tgt_all.append(f"{tm}(__all__={'yes' if has_all else 'NO'})")
            except SyntaxError:
                tgt_all.append(f"{tm}(parse-error)")
        else:
            tgt_all.append(f"{tm}(pkg)")
    extra = ", ".join(f"module.{m}" for m in mods) or "-"
    leak_report.append((p.name, explicit, extra, "; ".join(tgt_all)))
print(f"  使用 `import *` 的 shim = {star}/{len(shim_files)}")
print("  没有 __all__ 的 shim（star 会把被导入模块的 import 也一起再导出）:")
for name, explicit, extra, tgts in leak_report:
    if "NO" in tgts or extra != "-":
        print(f"    {name:30s} 显式别名={sorted(explicit)} 额外顶层 import=[{extra}]")
        print(f"      {'':30s} star 目标: {tgts}")

print()
print("== 5) 真实模块是否定义 __all__ ==")
for p in sorted(MOD.rglob("*.py")):
    if "__pycache__" in p.parts:
        continue
    src = p.read_text(encoding="utf-8")
    if "__all__" in src:
        pass
n_all = sum(1 for p in MOD.rglob("*.py") if "__pycache__" not in p.parts
            and "__all__" in p.read_text(encoding="utf-8"))
n_tot = sum(1 for p in MOD.rglob("*.py") if "__pycache__" not in p.parts)
print(f"  module/ 下定义 __all__ 的文件 = {n_all} / {n_tot}")
