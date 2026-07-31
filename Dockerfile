FROM python:3.13.14-slim

ARG RCLONE_VERSION=1.74.4

# 设置工作目录。
WORKDIR /app

# 设置环境变量。
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    XDG_CONFIG_HOME=/app \
    TERM=xterm-256color

# 安装系统依赖+固定版 rclone+Python 依赖，编译后清理，合并为一个 RUN 层以减小镜像体积。
# requirements.txt 由 uv.lock 导出（uv export --no-dev --no-emit-project --frozen），勿手改。
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libmediainfo0v5 \
        unzip \
        gcc \
        g++ \
    && arch="$(dpkg --print-architecture)" \
    && case "$arch" in \
         amd64) rclone_arch=amd64 ;; \
         arm64) rclone_arch=arm64 ;; \
         *) echo "unsupported arch: $arch" >&2; exit 1 ;; \
       esac \
    && rclone_zip="rclone-v${RCLONE_VERSION}-linux-${rclone_arch}.zip" \
    && rclone_dir="rclone-v${RCLONE_VERSION}-linux-${rclone_arch}" \
    && curl -fsSL "https://github.com/rclone/rclone/releases/download/v${RCLONE_VERSION}/${rclone_zip}" \
         -o /tmp/rclone.zip \
    && curl -fsSL "https://github.com/rclone/rclone/releases/download/v${RCLONE_VERSION}/SHA256SUMS" \
         -o /tmp/rclone.sha256sums \
    && expected="$(awk -v f="${rclone_zip}" '$2 == f { print $1; exit }' /tmp/rclone.sha256sums)" \
    && test -n "$expected" \
    && echo "${expected}  /tmp/rclone.zip" | sha256sum -c - \
    && unzip -j /tmp/rclone.zip "${rclone_dir}/rclone" -d /usr/local/bin \
    && chmod +x /usr/local/bin/rclone \
    && rm -f /tmp/rclone.zip /tmp/rclone.sha256sums \
    && rclone help backends | grep -E '(^|[[:space:]])pikpak([[:space:]]|$)' \
    && pip install --no-cache-dir --require-hashes -r requirements.txt \
    && apt-get purge -y gcc g++ \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
# 创建配置目录、下载目录、会话目录、临时目录、统计表目录、rclone配置目录。
RUN mkdir -p /app/TRMD /app/downloads /app/sessions /app/temp /app/form /app/rclone

# 复制项目文件。
COPY main.py .
COPY module/ ./module/
COPY scripts/ ./scripts/

# 设置挂载点。
VOLUME ["/app/TRMD", "/app/downloads", "/app/sessions", "/app/temp", "/app/form", "/app/rclone"]

# 运行应用。
# --config: 用户配置存到挂载目录，容器重启不丢失。
# session_directory和temp_directory可在config.yaml中自行配置。
CMD ["python", "main.py", "--config", "/app/TRMD/config.yaml"]
