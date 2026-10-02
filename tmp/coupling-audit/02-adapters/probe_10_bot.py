import ast, os, re, collections
ROOT = r"E:\codebase\tgbot"
OUT = os.path.join(ROOT, "tmp", "coupling-audit", "02-adapters")
lines = []
def w(s=""): lines.append(s)

w("=" * 90)
w("# 1. bot <-> downloader back-reference (who assigns .downloader / .bot)")
w("=" * 90)
for dp, dn, fn in os.walk(os.path.join(ROOT, "module")):
    dn[:] = [d for d in dn if d != "__pycache__"]
    for f in sorted(fn):
        if not f.endswith(".py"): continue
        fp = os.path.join(dp, f)
        rel = os.path.relpath(fp, ROOT).replace("\\", "/")
        for i, line in enumerate(open(fp, encoding="utf-8").read().splitlines(), 1):
            if re.search(r"\.downloader\s*=|\.bot\s*=\s*(self|bot\b)|downloader\.bot\b|bot\.downloader\b|downloader_ref\s*=", line):
                w(f"{rel}:{i}: {line.strip()[:120]}")

w("\n" + "=" * 90)
w("# 2. bot.py structure")
w("=" * 90)
bp = os.path.join(ROOT, "module/adapters/bot/bot.py")
bsrc = open(bp, encoding="utf-8").read()
bt = ast.parse(bsrc)
for n in bt.body:
    if isinstance(n, ast.ClassDef):
        ms = [m for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
        w(f"class {n.name}({', '.join(ast.unparse(b) for b in n.bases)}) L{n.lineno}-{n.end_lineno} methods={len(ms)}")
        big = sorted(ms, key=lambda m: m.end_lineno - m.lineno, reverse=True)[:12]
        for m in big:
            w(f"    {m.name:38s} L{m.lineno}-{m.end_lineno} ({m.end_lineno-m.lineno+1} lines)")
print("")

w("\n" + "=" * 90)
w("# 3. host attributes bot.py requires from the god host (self.<x> not defined locally)")
w("=" * 90)
defined = set()
for n in ast.walk(bt):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): defined.add(n.name)
assigned = set(re.findall(r"self\.([A-Za-z_][A-Za-z0-9_]*)\s*=", bsrc))
read = collections.Counter()
for node in ast.walk(bt):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        read[node.attr] += 1
missing = {k: v for k, v in read.items() if k not in defined and k not in assigned}
w(f"bot.py: self-defined attrs/methods = {len(defined)}, assigned = {len(assigned)}")
w(f"bot.py: reads self.<x> that are NEITHER defined NOR assigned here = {len(missing)}")
for k, v in sorted(missing.items(), key=lambda kv: -kv[1]):
    w(f"    self.{k}  (read {v}x)")
w(f"\nbot.py total distinct self.<x> read = {len(read)}")
w(f"top 25: {read.most_common(25)}")

w("\n" + "=" * 90)
w("# 4. architecture guard scope")
w("=" * 90)
ag = os.path.join(ROOT, "unit_tests/architecture_guard_case.py")
s = open(ag, encoding="utf-8").read()
w(f"{os.path.relpath(ag, ROOT)}: {len(s.splitlines())} lines")
for i, line in enumerate(s.splitlines(), 1):
    if re.search(r"^\s*(def |class |#\s*(Test|Rule|FORBID|ALLOW))|assert|Protocol|isinstance", line) and not line.strip().startswith("'''"):
        t = line.strip()
        if t.startswith("assert") or t.startswith("def ") or t.startswith("class ") or "Protocol" in t:
            w(f"  {i}: {t[:130]}")

open(os.path.join(OUT, "bot.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("wrote bot.txt", len(lines))
