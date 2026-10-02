# coding=UTF-8
"""WebUI 静态资源加载器。

## 为什么不再把资源内联进 Python 常量
历史实现由 ``build_frontend.py`` 把 3 份完整 HTML（内联 CSS/JS、base64 字体）写进
``assets.py``，形成 1.2 MB / 约 15,700 行、占 ``module/`` 全部 Python 字节 41% 的
提交物。代价是全仓第一名的 churn：近 200 次提交里被改 141 次、单次 diff 最大 2,215 行，
而它只是机器生成的副本，reviewer 无法真正审阅。

现在改为：``templates/`` + ``static/`` 是唯一真源，``build_frontend.py`` 产出运行时
产物 ``dist/webui/assets.json`` + ``dist/webui/fonts/*``；本模块负责读取与缓存。

## 三级来源（依次回退）
1. 构建产物 ``dist/webui/assets.json``：生产与 CI 路径；
2. 内存重建：**源码在时**直接调用 ``build_frontend`` 的纯函数拼装（因此改了模板/JS/CSS
   立刻生效，不需要先跑构建；测试环境也走这条）；
3. 都没有：抛 ``RuntimeError``，附上"跑哪条命令"的提示。

字体：``FONTS`` 仍以 ``{filename: base64}`` 暴露（HTTP 层按原样回写），
但改为从 ``dist/webui/fonts/*`` 按需读取，不再把 base64 常驻在 Python 源里。
"""
from __future__ import annotations

import base64
import json
import pathlib
import threading
from typing import Optional

def _resource_base() -> pathlib.Path:
    """资源根目录。

    在 **Nuitka 单文件/独立包**里 ``__file__`` 指向源码路径（部署机上并不存在），
    打包进去的数据实际落在 ``__compiled__.containing_dir``。因此这里优先取后者，
    否则冻结包会出现"产物与源码都找不到"而**首开页面必崩**。
    """
    compiled = globals().get("__compiled__")
    if compiled is not None:
        containing_dir = getattr(compiled, "containing_dir", None)
        if containing_dir:
            candidate = pathlib.Path(containing_dir)
            if candidate.is_dir():
                return candidate
    return pathlib.Path(__file__).resolve().parent


HERE = _resource_base()
BUNDLE_DIR = HERE / "dist" / "webui"
BUNDLE_FILE = BUNDLE_DIR / "assets.json"
FONTS_DIR = BUNDLE_DIR / "fonts"

_TEMPLATES_DIR = HERE / "templates"
_STATIC_DIR = HERE / "static"
_SOURCES_PRESENT = (_TEMPLATES_DIR / "base.html").is_file()

_lock = threading.Lock()
_cache: Optional[dict] = None


def _load_builder():
    """按文件路径加载 build_frontend，避免它被当成包内模块参与 import 图。"""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_trmd_build_frontend", HERE / "build_frontend.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _render_from_sources() -> dict:
    """源码在时：内存里重建（不需要先跑构建）。"""
    builder = _load_builder()
    tailwind_css = (HERE / "dist" / "tailwind.min.css").read_text(encoding="utf-8")
    fonts_css, _ = builder._load_font_data()
    return {
        "web_ui_html": builder.build_desktop_html(tailwind_css, fonts_css),
        "web_ui_mobile_html": builder.build_mobile_html(tailwind_css, fonts_css),
        "login_page_html": builder.build_login_page(tailwind_css, fonts_css),
    }


def _load_bundle() -> dict:
    global _cache
    with _lock:
        if _cache is not None:
            return _cache
        bundle: Optional[dict] = None
        if BUNDLE_FILE.is_file():
            bundle = json.loads(BUNDLE_FILE.read_text(encoding="utf-8"))
        elif _SOURCES_PRESENT:
            bundle = _render_from_sources()
        if bundle is None:
            raise RuntimeError(
                "WebUI 静态资源缺失：既没有构建产物 "
                f"{BUNDLE_FILE}，也没有模板源码 {_TEMPLATES_DIR}。"
                "请运行 `python module/adapters/webui/build_frontend.py` 生成产物"
                "（源码模式下无需构建，缺失说明部署包裁剪过度）。"
            )
        _cache = bundle
        return bundle


def clear_cache() -> None:
    """清缓存（测试或热重载用）。"""
    global _cache
    with _lock:
        _cache = None


def _font_files() -> list[pathlib.Path]:
    if FONTS_DIR.is_dir():
        return sorted(
            p for p in FONTS_DIR.iterdir()
            if p.suffix in (".woff2", ".woff", ".ttf")
        )
    if _SOURCES_PRESENT:
        fonts = _STATIC_DIR / "fonts"
        if fonts.is_dir():
            return sorted(
                p for p in fonts.iterdir()
                if p.suffix in (".woff2", ".woff", ".ttf")
            )
    return []


def load_font(filename: str) -> Optional[bytes]:
    """按文件名取字体原始字节；不存在返回 None。"""
    if not filename or "/" in filename or "\\" in filename:
        return None
    for path in _font_files():
        if path.name == filename:
            return path.read_bytes()
    return None


def font_names() -> list[str]:
    return [p.name for p in _font_files()]


def _fonts_as_base64() -> dict:
    """兼容旧接口：{filename: base64}。按需从磁盘读取，不常驻内存。"""
    return {
        path.name: base64.b64encode(path.read_bytes()).decode("ascii")
        for path in _font_files()
    }


def __getattr__(name: str):
    """按需暴露 4 个资源名，保持既有 `from ...assets import WEB_UI_HTML` 写法可用。"""
    mapping = {
        "WEB_UI_HTML": "web_ui_html",
        "WEB_UI_MOBILE_HTML": "web_ui_mobile_html",
        "LOGIN_PAGE_HTML": "login_page_html",
    }
    if name in mapping:
        return _load_bundle()[mapping[name]]
    if name == "FONTS":
        return _fonts_as_base64()
    raise AttributeError(name)


__all__ = [
    "BUNDLE_DIR",
    "BUNDLE_FILE",
    "FONTS",
    "LOGIN_PAGE_HTML",
    "WEB_UI_HTML",
    "WEB_UI_MOBILE_HTML",
    "clear_cache",
    "font_names",
    "load_font",
]
