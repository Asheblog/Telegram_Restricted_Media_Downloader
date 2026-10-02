# coding=UTF-8
"""最小改进建议的可运行实现：检测 templates/ static/ dist/ 与 assets.py 是否漂移。

用法（只读，不写任何文件）：
    .venv313\\Scripts\\python.exe tmp/coupling-audit/03-build/check_frontend_drift.py
退出码 0 = 同步；1 = 漂移（源文件改了但 assets.py 未重新生成）。
可直接放进 CI 或作为 pytest 用例。
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WEBUI = REPO / "module/adapters/webui"

spec = importlib.util.spec_from_file_location("_bf_check", WEBUI / "build_frontend.py")
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)  # 不调用 main()，因此不会写 assets.py

tailwind = (WEBUI / "dist/tailwind.min.css").read_text(encoding="utf-8")
fonts_css, font_files = bf._load_font_data()
expected = {
    "WEB_UI_HTML": bf.build_desktop_html(tailwind, fonts_css),
    "WEB_UI_MOBILE_HTML": bf.build_mobile_html(tailwind, fonts_css),
    "LOGIN_PAGE_HTML": bf.build_login_page(tailwind, fonts_css),
}

# 直接在源码里取常量，避免 import module 触发副作用
import ast

tree = ast.parse((WEBUI / "assets.py").read_text(encoding="utf-8"))
actual = {}
fonts = None
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name in expected and isinstance(node.value, ast.Constant):
            actual[name] = node.value.value
        elif name == "FONTS":
            fonts = {k.value: v.value for k, v in zip(node.value.keys, node.value.values)}

drift = []
for name, want in expected.items():
    if actual.get(name) != want:
        drift.append(f"{name}: assets.py {'缺失' if name not in actual else '与源文件不一致'}")
if fonts != font_files:
    drift.append(f"FONTS: assets.py={len(fonts or {})} 项 / static/fonts={len(font_files)} 项")

if drift:
    print("FRONTEND DRIFT DETECTED — 请重新运行 build_frontend.py：")
    for d in drift:
        print("  -", d)
    sys.exit(1)
print("FRONTEND IN SYNC — assets.py 与 templates/ static/ dist/ 逐字节一致")
sys.exit(0)
