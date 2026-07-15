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

Phase 0–3 架构解耦已完成：业务实现落在子包，顶层 `module/*.py` 多为兼容 shim；装配集中在 composition root；对外仍以 `TelegramRestrictedMediaDownloader` 为门面。

```
main.py
  └── TelegramRestrictedMediaDownloader          # module/downloader.py（门面）
        ├── TrmdCompositionRoot                  # module/composition_root.py（接线）
        ├── WebOperationsMixin                   # module/web_operations.py
        └── BotHostMixin                         # module/bot_host.py

装配出的主要模块：
  core/app.py              Application（下载路径 / 文件名）
  infra/client.py          Telegram 客户端（Pyrogram 扩展）
  adapters/bot/            Bot + CallbackHandler
  transfer/engine.py       TransferEngine
  transfer/runner.py       WebTransferRunner
  transfer/progress.py     TransferProgressTracker
  transfer/live_watch.py   LiveWatchManager
  persistence/transfer_store.py   TransferStore（SQLite）
  adapters/pikpak/         PikPak 集成 + rclone 归档
  adapters/webui/          HTTP 服务 / ViewModel / 任务调度 / 前端资源
  persistence/             LocalStorageGuard / MediaManager / SystemLog
  infra/                   DynamicAsyncWindow / TelegramUploader
  core/config.py           UserConfig + GlobalConfig
  ports.py                 Protocol seam（IWebUiOperations / IBotHost 等）
  transfer/context.py      TransferContext + TransferPorts
```

### 配置系统（双层）

| 配置层 | 类 | 文件名 | 位置 | 用途 |
|--------|-----|--------|------|------|
| 用户层 | `UserConfig` | `config.yaml` | 工作目录 | Telegram API 凭证、下载类型（由统一白名单派生兼容）、代理 |
| 全局层 | `GlobalConfig` | `.CONFIG.yaml` | `~/.config/TRMD/` | 上传行为、目标配置、消息过滤；媒体类型唯一真源为 `message_filter.media_types` |

### 子包结构

```
module/
  adapters/
    bot/          # Bot 命令与回调（bot.py, callback_handler.py）
    pikpak/       # PikPak 集成与 rclone 归档
    webui/        # HTTP 服务、ViewModel、任务调度、内嵌前端
  core/           # Application、Config、Enums、Filter、TargetProfiles
  infra/          # Client、Uploader、AsyncWindow
  persistence/    # TransferStore、MediaManager、LocalStorageGuard、SystemLog
  transfer/       # Engine、Runner、Progress、LiveWatch、DeepLink、CommentDelay…
  utils/          # util、stdio、path_tool、parser、language、diagnostics
```

顶层仍保留：`downloader.py`（门面）、`composition_root.py`、`web_operations.py`、`bot_host.py`、`ports.py`，以及指向子包实现的 shim（如 `bot.py` → `adapters.bot.bot`）。

**架构立场**：大规模搬包 / 再拆 God Object 已暂停；后续仅在具体痛点出现时做局部深化（例如 listen/forward 出门面、收窄 TransferPorts）。

---

## 数据流 — 转存流程

```
来源 Telegram 消息
    │
    ├──→ 尝试直接转发 (forward_messages)
    │       │
    │       ├── 成功 → [PikPak] 等待入库确认 → rclone 归档 → 完成
    │       └── 失败 (ChatForwardsRestricted 等)
    │              └──→ 回退: 创建 Watch Inline Transfer Task → 下载到本地 → 上传到目标
    │                     → [PikPak] 延迟 rclone 归档（可重试，重启可恢复）
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

**Execution Mode** — Transfer Task 的执行归属：`web_queue` 由 Web 转存队列串行编排；`watch_inline` 由监听 Restricted Content Transfer 内联执行，不入 Web 队列，不出现在转存任务列表，改在对应监听的「下载记录」中查看，并参与 PikPak Archive 延迟重试与重启恢复。
_Avoid_: Task queue type, hidden task, second queue

**Watch Inline Transfer Task** — 监听命中 Restricted Content Transfer 时自动创建的 Transfer Task（Execution Mode = `watch_inline`），单条消息一个 Task，创建时写入 `watch_id`；下载/上传走既有并发窗口，归档走与 Web 任务相同的延迟重试与恢复路径。WebUI 按监听展示进行中 / 已完成 / 失败。
_Avoid_: Listen queue job, ghost task

**Transfer Task** — 一条持久化的转存请求（来源链接 → 目标链接，含可选 ID 范围）。存储在 SQLite 的 `transfer_tasks` 表。
_Avoid_: Download task, forward job

**Transfer Item** — Transfer Task 中的单条消息/媒体记录。存储在 `transfer_items` 表。
_Avoid_: File task, message job

**Transfer Progress** — 已完成 Transfer Item 的集合。同名 Task 再次执行时跳过已完成的 Item，实现断点续传。
_Avoid_: Chapter cursor, runtime offset

**PikPak Target** — 与 PikPak 官方 bot 的 Telegram 会话，作为接收转存媒体的目标。
_Avoid_: PikPak API, cloud drive target

**PikPak Archive** — 目标侧组织步骤：确认 Source Post Archive Path 存在，将 PikPak Target 接收的媒体从 PikPak Ingest Folder 移动到该路径。启用时，归档必须完成才算 Transfer Item 成功。
_Avoid_: Local download folder, bot chat folder

**PikPak Ingest Folder** — PikPak bot 入库后的默认目录（"My Telegram"），PikPak Archive 执行前文件暂存于此。
_Avoid_: Archive root, source channel folder

**PikPak Ingest Confirmation** — PikPak bot 回复的确认消息，表示已接收并保存媒体。Telegram 送达不代表转存成功。
_Avoid_: Forward success, copy success

**Target Profile** — 目标特定的配置预设（如 `pikpak`），控制：是否以文档发送、发送后是否删除本地文件、文件大小上限。
_Avoid_: Preset, mode

**Source Channel Folder** — 来源频道对应的顶层文件夹名（归档路径第一段）；频道统计与来源身份按此聚合。
_Avoid_: Target folder, chat title cache, full archive path

**Source Post Archive Path** — 相对归档路径 `{Source Channel Folder}/{message_id} - {正文摘要}`（无摘要则仅 message_id）。同一频道主贴及其 Discussion Reply、深链取回内容共用此路径。
_Avoid_: Discussion group folder, bot chat folder, flat channel dump

**Live Transfer Watch** — 持续的频道监听规则，新消息到达时自动触发转存/转发；WebUI 表格中的“今日记录”只统计本地当天事件，完整历史记录通过分页弹框查看。
_Avoid_: Listen job, bot listener

**Live Transfer Status** — 用户可见的进度消息，展示下载/上传/目标发送/失败各阶段状态。
_Avoid_: Container log, final notice

**Automatic Transfer Range** — 仅提供频道链接（无消息 ID）时，自动探测最早和最晚可访问消息来确定范围。
_Avoid_: Auto dump, guessed range

**Download Success Record** — 已成功下载消息的持久化记录（按来源会话+消息 ID），后续转存可复用，避免重复下载。
_Avoid_: Cache hit, finished file

**Channel Download Statistics** — WebUI 统计面板按 Source Channel Folder（取 Source Post Archive Path 第一段；缺省回退 `source_chat_id`）聚合近 7 个本地自然日的 Transfer Item 终端态（success / failure / skipped）；数据来自 TransferStore，进程重启不丢失。
_Avoid_: In-memory link completion, upload task counters, media-type-only chart, per-post stats

**Local Transfer Storage Budget** — 下载→上传回退流程的本地磁盘预算。启动下载前按文件大小预留空间；成功、失败、跳过或删除后必须释放预算并清理不再可恢复的本地文件。
_Avoid_: Upload concurrency, temp cache size

**Transfer Task Pausing** — 用户请求暂停后的中间态：当前 Transfer Item 继续跑完，不新开下一条；兑现后进入 Transfer Task Pause。无手头 Item（排队中或重启后无在途工作）时可直接进入 Pause。
_Avoid_: Immediate kill, hard pause, force stop

**Transfer Task Pause** — 已兑现的暂停态：Transfer Task 不再启动下一条 Transfer Item；未完成 Item 可保留已对齐的临时缓存以便恢复，不视为失败清理。
_Avoid_: Cancel task, delete task, kill transfer

**Failed Item Retry** — 重试失败的 Transfer Item，成功的和跳过的保持为已完成。
_Avoid_: Restart task, rerun all, clear history

**Discussion Reply Inclusion** — 可选的 `--include-comment` 行为，包含来源消息下的讨论区回复。
_Avoid_: Comment scraping, reply mirroring

**Deferred Discussion Reply Capture** — 监听转发在开启 Discussion Reply Inclusion 时，主贴立即转发后，将讨论区抓取推迟到配置的到期时刻再执行一次的持久化任务。执行中可取消；失败或已取消可手动重试；无活跃 worker/派生转存的僵死 running（例如进程重启残留）会重新入队为 pending（`due_at=now`）以便恢复后续抓，不标失败、不触发取消钩子。
_Avoid_: Comment delay job, deferred comment poll, comment scrape loop, wall-clock capture timeout

**Deep Link Resolve** — 可选的转存前置步骤：当来源消息含白名单资源 bot 的 `t.me/<bot>?start=<param>`（或等价 `tg://`）时，用用户会话调用 `messages.startBot` 取回 bot 私聊中的 video/document/animation/photo，再对取回消息执行既有转发/下载上传；业务来源仍记为原频道帖。由任务/监听上的 `resolve_deep_link` 开关控制；全局 `deep_link.bot_whitelist` 限定可解析 bot；`timeout_seconds` / `min_interval_seconds` 控制取片超时与两次 StartBot 冷却（遇 FloodWait 在剩余超时预算内等待后重试；预算不足或拉历史挂起则立即失败并释放串行锁）；`settle_seconds`（默认 3）在首条媒体后继续收齐连发/相册直至静默。评论区深链仅在同时开启 Discussion Reply Inclusion 时处理：延迟抓取到的讨论回复**仅**走白名单深链 resolve（不附带按 `check_type` 转存其它评论）。取回内容仍受 Media Type Allowlist 约束。
_Avoid_: Bot scrape, start param hack, auto click teaser

**Media Type Allowlist** — 全局唯一的允许处理媒体类型集合（`message_filter.media_types`）。所有下载/转发链路（Web 转存、实时监听、Bot 频道下载、深链取回）共用；消息过滤总开关不管媒体类型，只控制日期与关键词。
_Avoid_: download_type, forward_type, per-pipeline type checkbox

**Media Type Override** — 转存任务、实时监听或 Bot 下载会话上可选的媒体类型整表替换；未设置则继承 Media Type Allowlist，设置后不再并入全局。
_Avoid_: type delta, additive filter, per-pipeline settings

**WebUI Credentials** — 环境变量提供的站内登录凭据。`TRMD_WEB_HOST` 非 localhost 时，必须设置用户名和密码；用户通过 WebUI 登录页换取 HttpOnly 签名 session cookie（HMAC，密钥由用户名/密码派生；勾选记住我后 Cookie `Max-Age` 为 30 天，进程/容器重启后仍有效；修改密码会使旧 cookie 失效）。
_Avoid_: HTTP Basic Auth, Random ttyd password, public WebUI, in-memory-only session store

**WebUI Telegram Login** — WebUI 中通过表单完成 Telegram 登录（替代 CLI `console.input()`）。
_Avoid_: CLI login, console auth, terminal login

**First-run Setup Wizard** — `--web` 模式下，在站内登录之后引导用户完成初始化：填写 Telegram API 凭证、完成 WebUI Telegram Login、可选配置 rclone PikPak remote。就绪判定以真实配置与会话为准（合法 `api_id`/`api_hash` + 已授权 Session）；已就绪的升级环境不弹全屏向导。rclone 可跳过；跳过或未探测成功时归档保持关闭。
_Avoid_: setup completed flag, forced rclone gate, stdin config_guide in web mode, ttyd rclone wizard

**Setup Ready** — First-run Setup Wizard 的硬门槛：API 凭证已保存且 Telegram 会话已授权。未就绪时屏蔽转存/监听等业务 API；设置里可重新登录 Telegram 或重配 rclone。
_Avoid_: initialization token, wizard finished marker

**WebUI ViewModel Contract** — WebUI 后端为桌面端与移动端共同输出的唯一公共数据契约。任务列表、任务详情、任务统计、设置选项均先在服务端归一化，再由前端共享脚本消费。
_Avoid_: Desktop-only payload, mobile-only field mapping, duplicated frontend state

---

## 关键外部依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| [kurigram](https://github.com/KurimizunAkuma/pyrogram) | 2.2.19 | Telegram MTProto API (Pyrogram fork) |
| rclone | — | PikPak 云盘归档（容器内安装） |
| SQLite | — | 转存任务状态持久化 |
| TailwindCSS | ^4.1.18 | WebUI 前端样式（字号 token：page 20 / title 16 / body 14 / caption 12；根 16px；表格统一 caption；仅移动端输入允许 16px；行距：标题 1.25 / 正文与说明 1.5；字距：仅 uppercase 标签 0.04em） |
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
- [ADR-0009](docs/adr/0009-watch-inline-transfer-execution-mode.md) — 监听下载回退用 watch_inline，不入 Web 队列
- [ADR-0010](docs/adr/0010-unified-media-type-allowlist.md) — 统一媒体类型白名单与任务级覆盖
- [ADR-0011](docs/adr/0011-source-post-archive-path.md) — 按频道主贴嵌套归档路径
- [ADR-0012](docs/adr/0012-first-run-webui-setup.md) — WebUI 首启配置向导（API / Telegram / rclone）

---

## 开发约定

- **版本号**: `pyproject.toml` 和 `module/__init__.py` 必须一致
- **测试**: `unit_tests/`，pytest 运行
- **Docker 构建**: GitHub Actions 在 `v*.*.*` tag push 时触发
- **发布流程**: bump 版本 → 提交 → `git tag -a vX.Y.Z` → push main + tag
- **提交信息** 末尾可附 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
