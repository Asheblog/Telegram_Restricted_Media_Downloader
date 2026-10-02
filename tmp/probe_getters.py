# coding=UTF-8
"""探针：把 composition_root 的 getter 包一层"返回 None 就告警"，跑全量收集依赖点。

目的：找出哪些 getter 的静默兜底是**真的被用到**（即半构造宿主依赖它），
从而判断哪些可以安全收紧为直接属性访问。
"""
import pathlib
import subprocess
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
PROBE = REPO / "unit_tests" / "support" / "_getter_probe.py"

PROBE.write_text('''# coding=UTF-8
"""临时探针（由 tmp/probe_getters.py 生成，跑完即删）：记录解析为 None 的 getter。"""
import atexit
import os

import module.composition_root as cr

TARGETS = ("_app", "_gc", "_loop", "_pb", "_transfer_store", "_runtime_user",
           "_watch_manager", "_pikpak_manager")

records = set()


def _install():
    root = cr.TrmdCompositionRoot
    for name in TARGETS:
        original = getattr(root, name, None)
        if original is None:
            continue

        def make(name=name, original=original):
            def wrapper(self):
                value = original(self)
                if value is None:
                    records.add(f"{name} -> None")
                return value
            return wrapper

        setattr(root, name, make())


def _dump():
    path = os.environ.get("TRMD_GETTER_PROBE_OUT")
    if not path:
        return
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\\n".join(sorted(records)) or "(no None resolutions)")


_install()
atexit.register(_dump)
''', encoding="utf-8")

# 通过 sitecustomize 方式注入：用 PYTHONSTARTUP 不生效，改用 conftest 不方便，
# 这里直接把探针 import 进一个 pytest 插件参数（-p）里。
plugin = REPO / "tmp" / "_probe_plugin.py"
plugin.write_text('''# coding=UTF-8
"""pytest 插件：加载 getter 探针。"""
from unit_tests.support import _getter_probe  # noqa: F401
''', encoding="utf-8")

sys.path.insert(0, str(REPO))
tests = sorted(str(p) for p in (REPO / "unit_tests").glob("*_case.py"))
env_out = REPO / "tmp" / "getter_probe_result.txt"
if env_out.exists():
    env_out.unlink()

import os  # noqa: E402

env = dict(os.environ)
env["TRMD_GETTER_PROBE_OUT"] = str(env_out)
env["PYTHONPATH"] = str(REPO)

proc = subprocess.run(
    [sys.executable, "-m", "pytest", *tests, "-q", "--no-header",
     "-p", "no:cacheprovider", "-p", "tmp._probe_plugin"],
    cwd=str(REPO), capture_output=True, env=env,
)
out = proc.stdout.decode("utf-8", "replace")
print("pytest exit:", proc.returncode)
for line in out.splitlines():
    if "passed" in line or "failed" in line:
        print(" ", line.strip())

print("\n=== getter 解析为 None 的情况 ===")
if env_out.exists():
    print(env_out.read_text(encoding="utf-8"))
else:
    print("(探针未产出结果文件)")
