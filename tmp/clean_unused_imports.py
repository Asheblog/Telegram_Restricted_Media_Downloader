# coding=UTF-8
"""按"名字在文件中只出现 1 次（仅 import 行）"判据清理未用导入。

比 AST 名字解析更保守：# 出现次数 > 1 即视为在用（含字符串/属性/装饰器）。
只处理 module/webops/operations.py。
"""
import ast
import pathlib
import re

REPO = pathlib.Path(r"E:\codebase\tgbot")
P = REPO / "module" / "webops" / "operations.py"
src = P.read_text(encoding="utf-8")
lines = src.splitlines(keepends=True)
tree = ast.parse(src)

# 收集导入位置
imports = []  # (lineno_1based, name, raw_line)
for n in tree.body:
    if isinstance(n, ast.Import):
        for a in n.names:
            imports.append((n.lineno, (a.asname or a.name).split(".")[0], a.name))
    elif isinstance(n, ast.ImportFrom):
        for a in n.names:
            imports.append((n.lineno, a.asname or a.name, a.name))

# 逐名字统计出现次数（词边界）
counts = {}
for _, local, _orig in imports:
    counts[local] = len(re.findall(rf"\b{re.escape(local)}\b", src))

to_remove = {local for local, c in counts.items() if c <= 1}
print("candidates (occurrences<=1):", len(to_remove))
for local in sorted(to_remove):
    print(f"   {local}")

# 从 import 行里剔除这些名字；整行只剩空括号时删行
new_lines = []
removed_total = 0
i = 0
while i < len(lines):
    line = lines[i]
    lineno = i + 1
    names_here = [local for (ln, local, _o) in imports if ln == lineno]
    if not names_here:
        new_lines.append(line)
        i += 1
        continue
    survivors = [n for n in names_here if n not in to_remove]
    removed_total += len(names_here) - len(survivors)
    if not survivors:
        # 整条 import 都无用：跳过该行（多行导入需一并跳过到右括号）
        stripped = line.rstrip()
        while stripped.count("(") > stripped.count(")") and i + 1 < len(lines):
            i += 1
            stripped = lines[i].rstrip()
        i += 1
        continue
    # 只删部分名字：从原文里删掉对应 token（含可能的逗号）
    text = line
    for name in names_here:
        if name in to_remove:
            text = re.sub(rf"\b{re.escape(name)}\b\s*,\s*", "", text, count=1)
            text = re.sub(rf",?\s*\b{re.escape(name)}\b", "", text, count=1)
    if re.search(r"import\s*\(\s*\)|import\s*$", text.strip()) or text.strip().endswith(","):
        text = text.rstrip().rstrip(",").rstrip() + "\n"
    new_lines.append(text)
    i += 1

P.write_text("".join(new_lines), encoding="utf-8")
print(f"removed {removed_total} import name(s); lines {len(lines)} -> {len(new_lines)}")

# 语法与名字自检
import subprocess
import sys

r = subprocess.run(
    [sys.executable, "-c", "import ast,pathlib; ast.parse(pathlib.Path(r'module/webops/operations.py').read_text(encoding='utf-8')); print('syntax OK')"],
    cwd=str(REPO), capture_output=True,
)
print(r.stdout.decode("utf-8", "replace").strip() or r.stderr.decode("utf-8", "replace").strip()[:300])
