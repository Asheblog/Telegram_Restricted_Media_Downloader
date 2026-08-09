# Dedup PikPak archive target names so same-post media never overwrites

同一来源帖的多个媒体（相册成员、Deep Link 批次、或携带相同 caption 的资源 bot 媒体）会共享同一个确定性归档名 `{来源帖 message_id} - {标题}.{ext}`：`get_message_media_archive_filename` 以来源帖 id 作 `post_message_id`，标题经 `inherit_media_group_title` / 相同 caption 传播到每个媒体。此前 `RclonePikPakArchiveClient.archive_file` 对每个文件执行 `rclone moveto` 到同一目标路径，且没有任何查重/加后缀逻辑——后到的 moveto 静默覆盖先到的，先到的被移走后后续调用按名命中已有文件返回 `already_archived`。日志全绿但网盘只剩一个文件，SQLite 里却保留多条各带独立 `file_size` 的 Transfer Item（诊断复现：5 个不同大小的 ingest 文件全部 moveto 到同一 `Telegram/.../2509 - 标题.mp4`，最终唯一目标路径数 1/5）。

**决策：** 归档目标名在锁定下按需追加 PikPak 风格括号后缀 ` (1)` / ` (2)`…。同一来源帖多媒体最终落为 `2509 - 标题.mp4`、`2509 - 标题 (1).mp4`、`2509 - 标题 (2).mp4`……不再互相覆盖。比对按「扩展名 + 去除 `(N)` 后缀后的 stem」做 casefold（复用 `stem_without_duplicate_suffix`），与既有 `candidate_matches_ingest_name` / `disambiguate_archive_candidates` 的归一化口径一致，因此重试与「系统日志手动重试归档」仍能命中带后缀的历史文件。目标目录列名探测 + 命名 + `moveto`（含 source-missing 恢复）整体放入 `RclonePikPakArchiveClient` 实例级 `threading.Lock` 临界区——实时归档均共享同一缓存 client 实例（`PikpakIntegrationManager.get_pikpak_archive_client`），锁在实例上即可串行化并发归档；先到者落盘后，后到者在列名阶段必然看到它并取下一个空闲序号。

**Considered Options:** 不做任何去重（现状——覆盖数据丢失）；在 `get_message_media_archive_filename` 按成员 id 生成唯一名（违背「同一相册共享最小 message_id」的归档语义，Deep Link 取回消息无频道成员 id 可区分）；把去重放在 ingest 层改名（本 bug 不在 ingest，改名为 `name (N)` 反会被 ingest 匹配逻辑当成 PikPak 重复名处理）；连字符后缀 ` - 1`（与既有「消息ID - 描述」命名段混淆，`POST_FOLDER_SEGMENT_RE` / `message_id_from_post_folder_segment` 会误解析）；括号式 ` (N)`（PikPak 自身命名风格、语义清晰、与去重归一化兼容——选定）。

**Consequences:**

- 归档 `moveto` 前新增一次**非递归**目标帖目录 `rclone lsjson --files-only`（单目录、廉价；失败降级为空列表仍继续归档）。不影响 ingest 轮询的递归列表。
- 相同 `{message_id} - {标题}` 的并发/顺序归档自动获得不同后缀，不再覆盖。
- 归档路径的日志与 Transfer Item `archive_path` 反映实际落盘文件名（含后缀）。
- 目标目录已存在同名历史文件时，新归档自动避让，不会改写旧文件。
- 已入库的「只有 bare 名」旧文件不受影响；重试/手动重试按 bare 或 `(N)` 名均可匹配。
- 历史已被覆盖的文件无法通过本修复找回；如需追认可扫 SQLite 中同链路多条 item 指向同一 `archive_path` 的记录（本次不实现）。
