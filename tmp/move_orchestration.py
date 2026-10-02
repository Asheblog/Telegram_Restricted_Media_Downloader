# coding=UTF-8
"""把 task_manager / setup / statistics_payload 从 adapters/webui 搬到 webops。"""
import pathlib
import re

REPO = pathlib.Path(r"E:\codebase\tgbot")
WEBUI = REPO / "module" / "adapters" / "webui"
WEBOPS = REPO / "module" / "webops"

MOVES = ["task_manager.py", "setup.py", "statistics_payload.py"]
OLD_PREFIX = "module.adapters.webui."
NEW_PREFIX = "module.webops."

# 1) 搬文件（文件内对同批模块的引用一并改）
for name in MOVES:
    src = WEBUI / name
    dst = WEBOPS / name
    text = src.read_text(encoding="utf-8")
    for m in MOVES:
        text = text.replace(
            f"{OLD_PREFIX}{m[:-3]}", f"{NEW_PREFIX}{m[:-3]}"
        )
    dst.write_text(text, encoding="utf-8")
    src.unlink()
    print("moved", name)

# 2) 全仓更新引用（module + unit_tests）
stems = [m[:-3] for m in MOVES]
pat = re.compile(
    r"module\.adapters\.webui\.(" + "|".join(stems) + r")"
)
changed = []
for base in ("module", "unit_tests"):
    for path in (REPO / base).rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        new = pat.sub(lambda m: f"module.webops.{m.group(1)}", text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(str(path.relative_to(REPO)))

print(f"refs updated in {len(changed)} files")
for c in changed:
    print("  ", c)

# 3) 残留检查
leftover = []
for base in ("module", "unit_tests"):
    for path in (REPO / base).rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if pat.search(path.read_text(encoding="utf-8")):
            leftover.append(str(path.relative_to(REPO)))
print("leftover:", leftover or "none")
