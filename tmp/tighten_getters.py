# coding=UTF-8
"""把 composition_root 里"构造期必定已赋值"的 getter 改成直接属性访问。

判定依据（逐个人工核对过 __init__ 的赋值顺序）：
- 必定已赋值（在任何 getter 被调用之前）：app / gc / loop / pb / diagnostic
- 可能合法为 None（运行期才装配）：transfer_store / user / uploader /
  watch_manager / pikpak_manager / progress_tracker / web_task_manager /
  _api_credentials_event / web_ui_auth

因此只替换前一组：把 `getattr(self, "x", None)` 换成 `self.x`，
让"初始化顺序写错"从静默 None 变成显式 AttributeError。
"""
import pathlib

REPO = pathlib.Path(r"E:\codebase\tgbot")
P = REPO / "module" / "composition_root.py"
text = P.read_text(encoding="utf-8")

REPLACEMENTS = [
    ('    def _app(self):\n        return getattr(self, "app", None)\n',
     '    def _app(self):\n        # __init__ 保证 app 在任何协作者访问前已赋值；不兜底，顺序错了要立刻炸。\n        return self.app\n'),
    ('    def _gc(self):\n        return getattr(self, "gc", None)\n',
     '    def _gc(self):\n        return self.gc\n'),
    ('    def _loop(self):\n        return getattr(self, "loop", None)\n',
     '    def _loop(self):\n        return self.loop\n'),
    ('    def _pb(self):\n        return getattr(self, "pb", None)\n',
     '    def _pb(self):\n        return self.pb\n'),
]
for old, new in REPLACEMENTS:
    assert old in text, f"anchor missing: {old[:40]!r}"
    text = text.replace(old, new, 1)

P.write_text(text, encoding="utf-8")
print("updated:", len(REPLACEMENTS), "getters")
