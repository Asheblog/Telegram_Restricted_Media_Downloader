"""检查两个 venv 里 PyYAML C 扩展的构建元数据，判定 AV 根因。"""
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for v, tag in ((".venv", "cp314"), (".venv313", "cp313")):
    p = os.path.join(ROOT, v, "Lib", "site-packages", "yaml", f"_yaml.{tag}-win_amd64.pyd")
    if not os.path.exists(p):
        print(v, "missing", p)
        continue
    b = open(p, "rb").read()
    strs = {s.decode("ascii", "replace") for s in re.findall(rb"[ -~]{4,}", b)}
    vers = sorted({s for s in strs if re.fullmatch(r"3\.\d+\.\d+[a-z0-9]*", s)})
    tags = sorted({s for s in strs if s.startswith("cpython-3") or s.startswith("cp3")})[:8]
    dll = sorted({s for s in strs if s.lower().endswith(".dll")})[:8]
    print(f"{v}: size={os.path.getsize(p)}")
    print(f"   version_strings={vers}")
    print(f"   abi_tag_strings={tags}")
    print(f"   dll_refs={dll}")
    di = glob.glob(os.path.join(ROOT, v, "Lib", "site-packages", "*yaml*dist-info"))
    di += glob.glob(os.path.join(ROOT, v, "Lib", "site-packages", "*PyYAML*"))
    print(f"   dist-info={[os.path.basename(x) for x in di]}")
    for d in di:
        m = os.path.join(d, "METADATA")
        if os.path.exists(m):
            for line in open(m, encoding="utf-8", errors="replace").read().splitlines()[:8]:
                if line.startswith(("Name:", "Version:")):
                    print("     ", line)
    # RECORD 中 _yaml 的 hash 行
    rec = os.path.join(d, "RECORD") if di else None
    if rec and os.path.exists(rec):
        for line in open(rec, encoding="utf-8", errors="replace"):
            if "_yaml" in line:
                print("      RECORD:", line.strip())
