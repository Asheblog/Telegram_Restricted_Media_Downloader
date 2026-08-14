# Spec: arch/decouple-phases

## Goal

消除上一轮「深化模块」留下的结构性耦合：import 副作用、分层倒置、反射式装配、神级 Protocol、顶层厨房水槽。行为与公开 API 保持不变；按 Phase 渐进落地，每个 Phase 独立可验证、可回滚。

## 背景（诊断结论）

`project_report` 显示 `module <-> adapters <-> core <-> infra <-> persistence <-> transfer <-> utils` 形成 251 条边的跨子包循环；全仓 190 处函数体内延迟 import 用于打破循环。具体耦合点：

1. `module/__init__.py`（259 行）在 import 时执行 `os.makedirs`、读写 `.CONFIG.yaml`、创建 `TimedRotatingFileHandler`、`logging.basicConfig`、启动日志清理守护线程、readline 历史等副作用；被 23 个模块 import（含 `core/enums.py` 这类纯叶子、以及只取版本号的 `build.py`）。
2. 顶层 `module/` 仍有 14+ 个非 shim 大文件：`downloader.py`(1967)、`web_operations.py`(1853)、`archive_author_tool.py`(1196)、`source_folders.py`(1121)、`archive_author_jobs.py`(538)、`archive_reorganize.py`(462)、`bot_host.py`(375) 等。
3. 分层倒置：`core/config.py`/`core/app.py` → `adapters/webui/setup`；`transfer/live_watch.py` → `adapters/webui/view_model`；`persistence/store/*` → 顶层 `source_folders`。
4. 反射式装配：`composition_root` 用几十个 `lambda: self.__dict__.get(...)`；`TransferPorts.from_host` 用 `getattr + no-op`；`TrmdCompositionRoot.__getattr__` 魔法遍历 managers。
5. 神级 Protocol：`IBotHost`（17 成员）、`IPikPakTarget`（14 方法）镜像上帝对象。

## Requirements

### Phase 1 — 拆 `module/__init__.py` 副作用

1. 新建 `module/constants.py`：纯常量与无副作用对象（`__version__`、`SOFTWARE_*`、`APPDATA_PATH`、`GLOBAL_CONFIG_PATH`、`LOG_PATH`、`LINK_PREVIEW_OPTIONS`、`SLEEP_THRESHOLD`、`README`、`CustomDumper`、`console`、`log` 等），import 时零 I/O、零目录创建、零线程。
2. 新建 `module/bootstrap.py`：`initialize()` 幂等函数，收拢全部副作用（建目录、readline 历史、日志文件 handler、`.CONFIG.yaml` 读取、`logging.basicConfig`、banner、日志清理线程、`CustomDumper.add_representer`）。
3. `module/__init__.py` 改为纯 re-export（从 `constants` 导入并 `__all__` 导出），import 零副作用。
4. 运行入口显式初始化：`main.py` 与 `TrmdCompositionRoot.__init__` 调用 `bootstrap.initialize()`（幂等，覆盖 CLI / WebUI / 测试构造路径）。
5. `build.py` 等「只取常量」的脚本 import `module` 不再产生任何副作用。

### Phase 2 — 反转分层倒置

1. `core/config.py`、`core/app.py` 不再 import `module.adapters.webui.setup`：把 `apply_web_safe_user_defaults` / `has_telegram_api_credentials` 所需的核心能力下沉，webui 层通过注入或回调获得，方向统一为 adapters → core。
2. `transfer/live_watch.py` 不再 import `module.adapters.webui.view_model`：ViewModel 组装留在 webui 层，live_watch 只产出领域数据，经端口回调交给调用方渲染。
3. `persistence/store/tasks.py`、`watches.py` 不再 import 顶层 `source_folders`：`normalize_archive_title_source` 归入领域包（见 Phase 3），持久层只依赖领域包与自身。

### Phase 3 — `source_folders` 归入领域包

1. 新建 `module/domain/archive_naming/`，迁移 `source_folders.py`（1121 行纯函数：标题打分、作者提取、归档路径组装）及 `author_hashtag_match.py`、`archive_author_tool.py` 中同域逻辑；顶层 `source_folders.py` 降级为 shim（保持公开签名兼容）。

### Phase 4 — 消灭反射式装配

 1. `TransferPorts.from_host(host)` 的 `getattr + no-op` 改为组合根显式构造（`TransferPorts(paths=..., progress=..., ...)`），缺失依赖在装配期报错而非运行时静默降级。
 2. `composition_root` 的 `lambda: self.__dict__.get(...)` 收敛为显式依赖构造；`TrmdCompositionRoot.__getattr__` 魔法委托改为显式属性/方法。
 3. `TransferContext.build()` 的 getter 解析改为显式装配（构造时传入实例）。

### Phase 5 — 拆神级 Protocol

 1. `IBotHost` / `IPikPakTarget` 按职责聚类拆成小 Protocol（参照 `TransferPorts` 的 `paths/progress/target/storage/runtime` 分簇方向）；调用方只依赖所需的小 Protocol。

### Phase 6 — 收尾顶层厨房水槽

 1. `archive_author_tool.py`、`archive_author_jobs.py`、`archive_reorganize.py`、`bot_host.py`、`live_watch_applicator.py` 归位到对应子包（adapters / domain / transfer）。
 2. `downloader.py`、`web_operations.py` 继续瘦身：残留业务委托给既有服务，门面只留编排与 Bot UX 胶水。

## Non-goals

- 不改 REST 路径 / JSON 字段 / SQLite 语义；不改 Docker / assets 生成；不重写前端。
- 不做纯搬包（每个迁移必须有依赖方向或副作用消除的实质收益）。
- 不引入新领域术语，除非服务名进入普适语言。
- 不以单文件行数上限为完成标准。

## Seams under test

1. `module/constants` import 零副作用（`import module` 后 APPDATA 目录、日志文件、线程均不产生）。
2. `bootstrap.initialize()` 幂等：重复调用不重复建 handler / 线程。
3. 既有 `unit_tests/` 全套回归（Phase 1 仅涉及 import 时副作用，预期零行为变化）。
4. `build.py` 在无 APPDATA 环境（如 CI）可正常 import `module` 取版本号。
