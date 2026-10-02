# A4 对抗性抽查：对队友证据的挑错清单

- 抽查对象：`tmp/coupling-audit/02-adapters/evidence.md`、`tmp/coupling-audit/03-build/evidence.md`
- 抽查方式：不读结论下判断，凡是可量化的都用自己的脚本重算（`challenge_a2.py`、`challenge_a3.py`、`repro_guard_gaps.py`，原始输出 `raw_challenge_*.txt`）
- 分类标签：`[数字错误]` `[口径未披露]` `[证据不足]` `[例子错误]` `[结论夸大]` `[未独立复现]` `[确认无误]`
- 结论：**两份证据的整体质量很高**。A2 抽查 12 项量化指标，11 项完全一致、1 项数字错误；A3 抽查 14 项，11 项完全一致、3 项需修正（含 1 个 off-by-one、1 个例子错误、1 个因果表述不准）。未发现"编造数据"或"把风格偏好包装成耦合"的情况。

---

## 1. 对 `02-adapters/evidence.md`（A2）的挑错

### 1.1 `[数字错误]` §2.3 与 §5.2：`ports.py` 的 Protocol 数是 **9**，不是 7

A2 在 §2.3 表写 `ports.py 行数 / Protocol 数 = 121 / 7`，§5.2 重申"`ports.py` 只有 121 行、7 个 Protocol"。

我的复现（`challenge_a2.py`）：

```
ports.py 行数                  A2=121  我=121  一致
ports.py Protocol 类数         A2=7    我=9
  -> ['IWatchOps','ITaskOps','IMediaOps','IStatsOps','IUploadOps',
      'IWebUiOperations','IBotCallbackHost','IUploadContext','IDiagnosticPort']
```

`module/ports.py` 里 **9 个** `@runtime_checkable class ...(Protocol)`：
L13 `IWatchOps`、L30 `ITaskOps`、L40 `IMediaOps`、L54 `IStatsOps`、L61 `IUploadOps`、L67 `IWebUiOperations`、L72 `IBotCallbackHost`、**L98 `IUploadContext`**、**L114 `IDiagnosticPort`**。

致错原因可推断：A2 的 §2.3 是从"5 个从未被 import 的 Protocol + `IWebUiOperations` + `IBotCallbackHost`"推出 7，**漏掉了恰好在生产里被使用的 `IUploadContext`、`IDiagnosticPort`**（这两个正是 `server.py:28` 一带 import 的）。所以"从未被 import 的 Protocol = 5"这一条**是对的**，但由它反推总数就错了。

影响面：A2 的核心结论（Protocol 对实现表面覆盖率 47.5% = 19/40）**不受影响**；但"7 个 Protocol"这个数字会被下游引用，必须改。

顺带强化（不是挑错，是给 A2 补弹药）：这 9 个 Protocol **全部**带 `@runtime_checkable` 装饰器（9 个），而全仓针对它们的 `isinstance/issubclass/cast` 实测 **0 处**。`@runtime_checkable` 的唯一用途就是让 `isinstance` 可用——**声明了 9 次运行期检查能力，一次都没用**。这比 A2 原文的表述更尖锐。

### 1.2 `[证据不足]` §2.1 的分组表**无法支撑**"无交叠"

标题写"114 方法按职责分组（**无遗漏、无交叠**，合计 114）"，但同一张表的"行号区间"列自己就互相重叠：

- 任务控制 `L108–1822` 与 监听 `L150–1860` 重叠 L150–1822（重叠 1673 行，占全文 88%）；
- 归档工具 `L839–925` 与 诊断导出 `L886–1052` 重叠 L886–925；
- 任务控制 `L108–1822` 与 账号与设置 `L1054–1413`、安装向导 `L1415–1575`、统计 `L619–718` 也全部包含在 L108–1822 内。

也就是说，表里给出的"区间"是**该组方法行号的最小值~最大值**（包络），不能证明划分互斥；"无交叠"只能来自 A2 私有脚本 `probe_02_shims.py` 的分类逻辑，而该判据没有写进文档。建议 A2 把分组判据（关键词表/白名单）附在文档里，或改口径为"每组按方法名清单划分，见 `ops_methods.json`"。

**结论本身可能是对的**（合计 41+25+17+8+5+12+3+3 = 114 与我的 114 吻合），但当前文档里的证据不支持"无交叠"这个强断言。

附：该表百分比逐项相加为 99.9%，合计行写 100%（四舍五入），无需更正。

### 1.3 `[口径未披露]` §2.1 相邻两句给出两个不同的 shim 数（40 vs 38）

第 57 行表尾"纯转发 shim … **合计 40**"，第 60 行紧接着"其中**严格意义的纯转发 shim（单语句、转发到其它对象）共 38 个**"。同一指标相差 2，虽然"严格意义"作了限定，但两行并排出现容易被下游引用成"40 或 38 都行"。建议在表内把列名改成"转发类 shim（含简单包装）40"与"单语句严格转发 38"。

### 1.4 `[口径未披露]` §4.1 "40 个非 chore 提交"的过滤规则不足

A2 声明口径为"取最近 60 个提交，跳过 `chore`/`docs` 前缀"。我按同一口径复现：

```
$ git log --format='%h|%s' -60  →  非 chore/docs 提交 = 44 个
其中 --stat 非空 = 44 个；窗口内 merge 提交 = 2 个
```

**44 ≠ 40**，差 4 个。差额可能来自"跳过 merge/空变更"等额外规则，但文档没写。这会影响"`files/commit mean=11.05`"这类均值（分母不同）。建议补一句精确的过滤表达式（`--no-merges`？多个前缀？）。

不影响结论方向：即使 44 个提交，A2 的"跨 ≥2 层 100%"方向性结论不受威胁（这一点我没有逐提交重算层映射，故只质疑计数口径，不质疑结论）。

### 1.5 `[确认无误]` 我逐项重算并全部吻合的 A2 数字

| 指标 | A2 | 我的复现 | 证据 |
|---|---|---|---|
| `WebOperationsMixin` 方法数 | 114 | **114** | AST `class` 直接子节点 |
| `WebUiServer` 方法数 | 67 | **67** | 同上 |
| 两者同名方法数 | 32 | **32** | 集合交集；且 A2 的 32 个名字清单与我算出的**完全一致**（`set(a2) - set(mine)` 与 `set(mine) - set(a2)` 均为空）|
| 同名中"校验后转发" | 31 | **31** | 方法体含 `_operation(`/`self.operations` |
| 同名中真实实现 | 1（`is_setup_ready`）| **1（`is_setup_ready`）** | 同上 |
| `WebUiServer.start` 行跨度 | 463（L440–902）| **463（L440–902）** | 其中非空行 415、空行 48 |
| `_WEB_UI_DELEGATE_METHODS` 条数 | 40 | **40**（去重 40） | 字面量正则 |
| `ports.py` 行数 | 121 | **121** | — |
| 针对 Protocol 的 `isinstance/issubclass/cast` | 0 | **0** | 全 `module/` AST 扫描 |
| `IWebUiOperations` 继承闭包成员数 | 19 | **19** | 递归基类闭包 |
| 从未被 import 的 Protocol | 5 | **5**（`IMediaOps/IStatsOps/ITaskOps/IUploadOps/IWatchOps`）| 与 A2 名单一致 |
| git 提交文件数 | `b352fc3`=20 / `187d1d8`=71 / `e6621e4`=53 | **20 / 71 / 53** | `git show --stat` |

### 1.6 `[措辞建议]` §2.3 "`IWebUiOperations` 作为注解使用处 = 1"

按"注解"口径**正确**（唯一注解在 `server.py:198 operations: Optional[IWebUiOperations] = None`）。但全仓对该名字的**提及**有 4 处：`operations.py:2`（docstring）、`operations.py:1883`（docstring）、`server.py:28`（import）、`server.py:198`（注解）。建议写成"1 处注解 + 1 处 import"，避免下游误读为"只出现 1 次"。

### 1.7 值得肯定的对抗性设计（非挑错）

A2 的 §5"反例与诚实边界"主动排除了三项（`IBotCallbackHost` 19/19 完整、`ports.py` 体积小、`adapters/pikpak` 未发现私有 API 调用），并明确写"这点比任务书的预期更干净，故不计为发现"。这是本仓库审查里少见的"主动缩小结论"行为，建议 Lead 在最终报告里保留该边界说明。

---

## 2. 对 `03-build/evidence.md`（A3）的挑错

### 2.1 `[数字错误]` F8 分子含"桩文件自身"→ 应为 **59/66**，不是 60/66

A3 写"**60/66** 个测试文件用桩替换整个 pyrogram API 面"。我的复现：

```
unit_tests/*_case.py 中含 install_pyrogram_stub 的文件 = 59
unit_tests 下所有 .py 中含 install_pyrogram_stub 的文件 = 60
其中多出来的那个 = unit_tests/pyrogram_stub.py（桩自己的定义文件）
```

分母 66 是 `*_case.py` 的数量，分子 59 才是**测试文件**数；60 是"把桩自己也算成使用者"。应改为 `59/66`（或换分母写成 `60/67` 全 `.py`），二者取一，不能混。

### 2.2 `[例子错误]` F6 的"约束盲区"举错了例子

A3 §F6 代价 4 写：

> `:198-219` 只查子包、只查首个 alias；`from module.util import yaml` 这类多 alias 形式…完全不设限

这个例子是**反的**：`architecture_guard_case.py:209-218` 对 `ImportFrom` 取的是 `node.module`，`from module.util import yaml` 的 module 部分是 `module.util`，leaf=`util` 恰好在 `OLD_TOP_LEVEL_NAMES` 里 → **会被检出**为违规。

真正漏掉的是**反向形式**：`from module import <shim>`。我实测（`repro_guard_gaps.py`）：

```
守卫能检出的违规: 无
★守卫漏掉的违规（`from module import <shim>`）:
   module.core.app:30  from module import app
   合计: 1
```

`module/core/app.py:30`（子包 `module.core.app`）`from module import app` 导入顶层垫片 `app`，`:214` 的过滤条件 `alias.startswith("module.")` 对 `alias == "module"` 判假 → 直接跳过。**请把例子换成这一条**（它同时是我 §3 那条真实环的一半）。

另外"只查首个 alias"也不准确：对 `ast.Import`，`:208` 取的是**全部** `node.names`，不是首个。准确表述应为"`ImportFrom` 只取 module 名、丢弃被导入的名字"。

### 2.3 `[结论夸大/因果不准]` F5 "用 `.venv` 跑 `python build.py` 会在第一步 `sys.exit(1)`"

判定表达式本身**正确**（`build.py:95-111`：`min_version=(3,9,0) <= current_version < max_version=(3,14,0)`，3.14.0a5 → `False`）。但"第一步"不成立：`build.py:13` 在**模块级**就 `from module import AUTHOR, __version__, ...`，`module/__init__.py:10` 又 `import yaml` → 在 `.venv` 下**根本到不了** `check_python_version()`。实测：

```
$ .venv\Scripts\python.exe build.py --help
exit=-1073741819        # 0xC0000005，不是 1
$ .venv313\Scripts\python.exe -c "import sys; v=sys.version_info[:3]; print((3,9,0) <= v < (3,14,0))"
3.13.7: True
```

建议改成："在一个 `import yaml` 可用的 3.14 解释器上，`build.py` 会在 L108 判 `False` 并 `sys.exit(1)`；而在当前 `.venv` 下更早一步就被 AV 掉。" 这条差异对结论方向无影响，但引用时会误导。

### 2.4 `[口径未披露]` F1 的 "14,917 是旧数据" —— 成因判断错了

A3 写"任务描述中的 14,917 行是**旧数据**"。我的复现（PowerShell 与 Python 双口径）：

```
Get-Content module\adapters\webui\assets.py   → 15679 行
            非空行 = 14917 ； 空行 = 762
```

**14 917 精确等于"非空行"数**（15679 − 762 = 14917），不是过期数据，而是**行数口径被换成了非空行口径**。A3 的 15 679 是正确值（我独立复现一致），只是因果归错。建议改为："14,917 是非空行数（去掉 762 个空行），行数应为 15,679。"

### 2.5 `[口径并存]` "真实现 5" 与架构守卫的 `EXPECTED_TOP_LEVEL_REAL`（6 个）不一致

A3 §F6 写"顶层 shim / 真实现 = 39 / 5"，我实测：

```
顶层 .py 总数 = 45 = 39 shim + 6 非 shim
非 shim 6 个 = ['__init__.py','bootstrap.py','composition_root.py','constants.py','downloader.py','ports.py']
```

A3 的 5 是**排除 `__init__.py`** 的口径；而 `unit_tests/architecture_guard_case.py:27-30` 的 `EXPECTED_TOP_LEVEL_REAL` 是**6 个**（含 `__init__.py`）。两个口径都不错，但必须在文档里声明，否则与守卫对不上。39 + 6 = 45 与实测顶层文件数吻合。

### 2.6 `[未独立复现]` F3 "双份真相目前同步" 我无法在只读授权内验证

F3 的核心证据是"重新生成 assets.py 后逐字节比对，当前同步"。复现这条**必须运行生成器**，而生成器会写 `module/adapters/webui/assets.py`——超出我"`module/` 只读"的硬约束，故**我不验证、也不否定**。

建议 A3 补一个"只读可复核"的命令（例如生成到临时目录再 `git diff --no-index`），否则该结论对第三方不可复核；一旦漂移，F1/F3 的"生成物已入库"代价评估会随之变化。

### 2.7 `[确认无误]` 我逐项重算并全部吻合的 A3 数字

| 指标 | A3 | 我的复现 |
|---|---|---|
| `module/` `.py` 文件数 | 145 | **145** |
| `module/` `.py` 总字节 | 2,909,765 | **2,909,765** |
| `assets.py` 字节 | 1,203,917 | **1,203,917** |
| `assets.py` 占 `module/` 字节比 | 41.4% | **41.4%** |
| 顶层常量数 | 4（3 HTML + 1 FONTS） | **4**：`WEB_UI_HTML`/`WEB_UI_MOBILE_HTML`/`LOGIN_PAGE_HTML`/`FONTS` |
| `WEB_UI_HTML` | 447,549 B / 8,750 行 | **447,549 B（UTF-8）/ 8,750 行** ✔（字符数 435,104，A3 用的是字节，正确）|
| `FONTS` 条目 | 13 个 woff2 | **13 项** |
| tailwind 内联份数 / 单份 | 3 / 100,891 B | **3** / `dist/tailwind.min.css` = **100,891 B** |
| `fonts.css` 单份 | 9,234 B | **9,234 B** |
| 顶层 shim 数 | 39 | **39**（注释判据 `Compatibility shim`）|
| shim 用 `import *` | 24/39 | **24/39** |
| 定义 `__all__` 的模块 | 10/145 | **10/145** |
| 生产引用 shim | 2 处 | **2**：`main.py:8`、`scripts/diagnose_pikpak_forward.py:98`（都指向 `module.util`）|
| 测试引用 shim | 160 处 / 29 个 | **160 处 / 29 个** |

### 2.8 A3 的 F4/F5 与我的独立结论完全一致

- F4（`pytest unit_tests -q` → 0 用例、exit=5；702 用例需显式传文件名）：我用 `.venv313` 与 `.venv` 双跑，均为 `no tests ran in 0.02s` / `exit=5`；显式 66 文件 = `702 passed, 1 warning, 27 subtests passed in 79.28s`。
- F5（`.venv` = 3.14.0a5，`import yaml` → 0xC0000005）：见 `verify.md` §0。我进一步定位到崩溃点是 `yaml/_yaml.cp314-win_amd64.pyd` 的扩展初始化（`-X faulthandler` 显示 AV 在 `exec_module` 内），并排除了"所有 C 扩展都崩"（`tgcrypto.cp314` 正常）。A3 的崩溃栈（`module/__init__.py:10` → `yaml/cyaml.py` → `_yaml`）与我的定位一致。

---

## 3. 对 `01-host/evidence.md`（A1）的抽查

A1 的 `evidence.md` 在我抽查 02/03 期间落盘（44,658 B，H-01…H-11 共 11 条发现 + 一节"度量否证的假设"）。我抽查了其中 6 条的**可计数**部分（`challenge_a1.py`）。

### 3.1 `[确认无误]` H-01 —— 33 个代理名 / 125 处读点 / 5 个宿主私有方法，**三项全部精确吻合**

```
定义 __getattr__ : True
self.<attr> 不同名字总数: 49
需代理的不同名字数 A1=33  我=33
代理读点总数       A1=125 我=125
其中宿主私有方法   A1=5   我=5 -> ['_forward_success_event_message','_log_system_chain',
                                   '_message_chain_context','_record_watch_event','_watch_media_types_override']
```

连 5 个私有方法的名字都完全一致。被代理最多的名字是 `_log_system_chain`(26 次)、`gc`(13)、`app`(13)。

### 3.2 `[确认无误]` H-08 —— `self.__dict__.get(...)` 12 处，逐行位置全部吻合

我扫全 `module/` 得到 **12 处**，与 A1 完全一致，且位置可逐条对上：`downloader.py:177`；`operations.py:118/170/309/410/738/739/743/852/920/1122/1636`。

（这与我在 `verify.md` §3 的结论互为佐证：`operations.py:118` 与 `:1122` 正**是**"绕开类属性校验去同步 `ctx`"的那两处，也是 `architecture_guard_case.py:292` 只对 `composition_root.py` 禁用该模式、对 `operations.py` **完全不设限**的漏洞。）

### 3.3 `[确认无误]` H-09 的装配成本数字 —— 199 kwarg / 0 次完整构造 / 唯一构造点

```
composition_root.py keyword args total = 199   (A1=199，涉及 33 个调用表达式)
unit_tests/ 中 TrmdCompositionRoot( 出现次数 = 0
unit_tests/ 中 TelegramRestrictedMediaDownloader( 出现次数 = 0
main.py:13  trmd = TelegramRestrictedMediaDownloader()      ← 唯一完整构造点
```

三项**全部精确吻合**。这条对"上帝对象无法在测试里完整构造"的论证成立。

### 3.4 `[口径未披露]` H-09 的 "92 个 `__new__` 骨架" 我无法复现

A1 给的 4 个细分中 2 个精确吻合、2 个对不上：

| 文件 | A1 | 我的复现 |
|---|---|---|
| `transfer_store_webui_case.py` | 47 | **47**（`object.__new__`）✔ |
| `downloader_transfer_record_case.py` | 17 | **17**（`TelegramRestrictedMediaDownloader.__new__`）✔ |
| `web_task_delete_case.py` | 9 | **11**（`object.__new__`）✘ |
| `live_transfer_wire_case.py` | 3 | **4**（`.__new__(` 全部形态）✘ |

总量口径也对不上：我测得 `object.__new__` = **90**、`TelegramRestrictedMediaDownloader.__new__` = **23**、全部 `.__new__(` = **121**（涉及 21 个测试文件），而 A1 报 92。**92 落在 90 与 121 之间，无法由任一简单口径推出**。这不是"数字造假"（前两项精确吻合说明匹配器高度相似），而是**匹配表达式未披露**。请 A1 把 `test_assembly_cost.py` 的正则/过滤条件写进文档，否则该数字对第三方不可复核——而它是"上帝对象可测性代价"这一条的主量化依据。

### 3.5 `[确认无误]` H-05 —— "17 个透传 shim" 成立（但标题宜加"纯透传"限定）

`composition_root.py` 里含 `*args`/`**kwargs` 的函数实为 **22 个**（多出的 5 个是 L495–504 的 `_noop/_noop_false/_noop_dict/_noop_str` 与 L404 `_schedule_deferred_archive`）；而"纯 `return f(*args, **kwargs)` 透传形态"恰好 **17 个**：L320/323/326/329/332/335/338/341/344/347/350/353/356/359/362/365/368。A1 的 17 与我完全一致——建议标题从"17 个 `*args/**kwargs` 透传 shim"改成"17 个**纯**透传 shim（另有 4 个 `_noop*` + 1 个 `**kwargs` 辅助）"，避免下游误以为全文只有 17 个变参函数。

### 3.6 `[确认无误 · 高价值]` H-02 的死代码论证成立

`runner.py:80-86` 的 `instance_method is not class_method`：普通实例方法每次 `getattr` 都新建 bound method（`h.m is h.m` → False），与类上的 function 永不相等 ⇒ 条件恒真 ⇒ `:85-86` 的本地兜底**不可达**。A1 的 `repro_resolve_method.py` 输出与 Python 语义一致，且 `[4] staticmethod 是唯一能让分支生效的形态` 这个反例设计得很严谨。这是本次审查里最锋利的一条发现，建议 Lead 保留。

### 3.7 已确认：A1、A2、A3 **都没有**传播"import 图无环"

我对三份文档 grep `无环|import 图|循环依赖|Tarjan|SCC` → **0 命中**。因此"module/ import 图无环"（已被我推翻：真实 3 个非平凡 SCC）**在四份证据里都找不到出处**，它是任务书里的一个未经复核的假设。**不应记在 A1/A2/A3 任何一份账上**，但必须从最终报告里撤掉（见 §4）。

### 3.8 未抽查项（诚实声明）

A1 的 H-03（WebUITaskManager 两处接线 27 vs 21）、H-04（`_require_*` 重复构造 + 25 个端口接线）、H-06（别名共享/双注入通道）、H-07（12 参数手工重排）、H-11（乒乓调用链）我**没有逐条复现**（预算用于 02/03 与 A1 的 6 条可计数项）。按已抽查 6 条中 5 条精确吻合的命中率，A1 的证据质量与 A2/A3 同级；但 Lead 若要把 H-03/H-07 写进最终结论，建议再抽查一次。"度量否证的假设"一节（A1 主动排除项）与 A2 §5、A3 F7 风格一致，属高质量自我约束。

---

## 4. 我给 Lead 的"不要再传播"清单（含对任务书本身的两条更正）

1. **"module/ import 图无环（Tarjan SCC）"** → 错。真实 **3 个非平凡 SCC**（`core.filter`⇄`core.media_types`、`module.app`⇄`module.core.app`、`adapters.webui.server`⇄`adapters.webui.handlers`+子模块）；且守卫 `architecture_guard_case.py:61-76/47-58` 的环检测存在 3 个实现缺陷，实测为**假阳性**（自建图 384 边/0 环 vs 正确图 398 边/3 环）。**四份队友证据均未声称过这一点**，它只出现在任务书里。
2. **"assets.py 14917 行"** → 错（那是**非空行**数）。真实 **15679 行**（空行 762）。A3 已自行更正为 15679，但其成因说明"旧数据"不对，应改为"行数口径被换成了非空行口径"。
3. **"`WebOperationsMixin` 118 方法"** → 口径混淆。**114 个方法**（+4 个嵌套闭包 = 118 个 `def` 节点）。A2 报的 114 与我的独立复现一致。
4. **"全量测试原生崩溃 = 测试基建缺陷"** → 因果错。0xC0000005 的根因是 `.venv` = Python **3.14.0a5**（alpha）与 `yaml/_yaml.cp314-win_amd64.pyd` 的二进制 ABI 不匹配，崩在扩展初始化（`-X faulthandler` 已定位）；与测试内容无关，无需二分。有效基线是 `.venv313`（3.13.7）= **702 passed**；`.venv` 下唯一不崩的测试文件是纯 AST 的 `architecture_guard_case.py`。
5. **需向队友回收的三处口径**：A2 的 `ports.py` Protocol 数（7 → **9**）、A2 的提交采样口径（40 vs 我复现的 **44**）、A3 的 F8 分子（60/66 → **59/66**）、A1 的 `__new__` 骨架匹配表达式（报 92，我复现 `object.__new__`=**90** / 全部 `.__new__(`=**121**）。

---

## 5. 抽查覆盖率与自我限制（诚实声明）

| 对象 | 抽查项 | 精确吻合 | 需修正 | 未复现 |
|---|---|---|---|---|
| A2 `02-adapters` | 12 | 11 | 1（Protocol 数 7→9）+ 2 项口径 | — |
| A3 `03-build` | 14 | 11 | 3（F8 分子、F6 例子、F5 因果）+ 1 口径 | F3 的"双份真相同步"（复现需运行生成器写 `module/`，超出只读授权）|
| A1 `01-host` | 6 | 5 | 0 + 1 项口径（H-09 的 92）| H-03/H-04/H-06/H-07/H-11 |

自我限制：
- 我**没有**修改 `module/` 或 `unit_tests/` 下任何文件，**没有** git commit（唯一写入是 `tmp/coupling-audit/04-verify/`）。
- 我**没有**运行任何会写 `module/` 的生成器（因此 A3 的 F3 未复现）。
- 我**没有**联网（无 web 检索）。
- A1/A2/A3 的"变更放大"结论我只复核了 git 计数，**未逐提交重算层映射**——那些结论方向性可信，但如需精确均值请以各作者口径为准。
