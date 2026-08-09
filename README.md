# Telegram Restricted Media Downloader (WebUI Fork)

TRMD 是面向**长期运行**的 Telegram 受限媒体转存工具：WebUI 管理批量转存、实时监听与任务恢复，默认转存到 PikPak，并按来源频道 / 帖子自动归档。

> 请只用于你有权访问、保存和转存的内容。使用者需自行承担使用行为及其后果。

## 功能优势

- **WebUI 任务中心** —— 浏览器完成 Telegram 登录与 PikPak rclone 初始化；转存 / 监听任务的进度、暂停继续、失败重试、历史记录与导入导出全部可视化。
- **深链取片** —— 帖子只有 `t.me/<bot>?start=...` 按钮、正片在资源 bot 私聊，或资源藏在评论区时，自动用已登录账号取回媒体再转存。
- **断点续传** —— SQLite 持久化任务状态，进程重启、镜像升级后未完成任务自动续跑。
- **PikPak 按帖归档** —— rclone 将文件整理为 `Telegram/来源频道/帖子路径`，评论区与深链内容仍归属原帖。
- **TG Bot 辅助** —— `/download`、`/forward`、`/listen_*` 等命令仍可用，适合临时操作。
- **一键 Docker 部署** —— 单容器 Compose 启动，提供 linux/amd64 与 linux/arm64 镜像。

## 快速开始（Docker 部署）

准备：

1. 一台能运行 Docker / Docker Compose 的机器。
2. Telegram `api_id` / `api_hash`：登录 [my.telegram.org](https://my.telegram.org/auth) → `API development tools` 创建应用获取。
3. 一个可登录的 Telegram 账号（读取来源频道用）和一个 PikPak 账号。

推荐部署目录为 `/opt/trmd`。Windows + Docker Desktop 使用同一份 Compose，只需把挂载路径改为 Windows 路径（如 `D:/trmd/config:/app/TRMD`）。

**1. 创建 `docker-compose.yml`：**

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
      - TRMD_WEB_PASSWORD=replace-with-a-strong-password  # 改成强密码
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

> `TRMD_WEB_HOST=0.0.0.0` 时必须设置 `TRMD_WEB_USERNAME` 和 `TRMD_WEB_PASSWORD`，否则程序会拒绝启动，避免 WebUI 无密码暴露。

**2. 启动：**

```bash
docker compose up -d
```

**3. 浏览器完成初始化（推荐）：**

打开 `http://服务器IP:2921`，账号密码为 Compose 中设置的 `admin / 你的密码`。首次登录进入初始化向导，按页面提示依次：

1. 填写 Telegram `api_id` / `api_hash`（可选代理）。
2. 完成 Telegram 登录（手机号、验证码、二步验证；手机号用国际格式，如 `+86…`）。
3. 配置 PikPak rclone（不可跳过，下载回退依赖它）。

登录会话保存在 `/opt/trmd/sessions`，升级或重启请勿删除。已有部署升级时，只要 `api_id` / `api_hash` 与 sessions 仍有效，不会强弹向导。

## 开始使用

在 WebUI 创建转存任务：

1. 来源链接填 Telegram 消息或频道链接。
2. 目标保持默认 `https://t.me/pikpak_bot`，目标配置选 `PikPak 文档转存`。
3. 单条消息直接提交；频道范围任务填写起始 / 结束 ID。

默认流程：

```text
Telegram 来源消息 -> PikPak bot -> PikPak 的 My Telegram -> rclone 移动到 Telegram/来源频道
```

**深链取片**：先在「系统设置 → 深链取片」配置资源 bot 白名单，新建转存 / 监听任务时勾选「深链取片」（资源在评论区则再勾选「包含评论区」）即可。

## 常用命令

```bash
docker logs -f trmd                                     # 查看日志
docker compose restart                                  # 重启
docker compose pull && docker compose up -d             # 升级镜像
docker compose down                                     # 停止
```

备份：保留 `config`、`sessions`、`temp`、`form`、`rclone` 目录即可完整保留配置、登录态、任务历史、统计表与 PikPak rclone 登录信息：

```bash
tar -C /opt/trmd -czf trmd-backup.tar.gz config sessions temp form rclone
```

## 常见问题

**WebUI 打不开**：先 `docker ps` 和 `docker logs -f trmd` 查看容器状态；若提示认证缺失，检查 `TRMD_WEB_USERNAME` / `TRMD_WEB_PASSWORD`。

**Telegram 登录失败或下载不动**：检查 `api_id`、`api_hash`、代理与账号权限；遇到 FloodWait 时程序会等待后继续，不建议频繁重启。

**PikPak 已收到文件但未归档**：在「系统设置 → PikPak 归档」点「验证 remote」，确认 rclone 可用且归档开关已打开。

排障时可从「系统设置 → 诊断包导出」下载 ZIP（含日志与失败项实测结果）。注意该包**含登录态与密钥**，请仅私密传输，勿公开分享。

## License

本项目继承上游 [Gentlesprite/Telegram_Restricted_Media_Downloader](https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader) 的 MIT License。
