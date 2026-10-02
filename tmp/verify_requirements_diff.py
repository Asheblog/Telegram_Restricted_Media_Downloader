# coding=UTF-8
"""Verify every hash removed from requirements.txt belonged to a cp314 wheel.

Reads the git diff of requirements.txt, extracts removed sha256 values, and checks
each against the cp314 wheels that uv.lock used to contain (from git HEAD).
"""
import pathlib
import re
import subprocess

REPO = pathlib.Path(r"E:\codebase\tgbot")


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=str(REPO), capture_output=True, check=True
    ).stdout.decode("utf-8", "replace")


diff = git("diff", "--", "requirements.txt")
removed = re.findall(r"^-    --hash=sha256:([0-9a-f]{64})", diff, re.M)
added = re.findall(r"^\+    --hash=sha256:([0-9a-f]{64})", diff, re.M)
print(f"removed hashes: {len(removed)}  added hashes: {len(added)}")

# 旧 uv.lock 里所有含 cp314 的轮子行 -> 收集其 hash
old_lock = git("show", "HEAD:uv.lock")
cp314_hashes = set()
other_hashes = {}
for line in old_lock.splitlines():
    m = re.search(r"url = \"([^\"]+)\".*hash = \"sha256:([0-9a-f]{64})\"", line)
    if not m:
        continue
    url, h = m.group(1), m.group(2)
    if "cp314" in url:
        cp314_hashes.add(h)
    else:
        other_hashes[h] = url

print(f"old lock cp314 wheel hashes: {len(cp314_hashes)}")

not_cp314 = [h for h in removed if h not in cp314_hashes]
print(f"removed hashes NOT explainable as cp314: {len(not_cp314)}")
for h in not_cp314:
    print(f"   {h}  -> {other_hashes.get(h, '<not in old lock at all>')[:120]}")

# 新 requirements.txt 必须仍能被 Linux/py3.13 满足：检查每个包的剩余 hash 里
# 至少有非 cp314 的轮子（说明保留了解释器无关或 cp313 的目标）。
new_req = (REPO / "requirements.txt").read_text(encoding="utf-8")
new_lock = (REPO / "uv.lock").read_text(encoding="utf-8")
print()
print("new requirements.txt sha256 lines:", len(re.findall(r"--hash=sha256:", new_req)))
print("new uv.lock still has cp313 wheels:", "cp313" in new_lock)
print("new uv.lock still has cp314 wheels:", "cp314" in new_lock)
