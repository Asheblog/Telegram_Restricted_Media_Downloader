# TRMD 耦合度审查报告

- 仓库：`E:\codebase\tgbot` · 审查基线：`HEAD = 1f7a43b`（0.2.248）
- 方式：**只读分析**。`module/` 与 `unit_tests/` 零改动（`git diff --stat HEAD -- module unit_tests` 为空），无 commit
- 有效解释器：`.venv313\Scripts\python.exe`（3.13.7）。**`.venv` 是 Python 3.14.0a5 且 PyYAML C 扩展 ABI 不匹配，`import module` 即 0xC0000005**，其结论一律不可用
- 测试基线：`.venv313` + 显式传 66 个 `*_case.py` = **702 passed / 27 subtests / 79s / exit 0**
- 取证分工：A1 门面·host / A2 adapters·域 / A3 构建·前端·测试基建 / A4 独立复现·时序·对抗性验证（A4 抽查 32 项，27 项精确吻合，5 项已修正或标注口径）

---

## 结论

**这个项目"看起来解耦了，但缝是假的"。**

导入图、层规则、Protocol、组合根、facade —— 解耦需要的形状全都在，`architecture_guard_case.py` 也逐条守着。但真正的耦合没有被消除，而是被**转移**到了三种守卫看不见的形态里：

1. **值 / 字符串形态**：50 个 `*_getter` 回调、40 个 `setattr` 生成的 facade 方法、35 处 `_operation("字符串名")`。名字写错不报错，表现为 503「服务不可用」。
2. **时序形态**：`transfer_store` 构造期被当成值捕获（`composition_root.py:193`、`:521`），靠 `operations.py:120/1124` 两处手工同步补救。
3. **测试基建形态**：`pytest unit_tests` 收集 0 个用例且 exit=5 —— 那个用于防腐化的守卫，因为仓库没有任何 pytest 配置，**从未在默认流程里执行过**。

代价已有硬数据兑现：120 个提交里 67% 跨 ≥2 层；一个前端端点改动要动 20 个文件 / 6 层。

---

## P0 — 真正严重的

### 1. 上帝对象：单个 host 承载 276 个方法，且没有合法的构造路径

| 度量 | 数值 | 证据 |
|---|---|---|
| 四个类合计方法定义 | **276**（downloader 89 / WebOperationsMixin 114 / composition_root 51 / BotHostMixin 22） | `tmp/god_object_surface.py` |
| `composition_root` 传给下游的 `*_getter` 回调 | **50**（分属 8 个调用、25 个 getter 名） | `composition_root.py:95-184`；A4 复现一致 |
| `composition_root` 内 kwarg / self 状态槽 | **199 / 49** | A1 evidence |
| `WebTransferRunner` 读 host 属性 | **128**（23 个属性，其中 `transfer_store` 独占 71 次 = 56%） | `runner.py` 12 处 `host = self._host` + 126 次 `host.x`；A4 复现一致 |
| `LiveTransferService` 经 `__getattr__` 落到宿主 | **33 个名字 / 125 个读点**（占其 self 读点 82%），含 5 个 facade 私有方法 | `live_transfer.py:91-92` |
| 测试如何拿到 host | **90 处 `object.__new__(...)`**，手工塞属性；`unit_tests` 里**完整构造 0 次** | `web_task_delete_case.py:72-107` 等 |

为什么是耦合：`TelegramRestrictedMediaDownloader` 同时是门面、组合根、业务编排器、Bot 宿主。协作者拿到的不是接口，而是这个对象本身，因此**任何协作者都能读它任意 276 个方法中的任意一个**，编译器与 IDE 全程无法介入。

最小改进（按性价比排序）：
- **(a)** 给 host 加一个测试构造器（如 `build_for_test(**overrides)`），把 90 处 `__new__` + 手工塞属性收敛到一个地方。这一步单独就能止血，不需要动架构。
- **(b)** `composition_root.py:234-318` 的 3 个 `_require_*` 各抄了一份完整构造（80 行），且 `_create_standalone_transfer_engine` 重写 25 个端口字段、兜底全是静默 `noop`。删掉 standalone 兜底路径，改为在缺少依赖时**大声失败**。

### 2. 假缝：三层字符串键派发 + 零约束力的 Protocol

一次 WebUI 请求的调用链：

```
handlers/*.py
  → WebUiServer.<method>                       # 2033 行
  → self._operation("create_upload")           # server.py:287，35 个调用点
  → WebOperationsFacade                         # 40 个方法由 setattr 生成
  → getattr(host, name)                         # 276 方法对象，无类型约束
```

- `WebOperationsFacade` 类体内只有 `__init__`，**40 个方法全部在 `operations.py:1896-1897` 用 `setattr` 反射生成**。
- 实测：`_operation("create_upload")` → method；`_operation("create_upload_typo")` → **`None`，不抛异常**；`server.create_upload()` 随后抛 `error_code='upload_operations_unavailable'`、**HTTP 503「Upload operations are unavailable」** —— 接线错误被伪装成服务故障。
- `ports.py` 的 **9 个 Protocol 零约束力**：全仓 `isinstance`/`issubclass` 针对 Protocol 命中 **0**；`IWebUiOperations` 只覆盖 facade 实际表面的 **19/40（47.5%）**，21 个方法没有端口声明；`WebTransferHost`、`WatchApplicatorHost` 同样只有注解、0 处运行时校验。
- 好消息：现存 35 个派发点的名字**全部与实际实现对得上**（我做了实测审计），所以这不是活跃 bug，而是"任何一次改名/新增都会静默出错"的结构风险。

最小改进：把 `_operation(name)` 改成在 `None` 时抛 `WebUiApiError("operation_not_wired", 500)`，并加一个覆盖全部 35 个调用点的名字一致性测试（可直接复用我写的审计逻辑）。这能在不改架构的前提下，把"静默 503"变成"启动即失败"。

### 3. 架构守卫的核心断言是假阳性：真实存在 3 个导入环

`architecture_guard_case.py:158` 断言 "import 图无环"，但它自建的图**丢了 14 条边**：

| 缺陷 | 位置 | 后果 |
|---|---|---|
| `ast.ImportFrom` 只取 `node.module`，丢弃 `node.names` | `:61-76` | `from pkg import submodule` 的边全丢 |
| `_resolve()` 没把 `__init__.py` 当包 | `:47-58` | 相对导入整体偏移一级 |
| 用 `alias.startswith("module.")` 过滤 | `:214` | `from module import app` 直接跳过 |

实测：守卫图 **384 边 / 0 环**（所以断言通过）；正确图 **398 边 / 3 环**：

| 环 | 边 A | 边 B |
|---|---|---|
| `core.filter` ⇄ `core.media_types` | `filter.py:11`（模块级） | `media_types.py:69/80`（函数内延迟导入） |
| `module.app` ⇄ `module.core.app` | `app.py:10`（模块级） | `core/app.py:30`（函数内延迟导入） |
| `adapters.webui.server` ⇄ `handlers/*` | `server.py:441`（函数内） | `handlers/tasks.py:7`、`misc.py:8` 等 8 文件（模块级） |

诚实边界：3 个环都至少有一条边是函数内延迟导入，所以**运行期不会 ImportError**，危害是"静态架构断言失去意义，守卫的信用被高估"。

同一守卫还漏掉唯一一条真实违规：**`core/app.py:30` 在函数内 `from module import app as app_module`，反向依赖顶层遗留 shim `module.app`** —— 而 `app` 就在 `OLD_TOP_LEVEL_NAMES` 里。该包装器被 `core/app.py:330/364/368/419` 调用，位于**每个媒体文件生成文件名的热路径**上。守卫的 `test_subpackages_do_not_import_top_level_shims` 因为第 3 个缺陷看不见它。

---

## P1 — 会持续放大成本的

### 4. `WebTransferRunner` 的"兜底"是死代码，同一语义有两份实现

```python
# module/transfer/runner.py:80-86
instance_method = getattr(self._host, name)
class_method = getattr(host_type, name, None)
if instance_method is not class_method:   # 对普通方法恒为真
    return instance_method
return getattr(self, name)                # ← 永远不执行
```

`bound method is class function` 对普通方法恒为 `False`，所以宿主实现永远优先。实测：宿主缺少该属性时抛 `AttributeError`，**本地兜底不会被使用** —— "兜底"保障是假的。4 个双实现方法中 3 个与宿主同名，且判定依据已分歧：`web_task_manager` / `transfer_store.get_task` / `transfer_store.get_item` 三种。

### 5. 前端资源：1.2 MB 生成物提交进仓，且没有任何守门

- `module/adapters/webui/assets.py` = **15,679 行 / 1,203,917 B**，占 `module/` 全部 Python 字节的 **41.4%**；只有 4 个常量，`tailwind.min.css` 内联 3 份（302,673 B）、字体 base64 占 18.5%。
- 源文件在 `templates/` + `static/`（23 个），生成器是 `build_frontend.py` —— **Dockerfile / build.py / package.json / CI 里都没有调用它**，是纯手工步骤。
- 当前**逐字节同步**（A3 用纯函数在内存重建后比对，sha 全等），但**零守门**：43 个 UI 测试 0 次引用源文件，测的是生成的副本；CI 只有 tag 触发的 Docker 构建。
- ⇒ 改前端源文件忘记重新生成 → **测试全绿 + 页面陈旧**，没有任何机制能发现。A3 已交付可运行的检测器 `tmp/coupling-audit/03-build/check_frontend_drift.py`（灵敏度已验证：往内存里加 1 行 CSS 即报不同步）。
- 影响面：近 200 个提交中它被改 **141 次（70.5%）**，`+10,793/−3,082` 行 = 全仓 churn 的 13.1%，单次最大 diff **2,215 行**（机器生成，reviewer 无法真正审阅）。

### 6. 工具链与测试基建

| 问题 | 证据 | 影响 |
|---|---|---|
| 无 `[tool.pytest.ini_options]`，测试命名 `*_case.py` | `pytest unit_tests -q` → `no tests ran`，**exit=5**（两个 venv 都是 5）；显式传 66 个文件 → 702 passed | 702 个用例 + 唯一架构守卫**默认从不执行**；`exit=5` 在"无测试"与"测试失败"之间极易被忽略 |
| 双解释器，默认那个是坏的 | `.venv` = **3.14.0a5**，`_yaml.cp314-win_amd64.pyd` 扩展初始化即 **0xC0000005**；`build.py:95-111` 明确拒绝 `≥3.14`；`pyproject` 无上界 | 任何 `import module` 的操作原生崩栈（不可读报错）；极易被误判为"产品/测试坏了"（本次审查开始时我就踩了这个坑） |
| 唯一 CI 不含测试 | `.github/workflows/` 只有 `release_docker.yml`（tag 触发） | 回归只能靠人工 |

修复只需 4 行：`pyproject.toml` 加 `[tool.pytest.ini_options]` 的 `python_files = ["test_*.py","*_test.py","*_case.py"]` + `testpaths = ["unit_tests"]`。

### 7. 遗留 shim 与"双份真相"

- `module/` 顶层 **39 个兼容 shim**，生产代码只剩 **2 处**引用（`main.py:8`、`scripts/diagnose_pikpak_forward.py:98`），38/39 生产零引用；但 `unit_tests` 引用 **160 处 / 29 个**。
- 24/39 个 shim 用 `import *`，而 `module/` 只有 10/145 个文件定义 `__all__` → `module.uploader.asyncio` 这类名字泄漏。
- 守卫用注释字符串 `"Compatibility shim"` 来分类 shim —— 改注释即改规则。

---

## P2 — 值得修，但不紧急

- **时序耦合**：`composition_root.py:193` 把 `transfer_store`（当时为 `None`）值捕获进 `TransferContext`；`:521` 的 standalone 引擎把 `None` 捕获进**新建的 ctx**，而仅有的修复点 `operations.py:120/1124` 只写 `self.__dict__['ctx']`，**永远够不到它** → 运行时证明该引擎的 `transfer_store` 永久为 `None`，`engine.py:428/457/493` 在 `None` 下必抛 `AttributeError`。诚实边界：生产路径上被 `runner.py:154` 的 guard 遮盖，未构造出真实触发顺序。
- **死抽象**：`TransferContext.build()`、`resolve()`、`downloader_callbacks` 全仓零调用 —— 一个"替代 50 个 getter"的设计（docstring 自述）从未被使用。
- **接线两套**：同一个 `WebUITaskManager` 在 `operations.py:73-99` 与 `composition_root.py:156-184` 各接线一次（21 项 vs 27 项），6 个 getter 只在主路径存在 → 走兜底时功能静默缺失。
- **私有方法越界**：`archive_author_ops.py:50/57/111` 依赖 `host._ensure_transfer_store()` / `host._run_telegram_coro`，且用 `try/except` 兜底会吞掉 store 初始化的真实错误。

---

## 健康的部分（经度量确认，不是客套）

- **领域层是真解耦的**：`domain/archive_naming/source_folders.py` 1,102 行 / 41 函数 / 被 23 个文件依赖，但模块外依赖只有 3 个 → 判为**深模块，不是垃圾桶**。
- **`IBotCallbackHost` 是精确端口**：19 个成员 **19 个都被使用**（63 处访问），0 个声明未用、0 个用了未声明。团队**会**写端口 —— 问题在于 WebUI 路径整体绕开了端口。
- **守卫确实防住了它宣称的两件事**：禁止子包 import 顶层 shim（除上面那 1 条例外）、`test_composed_host_resolves_every_attribute_read` 能挡住 `187d1d8` 那类 AttributeError 回归（该事故曾导致机器人整体离线，事后用 3 个提交 / 22 文件 / 332 行抢修）。
- **`adapters/pikpak/archive*.py` 对 host 私有 API 命中为 0**，比预期干净（A2 主动证伪了我在任务里的假设）。
- **三个 mixin 之间 0 个同名方法冲突**，MRO 干净。

---

## 建议的最小行动顺序

| 优先 | 动作 | 成本 | 收益 |
|---|---|---|---|
| 1 | `pyproject.toml` 加 pytest 配置（4 行） | 分钟级 | 702 个用例 + 架构守卫回到默认流程 |
| 2 | 修复 guard 的 `_import_graph`/`_resolve`（约 20 行），让"无环"与"不 import shim"成为真断言 | 小时级 | 恢复架构断言的可信度；暴露 `core/app.py:30` |
| 3 | 接入 `check_frontend_drift.py` 作为测试/CI 步骤 | 小时级 | 消除"改源忘重生成"的静默故障类 |
| 4 | `_operation(name)` 未命中时改为显式抛错 + 35 个调用点的名字一致性测试 | 半天 | 把静默 503 变成启动即失败 |
| 5 | 给 host 加测试构造器，收敛 90 处 `object.__new__` | 1-2 天 | 测试可维护性；为后续拆分解锁 |
| 6 | 删 `_create_standalone_transfer_engine` 静默兜底，缺依赖就大声失败 | 1 天 | 消除"归档没发生 / 窗口没释放"这类无声故障 |
| 7 | 删死抽象（`TransferContext.build/resolve/downloader_callbacks`） | 分钟级 | 减少误导 |

**不建议**做的：把 `WebOperationsMixin` 整体搬到新包、给 `assets.py` 做"包搬家"式重构。前者是纯移动、不解决字符串派发这一根因；后者只换个位置、不减少 churn（churn 来自"每次前端改动都重写整个内联产物"，应改为运行时读取文件或构建时生成到 `dist/`）。

---

## 附：核对边界（诚实声明）

本报告正文引用的每个数字，我都**亲自用 Python 复核过一遍**（PowerShell `Get-Content | Measure-Object -Line` 口径偏低，不可用于行数）。下列为已知的队友间口径问题，均**不影响正文结论**，但记录在此以免被误用：

- A1 报告称 `self.__dict__.get(...)` 有 12 处，A4 判其"逐行吻合"；**实仓 grep 只有 1 处**（`downloader.py:177`）。这是本次审查里唯一发现的"二级验证失效"样本 —— 说明抽样验证不能替代自己复算。
- A1 称 `object.__new__` 骨架 92 处；实测 **90** 处（`unit_tests/*.py`）。口径未披露。
- A2 称 `ports.py` 有 7 个 Protocol；实为 **9**（漏计 `IUploadContext`、`IDiagnosticPort`）。A2 关于"零约束力"的结论不受影响。
- A3 称 60/66 个测试依赖 `pyrogram_stub`；分子含桩文件自身，应为 **59/66**。
- A2 的"40 个非 chore 提交"与我的"120 个提交中 67% 跨层"口径不同（过滤规则不同），两者不矛盾但不可混用。
- **"import 图无环"这条断言来自 `CONTEXT.md` 与 `architecture_guard_case.py` 的自述，A1/A2/A3 三份证据都没有传播它**；推翻它的工作全部属于 A4。

## 附：证据文件

| 文件 | 内容 |
|---|---|
| `tmp/coupling-audit/01-host/evidence.md` | 803 行，11 条 host 耦合 + 5 条度量否证 + 16 个可复现脚本 |
| `tmp/coupling-audit/02-adapters/evidence.md` | 724 行，adapters/域耦合 + 变更放大实测（真实提交号） |
| `tmp/coupling-audit/03-build/evidence.md` | 742 行，F1–F8 构建/前端/测试基建 + `check_frontend_drift.py` |
| `tmp/coupling-audit/04-verify/verify.md` | 独立复现表、时序耦合运行时取证、守卫 7 项能力边界 |
| `tmp/coupling-audit/04-verify/challenges.md` | 对 A1/A2/A3 的逐条挑错（32 项抽查，27 项吻合，5 项修正） |
| `tmp/coupling-audit/*/raw_*.txt`、`probe_*.py` | 原始命令输出与可复跑探针 |
