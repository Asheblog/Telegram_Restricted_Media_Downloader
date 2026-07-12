# Deep link resolve before transfer

部分频道帖只含资源 bot 的 `t.me/<bot>?start=` 深链而非可直接转发的媒体。我们选择：任务/监听勾选 `resolve_deep_link` 且全局白名单非空时，用**用户会话**（`messages.startBot`）向白名单 bot 取回 `video`/`document`/`animation`，再对取回消息走既有转发→下载上传链路；命中白名单深链时以 bot 回传为准，**不回退**频道预览；取片失败即失败。全局 `deep_link.bot_whitelist` 限定可解析 bot；**串行**取片，默认超时 60s（可配），默认最小间隔 30s（可配）；`FloodWait` 仅在剩余超时预算内等待后重试，预算不足或拉历史挂起则立即失败并释放串行锁，避免整队卡死。PikPak 归档与 Transfer Item 来源仍归属**原频道帖**。

**Considered Options:** Bot API 代点 start（无用户私聊上下文）；并行多 bot 取片；取片失败回退频道媒体/预览；自动加频道或点验证按钮；FloodWait 必须等满 Telegram 秒数再失败（否决：长限流会占死串行锁）。

**Consequences:** 需维护白名单、超时与最小间隔配置；勾选但白名单空时创建任务/监听应拒绝；bot 私聊消息不自动清理；监听转发与转存任务共用同一规则；长 `FloodWait` 会令当前项快速失败而非无限阻塞后续取片。
