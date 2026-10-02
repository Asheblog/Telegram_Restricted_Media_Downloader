# coding=UTF-8
"""对照：git 里的旧 assets.py 内联常量 vs 新构建产物，确认是否等价。"""
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

old_src = subprocess.run(
    ["git", "show", "HEAD:module/adapters/webui/assets.py"],
    cwd=str(REPO), capture_output=True, check=True,
).stdout.decode("utf-8")

# 提取旧内联常量
def extract(name: str) -> str:
    m = re.search(rf'{name} = r"""(.*?)"""', old_src, re.S)
    return m.group(1) if m else "<missing>"

old_desktop = extract("WEB_UI_HTML")
old_mobile = extract("WEB_UI_MOBILE_HTML")
old_login = extract("LOGIN_PAGE_HTML")

bundle = json.loads(
    (REPO / "module/adapters/webui/dist/webui/assets.json").read_text(encoding="utf-8")
)
new_desktop = bundle["web_ui_html"]
new_mobile = bundle["web_ui_mobile_html"]
new_login = bundle["login_page_html"]

for label, old, new in (
    ("desktop", old_desktop, new_desktop),
    ("mobile", old_mobile, new_mobile),
    ("login", old_login, new_login),
):
    same = old == new
    print(f"{label:8s} old={len(old):7d} new={len(new):7d} identical={same}")
    if not same:
        # 找第一个差异位置
        n = min(len(old), len(new))
        i = next((k for k in range(n) if old[k] != new[k]), n)
        print(f"          first diff at {i}")
        print(f"          old: {old[max(0,i-60):i+60]!r}")
        print(f"          new: {new[max(0,i-60):i+60]!r}")

# 旧 FONTS 字典条目数
fonts_old = re.findall(r'"([0-9a-f]+\.woff2)": "', old_src)
print("old FONTS entries:", len(fonts_old))
new_fonts = sorted(p.name for p in (REPO / "module/adapters/webui/dist/webui/fonts").iterdir())
print("new font files   :", len(new_fonts))
print("same names       :", sorted(fonts_old) == new_fonts)
