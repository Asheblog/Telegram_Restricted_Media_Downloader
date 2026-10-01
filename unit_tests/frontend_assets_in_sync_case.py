# coding=UTF-8
"""前端资源守门：运行时资源必须等于由 templates/ + static/ 重建的结果。

## 背景与不变量
历史实现把 3 份完整 HTML（内联 CSS/JS + base64 字体）以 1.2 MB / 约 15,700 行
Python 常量提交进仓库，且生成器 ``build_frontend.py`` 没有任何自动调用方：
改了模板忘记重生成会「测试全绿 + 页面陈旧」。

现在 ``templates/`` + ``static/`` 是**唯一真源**，运行时资源由
``static_assets`` 提供：优先读构建产物 ``dist/webui/assets.json``，
源码在时内存重建。本用例锁两件事：

1. 运行时实际提供的 HTML 必须与"当场从源码重建"的结果逐字节一致
   （无论它来自构建产物还是内存重建）——构建产物一旦陈旧就会被抓住；
2. 字体集合与字节必须与 ``static/fonts/`` 一致。

只调用 ``build_frontend`` 的纯函数，不执行其 ``main()``（那会写盘）。
"""
import pathlib
import sys
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
_ORIGINAL_ARGV = sys.argv
sys.argv = [_ORIGINAL_ARGV[0]]

from module.adapters.webui import static_assets  # noqa: E402

sys.argv = _ORIGINAL_ARGV

WEBUI_DIR = pathlib.Path(__file__).resolve().parents[1] / "module" / "adapters" / "webui"


class FrontendAssetsInSyncCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder = static_assets._load_builder()
        cls.builder = builder
        cls.tailwind_css = (WEBUI_DIR / "dist" / "tailwind.min.css").read_text(encoding="utf-8")
        cls.fonts_css, cls.font_files = builder._load_font_data()

    def _rebuilt(self) -> dict:
        return {
            "desktop": self.builder.build_desktop_html(self.tailwind_css, self.fonts_css),
            "mobile": self.builder.build_mobile_html(self.tailwind_css, self.fonts_css),
            "login": self.builder.build_login_page(self.tailwind_css, self.fonts_css),
        }

    def test_runtime_html_matches_sources_byte_for_byte(self):
        rebuilt = self._rebuilt()
        served = {
            "desktop": static_assets._load_bundle()["web_ui_html"],
            "mobile": static_assets._load_bundle()["web_ui_mobile_html"],
            "login": static_assets._load_bundle()["login_page_html"],
        }
        source = (
            "构建产物 dist/webui/assets.json"
            if static_assets.BUNDLE_FILE.is_file()
            else "内存重建"
        )
        for label, expected in rebuilt.items():
            self.assertEqual(
                expected,
                served[label],
                f"{label} 与源码重建结果不一致（当前来源：{source}）——"
                "改了 templates/static 后请运行 "
                "`python module/adapters/webui/build_frontend.py` 重新生成产物",
            )

    def test_bundle_matches_sources_when_artifact_exists(self):
        """有构建产物时，逐字节比对产物与当场重建 —— 专门抓"产物陈旧"。"""
        if not static_assets.BUNDLE_FILE.is_file():
            self.skipTest("无构建产物（源码模式），由上一用例覆盖")
        import json

        bundle = json.loads(static_assets.BUNDLE_FILE.read_text(encoding="utf-8"))
        rebuilt = self._rebuilt()
        self.assertEqual(rebuilt["desktop"], bundle["web_ui_html"], "产物中的桌面 HTML 已陈旧")
        self.assertEqual(rebuilt["mobile"], bundle["web_ui_mobile_html"], "产物中的移动 HTML 已陈旧")
        self.assertEqual(rebuilt["login"], bundle["login_page_html"], "产物中的登录页已陈旧")

    def test_fonts_match_source_files(self):
        """运行时字体的文件名与字节必须与 static/fonts/ 一致。"""
        self.assertEqual(
            sorted(static_assets.font_names()),
            sorted(self.font_files),
            "运行时字体集合与 static/fonts/ 不一致",
        )
        for name, encoded in self.font_files.items():
            raw = static_assets.load_font(name)
            self.assertIsNotNone(raw, f"运行时取不到字体 {name}")
            import base64

            self.assertEqual(encoded, base64.b64encode(raw).decode("ascii"),
                             f"字体 {name} 的字节与源文件不一致")

    def test_font_lookup_rejects_path_traversal(self):
        """字体名来自 URL，必须拒绝路径穿越。"""
        for bad in ("../secrets.txt", "a/b.woff2", "a\\b.woff2", "", "nope.woff2"):
            self.assertIsNone(static_assets.load_font(bad), bad)


if __name__ == "__main__":
    unittest.main()
