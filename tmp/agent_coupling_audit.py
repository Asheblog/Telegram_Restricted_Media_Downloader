# coding=UTF-8
"""Coupling metrics for the TRMD module tree (read-only analysis helper).

Writes nothing; prints JSON-ish tables to stdout.
"""
from __future__ import annotations

import ast
import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
MODULE_DIR = REPO / "module"


def modules() -> dict[str, pathlib.Path]:
    out: dict[str, pathlib.Path] = {}
    for path in sorted(MODULE_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(MODULE_DIR).with_suffix("")
        if rel.name == "__init__":
            name = "module" if len(rel.parts) == 1 else "module." + ".".join(rel.parts[:-1])
        else:
            name = "module." + ".".join(rel.parts)
        out[name] = path
    return out


def resolve(alias: str, current: str) -> str | None:
    if alias.startswith("."):
        parts = current.split(".")
        dots = len(alias) - len(alias.lstrip("."))
        rest = alias.lstrip(".")
        base = parts[: len(parts) - dots]
        if rest:
            base += rest.split(".")
        return ".".join(base)
    if alias == "module" or alias.startswith("module."):
        return alias
    return None


def import_graph(mods):
    graph = {name: set() for name in mods}
    edges: list[tuple[str, str, int]] = []
    for name, path in mods.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                aliases = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                aliases = [node.module or ""]
            else:
                continue
            for alias in aliases:
                target = resolve(alias, name)
                if target in mods:
                    graph[name].add(target)
                    edges.append((name, target, node.lineno))
    return graph, edges


ATTR_HOLDERS = {"host", "_host", "self", "downloader_ref", "downloader"}


def attribute_reads(path: pathlib.Path, holders: set[str]):
    """(holder, attr, lineno) for every read of holder.attr, skipping assignments."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assigned = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Attribute):
                    assigned.add(id(t))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Attribute):
            assigned.add(id(node.target))
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or id(node) in assigned:
            continue
        if isinstance(node.value, ast.Name) and node.value.id in holders:
            out.append((node.value.id, node.attr, node.lineno))
    return out


def main() -> None:
    mods = modules()
    graph, edges = import_graph(mods)

    fan_out = {n: len(t) for n, t in graph.items()}
    fan_in = collections.Counter()
    for src, targets in graph.items():
        for t in targets:
            fan_in[t] += 1

    print("== fan-out top 20 (module -> #internal deps) ==")
    for name, count in sorted(fan_out.items(), key=lambda kv: -kv[1])[:20]:
        print(f"{count:4d}  {name}")

    print("\n== fan-in top 20 (module -> #importers) ==")
    for name, count in fan_in.most_common(20):
        print(f"{count:4d}  {name}")

    print("\n== host/service coupling: readers per attribute ==")
    by_attr: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for name, path in mods.items():
        for holder, attr, lineno in attribute_reads(path, ATTR_HOLDERS):
            if holder == "self":
                continue
            by_attr[(holder, attr)].append(f"{name}:{lineno}")
        # self.<attr> inside service classes -> handled separately below
    for (holder, attr), where in sorted(by_attr.items(), key=lambda kv: -len(kv[1])):
        print(f"{len(where):4d}  {holder}.{attr}  <- {', '.join(sorted(set(where))[:6])}")

    print("\n== per-module self.<attr> reads (possible host leakage) ==")
    for name, path in mods.items():
        src = path.read_text(encoding="utf-8")
        if "class " not in src:
            continue
        reads = attribute_reads(path, {"self"})
        attrs = sorted({a for _, a, _ in reads if not a.startswith("__")})
        if len(attrs) >= 12:
            print(f"{len(attrs):4d}  {name}")

    print("\n== composition root wiring surface ==")
    cr = MODULE_DIR / "composition_root.py"
    tree = ast.parse(cr.read_text(encoding="utf-8"))
    getter_params = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg and node.arg.endswith("_getter"):
            getter_params += 1
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    print(f"getter= keyword args passed to services: {getter_params}")
    print(f"methods on composition root: {len(funcs)}")
    print("defined attrs: ", end="")
    defined = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                    defined.add(t.attr)
    print(len(defined))

    print("\n== hub modules: both high fan-in and high fan-out ==")
    hub = [(n, fan_in[n], fan_out[n]) for n in mods if fan_in[n] >= 3 and fan_out[n] >= 3]
    for n, fi, fo in sorted(hub, key=lambda t: -(t[1] * t[2]))[:20]:
        print(f"in={fi:3d} out={fo:3d}  {n}")


if __name__ == "__main__":
    sys.exit(main())
