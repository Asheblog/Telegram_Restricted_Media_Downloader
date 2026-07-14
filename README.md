# Telegram Restricted Media Downloader WebUI Fork

这是一个面向长期运行的 Telegram 媒体转存 WebUI。它可以把你有权访问的 Telegram 内容转存到目标会话，默认目标是 PikPak bot，并可通过 rclone 把 PikPak 入库后的文件按来源频道归档。

请只用于你有权访问、保存和转存的内容。使用者需要自行承担使用行为及其后果。

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
