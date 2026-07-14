# Defer discussion reply capture for live forward watches

监听转发开启「包含评论区」时，主贴到达瞬间评论区资源常尚未就绪。我们选择：主贴立刻转发；讨论区按绝对到期时间延迟一次抓取（默认 20 分钟，可配置；`0` 表示立刻），任务写入 SQLite 以便重启恢复。拒绝轮询重试，以免半成品媒体组与资源浪费；手动/WebUI 事后转存不延迟。

**Considered Options:** 主贴与评论区一并延迟；到期后轮询直到有内容；仅内存 `asyncio.sleep` 不落库。

**Consequences:** 需调度器恢复与删规则时取消 pending/running；改延迟分钟数只影响新任务。执行中可手动取消（尽力中断派生转存）；失败/已取消可手动重试；无 worker 且无活跃派生转存的僵死 running（例如进程重启残留）重新入队为 pending（`due_at=now`）以便重启后续抓，不标失败、不触发取消钩子；不按墙钟超时误杀正常长任务。调度器须能挂到应用事件循环（含 WebUI 工作线程先创建实例的场景）。
