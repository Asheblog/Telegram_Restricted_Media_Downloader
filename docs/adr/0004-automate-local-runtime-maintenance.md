# ADR-0004: 自动本地运行时维护

**决策日期**: 2025-06 | **最后更新**: 2026-07-07 | **状态**: ✅ 已采纳

---

## Context

长期运行的 WebUI 部署会产生：

- 日志文件：每日轮转但旧文件无自动清理机制，磁盘占用持续增长
- SQLite 数据库：频繁写入后产生碎片，查询性能下降；WAL 文件可能膨胀
- 之前依赖运维人员手动维护，不适合无人值守的长期部署

## Decision

自动化以下维护任务：

**日志维护**：
- 使用 `TimedRotatingFileHandler` 按日轮转
- 启动时清理超过 3 天的旧日志文件 (`cleanup_old_log_files()`)
- 默认保留 3 天日志备份

**SQLite 维护** (`TransferStore.maintain()`)：
- 连接时执行 `PRAGMA journal_mode=WAL` 和性能相关 pragma
- 定期 WAL checkpoint（避免 WAL 文件无限增长）
- 定期 `PRAGMA optimize`（更新查询计划统计）
- 空闲页超过阈值（512 页）时执行 `VACUUM`（回收磁盘空间）
- 维护间隔最小 6 小时，避免频繁 VACUUM 影响性能

## Consequences

- ✅ 长期运行无需手动维护
- ✅ 磁盘空间自动回收
- ✅ SQLite 性能保持稳定
- ⚠️ VACUUM 期间数据库锁定，可能短暂阻塞写入
- ⚠️ 不删除持久化的 Transfer Tasks / Items / Events / Watch 数据
