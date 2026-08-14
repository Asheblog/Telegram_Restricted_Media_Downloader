# 拆分 module 包 import 副作用 Implementation Plan（Phase 1）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `import module`（及其任意子模块）零副作用——不建目录、不写日志文件、不起线程、不读 `.CONFIG.yaml`；把全部运行时副作用收进 `bootstrap.initialize()`，由运行入口显式调用。行为与公开 API 完全不变。

**Architecture:** 新增 `module/constants.py`（纯常量 + 无副作用对象 `console`/`log`/`CustomDumper`）与 `module/bootstrap.py`（幂等 `initialize()` + 副作用函数）。`module/__init__.py` 重写为纯 re-export。`main.py` 与 `TrmdCompositionRoot.__init__` 显式调用 `initialize()`（幂等，双保险覆盖 CLI / WebUI / 测试构造路径）。`build.py` 只取常量，import `module` 后不再产生任何副作用。

**Tech Stack:** Python 3.11+、rich、pyrogram、yaml、unittest/pytest。无新增第三方依赖。

**Spec:** `docs/specs/arch-decouple-phases.md`（本 plan 仅落地 Phase 1）

**行为契约（不得破坏）:** 以下 `from module import X` 在拆分后全部可用：`console`、`log`、`LINK_PREVIEW_OPTIONS`、`SOFTWARE_FULL_NAME`、`SLEEP_THRESHOLD`、`GLOBAL_CONFIG_PATH`、`LOG_PATH`、`__version__`、`app`（子模块 shim）、`CustomDumper`、`README`、`AUTHOR`、`__update_date__`、`SOFTWARE_SHORT_NAME`。

---

## File map

| 文件 | 职责 |
| ------ | ------ |
| `module/constants.py` | 纯常量、`console`/`log` 对象、`CustomDumper`、`README`（import 零副作用） |
| `module/bootstrap.py` | `initialize()` 幂等入口 + `read_input_history` / `cleanup_old_log_files` / `start_periodic_log_cleanup` / `via_log_level` |
| `module/__init__.py` | 重写为 re-export（零副作用） |
| `main.py` | 运行前调用 `bootstrap.initialize()` |
| `module/composition_root.py` | `__init__` 开头调用 `bootstrap.initialize()`（幂等兜底） |
| `unit_tests/module_bootstrap_case.py` | subprocess 隔离验证 import 零副作用 + initialize 幂等 |

---

### Task 1: 新建 `module/constants.py`（纯常量，零副作用）

**Files:**

- Create: `module/constants.py`

- [ ] **Step 1: 从 `module/__init__.py` 提取常量与无副作用对象**

迁移内容（原样保留值，仅去掉副作用行）：

- `LOG_TIME_FORMAT`、`console = Console(log_path=False, log_time_format=...)`
- `SLEEP_THRESHOLD`、`AUTHOR`、`__version__`、`__license__`、`__update_date__`、`__copyright__`
- `SOFTWARE_FULL_NAME`、`SOFTWARE_SHORT_NAME`
- `APPDATA_PATH`（`os.path.join` 计算，不含 `os.makedirs`）、`GLOBAL_CONFIG_NAME`、`GLOBAL_CONFIG_PATH`、`PLATFORM`
- `INPUT_HISTORY_PATH`、`MAX_RECORD_LENGTH`、`LOG_PATH`、`LOG_RETENTION_DAYS`、`LOG_CLEANUP_INTERVAL_SECONDS`
- `LINK_PREVIEW_OPTIONS`、`LOG_FORMAT`、`FILE_LOG_LEVEL: int = logging.INFO`、`CONSOLE_LOG_LEVEL: int = logging.WARNING`
- `CustomDumper` 类、`log = logging.getLogger("rich")`、`README`

**验收:** `python -c "import module.constants"` 不创建 `%APPDATA%/TRMD` 目录、不写日志文件（在临时 `APPDATA` 环境变量下验证）。

---

### Task 2: 新建 `module/bootstrap.py`（幂等 `initialize()`）

**Files:**

- Create: `module/bootstrap.py`

- [ ] **Step 1: 迁入副作用函数**

从 `module/__init__.py` 迁入（函数体不变）：`read_input_history`、`cleanup_old_log_files`、`start_periodic_log_cleanup`、`via_log_level`（签名改为接收 `global_config` 参数，消除对模块级 `global_config` 的隐式依赖）。

- [ ] **Step 2: 实现幂等 `initialize()`**

按原执行顺序收拢副作用：`os.makedirs` → readline 历史 → `cleanup_old_log_files` → 读 `.CONFIG.yaml`（局部 `global_config = {}` 兜底）→ `TimedRotatingFileHandler` + `file_handler.setLevel` → `RichHandler` → `logging.basicConfig` → banner 日志 → `start_periodic_log_cleanup` → `CustomDumper.add_representer`。

幂等：`_initialized` 标志 + `threading.Lock`，重复调用直接返回。

- [ ] **Step 3: 单元测试 `unit_tests/module_bootstrap_case.py`（TDD）**

```bash
python -m pytest unit_tests/module_bootstrap_case.py -q
```

用例：

1. subprocess 隔离 `import module` 后，临时 `APPDATA` 目录不存在、无日志文件、无 `trmd-log-cleanup` 线程。
2. `initialize()` 连续调用两次，`logging` 根 logger handlers 数量不翻倍、`_log_cleanup_thread_started` 不重复启动。

---

### Task 3: 重写 `module/__init__.py` 为 re-export

**Files:**

- Modify: `module/__init__.py`

- [ ] **Step 1: re-export constants + bootstrap 符号**

```python
from module.constants import (console, log, SLEEP_THRESHOLD, AUTHOR, __version__,
    __license__, __update_date__, __copyright__, SOFTWARE_FULL_NAME,
    SOFTWARE_SHORT_NAME, APPDATA_PATH, GLOBAL_CONFIG_NAME, GLOBAL_CONFIG_PATH,
    PLATFORM, INPUT_HISTORY_PATH, MAX_RECORD_LENGTH, LOG_PATH, LOG_RETENTION_DAYS,
    LOG_CLEANUP_INTERVAL_SECONDS, LINK_PREVIEW_OPTIONS, LOG_FORMAT, FILE_LOG_LEVEL,
    CONSOLE_LOG_LEVEL, CustomDumper, README)
from module.bootstrap import (initialize, read_input_history,
    cleanup_old_log_files, start_periodic_log_cleanup)
```

保留 `from module import app` 子模块行为（不在 `__init__` 定义 `app` 属性，让 Python 自然导入 `module/app.py` shim）。

- [ ] **Step 2: 全仓回归**

```bash
python -m pytest unit_tests/ -q
```

预期：全部通过（import 副作用移除不影响既有测试）。

---

### Task 4: 运行入口显式初始化

**Files:**

- Modify: `main.py`
- Modify: `module/composition_root.py`

- [ ] **Step 1: `main.py` 调用 `initialize()`**

在 `check_environ()` 之后、构造 `TelegramRestrictedMediaDownloader()` 之前调用 `module.bootstrap.initialize()`。

- [ ] **Step 2: `TrmdCompositionRoot.__init__` 开头调用 `initialize()`（幂等兜底）**

覆盖直接构造 composition root 而不走 `main.py` 的路径（如 WebUI 测试、其他脚本）。

- [ ] **Step 3: `build.py` 无副作用验证**

```bash
python -c "import sys; sys.path.insert(0,'.'); from module import __version__; print(__version__)"
```

在 `APPDATA` 指向不存在路径的环境下运行，确认不报错、不建目录。

---

### Task 5: 文档同步

**Files:**

- Modify: `CONTEXT-MAP.md`（新增 `module/constants.py`、`module/bootstrap.py` 条目）
- Modify: `CONTEXT.md`（架构立场补充「import 零副作用」约定）

---

## 回滚策略

`git revert` 本次提交即可整体回滚；拆分保持 `from module import X` 契约不变，任何遗漏可通过 `python -m pytest unit_tests/` 与 `python main.py` 冒烟发现。
