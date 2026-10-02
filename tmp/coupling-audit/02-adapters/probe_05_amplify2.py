import subprocess, os, re, collections, json
ROOT = r"E:\codebase\tgbot"
OUT = os.path.join(ROOT, "tmp", "coupling-audit", "02-adapters")
def git(*a):
    return subprocess.run(["git"]+list(a), cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout

REFACTOR = "187d1d8"   # refactor(module): 完成架构解耦 Phase 3-6 并加架构守卫

LAYER = [
    ("module/adapters/webui", "adapters/webui"),
    ("module/adapters/bot", "adapters/bot"),
    ("module/adapters/pikpak", "adapters/pikpak"),
    ("module/adapters", "adapters/other"),
    ("module/transfer", "domain.transfer"),
    ("module/watches", "domain.watches"),
    ("module/pikpak", "domain.pikpak"),
    ("module/persistence", "domain.persistence"),
    ("module/domain", "domain.models"),
    ("module/core", "domain.core"),
    ("module/media", "domain.media"),
    ("module/utils", "utils"),
    ("module/infra", "infra"),
    ("module/app", "app.host"),
    ("module/", "domain.other"),
    ("unit_tests", "tests"),
    ("docs", "docs"),
    ("frontend", "frontend"),
]
def layer_of(p):
    for pre, n in LAYER:
        if p.startswith(pre): return n
    return "root.other"

lines = []
def w(s=""):
    lines.append(s)

# ---- post-refactor commits ----
post = git("log", "--format=%H\t%ad\t%s", "--date=short", f"{REFACTOR}..HEAD").strip().splitlines()
w(f"# post-refactor commits: {len(post)}  (range {REFACTOR}..HEAD)\n")
w("=" * 100)
for row in post:
    sha, date, subj = row.split("\t", 2)
    ss = git("show", "--shortstat", "--format=", sha).strip()
    stat = git("show", "--stat", "--format=", sha)
    files = [l.split("|")[0].strip() for l in stat.splitlines() if "|" in l]
    layers = collections.Counter(layer_of(f) for f in files)
    w(f"\n### {sha[:7]} {date}  {subj}")
    w(f"    shortstat: {ss}")
    w(f"    files={len(files)}  layers={len(layers)}  {dict(layers)}")
    for f in files:
        w(f"       - {f}")

# ---- aggregate over last 40 non-chore commits ----
w("\n" + "=" * 100)
w("# AGGREGATE over last 40 non-chore commits\n")
log = git("log", "--format=%H\t%s", "-60").strip().splitlines()
recs = []
for row in log:
    sha, subj = row.split("\t", 1)
    if re.match(r"^(chore|docs)", subj):
        continue
    stat = git("show", "--stat", "--format=", sha)
    files = [l.split("|")[0].strip() for l in stat.splitlines() if "|" in l]
    if not files:
        continue
    layers = collections.Counter(layer_of(f) for f in files)
    code = [f for f in files if f.endswith((".py", ".js", ".html", ".css", ".toml"))]
    recs.append({"sha": sha, "subj": subj, "n": len(files), "ncode": len(code),
                 "nlayers": len(layers), "layers": sorted(layers)})
    if len(recs) >= 40:
        break

w(f"sampled commits (non-chore, has file changes): {len(recs)}")
ns = [r["n"] for r in recs]
w(f"files/commit: sum={sum(ns)} mean={sum(ns)/len(ns):.2f} median={sorted(ns)[len(ns)//2]} min={min(ns)} max={max(ns)}")
cross = [r for r in recs if r["nlayers"] >= 2]
w(f"commits touching >=2 layers: {len(cross)}/{len(recs)} = {100*len(cross)/len(recs):.1f}%")
cross3 = [r for r in recs if r["nlayers"] >= 3]
w(f"commits touching >=3 layers: {len(cross3)}/{len(recs)} = {100*len(cross3)/len(recs):.1f}%")
w("\nper-commit detail (sha files codefiles layers subject):")
for r in recs:
    w(f"  {r['sha'][:7]}  files={r['n']:3d} code={r['ncode']:3d} layers={r['nlayers']}  {','.join(r['layers'])}  | {r['subj']}")

# ---- how often do adapter edits co-occur with domain edits ----
w("\n" + "=" * 100)
w("# co-occurrence: adapter-touching commits that ALSO touch non-adapter domain code")
adap = [r for r in recs if any(l.startswith("adapters") for l in r["layers"])]
both = [r for r in adap if any(not l.startswith("adapters") and l not in ("tests", "docs", "root.other") for l in r["layers"])]
w(f"commits touching adapters: {len(adap)}; of those also touching domain/other layers: {len(both)} = {100*len(both)/max(1,len(adap)):.1f}%")
for r in both:
    w(f"  {r['sha'][:7]} files={r['n']:3d} layers={r['nlayers']}  {r['subj']}")

# ---- verbatim raw stats for the 3 headline commits ----
w("\n" + "=" * 100)
w("# VERBATIM git show --stat for headline commits")
for sha in ["5538e56", "e0b739d", "523df22", "a3dcbf9", "b352fc3"]:
    w(f"\n$ git show --stat {sha}")
    w(git("show", "--stat", sha).rstrip())

open(os.path.join(OUT, "amplify.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("wrote amplify.txt lines:", len(lines))
print("\n".join(lines[:6]))
