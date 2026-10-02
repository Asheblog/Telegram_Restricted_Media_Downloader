import ast, os
ROOT = r"E:\codebase\tgbot"
print("=== 1. WebUiServer.__init__ 参数数 ===")
srv = open(os.path.join(ROOT, "module/adapters/webui/server.py"), encoding="utf-8").read()
t = ast.parse(srv)
for n in t.body:
    if isinstance(n, ast.ClassDef) and n.name == "WebUiServer":
        for m in n.body:
            if isinstance(m, (ast.FunctionDef,)) and m.name == "__init__":
                args = [a.arg for a in m.args.args] + [a.arg for a in m.args.kwonlyargs]
                args = [a for a in args if a != "self"]
                print(f"  __init__ L{m.lineno}-{m.end_lineno}: {len(args)} params")
                print("   ", args)

print("\n=== 2. handlers/*.py 顶层函数数 ===")
hd = os.path.join(ROOT, "module/adapters/webui/handlers")
tot = 0
for f in sorted(os.listdir(hd)):
    if not f.endswith(".py") or f == "__init__.py":
        continue
    tt = ast.parse(open(os.path.join(hd, f), encoding="utf-8").read())
    fns = [x for x in tt.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]
    tot += len(fns)
    print(f"  {f}: {len(fns)}  {[x.name for x in fns]}")
print(f"  TOTAL top-level handler functions = {tot}")

print("\n=== 3. _ensure_transfer_store 实现 ===")
ops = open(os.path.join(ROOT, "module/adapters/webui/operations.py"), encoding="utf-8").read().splitlines()
for i, l in enumerate(ops[105:130], 106):
    print(f"  {i}: {l}")
