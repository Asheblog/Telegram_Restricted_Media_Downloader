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
  transfer/live_transfer.py LiveTransferService（listen/forward）
  persistence/transfer_store.py   TransferStore（SQLite）
  adapters/pikpak/         PikPak 集成 + rclone 归档
  adapters/webui/          HTTP 服务 / ViewModel / 任务调度 / 前端资源
  persistence/             LocalStorageGuard / MediaManager / SystemLog
  infra/                   DynamicAsyncWindow / TelegramUploader
  core/config.py           UserConfig + GlobalConfig
  ports.py                 Protocol seam（IWebUiOperations / IBotHost 等）
  transfer/context.py      TransferContext + TransferPorts（Paths / Progress / Target / Storage / Runtime 分簇）
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
  transfer/       # Engine、Runner、Progress、LiveWatch、LiveTransfer、DeepLink、CommentDelay…
  utils/          # util、stdio、path_tool、parser、language、diagnostics
```

顶层仍保留：`downloader.py`（门面）、`composition_root.py`、`web_operations.py`、`bot_host.py`、`ports.py`，以及指向子包实现的 shim（如 `bot.py` → `adapters.bot.bot`）；零引用的 `client.py` shim 已删除，请直接用 `module.infra.client`。

**架构立场**：大规模搬包 / 再拆 God Object 已暂停；后续仅在具体痛点出现时做局部深化（listen/forward 已抽出；TransferPorts 已分簇）。

---

## 数据流 — 转存流程

```
来源 Telegram 消息
    │
    ├──→ 尝试直接转发 (forward_messages)
    │       │
    │       ├── 成功 → [PikPak] 等待入库确认 → rclone 归档 → 完成
    │       └── 失败 (ChatForwardsRestricted 等)
    │              └──→ 回退: 创建 Watch Inline Transfer Task → 下载到本地
    │                     → [PikPak] rclone copyto "My Telegram"
    │                     → 延迟 rclone 归档（可重试，重启可恢复）
    │
    └── 下载→上传流程
            │
            下载到 temp_directory/chat_id/
            │
            [非 PikPak] 上传到目标会话
            [PikPak] rclone copyto "My Telegram"（不经 pikpak_bot）
            │
            [PikPak archive=true] rclone 从 "My Telegram" 移动到 "Telegram/<频道名>"
            │
            清理本地临时文件（rclone/上传成功后再删）
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

**Transfer Item** — Transfer Task 中的单条消息/媒体记录。存储在 `transfer_items` 表。长时间停在 `PENDING`/`RUNNING` 且无进度更新时，对账按全局 `transfer.item_stale_timeout_minutes`（默认 5）判失败并协作中止在途下载/转发，以释放队列；有下载/上传进度刷新 `updated_at` 时不误杀。
_Avoid_: File task, message job

**Transfer Progress** — 已完成 Transfer Item 的集合。同名 Task 再次执行时跳过已完成的 Item，实现断点续传。
_Avoid_: Chapter cursor, runtime offset

**PikPak Target** — 与 PikPak 官方 bot 的 Telegram 会话，作为接收转存媒体的目标。
_Avoid_: PikPak API, cloud drive target

**PikPak Archive** — 目标侧组织步骤：确认 Source Post Archive Path 存在，将 PikPak Target 接收的媒体从 PikPak Ingest Folder 移动到该路径。启用时，下载回退与直接转发均在入库确认后**延迟归档**（`archive_status=pending`）；Transfer Item 可先标 SUCCESS，归档失败记 archive 状态并可重试，不回滚转存成功。监听转发路径的归档在后台线程执行，不阻塞转发循环。Bot 直转入库名常为原始 basename，归档目标为 `{message_id} - {stem}.ext`；同 size 多候选时按「完整归档名 → 原始 basename（含 `name(N).ext`）→ 浅层 Path（优先 My Telegram 根下）→ 最近 ModTime」消歧；有 `{message_id} -` 前缀却无名命中、或仍并列时保持 ambiguous。递归 `lsjson` 若因幽灵子目录 `file_not_found` 失败，回退为非递归列表；`moveto` 源已不存在时若目标侧已有唯一匹配则记 `already_archived`。
_Avoid_: Local download folder, bot chat folder

**PikPak Ingest Folder** — PikPak bot 入库后的默认目录（"My Telegram"），PikPak Archive 执行前文件暂存于此。
_Avoid_: Archive root, source channel folder

**PikPak Ingest Confirmation** — PikPak bot 回复的确认消息，表示已接收并保存媒体。Telegram 送达不代表转存成功。
_Avoid_: Forward success, copy success

**Target Profile** — 目标特定的配置预设（如 `pikpak`），控制：是否以文档发送、发送后是否删除本地文件、文件大小上限。
_Avoid_: Preset, mode

**Source Channel Folder** — 来源频道对应的顶层文件夹名（归档路径第一段）；频道统计与来源身份按此聚合。
_Avoid_: Target folder, chat title cache, full archive path

**Source Post Archive Path** — 相对归档路径默认扁平 `{Source Channel Folder}/{message_id} - {正文摘要}`（无摘要则仅 message_id）。任务/监听规则勾选 **按作者归档**（`archive_by_author`，默认关）时扩展为 `{Source Channel Folder}/{Post Author}/{message_id} - {正文摘要}`；抽不到作者时 Post Author 为 `_未知作者`。正文摘要选择顺序：`【标题】` / `27. ...` 硬标题 → **正文中首个可用内容行为纯 `#标签` 时取其第一个非站点/题材黑名单标签**（导流句如「进入评论区…」「推荐指数」与纯 emoji 不计为可用内容）→ 普通正文行 → 文末标签；纯日期、`帖子内容`、作者署名行仍跳过。井号只进叶子摘要，不进 Post Author。否则取媒体原始 `file_name` 去扩展名。**叶子名稳定性（可追踪）**：同一次转存链路内，帖子叶子段一旦写成 `{message_id} - {描述}` 即冻结，归档 re-resolve / 迁入作者目录时不得再用「更好标题」改写描述；仅允许对纯 `{message_id}` **补全一次**标题。父级作者层仍可抬升（扁平→作者、`_未知作者`→真作者），已嵌套的作者段（含 `_未知作者`）不因 flag 丢失被压扁。Post Author 从正文署名行解析：完整标记 `…作者：#名字`，或短形式 `作者：#名字` / `作者：@名字`（去掉 `#`/`@`）。同一媒体组（相册）的图片/视频必须共用最小 `message_id` + 组内最佳标题 +（若开启）组内解析到的作者，禁止每个成员各自建目录；Web 区间转存命中相册时一次拉齐组成员、共享 `source_folder`，并跳过组内其余 id，评论只挂在共享主贴 id 上。每个成员的 `range_message_id` 仍用自身 message id，避免区间进度在相册空洞处卡住。目录段与可控文件名统一为 `{message_id} - {正文}`。同一频道主贴及其 Discussion Reply、深链取回内容共用此路径。历史扁平 `{channel}/{post}` 可由归档整理工具抬升到作者层（整理工具本身始终按作者启发式，与实时链路开关解耦；整理工具允许改路径，不受上述实时冻结约束）。
_Avoid_: Discussion group folder, bot chat folder, flat channel dump, per-album-member folders

**Post Author** — 主贴正文署名解析出的作者文件夹名（完整标记 `…作者：#xxx` 或短形式 `作者：#xxx` / `作者：@xxx`）；仅当 `archive_by_author` 开启时写入路径；无法解析时使用 `_未知作者`。位于 Source Channel Folder 与主贴目录之间。站点名 `海角社区` 等不当作者；上传者 UID `海角_<数字>` 可作为作者目录。历史归档整理还可在无署名时，用正文 hashtag 回连频道内已确认作者集合（精确命中可自动搬；近似命中进待确认）；若过滤站点/主题标签后只剩一个作者样标签，则进「待确认」作为标签候选（不自动建已知作者）。
_Avoid_: Telegram from_user, channel signature, uploader account

**Archive By Author** — 转存任务 / 监听规则上的可选开关（默认关）。关：扁平 Source Post Archive Path；开：嵌套 Post Author 层。字段名 `archive_by_author`；监听转发规则串可带 `--archive-by-author`。
_Avoid_: global channel preference, automatic opt-in

**Author Archive Reorganize** — WebUI 工具：按 Source Channel Folder 扫描 PikPak 归档中**频道顶层、数字 ID 开头**的扁平主贴目录（`{message_id} - …`）；已归档作者目录 / `更新` / 站点杂项目录等非数字 ID 顶层项只取其名称作已知作者种子（若可作作者），**不进入列子目录**。回查 Telegram 主贴解析 Post Author（署名 → 标签回连已知作者 / 唯一标签候选 → 未识别），生成迁移一览（汇总可点开分页明细）；「全部迁移」一键执行高置信 + 待确认，未识别默认不搬。「仅解析未识别」保留上次已识别结果，只回查未识别、`_未知作者` 与站点名误标主贴（含相册兄弟 hashtag），不必为此全量。整理串行移动并写 checkpoint；进程重启后自动续跑剩余项（幂等跳过已就位），可「停止」后再次迁移续跑。与实时链路的 `archive_by_author` 解耦，仅用于显式历史整理。
_Avoid_: media cleanup, full-disk rename, manual rclone script

**Migration Overview** — Author Archive Reorganize 的计划汇总视图：按 `move` / `needs_confirm` / `needs_review` / skip 分桶计数，明细经分页 API 拉取全量，浏览器不再截断预览。
_Avoid_: truncated 200-row table, per-row manual approve

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

**Transfer Task Pausing** — 用户请求暂停后的中间态：当前 Transfer Item（单个媒体文件/视频）继续跑完转发/入库确认，不新开下一条 Item（同一主贴/相册里的下一个视频也不开）；在途下载上传排空后进入 Transfer Task Pause。**不等待 PikPak Archive**（归档已改为延迟/后台）。无手头 Item（排队中或重启后无在途工作）时可直接进入 Pause。
_Avoid_: Immediate kill, hard pause, force stop, wait for whole post/album, wait for archive

**Transfer Task Pause** — 已兑现的暂停态：Transfer Task 不再启动下一条 Transfer Item；未完成 Item 可保留已对齐的临时缓存以便恢复，不视为失败清理。恢复时绑定已有 Item（item_id），跳过已 success/skipped 的来源消息；压制同消息上的僵尸 active 行，避免再开一轮 fallback 下载。
_Avoid_: Cancel task, delete task, kill transfer

**Failed Item Retry** — 重试失败的 Transfer Item，成功的和跳过的保持为已完成。
_Avoid_: Restart task, rerun all, clear history

**Discussion Reply Inclusion** — 可选的 `--include-comment` 行为，包含来源消息下的讨论区回复。
_Avoid_: Comment scraping, reply mirroring

**Deferred Discussion Reply Capture** — 监听转发在开启 Discussion Reply Inclusion 时，主贴立即转发后，将讨论区抓取推迟到配置的到期时刻再执行一次的持久化任务。延迟分钟数默认取全局 `live_watch.comment_delay_minutes`；Live Transfer Watch 可空字段 `comment_delay_minutes` 覆盖该默认（空=继承全局；`0`=立刻）。改全局或改任务覆盖均只影响之后新主贴。执行中可取消；失败或已取消可手动重试；无活跃 worker/派生转存的僵死 running（例如进程重启残留）会重新入队为 pending（`due_at=now`）以便恢复后续抓，不标失败、不触发取消钩子。
_Avoid_: Comment delay job, deferred comment poll, comment scrape loop, wall-clock capture timeout

**Deep Link Resolve** — 可选的转存前置步骤：当来源消息含白名单资源 bot 的 `t.me/<bot>?start=<param>`（或等价 `tg://`）时，用用户会话调用 `messages.startBot` 取回 bot 私聊中的 video/document/animation/photo，再对取回消息执行既有转发/下载上传；业务来源仍记为原频道帖。由任务/监听上的 `resolve_deep_link` 开关控制；全局 `deep_link.bot_whitelist` 限定可解析 bot；`timeout_seconds` / `min_interval_seconds` 控制取片超时与两次 StartBot 冷却（遇 FloodWait 在剩余超时预算内等待后重试；预算不足或拉历史挂起则立即失败并释放串行锁）；`settle_seconds`（默认 3）在首条媒体后继续收齐连发/相册直至静默；若 bot 以 inline 翻页/组别按钮分批发片，则在同一超时预算内自动点击收齐（`max_pages` 默认 20、`page_click_interval_seconds` 默认 1）；零媒体时优先点组别（含当前页标记如 `❄️ 1`）以触发发片；**已有媒体后跳过当前组别**（优先认 `❄/❄️` 标记，否则认首个带标记组别），优先点页码更大的组别（含 `✅` 访问标记），否则点「下一页」；发片机式 `📋 1-3/3` 页码条不单独当作内容末页，而以当前组别对比 status 总数判断是否还可下一页，避免重点当前页无新媒体而提前停翻。翻页点击失败时保留已收媒体继续转存。收片按 `file_unique_id`（无则 `file_id`）去重，同内容不同消息 ID 只保留一条；已有媒体时，某次翻页点击后若本波未接受任何新媒体则停止继续翻页；零媒体时点翻页无新媒体仍继续等到 `timeout_seconds`，不提前失败。若 bot 私聊出现业务失败文案：硬标记（「会话已超时关闭」「会话超时」）整波作废并可再 StartBot；软标记（「会话已关闭」「会话已退出」）仅在无媒体或仅 photo 预览时作废并重试，已有 video/document/animation 则保留（正常收尾，防误伤）；永久业务失败（「未找到凭证码」）立即标 FAILURE 且不再 StartBot（同参重试无意义）。同一轮历史先收媒体再判会话文案；仅 photo 预览波在 settle 后再宽限轮询约 2s 查会话失败文案，避免预览 collage 后超时句晚到而误标成功。作废后在遵守 `min_interval_seconds` 后再次 `StartBot`；同一次 resolve 最多 3 次 StartBot（每次各自使用完整 `timeout_seconds`）；仍失败则抛错标 FAILURE，不把预览图当成功、不回退频道封面。开启深链后若消息无白名单深链，则不转发原帖封面/预览（不回退、不标成功）；双开「包含评论区」时不记跳过项、交由评论区深链取片；未开评论区则标 FAILURE。翻页/组别按钮只认本次 StartBot 之后的消息，避免误点历史菜单。Web 转存在 resolve 与多片批次转发中响应 Transfer Task Pausing；暂停打断批次时**不**把原帖/原评论标为完成。评论区深链仅在同时开启 Discussion Reply Inclusion 时处理：延迟抓取到的讨论回复**仅**走白名单深链 resolve（不附带按 `check_type` 转存其它评论）。取回内容仍受 Media Type Allowlist 约束。
_Avoid_: Bot scrape, start param hack, auto click teaser, cover-fallback-as-success, no-link-as-skipped

**Media Type Allowlist** — 全局唯一的允许处理媒体类型集合（`message_filter.media_types`）。所有下载/转发链路（Web 转存、实时监听、Bot 频道下载、深链取回）共用；消息过滤总开关不管媒体类型，只控制日期与关键词。
_Avoid_: download_type, forward_type, per-pipeline type checkbox

**Keyword Blacklist** — `message_filter.keywords` 黑名单扫描面与 Source Post 标题语料对齐：`text` / `caption` / 相册继承 `_trmd_source_title` / `web_page.title` / 媒体 `file_name`。命中任一表面即跳过转发/转存。相册场景须把标题 `propagate_to` 写回监听更新里的触发消息（`get_media_group()` 常返回新对象）；开启 Deep Link Resolve 时先对**无白名单深链的来源帖**做黑名单，再 resolve；**含白名单深链的评论区资源卡**及 resolve 取回的 bot 媒体跳过关键词（资源卡常含「搜索」等，否则会误杀取片）。
_Avoid_: caption-only keyword scan, whitelist-as-blacklist, keyword-block-deep-link-comments

**Media Type Override** — 转存任务、实时监听或 Bot 下载会话上可选的媒体类型整表替换；未设置则继承 Media Type Allowlist，设置后不再并入全局。
_Avoid_: type delta, additive filter, per-pipeline settings

**WebUI Credentials** — 环境变量提供的站内登录凭据。`TRMD_WEB_HOST` 非 localhost 时，必须设置用户名和密码；用户通过 WebUI 登录页换取 HttpOnly 签名 session cookie（HMAC，密钥由用户名/密码派生；勾选记住我后 Cookie `Max-Age` 为 30 天，进程/容器重启后仍有效；修改密码会使旧 cookie 失效）。
_Avoid_: HTTP Basic Auth, Random ttyd password, public WebUI, in-memory-only session store

**WebUI Telegram Login** — WebUI 中通过表单完成 Telegram 登录（替代 CLI `console.input()`）。
_Avoid_: CLI login, console auth, terminal login

**First-run Setup Wizard** — `--web` 模式下，在站内登录之后引导用户完成初始化：填写 Telegram API 凭证、完成 WebUI Telegram Login、**强制配置** rclone PikPak remote（新装不可跳过）、可选配置 Bot Token（`getMe` 校验或跳过；已有合法 token 则自动跳过）。就绪判定以真实配置与会话为准（合法 `api_id`/`api_hash` + 已授权 Session）；已就绪的升级环境不弹全屏向导。rclone 探测成功后开启归档。
_Avoid_: setup completed flag, optional rclone skip on new install, required bot token on first run, stdin config_guide in web mode, ttyd rclone wizard

**Setup Ready** — First-run Setup Wizard 的硬门槛：API 凭证已保存且 Telegram 会话已授权。未就绪时屏蔽转存/监听等业务 API；新装另需配通 rclone，并处理可选 Bot Token 步（保存或跳过）后才结束向导。设置里可重新登录 Telegram、重配 rclone 或填写 Bot Token。
_Avoid_: initialization token, wizard finished marker

**PikPak Rclone Ingest** — 下载回退路径将本地文件经 rclone `copyto` 上传到 PikPak Ingest Folder（`My Telegram`），再复用既有 PikPak Archive（匹配/moveto/改名）；不再经 `@pikpak_bot` Telegram 上传。直接转发路径仍可走 bot。
_Avoid_: bot-only ingest, archive-bypass upload

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
- [ADR-0012](docs/adr/0012-first-run-webui-setup.md) — WebUI 首启配置向导（API / Telegram / rclone / 可选 Bot Token）

---

## 开发约定

- **版本号**: `pyproject.toml` 和 `module/__init__.py` 必须一致
- **测试**: `unit_tests/`，pytest 运行
- **Docker 构建**: GitHub Actions 在 `v*.*.*` tag push 时触发
- **发布流程**: bump 版本 → 提交 → `git tag -a vX.Y.Z` → push main + tag
- **提交信息** 末尾可附 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
