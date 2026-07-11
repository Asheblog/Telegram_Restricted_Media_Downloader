# CONTEXT-MAP — 项目速查映射

> **注意**: 行数为编写时的近似快照，随时可能因代码变更而过时。

## 文件 → 职责速查

| 文件 | 职责 | 行数(≈快照) |
|------|------|----------|
| `main.py` | 入口：检查环境 → 创建 TRMD → run() | 12 |
| `module/__init__.py` | 全局常量、版本号、日志初始化、banner | 196 |
| `module/downloader.py` | 主控制器，编排所有子系统 | 3700+ |
| `module/app.py` | Telegram 客户端、下载文件名生成、关机 | 374 |
| `module/client.py` | Pyrogram 客户端扩展（登录、文件下载、会话） | 958 |
| `module/bot.py` | Telegram Bot 命令处理 + 内联键盘 | 1962 |
| `module/callback_handler.py` | Bot 内联按钮回调路由 | ~500 |
| `module/config.py` | 双层配置系统（UserConfig + GlobalConfig） | 870 |
| `module/transfer_engine.py` | 转存核心引擎（下载→上传流程编排） | ~800 |
| `module/transfer_store.py` | SQLite 持久化（任务/Item/事件/Watch CRUD） | ~600 |
| `module/transfer_progress.py` | 转存进度跟踪（恢复/续传） | ~400 |
| `module/web_ui.py` | WebUI HTTP 服务 + REST API | ~2000 |
| `module/webui_view_model.py` | WebUI 桌面端/移动端统一 ViewModel 契约 | ~300 |
| `module/web_task_manager.py` | WebUI 任务调度器 | ~500 |
| `module/web_ui_assets.py` | WebUI 内嵌前端资源（兼容别名） | — |
| `module/live_watch_manager.py` | 实时监听频道管理 | ~300 |
| `module/pikpak_integration.py` | PikPak 集成（入库确认、归档） | ~300 |
| `module/pikpak_archive.py` | rclone PikPak 归档客户端 | ~150 |
| `module/filter.py` | 消息过滤器（媒体类型/日期/关键词黑名单） | 185 |
| `module/target_profiles.py` | 目标配置：PikPak 大小限制、默认 profile | 43 |
| `module/source_folders.py` | 来源频道文件夹名提取 | 64 |
| `module/uploader.py` | Telegram 上传器 | ~400 |
| `module/task.py` | DownloadTask / UploadTask 数据结构 | ~200 |
| `module/enums.py` | 枚举/常量：类型、状态、按钮文案、验证、Banner | 1582 |
| `module/parser.py` | CLI 参数解析 | 100 |
| `module/language.py` | 中文本地化翻译表 | 67 |
| `module/path_tool.py` | 路径/文件名处理工具 | ~300 |
| `module/util.py` | 通用工具（链接解析、消息、环境判断） | 428 |
| `module/stdio.py` | 终端 I/O、进度条、统计表 | ~600 |
| `module/diagnostics.py` | 诊断日志适配器 | ~100 |
| `module/comp.py` | TransferContext 组合上下文 | 52 |
| `module/ports.py` | Protocol 接口定义（IWebUiOperations 等） | 73 |
| `module/transfer_registry.py` | 转存注册表 | — |
| `module/async_window.py` | 动态并发窗口 | ~80 |
| `module/local_storage_guard.py` | 磁盘空间守护 | ~150 |
| `module/media_manager.py` | 媒体文件清理 | ~300 |

## 子包 → 内容

| 子包 | 内容 | 状态 |
|------|------|------|
| `adapters/webui/` | `assets.py`（内嵌 HTML/CSS/JS/Font）、`build_frontend.py`（Tailwind 构建）、`download_fonts.py` | ✅ 已填充 |
| `adapters/bot/` | `__init__.py` 占位 | 🔜 待迁移 |
| `adapters/pikpak/` | `__init__.py` 占位 | 🔜 待迁移 |
| `core/` | `__init__.py` 占位 | 🔜 待迁移 |
| `infra/` | `__init__.py` 占位 | 🔜 待迁移 |
| `persistence/` | `__init__.py` 占位 | 🔜 待迁移 |
| `transfer/` | `__init__.py` 占位 | 🔜 待迁移 |
| `utils/` | `__init__.py` 占位 | 🔜 待迁移 |

## 配置项 → 位置

| 配置项 | 所属配置层 | 字段路径 |
|--------|-----------|----------|
| api_id, api_hash | UserConfig | `config.api_id` / `config.api_hash` |
| bot_token | UserConfig | `config.bot_token` |
| download_type | UserConfig | `config.download_type` |
| save/temp/session_directory | UserConfig | `config.*_directory` |
| proxy | UserConfig | `config.proxy.*` |
| max_tasks (download/upload) | UserConfig | `config.max_tasks.*` |
| max_retries | UserConfig | `config.max_retries.*` |
| upload (download_upload, delete, pending_limit) | GlobalConfig | `gc.upload.*` |
| target_profiles (pikpak archive 等) | GlobalConfig | `gc.target_profiles.pikpak.*` |
| forward_type (媒体类型开关) | GlobalConfig | `gc.forward_type.*` |
| message_filter | GlobalConfig | `gc.message_filter.*` |
| file_log_level / console_log_level | GlobalConfig | `.CONFIG.yaml` |
| notice | GlobalConfig | `.CONFIG.yaml` |
| `deep_link.bot_whitelist` | GlobalConfig | 资源 bot 白名单 |
| `deep_link.timeout_seconds` | GlobalConfig | 取片超时秒数 |

## WebUI API → handler

| 路由 | 方法 | 作用 |
|------|------|------|
| `/api/settings` | GET/PATCH | 读写配置 |
| `/api/tasks` | GET/POST | 列出/创建转存任务；GET 返回 WebUI ViewModel task 列表 |
| `/api/tasks/<id>` | GET/DELETE | 获取任务详情 ViewModel / 删除任务 |
| `/api/tasks/<id>/summary` | GET | 获取任务统计 ViewModel 与最近事件 |
| `/api/tasks/<id>/pause` | POST | 暂停任务 |
| `/api/tasks/<id>/resume` | POST | 恢复任务 |
| `/api/tasks/<id>/retry-failed` | POST | 重试失败 Items |
| `/api/watches` | GET/POST | 列出/创建监听规则 |
| `/api/watches/<id>` | DELETE/PATCH | 删除/更新监听 |
| `/api/statistics` | GET | 获取统计 |
| `/api/operations` | GET | 操作历史 |
| `/api/transfer/detect-range` | POST | 检测频道消息范围 |
| `/api/media/scan` | GET | 扫描可清理文件 |
| `/api/media/cleanup` | POST | 执行文件清理 |
| `/api/telegram/status` | GET | Telegram 登录状态 |
| `/api/telegram/login` | POST | WebUI 登录 Telegram |

## 术语 → 代码实体

| 术语 | 代码实体 |
|------|----------|
| Transfer Task | `transfer_store.py` → `transfer_tasks` 表 |
| Transfer Item | `transfer_store.py` → `transfer_items` 表 |
| Transfer Progress | `transfer_store.py` → completed source_message_ids |
| PikPak Archive | `pikpak_integration.py` → `archive_pikpak_item()` |
| PikPak Ingest Confirmation | `downloader.py` → `wait_for_pikpak_ingest_confirmation()` |
| Target Profile | `target_profiles.py` → `DEFAULT_TARGET_PROFILES` |
| Live Transfer Watch | `live_watch_manager.py` → `LiveWatchManager` |
| Message Filter | `filter.py` → `MessageFilter` |
| Download Success Record | `transfer_store.py` → `download_success` 表 |
| WebUI ViewModel Contract | `webui_view_model.py` → `WebUiViewModel` |
