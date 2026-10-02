import ast, os, re, collections
ROOT = r"E:\codebase\tgbot"
OUT = os.path.join(ROOT, "tmp", "coupling-audit", "02-adapters")
lines = []
def w(s=""): lines.append(s)

ops = open(os.path.join(ROOT, "module/adapters/webui/operations.py"), encoding="utf-8").read()
srv = open(os.path.join(ROOT, "module/adapters/webui/server.py"), encoding="utf-8").read()
ports = open(os.path.join(ROOT, "module/ports.py"), encoding="utf-8").read()

def cls_ast(src, name):
    for n in ast.parse(src).body:
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n

mixin = cls_ast(ops, "WebOperationsMixin")
server = cls_ast(srv, "WebUiServer")
mnames = {m.name for m in mixin.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
snames = {m.name for m in server.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
overlap = sorted(mnames & snames)
w(f"WebOperationsMixin public+private methods : {len(mnames)}")
w(f"WebUiServer methods                      : {len(snames)}")
w(f"NAME COLLISIONS (same method on both)     : {len(overlap)}")
w(f"  {overlap}")
w("")
w("=> these names exist as a thin mixin shim AND as a real impl on WebUiServer")

# delegate tuple vs protocol
mt = re.search(r"_WEB_UI_DELEGATE_METHODS\s*=\s*\((.*?)\n\)", ops, re.S)
names = re.findall(r"'([^']+)'", mt.group(1)) if mt else []
w(f"\n_WEB_UI_DELEGATE_METHODS entries (dynamic setattr facade surface): {len(names)}")

p = ast.parse(ports)
protos = {}
for n in p.body:
    if isinstance(n, ast.ClassDef):
        mem = set()
        for s in n.body:
            if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name): mem.add(s.target.id)
            elif isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)): mem.add(s.name)
        protos[n.name] = mem
for k, v in protos.items():
    w(f"  Protocol {k}: {len(v)} members")

webproto = protos.get("IWebUiOperations", set())
w(f"\nIWebUiOperations members           : {len(webproto)} -> {sorted(webproto)}")
w(f"delegate tuple NOT in Protocol     : {sorted(set(names) - webproto)}")
w(f"Protocol members NOT in tuple      : {sorted(webproto - set(names))}")

# Are all delegate-tuple names actually present on the mixin? (silent-failure surface)
w(f"\ndelegate tuple names missing from WebOperationsMixin: {sorted(set(names) - mnames)}")
w(f"=> getattr(self._host, name) at operations.py:1891 would raise AttributeError at CALL time, not import time")

# getattr-based dynamic dispatch sites in webui/
w("\n" + "=" * 90)
w("# dynamic getattr dispatch sites (defeat static typing)")
w("=" * 90)
tot = 0
for dp, dn, fn in os.walk(os.path.join(ROOT, "module/adapters")):
    dn[:] = [d for d in dn if d != "__pycache__"]
    for f in sorted(fn):
        if not f.endswith(".py"): continue
        fp = os.path.join(dp, f)
        rel = os.path.relpath(fp, ROOT).replace("\\", "/")
        for i, line in enumerate(open(fp, encoding="utf-8").read().splitlines(), 1):
            if re.search(r"getattr\(\s*(self\.operations|host|self\._host|self\.downloader|self\._downloader)", line):
                w(f"{rel}:{i}: {line.strip()[:120]}")
                tot += 1
w(f"\ntotal getattr-on-host dispatch sites in adapters/: {tot}")

# host attribute contract size: union of getattr(host,'x') / host.x  / self.x-on-mixin
w("\n" + "=" * 90)
w("# host attribute contract size implied by adapters")
w("=" * 90)
hostattrs = set()
for dp, dn, fn in os.walk(os.path.join(ROOT, "module/adapters")):
    dn[:] = [d for d in dn if d != "__pycache__"]
    for f in sorted(fn):
        if not f.endswith(".py"): continue
        s = open(os.path.join(dp, f), encoding="utf-8").read()
        hostattrs |= set(re.findall(r"getattr\(\s*host\s*,\s*'([A-Za-z_][A-Za-z0-9_]*)'", s))
        hostattrs |= set(re.findall(r"host\.([A-Za-z_][A-Za-z0-9_]*)", s))
        hostattrs |= set(re.findall(r"self\._host\.([A-Za-z_][A-Za-z0-9_]*)", s))
w(f"distinct host.<attr> contract required by module/adapters/: {len(hostattrs)}")
w("  " + ", ".join(sorted(hostattrs)))

# composition_root host surface
cr = os.path.join(ROOT, "module/composition_root.py")
if os.path.exists(cr):
    s = open(cr, encoding="utf-8").read()
    w(f"\nmodule/composition_root.py: {len(s.splitlines())} lines")
    for n in ast.parse(s).body:
        if isinstance(n, ast.ClassDef):
            ms = [m for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            w(f"  class {n.name}({', '.join(ast.unparse(b) for b in n.bases)}) L{n.lineno}-{n.end_lineno} methods={len(ms)}")
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            w(f"  func {n.name} L{n.lineno}-{n.end_lineno}")

open(os.path.join(OUT, "surfaces.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("wrote surfaces.txt", len(lines))
