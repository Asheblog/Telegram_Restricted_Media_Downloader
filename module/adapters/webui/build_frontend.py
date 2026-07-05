#!/usr/bin/env python3
"""Build frontend assets into assets.py Python string constants.

Reads HTML/JS/CSS files from templates/ and static/ directories,
assembles the final HTML documents, and writes them as Python
constants in assets.py.
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST_DIR = HERE / "dist"
TEMPLATES_DIR = HERE / "templates"
STATIC_DIR = HERE / "static"
OUTPUT_FILE = HERE / "assets.py"

# -- Green → Blue color migration (shared by all mobile CSS paths) --
COLOR_MIGRATIONS = [
    ("#0f8f72", "#2563EB"),
    ("#0a6f5a", "#1D4ED8"),
    ("#e4f5ef", "#EFF6FF"),
    ("#9fcfbe", "#93C5FD"),
    ("rgba(15, 143, 114, 0.4)", "rgba(37, 99, 235, 0.4)"),
    ("rgba(15, 143, 114, .4)", "rgba(37, 99, 235, .4)"),
    ("rgba(15, 143, 114, 0.3)", "rgba(37, 99, 235, 0.3)"),
    ("rgba(15, 143, 114, .3)", "rgba(37, 99, 235, .3)"),
    ("rgba(15, 143, 114, 0.15)", "rgba(37, 99, 235, 0.12)"),
    ("rgba(15, 143, 114, .15)", "rgba(37, 99, 235, .12)"),
    ("rgba(15, 143, 114, 0.12)", "rgba(37, 99, 235, 0.12)"),
    ("rgba(15, 143, 114, .12)", "rgba(37, 99, 235, .12)"),
    ("rgba(15, 143, 114, 0.08)", "rgba(37, 99, 235, 0.08)"),
    ("rgba(15, 143, 114, .08)", "rgba(37, 99, 235, .08)"),
    ("--accent: #0f8f72", "--accent: #2563EB"),
    ("--accent-strong: #0a6f5a", "--accent-strong: #1D4ED8"),
    ("--bg: #f7f8fa", "--bg: #F0F4FF"),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def migrate_colors(text: str) -> str:
    """Apply green→blue color replacement to mobile CSS."""
    for old, new in COLOR_MIGRATIONS:
        text = text.replace(old, new)
    return text


def build_login_page(tailwind_css: str) -> str:
    html = read_text(TEMPLATES_DIR / "login.html")
    return html.replace("/* tailwind.min.css */", tailwind_css)


def build_desktop_html(tailwind_css: str) -> str:
    base = read_text(TEMPLATES_DIR / "base.html")
    views = read_text(TEMPLATES_DIR / "views.html")
    shared_js = read_text(STATIC_DIR / "shared.js")
    desktop_js = read_text(STATIC_DIR / "desktop.js")

    html = base.replace("/* tailwind.min.css */", tailwind_css)
    html = html.replace("<!-- VIEWS PLACEHOLDER -->", views)
    html = html.replace("/* shared.js */", shared_js)
    html = html.replace("/* desktop.js */", desktop_js)
    return html


def build_mobile_html() -> str:
    """Build mobile HTML with blue color scheme."""
    mobile_body = read_text(TEMPLATES_DIR / "mobile_body.html")
    mobile_css = migrate_colors(read_text(STATIC_DIR / "mobile.css"))
    shared_js = read_text(STATIC_DIR / "mobile_shared.js")
    mobile_script = read_text(STATIC_DIR / "mobile_script.js")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title data-i18n="app.title">TRMD 转存控制台</title>
<style>{mobile_css}</style>
</head>
<body>
{mobile_body}
<script>{shared_js}</script>
<script>{mobile_script}</script>
</body>
</html>"""


def main():
    tailwind_css = read_text(DIST_DIR / "tailwind.min.css")

    login_html = build_login_page(tailwind_css)
    desktop_html = build_desktop_html(tailwind_css)
    mobile_html = build_mobile_html()

    # Backward-compatible exports
    mobile_body = read_text(TEMPLATES_DIR / "mobile_body.html")
    css_export = migrate_colors(read_text(STATIC_DIR / "mobile.css"))
    shared_js = read_text(STATIC_DIR / "mobile_shared.js")
    mobile_script = read_text(STATIC_DIR / "mobile_script.js")

    # Use sentinel strings to safely embed content with braces into f-string template.
    # Sentinel: __DLB__ → {, __DRB__ → }
    LB = "__DLB__"
    RB = "__DRB__"

    output = f'''# coding=UTF-8
# WebUI 静态资源 — 由 build_frontend.py 自动生成
# 请勿手动编辑。模板文件在 templates/ 和 static/ 目录。

from html import escape


def _html_attr(name: str, value: str = None) -> str:
    if value is None:
        return ''
    return f' {LB}name{RB}="{LB}escape(str(value), quote=True){RB}"'


def panel_head(
        *,
        title_i18n: str,
        title_text: str,
        meta_i18n: str = None,
        meta_text: str = None,
        meta_id: str = None,
        indent: int = 10
) -> str:
    pad = ' ' * indent
    child_pad = ' ' * (indent + 2)
    title = escape(title_text, quote=False)
    head = [
        f'{LB}pad{RB}<div class="panel-head" data-component="panel-head">',
        f'{LB}child_pad{RB}<h3 class="panel-head__title"{LB}_html_attr("data-i18n", title_i18n){RB}>{LB}title{RB}</h3>'
    ]
    if meta_text is not None or meta_i18n is not None or meta_id is not None:
        meta = escape(meta_text or '', quote=False)
        head.append(
            f'{LB}child_pad{RB}<div class="panel-head__meta"'
            f'{LB}_html_attr("id", meta_id){RB}'
            f'{LB}_html_attr("data-i18n", meta_i18n){RB}>{LB}meta{RB}</div>'
        )
    head.append(f'{LB}pad{RB}</div>')
    return '\\n'.join(head)


WEB_UI_HTML = r"""{desktop_html}"""

WEB_UI_MOBILE_HTML = r"""{mobile_html}"""

LOGIN_PAGE_HTML = r"""{login_html}"""

WEB_UI_CSS = r"""{css_export}"""
WEB_UI_MOBILE_CSS = WEB_UI_CSS

WEB_UI_MOBILE_BODY = r"""{mobile_body}"""

SHARED_WEB_UI_SCRIPT = r"""{shared_js}"""
WEB_UI_MOBILE_SCRIPT = SHARED_WEB_UI_SCRIPT + r"""{mobile_script}"""
'''

    # Resolve sentinels
    output = output.replace(LB, "{").replace(RB, "}")

    OUTPUT_FILE.write_text(output, encoding="utf-8")
    print(f"[build_frontend] Written {OUTPUT_FILE} ({len(output)} bytes)")
    print(f"  Tailwind CSS: {len(tailwind_css)} bytes")
    print(f"  Desktop HTML: {len(desktop_html)} bytes")
    print(f"  Login HTML:   {len(login_html)} bytes")
    print(f"  Mobile HTML:  {len(mobile_html)} bytes")


if __name__ == "__main__":
    main()
