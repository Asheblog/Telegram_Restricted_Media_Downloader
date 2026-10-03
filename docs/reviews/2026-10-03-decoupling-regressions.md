# 架构解耦回归审查

## 范围与判据

- 固定范围：`e6818d1...1dee579`，覆盖 2026-08-14 起的 Phase 1–6、2026-10-02 的 WebOps/资源拆分及后续清理，共 173 个变更文件。
- 最近一轮 WebOps 拆分的业务基线为 `56bcd7d`（v0.2.251）。同时审查早期 Phase，避免遗漏至今仍存在的回归。
- 依据：`docs/specs/arch-decouple-phases.md`、`docs/specs/arch-deepen-modules.md`、`CONTEXT.md`、`CONTEXT-MAP.md` 及各业务 ADR。
- 审查重点：真实生产接线、参数与默认值、状态及取消语义、异步生命周期、资源与分发。文件搬移通过函数 AST 对比辅助验证；业务差异必须有调用链和可运行复现。
- 分工：组合根由主审查员负责，转存/持久化、WebOps/归档、HTTP/资源、Bot/初始化/工具、工程规范分别独立审查。修复再做独立规格和质量复核。
- 边界：恢复解耦前业务行为，保留现有领域术语和数据格式；本轮没有新增领域规则或架构决策，无需新增 ADR。

## 已确认业务回归

### 上传并发窗口固定为 1

- 引入提交：`187d1d8`。
- 位置：`module/composition_root.py` 的 `DynamicAsyncWindow` 装配。
- 原因：把 `lambda: self.gc.upload_pending_limit` 改成整数值。窗口调用 provider 时发生 `TypeError`，被内部异常处理降级为最小值 1。
- 影响：默认限额 3、用户配置 5 和热更新均不生效，下载后上传被意外串行化。
- 修复：传入读取当前配置的绑定方法，保留窗口的回调合同。
- 回归：`unit_tests/composition_window_case.py` 在独立进程和临时配置目录中构造真实宿主，使用真实 Pyrogram，验证配置 5、默认 3、保存后 3→5，以及第 6 个租约阻塞、释放后继续。
- 红绿：修复前 2 个用例失败，窗口实际值均为 1；修复后均通过。

### 频道下载丢失媒体类型覆盖参数

- 引入提交：`6e0d564`。
- 位置：`module/webops/operation_applicator.py` 的 `apply_web_channel_download()` 与 `module/webops/operations.py` 的协作者接线。
- 原因：计算了 `media_types_override`，但通过零参数 getter 调用过滤器，覆盖表未传入。
- 影响：频道下载表单选择的媒体类型无法覆盖全局列表；如全局禁用 photo 而表单选择 photo，实际零下载仍可显示操作成功。
- 既有约定：未设置覆盖时继承全局，设置后整表替换，主贴与评论区共用过滤器。依据 ADR-0010。空列表沿用解耦前行为：HTTP 入口归一为全部类型，底层全 False 白名单也允许全部类型；本轮不改变这项既有业务规则。
- 修复：协作者 getter 接收并透传 `media_types_override`，最终交给真实宿主的运行时过滤器。
- 回归：真实组合根、过滤器和操作队列覆盖整表替换、未设置继承、主贴与评论共用，以及日期和关键词限制。
- 红绿：最初 WebOps 九个场景修复前 7 failed、2 passed；补全入口、归属和契约验证后共有 12 个场景，最终均通过。

### 冷调度器上的延迟抓取手动操作访问 None

- 引入：`dde1ac3` 拆入口后，`8b43528` 将共用 getter 改为 `scheduler_if_started()`；组合后暴露缺口。
- 位置：`module/webops/watch_operations.py` 的取消、立即执行、重试，以及 `operations.py` 的接线。
- 原因：只读取已有调度器的 getter 可能返回 None，三个主动操作直接调用其方法。
- 影响：有持久化 capture、调度器尚未创建时，三个入口抛 `AttributeError`。
- 边界：主动操作需要按需创建；删除监听只读取已有调度器。`LiveWatchManager.delete_watch()` 自身负责取消持久化 pending/running，不需要因为删除而启动调度器。依据 ADR-0007。
- 修复：区分读取已有调度器与按需创建调度器的两个必填 getter，三个主动操作使用创建入口，删除仍使用只读入口。归属校验先于创建，沿用现有锁保证调度器单实例。
- 回归：真实组合根和 SQLite 覆盖冷启动取消/立即执行/重试、调度器复用、非归属 capture 拒绝且不启动，以及删除时取消持久化记录但不创建调度器。

### 已配置日志环境中的文件处理器未关闭

- 引入提交：`8e44f61`。
- 位置：`module/bootstrap.py` 的 `initialize()`。
- 原因：根 logger 已有 handler 时 `logging.basicConfig()` 不接纳新处理器。旧代码的模块级变量持有文件处理器，拆分后改为局部变量，函数返回即失去强引用，产生未关闭文件的 ResourceWarning。
- 触发：pytest 或嵌入调用方提前配置根 logger；普通入口根 logger 为空时不触发。
- 判据：相同解释器和预置 NullHandler 条件下，新旧版本差分验证。
- 边界：不能清空调用方已有 handler，也不能添加重复日志输出；未被接纳的自建处理器必须释放。
- 修复：根 logger 已有 handler 时不构造文件处理器；若其他线程抢先注册使 `basicConfig()` 不接纳新文件处理器，显式关闭该处理器。
- 回归：独立子进程将 ResourceWarning 作为错误，记录 GC 的 unraisable 异常，验证没有文件句柄泄漏且保留调用方原有 handler。修复前失败，修复后 bootstrap 集合 5 passed；独立复核另验证了竞态分支。

## 测试与导航缺陷

- `unit_tests/uploader_init_case.py` 的 `create_task` 桩丢弃协程，导致未 await 警告；改为显式关闭协程。
- 同一测试污染 `transfer_registry.notify/loop/directory_name`，使 init→flood_wait 执行顺序出现 4 个失败。用限定生命周期的字段 patch 恢复原值，两种顺序均为 14 passed，不清空其他注册表状态。
- 本轮新增 WebOps 回归用例的首版在收集阶段改写 `PARSE_ARGS.config`，完整测试发现它污染了原有集成测试的沙箱路径（1 failed、773 passed、128 subtests）。已将 12 个场景隔离到独立子进程与显式清理的临时目录，父进程不再修改 argv、cwd、环境或配置；新旧集成测试组合修复前 1 failed、20 passed，修复后 21 passed、10 subtests。
- 独立复核另在 `PYTHONDEVMODE=1` 下发现新增测试的立即执行/重试场景从主线程停止后台调度任务，触发 asyncio 的线程检查，异常又被 Windows 上 SQLite 文件未关闭导致的目录清理错误掩盖。已改为在 loop 线程内取消并等待任务结束、关闭该线程连接，再停止并等待线程退出、关闭主线程连接及 loop。开发模式的 12 场景连续三轮通过，新旧集成测试组合也通过。
- `CONTEXT-MAP.md` 的 WebOps、SetupCoordinator、静态资源、领域命名路径仍指向迁移前位置，已修正。
- `module/core/message_filter_factory.py` 的说明仍声称旧工厂入口保留转发，实际已经删除，已纠正说明。

## 未发现回归的证据

- 转存任务/监听/日志持久化、转存领域模型和注册表、评论调度器的搬移函数经 AST 对比无差异；其真实接线和关联测试另行核对。
- 三份 HTML 与拆分前逐字节一致，分别为 447549、403987、113629 个 UTF-8 字节；13 个字体名称和原始字节一致。
- HTTP 路由、设置合并、公开 shim 和资源读取检查通过；模拟 Docker 裁剪源码后资源仍能读取。
- `static_assets.__all__` 的三份 HTML 由模块 `__getattr__` 提供，F822 静态提示不代表运行时缺失，实际导入已验证。
- 日志等级常量候选经新旧版本对比撤回：有效、自定义、缺失、损坏或非法配置下，真实 handler 等级和持久化配置均相同；静态默认常量差异不计业务回归。

## 验证与限制

- 原始基线：759 passed、128 subtests，1 条未 await 警告。
- 窗口与测试隔离修复后：`uv run --locked pytest -q -W error::RuntimeWarning` 为 761 passed、128 subtests，无警告。
- 最终完整验证：`uv run --locked pytest -q -W error::RuntimeWarning` 为 774 passed、128 subtests，无警告，124.66 秒；这是最后一轮测试生命周期修正后的结果。
- 子进程补充验证：父进程 pytest 的 `-W` 不会自动传给子进程，不能据此声称子进程也启用了严格警告。另显式通过 `PYTHONWARNINGS=error::RuntimeWarning,error::ResourceWarning` 运行 12 个 WebOps 场景，并逐个断言 stderr 不含两类警告（包含 exit 0 的 unraisable 析构异常），全部通过，9.582 秒。
- 最终 WebOps 用例自身显式给子进程传入两类 `-W error`，并检查 stderr 中的警告标记；这项门禁已包含在上述 774 个测试中。
- `uv run --locked ruff check --select F401,F811 module/ unit_tests/` 通过。
- Node 的 `watch_ui_helpers.test.mjs` 通过。
- `git diff --check` 通过，13 个修改/新增文件均验证为 UTF-8 无 BOM、LF。
- 首次扩展检查 `pytest -q -W error` 未通过：30 failed、730 passed、1 error。文件处理器警告已归为 Phase 1 回归并修复；SQLite 连接警告属于存量测试收尾问题，连接实现与基线逐字一致。最终独立检查仍在旧集成测试发现未关闭 SQLite 连接，本轮未批量改写这些 fixture。不能把全警告检查报告为通过，也不能把存量 fixture 警告归因于本轮业务变更。
- Windows 宿主未提供 Docker CLI；审查阶段未本地重建 Linux 镜像。`1dee579` 对应 GitHub Tests 与 v0.2.266 Release Docker 均已成功，但不能代替新修复的 Linux 构建验证；后续发布以新版本 tag 对应的 GitHub Actions 结果验收。
- 不使用真实 Telegram/PikPak 账户进行外部服务端到端操作。本地集成以外部客户端替身隔离网络，真实 HTTP、SQLite、组合根和 Pyrogram 导入由对应测试覆盖。
- 本轮不需要数据迁移，直接替换代码；审查交付阶段未创建版本 tag、推送或发布镜像。

## 最终验收

四处已确认的解耦回归均已修复，对应红绿回归和最终完整验证通过。

- Spec：生产接线、媒体覆盖、归属校验、冷启动调度器、删除时不启动的既有语义通过独立复核，无未修复阻塞项。
- Standards/Quality：保留模块边界与现有工厂、锁及实例生命周期；新增测试的配置污染、临时目录泄漏和跨线程收尾问题均已修复并独立复现验证，无未修复阻塞项。
- 审查交付：本地提交并快进合入 `main`，无需数据迁移，直接替换；当时未推送、打 tag 或发布，也未宣称外部服务与新 Linux 镜像已经验证。
- 后续发布：用户已授权随 `v0.2.267` 推送修复，按现有发布流程同步推送 `main` 与版本 tag，并监督 Tests、真实镜像导入/资源冒烟及 Linux 双架构构建通过。
