# ADR-0012: WebUI 首启配置向导

`--web` 模式下，把原先依赖 TTY/`docker exec` 的初始化（`api_id`/`api_hash`、Telegram 登录、rclone PikPak、可选 Bot Token）收成 WebUI 内多步向导；站内登录仍先于向导（ADR-0003）。已具备有效 API 凭证与 Telegram Session 的升级环境按真实状态判定就绪，不弹全屏向导。**新装引导必须配通 rclone**（探测成功后开启归档）：下载回退不再经 `pikpak_bot`，改为 rclone 直传到 `My Telegram` 再复用归档。rclone 之后引导可选配置 Bot Token（`getMe` 校验或跳过）。CLI 无 `--web` 时仍走原 stdin `config_guide`。

**Considered Options**

- 仅补 rclone、不改启动序：空配置仍卡在 `config_guide` stdin，WebUI 起不来。
- 允许跳过 rclone：PikPak 下载回退入库失败，首启体验残缺。
- 交互式嵌伪终端跑 `rclone config`：退回 ttyd 体验，状态难控。
- 首启不提 Bot Token：用户易误以为「Telegram」步已覆盖机器人；CLI 旧引导有可选机器人提问。

**Consequences**

- `--web` 缺关键字段时不得阻塞 stdin；先起 HTTP，再懒建 Client。
- 业务 API 在「API 已配 + Telegram 已授权」前统一拒绝（`setup_required`）；setup/auth/settings 例外。
- 新装向导在 Telegram 登录后进入 rclone 步，不可「稍后再说」；升级已就绪环境不强制补配。
- rclone 凭据经 `rclone config create` + `obscure` 写入 `$RCLONE_CONFIG`，不由应用手写 INI。
- 新装 rclone 完成后进入可选 Bot Token 步：保存时 `getMe` 校验；网络失败与无效 token 区分提示；可跳过，稍后在设置页配置。已有合法 `bot_token` 则自动跳过。
- 桌面与移动端共用同一 setup 状态契约（ADR-0005）。
