# coding=UTF-8
"""把归档工具类从 adapters/webui 搬到 webops（编排层），并更新引用。

- archive_author_ops.py      -> webops/archive_author_ops.py
- archive_author_jobs.py     -> webops/archive_author_jobs.py
- system_log_archive_retry_ops.py -> webops/system_log_archive_retry_ops.py
"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
WEBUI = REPO / "module" / "adapters" / "webui"
WEBOPS = REPO / "module" / "webops"

MOVES = [
    "archive_author_ops.py",
    "archive_author_jobs.py",
    "system_log_archive_retry_ops.py",
]

for name in MOVES:
    src = WEBUI / name
    dst = WEBOPS / name
    text = src.read_text(encoding="utf-8")
    # 文件内部对同批模块的引用改到新路径
    text = text.replace(
        "module.adapters.webui.archive_author_jobs", "module.webops.archive_author_jobs"
    )
    text = text.replace(
        "module.adapters.webui.archive_author_ops", "module.webops.archive_author_ops"
    )
    text = text.replace(
        "module.adapters.webui.system_log_archive_retry_ops",
        "module.webops.system_log_archive_retry_ops",
    )
    dst.write_text(text, encoding="utf-8")
    src.unlink()
    print(f"moved {name} -> webops/")

# 更新引用者
REF_FILES = [
    REPO / "module" / "webops" / "operations.py",
    REPO / "module" / "archive_author_jobs.py",
    REPO / "module" / "archive_author_tool.py",
    REPO / "module" / "archive_reorganize.py",
]
for path in REF_FILES:
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    before = text
    for name in MOVES:
        text = text.replace(
            f"module.adapters.webui.{name[:-3]}", f"module.webops.{name[:-3]}"
        )
    if text != before:
        path.write_text(text, encoding="utf-8")
        print("updated refs:", path.relative_to(REPO))

# 全仓（module 与 unit_tests）扫一遍剩余引用
import re  # noqa: E402

pattern = re.compile(r"module\.adapters\.webui\.(archive_author_ops|archive_author_jobs|system_log_archive_retry_ops)")
leftover = []
for path in list((REPO / "module").rglob("*.py")) + list((REPO / "unit_tests").rglob("*.py")):
    if "__pycache__" in path.parts:
        continue
    text = path.read_text(encoding="utf-8")
    if pattern.search(text):
        leftover.append(str(path.relative_to(REPO)))
print("leftover refs:", leftover or "none")
