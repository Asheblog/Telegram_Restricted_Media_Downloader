#!/usr/bin/env python3
"""Build frontend runtime assets into dist/webui/.

Reads HTML/JS/CSS from templates/ and static/, assembles the final documents, and
writes `dist/webui/assets.json` plus `dist/webui/fonts/*`.

产物是**运行时**资源，不再写入 Python 源：历史做法把 3 份完整 HTML（含内联
CSS/JS 与 base64 字体）写进 assets.py，得到 1.2 MB / 约 15,700 行的提交物，
占 module/ 全部 Python 字节 41%，且是全仓 churn 第一名（近 200 次提交改动 141 次）。
现在 templates/ + static/ 是唯一真源，构建只产出部署产物；
`module/adapters/webui/static_assets.py` 负责运行时读取，源码在时还会内存重建，
因此改完模板不跑构建也能立刻看到效果。

All styles live in tailwind.css (@theme + @layer components); there is no
separate mobile.css — mobile components come from the same Tailwind build.
"""

import base64
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST_DIR = HERE / "dist"
TEMPLATES_DIR = HERE / "templates"
STATIC_DIR = HERE / "static"
OUTPUT_DIR = DIST_DIR / "webui"
OUTPUT_FILE = OUTPUT_DIR / "assets.json"
OUTPUT_FONTS_DIR = OUTPUT_DIR / "fonts"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_font_data() -> tuple[str, dict[str, str]]:
    """Return (fonts_css, {filename: base64_data}) or ("", {}) if no fonts."""
    fonts_css_path = STATIC_DIR / "fonts.css"
    fonts_dir = STATIC_DIR / "fonts"
    if not fonts_css_path.exists():
        return "", {}

    fonts_css = read_text(fonts_css_path)
    font_files: dict[str, str] = {}
    for f in sorted(fonts_dir.iterdir()) if fonts_dir.is_dir() else []:
        if f.suffix in (".woff2", ".woff", ".ttf"):
            font_files[f.name] = base64.b64encode(f.read_bytes()).decode("ascii")
    return fonts_css, font_files


def _inject_css(html: str, fonts_css: str, tailwind_css: str) -> str:
    """Replace CSS placeholders with actual content."""
    html = html.replace("/* fonts.css */", fonts_css)
    html = html.replace("/* tailwind.min.css */", tailwind_css)
    return html


def build_login_page(tailwind_css: str, fonts_css: str) -> str:
    html = read_text(TEMPLATES_DIR / "login.html")
    return _inject_css(html, fonts_css, tailwind_css)


def build_desktop_html(tailwind_css: str, fonts_css: str) -> str:
    base = read_text(TEMPLATES_DIR / "base.html")
    views = read_text(TEMPLATES_DIR / "views.html")
    helpers_js = read_text(STATIC_DIR / "watch_ui_helpers.js")
    shared_js = read_text(STATIC_DIR / "shared.js")
    desktop_js = read_text(STATIC_DIR / "desktop.js")

    html = _inject_css(base, fonts_css, tailwind_css)
    html = html.replace("<!-- VIEWS PLACEHOLDER -->", views)
    html = html.replace("/* shared.js */", helpers_js + "\n" + shared_js)
    html = html.replace("/* desktop.js */", desktop_js)
    return html


def build_mobile_html(tailwind_css: str, fonts_css: str) -> str:
    """Build mobile HTML — single Tailwind build for all platforms."""
    mobile_body = read_text(TEMPLATES_DIR / "mobile_body.html")
    helpers_js = read_text(STATIC_DIR / "watch_ui_helpers.js")
    shared_js = read_text(STATIC_DIR / "shared.js")
    mobile_script = read_text(STATIC_DIR / "mobile_script.js")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title data-i18n="app.title">TRMD 转存控制台</title>
<style>{fonts_css}</style>
<style>{tailwind_css}</style>
</head>
<body class="mob-body bg-bg text-text">
{mobile_body}
<script>{helpers_js}
{shared_js}</script>
<script>{mobile_script}</script>
</body>
</html>"""


def _copy_font_files() -> int:
    """把字体原始文件复制到产物目录（运行时按需读取，不再 base64 常驻）。"""
    output_fonts = OUTPUT_FONTS_DIR
    if output_fonts.is_dir():
        shutil.rmtree(output_fonts)
    output_fonts.mkdir(parents=True, exist_ok=True)
    source = STATIC_DIR / "fonts"
    count = 0
    if source.is_dir():
        for path in sorted(source.iterdir()):
            if path.suffix in (".woff2", ".woff", ".ttf"):
                shutil.copyfile(path, output_fonts / path.name)
                count += 1
    return count


def main():
    tailwind_css = read_text(DIST_DIR / "tailwind.min.css")
    fonts_css, font_files = _load_font_data()

    login_html = build_login_page(tailwind_css, fonts_css)
    desktop_html = build_desktop_html(tailwind_css, fonts_css)
    mobile_html = build_mobile_html(tailwind_css, fonts_css)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bundle = {
        "web_ui_html": desktop_html,
        "web_ui_mobile_html": mobile_html,
        "login_page_html": login_html,
    }
    OUTPUT_FILE.write_text(
        json.dumps(bundle, ensure_ascii=False), encoding="utf-8"
    )
    font_count = _copy_font_files()

    print(f"[build_frontend] Written {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size} bytes)")
    print(f"  Font files:   {font_count} copied to {OUTPUT_FONTS_DIR}")
    print(f"  Fonts CSS:    {len(fonts_css)} bytes")
    print(f"  Tailwind CSS: {len(tailwind_css)} bytes")
    print(f"  Desktop HTML: {len(desktop_html)} bytes")
    print(f"  Login HTML:   {len(login_html)} bytes")
    print(f"  Mobile HTML:  {len(mobile_html)} bytes")


if __name__ == "__main__":
    main()
