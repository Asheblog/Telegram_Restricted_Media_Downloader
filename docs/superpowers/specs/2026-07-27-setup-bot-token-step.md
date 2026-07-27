# Spec: 首启向导可选 Bot Token 步骤

## Goal

WebUI First-run Setup Wizard 在 rclone 之后增加一步可选的 Bot Token 指引：可「保存并验证」或「跳过」；已配置 token 则自动跳过。

## Requirements

1. **步骤顺序**：API → Telegram 登录 → rclone（必选）→ Bot Token（可选）→ 完成。文案为步骤 1–4 / 4。
2. **硬门槛可跳过**：guided 新装在 rclone 完成后须保存并验证或跳过才结束向导；已有格式合法的 `bot_token` 自动跳过本步。
3. **保存校验**：格式检查（含 `:`）后调用 Telegram Bot API `getMe`；成功才写入 `user.bot_token`。
4. **错误区分**：
   - token 无效 → 错误提示，不可假装成功，可改 token 或跳过
   - 网络失败 → 明确提示可跳过稍后再配；不提供强制保存不验证
5. **代理**：若已配 HTTP(S) 代理则走代理；无代理或 socks 不可用时直连，失败走网络错误路径。
6. **API**：`POST /api/setup/bot`、`POST /api/setup/bot/skip`；`GET /api/setup/status` 的 `steps.bot` 与 `current_step: bot`。
7. **ready 不变**：业务 API 仍只要求 `api_done ∧ telegram_done`。
8. **桌面 + 移动**共用 status 契约；改源文件后 `build_frontend.py` 重生 `assets.py`。
9. **文档**：更新 ADR-0012、CONTEXT.md、CONTEXT-MAP.md。

## Out of scope

- Bot 必填、强制保存不验证、本步配代理、CLI `config_guide`、Bot 进程热启改造

## Seams under test

1. `SetupCoordinator.build_status` — bot 步状态机
2. `verify_bot_token` — invalid vs network（injectable fetch）
3. WebUI assets — 含 `#setup-form-bot` 与 `/api/setup/bot`
