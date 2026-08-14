# coding=UTF-8
"""Phase 1 回归：import module 零副作用 + bootstrap.initialize 幂等。"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_isolated(code: str) -> subprocess.CompletedProcess:
    """在临时 APPDATA 环境下运行代码，隔离 import 副作用。"""
    env = os.environ.copy()
    env.pop("XDG_CONFIG_HOME", None)
    with tempfile.TemporaryDirectory() as tmp:
        env["APPDATA"] = tmp
        return subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
            cwd=ROOT,
        )


class ModuleBootstrapCase(unittest.TestCase):
    def test_import_module_is_side_effect_free(self):
        """import module 不应创建目录、写日志文件或启动清理线程。"""
        code = (
            "import os, threading\n"
            "import module\n"
            "appdata = os.path.join(os.environ['APPDATA'], 'TRMD')\n"
            "print('DIR_EXISTS', os.path.exists(appdata))\n"
            "print('LOG_EXISTS', os.path.exists(os.path.join(appdata, 'TRMD_LOG.log')))\n"
            "print('THREADS', [t.name for t in threading.enumerate() if 'trmd' in t.name.lower()])\n"
            "print('VERSION', module.__version__)\n"
        )
        result = _run_isolated(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DIR_EXISTS False", result.stdout)
        self.assertIn("LOG_EXISTS False", result.stdout)
        self.assertIn("THREADS []", result.stdout)
        self.assertIn("VERSION 0.2.240", result.stdout)

    def test_initialize_is_idempotent(self):
        """重复调用 initialize 不应重复配置日志 handler 或线程。"""
        code = (
            "import logging\n"
            "from module.bootstrap import initialize\n"
            "before = len(logging.getLogger().handlers)\n"
            "initialize()\n"
            "after_first = len(logging.getLogger().handlers)\n"
            "initialize()\n"
            "after_second = len(logging.getLogger().handlers)\n"
            "print('CONFIGURED', after_first > before)\n"
            "print('IDEMPOTENT', after_first == after_second)\n"
        )
        result = _run_isolated(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CONFIGURED True", result.stdout)
        self.assertIn("IDEMPOTENT True", result.stdout)

    def test_build_script_imports_constants_without_side_effects(self):
        """build.py 只取常量，import module 后 APPDATA 目录不应存在。"""
        code = (
            "import os\n"
            "from module import AUTHOR, SOFTWARE_SHORT_NAME, __version__, __update_date__\n"
            "appdata = os.path.join(os.environ['APPDATA'], 'TRMD')\n"
            "print('DIR_EXISTS', os.path.exists(appdata))\n"
            "print('AUTHOR', AUTHOR)\n"
            "print('NAME', SOFTWARE_SHORT_NAME)\n"
            "print('VERSION', __version__)\n"
            "print('DATE', __update_date__)\n"
        )
        result = _run_isolated(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DIR_EXISTS False", result.stdout)
        self.assertIn("AUTHOR Gentlesprite", result.stdout)
        self.assertIn("NAME TRMD", result.stdout)
        self.assertIn("VERSION 0.2.240", result.stdout)


if __name__ == "__main__":
    unittest.main()
