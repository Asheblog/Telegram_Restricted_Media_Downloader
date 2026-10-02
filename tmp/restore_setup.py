# coding=UTF-8
"""把 setup.py 移回 adapters/webui：它的异常类型是 HTTP handler 需要的契约。"""
import pathlib
import re

REPO = pathlib.Path(r"E:\codebase\tgbot")
WEBUI = REPO / "module" / "adapters" / "webui"
WEBOPS = REPO / "module" / "webops"

src = WEBOPS / "setup.py"
dst = WEBUI / "setup.py"
dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
src.unlink()
print("setup.py -> adapters/webui/")

pat = re.compile(r"module\.webops\.setup")
changed = []
for base in ("module", "unit_tests"):
    for path in (REPO / base).rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        new = pat.sub("module.adapters.webui.setup", text)
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
print("leftover webops.setup:", leftover or "none")
