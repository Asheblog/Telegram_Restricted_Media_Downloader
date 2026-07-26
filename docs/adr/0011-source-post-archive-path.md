# Nest PikPak archives under each channel post

频道帖评论区常承载正文资源，扁平按频道归档会把多帖视频混在一起。我们选择：所有转发/下载/深链/评论归档统一使用 Source Post Archive Path，`{Source Channel Folder}/{message_id} - {正文摘要}`（无摘要则仅 message_id）；Discussion Reply 与深链取回内容归属其频道主贴路径，而非讨论组或 bot 会话。同一媒体组（相册）的全部成员共用组内最小 `message_id` 与组内最佳正文摘要，禁止按成员各自建目录。频道统计仍只按路径第一段（Source Channel Folder）聚合。不回填历史扁平文件。

**Considered Options:** 仅频道一层；仅评论区嵌套；子目录纯用正文标题（无 message_id，易重名）；按讨论组 chat 命名；相册成员各自建目录（否决：图/视频会拆开）。

**Consequences:** rclone/local 路径需支持嵌套；写 item 时即写入完整路径；恢复归档可从 link/message_id 重建；标题需 sanitize 与截断。摘要启发式：硬标题（`【】` / 编号）优先；否则若正文**首个可用内容行**为纯 `#标签`，取第一个非站点/题材黑名单标签作叶子摘要（压过评论区导流句）；文末主题标签不得压过正文标题行；作者署名行仍只影响 Post Author，不因井号摘要而改变。无媒体（纯文字等）不得转发到 PikPak，也不得 `ensure_source_folder`，避免空帖目录与「入库确认超时」；PikPak 回复「不支持」视为入库失败并立即结束等待。相册共享路径应在可 await `get_media_group` 的链路预计算后写入 `source_folder`，避免同步路径误用异步 API。Web 区间循环必须在命中相册时拉齐组成员、共享归档目录，并跳过组内后续 id；`range_message_id` 仍按成员各自记账，否则 `range_transfer_progress` 会在相册空洞处冻结 completed_ids。
