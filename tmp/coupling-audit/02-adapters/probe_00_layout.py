import ast, os, sys, json, collections

ROOT = r"E:\codebase\tgbot"

def count_lines(p):
    with open(p, "rb") as f:
        return sum(1 for _ in f)

targets = [
    r"module\adapters\webui\operations.py",
    r"module\adapters\webui\server.py",
    r"module\adapters\bot\bot.py",
    r"module\adapters\bot\callback_handler.py",
    r"module\ports.py",
    r"module\adapters\pikpak\integration.py",
]
print("== file sizes ==")
for t in targets:
    p = os.path.join(ROOT, t)
    if os.path.exists(p):
        print(f"{t}: {count_lines(p)} lines, {os.path.getsize(p)} bytes")
    else:
        print(f"{t}: MISSING")

print()
print("== adapters tree ==")
for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "module", "adapters")):
    dirnames[:] = [d for d in dirnames if d != "__pycache__"]
    rel = os.path.relpath(dirpath, ROOT)
    for fn in sorted(filenames):
        if fn.endswith(".py"):
            p = os.path.join(dirpath, fn)
            print(f"{rel}\\{fn}\t{count_lines(p)}")

print()
print("== top-level classes in operations.py ==")
p = os.path.join(ROOT, targets[0])
tree = ast.parse(open(p, encoding="utf-8").read())
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        meths = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        print(f"class {node.name}: lines {node.lineno}-{node.end_lineno}, methods={len(meths)}")
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        print(f"func {node.name}: lines {node.lineno}-{node.end_lineno}")
