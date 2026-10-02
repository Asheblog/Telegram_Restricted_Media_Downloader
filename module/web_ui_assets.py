# coding=UTF-8
"""Compatibility shim — re-export module.adapters.webui.static_assets.

历史上本文件转发的是 ``module.adapters.webui.assets``；那个 1.2 MB 生成物已删除
（资源改为运行时加载，见 ``static_assets``）。本 shim 保留是因为
``unit_tests/web_ui_assets_case.py`` 仍按此路径导入；新代码请直接用
``module.adapters.webui.static_assets``。

注意：首行的 "Compatibility shim" 字样被 ``architecture_guard_case``
用来识别"顶层 shim"，改名或改措辞会让该守卫误判为"多出的真实模块"。
"""
from module.adapters.webui.static_assets import (  # noqa: F401
    FONTS,
    LOGIN_PAGE_HTML,
    WEB_UI_HTML,
    WEB_UI_MOBILE_HTML,
)

__all__ = [
    "FONTS",
    "LOGIN_PAGE_HTML",
    "WEB_UI_HTML",
    "WEB_UI_MOBILE_HTML",
]
