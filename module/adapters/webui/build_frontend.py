#!/usr/bin/env python3
"""Build frontend assets into assets.py Python string constants.

Reads HTML/JS/CSS files from templates/ and static/ directories,
assembles the final HTML documents, and writes them as Python
constants in assets.py.

All styles now live in tailwind.css (@theme + @layer components);
mobile.css has been removed — mobile components are part of the
same Tailwind build.
"""

import base64
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST_DIR = HERE / "dist"
TEMPLATES_DIR = HERE / "templates"
STATIC_DIR = HERE / "static"
OUTPUT_FILE = HERE / "assets.py"


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


def main():
    tailwind_css = read_text(DIST_DIR / "tailwind.min.css")
    fonts_css, font_files = _load_font_data()

    login_html = build_login_page(tailwind_css, fonts_css)
    desktop_html = build_desktop_html(tailwind_css, fonts_css)
    mobile_html = build_mobile_html(tailwind_css, fonts_css)

    # Build font data dict source code
    if font_files:
        font_entries = ",\n    ".join(
            f'"{name}": "{data}"' for name, data in sorted(font_files.items())
        )
        font_dict_src = "{\n    " + font_entries + "\n}"
    else:
        font_dict_src = "{}"

    output = f'''# coding=UTF-8
# WebUI 静态资源 — 由 build_frontend.py 自动生成
# 请勿手动编辑。模板文件在 templates/ 和 static/ 目录。

WEB_UI_HTML = r"""{desktop_html}"""

WEB_UI_MOBILE_HTML = r"""{mobile_html}"""

LOGIN_PAGE_HTML = r"""{login_html}"""

FONTS = {font_dict_src}
'''

    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(f"[build_frontend] Written {OUTPUT_FILE} ({len(output)} bytes)")
    print(f"  Fonts CSS:    {len(fonts_css)} bytes ({len(font_files)} files, {sum(len(b64) for b64 in font_files.values()) * 3 // 4 // 1024} KB raw)")
    print(f"  Tailwind CSS: {len(tailwind_css)} bytes")
    print(f"  Desktop HTML: {len(desktop_html)} bytes")
    print(f"  Login HTML:   {len(login_html)} bytes")
    print(f"  Mobile HTML:  {len(mobile_html)} bytes")


if __name__ == "__main__":
    main()
