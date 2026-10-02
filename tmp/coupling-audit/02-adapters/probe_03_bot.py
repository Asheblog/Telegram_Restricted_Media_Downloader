import ast, os, re, collections

ROOT = r"E:\codebase\tgbot"

# ---------- 1. IBotCallbackHost member usage ----------
ports = open(os.path.join(ROOT, "module", "ports.py"), encoding="utf-8").read()
pt = ast.parse(ports)
proto = None
for n in pt.body:
    if isinstance(n, ast.ClassDef) and n.name == "IBotCallbackHost":
        proto = n
attrs, meths = [], []
for s in proto.body:
    if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
        attrs.append(s.target.id)
    elif isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
        meths.append(s.name)
members = attrs + meths
print(f"IBotCallbackHost: {len(attrs)} data attrs + {len(meths)} methods = {len(members)} members")
print("  attrs  :", attrs)
print("  methods:", meths)

ch = open(os.path.join(ROOT, "module", "adapters", "bot", "callback_handler.py"), encoding="utf-8").read()
used, unused = [], []
for m in members:
    # any usage of .m  (attribute access) in callback_handler
    if re.search(r"\.\s*" + re.escape(m) + r"\b", ch):
        used.append(m)
    else:
        unused.append(m)
print(f"\n  USED in callback_handler.py: {len(used)} -> {used}")
print(f"  NEVER used: {len(unused)} -> {unused}")
# getattr-style dynamic access
print("  getattr( usages in callback_handler.py:", len(re.findall(r"getattr\(", ch)))
print("  self.host refs:", len(re.findall(r"\bhost\.", ch)))

# what the handler actually touches on host
touched = collections.Counter(re.findall(r"(?:self\.)?host\.([A-Za-z_][A-Za-z0-9_]*)", ch))
print(f"\n  distinct host.<x> touched in callback_handler.py: {len(touched)}")
print("  members declared in Protocol but NOT touched:", sorted(set(members) - set(touched)))
print("  touched but NOT declared in Protocol:", sorted(set(touched) - set(members)))

# ---------- 2. IBotCallbackHost conformance ----------
print("\n=== does anything isinstance-check the protocols? ===")
hits = 0
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in (".git", "__pycache__", ".venv", "node_modules", "tmp", "data")]
    for f in fn:
        if not f.endswith(".py"):
            continue
        p = os.path.join(dp, f)
        try:
            s = open(p, encoding="utf-8").read()
        except Exception:
            continue
        for i, line in enumerate(s.splitlines(), 1):
            if re.search(r"isinstance\s*\(.*(IWebUiOperations|IWatchOps|ITaskOps|IMediaOps|IStatsOps|IUploadOps|IBotCallbackHost|IUploadContext|IDiagnosticPort)", line) or \
               re.search(r"(cast)\s*\(\s*(IWebUiOperations|IBotCallbackHost|IUploadContext)", line):
                print(f"{os.path.relpath(p, ROOT)}:{i}: {line.strip()}")
                hits += 1
print("total isinstance/cast protocol hits:", hits)

# ---------- 3. bot <-> downloader back reference ----------
print("\n=== bot.downloader back-reference ===")
for rel in ["module/adapters/bot/bot.py"]:
    p = os.path.join(ROOT, rel)
    s = open(p, encoding="utf-8").read()
    for i, line in enumerate(s.splitlines(), 1):
        if re.search(r"\bdownloader\b", line):
            print(f"{rel}:{i}: {line.rstrip()}")
