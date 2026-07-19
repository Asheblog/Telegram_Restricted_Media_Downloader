# Nest PikPak archives under Post Author (opt-in)

部分频道主贴正文含作者署名行（完整标记 `…作者：#名字`，或频道常见短形式 `作者：#名字` / `作者：@名字`），但并非所有频道如此。我们选择：默认 Source Post Archive Path 保持扁平 `{Source Channel Folder}/{message_id} - {正文摘要}`；转存任务与监听规则增加可选开关 `archive_by_author`（默认关），勾选后路径扩展为 `{Source Channel Folder}/{Post Author}/{message_id} - {正文摘要}`，抽不到作者时落 `_未知作者`。新转存按任务/规则开关写入；历史扁平目录仍可由 WebUI「归档整理」显式抬升（与实时开关解耦）。频道统计仍只按路径第一段聚合。

**Considered Options:** 全局默认按作者（误伤无署名频道）；按频道记忆勾选；仅整理历史不改新路径；抽不到作者时保持扁平（即使已勾选）。

**Consequences:** 需从正文解析作者署名行；rclone 需列目录并移动整夹；TransferStore 的 `source_folder` 在整理时尽量回写；不回填更早的无主贴目录散文件。历史整理必须串行慢速（Telegram 逐条拉取、rclone 列表/移动带间隔）。网盘列目录与 Telegram 作者解析分离：目录清单可复用，「重新解析作者」只按主贴 ID 回查 Telegram 并重建计划，禁止为了改作者再全量扫网盘；整理复用最近一次成功扫描/解析计划。实时链路默认扁平，避免无署名频道大量 `_未知作者`。
