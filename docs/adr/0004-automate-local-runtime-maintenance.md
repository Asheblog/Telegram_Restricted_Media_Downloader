# ADR-0004: 自动本地运行时维护

**决策日期**: 2025-06 | **最后更新**: 2026-07-11 | **状态**: ✅ 已采纳

---

## Context

长期运行的 WebUI 部署会产生：

- 日志文件：每日轮转但旧文件无自动清理机制，磁盘占用持续增长
- Docker 容器 stdout/stderr：长期运行后 json-file 日志可能占满磁盘
- SQLite 数据库：频繁写入后产生碎片，查询性能下降；WAL 文件可能膨胀；业务事件表（transfer_events、live_watch_events、cleanup_log）持续增长
- 媒体目录：Transfer 完成后可能残留孤儿文件，此前主要依赖 WebUI 手动扫描
- 之前依赖运维人员手动维护，不适合无人值守的长期部署

## Decision

自动化以下维护任务：

**Docker 容器日志**：
- `docker-compose.yml` 为 `trmd` 服务配置 `json-file` 驱动
- `max-size: 10m`、`max-file: 5`，限制单容器 docker logs 占用约 50MB

**应用日志维护**：
- 使用 `TimedRotatingFileHandler` 按日轮转
- 启动时清理超过 3 天的旧日志文件 (`cleanup_old_log_files()`)
- 后台 daemon 线程每 24 小时再次执行 `cleanup_old_log_files()`
- 默认保留 3 天日志备份（`LOG_RETENTION_DAYS = 3`）

**SQLite 维护** (`TransferStore.maintain()`)：
- 连接时执行 `PRAGMA journal_mode=WAL` 和性能相关 pragma
- 定期 WAL checkpoint（避免 WAL 文件无限增长）
- 定期 `PRAGMA optimize`（更新查询计划统计）
- 空闲页超过阈值（512 页）时执行 `VACUUM`（回收磁盘空间）
- 维护间隔最小 6 小时，避免频繁 VACUUM 影响性能

**SQLite 业务事件保留** (`TransferStore.purge_old_event_records()`)：
- 在 `maintain()` 结束时调用，独立 marker 控制频率（至少间隔 7 天）
- `transfer_events`：保留 90 天
- `live_watch_events`：保留 30 天
- `cleanup_log`：保留 30 天
- 仅删除事件/日志行，不删除 `transfer_tasks`、`transfer_items`、`live_transfer_watches`

**媒体孤儿文件自动清理**：
- `MediaManager.auto_cleanup_orphan_files()` 扫描并删除超过保留天数（默认 7 天）的孤儿文件
- 主事件循环中 `maybe_run_scheduled_media_cleanup()` 每 24 小时执行一次
- 与 WebUI 手动清理共用同一套路径规则与 `cleanup_log` 记录

## Consequences

- ✅ 长期运行无需手动维护
- ✅ 磁盘空间自动回收（应用日志、Docker 日志、SQLite 事件、媒体孤儿文件）
- ✅ SQLite 性能保持稳定
- ⚠️ VACUUM 期间数据库锁定，可能短暂阻塞写入
- ⚠️ 超过保留期的事件/WebUI 日志不可恢复；Transfer Tasks / Items 本身不受影响
- ⚠️ 自动孤儿清理仅处理超过保留阈值且不在活跃 transfer item 中的文件
