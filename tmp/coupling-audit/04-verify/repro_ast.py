"""A4 独立复现脚本：AST 统计 6 项数值。

只读分析，不修改仓库。输出带原始证据片段。
运行: .venv\\Scripts\\python.exe tmp\\coupling-audit\\04-verify\\repro_ast.py
"""
from __future__ import annotations

import ast
import io
import os
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODULE = os.path.join(ROOT, "module")
OUT = io.StringIO()


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")


def rel(pth: str) -> str:
    return os.path.relpath(pth, ROOT).replace("\\", "/")


def parse(pth: str) -> ast.Module:
    with open(pth, "rb") as f:
        src = f.read()
    return ast.parse(src, filename=pth)


def all_py(root: str) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".ruff_cache"}]
        for fn in filenames:
            if fn.endswith(".py"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def modname(pth: str) -> str:
    r = os.path.relpath(pth, ROOT).replace("\\", "/")
    assert r.endswith(".py")
    r = r[:-3]
    if r.endswith("/__init__"):
        r = r[: -len("/__init__")]
    return r.replace("/", ".")


# ---------------------------------------------------------------- 1. import graph
class ImportCollector(ast.NodeVisitor):
    """收集每个模块的 import 目标（绝对 + 相对）。"""

    def __init__(self, owner: str, is_pkg: bool):
        self.owner = owner
        self.is_pkg = is_pkg
        self.targets: list[str] = []

    def visit_Import(self, node: ast.Import):
        for a in node.names:
            self.targets.append(a.name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.level == 0:
            if node.module:
                self.targets.append(node.module)
            return
        # 相对 import: level 层级。owner 为包时 base = owner，否则 base = owner 的父包
        parts = self.owner.split(".")
        if not self.is_pkg:
            parts = parts[:-1]
        # level=1 指向当前包
        up = node.level - 1
        if up > 0:
            parts = parts[:-up] if up <= len(parts) else []
        base = ".".join(parts)
        if node.module:
            base = base + "." + node.module if base else node.module
        if base:
            self.targets.append(base)

    def visit_If(self, node: ast.If):
        # TYPE_CHECKING 分支也计入（静态依赖）
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        self.generic_visit(node)


def build_graph():
    files = all_py(MODULE)
    mods = {modname(f): f for f in files}
    edges = defaultdict(set)
    raw_edges = defaultdict(list)  # (owner, target, lineno, kind)
    for m, f in mods.items():
        tree = parse(f)
        is_pkg = os.path.basename(f) == "__init__.py"
        c = ImportCollector(m, is_pkg)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                c.visit_Import(node)
                for a in node.names:
                    raw_edges[m].append((a.name, node.lineno, "Import"))
            elif isinstance(node, ast.ImportFrom):
                c.visit_ImportFrom(node)
                if node.level == 0:
                    tgt = node.module or ""
                else:
                    parts = m.split(".")
                    if not is_pkg:
                        parts = parts[:-1]
                    up = node.level - 1
                    if up > 0:
                        parts = parts[:-up] if up <= len(parts) else []
                    base = ".".join(parts)
                    tgt = (base + "." + node.module) if (base and node.module) else (base or node.module or "")
                raw_edges[m].append((tgt, node.lineno, f"From level={node.level}"))
    # 解析到真实模块（最长前缀匹配）
    for m, lst in raw_edges.items():
        for tgt, lineno, kind in lst:
            if not tgt:
                continue
            best = None
            for cand in mods:
                if tgt == cand or tgt.startswith(cand + "."):
                    if best is None or len(cand) > len(best):
                        best = cand
            if best is None:
                # 也许目标是包的顶层（module.x.y 但 y 是模块）
                continue
            if best != m:
                edges[m].add(best)
    return mods, edges, raw_edges


def tarjan(nodes, edges):
    index = {}
    low = {}
    on = {}
    stack = []
    sccs = []
    counter = [0]

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on[v] = True
        for w in edges.get(v, ()):
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif on.get(w):
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on[w] = False
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    sys.setrecursionlimit(100000)
    for n in sorted(nodes):
        if n not in index:
            strong(n)
    return sccs


# ---------------------------------------------------------------- helpers
def kw_getter_count(pth: str):
    """统计 composition_root.py 中关键字参数名以 _getter 结尾的实参。"""
    tree = parse(pth)
    hits = []  # (lineno, func_text, argname)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg and kw.arg.endswith("_getter"):
                    fn = node.func
                    if isinstance(fn, ast.Attribute):
                        fname = fn.attr
                    elif isinstance(fn, ast.Name):
                        fname = fn.id
                    else:
                        fname = "<expr>"
                    hits.append((node.lineno, fname, kw.arg))
    return hits


def host_attr_count(pth: str, attr: str = "_host"):
    """统计 host 属性访问次数，给出多种口径。"""
    tree = parse(pth)
    bare = []  # self._host（无后续属性）
    dotted = []  # self._host.X
    distinct = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
            inner = node.value
            if isinstance(inner.value, ast.Name) and inner.value.id == "self" and inner.attr == attr:
                dotted.append((node.lineno, node.attr))
                distinct.add(node.attr)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "self" and node.attr == attr:
                bare.append(node.lineno)
    return bare, dotted, distinct


def class_method_count(pth: str, cls: str):
    tree = parse(pth)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            funcs = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            nested = 0
            for n in ast.walk(node):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n not in funcs:
                    nested += 1
            names = [f.name for f in funcs]
            return funcs, nested, names
    return None, None, None


def internal_import_count_of(target_mod_files: list[str], all_mods: dict[str, str]):
    """统计给定文件集合里的 import 语句中指向 module.* 内部模块的条数（多口径）。"""
    res = {}
    stmts = 0
    names = 0
    distinct_targets = set()
    for f in target_mod_files:
        m = modname(f)
        tree = parse(f)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    stmts += 1
                    if a.name.startswith("module"):
                        names += 1
                        best = None
                        for cand in all_mods:
                            if a.name == cand or a.name.startswith(cand + "."):
                                if best is None or len(cand) > len(best):
                                    best = cand
                        if best:
                            distinct_targets.add(best)
            elif isinstance(node, ast.ImportFrom):
                stmts += 1
                if node.level > 0:
                    # 相对 import 视为内部
                    names += 1
                    parts = m.split(".")
                    if not os.path.basename(f) == "__init__.py":
                        parts = parts[:-1]
                    up = node.level - 1
                    if up > 0:
                        parts = parts[:-up] if up <= len(parts) else []
                    base = ".".join(parts)
                    tgt = (base + "." + node.module) if (base and node.module) else (base or node.module or "")
                    best = None
                    for cand in all_mods:
                        if tgt == cand or tgt.startswith(cand + "."):
                            if best is None or len(cand) > len(best):
                                best = cand
                    if best:
                        distinct_targets.add(best)
                elif node.module and node.module.startswith("module"):
                    names += 1
                    best = None
                    for cand in all_mods:
                        if node.module == cand or node.module.startswith(cand + "."):
                            if best is None or len(cand) > len(best):
                                best = cand
                    if best:
                        distinct_targets.add(best)
    res["import_stmts"] = stmts
    res["internal_import_names"] = names
    res["distinct_internal_targets"] = len(distinct_targets)
    res["targets"] = sorted(distinct_targets)
    return res


def file_line_count(pth: str):
    with open(pth, "rb") as f:
        data = f.read()
    text = data.decode("utf-8", errors="replace")
    lines = text.split("\n")
    # 最后一行若是空（文件以 \n 结尾），不计入
    n_logical = len(lines) - (1 if lines and lines[-1] == "" else 0)
    return {
        "bytes": len(data),
        "split_len": len(lines),
        "wc_l": n_logical,
        "ends_with_newline": data.endswith(b"\n"),
        "nonempty": sum(1 for x in lines if x.strip()),
    }


def main():
    p("=" * 72)
    p("A4 独立复现 — AST 统计")
    p("Python:", sys.version.replace("\n", " "))
    p("ROOT:", ROOT)
    p("=" * 72)

    mods, edges, raw_edges = build_graph()
    p("\n[1] module/ 内 import 图")
    p(f"    模块总数(含包): {len(mods)}")
    p(f"    有出边的模块数: {len(edges)}")
    p(f"    边总数(去重): {sum(len(v) for v in edges.values())}")
    sccs = tarjan(set(mods), edges)
    cycles = [c for c in sccs if len(c) > 1]
    self_loops = [c for c in sccs if len(c) == 1 and c[0] in edges.get(c[0], set())]
    p(f"    SCC 总数: {len(sccs)}; 非平凡(>1) SCC: {len(cycles)}; 自环: {len(self_loops)}")
    for c in cycles:
        p("    循环:", sorted(c))
    p(f"    结论: module/ import 图{'无环' if not cycles and not self_loops else '有环'}")
    # 最大的 SCC 规模分布
    from collections import Counter

    p("    SCC 规模分布:", dict(Counter(len(c) for c in sccs)))
    # 内部 import 边里跨层统计
    layers = Counter()
    for a, bs in edges.items():
        for b in bs:
            layers[(a.split(".")[1] if len(a.split(".")) > 1 else a, b.split(".")[1] if len(b.split(".")) > 1 else b)] += 1
    p("    跨层边 Top10:", layers.most_common(10))

    p("\n[2] composition_root.py 中 *_getter 关键字实参")
    cr = os.path.join(MODULE, "composition_root.py")
    hits = kw_getter_count(cr)
    p(f"    *_getter 关键字实参总数: {len(hits)}")
    p(f"    去重后的 getter 名: {len({h[2] for h in hits})}")
    p(f"    涉及调用表达式数: {len({(h[0], h[1]) for h in hits})}")
    p(f"    被调用目标 Top: ")
    fnames = Counter(h[1] for h in hits)
    for k, v in fnames.most_common():
        p(f"      {k}: {v}")
    p(f"    前 5 条证据 (lineno, callee, kwarg):")
    for h in hits[:5]:
        p(f"      L{h[0]}  {h[1]}(... {h[2]}=...)")

    p("\n[3] transfer/runner.py 对 host 的属性访问")
    runner = os.path.join(MODULE, "transfer", "runner.py")
    bare, dotted, distinct = host_attr_count(runner, "_host")
    p(f"    self._host 裸访问(不带后续属性): {len(bare)}  L{bare[:10]}")
    p(f"    self._host.<attr> 有后续属性访问: {len(dotted)}")
    p(f"    不同属性名数: {len(distinct)}")
    p(f"    属性名 Top15:")
    for k, v in Counter(a for _, a in dotted).most_common(15):
        p(f"      {k}: {v}")
    # 其他口径: 任意 self._host 出现
    p(f"    口径A 任意 Attribute 链 self._host*: {len(bare) + len(dotted)}")
    # 是否有局部别名 h = self._host
    tree = parse(runner)
    aliases = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Attribute):
            if isinstance(node.value.value, ast.Name) and node.value.value.id == "self" and node.value.attr == "_host":
                tgts = [t.id for t in node.targets if isinstance(t, ast.Name)]
                aliases.extend((node.lineno, t) for t in tgts)
    p(f"    self._host 局部别名赋值: {aliases}")
    p(f"    其他 host 相关名 (self.host / host.):")
    other = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "self" and node.attr == "host":
                other["self.host"] += 1
            if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name) and node.value.value.id == "self" and node.value.attr == "host":
                other[f"self.host.{node.attr}"] += 1
    p(f"      {dict(other)}")

    p("\n[4] adapters/webui/operations.py WebOperationsMixin 方法数")
    ops = os.path.join(MODULE, "adapters", "webui", "operations.py")
    funcs, nested, names = class_method_count(ops, "WebOperationsMixin")
    if funcs is None:
        p("    未找到 WebOperationsMixin，列出所有类:")
        t = parse(ops)
        p("   ", [n.name for n in ast.walk(t) if isinstance(n, ast.ClassDef)])
    else:
        p(f"    直接定义的方法数: {len(funcs)}  (async: {sum(1 for f in funcs if isinstance(f, ast.AsyncFunctionDef))})")
        p(f"    类内嵌套函数(def 在内的其他函数)数: {nested}")
        p(f"    私有(_开头): {sum(1 for n in names if n.startswith('_'))}, 双下划线: {sum(1 for n in names if n.startswith('__'))}")
        p(f"    去重方法名数: {len(set(names))}")
        dup = [n for n, c in Counter(names).items() if c > 1]
        p(f"    重复方法名: {dup}")
        # 该文件所有类
        t = parse(ops)
        classes = [(n.name, len([x for x in n.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))])) for n in ast.walk(t) if isinstance(n, ast.ClassDef)]
        p(f"    文件内所有类(名,直接方法数): {classes}")
        p(f"    operations.py 全文函数定义总数(含模块级/嵌套): {sum(1 for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))}")

    p("\n[5] module.downloader 的内部 import 依赖")
    dl = os.path.join(MODULE, "downloader.py")
    r = internal_import_count_of([dl], mods)
    p(f"    import 语句总数: {r['import_stmts']}")
    p(f"    内部(module.*) import 名条数: {r['internal_import_names']}")
    p(f"    去重内部目标模块数: {r['distinct_internal_targets']}")
    for t in r["targets"]:
        p(f"      -> {t}")

    p("\n[6] adapters/webui/assets.py 行数")
    ap = os.path.join(MODULE, "adapters", "webui", "assets.py")
    lc = file_line_count(ap)
    for k, v in lc.items():
        p(f"    {k}: {v}")
    # 与 wc -l 对应口径
    p(f"    与 `wc -l` 等价口径(len(splitlines)): {len(open(ap, encoding='utf-8', errors='replace').read().splitlines())}")

    outdir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(outdir, "raw_ast_output.txt"), "w", encoding="utf-8") as f:
        f.write(OUT.getvalue())
    p(f"\n[写出] {os.path.join(outdir, 'raw_ast_output.txt')}")


if __name__ == "__main__":
    main()
