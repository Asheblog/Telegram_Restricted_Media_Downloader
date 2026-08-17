# coding=UTF-8
"""Pure constants and side-effect-free singletons.

Importing this module must not perform any I/O, create directories, open file
handles, or start threads. All runtime side effects live in
``module.bootstrap.initialize()``.
"""

import logging
import os
import platform

import yaml
from pyrogram.types.messages_and_media import LinkPreviewOptions
from rich.console import Console

LOG_TIME_FORMAT = "[%Y-%m-%d %H:%M:%S]"
console = Console(log_path=False, log_time_format=LOG_TIME_FORMAT)

SLEEP_THRESHOLD = 60
AUTHOR = "Gentlesprite"
__version__ = "0.2.243"
__license__ = "MIT License"
__update_date__ = "2026/08/12 20:24:00"
__copyright__ = f"Copyright (C) 2024-{__update_date__[:4]} {AUTHOR} <https://github.com/Gentlesprite>"
SOFTWARE_FULL_NAME = "Telegram Restricted Media Downloader"
SOFTWARE_SHORT_NAME = "TRMD"

APPDATA_PATH = os.path.join(
    os.environ.get("APPDATA")
    or os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    SOFTWARE_SHORT_NAME,
)
GLOBAL_CONFIG_NAME = ".CONFIG.yaml"
GLOBAL_CONFIG_PATH = os.path.join(APPDATA_PATH, GLOBAL_CONFIG_NAME)
PLATFORM = platform.system()

INPUT_HISTORY_PATH = os.path.join(APPDATA_PATH, f".{SOFTWARE_SHORT_NAME}_HISTORY")
MAX_RECORD_LENGTH = 1000

LOG_PATH = os.path.join(APPDATA_PATH, f"{SOFTWARE_SHORT_NAME}_LOG.log")
LOG_RETENTION_DAYS = 3
LOG_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60

LINK_PREVIEW_OPTIONS = LinkPreviewOptions(is_disabled=True)
LOG_FORMAT = "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
FILE_LOG_LEVEL: int = logging.INFO
CONSOLE_LOG_LEVEL: int = logging.WARNING

log = logging.getLogger("rich")


class CustomDumper(yaml.Dumper):
    """Custom YAML dumper that renders ``None`` as ``~``."""

    def represent_none(self, data):
        return self.represent_scalar("tag:yaml.org,2002:null", "~")


README = r"""
```yaml
api_hash: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx # 申请的api_hash。
api_id: 'xxxxxxxx' # 申请的api_id。
# bot_token（选填）如果不填，就不能使用机器人功能。可前往https://t.me/BotFather免费申请。
bot_token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
download_type: # 需要下载的类型。支持的参数:video,photo,document,audio,voice,animation。
- video # 视频。
- photo # 图片。
- document # 文档。
- audio # 音频。
- voice # 语音。
- animation # GIF。
- video_note # 视频笔记。
is_shutdown: true # 下载完成后是否自动关机。支持的参数：true,false。
links: D:\path\where\your\link\files\save\content.txt # 链接地址写法如下:
# 新建txt文本，一个链接为一行，将路径填入即可请不要加引号，在软件运行前就准备好。
# D:\path\where\your\link\txt\save\content.txt 一个链接一行。
max_retries:
  download: 5 # 最大的下载任务的重试次数。
  upload: 3 # 最大的上传任务的重试次数。
max_tasks:
  download: 1 # 最大同时下载的任务数。
  upload: 1 # 最大同时上传的任务数。
target_profiles:
  pikpak:
    max_file_size: 4294967296 # PikPak目标允许的最大文件大小,默认4GiB。
    archive:
      enable: true # 是否使用rclone将PikPak入库后的文件按来源频道归档。
      remote: pikpak # rclone中的PikPak remote名称。
      source_directory: My Telegram # PikPak 入库落点（bot 转发或 rclone copyto）；归档前暂存于此。
      root_directory: Telegram # PikPak归档根目录。
      poll_seconds: 180 # 每次归档尝试在My Telegram中轮询匹配的最长秒数。
      poll_interval_seconds: 5 # 轮询间隔秒数。
      match_window_seconds: 3600 # 按时间匹配入库文件的窗口秒数（窗口内失败会自动重试）。
      poll_cap_seconds: 1800 # 大文件入库轮询上限秒数。
      archive_delay_seconds: 600 # 上传完成后延迟多久再执行首次PikPak归档（秒）。
      archive_retry_interval_seconds: 300 # 归档失败后再次尝试的间隔秒数（在匹配窗口内有效）。
proxy: # 代理部分，如不使用请全部填null注意冒号后面有空格，否则不生效导致报错。
  enable_proxy: true # 是否开启代理。支持的参数：true,false。
  hostname: 127.0.0.1 # 代理的ip地址。
  scheme: socks5 # 代理的类型。支持的参数：http,socks4,socks5。
  port: 10808 # 代理ip的端口。支持的参数：0~65535。
  username: null # 代理的账号，没有就填null。
  password: null # 代理的密码，没有就填null。
save_directory: F:\directory\media\where\you\save # 下载的媒体保存的目录（支持通配符）。
session_directory: F:\directory\session\where\you\save # 会话的保存目录（支持通配符）。
temp_directory: F:\directory\temp\where\you\save # 缓存保存的目录（支持通配符）。
```
"""

__all__ = [
    "console",
    "log",
    "SLEEP_THRESHOLD",
    "AUTHOR",
    "__version__",
    "__license__",
    "__update_date__",
    "__copyright__",
    "SOFTWARE_FULL_NAME",
    "SOFTWARE_SHORT_NAME",
    "APPDATA_PATH",
    "GLOBAL_CONFIG_NAME",
    "GLOBAL_CONFIG_PATH",
    "PLATFORM",
    "INPUT_HISTORY_PATH",
    "MAX_RECORD_LENGTH",
    "LOG_PATH",
    "LOG_RETENTION_DAYS",
    "LOG_CLEANUP_INTERVAL_SECONDS",
    "LINK_PREVIEW_OPTIONS",
    "LOG_FORMAT",
    "FILE_LOG_LEVEL",
    "CONSOLE_LOG_LEVEL",
    "CustomDumper",
    "README",
]
