# 监听下载回退使用 watch_inline，不进入 Web 转存队列

Restricted Content Transfer（监听命中转发受限后的下载→上传）需要持久化 Transfer Task/Item，以便 PikPak Archive 延迟重试与进程重启恢复，并在 WebUI 可见。若把这些 Task 当作普通 `web_queue` 任务，启动恢复时会再次进入 `web_task_queue`，可能重复执行转发/下载。

**决定：** 增加 Execution Mode：`web_queue`（默认，由 Web 队列串行编排）与 `watch_inline`（监听内联执行）。`watch_inline` 任务永不入队；下载/上传继续共用既有 `download_upload_window` 与 FloodWait；归档与 Web 任务共用延迟重试 / `recover_pending_upload_archives`。任务创建时写入 `watch_id`；WebUI 转存任务列表不展示 `watch_inline`，改在对应监听的「下载记录」中按进行中 / 已完成 / 失败查看。

**考虑过但未采用：** 新建第二条互不干扰的执行队列（复杂度高，且归档本就不属于转存编排队列）；把监听回退强行并入 `web_task_queue` 串行（会让监听被大批量 Web 任务堵住，且不降低 API 限流风险——限流已由并发窗口与 FloodWait 处理）。
