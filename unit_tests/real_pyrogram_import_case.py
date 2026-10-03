# coding=UTF-8
"""真实导入守卫：在**没有 pyrogram stub** 的独立进程里导入整个 module 树。

## 为什么必须是子进程、且必须显式绕过 stub
本仓库的测试通过 `unit_tests/pyrogram_stub.py` 注入一个 **DummyModule**，它会为
**任意属性名**伪造对象。因此：

```python
from pyrogram.errors.exceptions.bad_request_400 import ChannelPrivate_400   # 真实 pyrogram 没有
```
在测试里**永远成功**，而在容器里立刻 `ImportError`。

这不是假设 —— 2026-10-03 的生产事故正是如此：我把一条多行 import 压成单行时
丢了 `as` 别名（`ChannelPrivate as ChannelPrivate_400` → 裸 `ChannelPrivate_400`），
**镜像构建通过、757 个测试全绿、CI 全绿，但用户容器一启动就崩**。
本用例就是为堵住这个缺口而写。

## 判据
在干净子进程里：
1. 确认用的是**真实** pyrogram（不是 stub）；
2. 遍历导入 `module/**/*.py` 的全部模块；
3. 任一失败即用例失败，并把子进程 stderr 带回来。
"""
import pathlib
import subprocess
import sys
import unittest

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

ROOT = pathlib.Path(__file__).resolve().parents[1]

# 在子进程里执行：先自证不是 stub，再导入整棵树。
PROBE = r'''
import importlib, pathlib, sys
sys.path.insert(0, ".")

# 1) 自证使用真实 pyrogram（stub 是注入 sys.modules 的 DummyModule，没有真实 __file__）
import pyrogram
pyro = getattr(pyrogram, "__file__", None)
if pyro is None or "site-packages" not in pyro.replace("\\", "/"):
    print("STUB_DETECTED:" + str(pyro))
    sys.exit(9)
print("PYROGRAM:" + pyro)

# 2) 导入整个 module 树
root = pathlib.Path("module")
mods = []
for p in sorted(root.rglob("*.py")):
    if "__pycache__" in p.parts:
        continue
    parts = list(p.relative_to(".").with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    mods.append(".".join(parts))

failed = []
for name in mods:
    try:
        importlib.import_module(name)
    except Exception as exc:
        failed.append(f"{name}: {type(exc).__name__}: {exc}")

print(f"IMPORTED:{len(mods) - len(failed)}/{len(mods)}")
for item in failed:
    print("FAILED:" + item)
sys.exit(1 if failed else 0)
'''


class RealPyrogramImportTreeCase(unittest.TestCase):
    def test_whole_module_tree_imports_without_the_stub(self):
        proc = subprocess.run(
            [sys.executable, "-c", PROBE],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        out = proc.stdout or ""
        err = proc.stderr or ""

        self.assertNotIn(
            "STUB_DETECTED",
            out,
            "子进程里出现的是 pyrogram stub —— 本用例会因此失去意义，"
            f"请检查子进程为何被注入 stub：{out}",
        )
        self.assertIn(
            "PYROGRAM:",
            out,
            f"子进程没能确认使用真实 pyrogram。stdout={out!r} stderr={err[-1500:]!r}",
        )

        if proc.returncode != 0:
            failed = [l for l in out.splitlines() if l.startswith("FAILED:")]
            self.fail(
                "在真实 pyrogram 下导入 module 树失败 —— "
                "这类错误在带 stub 的测试里是**看不见**的，但在容器里会让进程起不来。\n"
                + "\n".join(failed)
                + f"\n\nstderr（末 1500 字）：\n{err[-1500:]}"
            )

    def test_probe_detects_a_broken_import(self):
        """反向自检：探测脚本必须真的会因为坏导入而失败。

        做法：在子进程里先插入一个"只有 stub 才有"的名字再导入，
        验证探测逻辑会把它报出来 —— 保证上面的用例不是"永远通过"。
        """
        broken = (
            PROBE.replace(
                "failed = []",
                "failed = []\n"
                "import pyrogram.errors.exceptions.bad_request_400 as _m\n"
                "if not hasattr(_m, 'DefinitelyNotARealError_XYZ'):\n"
                "    failed.append('selftest: DefinitelyNotARealError_XYZ missing')\n",
            )
        )
        proc = subprocess.run(
            [sys.executable, "-c", broken],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertNotEqual(
            0,
            proc.returncode,
            "探测脚本对一个确定不存在的名字仍返回 0 —— 说明它没有真正的检测能力",
        )
        self.assertIn("DefinitelyNotARealError_XYZ", proc.stdout or "")


if __name__ == "__main__":
    unittest.main()
