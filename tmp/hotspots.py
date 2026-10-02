# coding=UTF-8
"""Which module files change most often, and how often do the God-host files move?"""
import collections
import pathlib
import subprocess

REPO = pathlib.Path(r"E:\codebase\tgbot")
N = 200


def git(*args):
    return subprocess.run(["git", *args], cwd=str(REPO), capture_output=True, check=True)\
        .stdout.decode("utf-8", "replace")


raw = git("log", "--pretty=format:%H", "-n", str(N), "--", "module/").split()
counts = collections.Counter()
cochange_with_downloader = 0
cochange_host_group = 0
HOST_GROUP = {"module/downloader.py", "module/composition_root.py"}

for sha in raw:
    files = [
        f for f in git("show", "--pretty=format:", "--name-only", sha).split("\n") if f.strip()
    ]
    mods = [f for f in files if f.startswith("module/")]
    counts.update(mods)
    if "module/downloader.py" in mods and len(mods) > 1:
        cochange_with_downloader += 1
    if HOST_GROUP & set(mods) and len(mods) > 1:
        cochange_host_group += 1

print(f"=== top 25 hottest module files over last {len(raw)} commits touching module/ ===")
for f, n in counts.most_common(25):
    bar = "#" * min(n, 40)
    print(f"  {n:3d}  {f:<60} {bar}")

print()
print(f"commits in window: {len(raw)}")
print(f"downloader.py changed alongside other module files: {cochange_with_downloader}")
print(f"downloader.py or composition_root.py + others:      {cochange_host_group}")
print(f"distinct module files touched: {len(counts)}")
print()
print("=== share of all module-file edits that land in the top 10 files ===")
top10 = sum(n for _, n in counts.most_common(10))
total = sum(counts.values())
print(f"  {top10}/{total} = {100*top10//total}%")
