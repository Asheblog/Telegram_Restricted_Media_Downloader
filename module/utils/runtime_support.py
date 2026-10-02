# coding=UTF-8
"""运行环境与进程辅助（docker/nuitka 探测、子进程参数、权限、随机凭据）。

从 ``utils/util.py`` **逐字搬移**：这一组是"进程/环境"关切，与标志位解析、
终端展示无关。``utils/util.py`` 仍 re-export，既有导入不必改。
"""
from __future__ import annotations

import os
import random
import stat
import string
import sys


from module import log
from module.core.enums import ENVIRON
from module.utils.parser import PARSE_ARGS



def add_executable_permission(file_path: str) -> bool:
    """确保文件具有执行权限(仅Linux/macOS)。"""
    if sys.platform not in ("linux", "darwin"):
        return True
    try:
        st = os.stat(file_path)
        mode = st.st_mode
        if not (mode & stat.S_IXUSR):
            os.chmod(file_path, mode | stat.S_IXUSR)
            log.info(f'已为"{file_path}"添加执行权限。')
        return True
    except Exception as e:
        log.warning(f"添加执行权限失败:{e}。")
        return False


def get_subprocess_args(main_file: str) -> list:
    """获取子进程参数列表。"""
    args = [sys.argv[0]] if "__compiled__" in globals() else [sys.executable, main_file]
    # 添加非web参数
    if PARSE_ARGS.quiet:
        args.append("--quiet")
    if PARSE_ARGS.config:
        args.extend(["--config", PARSE_ARGS.config])
    if PARSE_ARGS.session:
        args.extend(["--session", PARSE_ARGS.session])
    if PARSE_ARGS.temp:
        args.extend(["--temp", PARSE_ARGS.temp])

    return args


def gen_random_credential() -> dict:
    chars = string.ascii_letters + string.digits
    username = "".join(random.choices(chars, k=8))
    password = "".join(random.choices(chars, k=12))
    return {"username": username, "password": password}


def check_environ() -> None:
    if PARSE_ARGS.web is not None:
        environ_name, environ_param = ENVIRON.TRMD_WEB_PORT, str(PARSE_ARGS.web)
        os.environ[environ_name] = environ_param
        log.info(f'添加系统环境变量:"{environ_name}={environ_param}"。')


def is_nuitka() -> bool:
    return "__compiled__" in globals()


def is_docker() -> bool:
    """检查是否在Docker容器中运行。"""
    # 检查/.dockerenv文件是否存在。
    if os.path.exists("/.dockerenv"):
        return True

    # 检查/proc/1/cgroup中是否包含"docker"。
    try:
        with open("/proc/1/cgroup", "r") as f:
            content = f.read()
            if "docker" in content or "kubepods" in content:
                return True
    except (FileNotFoundError, IOError):
        pass
    except Exception:
        pass

    return False
