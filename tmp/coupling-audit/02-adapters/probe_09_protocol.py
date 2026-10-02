import ast, os, re, collections
ROOT = r"E:\codebase\tgbot"
OUT = os.path.join(ROOT, "tmp", "coupling-audit", "02-adapters")
lines = []
def w(s=""): lines.append(s)

ports = open(os.path.join(ROOT, "module/ports.py"), encoding="utf-8").read()
pt = ast.parse(ports)
proto_members, proto_bases = {}, {}
for n in pt.body:
    if isinstance(n, ast.ClassDef):
        mem = set()
        for s in n.body:
            if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name): mem.add(s.target.id)
            elif isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)): mem.add(s.name)
        proto_members[n.name] = mem
        proto_bases[n.name] = [ast.unparse(b) for b in n.bases if ast.unparse(b) != "Protocol"]

def closure(name, seen=None):
    seen = seen or set()
    out = set(proto_members.get(name, set()))
    for b in proto_bases.get(name, []):
        out |= closure(b, seen)
    return out

full = closure("IWebUiOperations")
w(f"IWebUiOperations EFFECTIVE (inherited) surface = {len(full)} members")
w(f"  {sorted(full)}")

ops = open(os.path.join(ROOT, "module/adapters/webui/operations.py"), encoding="utf-8").read()
mt = re.search(r"_WEB_UI_DELEGATE_METHODS\s*=\s*\((.*?)\n\)", ops, re.S)
names = re.findall(r"'([^']+)'", mt.group(1))
w(f"\nWebOperationsFacade actual surface (delegate tuple) = {len(names)}")
w(f"  facade methods NOT covered by IWebUiOperations Protocol: {len(set(names)-full)}")
w(f"  {sorted(set(names) - full)}")
w(f"  Protocol members not implemented by facade: {sorted(full - set(names))}")
w(f"  => Protocol covers {100*len(set(names)&full)/len(set(names)):.1f}% of the facade surface")

# ---- the 32 collisions: real impl or delegation? ----
def cls_ast(src, name):
    for n in ast.parse(src).body:
        if isinstance(n, ast.ClassDef) and n.name == name: return n
mixin = cls_ast(ops, "WebOperationsMixin")
srv = open(os.path.join(ROOT, "module/adapters/webui/server.py"), encoding="utf-8").read()
server = cls_ast(srv, "WebUiServer")
mnames = {m.name: m for m in mixin.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
snodes = {m.name: m for m in server.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
coll = sorted(set(mnames) & set(snodes))

w("\n" + "=" * 90)
w(f"# classifying the {len(coll)} name collisions (mixin shim vs WebUiServer impl)")
w("=" * 90)
real, deleg = [], []
for n in coll:
    m = snodes[n]
    body = ast.get_source_segment(srv, m)
    is_deleg = bool(re.search(r"self\._operation\(|self\.operations\.", body))
    (deleg if is_deleg else real).append(n)
    tag = "DELEGATE->operations" if is_deleg else "REAL IMPL"
    w(f"  {n:42s} server L{m.lineno}-{m.end_lineno} ({m.end_lineno-m.lineno+1:3d} lines)  {tag}")

w(f"\n  server methods that DELEGATE to self.operations: {len(deleg)} -> {sorted(deleg)}")
w(f"  server methods with a REAL implementation      : {len(real)} -> {sorted(real)}")

# ---- HTTP-ness of operations.py: whole-file token census ----
w("\n" + "=" * 90)
w("# HTTP-ness census of operations.py (whole file)")
w("=" * 90)
toks = ["BaseHTTPRequestHandler", "self.headers", "self.wfile", "self.rfile", "urlparse", "parse_qs",
        "HTTPStatus", "send_response", "send_header", "end_headers", "json.dumps", "handler", "request", "parsed"]
for t in toks:
    w(f"  {t:28s}: {len(re.findall(re.escape(t), ops))}")
w("\n  -> the file has 0 HTTP primitives; it is a business-orchestration module living in adapters/")

open(os.path.join(OUT, "protocol.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("wrote protocol.txt", len(lines))
