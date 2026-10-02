# coding=UTF-8
"""模块规模守卫：单个模块不得无限膨胀，超出阈值必须显式登记理由。

## 为什么需要
本仓库的工程规则里有"不把几千行塞进一个文件，导致后面还要再解耦"。但"几千行"
是主观的，靠人盯不住。这个用例把它变成**可执行的检查**：

- 任一 `module/**/*.py` 超过 `MAX_LINES` 就必须出现在 `JUSTIFIED` 里，并写明
  "为什么它大得合理"或"计划怎么拆"；
- 已经拆过的文件登记后，若日后又被合并回大文件，用例会失败。

## 为什么允许清单而不是硬阈值
有些模块"大得合理"：
- `core/enums.py`：纯常量/枚举定义，没有逻辑分支，行数与复杂度不成正比；
- `utils/stdio.py`、`core/config.py`：数据结构 + 少量校验；
- 已登记"待拆/不拆结论"的文件（见 CONTEXT 的"不该拆"段落）。

硬阈值会把它们全判违规，反而逼人为了过检查而做无意义的拆包 —— 那正是
本仓库明确反对的"纯包搬家"。

## 阈值怎么定的
当前最大模块约 1,900 行，拆分轮把 3 个超大文件降到了 1,230 / 1,891 / 526。
阈值取 2,000：**高于现存所有文件**，因此本用例不会为存量文件制造噪声；
它的作用是拦住"以后新写一个 2,000+ 行的文件"。
"""
import pathlib
import sys
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / "module"

MAX_LINES = 2000

# 超过上限才需要登记；键是相对 module/ 的路径。
JUSTIFIED: dict[str, str] = {}


def _module_files() -> list[pathlib.Path]:
    return sorted(
        p
        for p in MODULE.rglob("*.py")
        if "__pycache__" not in p.parts
    )


class ModuleSizeCase(unittest.TestCase):
    def test_no_module_exceeds_line_budget_without_justification(self):
        oversized = {}
        for path in _module_files():
            rel = path.relative_to(MODULE).as_posix()
            lines = len(path.read_text(encoding="utf-8").splitlines())
            if lines > MAX_LINES and rel not in JUSTIFIED:
                oversized[rel] = lines
        self.assertEqual(
            {},
            oversized,
            f"这些模块超过 {MAX_LINES} 行且未登记理由：{oversized}。"
            "请按职责拆分（拆完要确认调用方真的改道、且新模块入度 > 1），"
            "或在 JUSTIFIED 里写明为什么它大得合理。",
        )

    def test_justification_entries_are_not_stale(self):
        """登记不能腐烂：已拆小的文件必须从允许清单移除。"""
        stale = []
        for rel in JUSTIFIED:
            path = MODULE / rel
            if not path.exists():
                stale.append(f"{rel}（文件已不存在）")
                continue
            lines = len(path.read_text(encoding="utf-8").splitlines())
            if lines <= MAX_LINES:
                stale.append(f"{rel}（现在只有 {lines} 行，已达标）")
        self.assertEqual(
            [],
            stale,
            f"这些登记已过时，请从 JUSTIFIED 移除：{stale}",
        )

    def test_justification_entries_exist(self):
        missing = [rel for rel in JUSTIFIED if not (MODULE / rel).exists()]
        self.assertEqual([], missing, f"JUSTIFIED 里的文件不存在：{missing}")

    def test_no_empty_justification_text(self):
        empty = [rel for rel, why in JUSTIFIED.items() if len(why.strip()) < 10]
        self.assertEqual(
            [],
            empty,
            f"这些登记没有写清理由（少于 10 字）：{empty}",
        )


if __name__ == "__main__":
    unittest.main()
