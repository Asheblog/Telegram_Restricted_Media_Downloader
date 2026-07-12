# TRMD — Telegram Restricted Media Downloader (WebUI Fork)

## 项目概述

TRMD 是一个长期运行的 Telegram 媒体转存工具，通过 WebUI 操作。它把用户有权访问的 Telegram 内容转存到目标会话（默认为 PikPak bot），并可自动将 PikPak 入库后的文件按来源频道归档到 PikPak 云盘。

- **上游**: [Gentlesprite/Telegram_Restricted_Media_Downloader](https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader) (v2.x)
- **本 Fork**: [Asheblog/Telegram_Restricted_Media_Downloader](https://github.com/Asheblog/Telegram_Restricted_Media_Downloader) (v0.2.x)
- **许可证**: MIT
- **Python**: ≥3.13.2
- **入口**: `main.py`

---

## 核心架构

```
main.py (入口)
  └── TelegramRestrictedMediaDownloader (主控制器, downloader.py, ~3700行)
        ├── Application (Telegram 客户端 + 下载/文件名逻辑, app.py)
        │     └── TelegramRestrictedMediaDownloaderClient (Pyrogram 扩展, client.py)
        ├── Bot (Telegram Bot 命令处理, bot.py)
        ├── CallbackHandler (Bot 回调处理, callback_handler.py)
        ├── TransferEngine (转存引擎, transfer_engine.py)
        ├── TransferStore (SQLite 持久化, transfer_store.py)
        ├── TransferProgressTracker (转存进度跟踪, transfer_progress.py)
        ├── PikpakIntegrationManager (PikPak 集成, pikpak_integration.py)
        ├── WebUITaskManager (WebUI 任务调度, web_task_manager.py)
        ├── LiveWatchManager (实时监听管理, live_watch_manager.py)
        ├── WebUiServer (WebUI HTTP 服务, web_ui.py)
        ├── WebUiViewModel (WebUI 统一数据契约, webui_view_model.py)
        ├── LocalStorageGuard (本地磁盘守护, local_storage_guard.py)
        ├── DynamicAsyncWindow (并发窗口控制, async_window.py)
        ├── MediaManager (媒体文件清理, media_manager.py)
        ├── UserConfig (config.yaml 用户配置, config.py)
        └── GlobalConfig (.CONFIG.yaml 全局配置, config.py)
```

### 配置系统（双层）

| 配置层 | 类 | 文件名 | 位置 | 用途 |
|--------|-----|--------|------|------|
| 用户层 | `UserConfig` | `config.yaml` | 工作目录 | Telegram API 凭证、下载类型、代理 |
| 全局层 | `GlobalConfig` | `.CONFIG.yaml` | `~/.config/TRMD/` | 上传行为、目标配置、消息过滤、转发类型 |

### 子包结构

```
module/
  adapters/       # 外部系统适配器
    bot/          # Bot 相关（待迁移）
    pikpak/       # PikPak 相关（待迁移）
    webui/        # WebUI HTTP + 内嵌前端资源 (assets.py, build_frontend.py)
  core/           # 核心域对象（占位）
  infra/          # 基础设施（占位）
  persistence/    # 持久化层（占位）
  transfer/       # 转存领域（占位）
  utils/          # 工具函数（占位）
```

大部分业务逻辑仍在 `module/*.py` 顶层文件中，子包为架构升级框架。

---

## 数据流 — 转存流程

```
来源 Telegram 消息
    │
    ├──→ 尝试直接转发 (forward_messages)
    │       │
    │       ├── 成功 → [PikPak] 等待入库确认 → rclone 归档 → 完成
    │       └── 失败 (ChatForwardsRestricted 等)
    │              └──→ 回退: 下载到本地 → 上传到目标
    │
    └── 下载→上传流程
            │
            下载到 temp_directory/chat_id/
            │
            上传到目标会话
            │
            [PikPak] 等待 PikPak bot 回复确认消息
            │
            [PikPak archive=true] rclone 从 "My Telegram" 移动到 "Telegram/<频道名>"
            │
            清理本地临时文件
```

---

## 领域术语表

**Restricted Content Transfer** — Telegram 原生转发受限时的下载→重发回退流程。
_Avoid_: Forward bypass, restricted forward, mirror

**Transfer Task** — 一条持久化的转存请求（来源链接 → 目标链接，含可选 ID 范围）。存储在 SQLite 的 `transfer_tasks` 表。
_Avoid_: Download task, forward job

**Transfer Item** — Transfer Task 中的单条消息/媒体记录。存储在 `transfer_items` 表。
_Avoid_: File task, message job

**Transfer Progress** — 已完成 Transfer Item 的集合。同名 Task 再次执行时跳过已完成的 Item，实现断点续传。
_Avoid_: Chapter cursor, runtime offset

**PikPak Target** — 与 PikPak 官方 bot 的 Telegram 会话，作为接收转存媒体的目标。
_Avoid_: PikPak API, cloud drive target

**PikPak Archive** — 目标侧组织步骤：确认 Source Channel Folder 存在，将 PikPak Target 接收的媒体从 PikPak Ingest Folder 移动到对应 Source Channel Folder。启用时，归档必须完成才算 Transfer Item 成功。
_Avoid_: Local download folder, bot chat folder

**PikPak Ingest Folder** — PikPak bot 入库后的默认目录（"My Telegram"），PikPak Archive 执行前文件暂存于此。
_Avoid_: Archive root, source channel folder

**PikPak Ingest Confirmation** — PikPak bot 回复的确认消息，表示已接收并保存媒体。Telegram 送达不代表转存成功。
_Avoid_: Forward success, copy success

**Target Profile** — 目标特定的配置预设（如 `pikpak`），控制：是否以文档发送、发送后是否删除本地文件、文件大小上限。
_Avoid_: Preset, mode

**Source Channel Folder** — 从来源链接提取的文件系统安全文件夹名，同一来源频道的媒体归入同一文件夹。
_Avoid_: Target folder, chat title cache

**Live Transfer Watch** — 持续的频道监听规则，新消息到达时自动触发转存/转发；WebUI 表格中的“今日记录”只统计本地当天事件，完整历史记录通过分页弹框查看。
_Avoid_: Listen job, bot listener

**Live Transfer Status** — 用户可见的进度消息，展示下载/上传/目标发送/失败各阶段状态。
_Avoid_: Container log, final notice

**Automatic Transfer Range** — 仅提供频道链接（无消息 ID）时，自动探测最早和最晚可访问消息来确定范围。
_Avoid_: Auto dump, guessed range

**Download Success Record** — 已成功下载消息的持久化记录（按来源会话+消息 ID），后续转存可复用，避免重复下载。
_Avoid_: Cache hit, finished file

**Channel Download Statistics** — WebUI 统计面板按 Source Channel Folder（缺省回退 `source_chat_id`）聚合近 7 个本地自然日的 Transfer Item 终端态（success / failure / skipped）；数据来自 TransferStore，进程重启不丢失。
_Avoid_: In-memory link completion, upload task counters, media-type-only chart

**Local Transfer Storage Budget** — 下载→上传回退流程的本地磁盘预算。启动下载前按文件大小预留空间；成功、失败、跳过或删除后必须释放预算并清理不再可恢复的本地文件。
_Avoid_: Upload concurrency, temp cache size

**Transfer Task Pause** — 暂停后的 Transfer Task 阻止下一条 Transfer Item 启动；正在下载的 Transfer Item 可保留已对齐的临时缓存以便恢复，不视为失败清理。
_Avoid_: Cancel task, delete task, kill transfer

**Failed Item Retry** — 重试失败的 Transfer Item，成功的和跳过的保持为已完成。
_Avoid_: Restart task, rerun all, clear history

**Discussion Reply Inclusion** — 可选的 `--include-comment` 行为，包含来源消息下的讨论区回复。
_Avoid_: Comment scraping, reply mirroring

**Deferred Discussion Reply Capture** — 监听转发在开启 Discussion Reply Inclusion 时，主贴立即转发后，将讨论区抓取推迟到配置的到期时刻再执行一次的持久化任务。
_Avoid_: Comment delay job, comment scrape retry, deferred comment poll

**Deep Link Resolve** — 可选的转存前置步骤：当来源消息含白名单资源 bot 的 `t.me/<bot>?start=<param>`（或等价 `tg://`）时，用用户会话调用 `messages.startBot` 取回 bot 私聊中的 video/document/animation，再对取回消息执行既有转发/下载上传；业务来源仍记为原频道帖。由任务/监听上的 `resolve_deep_link` 开关控制；全局 `deep_link.bot_whitelist` 限定可解析 bot；`timeout_seconds` / `min_interval_seconds` 控制取片超时与两次 StartBot 冷却（遇 FloodWait 等待后重试）。
_Avoid_: Bot scrape, start param hack, auto click teaser

**WebUI Credentials** — 环境变量提供的站内登录凭据。`TRMD_WEB_HOST` 非 localhost 时，必须设置用户名和密码；用户通过 WebUI 登录页换取 HttpOnly session cookie。
_Avoid_: HTTP Basic Auth, Random ttyd password, public WebUI

**WebUI Telegram Login** — WebUI 中通过表单完成 Telegram 登录（替代 CLI `console.input()`）。
_Avoid_: CLI login, console auth, terminal login

**WebUI ViewModel Contract** — WebUI 后端为桌面端与移动端共同输出的唯一公共数据契约。任务列表、任务详情、任务统计、设置选项均先在服务端归一化，再由前端共享脚本消费。
_Avoid_: Desktop-only payload, mobile-only field mapping, duplicated frontend state

---

## 关键外部依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| [kurigram](https://github.com/KurimizunAkuma/pyrogram) | 2.2.19 | Telegram MTProto API (Pyrogram fork) |
| rclone | — | PikPak 云盘归档（容器内安装） |
| SQLite | — | 转存任务状态持久化 |
| TailwindCSS | ^4.1.18 | WebUI 前端样式 |
| Rich | 14.2.0 | 终端格式化输出 |
| PyYAML | ≥6.0.3 | 配置文件读写 |
| pymediainfo | 7.0.1 | 媒体文件元信息 |
| qrcode | ≥8.2 | QR 码登录 |
| tgcrypto | ≥1.2.5 | Telegram 加密加速 |
| pygments | ≥2.19.2 | 语法高亮 |

---

## 技术决策记录

见 `docs/adr/`:

- [ADR-0001](docs/adr/0001-replace-ttyd-with-visual-webui.md) — 用 WebUI 替代 ttyd 终端
- [ADR-0002](docs/adr/0002-persist-transfer-state-in-sqlite.md) — SQLite 持久化转存状态
- [ADR-0003](docs/adr/0003-require-webui-auth-for-remote-listening.md) — 远程访问必须认证
- [ADR-0004](docs/adr/0004-automate-local-runtime-maintenance.md) — 自动日志轮转与 SQLite 维护
- [ADR-0005](docs/adr/0005-unify-webui-view-model-contract.md) — 统一 WebUI 桌面端与移动端数据契约
- [ADR-0007](docs/adr/0007-defer-discussion-reply-capture.md) — 监听转发评论区延迟一次抓取
- [ADR-0008](docs/adr/0008-deep-link-resolve.md) — 转存前深链取片（用户会话 StartBot）

---

## 开发约定

- **版本号**: `pyproject.toml` 和 `module/__init__.py` 必须一致
- **测试**: `unit_tests/`，pytest 运行
- **Docker 构建**: GitHub Actions 在 `v*.*.*` tag push 时触发
- **发布流程**: bump 版本 → 提交 → `git tag -a vX.Y.Z` → push main + tag
- **提交信息** 末尾可附 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
