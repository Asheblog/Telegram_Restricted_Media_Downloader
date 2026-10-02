# coding=UTF-8
"""把 statistics_payload 移回 adapters/webui（它是 WebUI 数据契约，不是编排）。"""
import pathlib
import re

REPO = pathlib.Path(r"E:\codebase\tgbot")
WEBUI = REPO / "module" / "adapters" / "webui"
WEBOPS = REPO / "module" / "webops"

src = WEBOPS / "statistics_payload.py"
dst = WEBUI / "statistics_payload.py"
dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
src.unlink()
print("statistics_payload.py -> adapters/webui/")

pat = re.compile(r"module\.webops\.statistics_payload")
changed = []
for base in ("module", "unit_tests"):
    for path in (REPO / base).rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        new = pat.sub("module.adapters.webui.statistics_payload", text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(str(path.relative_to(REPO)))
print("refs restored:", changed)

leftover = []
for base in ("module", "unit_tests"):
    for path in (REPO / base).rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if pat.search(path.read_text(encoding="utf-8")):
            leftover.append(str(path.relative_to(REPO)))
print("leftover webops.statistics_payload:", leftover or "none")
