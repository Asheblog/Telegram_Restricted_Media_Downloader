# Unified media type allowlist

媒体类型曾分散在 `download_type`、`forward_type`、`message_filter.media_types`，且 Web 转存用 `ignore_type_filter` 绕过过滤，导致系统设置与执行不一致。我们选择以全局 `message_filter.media_types` 为唯一真源；`forward_type` / `download_type` 仅双写兼容。消息过滤总开关只控制日期与关键词，媒体类型始终生效。转存任务、实时监听与 Bot 频道下载会话可存可选覆盖（`NULL`/未设置=继承全局，设置后整表替换）；深链取回内容同样按生效白名单过滤，未放行记 skipped 而非 failure。

**Considered Options:** 继续多套独立勾选；仅统一全局、不做任务级；任务级用差量（并集/差集）而非整表替换。

**Consequences:** UI 只保留一组全局媒体类型勾选；创建/编辑任务与监听可弹框覆盖；Bot 会话默认继承全局、按钮可覆盖；所有下载/转发链路（含深链）走同一解析函数。
