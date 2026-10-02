# coding=UTF-8
"""Prove what --frozen actually enforces vs --locked, in a scratch copy.

Mutates only a temp copy; the repo is untouched.
"""
import os
import pathlib
import shutil
import subprocess
import tempfile

REPO = pathlib.Path(r"E:\codebase\tgbot")
tmp = pathlib.Path(tempfile.mkdtemp(prefix="lockprobe-"))
try:
    for name in ("pyproject.toml", "uv.lock", ".python-version", "requirements.txt", "README.md"):
        src = REPO / name
        if src.exists():
            shutil.copy(src, tmp / name)
    (tmp / "module").mkdir(exist_ok=True)

    pyproject = tmp / "pyproject.toml"
    original = pyproject.read_text(encoding="utf-8")
    assert 'version = "0.2.250"' in original
    pyproject.write_text(
        original.replace('version = "0.2.250"', 'version = "0.2.251"'), encoding="utf-8"
    )
    print("scratch: pyproject version=0.2.251, uv.lock still 0.2.250 (故意不匹配)\n")

    cases = [
        ["uv", "lock", "--check"],
        ["uv", "sync", "--frozen", "--group", "dev", "--dry-run"],
        ["uv", "sync", "--locked", "--group", "dev", "--dry-run"],
        ["uv", "run", "--frozen", "python", "-c", "print(1)"],
        ["uv", "run", "--locked", "python", "-c", "print(1)"],
    ]
    for args in cases:
        proc = subprocess.run(args, cwd=str(tmp), capture_output=True)
        tail = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip().splitlines()
        msg = tail[-1][:95] if tail else ""
        print(f"exit={proc.returncode:<3} {' '.join(args):50s} {msg}")

    # 一致性时应当全部通过
    pyproject.write_text(original, encoding="utf-8")
    print("\nscratch: 版本改回一致后")
    for args in cases:
        proc = subprocess.run(args, cwd=str(tmp), capture_output=True)
        print(f"exit={proc.returncode:<3} {' '.join(args)}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
    print("\nscratch removed:", not tmp.exists())
