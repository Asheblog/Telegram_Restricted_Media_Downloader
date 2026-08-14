# CONTEXT-MAP — 项目速查映射

> **注意**: 行数为编写时的近似快照，随时可能因代码变更而过时。
> 顶层 `module/*.py` 大量为兼容 shim（约 3 行），实现以「实现路径」为准。

## 文件 → 职责速查

### 入口与装配（顶层）

| 文件 | 职责 | 行数(≈) |
| ------ | ------ | -------- |
| `main.py` | 入口：`initialize()` → 检查环境 → 创建 TRMD → `run()` | 12 |
| `module/__init__.py` | re-export constants + bootstrap（import 零副作用） | ~70 |
| `module/constants.py` | 纯常量、`console`/`log`/`CustomDumper`/`README`（零副作用） | ~130 |
| `module/bootstrap.py` | 幂等 `initialize()`：日志 handler、readline、清理线程、`.CONFIG.yaml` | ~210 |
| `module/downloader.py` | 门面：`CompositionRoot` + `WebOperationsMixin` + `BotHostMixin`；listen/forward/runner/PikPak 多已委托；残留下载编排与 Bot UX | ~1920 |
| `module/composition_root.py` | 装配根：接线 app / bot / store / managers / TransferEngine / LiveTransferService | ~365 |
| `module/web_operations.py` | WebUI 操作 mixin + `WebOperationsFacade`；Archive Author / 任务控制委托 | ~1630 |
| `module/bot_host.py` | Bot 宿主 mixin（start / callback / download_chat 等） | ~370 |
| `module/ports.py` | Protocol seam（`IWebUiOperations`、`IBotHost`、`IPikPakTarget` 等） | ~160 |
| `module/live_watch_applicator.py` | 将 watch payload 应用到运行时监听 | ~85 |
| `module/source_folders.py` | 来源频道 / 帖级归档路径命名 | ~200 |

### 实现路径（子包）

| 实现路径 | 顶层 shim（若有） | 职责 | 行数(≈) |
| ---------- | ------------------- | ------ | -------- |
| `core/app.py` | `app.py` | Telegram 应用、下载文件名、关机 | ~340 |
| `core/config.py` | `config.py` | 双层配置（UserConfig + GlobalConfig） | ~920 |
| `core/enums.py` | `enums.py` | 枚举/常量：类型、状态、按钮文案等 | ~1440 |
| `core/filter.py` | `filter.py` | 消息过滤器 | ~170 |
| `core/target_profiles.py` | `target_profiles.py` | 目标 profile（PikPak 限制等） | ~40 |
| `infra/client.py` | —（已删零引用 shim） | Pyrogram 客户端扩展 | ~830 |
| `infra/uploader.py` | `uploader.py` | Telegram 上传器 | ~970 |
| `infra/async_window.py` | `async_window.py` | 动态并发窗口 | ~50 |
| `persistence/transfer_store.py` | `transfer_store.py` | `TransferStore` 门面（组合 `store/*` mixins） | ~80 |
| `persistence/store/tasks.py` | — | 任务 CRUD / 状态 | ~860 |
| `persistence/store/items.py` | — | Transfer Item CRUD | ~570 |
| `persistence/store/watches.py` | — | Live watch CRUD / 事件 | ~270 |
| `persistence/store/deferred.py` | — | 讨论区延迟抓取持久化 | ~300 |
| `persistence/store/archive_jobs.py` | — | Archive Author 作业 | ~160 |
| `persistence/store/schema.py` | — | SQLite schema / 迁移 | ~270 |
| `persistence/store/maintenance.py` | — | 维护 / reconcile / purge | ~140 |
| `persistence/store/connection.py` | — | 连接 / TLS | ~100 |
| `persistence/store/*`（其余） | — | events / status / constants / system_logs / cleanup_logs | 小文件合计 ~190 |
| `persistence/media_manager.py` | `media_manager.py` | 媒体文件清理 | ~480 |
| `persistence/local_storage_guard.py` | `local_storage_guard.py` | 本地磁盘预算守护 | ~100 |
| `persistence/system_log.py` | — | 系统日志追踪 | ~140 |
| `transfer/engine.py` | `transfer_engine.py` | 转存引擎（下载→上传编排） | ~640 |
| `transfer/runner.py` | — | Web 转存任务 runner | ~860 |
| `transfer/progress.py` | `transfer_progress.py` | 进度跟踪 / 恢复续传 | ~940 |
| `transfer/live_watch.py` | `live_watch_manager.py` | 实时监听管理 | ~400 |
| `transfer/live_transfer.py` | — | listen/forward 转存（`forward` / `listen_*` / `on_listen` / discussion replies） | ~1120 |
| `transfer/context.py` | `comp.py` | `TransferContext` + 分簇 `TransferPorts`（Paths/Progress/Target/Storage/Runtime） | ~180 |
| `transfer/models.py` | `task.py` | DownloadTask / UploadTask | ~350 |
| `transfer/deep_link.py` | — | 深链取片 | ~200 |
| `transfer/comment_delay.py` | — | 讨论区延迟抓取调度 | ~240 |
| `transfer/watch_inline.py` | — | watch_inline 执行模式辅助 | ~50 |
| `transfer/forward_watch_backup.py` | — | 转发监听导入/导出 | ~110 |
| `transfer/registry.py` | `transfer_registry.py` | 转存注册表 | ~20 |
| `adapters/bot/bot.py` | `bot.py` | Bot 命令 + 内联键盘 | ~1900 |
| `adapters/bot/callback_handler.py` | `callback_handler.py` | Bot 回调路由 | ~740 |
| `adapters/pikpak/integration.py` | `pikpak_integration.py` | 入库确认、归档编排 | ~410 |
| `adapters/pikpak/archive.py` | `pikpak_archive.py` | rclone PikPak 归档客户端 | ~350 |
| `adapters/webui/server.py` | `web_ui.py` | WebUI HTTP 壳（路由调度进 handlers） | ~1500 |
| `adapters/webui/handlers/` | — | 按 API 域拆分的 HTTP handlers（auth/tasks/watches/…） | ~1140 |
| `adapters/webui/archive_author_ops.py` | — | Archive Author 作业编排（WebOps 委托） | ~550 |
| `adapters/webui/setup.py` | — | First-run Setup Wizard 状态 / rclone / 可选 Bot Token | ~350 |
| `adapters/webui/view_model.py` | `webui_view_model.py` | 桌面/移动统一 ViewModel | ~550 |
| `adapters/webui/task_manager.py` | `web_task_manager.py` | WebUI 任务调度器 | ~740 |
| `adapters/webui/statistics_payload.py` | `statistics_payload.py` | 统计面板 payload | ~80 |
| `adapters/webui/assets.py` | `web_ui_assets.py` | 内嵌 HTML/CSS/JS/字体 | 大文件 |
| `adapters/webui/build_frontend.py` | — | Tailwind 前端构建 | ~100 |
| `utils/util.py` | `util.py` | 链接解析、消息、环境判断 | ~550 |
| `utils/stdio.py` | `stdio.py` | 终端 I/O、进度条 | ~560 |
| `utils/path_tool.py` | `path_tool.py` | 路径/文件名工具 | ~280 |
| `utils/parser.py` | `parser.py` | CLI 参数解析 | ~90 |
| `utils/language.py` | `language.py` | 中文本地化 | ~65 |
| `utils/diagnostics.py` | `diagnostics.py` | 诊断日志适配器 | ~30 |

## 子包 → 状态

| 子包 | 内容 | 状态 |
| ------ | ------ | ------ |
| `adapters/webui/` | server / handlers / archive_author_ops / view_model / task_manager / assets / build | ✅ 已填充（P3 handlers 拆分） |
| `adapters/bot/` | bot.py / callback_handler.py | ✅ 已填充 |
| `adapters/pikpak/` | integration.py / archive.py | ✅ 已填充 |
| `core/` | app / config / enums / filter / target_profiles | ✅ 已填充 |
| `infra/` | client / uploader / async_window | ✅ 已填充 |
| `persistence/` | transfer_store 门面 + store/* / media_manager / local_storage_guard / system_log | ✅ 已填充（P2 拆 mixin） |
| `transfer/` | engine / runner / progress / live_watch / deep_link / comment_delay 等 | ✅ 已填充 |
| `utils/` | util / stdio / path_tool / parser / language / diagnostics | ✅ 已填充 |

> Phase 0–3 目录迁移与 seam 引入已完成；deepen 轮 P1–P4 已完成。不做纯搬包、不以行数硬顶为目标；见 `CONTEXT.md` 架构立场与 ADR 0014。

## 配置项 → 位置

| 配置项 | 所属配置层 | 字段路径 |
| -------- | ----------- | ---------- |
| api_id, api_hash | UserConfig | `config.api_id` / `config.api_hash` |
| bot_token | UserConfig | `config.bot_token` |
| download_type | UserConfig | `config.download_type` |
| save/temp/session_directory | UserConfig | `config.*_directory` |
| proxy | UserConfig | `config.proxy.*` |
| max_tasks (download/upload) | UserConfig | `config.max_tasks.*` |
| max_retries | UserConfig | `config.max_retries.*` |
| upload (download_upload, delete, pending_limit) | GlobalConfig | `gc.upload.*` |
| target_profiles (pikpak archive 等) | GlobalConfig | `gc.target_profiles.pikpak.*` |
| PikPak 账号列表 / 当前激活账号 | GlobalConfig | `gc.target_profiles.pikpak.accounts` / `.archive.remote` |
| Media Type Allowlist（唯一真源） | GlobalConfig | `gc.message_filter.media_types` |
| Keyword Blacklist（与归档标题面一致） | GlobalConfig | `gc.message_filter.keywords` |
| forward_type（兼容双写） | GlobalConfig | `gc.forward_type.*` |
| message_filter（日期/关键词 + media_types） | GlobalConfig | `gc.message_filter.*` |
| Media Type Override（任务/监听） | TransferStore | `transfer_tasks.media_types` / `live_transfer_watches.media_types` |
| file_log_level / console_log_level | GlobalConfig | `.CONFIG.yaml` |
| notice | GlobalConfig | `.CONFIG.yaml` |
| `transfer.item_stale_timeout_minutes` | GlobalConfig | 转存项无进展超时（分钟，默认 5） |
| `deep_link.bot_whitelist` | GlobalConfig | 资源 bot 白名单 |
| `deep_link.timeout_seconds` | GlobalConfig | 取片超时秒数 |
| `deep_link.min_interval_seconds` | GlobalConfig | 两次 StartBot 最小间隔秒数 |
| `deep_link.settle_seconds` | GlobalConfig | 首条媒体后的收齐静默秒数 |
| `deep_link.max_pages` | GlobalConfig | 翻页/组别按钮最大点击次数 |
| `deep_link.page_click_interval_seconds` | GlobalConfig | 翻页点击间隔秒数 |

## WebUI API → handler

路由仍由 `adapters/webui/server.py` 承接；具体 GET/POST/… 分发在 `adapters/webui/handlers/`（`auth` / `setup_api` / `tasks` / `watches` / `stats` / `media` / `archive_author` / `settings` / `misc` / `static_pages`）。契约未改。

| 路由 | 方法 | 作用 |
| ------ | ------ | ------ |
| `/api/settings` | GET/PATCH | 读写配置 |
| `/api/tasks` | GET/POST | 列出/创建转存任务；GET 返回 WebUI ViewModel task 列表 |
| `/api/tasks/<id>` | GET/DELETE | 获取任务详情 ViewModel / 删除任务 |
| `/api/tasks/<id>/summary` | GET | 获取任务统计 ViewModel 与最近事件 |
| `/api/tasks/<id>/pause` | POST | 暂停任务 |
| `/api/tasks/<id>/resume` | POST | 恢复任务 |
| `/api/tasks/<id>/retry-failed` | POST | 重试失败 Items |
| `/api/watches` | GET/POST | 列出/创建监听规则 |
| `/api/watches/<id>` | DELETE/PATCH | 删除/更新监听 |
| `/api/watches/<id>/events` | GET | 监听转发记录；`limit`/`offset`/`today`/`tz_offset`/`status=success\|skipped\|failure`；响应含 `status_counts` |
| `/api/statistics` | GET | 近 7 天按频道聚合的转存统计（`tz_offset` 可选） |
| `/api/operations` | GET | 操作历史 |
| `/api/transfer/detect-range` | POST | 检测频道消息范围 |
| `/api/media/scan` | GET | 扫描可清理文件 |
| `/api/media/cleanup` | POST | 执行文件清理 |
| `/api/auth/status` | GET | WebUI Telegram Login 步进状态 |
| `/api/auth/submit` | POST | 提交手机号/验证码/2FA |
| `/api/setup/status` | GET | First-run Setup Wizard 状态（含 Setup Ready） |
| `/api/setup/api` | POST | 保存 `api_id`/`api_hash`（可选代理）并触发 Client 重建 |
| `/api/setup/rclone` | POST | 非交互创建/覆盖 PikPak rclone remote 并探测 |
| `/api/setup/rclone/skip` | POST | 跳过 rclone；关闭归档 |
| `/api/setup/rclone/test` | POST | 探测已有 remote |
| `/api/setup/rclone/accounts` | GET | 列出绑定的 PikPak 账号（remote 名、激活态、缺失态） |
| `/api/setup/rclone/account` | POST | 添加 PikPak 账号（自动命名 remote，上限 5） |
| `/api/setup/rclone/switch` | POST | 切换到指定 PikPak 账号（改 `archive.remote` 并失效缓存） |
| `/api/setup/rclone/account/remove` | POST | 删除非激活 PikPak 账号（含 `rclone config delete`） |
| `/api/setup/bot` | POST | 校验（getMe）并保存可选 `bot_token` |
| `/api/setup/bot/skip` | POST | 跳过可选 Bot Token 步 |

## 术语 → 代码实体

| 术语 | 代码实体 |
| ------ | ---------- |
| Transfer Task | `persistence/store/tasks.py`（门面 `transfer_store.py`）→ `transfer_tasks` 表 |
| Transfer Item | `persistence/store/items.py` → `transfer_items` 表 |
| Transfer Progress | `persistence/store/*` → completed source_message_ids |
| PikPak Archive | `adapters/pikpak/integration.py` → `archive_pikpak_item()` |
| Source Channel Folder / Source Post Archive Path | `module/source_folders.py` → `archive_source_folder()` |
| PikPak Ingest Confirmation | `adapters/pikpak/integration.py` / downloader 转发等待路径 |
| Target Profile | `core/target_profiles.py` → `DEFAULT_TARGET_PROFILES` |
| Live Transfer Watch | `transfer/live_watch.py` → `LiveWatchManager` |
| Message Filter | `core/filter.py` → `MessageFilter` |
| Download Success Record | `persistence/store/tasks.py` 等 → `download_success` 表 |
| WebUI ViewModel Contract | `adapters/webui/view_model.py` → `WebUiViewModel` |
| First-run Setup Wizard / Setup Ready | `adapters/webui/setup.py` → `SetupCoordinator` |
| Archive Author Ops | `adapters/webui/archive_author_ops.py` → `ArchiveAuthorOps` |
| Execution Mode / watch_inline | `transfer/watch_inline.py` + TransferStore `execution_mode` |
| Deep Link Resolve | `transfer/deep_link.py` |
| Deferred Discussion Reply Capture | `transfer/comment_delay.py` |
| Composition Root | `composition_root.py` → `TrmdCompositionRoot` |
| TransferPorts / TransferContext | `transfer/context.py` |
