# Nest PikPak archives under Post Author

示例类频道主贴正文含 `示例社区作者：#名字`，但 ADR-0011 的 Source Post Archive Path 只有频道与主贴段，同一作者的帖子在 PikPak 里扁平散落。我们选择：路径扩展为 `{Source Channel Folder}/{Post Author}/{message_id} - {正文摘要}`；抽不到作者时落 `_未知作者`；新转存立即写入作者层；历史扁平目录由 WebUI「归档整理」扫描 Telegram 主贴后 rclone 整夹 `moveto` 抬升，已正确嵌套则跳过。频道统计仍只按路径第一段聚合。

**Considered Options:** 仅改文件夹名塞进作者（仍扁平）；作者放在频道之上；只整理历史不改新路径；抽不到作者时保持扁平。

**Consequences:** 需从正文解析示例作者行；rclone 需列目录并移动整夹；TransferStore 的 `source_folder` 在整理时尽量回写；不回填更早的无主贴目录散文件。历史整理必须串行慢速（Telegram 逐条拉取、rclone 列表/移动带间隔），整理复用最近一次成功扫描计划、禁止执行前再全量扫描，以避免触发 PikPak/Telegram 限流。
