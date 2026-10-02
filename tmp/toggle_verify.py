# coding=UTF-8
"""临时：允许指定分支触发 ci.yml 与 release_docker.yml，用于在分支上验证镜像构建。

安全说明：release_docker.yml 的镜像 tag 取自 GITHUB_REF_NAME，分支名含 "/" 会得到
非法 tag（实测报 invalid reference format），因此验证用的分支名必须无斜杠。

用法: add <branch> | revert
"""
import pathlib
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
CI = REPO / ".github" / "workflows" / "ci.yml"
DOCKER = REPO / ".github" / "workflows" / "release_docker.yml"

CI_ORIG = "on:\n  push:\n    branches: ['main']\n  pull_request:\n    branches: ['main']\n  workflow_dispatch:\n"
DOCKER_ORIG = "on:\n  push:\n    tags:\n      - 'v*.*.*'\n"


def _write(path: pathlib.Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def add(branch: str) -> None:
    ci = CI.read_text(encoding="utf-8")
    assert CI_ORIG in ci, "ci.yml 结构不符合预期，请人工处理"
    _write(CI, ci.replace(
        CI_ORIG,
        f"on:\n  push:\n    branches: ['main', '{branch}']\n"
        f"  pull_request:\n    branches: ['main']\n  workflow_dispatch:\n",
        1,
    ))
    print(f"ci.yml: 已允许 {branch}")

    docker = DOCKER.read_text(encoding="utf-8")
    assert DOCKER_ORIG in docker, "release_docker.yml 结构不符合预期，请人工处理"
    _write(DOCKER, docker.replace(
        DOCKER_ORIG,
        f"on:\n  push:\n    tags:\n      - 'v*.*.*'\n    branches: ['{branch}']\n",
        1,
    ))
    print(f"release_docker.yml: 已允许 {branch}")


def revert() -> None:
    _write(CI, CI.read_text(encoding="utf-8"))
    ci = CI.read_text(encoding="utf-8")
    import re

    text = re.sub(
        r"on:\n  push:\n    branches: \[[^\]]*\]\n  pull_request:\n    branches: \['main'\]\n  workflow_dispatch:\n",
        CI_ORIG,
        ci,
        count=1,
    )
    _write(CI, text)
    print("ci.yml: 已还原")

    docker = DOCKER.read_text(encoding="utf-8")
    text = re.sub(
        r"on:\n  push:\n    tags:\n      - 'v\*\.\*\.\*'\n(    branches: \[[^\]]*\]\n)?",
        DOCKER_ORIG,
        docker,
        count=1,
    )
    _write(DOCKER, text)
    print("release_docker.yml: 已还原")


if sys.argv[1] == "add":
    add(sys.argv[2])
else:
    revert()
