# coding=UTF-8
"""第二轮迁移：支持多行 rhs（按括号平衡续行收集成一个关键字实参）。

语义保持：rhs 原文不变（含换行与缩进），只是从 `var.attr = rhs` 变成 `attr=rhs`。
多行 rhs 放进关键字实参里需要缩进对齐，这里统一把续行缩进到关键字的列。
"""
import pathlib
import re

REPO = pathlib.Path(r"E:\codebase\tgbot")
P = REPO / "unit_tests" / "transfer_store_webui_case.py"
lines = P.read_text(encoding="utf-8").splitlines(keepends=True)

NEW_PATTERNS = [
    re.compile(r"^(\s*)(\w+) = object\.__new__\(TelegramRestrictedMediaDownloader\)\s*$"),
    re.compile(
        r"^(\s*)(\w+) = TelegramRestrictedMediaDownloader\.__new__"
        r"\(TelegramRestrictedMediaDownloader\)\s*$"
    ),
]
ASSIGN_START = re.compile(r"^(\s*)(\w+)\.(\w+) = (.*)$")


def depth_delta(text: str) -> int:
    """净括号深度（忽略字符串内的括号，简化处理：只认引号配对）。"""
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
        i += 1
    return depth


out = []
i = 0
converted = 0
while i < len(lines):
    line = lines[i]
    m = next((p.match(line) for p in NEW_PATTERNS if p.match(line)), None)
    if not m:
        out.append(line)
        i += 1
        continue

    indent, var = m.group(1), m.group(2)
    kwargs = []
    j = i + 1
    while j < len(lines):
        a = ASSIGN_START.match(lines[j])
        if not a or a.group(1) != indent or a.group(2) != var:
            break
        attr, first = a.group(3), a.group(4).rstrip("\n")
        body_lines = [first]
        depth = depth_delta(first)
        k = j + 1
        while depth > 0 and k < len(lines):
            body_lines.append(lines[k].rstrip("\n"))
            depth += depth_delta(lines[k])
            k += 1
        if depth != 0:
            # 收集不完整，保守放弃整次替换
            break
        if len(body_lines) == 1:
            kwargs.append(f"{attr}={body_lines[0]}")
        else:
            inner = ("\n" + " " * (len(indent) + 4)).join(
                [body_lines[0]] + [b.strip() for b in body_lines[1:]]
            )
            kwargs.append(f"{attr}={inner}")
        j = k

    if not kwargs:
        out.append(line)
        i += 1
        continue

    joined = ",\n".join(f"{indent}    {kw}" for kw in kwargs)
    out.append(f"{indent}{var} = build_downloader(\n{joined},\n{indent})\n")
    converted += 1
    i = j

NEW_SRC = "".join(out)
P.write_text(NEW_SRC, encoding="utf-8")
print(f"converted={converted}")
print(
    "remaining:",
    len(re.findall(r"object\.__new__\(TelegramRestrictedMediaDownloader\)", NEW_SRC)),
)
