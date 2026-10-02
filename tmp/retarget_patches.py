# coding=UTF-8
"""把测试里的 patch 目标从 adapters.webui.operations 改到 webops.operations。

实现已搬到编排层；patch 必须打在实现模块的命名空间上，打在 shim 上不会生效。
"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
OLD = "module.adapters.webui.operations."
NEW = "module.webops.operations."

changed = []
for path in sorted(REPO.rglob("unit_tests/*.py")):
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        continue
    count = text.count(OLD)
    path.write_text(text.replace(OLD, NEW), encoding="utf-8")
    changed.append((path.name, count))

for name, count in changed:
    print(f"{name}: {count} 处")
print("合计文件:", len(changed))
