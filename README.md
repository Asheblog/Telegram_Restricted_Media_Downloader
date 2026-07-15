# Telegram Restricted Media Downloader WebUI Fork

面向**长期运行**的 Telegram 媒体转存工具：用 WebUI 管理批量转存、实时监听和任务恢复，默认转存到 PikPak bot，并可用 rclone 按**来源频道 / 帖子**自动归档。

请只用于你有权访问、保存和转存的内容。使用者需要自行承担使用行为及其后果。

## 本 Fork 做什么

继承上游 [Gentlesprite/TRMD](https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader) 的受限内容下载→上传链路，在此基础上把**运维和任务管理**搬到 WebUI，并补齐一批频道搬运场景里常见、但多数同类项目没做好的能力：

| 能力 | 说明 |
| --- | --- |
| **深链取片** | 频道帖只有 `t.me/<bot>?start=...` 按钮、正片在资源 bot 私聊里时，用已登录账号 `startBot` 取回媒体再转存；支持评论区深链、连发收齐、白名单与超时控制 |
| **WebUI 任务中心** | 转存 / 监听、进度与失败原因、暂停继续、重试、监听历史与导出导入；浏览器完成 API / 登录 / rclone 初始化 |
| **PikPak 归档** | 转存到 PikPak 后，rclone 按 `Telegram/频道名/帖子路径` 整理，评论区与深链内容仍归属原帖 |
| **TG Bot 辅助** | `/download`、`/forward`、`/listen_*` 等命令仍可用，适合临时操作；长期任务推荐 WebUI |

## 与同类项目怎么选

| 项目 | 更适合 | 优势 | 局限 |
| --- | --- | --- | --- |
| **本 Fork** | PikPak 长期归档、资源 bot 深链频道、需要 WebUI 管任务 | 深链取片 + 评论区、按帖归档、监听可恢复、失败可观测 | 部署比纯 Bot 重；存储侧偏 PikPak / rclone，不如多后端工具灵活 |
| [Gentlesprite 上游](https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader) | 轻量 CLI / Bot、熟悉原版工作流 | 成熟、断点续传、命令齐全 | 无 WebUI；初始化多依赖 TTY / `docker exec` |
| [SaveAny-Bot](https://github.com/krau/saveany-bot) | 多存储（Alist / S3 / WebDAV 等）统一搬运 | 后端生态广、监听与规则丰富 | AGPL；工作流与 PikPak 按帖归档不同；无资源 bot 深链取片 |
| [TeleFlow](https://github.com/AvishkarPatil/TeleFlow) 等链接 Bot | 偶尔单条 / 小批量取片 | 上手快、双客户端架构清晰 | 缺长期任务、监听历史、深链与按帖归档 |
| [telegram-media-downloader](https://github.com/botnick/telegram-media-downloader) | 本地媒体库与图库浏览 | PWA 图库、监控与去重很强 | 重心在本地下载库，不是 PikPak 转存流水线 |

若你的来源帖**只有深链按钮、没有可直接转发的正片**，或需要**评论区才能拿到资源**，本 Fork 的深链取片通常是更省心的选择。

## 快速开始

准备好这些东西：

- 一台能运行 Docker / Docker Compose 的机器。
- Telegram `api_id` 和 `api_hash`：到 `https://my.telegram.org/auth` 登录后，在 `API development tools` 创建应用获取。
- 一个可登录的 Telegram 账号，用来读取来源频道并发送给 PikPak bot。
- 一个 PikPak 账号，用来给 rclone 配置 PikPak remote。

推荐部署目录为 `/opt/trmd`。Windows + Docker Desktop 也可以使用同一份 Compose，只需要把左侧宿主机挂载路径改成 Windows 路径，例如 `D:/trmd/config:/app/TRMD`。

## 1. 创建 docker-compose.yml

```yaml
services:
  trmd:
    image: ghcr.io/asheblog/telegram_restricted_media_downloader:latest
    container_name: trmd
    restart: unless-stopped
    stdin_open: true
    tty: true
    ports:
      - "2921:2921"
    volumes:
      - /opt/trmd/config:/app/TRMD
      - /opt/trmd/sessions:/app/sessions
      - /opt/trmd/downloads:/app/downloads
      - /opt/trmd/temp:/app/temp
      - /opt/trmd/form:/app/form
      - /opt/trmd/rclone:/app/rclone
    environment:
      - TZ=Asia/Singapore
      - RCLONE_CONFIG=/app/rclone/rclone.conf
      - TRMD_WEB_HOST=0.0.0.0
      - TRMD_WEB_USERNAME=admin
      - TRMD_WEB_PASSWORD=replace-with-a-strong-password
    command:
      - python
      - main.py
      - --config
      - /app/TRMD/config.yaml
      - --web
      - "2921"
      - --mode
      - SESSION
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"
```

把 `TRMD_WEB_PASSWORD` 改成强密码，然后启动：

```bash
docker compose up -d
docker logs -f trmd
```

打开 WebUI：

```text
http://服务器IP:2921
```

登录账号密码就是 Compose 里的：

```text
admin / replace-with-a-strong-password
```

如果 `TRMD_WEB_HOST=0.0.0.0`，必须设置 `TRMD_WEB_USERNAME` 和 `TRMD_WEB_PASSWORD`，否则程序会拒绝启动，避免 WebUI 无密码暴露。

## 2. 浏览器完成初始化（推荐）

启动容器并登录 WebUI 后，会进入**首次初始化向导**（桌面端与手机浏览器均可）：

1. 填写 Telegram `api_id` / `api_hash`（可选代理）
2. 在页面完成 Telegram 登录（手机号、验证码、二步验证）
3. 配置 PikPak rclone（可点「稍后再说」跳过；跳过后不会自动归档）

路径、媒体类型等会按 Docker 默认值自动生成，一般不必先手改配置文件。  
登录会话保存在 `/opt/trmd/sessions`，后续升级或重启请勿删除。

**已有部署升级**：只要原来的 `api_id`/`api_hash` 与 sessions 仍有效，不会强弹全屏向导。

若仍想手写 `config.yaml`，至少保证：

```yaml
api_id: "123456"
api_hash: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
save_directory: /app/downloads
session_directory: /app/sessions
temp_directory: /app/temp
```

PikPak 归档等全局项写在 `/opt/trmd/config/.CONFIG.yaml`（或 WebUI「系统设置」），不要写进 `config.yaml`。

也可以在「系统设置 → PikPak 归档」里随时「配置 / 更换 rclone」或「验证 remote」。

## 3. rclone 排障（可选）

正常情况用 WebUI 向导即可。若需命令行排查：

```bash
docker exec -it trmd rclone listremotes --config /app/rclone/rclone.conf
docker exec -it trmd rclone lsd pikpak: --config /app/rclone/rclone.conf
```

官方说明见 [rclone PikPak 文档](https://rclone.org/pikpak/)。

## 4. 开始使用

在 WebUI 里创建转存任务：

1. 来源链接填 Telegram 消息或频道链接。
2. 目标保持默认 `https://t.me/pikpak_bot`。
3. 目标配置选择 `PikPak 文档转存`。
4. 单条消息直接提交；频道范围任务填写起始 ID 和结束 ID。

### 深链取片

部分频道帖只有封面/`t.me/<bot>?start=...` 按钮（或评论区里才有深链），正片在资源 bot 私聊里。用法：

1. **系统设置 → 深链取片**：填写资源 bot 白名单（每行一个用户名，如 `123456`），可改超时、最小间隔、收齐静默秒数。
2. 新建转存或监听转发时勾选 **深链取片**（白名单为空时无法勾选创建）。若深链在评论区，再勾选 **包含评论区**。
3. 命中白名单深链时，会用已登录账号向该 bot 取 `video`/`document`/`animation`/`photo`（连发会按静默窗口收齐），再转存到目标；失败不会用频道预览顶替。

不勾选则行为与原来完全相同。

默认流程是：

```text
Telegram 来源消息 -> PikPak bot -> PikPak 的 My Telegram -> rclone 移动到 Telegram/来源频道
```

其中：

- `source_directory: My Telegram` 是 PikPak bot 入库后的默认目录。
- `root_directory: Telegram` 是最终归档根目录。
- 文件会按来源频道放到 `Telegram/来源频道`。
- 单个 PikPak 目标文件默认限制为 4 GiB，超过会提前失败。

## 常用命令

```bash
# 查看日志
docker logs -f trmd

# 重启
docker compose restart

# 升级镜像
docker compose pull
docker compose up -d

# 停止
docker compose down

# 备份关键数据
tar -C /opt/trmd -czf trmd-backup.tar.gz config sessions temp form rclone
```

Windows PowerShell 下备份可以直接复制部署目录，例如 `D:\trmd`。

## 目录说明

| 宿主机目录 | 容器目录 | 用途 |
| --- | --- | --- |
| `/opt/trmd/config` | `/app/TRMD` | `config.yaml` 用户配置 |
| `/opt/trmd/sessions` | `/app/sessions` | Telegram 登录会话 |
| `/opt/trmd/downloads` | `/app/downloads` | 下载后的媒体文件 |
| `/opt/trmd/temp` | `/app/temp` | 临时文件和 WebUI 任务状态 |
| `/opt/trmd/form` | `/app/form` | 统计表导出目录 |
| `/opt/trmd/rclone` | `/app/rclone` | rclone 配置，默认读取 `rclone.conf` |

保留 `config`、`sessions`、`temp`、`form`、`rclone` 这些目录，就能保留配置、登录状态、任务历史、统计表和 PikPak rclone 登录信息。

## 常见问题

**WebUI 打不开**

先看容器是否在运行：

```bash
docker ps
docker logs -f trmd
```

如果日志提示 WebUI 认证缺失，检查 `TRMD_WEB_USERNAME` 和 `TRMD_WEB_PASSWORD`。

**Telegram 登录失败或下载不动**

检查 `api_id`、`api_hash`、代理配置和账号是否能访问来源频道。遇到 FloodWait 时程序会等待后继续，不建议频繁重启。

**PikPak 已收到文件，但没有归档**

优先在 WebUI「系统设置 → PikPak 归档」点「验证 remote」。命令排障：

```bash
docker exec -it trmd rclone listremotes --config /app/rclone/rclone.conf
docker exec -it trmd rclone lsd pikpak: --config /app/rclone/rclone.conf
```

确认 remote 可用，且归档开关已打开（向导配置成功后会自动打开）。

**不想使用 PikPak 归档**

初始化时点「稍后再说」，或在设置里关闭「PikPak按来源频道归档」。仍可转存到 PikPak bot，只是不会用 rclone 移动文件。

## License

本项目继承上游 MIT License。上游作者为 [Gentlesprite](https://github.com/Gentlesprite)。
