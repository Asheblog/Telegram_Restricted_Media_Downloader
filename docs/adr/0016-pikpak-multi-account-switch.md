# 0016 — 支持绑定多个 PikPak 账号并切换（rclone remote 切换）

## 背景

此前 PikPak 归档/入库只支持单个账号：`target_profiles.pikpak.archive.remote` 保存一个 rclone remote 名，`RclonePikPakArchiveClient` 与 `SetupCoordinator.configure_pikpak_remote` 都只围绕这一单个 remote 工作。用户需要绑定多个 PikPak 账号（一个账号 = 一个 rclone remote），可在任意账号间切换（含切回原账号），上限 5 个。

## 决策

- **一个账号 = 一个 rclone remote**：rclone 原生支持在同一个 `rclone.conf` 里定义多个 remote，无需自建凭据存储。账号凭据仅经 `rclone config create` + `obscure` 写入 rclone.conf；应用配置只持久化 remote 名列表，绝不落密码。
- **数据模型**：`target_profiles.pikpak.accounts` 存 `list[{"remote": str}]`（上限 `PIKPAK_MAX_ACCOUNTS = 5`）；`target_profiles.pikpak.archive.remote` 仍为「当前激活账号」指针。切换账号 = 改写该指针 + 失效 `PikpakIntegrationManager` 缓存的 archive client（下次 `get_pikpak_archive_client()` 用新 remote 懒重建）。
- **自动命名**：首个 remote 名 `pikpak`，其后 `pikpak2`…`pikpak5`，自动跳过与已有 remote/已绑定账号冲突的名称；不提供用户自定义标签（减少输入与重名校验面）。
- **目录配置共享**：所有账号共用同一套 `source_directory` / `root_directory` 及轮询参数；切换只改 `remote`，不做 per-account 目录配置。
- **删除约束**：仅允许删除非激活账号；激活账号须先切换。删除时若 remote 仍存在于 rclone.conf 则执行 `rclone config delete <remote>`；若已缺失（账号标记 `missing`）则仅从应用配置移除，避免残留凭据或误报。
- **切换语义**：切换只改写 `archive.remote` 指针并失效缓存，**不**强制翻转 `archive.enable`（保持用户对归档开关的既有选择）。切换前校验 remote 仍存在于 rclone.conf，缺失则拒绝并提示重配。**添加账号同理只重定向指针、不翻转 `archive.enable`。**
- **失败语义（2026-08-13 修订）**：账号上限（5）在创建 rclone remote / 写配置 **之前** 校验，被拒请求不得留下孤儿 remote、凭据或翻转的归档开关；rclone 不可读（非空 remote 列表）与「remote 真正缺失」必须区分——不可读时拒绝切换/删除，避免把故障误判为缺失而静默丢绑定、残留凭据。

## API

| 路由 | 方法 | 作用 |
|------|------|------|
| `/api/setup/rclone/accounts` | GET | 列出绑定账号（remote / active / missing）与 `listremotes` 原始结果 |
| `/api/setup/rclone/account` | POST | 添加账号（username/password，自动命名；探测成功后设为激活） |
| `/api/setup/rclone/switch` | POST | 切换到指定 remote（须已绑定） |
| `/api/setup/rclone/account/remove` | POST | 删除非激活账号 |

`configure_setup_rclone`（首次/更换 rclone 向导）成功后也会把该 remote 注册进 `accounts`，保持「配置/更换 rclone」路径与多账号列表一致。

## Considered Options

- 自定义账号标签（如 `pikpak-工作号`）：展示更友好，但多输入框与重名校验，非本次最小诉求，弃用。
- per-account 目录配置：更灵活，但需把 `archive` 拆成 per-account 结构，改动面大，弃用。
- 自建凭据表 + 动态生成 remote：冗余且违背 rclone 原生能力，弃用。

## Consequences

- 升级安全：`accounts` 默认 `[]`，`process_target_profiles` 会为旧配置补齐该键（已写入 `DEFAULT_TARGET_PROFILES` 模板）。
- 切换后归档/入库立即生效：manager 的 archive client 缓存被失效，下次访问按新 remote 重建；实时归档共享同一缓存实例，故切换不影响并发归档的串行锁语义（锁在实例上）。
- 前端桌面与移动设置页共用一套账号列表渲染与操作（`shared.js` 共享函数），`assets.py` 由 `build_frontend.py` 重建。
- 删除/切换不影响共享的归档目录参数；仅影响 remote 指向。
