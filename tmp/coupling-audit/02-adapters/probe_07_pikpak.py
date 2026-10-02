import ast, os, re, collections
ROOT = r"E:\codebase\tgbot"
OUT = os.path.join(ROOT, "tmp", "coupling-audit", "02-adapters")
lines = []
def w(s=""): lines.append(s)

FILES = [
    "module/adapters/webui/archive_author_ops.py",
    "module/adapters/webui/archive_author_jobs.py",
    "module/adapters/webui/system_log_archive_retry_ops.py",
    "module/adapters/pikpak/archive_author.py",
    "module/adapters/pikpak/archive.py",
    "module/adapters/pikpak/integration.py",
]

w("=" * 95)
w("# PRIVATE host-method dependency per file (adapter calling underscore-prefixed host API)")
w("=" * 95)
summary = {}
for rel in FILES:
    p = os.path.join(ROOT, rel)
    src = open(p, encoding="utf-8").read()
    t = ast.parse(src)
    # find the attribute chains that look like host access: self._host.X  /  self.host.X / self.X where X starts with _
    priv, pub = collections.Counter(), collections.Counter()
    for node in ast.walk(t):
        if isinstance(node, ast.Attribute):
            base = node.value
            if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name) and base.value.id == "self" \
               and base.attr in ("_host", "host", "_bot", "_downloader", "_app", "downloader"):
                (priv if node.attr.startswith("_") else pub)[node.attr] += 1
    # also bare self.<priv> that are NOT methods defined in the file (inherited/expected from host)
    defined = set()
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(n.name)
    bare = collections.Counter()
    for node in ast.walk(t):
        if isinstance(node, ast.Attribute) and node.attr.startswith("_") and \
           isinstance(node.value, ast.Name) and node.value.id == "self":
            if node.attr not in defined:
                bare[node.attr] += 1
    summary[rel] = (priv, pub, bare)
    w(f"\n--- {rel}  ({len(src.splitlines())} lines)")
    w(f"  host.<x> PUBLIC called : {len(pub)} distinct -> {dict(pub)}")
    w(f"  host.<x> PRIVATE called: {len(priv)} distinct -> {dict(priv)}")
    w(f"  self.<_x> NOT defined in this file (inherited/host contract): {len(bare)} distinct -> {dict(bare)}")

# ---------- integration.py: host surface required ----------
w("\n" + "=" * 95)
w("# integration.py — class structure + host surface")
w("=" * 95)
p = os.path.join(ROOT, "module/adapters/pikpak/integration.py")
t = ast.parse(open(p, encoding="utf-8").read())
for n in t.body:
    if isinstance(n, ast.ClassDef):
        ms = [m for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
        w(f"class {n.name}({', '.join(ast.unparse(b) for b in n.bases)}) L{n.lineno}-{n.end_lineno} methods={len(ms)}")
        w("   " + ", ".join(m.name for m in ms))

# ---------- cross-adapter: who calls host private methods? ----------
w("\n" + "=" * 95)
w("# REPO-WIDE: calls to the two named private host methods")
w("=" * 95)
for pat in ["_ensure_transfer_store", "_run_telegram_coro", "_ensure_media_manager", "_ensure_watch_applicator"]:
    w(f"\n### {pat}")
    for dp, dn, fn in os.walk(os.path.join(ROOT, "module")):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for f in sorted(fn):
            if not f.endswith(".py"): continue
            fp = os.path.join(dp, f)
            s = open(fp, encoding="utf-8").read()
            for i, line in enumerate(s.splitlines(), 1):
                if pat in line:
                    w(f"  {os.path.relpath(fp, ROOT).replace(chr(92),'/'):58s}:{i}: {line.strip()[:110]}")

open(os.path.join(OUT, "pikpak.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("wrote pikpak.txt", len(lines), "lines")
