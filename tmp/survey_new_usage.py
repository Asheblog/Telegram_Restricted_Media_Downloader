# coding=UTF-8
"""盘点剩余 object.__new__(host) 的形态：赋值块 vs 零散赋值。

分类：
- contiguous   : 紧随 __new__ 的同缩进连续赋值块（工厂可直接吃下）
- scattered    : 赋值散落在后续代码里（含 with/try 内、或中间有其它语句）
- none         : __new__ 之后没有紧跟赋值
"""
import ast
import pathlib
import re

REPO = pathlib.Path(r"E:\codebase\tgbot")
PAT = re.compile(r"object\.__new__\(TelegramRestrictedMediaDownloader\)")
ASSIGN = re.compile(r"^(\s*)(\w+)\.(\w+) = ")

rows = []
for path in sorted((REPO / "unit_tests").glob("*.py")):
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if not PAT.search(line):
            continue
        m = re.match(r"^(\s*)(\w+) = ", line)
        var = m.group(2) if m else "?"
        indent = m.group(1) if m else ""
        # 统计紧随其后的同缩进连续赋值
        k = i + 1
        run = 0
        while k < len(lines):
            a = ASSIGN.match(lines[k])
            if a and a.group(1) == indent and a.group(2) == var:
                run += 1
                k += 1
            else:
                break
        # 该函数内（粗略：往下 80 行内同缩进）还有多少该变量赋值
        tail = lines[i + 1 : i + 81]
        total_assigns = sum(
            1
            for t in tail
            if (a2 := ASSIGN.match(t)) and a2.group(1) == indent and a2.group(2) == var
        )
        kind = "none" if total_assigns == 0 else ("contiguous" if run == total_assigns else "scattered")
        rows.append((path.name, i + 1, kind, run, total_assigns))

from collections import Counter

print("total:", len(rows), Counter(r[2] for r in rows))
print()
for kind in ("contiguous", "scattered", "none"):
    print(f"=== {kind} ===")
    for name, lineno, k, run, total in rows:
        if k == kind:
            print(f"  {name}:{lineno}  contiguous={run} total={total}")
