# coding=UTF-8
"""临时把 ci/verify-rst 加入 ci.yml 触发分支（验证后回滚）。"""
import pathlib
import sys

path = pathlib.Path(r"E:\codebase\tgbot\.github\workflows\ci.yml")
text = path.read_text(encoding="utf-8")
OLD = "branches: ['main']"
NEW = "branches: ['main', 'ci/verify-rst']"
if sys.argv[1] == "add":
    if NEW in text:
        print("already added")
    else:
        assert OLD in text, "anchor not found"
        path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
        print("added")
else:
    assert NEW in text, "temp trigger not present"
    path.write_text(text.replace(NEW, OLD), encoding="utf-8")
    print("reverted")
