import ast, os, re, collections
ROOT = r"E:\codebase\tgbot"
OUT = os.path.join(ROOT, "tmp", "coupling-audit", "02-adapters")
lines = []
def w(s=""): lines.append(s)

WEBUI = os.path.join(ROOT, "module", "adapters", "webui")
# ---------- A. how handlers obtain `operations` ----------
w("=" * 90)
w("# A. handler -> operations access pattern")
w("=" * 90)
pat = re.compile(r"\b(server|handler)\.(operations|web_operations|ops)\b|\.operations\b")
tot = 0
per = collections.Counter()
for dp, dn, fn in os.walk(WEBUI):
    dn[:] = [d for d in dn if d != "__pycache__"]
    for f in sorted(fn):
        if not f.endswith(".py"):
            continue
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        if rel.endswith("assets.py") or rel.endswith("build_frontend.py") or rel.endswith("download_fonts.py"):
            continue
        src = open(p, encoding="utf-8").read()
        for i, line in enumerate(src.splitlines(), 1):
            if re.search(r"\.operations\b|web_operations|server\.ops\b", line):
                w(f"{rel}:{i}: {line.strip()}")
                per[rel] += 1
                tot += 1
w(f"\ntotal `operations` access sites in webui/: {tot}")
w(f"by file: {dict(per)}")

# ---------- B. handler signature / type annotations ----------
w("\n" + "=" * 90)
w("# B. handler function signatures (first line only) — do they name a Protocol?")
w("=" * 90)
hd = os.path.join(WEBUI, "handlers")
for f in sorted(os.listdir(hd)):
    if not f.endswith(".py") or f == "__init__.py":
        continue
    p = os.path.join(hd, f)
    t = ast.parse(open(p, encoding="utf-8").read())
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = f"def {n.name}({ast.unparse(n.args)})"
            w(f"handlers/{f}:{n.lineno}: {sig}")

# ---------- C. does the facade/mixin get used via Protocol at all ----------
w("\n" + "=" * 90)
w("# C. WebOperationsFacade / WebOperationsMixin wiring")
w("=" * 90)
for rel in ["module/adapters/webui/server.py", "module/adapters/webui/operations.py"]:
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    for i, line in enumerate(src.splitlines(), 1):
        if re.search(r"WebOperationsFacade|WebOperationsMixin|WebOperations\b|IWebUiOperations", line):
            w(f"{rel}:{i}: {line.strip()}")

# ---------- D. server.py class structure + god-size ----------
w("\n" + "=" * 90)
w("# D. server.py classes / methods")
w("=" * 90)
sp = os.path.join(WEBUI, "server.py")
t = ast.parse(open(sp, encoding="utf-8").read())
for n in t.body:
    if isinstance(n, ast.ClassDef):
        ms = [m for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
        w(f"class {n.name}  lines {n.lineno}-{n.end_lineno}  methods={len(ms)}")
        for m in ms:
            w(f"    {m.name}  L{m.lineno}-{m.end_lineno} ({m.end_lineno-m.lineno+1})")
    elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        w(f"func {n.name}  L{n.lineno}-{n.end_lineno}")
w("\n# classes in operations.py / mixin base list")
t2 = ast.parse(open(os.path.join(WEBUI, "operations.py"), encoding="utf-8").read())
for n in t2.body:
    if isinstance(n, ast.ClassDef):
        w(f"class {n.name}({', '.join(ast.unparse(b) for b in n.bases)})  lines {n.lineno}-{n.end_lineno}")

open(os.path.join(OUT, "handlers.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("wrote handlers.txt", len(lines))
