# A4 独立复现与对抗性验证报告

- 责任人：verify-auditor（task-4）
- 仓库：`E:\codebase\tgbot`（TRMD）
- 写入范围：仅 `tmp/coupling-audit/04-verify/`；`module/` 与 `unit_tests/` 全程只读，未 git commit。
- 所有脚本与原始输出均在本目录，可复跑。

## 0. 环境双份 / 解释器不一致（前置事实，影响全部结论可信度）

| 项 | `.venv`（默认） | `.venv313` |
|---|---|---|
| `python -V` | **3.14.0a5**（alpha, MSC v.1942, Feb 11 2025） | **3.13.7** |
| `pyvenv.cfg` | `version_info = 3.14.0a5` | — |
| `SOABI` | `cp314-win_amd64` | `cp313-win_amd64` |
| `import yaml` | **退出码 -1073741819 = 0xC0000005（访问违例，原生崩溃）** | 0，`yaml 6.0.3` |
| `import _yaml` | **-1073741819** | 0 |
| `import module` / `module.downloader` | **-1073741819** | 0 |
| `import pytest` / `import pyrogram` | 0（纯 Python 包正常） | 0 |
| `pyproject.toml:11 requires-python` | `>=3.13.2` | 一致 |

命令与原始输出：

```
> .venv\Scripts\python.exe -c "import yaml"
exit=-1073741819
> .venv313\Scripts\python.exe -c "import yaml; print(yaml.__version__)"
yaml OK 6.0.3        exit=0
```

崩溃根因（机制级证据，不是"测试逻辑问题"）：

1. `-X -v` 导入轨迹的最后一行停在扩展模块加载处，即崩在 `_yaml` 的 C 模块初始化：

```
> .venv\Scripts\python.exe -v -c "import module"
... import 'yaml.dumper' ...
# extension module 'yaml._yaml' loaded from
#   'E:\codebase\tgbot\.venv\Lib\site-packages\yaml\_yaml.cp314-win_amd64.pyd'
exit=-1073741819
```

2. `-X faulthandler` 显示 AV 发生在扩展 `exec_module` 内部（最内层帧是 `_call_with_frames_removed` → `exec_module`），即 pyd 的 `PyInit_*`/模块初始化崩溃，**不是** PyYAML 的 Python 代码、也不是测试代码：

```
> .venv\Scripts\python.exe -X faulthandler -c "import _yaml"
  File "...\_yaml\__init__.py", line 6 in <module>
  File "<frozen importlib._bootstrap>", line 488 in _call_with_frames_removed
  File "<frozen importlib._bootstrap_external>", line 762 in exec_module
exit=-1073741819
```

3. 两个 venv 的 PyYAML 元数据完全一致（`pyyaml-6.0.3.dist-info`，纯 Python 文件逐字节同尺寸），**只有 C 扩展不同**：
   `_yaml.cp314-win_amd64.pyd`(258 560 B, 依赖 `python314.dll`) vs `_yaml.cp313-win_amd64.pyd`(253 952 B, `python313.dll`)。
4. 不是"所有 C 扩展都崩"：`.venv` 内只有两个 pyd，`tgcrypto.cp314-win_amd64.pyd` 导入正常（exit=0），其余模块名报 `ModuleNotFoundError`(exit=1)。
5. `module/__init__.py:10` 有 `import yaml  # noqa: F401 (re-exported for back-compat)`；`module/bootstrap.py:18`、`module/constants.py:13` 也 import yaml。因此 **任何 import `module` 的测试在 `.venv` 下必然 AV**；唯一不 AV 的是纯 AST、不 import `module` 的 `unit_tests/architecture_guard_case.py`（其文件头自述 "Pure AST / filesystem checks; no runtime imports required"）。

结论：`.venv` 是**被污染的默认解释器**（cp314 wheel 的二进制与 3.14.0a5 alpha ABI 不匹配）。它会把"环境缺陷"伪装成"测试基建崩溃/产品崩溃"。本报告的**全部运行时结论一律以 `.venv313` 为准**。

对结论可信度的影响评估：
- 任何在 `.venv` 上跑出来的"崩溃/失败"结论**一律不可用**（会把 0xC0000005 误判为产品缺陷）；
- 任何用 `.venv` 跑出来的"通过"结论也不可信（它连 `module` 都 import 不了，收集不到用例）；
- `.venv313` 与 `requires-python >=3.13.2` 一致，是唯一有效基线；
- 建议把该环境事实写进 CI/文档，否则后续审查会重复踩坑。

## 1. 独立复现结果表

复现脚本：`repro_ast.py`、`repro_host_runner.py`、`repro_import_graph_v2.py`、`repro_import_bytecode.py`、`repro_guard_gaps.py`（原始输出见同目录 `raw_*.txt`）。

| # | 项目 | 他人数值 | 我的数值 | 一致 | 命令 |
|---|---|---|---|---|---|
| 1 | `module/` import 图无环（Tarjan SCC） | 无环 | **有环：3 个非平凡 SCC** | ✘ **被推翻** | `.venv313\Scripts\python.exe -X utf8 tmp\coupling-audit\04-verify\repro_import_graph_v2.py` |
| 2 | `composition_root.py` 传给服务构造函数的 `*_getter` 关键字实参个数 | 50 | **50** | ✔ | `... repro_ast.py` |
| 3 | `transfer/runner.py` 对 host 的属性访问次数 | 128 | **128**（= 别名 `host.<attr>` 126 + `self._host.<attr>` 2） | ✔ | `... repro_host_runner.py` |
| 4 | `adapters/webui/operations.py` `WebOperationsMixin` 方法数 | 118 | **114 个直接方法**（118 = 114 + 4 个嵌套闭包） | ✘ **需改口径** | `... repro_ast.py` |
| 5 | `module.downloader` 的内部 import 依赖数 | 39 | **39**（去重内部目标模块数；import 名 44 条 / import 语句 63 条） | ✔ | `... repro_ast.py` |
| 6 | `adapters/webui/assets.py` 行数 | 14917 | **15679 行**（14917 是**非空行**数，空行 762） | ✘ **被推翻** | `Get-Content module\adapters\webui\assets.py \| Measure-Object -Line` |
| 7 | `pytest unit_tests -q` 收集用例数 / 退出码 | 0 用例 / exit 5 | **0 用例 / exit=5**（`.venv313` 与 `.venv` 都是 5） | ✔ | `.venv313\Scripts\python.exe -m pytest unit_tests -q` |
| 8 | `.venv313` + 显式全部 `*_case.py` 结果 | 702 passed | **702 passed, 1 warning, 27 subtests passed in 79.28s, exit=0**（66 个文件） | ✔ | 见下方命令 |
| 9 | 全量测试原生崩溃 0xC0000005 | — | **确认存在，但根因是解释器，不是测试** | 事实修正 | 见 §0 |

### 逐条说明

**#1 被推翻（最重要）**。我用了三种独立方法：

- v1 AST（丢弃 `from . import x`，错误）→ 0 环；
- v2 AST（正确枚举 `from pkg import submodule` 与 `from . import a,b`）→ **398 边，3 个非平凡 SCC**；
- 字节码法（`dis` 的 `IMPORT_NAME`/`IMPORT_FROM`，不使用 ast）→ 同样判定**有环**。

三个环与证据行：

| 环 | 边 A | 边 B | 运行期是否致命 |
|---|---|---|---|
| `module.core.filter` ⇄ `module.core.media_types` | `module/core/filter.py:11` `from module.core import media_types as media_types_mod`（模块级） | `module/core/media_types.py:69` 与 `:80` `from module.core.filter import MessageFilter`（**函数内延迟导入**） | 否 |
| `module.app` ⇄ `module.core.app` | `module/app.py:10` `from module.core.app import Application, DownloadFileName`（模块级，兼容垫片） | `module/core/app.py:30` `from module import app as app_module`（**函数 `get_extension()` 内延迟导入**） | 否（且 `module.app.get_extension` 实际 re-export 自 `utils/path_tool`，不递归） |
| `module.adapters.webui.server` ⇄ `module.adapters.webui.handlers`(+子模块) | `module/adapters/webui/server.py:441` `from module.adapters.webui.handlers import (...)`（**`start()` 内延迟导入**） | `module/adapters/webui/handlers/tasks.py:7`、`misc.py:8` 等 8 个文件 `from module.adapters.webui.server import WebUiApiError`（**模块级**）；`handlers/__init__.py:4` `from . import (...)` 引出 10 个子模块 | 否 |

口径说明（重要，避免误判）：3 个环都**至少有一条边是函数内延迟导入**，所以运行期不会 `ImportError`——这正是它长期没被发现的原因。但"import 图无环"作为一个静态依赖断言是**假的**；架构守卫的环检测正是漏掉了它们（见 §3）。

**#2 一致**。`*_getter` 实参 50 个，分布在 **8 个调用表达式**、涉及 **25 个不同 getter 名**：
`WebUITaskManager` 19、`TransferProgressTracker` 10、`PikpakIntegrationManager` 8、`CallbackHandler` 7、`LiveWatchManager` 6（19+10+8+7+6=50）。
前几处证据：`composition_root.py:95`（LiveWatchManager）、`:114`（PikpakIntegrationManager）、`:125`（TransferProgressTracker）、`:141`（CallbackHandler）、`:156`（WebUITaskManager）。

**#3 一致，但口径必须写明**。裸 `self._host` 只出现 18 次，`self._host.<attr>` 仅 2 次；真正的大头是**局部别名**：
`host = self._host` 出现在 12 处（行 107/118/132/153/560/598/658/691/729/1321/1486/1503），随后 `host.<attr>` 访问 126 次。
126 + 2 = **128**，与对方一致。补充（这是本项最有价值的信息）：被访问属性只有 23 个，其中 `host.transfer_store` **一个属性占 71 次**（126 次里的 56%）；访问集中在 `transfer_message_to_web_target()`（55 次）和 `process_task()`（41 次）。

**#4 口径需修正**。`WebOperationsMixin` **直接定义方法 114 个**（其中 13 个 async，27 个 `_` 前缀，无重名）；类内还嵌套 4 个闭包：`_stale_logger`(L136)、`executor`(L174)、`on_cancel`(L216)、`_media_ok`(L1711)。114+4=118，对方大概率是"类子树内全部 `def` 节点"。同文件另有 `WebOperationsFacade`(1 个方法)、`operations.py` 全文 `def` 节点 122 个 → 都不可与"方法数"混用。

**#5 一致**。去重内部目标模块 **39** 个（含包 `module` 本身；剔除它则为 38）。同文件 import 语句 63 条、内部 import 名 44 条。`module.downloader` 出度 39 是全仓最高（第二名 `composition_root` 29）。

**#6 被推翻**。`assets.py` 真实行数 **15679**（`wc -l` 口径；文件以换行结尾），**非空行 14917**，空行 762。14917 是"非空行/代码行"指标，被当成"行数"上报。两种口径 PowerShell 与 Python 互相印证：

```
Get-Content module\adapters\webui\assets.py  -> 15679 行；非空 14917；空行 762
```

**#7 一致**。仓库没有 `conftest.py`，`pyproject.toml` 也没有 `[tool.pytest.ini_options]`（只有 `[tool.hatch.build.targets.wheel]` 与 `[tool.uv]`），pytest 默认 `python_files=test_*.py`，而 `unit_tests/` 下 `test_*.py` 数量为 **0**，`*_case.py` 为 **66** → 收集 0 用例，pytest 以 `exit=5`（no tests collected）结束。

```
> .venv313\Scripts\python.exe -m pytest unit_tests -q
no tests ran in 0.02s
EXIT313=5
> .venv\Scripts\python.exe -m pytest unit_tests -q
no tests ran in 0.02s
EXIT314=5
```

**#8 一致**。

```
> .venv313\Scripts\python.exe -m pytest (全部 66 个 *_case.py) -q
702 passed, 1 warning, 27 subtests passed in 79.28s (0:01:19)
EXIT=0
```

顺带发现（非本次审查目标，但有价值）：唯一 warning 是一条真实缺陷信号——
`unit_tests/web_task_deferred_pause_case.py::WebTaskDeferredPauseCase::test_recover_pausing_without_active_item_converges_to_paused`
报 `RuntimeWarning: coroutine 'TelegramUploader.send_media_worker' was never awaited`（该**协程从未被 await**，即代码里存在忘记 await 的调用）。

**#9 事实修正**。0xC0000005 确实存在，但**不是测试基础设施缺陷、不是产品缺陷**，而是"用了 `.venv`（3.14.0a5）+ 不兼容的 `_yaml` C 扩展"。我**不需要二分**就不存在"某个测试文件组合触发崩溃"：崩溃与测试内容无关，只与"是否 import `module`"有关——这是单点根因，二分是多余动作。正确基线是 `.venv313`，702 passed。

## 2. 横向危害分析：`transfer_store` 时序耦合与初始化顺序

### 2.1 赋值时机与写入点全集（AST 穷举 `module/`，共 6 处）

| 文件:行 | 语句 | 角色 |
|---|---|---|
| `module/composition_root.py:81` | `self.transfer_store: Union[TransferStore, None] = None` | 构造期初始化为 **None** |
| `module/adapters/webui/operations.py:117` | `self.transfer_store = store` | 懒创建（`_ensure_transfer_store()`）|
| `module/adapters/webui/operations.py:120` | `ctx.transfer_store = store` | **唯一修复 ctx 的同步之一** |
| `module/adapters/webui/operations.py:1117` | `self.transfer_store = TransferStore(directory=self.app.temp_directory)` | WebUI 启动赋值点 |
| `module/adapters/webui/operations.py:1124` | `ctx.transfer_store = self.transfer_store` | **另一个同步** |
| `module/adapters/pikpak/archive_author.py:106` | `self.transfer_store = transfer_store` | 另一实现（见 §2.4）|

**`module/downloader.py` 与 `module/web_ui.py` 里没有任何 transfer_store 赋值点。** `module/web_ui.py`（570 B）只是 `from module.adapters.webui.server import ...` 的兼容垫片。WebUI 路径的真实赋值点是 `operations.py:1117`，由 `downloader.py:1838` 的 `start_web_ui(with_auth_provider=True, defer_runtime_recovery=True)` 触发；CLI 路径 `downloader.py:1814` 也调 `start_web_ui()`，但见 §2.3。

### 2.2 逐消费者清单：getter 延迟取（安全） vs 值捕获（危险）

| 消费者 | 位置 | 传递方式 | 判定 |
|---|---|---|---|
| `LiveWatchManager` | `composition_root.py:95-101` | `transfer_store_getter=self._transfer_store` | 安全（延迟取，`_transfer_store()` 在 `:225-226` 用 `getattr` 兜底）|
| `PikpakIntegrationManager` | `:114-124` | getter | 安全 |
| `TransferProgressTracker` | `:125-140` | getter | 安全 |
| `CallbackHandler` | `:141-152` | getter | 安全 |
| `WebUITaskManager` | `:156-184` | getter | 安全 |
| **`TransferContext`** | **`:185-198`，关键在 `:193` `transfer_store=self.transfer_store`** | **值捕获** | **★危险**（构造期捕获 `None`）|
| `_create_standalone_transfer_engine` | `:509-526`，关键在 `:521` `getattr(self, "transfer_store", None)` | **值捕获进一个"新建的 ctx"** | **★危险且不可修复** |
| `TransferEngine.transfer_store` | `transfer/engine.py:57-59` `return self.ctx.transfer_store` | 读上面那个 ctx | 受害者 |
| `transfer/runner.py` `host.transfer_store` | 72 处 | 直接属性读（**不是** getter） | 逐点看保护 |

### 2.3 真实可触发顺序 —— 运行时取证（`probe_timing_runtime2.py`，`.venv313`）

取证 A（CLI 模式）：
```
PARSE_ARGS.web = None
调用 host.start_web_ui() 后 host.transfer_store = None
```
`operations.py:1113-1115` 首行 `if PARSE_ARGS.web is None: return` → **CLI 模式下 WebUI 启动赋值点根本不执行**，`transfer_store` 只能靠 `_ensure_transfer_store()` 懒创建（调用点：`archive_author_ops.py:50,111`；`operations.py:172,238,256,1826,1831,1839,1851`）。

取证 B（值捕获 + 懒修复）：
```
构造后 ctx.transfer_store            = None          <- composition_root.py:193 值捕获
构造后 host._te.transfer_store       = None
_ensure_transfer_store() 返回        = TransferStore
修复后 ctx.transfer_store (同步过)   = TransferStore  <- operations.py:120
修复后 _te.transfer_store            = TransferStore  <- 因为 _te.ctx is host.ctx（同一对象）
```
即：正常主路径上，`:193` 的值捕获**会被 `operations.py:120/1124` 的显式同步修好**，因为 `_te` 与 host 共享同一个 ctx 对象。

取证 C（无保护消费者在 `None` 时的真实行为）：
```
skip_transfer_item_for_target_limit:      AttributeError: 'NoneType' object has no attribute 'add_item'  @ engine.py:428
skip_transfer_item_for_media_type:        AttributeError: 'NoneType' object has no attribute 'add_item'  @ engine.py:457
skip_missing_web_transfer_range_message:  AttributeError: 'NoneType' object has no attribute 'add_item'  @ engine.py:493
refresh_transfer_task_counts:             正常返回 None（guard 生效）
```
静态扫描（`repro_transfer_store_timing.py`）：`engine.py` 共 19 处 `self.transfer_store` 访问，分属 7 个方法，其中 **3 个方法完全无 None 保护**（`:428`、`:457`、`:493`）；`download_complete_callback()` 的 4 处被 `:618 if isinstance(with_upload, dict) and self.transfer_store:` 真值保护（我的启发式把它误标为无保护，此处更正）。`runner.py` 有 72 处 `host.transfer_store`，主入口 `process_task()` 在 `:154 if not host.transfer_store: return` 处提前返回。

**触发可达性结论（诚实版，不夸大）**：这 3 个无保护的 engine 方法，其调用者全部在 `transfer/runner.py` 的 `transfer_message_to_web_target()`（`:815/:1042/:1072/:1088`、`:804/:1031/:1060`）与 `_ensure_range_message_accounted()`（`:1539`）内，而这些都位于 `process_task()` 的 `:154` 保护之后；`host.skip_transfer_item_for_target_limit` 的唯一外部入口 `downloader.py:591` 也由 runner 调用。因此**我未能构造出生产路径上"store 为 None 时走到这 3 个方法"的真实顺序**——缺陷存在，但当前被两层偶然保护（`:154` 的 guard + `operations.py:120/1124` 的显式同步）遮盖。

**但下面这条是可运行的、无遮盖的**（取证 D）：
```
standalone engine.ctx is h4.__dict__.get('ctx') = False
standalone engine.transfer_store (构造当时)      = None
修复后 h4.transfer_store                          = TransferStore
修复后 h4.__dict__['ctx'].transfer_store          = TransferStore
修复后 standalone engine.transfer_store          = None   <- 仍旧 None，值捕获冻结
```
`_create_standalone_transfer_engine()`（`composition_root.py:492`，docstring 自述用于 "tests and recovery"）**新建了一个 ctx**（`:509`），`:521` 把当时的 `transfer_store`（None）值捕获进去；而仅有的两个修复点 `operations.py:1122-1124` 只写 `self.__dict__['ctx']`，**永远碰不到这个 standalone ctx**。于是半构造 host（`__new__` 出来的对象，正是测试的构造方式，见 `unit_tests/downloader_transfer_record_case.py:29`）一旦先访问 `transfer_engine` 属性，就会拿到一个 store 永久为 None 的引擎。这条是"值捕获式时序耦合"的真实、可复现实例。

### 2.4 host 双实现路径（顺带发现，属 A1/A2 交界）

`module/adapters/pikpak/archive_author.py:106` 也写 `self.transfer_store = transfer_store` —— 这是 `transfer_store` 的**第二个宿主**，与 `composition_root`/`operations` 的写入点是两套独立实现；`module/adapters/pikpak/integration.py` 用的是 getter（12 处提到 transfer_store）。同一依赖"有时 getter、有时值捕获、有时第三方宿主自己赋值"是本次审查里最典型的耦合形态。

## 3. `unit_tests/architecture_guard_case.py` 能力边界判定

它共 7 项检测（全部为纯 AST/文件系统检查，无运行时导入）：

| # | 测试 | 检测内容 | 本次审查中它**覆盖不到**的 |
|---|---|---|---|
| 1 | `test_module_import_graph_has_no_cycles`（:158） | 用 `_import_graph()` + 手写 Tarjan 判定无环 | **完全失效**：自身图构造有 3 个缺陷（下详），实测 0 环，而真实图有 3 个环 |
| 2 | `test_subpackages_do_not_import_top_level_shims`（:198） | 子包不得 import 顶层垫片 | 漏 `from module import <shim>` 形式（实测漏 1 条：`module/core/app.py:30 from module import app`，而 `app` 正在 `OLD_TOP_LEVEL_NAMES` 中）|
| 3 | `test_no_layer_inversions`（:221） | 层间方向（白名单矩阵） | 白名单里 `adapters` 允许依赖全部 7 层、`transfer` 允许依赖 6 层 → "层不反转"几乎只禁止 core→adapters 一类明显反向；`adapters -> adapters` 32 条、`adapters -> core` 22 条这类**同层/向下巨量耦合**它视为正常；且它继承 #1 的图缺陷 |
| 4 | `test_composed_host_resolves_every_attribute_read`（:248） | 4 个 host 类 + 1 个代理类里 `self.<attr>`/`host.<attr>` 的**名字**是否都有定义 | **名字级检查，无值/时序语义**：`transfer_store` 在 `composition_root.py:81` 有定义即算"已解析"，于是 §2 的值捕获 None 完全不可见；也不检查"定义在哪个类/哪个宿主"，**host 双实现路径**（`archive_author.py:106` 与 `operations.py:117`）互相不可见；`utils/` 被整层排除 |
| 5 | `test_composition_root_has_no_reflective_getattr`（:288） | 禁止 `def __getattr__`、`self.__dict__.get`、要求 `_build_transfer_ports()` 存在 | 只管**禁用模式**，与耦合强度无关；`getattr(self, "x", None)` 这种写法（`composition_root.py:521` 等）它不限制 |
| 6 | `test_transfer_ports_have_no_host_reflection`（:295） | `transfer/context.py` 里不得出现 `from_host` | 字符串级检查；**Protocol 无约束力**完全不在覆盖范围：`ports.py`/`context.py` 的 Protocol 只是类型标注，运行期不做校验，任何 host 属性访问都不受它约束 |
| 7 | `test_top_level_contains_only_facade_and_shims`（:300） | `module/` 顶层只剩 6 个真文件 + 兼容垫片 | 只约束**文件名集合**，不约束内容/耦合 |

### 3.1 检测 #1 的三个具体缺陷（实测，不是推断）

缺陷 a：`_import_graph()`（`:61-76`）对 `ast.ImportFrom` **只取 `node.module`，完全丢弃被导入的名字**：
```python
elif isinstance(node, ast.ImportFrom):
    aliases = [node.module or ""]     # <- 丢掉了 node.names
```
于是 `from pkg import submodule` 不会产生 `-> pkg.submodule` 的边。实测丢失的边（`repro_guard_gaps.py`）：
```
module.adapters.webui.server:441  from module.adapters.webui.handlers import (auth, ..., static_pages)
module.core.app:30                from module import app
module.core.filter:11             from module.core import media_types
```

缺陷 b：`_resolve()`（`:47-58`）**没有把 `__init__.py` 当包处理**，相对导入整体偏移一级。实测 `__init__.py` 中相对导入语句共 1 条，**唯一这条就解析错了**：
```
module.adapters.webui.handlers:4  from . import (archive_author, auth, ...)
    守卫 -> 'module.adapters.webui'      （错：父包）
    正确 -> 'module.adapters.webui.handlers'（+ 10 个子模块）
```
叠加缺陷 a（`node.module` 为 None → alias `""` → `_resolve` 返回 None），这 10 条子模块边**一条都没建出来**。

缺陷 c：检测 #2（`:214`）用 `alias.startswith("module.")` 过滤，`from module import app` 的 alias 是 `"module"`（不以 `"module."` 开头）→ 直接跳过。

实证：把守卫**自己的**图跑 Tarjan，得到 `384 边 / 0 环`（所以它的断言通过）；用正确解析得到 `398 边 / 3 环`。也就是说，**"import 图无环"这条架构断言目前是一个假阳性**，它测的是自己那张丢了 14 条边的图。

### 3.2 它完全防不住的四类本次发现

1. **值捕获式时序耦合**：`composition_root.py:193`、`:521`。名字级检查（#4）恒判"已定义"。
2. **host 双实现路径**：`archive_author.py:106` vs `operations.py:117/1117`。没有任何一项检查"同一属性的多个写入宿主"。
3. **Protocol 无约束力**：`ports.py`/`context.py` 的类型契约运行期不校验，7 项里没有一项做运行期/结构一致性校验。
4. **测试收集失效（元级盲区）**：`pytest unit_tests -q` 收集 0 用例、exit=5，守卫**一次都没跑**；而它自身无法检测"我没被执行"。这是最反讽的一条：一个用于防架构腐化的守卫，因为仓库没有任何 pytest 配置而形同虚设。

## 4. 复现命令清单

```powershell
# 环境事实
.venv\Scripts\python.exe -c "import yaml"                       # exit=-1073741819
.venv313\Scripts\python.exe -c "import yaml; print(yaml.__version__)"   # 6.0.3, exit=0
.venv\Scripts\python.exe -v -c "import module"                  # 崩在 _yaml.cp314-win_amd64.pyd

# 测试基线
.venv313\Scripts\python.exe -m pytest unit_tests -q             # no tests ran, exit=5
$f = Get-ChildItem unit_tests -Filter *_case.py | % FullName
.venv313\Scripts\python.exe -m pytest @f -q                     # 702 passed

# 数值复现
.venv313\Scripts\python.exe -X utf8 tmp\coupling-audit\04-verify\repro_ast.py
.venv313\Scripts\python.exe -X utf8 tmp\coupling-audit\04-verify\repro_host_runner.py
.venv313\Scripts\python.exe -X utf8 tmp\coupling-audit\04-verify\repro_import_graph_v2.py
.venv313\Scripts\python.exe -X utf8 tmp\coupling-audit\04-verify\repro_import_bytecode.py
.venv313\Scripts\python.exe -X utf8 tmp\coupling-audit\04-verify\repro_transfer_store_timing.py
.venv313\Scripts\python.exe -X utf8 tmp\coupling-audit\04-verify\probe_timing_runtime2.py
.venv313\Scripts\python.exe -X utf8 tmp\coupling-audit\04-verify\repro_guard_gaps.py
.venv313\Scripts\python.exe -X utf8 tmp\coupling-audit\04-verify\repro_guard_resolve_bug.py
```

## 5. 本次新发现（按重要性）

1. **架构守卫的"无环"是假阳性**（`unit_tests/architecture_guard_case.py:61-76` + `:47-58`）：实测真实图有 3 个 SCC，守卫自建图 0 个。三个环中 2 个跨层（`core` 内部、`app`/`core.app`、`adapters.webui.server` ⇄ `handlers`）。这是"用错误口径通过测试"的教科书案例。
2. **值捕获式时序耦合 + 不可修复的 standalone ctx**（`module/composition_root.py:193` 与 `:521`，修复点仅 `operations.py:120/1124`）：运行时证明 standalone 引擎的 `ctx.transfer_store` 永久为 None，后续任何同步都修不到它；`engine.py:428/457/493` 三处在 None 下必抛 `AttributeError`。
3. **`assets.py` 行数口径错误**：15679（真实）vs 14917（非空行）。
4. **`_yaml.cp314` + 3.14.0a5 alpha = 0xC0000005**：`.venv` 是被污染的解释器，任何在它上面得出的结论都不可用。
