# coding=UTF-8
"""Push 前一致性自检：版本三处、锁文件、python 约束、tag 冲突。"""
import pathlib
import re
import subprocess
import sys
import tomllib

REPO = pathlib.Path(r"E:\codebase\tgbot")
sys.path.insert(0, str(REPO))
from unit_tests.pyrogram_stub import install_pyrogram_stub  # noqa: E402

install_pyrogram_stub()
import module  # noqa: E402

pp = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
lock = (REPO / "uv.lock").read_text(encoding="utf-8")
m = re.search(
    r'name = "telegram-restricted-media-downloader"\nversion = "([^"]+)"', lock
)
versions = {
    "pyproject.toml": pp["project"]["version"],
    "module/constants.py": module.__version__,
    "uv.lock (root pkg)": m.group(1) if m else "<not found>",
}
for k, v in versions.items():
    print(f"  {k:22s} {v}")
unique = set(versions.values())
print("  一致:", "YES" if len(unique) == 1 else f"NO -> {unique}")

print("\n  requires-python :", pp["project"]["requires-python"])
print("  .python-version :", (REPO / ".python-version").read_text().strip())

print("\n  uv lock --check:")
proc = subprocess.run(["uv", "lock", "--check"], cwd=str(REPO), capture_output=True)
print("   exit =", proc.returncode)

print("\n  origin tag v0.2.250 present?")
out = subprocess.run(
    ["git", "ls-remote", "--tags", "origin", "v0.2.250"],
    cwd=str(REPO), capture_output=True,
).stdout.decode("utf-8", "replace").strip()
print("  ", out or "(none -> 可安全创建)")
