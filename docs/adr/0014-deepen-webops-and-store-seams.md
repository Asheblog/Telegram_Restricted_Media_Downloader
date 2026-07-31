# ADR 0014 — 深化 WebOps / TransferStore / WebUI Server seams

## Status

Accepted

## Context

Phase 0–3 已完成目录迁移与 Protocol 引入。此前 `CONTEXT.md` 曾暂停大规模搬包。仓库中仍存在厨房水槽：`WebOperationsMixin`、`TransferStore`、`WebUiServer`、Downloader 门面残留实现。行数最大的 `assets.py` 为生成物，不作为解耦信号。

## Decision

执行一轮「深模块」深化（非纯搬包、非行数硬顶）——P1–P4 已落地：

1. 从 `WebOperationsMixin` 抽出 `ArchiveAuthorOps`；Web 任务 pause/resume/delete/submit/retry 委托 `WebUITaskManager`。
2. `TransferStore` 按聚合拆为 `persistence/store/*` mixins（task/item/watch/deferred/archive_jobs/maintenance 等），对外门面签名保持。
3. `WebUiServer` 按 API 域拆到 `adapters/webui/handlers/*`；HTTP 契约不变。
4. Downloader / Bot 门面以委托既有服务为主（`LiveTransferService` / `TransferEngine` / `WebTransferRunner` / PikPak）；`composition_root` 为唯一装配根。残留下载编排与 Bot UX 胶水不强制再拆。

拒绝：以单文件行数上限为完成标准；仅为搬家而搬家；改 REST/SQLite 语义。

## Consequences

- 可维护性与 AI 导航性提升；回归依赖既有 unit_tests。
- 顶层 shim / 公开方法签名尽量兼容。
- `CONTEXT.md` 架构立场与 `CONTEXT-MAP.md` 已按本轮结果更新。
