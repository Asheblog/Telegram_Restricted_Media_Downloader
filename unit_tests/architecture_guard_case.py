# coding=UTF-8
"""Architecture guard for the decoupled module layout.

Pure AST / filesystem checks; no runtime imports required, so this test also
runs before the Pyrogram stub is installed.
"""
import ast
import pathlib
import sys
import unittest

MODULE_DIR = pathlib.Path(__file__).resolve().parents[1] / "module"

OLD_TOP_LEVEL_NAMES = {
    "app", "async_window", "bot", "bot_host", "callback_handler", "comp",
    "config", "diagnostics", "enums", "filter", "language",
    "live_watch_applicator", "live_watch_manager", "local_storage_guard",
    "media_manager", "parser", "path_tool", "pikpak_archive",
    "pikpak_integration", "source_folders", "statistics_payload", "stdio",
    "target_profiles", "task", "transfer_engine", "transfer_progress",
    "transfer_registry", "transfer_store", "uploader", "util",
    "web_operations", "web_task_manager", "web_ui", "web_ui_assets",
    "webui_view_model", "author_hashtag_match", "archive_reorganize",
    "archive_author_tool", "archive_author_jobs",
}

EXPECTED_TOP_LEVEL_REAL = {
    "__init__.py", "bootstrap.py", "composition_root.py", "constants.py",
    "downloader.py", "ports.py",
}


def _modules():
    modules = {}
    for path in sorted(MODULE_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(MODULE_DIR).with_suffix("")
        if rel.name == "__init__":
            name = "module" if len(rel.parts) == 1 else "module." + ".".join(rel.parts[:-1])
        else:
            name = "module." + ".".join(rel.parts)
        modules[name] = path
    return modules


def _module_is_in(alias, known):
    """``alias`` is ``known``, a submodule of it, or a package containing submodules of it."""
    return (
        alias in known
        or any(item.startswith(alias + ".") for item in known)
        or any(alias.startswith(item + ".") for item in known)
    )


def _resolve(alias, current_module, is_package=False, level=0):
    """Resolve one import target to the module names it can bind.

    Returns a set: ``from pkg import submodule`` genuinely depends on
    ``pkg.submodule``, and a relative import inside ``__init__.py`` is resolved
    against the package itself rather than its parent.

    ``level`` is ``ast.ImportFrom.level``: a leading dot is stored there, not in
    ``node.module``, so ``from . import x`` arrives with ``alias=""``.
    """
    if level or alias.startswith("."):
        dots = level or (len(alias) - len(alias.lstrip(".")))
        rest = alias.lstrip(".")
        parts = current_module.split(".")
        # Drop the imported module's own name, then one level per extra dot.
        # For a package (__init__.py) its own name *is* the base, so nothing drops.
        cut = len(parts) - (dots - 1 if is_package else dots)
        base = parts[:cut]
        if rest:
            base += rest.split(".")
        return {".".join(base)} if base else set()
    if alias == "module" or alias.startswith("module."):
        return {alias}
    return set()


def _import_targets(alias, current_module, is_package, known):
    """Expand a bare ``from X import Y`` statement into real module dependencies.

    The guard used to keep only ``node.module``, so ``from pkg import submodule``
    never produced the ``pkg.submodule`` edge — that blind spot is what let three
    genuine import cycles pass as "no cycles".
    """
    targets = _resolve(alias, current_module, is_package)
    if "." in alias:  # an absolute dotted module, never a name inside ``module``
        return targets
    return {t for t in targets if _module_is_in(t, known)}


def _import_graph(modules):
    graph = {name: set() for name in modules}
    for name, path in modules.items():
        is_package = path.name == "__init__.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for item in node.names:
                    for target in _import_targets(item.name, name, is_package, modules):
                        if target in modules and target != name:
                            graph[name].add(target)
            elif isinstance(node, ast.ImportFrom):
                base = _resolve(node.module or "", name, is_package, node.level)
                for target in base:
                    if target in modules and target != name:
                        graph[name].add(target)
                # `from pkg import submodule` also depends on pkg.submodule.
                for item in node.names:
                    for parent in base:
                        candidate = f"{parent}.{item.name}"
                        if candidate in modules and candidate != name:
                            graph[name].add(candidate)
    return graph


HOST_CLASSES = {
    "composition_root.py": ["TrmdCompositionRoot"],
    "webops/operations.py": ["WebOperationsMixin"],
    "adapters/bot/host.py": ["BotHostMixin"],
    "downloader.py": ["TelegramRestrictedMediaDownloader"],
}
# __getattr__ forwards every miss to the host, so their self.<attr> is a host read.
HOST_PROXY_CLASSES = {
    "transfer/live_transfer.py": ["LiveTransferService"],
}


def _class_nodes(path, names):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in names:
            yield node


def _assigned_attribute_nodes(root):
    targets = set()
    for node in ast.walk(root):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    targets.add(id(target))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Attribute):
            targets.add(id(node.target))
    return targets


def _host_names_defined(node):
    """Everything the class supplies: members plus self.<attr> assignments."""
    defined = set()
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(child.name)
        elif isinstance(child, ast.Assign):
            defined.update(
                target.id for target in child.targets if isinstance(target, ast.Name)
            )
        elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            defined.add(child.target.id)
    for sub in ast.walk(node):
        if isinstance(sub, ast.Assign):
            for item in sub.targets:
                if isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name):
                    if item.value.id == "self":
                        defined.add(item.attr)
        elif isinstance(sub, ast.AnnAssign):
            target = sub.target
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if target.value.id == "self":
                    defined.add(target.attr)
    return defined


def _attribute_reads(root, holders):
    """First read line for each `<holder>.<attr>` that is not an assignment target."""
    assigned = _assigned_attribute_nodes(root)
    reads = {}
    for node in ast.walk(root):
        if not isinstance(node, ast.Attribute) or id(node) in assigned:
            continue
        if isinstance(node.value, ast.Name) and node.value.id in holders:
            reads.setdefault(node.attr, node.lineno)
    return reads


def _layer(module_name):
    parts = module_name.split(".")
    if len(parts) > 1 and parts[1] in {
        "adapters", "core", "domain", "infra", "persistence", "transfer", "utils",
        "webops",
    }:
        return parts[1]
    return "top"


class ArchitectureGuardCase(unittest.TestCase):
    def test_module_import_graph_has_no_cycles(self):
        graph = _import_graph(_modules())
        nodes = sorted(graph)
        index = {name: i for i, name in enumerate(nodes)}
        num = {}
        low = {}
        stack = []
        on_stack = set()
        cycles = []
        timer = 0

        def strong(vertex):
            nonlocal timer
            timer += 1
            num[vertex] = low[vertex] = timer
            stack.append(vertex)
            on_stack.add(vertex)
            for target in graph[vertex]:
                if target not in num:
                    strong(target)
                    low[vertex] = min(low[vertex], low[target])
                elif target in on_stack:
                    low[vertex] = min(low[vertex], num[target])
            if low[vertex] == num[vertex]:
                component = []
                while True:
                    item = stack.pop()
                    on_stack.remove(item)
                    component.append(item)
                    if item == vertex:
                        break
                if len(component) > 1:
                    cycles.append(component)

        sys.setrecursionlimit(10000)
        for node in nodes:
            if node not in num:
                strong(node)
        self.assertEqual([], cycles)

    def test_subpackages_do_not_import_top_level_shims(self):
        modules = _modules()
        violations = []
        for name, path in modules.items():
            parts = name.split(".")
            if len(parts) < 3:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    aliases = [item.name for item in node.names]
                elif isinstance(node, ast.ImportFrom):
                    aliases = [node.module or ""]
                else:
                    continue
                for alias in aliases:
                    if not alias.startswith("module."):
                        continue
                    leaf = alias.split(".")[1] if len(alias.split(".")) > 1 else None
                    if leaf in OLD_TOP_LEVEL_NAMES:
                        violations.append(f"{name}:{node.lineno} imports {alias}")
        self.assertEqual([], violations)

    def test_no_layer_inversions(self):
        allowed = {
            "core": {"core", "domain", "utils"},
            "domain": {"core", "domain", "utils"},
            "infra": {"infra", "core", "domain", "utils"},
            "persistence": {"persistence", "core", "domain", "utils"},
            "transfer": {
                "transfer", "persistence", "core", "domain", "infra", "utils",
            },
            "utils": {"utils", "core", "domain"},
            "adapters": {
                "adapters", "core", "domain", "infra", "persistence",
                "transfer", "utils",
            },
            # webops = 业务编排层（从 adapters/webui 的 WebOperationsMixin 迁出）。
            # 它**有意**位于 adapters 之上：编排天然要组合适配器（PikPak 归档、
            # 媒体清理、上传器）。与"层反转"的区别在于方向——被依赖的 adapters
            # 不知道 webops 存在（无反向 import），且 webops 只暴露操作语义、
            # 不含 HTTP 原语。允许它依赖全部下层，禁止反向（见 allowed 里各层均无 "webops"）。
            "webops": {
                "webops", "adapters", "core", "domain", "infra", "persistence",
                "transfer", "utils",
            },
            "top": set(),
        }
        violations = []
        for source, targets in _import_graph(_modules()).items():
            if _layer(source) in ("top", "module"):
                continue
            for target in targets:
                if target in ("module", "module.ports"):
                    continue
                if _layer(target) not in allowed.get(_layer(source), set()):
                    violations.append(f"{source} -> {target}")
        self.assertEqual([], violations)

    def test_composed_host_resolves_every_attribute_read(self):
        """Without __getattr__, an unresolved self.<attr>/host.<attr> is a runtime crash.

        Production went dark because listen_forward_chat, mark_pending_watch and
        done_notice were only reachable through the reflective __getattr__ that
        187d1d8 deleted; each one surfaced as a separate AttributeError.
        """
        defined = set()
        reads = {}
        for rel, names in {**HOST_CLASSES, **HOST_PROXY_CLASSES}.items():
            path = MODULE_DIR / rel
            for node in _class_nodes(path, names):
                if rel in HOST_PROXY_CLASSES:
                    # Proxy methods resolve locally; only its self.<attr> misses hit the host.
                    defined.update(
                        child.name for child in node.body
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    )
                else:
                    defined |= _host_names_defined(node)
                for attr, lineno in _attribute_reads(node, {"self"}).items():
                    reads.setdefault(attr, f"{rel}:{lineno}")

        # Services receive the host explicitly. module/utils is excluded: the layer
        # rules forbid it from depending on the host, so its `host` params are strings.
        for path in sorted(MODULE_DIR.rglob("*.py")):
            rel = path.relative_to(MODULE_DIR).as_posix()
            if rel.startswith("utils/") or "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for attr, lineno in _attribute_reads(tree, {"host", "_host"}).items():
                reads.setdefault(attr, f"{rel}:{lineno}")

        unresolved = sorted(
            f"{attr} (first read at {where})"
            for attr, where in reads.items()
            if attr not in defined and not attr.startswith("__")
        )
        self.assertEqual([], unresolved)

    def test_composition_root_has_no_reflective_getattr(self):
        path = MODULE_DIR / "composition_root.py"
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("def __getattr__", source)
        self.assertNotIn("self.__dict__.get", source)
        self.assertIn("self._transfer_ports = self._build_transfer_ports()", source)

    def test_transfer_ports_have_no_host_reflection(self):
        path = MODULE_DIR / "transfer" / "context.py"
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("from_host", source)

    def test_top_level_contains_only_facade_and_shims(self):
        shims = {
            path.name
            for path in (MODULE_DIR).glob("*.py")
            if "Compatibility shim" in path.read_text(encoding="utf-8")
        }
        real = {
            path.name for path in (MODULE_DIR).glob("*.py")
            if path.name not in shims
        }
        self.assertEqual(EXPECTED_TOP_LEVEL_REAL, real)


if __name__ == "__main__":
    unittest.main()
