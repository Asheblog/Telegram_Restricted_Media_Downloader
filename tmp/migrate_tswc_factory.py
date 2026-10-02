# coding=UTF-8
"""把 transfer_store_webui_case.py 的 object.__new__ 装配迁移到 build_downloader 工厂。

语义保持：
- `downloader.<attr> = <rhs>` 原样变成工厂的 `attr=<rhs>` 关键字，rhs 文本不变；
- **仅当**赋值语句是单行、且 rhs 括号/引号平衡时才替换（多行赋值会破坏语法，
  上一版就是这么炸的）；
- 只处理紧跟 `object.__new__(TelegramRestrictedMediaDownloader)` 之后、
  同一缩进层级的连续赋值块。
"""
import pathlib
import re

REPO = pathlib.Path(r"E:\codebase\tgbot")
P = REPO / "unit_tests" / "transfer_store_webui_case.py"
src = P.read_text(encoding="utf-8")
lines = src.splitlines(keepends=True)

NEW_PATTERNS = [
    re.compile(r"^(\s*)(\w+) = object\.__new__\(TelegramRestrictedMediaDownloader\)\s*$"),
    re.compile(
        r"^(\s*)(\w+) = TelegramRestrictedMediaDownloader\.__new__"
        r"\(TelegramRestrictedMediaDownloader\)\s*$"
    ),
]
ASSIGN = re.compile(r"^(\s*)(\w+)\.(\w+) = (.+?)\s*$")


def balanced(text: str) -> bool:
    """rhs 的单行括号/引号是否平衡（不平衡说明是跨行赋值的一部分）。"""
    depth = 0
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0 and quote is None


out = []
i = 0
converted = 0
skipped_multiline = 0
while i < len(lines):
    line = lines[i]
    m = next((p.match(line) for p in NEW_PATTERNS if p.match(line)), None)
    if not m:
        out.append(line)
        i += 1
        continue

    indent, var = m.group(1), m.group(2)
    block = []
    j = i + 1
    ok = True
    while j < len(lines):
        a = ASSIGN.match(lines[j])
        if not a or a.group(1) != indent or a.group(2) != var:
            break
        rhs = a.group(4)
        if not balanced(rhs):
            ok = False
            break
        block.append((a.group(3), rhs))
        j += 1

    if not block or not ok:
        if not ok:
            skipped_multiline += 1
        out.append(line)
        i += 1
        continue

    kwargs = ", ".join(f"{name}={rhs}" for name, rhs in block)
    out.append(f"{indent}{var} = build_downloader({kwargs})\n")
    converted += 1
    i = j

NEW_SRC = "".join(out)
if "downloader_factory import" not in NEW_SRC:
    anchor = "from unit_tests.pyrogram_stub import install_pyrogram_stub\n"
    assert anchor in NEW_SRC
    NEW_SRC = NEW_SRC.replace(
        anchor,
        anchor + "\nfrom unit_tests.support.downloader_factory import build_downloader\n",
        1,
    )

P.write_text(NEW_SRC, encoding="utf-8")
print(f"converted={converted} skipped_multiline={skipped_multiline}")
print(
    "remaining object.__new__(host):",
    len(re.findall(r"object\.__new__\(TelegramRestrictedMediaDownloader\)", NEW_SRC)),
)
