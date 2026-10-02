# coding=UTF-8
"""版本 bump：同步 pyproject.toml 与 module/constants.py，并重跑 uv lock。"""
import pathlib
import subprocess
import sys
import tomllib

REPO = pathlib.Path(r"E:\codebase\tgbot")
OLD = sys.argv[1]
NEW = sys.argv[2]

targets = [
    (REPO / "pyproject.toml", f'version = "{OLD}"', f'version = "{NEW}"'),
    (REPO / "module" / "constants.py", f'__version__ = "{OLD}"', f'__version__ = "{NEW}"'),
]
for path, old, new in targets:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"anchor {old!r} missing in {path.name}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("bumped", path.name)

proc = subprocess.run(["uv", "lock"], cwd=str(REPO), capture_output=True)
print("uv lock exit =", proc.returncode, proc.stdout.decode('utf-8','replace').strip().splitlines()[-1:])

pp = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
import re
lock = (REPO / "uv.lock").read_text(encoding="utf-8")
m = re.search(r'name = "telegram-restricted-media-downloader"\nversion = "([^"]+)"', lock)
print("pyproject:", pp["project"]["version"])
print("uv.lock  :", m.group(1) if m else "?")
print("constants:", re.search(r'__version__ = "([^"]+)"', (REPO / "module" / "constants.py").read_text(encoding="utf-8")).group(1))
