# ADR-0005: 统一 WebUI ViewModel 数据契约

**决策日期**: 2026-07-07 | **状态**: ✅ 已采纳

---

## Context

WebUI 桌面端和移动端长期分别维护数据映射与状态字段：

- 桌面端读取 `completed_items`，移动端读取 `success_count`
- 任务详情、任务 summary、设置选项在不同前端各自猜测 payload 结构
- 移动端有独立 `mobile_shared.js`，与桌面端 `shared.js` 重复维护 API、状态、格式化和动作逻辑
- 修改任务统计或设置结构时，需要同步改多个前端文件，容易出现桌面/移动显示不一致

项目策略是正确性优先，不保留旧接口兼容层；因此不再继续支持旧的移动端字段名和旧设置路径。

## Decision

引入 `WebUiViewModel` 作为 WebUI 后端唯一公共输出契约：

- `/api/tasks` 返回统一 task model
- `/api/tasks/<id>` 返回 `{task, summary, items, events, page}`
- `/api/tasks/<id>/summary` 返回 `{task, summary, recent_events, page}`
- `/api/settings` 返回 `{settings, schema, settings_model}`
- 任务统计字段统一为 `completed_items`, `failed_items`, `skipped_items`, `progress_percent` 等 canonical 字段
- 设置选项统一由 `settings_model.options` 提供，设置选择统一由 `settings_model.selections` 表达
- 删除 `mobile_shared.js`，桌面端与移动端共同使用 `shared.js`
- WebUI operations 改为按能力调用对应方法，不再要求注入对象名义继承完整 Protocol

## Migration

无迁移，直接替换。

旧字段和旧路径不再作为公开契约：

- `success_count`
- `failed_count`
- `skipped_count`
- `global.download.types`
- `global.forward.types`
- `settings.downloadTypes || ...`

## Consequences

- ✅ 桌面端与移动端共享同一后端 ViewModel，字段含义一致
- ✅ 前端分页过滤由后端 `item_status` 支持，避免移动端/桌面端各自筛选导致总数不一致
- ✅ 设置页选项来源统一，后续新增类型只需改 schema/ViewModel
- ✅ 删除重复移动共享脚本，减少同步维护点
- ✅ 测试锁定旧字段不会重新进入生成资产
- ⚠️ 依赖旧移动字段的外部脚本需要改为新契约
