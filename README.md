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

## 2. 配置 Telegram

首次启动后会生成 `/opt/trmd/config/config.yaml`。编辑这个文件，至少填好下面几项：

```yaml
api_id: "123456"
api_hash: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
bot_token: null
download_type:
  - video
  - photo
  - document
  - audio
  - voice
  - animation
  - video_note
is_shutdown: false
max_tasks:
  download: 1
  upload: 3
max_retries:
  download: 5
  upload: 3
save_directory: /app/downloads
session_directory: /app/sessions
temp_directory: /app/temp
proxy:
  enable_proxy: false
  hostname: null
  scheme: null
  port: null
  username: null
  password: null
target_profiles:
  pikpak:
    max_file_size: 4294967296
    archive:
      enable: true
      remote: pikpak
      source_directory: My Telegram
      root_directory: Telegram
      poll_seconds: 60
      poll_interval_seconds: 5
      match_window_seconds: 3600
```

保存后重启：

```bash
docker compose restart
docker logs -f trmd
```

第一次登录 Telegram 时，按日志提示输入手机号、验证码和二步验证密码。登录会话会保存在 `/opt/trmd/sessions`，后续升级或重启不要删除这个目录。

如果你的服务器访问 Telegram 需要代理，把 `proxy.enable_proxy` 改为 `true`，并填写代理地址、协议和端口。

## 3. 配置 rclone PikPak

本项目的 PikPak 归档依赖 rclone。镜像里已经安装 rclone，你只需要生成 `/opt/trmd/rclone/rclone.conf`。

如果容器正在运行，执行：

```bash
docker exec -it trmd rclone config --config /app/rclone/rclone.conf
```

如果容器还没跑起来，也可以用一次性容器配置：

```bash
docker run --rm -it \
  -v /opt/trmd/rclone:/app/rclone \
  ghcr.io/asheblog/telegram_restricted_media_downloader:latest \
  rclone config --config /app/rclone/rclone.conf
```

按交互提示填写：

```text
n) New remote
name> pikpak
Storage> pikpak
user> 你的 PikPak 登录邮箱或手机号
y/g> y
password> 你的 PikPak 密码
Edit advanced config?> n
Keep this "pikpak" remote?> y
```

重点是 remote 名称必须叫 `pikpak`，因为默认配置里写的是：

```yaml
target_profiles:
  pikpak:
    archive:
      remote: pikpak
```

验证 rclone 能访问 PikPak：

```bash
docker exec -it trmd rclone lsd pikpak: --config /app/rclone/rclone.conf
```

能列出目录就表示配置成功。rclone 官方 PikPak 后端说明见 [rclone PikPak 文档](https://rclone.org/pikpak/)。

## 4. 开始使用

在 WebUI 里创建转存任务：

1. 来源链接填 Telegram 消息或频道链接。
2. 目标保持默认 `https://t.me/pikpak_bot`。
3. 目标配置选择 `PikPak 文档转存`。
4. 单条消息直接提交；频道范围任务填写起始 ID 和结束 ID。

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

依次检查：

```bash
docker exec -it trmd rclone listremotes --config /app/rclone/rclone.conf
docker exec -it trmd rclone lsd pikpak: --config /app/rclone/rclone.conf
```

确认存在名为 `pikpak` 的 remote，并且 `target_profiles.pikpak.archive.enable` 是 `true`。

**不想使用 PikPak 归档**

把配置改成：

```yaml
target_profiles:
  pikpak:
    archive:
      enable: false
```

这样仍可转存到 PikPak bot，但不会调用 rclone 移动文件。

## License

本项目继承上游 MIT License。上游作者为 [Gentlesprite](https://github.com/Gentlesprite)。
