# 转存项租约（防误判超时）+ 媒体管理失败项重试

## 背景与根因

- 对账 `TransferStore._fail_stale_active_items` 把 `updated_at` 超过 `item_stale_timeout_minutes`（默认 5）的 `PENDING/RUNNING` 条目直接 SQL 置为 `failure`，不调用本地文件清理钩子。
- 被判失败后 `should_continue_web_transfer_item` 返回 False，在途/排队的上传协作中止，于是文件留在磁盘、条目停在失败。
- 以下“合法等待”期间没有任何进度写 `updated_at`，因此被误判：
  - 上传并发等待：`TelegramUploader.__add_task` 在 `current_task_num >= max_upload_task`（默认 1）时死等；前一个 1.5 GB 在传，后面的文件排队 >5 分钟。
  - PikPak rclone ingest 只报开始/结束进度；FloodWait 等待。
  - 本地存储预留等待（`reserve_transfer_local_storage`），条目已是 RUNNING。
  - 重试后条目回到 `PENDING`，在下载槽/下载窗口/任务队列等待；若被判失败，`create_transfer_item_for_download` 见到终态会 `_skip_download`，重试白做。
- 媒体管理页列出“失败且留有本地文件”的条目，但无重试入口、不显示失败原因；任务级“重试失败”入口在转存任务/实时监听页，用户找不到。

## 决策

### A. 转存项租约（Transfer Item Lease）

- 进程内租约集合放在 `TransferStore`（与 `_last_reconcile_check` 同类的内存态，加 `threading.Lock`；不落库，重启即清空——重启后的僵尸条目仍按原超时回收）。
- 新增 `TransferStore.lease_items(item_ids: Iterable[int]) -> None`。
- 新常量 `TransferStore.LEASED_TRANSFER_ITEM_TIMEOUT_SECONDS = 24 * 3600`。
- `_fail_stale_active_items`：
  - 未持租约：沿用原超时与原文案。
  - 持租约：仅当 `updated_at` 超过 24 小时才判失败（兜底防泄漏），文案同格式，分钟数为 1440。
  - 每次对账先修剪租约：移除状态不再是 `pending/running` 或已不存在的条目。
- 加租约的位置（谁接手就谁加）：
  1. `TransferStore.retry_failed_item_ids`：对实际被重置的条目加租约（覆盖任务级重试与新增的媒体重试）。
  2. `TransferEngine.create_transfer_item_for_download`：条目置为 `RUNNING/downloading` 后加租约（新建与复用两个分支）。
  3. `TransferProgressTracker.on_transfer_file_ready`：两个分支置为 `RUNNING/uploading` 后加租约（覆盖不经 engine 的路径）。
- 不改：下载/上传进度刷新逻辑、`item_stale_timeout_minutes` 配置语义（仍为“无人接手的条目”超时）。

### B. 按条目重试（媒体管理页）

- `WebTaskManager.retry_failed_web_task(task_id, submit_fn=None, item_ids=None)`：`item_ids` 非空时只重试其中的失败/可恢复条目，且不走 watch inline “空失败”分支。
- 新增 `WebTaskManager.retry_failed_web_items(item_ids) -> dict`：按 `task_id` 分组调用上者，返回 `{"retried_items": int, "task_ids": [int]}`；不存在的条目忽略。
- 贯通：`WebOperationsMixin.retry_failed_web_items`（加入 ops 名单）→ `ports` 协议 → `WebUiServer.retry_media_items(payload)` → `POST /api/media/retry`，body `{"item_ids": [...]}`；空列表返回 400 `invalid_item_ids`。
- 扫描结果条目增加 `error_message` 字段。
- 桌面端媒体页：
  - 失败行的状态徽章 `title` 显示失败原因；行尾新增“重试”按钮（仅 `status == failure`）。
  - 头部新增“重试选中失败项”按钮（仅勾选中含失败项时可用），与“清理选中文件”并列。
  - 清理确认文案提示“失败项删除后重试需重新下载”。
- 移动端媒体页：失败条目显示“重试”小按钮。
- 重试成功后刷新媒体列表，提示重置条数。

## 验证

- 新增/修改测试：
  - `unit_tests/transfer_task_reconcile_case.py`：持租约条目在 5 分钟陈旧时不被判失败；超过 24 小时仍判失败；对账修剪终态条目的租约；`retry_failed_item_ids` 后条目持租约。
  - `unit_tests/transfer_store_webui_case.py`：`retry_failed_web_items` 只重置指定失败条目、按任务分组提交；`POST /api/media/retry` 路由与空参数 400。
  - `unit_tests/media_manager_case.py`：扫描结果含 `error_message`。
- 命令：`python -m pytest unit_tests -q`（全量，报告所有失败，含非本次引入）。
- UI：本地起 WebUI，截图媒体管理页（含失败项、按钮可用/禁用态、窄屏），截图存 `docs/superpowers/screenshots/2026-10-15-media-retry/`。

## 文档

- `CONTEXT.md` 的 Transfer Item 条目补充“租约”语义；新增术语 **Transfer Item Lease**。

## Review Focus

- 租约泄漏面：仅靠修剪 + 24 小时兜底是否足够；有没有遗漏的“合法等待”路径（如媒体组 `send_media_group` 轮询）。
- `retry_failed_web_task` 加 `item_ids` 后，watch inline 与 PikPak 可恢复条目的分支行为不变。
- 媒体重试与“清理”并存时的误操作风险（勾选同时含失败项）。
