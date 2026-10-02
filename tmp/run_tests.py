# coding=UTF-8
"""Reliable full-suite runner: explicit file list, real exit code, short summary.

Usage: .venv\\Scripts\\python.exe tmp/run_tests.py [pytest args...]
Passes every unit_tests/*_case.py explicitly and reports a short summary.
Console is GBK on this host, so non-encodable characters are replaced.
"""
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
TESTS = sorted(str(p) for p in (REPO / "unit_tests").glob("*_case.py"))

extra = sys.argv[1:]
proc = subprocess.run(
    [sys.executable, "-m", "pytest", *TESTS, "-q", "--no-header",
     "-p", "no:cacheprovider", *extra],
    cwd=str(REPO), capture_output=True,
)
out = proc.stdout.decode("utf-8", "replace")
err = proc.stderr.decode("utf-8", "replace")

summary = [l for l in out.splitlines() if re.search(r"\d+ (passed|failed|error)", l)]
tail = [l for l in out.splitlines() if l.startswith(("FAILED", "ERROR"))]


def safe(line: str) -> str:
    return line.encode("gbk", "replace").decode("gbk")


print(f"files: {len(TESTS)}")
for line in summary[-3:]:
    print(f"summary: {safe(line.strip())}")
if tail:
    print("failures:")
    for line in tail[:40]:
        print(f"  {safe(line.strip())}")
print(f"EXIT={proc.returncode}")
if proc.returncode != 0 and not summary:
    print("--- raw tail ---")
    print(safe(out[-3000:]))
    print(safe(err[-2000:]))
sys.exit(proc.returncode)
