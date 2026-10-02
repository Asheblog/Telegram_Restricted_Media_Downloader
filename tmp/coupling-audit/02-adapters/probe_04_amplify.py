import subprocess, os, re, sys, collections
ROOT = r"E:\codebase\tgbot"

def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout

# Pick candidate "one feature change" commits from the log and classify touched files by layer.
CANDIDATES = [
    "a3dcbf9",  # feat(archive): per-task archive title source with prefer+fallback
    "b352fc3",  # feat(webui): allow manual archive retry from system logs
    "523df22",  # fix(pikpak): harden multi-account switch semantics per ADR-0016
    "94bb15c",  # fix(webui): PikPak 账号表单排版 + 当前账号徽章
    "1f7a43b",  # fix(forward): 监听转发 file_reference 过期时刷新引用重试
    "bce98f8",  # fix(webui): 复核修复 Origin 端口误判与代理头信任
    "5538e56",  # fix: 修复机器人启动崩溃与全部宿主属性缺口
]

LAYER = [
    ("module/adapters/webui", "adapters/webui"),
    ("module/adapters/bot", "adapters/bot"),
    ("module/adapters/pikpak", "adapters/pikpak"),
    ("module/adapters", "adapters/other"),
    ("module/transfer", "domain:transfer"),
    ("module/watches", "domain:watches"),
    ("module/pikpak", "domain:pikpak"),
    ("module/statistics.py", "domain:statistics"),
    ("module/media", "domain:media"),
    ("module/archive", "domain:archive"),
    ("module/infra", "infra"),
    ("module/app", "app/host"),
    ("module/", "domain:other"),
    ("unit_tests", "tests"),
    ("docs", "docs"),
    ("frontend", "frontend"),
    (".", "root/other"),
]

def layer_of(path):
    for pre, name in LAYER:
        if path.startswith(pre):
            return name
    return "other"

report = []
for sha in CANDIDATES:
    subj = git("log", "-1", "--format=%s", sha).strip()
    stat = git("show", "--stat", "--format=", sha)
    files = [l.split("|")[0].strip() for l in stat.splitlines() if "|" in l]
    # filter out pure-format/version-only noise for the "files touched" count
    code_files = [f for f in files if f.endswith(".py") or f.endswith(".ts") or f.endswith(".js") or f.endswith(".vue") or f.endswith(".html") or f.endswith(".css")]
    layers = collections.Counter(layer_of(f) for f in files)
    report.append((sha, subj, files, code_files, layers))

print("=" * 100)
for sha, subj, files, code_files, layers in report:
    print(f"\n### {sha}  {subj}")
    print(f"  total files touched : {len(files)}")
    print(f"  code files (.py/.ts/.js/.vue/.html/.css): {len(code_files)}")
    print(f"  layers: {dict(layers)}  -> distinct layers = {len(layers)}")
    for f in files:
        print(f"     - {f}")

print("\n" + "=" * 100)
print("=== ADD/DEL summary (git show --shortstat) ===")
for sha in CANDIDATES:
    ss = git("show", "--shortstat", "--format=", sha).strip()
    print(f"{sha}: {ss}")

print("\n=== full raw --stat for the 3 target commits (verbatim) ===")
for sha in ["a3dcbf9", "b352fc3", "5538e56"]:
    print(f"\n$ git show --stat {sha}")
    print(git("show", "--stat", sha))
