# coding=UTF-8
"""兼容层 —— 资源实现见 ``module.adapters.webui.static_assets``。

历史上本文件是 ``build_frontend.py`` 生成的 1.2 MB / 约 15,700 行内联常量
（3 份完整 HTML + base64 字体），占 ``module/`` 全部 Python 字节 41%，
且是全仓 churn 第一名（近 200 次提交改动 141 次）。现在资源改为运行时从
``dist/webui/`` 读取、源码在时内存重建，见 ``static_assets``；本模块只转发名字。

新代码请直接 ``from module.adapters.webui.static_assets import ...``。
"""
from module.adapters.webui.static_assets import (  # noqa: F401
    FONTS,
    LOGIN_PAGE_HTML,
    WEB_UI_HTML,
    WEB_UI_MOBILE_HTML,
    clear_cache,
    font_names,
    load_font,
)

__all__ = [
    "FONTS",
    "LOGIN_PAGE_HTML",
    "WEB_UI_HTML",
    "WEB_UI_MOBILE_HTML",
    "clear_cache",
    "font_names",
    "load_font",
]
