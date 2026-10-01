# coding=UTF-8
"""前端资源同步守门：assets.py 必须等于由 templates/ + static/ 重建的结果。

背景（解耦审查结论）：``module/adapters/webui/assets.py`` 是 1.2 MB /
15,679 行的**生成物**，但被提交进仓库；生成器 ``build_frontend.py`` 没有任何
自动调用方（Dockerfile / build.py / package.json / CI 都没有），
而此前 43 个 UI 测试只断言"生成物里存在某些字符串"，0 次引用源文件。
于是「改了 templates/static 忘记重新生成」会**测试全绿 + 页面陈旧**。

本用例在内存里重建并与已提交常量逐字节比对，把这条静默故障类堵住。
只调用 build_frontend 的纯函数，不执行其 main()（那会写盘）。
"""
import base64
import importlib.util
import pathlib
import sys
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]

from module.adapters.webui import assets  # noqa: E402

sys.argv = _ORIGINAL_ARGV

WEBUI_DIR = pathlib.Path(__file__).resolve().parents[1] / "module" / "adapters" / "webui"


def _load_builder():
    """按文件路径加载 build_frontend，避免 import 触发任何副作用。"""
    spec = importlib.util.spec_from_file_location(
        "_trmd_build_frontend_check", WEBUI_DIR / "build_frontend.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FrontendAssetsInSyncCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = _load_builder()
        cls.tailwind_css = (WEBUI_DIR / "dist" / "tailwind.min.css").read_text(encoding="utf-8")
        cls.fonts_css, cls.font_files = cls.builder._load_font_data()

    def _assert_same(self, label, rebuilt, committed):
        self.assertEqual(
            rebuilt,
            committed,
            f"{label} 与 templates/static 重建结果不一致："
            f"改了源文件却没运行 python module/adapters/webui/build_frontend.py？",
        )

    def test_desktop_html_matches_sources(self):
        rebuilt = self.builder.build_desktop_html(self.tailwind_css, self.fonts_css)
        self._assert_same("WEB_UI_HTML", rebuilt, assets.WEB_UI_HTML)

    def test_mobile_html_matches_sources(self):
        rebuilt = self.builder.build_mobile_html(self.tailwind_css, self.fonts_css)
        self._assert_same("WEB_UI_MOBILE_HTML", rebuilt, assets.WEB_UI_MOBILE_HTML)

    def test_login_page_matches_sources(self):
        rebuilt = self.builder.build_login_page(self.tailwind_css, self.fonts_css)
        self._assert_same("LOGIN_PAGE_HTML", rebuilt, assets.LOGIN_PAGE_HTML)

    def test_fonts_dict_matches_font_files(self):
        """FONTS 里的 base64 必须与 static/fonts/ 下同名文件一致，且无多余/缺失。"""
        committed = assets.FONTS
        self.assertEqual(
            sorted(committed), sorted(self.font_files),
            "FONTS 字典的文件名集合与 static/fonts/ 不一致",
        )
        for name, encoded in self.font_files.items():
            self.assertEqual(
                committed[name], encoded,
                f"字体 {name} 的 base64 与源文件不一致",
            )
            # 顺带确认可解码，避免写入时被截断。
            base64.b64decode(encoded)


if __name__ == "__main__":
    unittest.main()
