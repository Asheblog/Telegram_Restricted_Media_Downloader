# Nest PikPak archives under each channel post

频道帖评论区常承载正文资源，扁平按频道归档会把多帖视频混在一起。我们选择：所有转发/下载/深链/评论归档统一使用 Source Post Archive Path，`{Source Channel Folder}/{message_id} - {正文摘要}`（无摘要则仅 message_id）；Discussion Reply 与深链取回内容归属其频道主贴路径，而非讨论组或 bot 会话。频道统计仍只按路径第一段（Source Channel Folder）聚合。不回填历史扁平文件。

**Considered Options:** 仅频道一层；仅评论区嵌套；子目录纯用正文标题（无 message_id，易重名）；按讨论组 chat 命名。

**Consequences:** rclone/local 路径需支持嵌套；写 item 时即写入完整路径；恢复归档可从 link/message_id 重建；标题需 sanitize 与截断。无媒体（纯文字等）不得转发到 PikPak，也不得 `ensure_source_folder`，避免空帖目录与「入库确认超时」；PikPak 回复「不支持」视为入库失败并立即结束等待。
