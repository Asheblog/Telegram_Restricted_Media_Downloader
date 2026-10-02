# coding=UTF-8
"""灵敏度验证：前端同步守门必须能抓到"源改了但 assets.py 没重生成"。

做法：把 build_desktop_html 的输入（tailwind_css）改一个字节再比对，
预期断言失败。不修改仓库任何文件。
"""
import importlib.util
import pathlib
import sys
import unittest

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))

from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from module.adapters.webui import assets  # noqa: E402
from unit_tests.frontend_assets_in_sync_case import FrontendAssetsInSyncCase  # noqa: E402

WEBUI = REPO / "module" / "adapters" / "webui"
spec = importlib.util.spec_from_file_location("_bf", WEBUI / "build_frontend.py")
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)

tailwind = (WEBUI / "dist" / "tailwind.min.css").read_text(encoding="utf-8")
fonts_css, _ = bf._load_font_data()

ok = bf.build_desktop_html(tailwind, fonts_css) == assets.WEB_UI_HTML
print(f"1) 未篡改时一致（守门应通过）            : {ok}")

drifted_css = tailwind + "\n/* drift */\n"
rebuilt = bf.build_desktop_html(drifted_css, fonts_css)
print(f"2) 源 CSS 加一行后仍与已提交常量相同？    : {rebuilt == assets.WEB_UI_HTML}")

case = FrontendAssetsInSyncCase("test_desktop_html_matches_sources")
case.builder = bf
case.tailwind_css = drifted_css
case.fonts_css = fonts_css
case.font_files = {}
try:
    case.test_desktop_html_matches_sources()
    print("3) 守门捕获漂移？                        : False  <-- 守门失效")
except AssertionError as exc:
    print("3) 守门捕获漂移？                        : True")
    print(f"   断言信息: {str(exc).splitlines()[0][:110]}")
