# coding=UTF-8
"""A3: assets.py 量化统计（只读）。"""
import ast
import base64
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"E:\codebase\tgbot")
WEBUI = ROOT / "module" / "adapters" / "webui"
ASSETS = WEBUI / "assets.py"

raw = ASSETS.read_bytes()
text = raw.decode("utf-8")
lines = text.splitlines()
print(f"[assets.py] bytes={len(raw)} lines={len(lines)} chars={len(text)}")

# 顶层常量
tree = ast.parse(text)
consts = []
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        val = node.value
        if isinstance(val, ast.Constant) and isinstance(val.value, str):
            consts.append((name, len(val.value.encode("utf-8")), val.lineno, val.end_lineno, val.value))
        elif isinstance(val, ast.Dict):
            consts.append((name, -1, val.lineno, val.end_lineno, val))
print(f"[assets.py] top-level names={len(tree.body)} string/dict consts={len(consts)}")
for name, size, l0, l1, _v in sorted(consts, key=lambda x: -(x[1] if x[1] >= 0 else 0)):
    print(f"  CONST {name:24s} bytes={size:>10d} lines={l0}-{l1} span={l1-l0+1}")

# FONTS 字典
for name, size, l0, l1, v in consts:
    if isinstance(v, ast.Dict):
        print(f"[FONTS] entries={len(v.keys)} dict_lines={l1-l0+1}")
        tot = 0
        biggest = None
        for k, val in zip(v.keys, v.values):
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                b = len(val.value)
                tot += b
                if biggest is None or b > biggest[1]:
                    biggest = (k.value, b)
        print(f"[FONTS] total_b64_chars={tot} decoded_bytes={tot*3//4} biggest={biggest}")

# 内联 base64 检测（字符串里出现长 base64 串）
b64_re = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")
for name, size, l0, l1, v in consts:
    if isinstance(v, str) and v:
        hits = b64_re.findall(v)
        if hits:
            print(f"[b64] {name}: {len(hits)} candidate base64 runs, max_run={max(len(h) for h in hits)}")

# data: URI 检测
for name, size, l0, l1, v in consts:
    if isinstance(v, str) and "data:" in v:
        m = re.findall(r"data:[a-zA-Z0-9/+.\-;=]{0,60}", v)
        print(f"[data-uri] {name}: {len(m)} occurrences, sample={Counter(m).most_common(5)}")

# 重复资源块检测：对每个常量做滑动行窗口 40 行的 sha1，找重复
print("[dup] 40-line window duplication per const (sha1):")
for name, size, l0, l1, v in consts:
    if not isinstance(v, str) or len(v) < 5000:
        continue
    vl = v.splitlines()
    W = 40
    seen = {}
    dups = []
    for i in range(0, max(0, len(vl) - W)):
        h = hashlib.sha1("\n".join(vl[i:i + W]).encode("utf-8")).hexdigest()
        if h in seen:
            dups.append((seen[h], i))
        else:
            seen[h] = i
    uniq = len(seen)
    print(f"  {name}: inner_lines={len(vl)} windows={max(0,len(vl)-W)} unique={uniq} dup_windows={len(dups)}")
    for a, b in dups[:5]:
        print(f"    dup: inner_line {a} == {b}")

# 生成链路里 r\"\"\" 的安全性：内容中是否含三引号
for name, size, l0, l1, v in consts:
    if isinstance(v, str):
        if '"""' in v:
            print(f"[UNSAFE] {name} contains triple-quote")
        if v.endswith("\\"):
            print(f"[UNSAFE] {name} ends with backslash")

# 关键字/文件构成提示
for name, size, l0, l1, v in consts:
    if isinstance(v, str) and len(v) > 1000:
        has_script = v.count("<script")
        has_style = v.count("<style")
        has_div = v.count("<div")
        print(f"[shape] {name}: <script>={has_script} <style>={has_style} <div>={has_div} lines={len(v.splitlines())}")
