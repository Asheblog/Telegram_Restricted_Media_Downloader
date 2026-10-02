# coding=UTF-8
"""Change amplification: how many files/layers does a typical commit touch?

Read-only git queries. Layers are derived from module/<layer>/ prefixes.
"""
import collections
import pathlib
import re
import subprocess

REPO = pathlib.Path(r"E:\codebase\tgbot")
LAYERS = ("adapters", "core", "domain", "infra", "persistence", "transfer", "utils")


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=str(REPO), capture_output=True, check=True
    ).stdout.decode("utf-8", "replace")


log = git("log", "--pretty=format:%H\x1f%s", "-n", "120")
commits = [line.split("\x1f") for line in log.splitlines() if "\x1f" in line]
print(f"analyzed commits: {len(commits)}")

rows = []
for sha, subject in commits:
    files = [f for f in git("show", "--pretty=format:", "--name-only", sha).split("\n") if f.strip()]
    mod_files = [f for f in files if f.startswith("module/")]
    test_files = [f for f in files if f.startswith("unit_tests/")]
    layers = set()
    for f in mod_files:
        parts = f.split("/")
        if len(parts) > 2 and parts[1] in LAYERS:
            layers.add(parts[1])
        else:
            layers.add("top")
    rows.append({
        "sha": sha[:8], "subject": subject[:60], "files": len(files),
        "mod": len(mod_files), "test": len(test_files), "layers": sorted(layers),
    })

by_files = sorted(rows, key=lambda r: -r["files"])
print()
print("=== top 12 commits by file count ===")
for r in by_files[:12]:
    print(f"  {r['files']:3d} files (module {r['mod']:2d}, tests {r['test']:2d})  layers={','.join(r['layers'])}")
    print(f"        {r['sha']}  {r['subject']}")

mods = [r for r in rows if r["mod"] > 0]
multi_layer = [r for r in mods if len(r["layers"]) > 1]
touching_tests = [r for r in rows if r["test"] > 0]
print()
print("=== aggregate over commits touching module/ ===")
print(f"  commits touching module/:            {len(mods)} / {len(rows)}")
print(f"  ... that span >1 layer:              {len(multi_layer)} ({100*len(multi_layer)//max(len(mods),1)}%)")
print(f"  ... that also touch unit_tests/:     {len(touching_tests)} ({100*len(touching_tests)//max(len(rows),1)}%)")
avg_mod = sum(r['mod'] for r in mods) / max(len(mods), 1)
avg_all = sum(r['files'] for r in rows) / max(len(rows), 1)
print(f"  mean files touched per commit:       {avg_all:.1f}")
print(f"  mean module files per commit:        {avg_mod:.1f}")

print()
print("=== layer co-change matrix (which layer pairs move together) ===")
pairs = collections.Counter()
for r in mods:
    ls = [l for l in r["layers"]]
    for i, a in enumerate(ls):
        for b in ls[i + 1:]:
            pairs[tuple(sorted((a, b)))] += 1
for (a, b), n in pairs.most_common(15):
    print(f"  {n:3d}  {a} <-> {b}")

print()
print("=== 单层内修改占比（真正的局部改动）===")
single = [r for r in mods if len(r["layers"]) == 1 and r["test"] == 0]
print(f"  {len(single)} / {len(mods)} commits touched exactly one layer and no tests")
for r in sorted(single, key=lambda r: -r["mod"])[:8]:
    print(f"      {r['mod']:2d} module files  {r['sha']}  {r['subject']}")
