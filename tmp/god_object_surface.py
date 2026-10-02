# coding=UTF-8
"""God-object surface + wiring duplication measurements for the TRMD host."""
import ast
import collections
import pathlib
import re

REPO = pathlib.Path(r"E:\codebase\tgbot")
MODULE = REPO / "module"


def methods_of(path: pathlib.Path, class_name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return [
                c.name for c in node.body
                if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
    return []


print("=== host public API surface (composition_root + downloader + mixins) ===")
host_parts = {
    "composition_root.TrmdCompositionRoot": methods_of(MODULE / "composition_root.py", "TrmdCompositionRoot"),
    "downloader.TelegramRestrictedMediaDownloader": methods_of(MODULE / "downloader.py", "TelegramRestrictedMediaDownloader"),
    "webui.operations.WebOperationsMixin": methods_of(MODULE / "adapters/webui/operations.py", "WebOperationsMixin"),
    "bot.host.BotHostMixin": methods_of(MODULE / "adapters/bot/host.py", "BotHostMixin"),
}
total = 0
for name, methods in host_parts.items():
    public = [m for m in methods if not m.startswith("_")]
    total += len(methods)
    print(f"  {len(methods):4d} methods ({len(public):4d} public)  {name}")
print(f"  ---- combined: {total} method definitions on the single host object")
# name collisions across mixins (MRO shadowing risk)
counts = collections.Counter()
for methods in host_parts.values():
    counts.update(set(methods))
collide = {k: v for k, v in counts.items() if v > 1}
print(f"  name collisions across the 4 classes (MRO shadowing risk): {len(collide)}")
for k in sorted(collide):
    print(f"      {k}  x{collide[k]}")

print()
print("=== WebUiServer.__init__ params vs operations facade ===")
srv = MODULE / "adapters/webui/server.py"
src = srv.read_text(encoding="utf-8")
tree = ast.parse(src)
params = []
for n in ast.walk(tree):
    if isinstance(n, ast.ClassDef) and n.name == "WebUiServer":
        for c in n.body:
            if isinstance(c, ast.FunctionDef) and c.name == "__init__":
                params = [a.arg for a in c.args.args + c.args.kwonlyargs if a.arg != "self"]
print(f"  ctor params: {len(params)}")

ops = methods_of(MODULE / "adapters/webui/operations.py", "WebOperationsMixin")
host_methods = set(host_parts["downloader.TelegramRestrictedMediaDownloader"]) | set(
    host_parts["webui.operations.WebOperationsMixin"]
) | set(host_parts["composition_root.TrmdCompositionRoot"])

print()
print("=== operations facade: delegate surface ===")
print("  WebOperationsFacade.delegate is generic; check explicit defs:")
for name in ("WebOperationsFacade",):
    ms = methods_of(MODULE / "adapters/webui/operations.py", name)
    print(f"    {name}: {len(ms)} methods -> {ms}")

print()
print("=== how many server ctor callables duplicate an operations/host method ===")
suspects = [
    "task_submitter", "settings_provider", "settings_updater", "deep_link_whitelist_getter",
    "setup_status_provider", "setup_api_saver", "setup_rclone_configurer", "setup_rclone_skipper",
    "setup_rclone_tester", "setup_bot_saver", "setup_bot_skipper", "setup_ready_checker",
    "pikpak_accounts_provider", "pikpak_account_adder", "pikpak_account_switcher",
    "pikpak_account_remover",
]
print(f"  candidate bound-method params: {len(suspects)}")
print()
print("=== which host methods are passed to WebUiServer in start_web_ui ===")
ops_src = (MODULE / "adapters/webui/operations.py").read_text(encoding="utf-8")
m = re.search(r"self\.web_ui = WebUiServer\((.*?)\n        \)", ops_src, re.S)
if m:
    body = m.group(1)
    passed = re.findall(r"=\s*(?:self\.)?([A-Za-z_][\w\.]*)", body)
    print(f"  {len(passed)} arguments passed; self.* references:")
    for p in sorted(set(x for x in passed if x != "self")):
        print(f"      self.{p} -> {'KNOWN HOST METHOD' if p in host_methods else 'other'}")
