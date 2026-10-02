# coding=UTF-8
"""生成聚焦版审查 diff：去掉纯删除块，只保留新增/修改行与文件名清单。

纯删除噪声（assets.py 的 15,700 行内联常量）会把审查上下文淹没，
但"删了什么"仍需可见，因此额外输出一份被删文件/块的行数清单。
"""
import pathlib
import re
import subprocess

REPO = pathlib.Path(r"E:\codebase\tgbot")


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=str(REPO), capture_output=True, check=True
    ).stdout.decode("utf-8", "replace")


full = git("diff", "origin/main...HEAD")
out_lines = []
deleted_summary = []
cur_file = None
deleted_in_file = 0
added_in_file = 0

for line in full.splitlines():
    if line.startswith("diff --git "):
        if cur_file and deleted_in_file >= 50:
            deleted_summary.append((cur_file, deleted_in_file, added_in_file))
        m = re.match(r"diff --git a/(\S+) b/(\S+)", line)
        cur_file = m.group(2) if m else "?"
        deleted_in_file = added_in_file = 0
        out_lines.append(line)
        continue
    if line.startswith(("index ", "--- ", "+++ ")):
        out_lines.append(line)
        continue
    if line.startswith("@@"):
        out_lines.append(line)
        continue
    if line.startswith("+"):
        added_in_file += 1
        out_lines.append(line)
    elif line.startswith("-"):
        deleted_in_file += 1
        # 纯删除行不进聚焦版
    else:
        out_lines.append(line)

if cur_file and deleted_in_file >= 50:
    deleted_summary.append((cur_file, deleted_in_file, added_in_file))

(REPO / "tmp" / "review_focus.diff").write_text("\n".join(out_lines), encoding="utf-8")

summary = ["# 大块删除清单（聚焦版 diff 中已省略其删除行）", ""]
for name, deleted, added in sorted(deleted_summary, key=lambda r: -r[1]):
    summary.append(f"- {name}: -{deleted} 行 / +{added} 行")
(REPO / "tmp" / "review_deletions.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

print("focus diff lines:", len(out_lines))
print("big deletions:", len(deleted_summary))
for row in deleted_summary[:10]:
    print("   ", row)
