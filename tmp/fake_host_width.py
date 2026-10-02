# coding=UTF-8
"""How wide are the test doubles? A seam is only real if fakes stay small.

Measures, for every unit test, the class-based fakes and how many attributes
they must provide to stand in for the host.
"""
import ast
import pathlib
import re

TESTS = pathlib.Path(r"E:\codebase\tgbot\unit_tests")
results = []

for path in sorted(TESTS.glob("*.py")):
    src = path.read_text(encoding="utf-8")
    if "class " not in src:
        continue
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # fakes are usually named Fake*/Stub*/Dummy*/Harness*/_Host*
        if not re.match(r"^(Fake|Stub|Dummy|Harness|Mock|_Fake|_Stub)", node.name):
            continue
        methods = [
            c.name for c in node.body
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        attrs = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assign):
                for t in sub.targets:
                    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                        attrs.add(t.attr)
            elif isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "self":
                attrs.add(sub.attr)
        results.append((len(methods), len(attrs), path.name, node.name, node.lineno))

results.sort(reverse=True)
print("=== test doubles: width of fakes (methods, attrs, file, class, line) ===")
for m, a, f, c, ln in results:
    print(f"  methods={m:3d} attrs={a:3d}  {f}:{ln}  class {c}")

print()
print(f"total fake classes detected: {len(results)}")
big = [r for r in results if r[0] + r[1] >= 15]
print(f"fakes with >=15 members (must mirror a large host surface): {len(big)}")

print()
print("=== how do tests obtain the host? (patterns) ===")
pat = {
    "object.__new__(TelegramRestrictedMediaDownloader)": 0,
    "TelegramRestrictedMediaDownloader()": 0,
    "MagicMock": 0,
    "TrmdCompositionRoot": 0,
    "types.SimpleNamespace": 0,
}
for path in sorted(TESTS.glob("*.py")):
    src = path.read_text(encoding="utf-8")
    for k in pat:
        pat[k] += src.count(k)
for k, v in pat.items():
    print(f"  {v:4d}  {k}")
