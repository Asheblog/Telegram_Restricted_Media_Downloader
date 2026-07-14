# Deep link resolve before transfer

部分频道帖只含资源 bot 的 `t.me/<bot>?start=` 深链而非可直接转发的媒体。我们选择：任务/监听勾选 `resolve_deep_link` 且全局白名单非空时，用**用户会话**（`messages.startBot`）向白名单 bot 取回 `video`/`document`/`animation`/`photo`，再对取回消息走既有转发→下载上传链路；命中白名单深链时以 bot 回传为准，**不回退**频道预览；取片失败即失败。全局 `deep_link.bot_whitelist` 限定可解析 bot；**串行**取片，默认超时 60s（可配），默认最小间隔 30s（可配），默认收齐静默 3s（可配）：首条媒体后继续收集直到静默窗口或超时，以覆盖资源 bot 连发多文件。PikPak 归档与 Transfer Item 来源仍归属**原频道帖**的 Source Post Archive Path（见 ADR-0011），不改成 bot 会话文件夹。

评论区深链：同时开启 Discussion Reply Inclusion 时，讨论回复（含延迟抓取）**仅**处理含白名单深链的评论并 resolve；不附带按 `forward_type`/`check_type` 转存其它闲聊或媒体。未开深链时评论区仍按原 `check_type` 过滤。监听转发与 Web 转存共用此规则。主贴无深链时不会在主贴瞬间主动嗅探评论（依赖「包含评论区」+ 延迟抓取，避免竞态）。

**Considered Options:** Bot API 代点 start（无用户私聊上下文）；并行多 bot 取片；取片失败回退频道媒体/预览；自动加频道/讨论群或点验证按钮；FloodWait 必须等满 Telegram 秒数再失败（否决：长限流会占死串行锁）；主贴无链时自动硬扫评论区（否决：与延迟抓取竞态）。

**Consequences:** 需维护白名单、超时、最小间隔与收齐静默配置；勾选但白名单空时创建任务/监听应拒绝；bot 私聊消息不自动清理；评论区资源需双开「包含评论区」+「深链取片」；长 `FloodWait` 会令当前项快速失败而非无限阻塞后续取片。
