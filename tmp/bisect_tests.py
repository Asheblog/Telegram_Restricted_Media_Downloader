# coding=UTF-8
"""Bisect the unit_tests suite to find which file makes the interpreter die.

Runs pytest per-file in a fresh subprocess and records the exit code.
0xC0000005 (3221225477) / negative codes mean a native crash.
"""
import pathlib
import subprocess
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
PY = REPO / ".venv" / "Scripts" / "python.exe"
TESTS = REPO / "unit_tests"


def run(args, timeout=300):
    proc = subprocess.run(
        [str(PY), "-m", "pytest", *args, "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=str(REPO), capture_output=True, text=True, timeout=timeout,
    )
    tail = (proc.stdout or "").strip().splitlines()
    return proc.returncode, (tail[-1] if tail else "")


files = sorted(p.name for p in TESTS.glob("*_case.py"))
results = []
for name in files:
    try:
        code, tail = run([f"unit_tests/{name}"])
    except subprocess.TimeoutExpired:
        code, tail = "TIMEOUT", ""
    results.append((name, code, tail))
    print(f"{code!s:>12}  {name}  |  {tail[:60]}", flush=True)

bad = [r for r in results if r[1] != 0]
print()
print(f"=== per-file: {len(results)} files, {len(bad)} with non-zero exit ===")
for name, code, tail in bad:
    print(f"  exit={code}  {name}  |  {tail[:90]}")
