import ast, os, json, re, collections

ROOT = r"E:\codebase\tgbot"
P = os.path.join(ROOT, "module", "adapters", "webui", "operations.py")
src = open(P, encoding="utf-8").read()
tree = ast.parse(src)
lines = src.splitlines()

def cls(name):
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None

# find all classes with methods (mixin + facade)
rows = []
for n in tree.body:
    if isinstance(n, ast.ClassDef):
        for m in n.body:
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                deco = [ast.unparse(d) for d in m.decorator_list]
                is_async = isinstance(m, ast.AsyncFunctionDef)
                # detect self.<attr> usage and returns
                body_src = ast.get_source_segment(src, m) or ""
                # HTTP-ish signals
                http_sig = bool(re.search(r"\b(handler|request|query|json_response|_send_json|urlparse|parse_qs|self\.send_|http_status|self\.headers|rfile|wfile)\b", body_src))
                has_await = "await " in body_src
                rows.append({
                    "cls": n.name, "name": m.name, "start": m.lineno, "end": m.end_lineno,
                    "nlines": m.end_lineno - m.lineno + 1, "async": is_async, "deco": deco,
                    "http_sig": http_sig, "await": has_await,
                    "args": [a.arg for a in m.args.args],
                })

for c in ("WebOperationsMixin", "WebOperationsFacade"):
    sub = [r for r in rows if r["cls"] == c]
    print(f"=== class {c}: {len(sub)} methods, lines {min(r['start'] for r in sub) if sub else '-'}-{max(r['end'] for r in sub) if sub else '-'}")
    print(f"    async={sum(1 for r in sub if r['async'])}  http-signal={sum(1 for r in sub if r['http_sig'])}")

print()
print("=== all methods (cls|name|lines|n|async|httpsig) ===")
for r in rows:
    print(f"{r['cls']}\t{r['name']}\t{r['start']}-{r['end']}\t{r['nlines']}\t{'A' if r['async'] else 's'}\t{'H' if r['http_sig'] else '-'}\t{','.join(r['deco'])}")

# duplicate names across mixins
print()
print("=== method name duplicates across classes ===")
cnt = collections.Counter(r["name"] for r in rows)
for k, v in cnt.most_common():
    if v > 1:
        print(k, v, [ (r['cls'], r['start']) for r in rows if r['name']==k])

json.dump(rows, open(os.path.join(ROOT, "tmp", "coupling-audit", "02-adapters", "ops_methods.json"), "w"), indent=1)
print("\nWROTE ops_methods.json count=", len(rows))
