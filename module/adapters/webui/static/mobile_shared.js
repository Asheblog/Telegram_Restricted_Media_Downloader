
  const i18n = {
    zh: {
      'app.subtitle': '转存控制台',
      'app.title': 'TRMD 转存控制台',
      'nav.transfers': '转存任务',
      'nav.watches': '实时监听',
      'nav.channelDownloads': '频道下载',
      'nav.uploads': '本地上传',
      'nav.statistics': '统计',
      'nav.settings': '设置',
      'nav.records': '下载记录',
      'nav.logout': '退出登录',
      'nav.primary': '主导航',
'side.failed': '失败',
      'hero.title': 'PikPak 转存队列',
      'hero.body': '创建、监控和配置 Telegram 受限内容转存任务。状态、文件进度、失败事件和下载成功记录会持久化保存。',
      'action.refresh': '刷新',
      'language.label': '语言',
      'new.title': '新建转存',
      'new.profileNote': '目标配置',
      'new.source': '来源链接',
      'new.target': '目标',
      'new.targetProfile': '目标配置',
      'profile.pikpak': 'PikPak 文档转存',
      'profile.generic': '通用 Telegram 目标',
      'new.startId': '起始 ID',
      'new.endId': '结束 ID',
      'new.optional': '可选',
      'new.includeComment': '包含评论区',
      'new.hint': '单条消息链接可留空。频道或群链接不填 ID 时会自动探测可访问范围，也可手动指定起止 ID。',
      'new.create': '创建任务',
      'watches.title': '当前实时监听',
      'watches.downloadTitle': '监听下载',
      'watches.downloadMeta': '新消息转存',
      'watches.forwardTitle': '监听转发',
      'watches.forwardMeta': '新消息转发',
      'watches.sources': '来源频道',
      'watches.sourcesHint': '每行一个 Telegram 频道链接。监听下载会处理新到达的视频和图片。',
      'watches.source': '来源频道',
      'watches.target': '目标频道',
      'watches.includeComment': '包含评论区',
      'watches.forwardHint': '同一来源不能同时存在监听下载和监听转发。',
      'watches.createDownload': '新增监听下载',
      'watches.createForward': '新增监听转发',
      'watches.type': '类型',
      'watches.empty': '还没有实时监听。',
      'watches.delete': '移除监听',
      'watches.download': '监听下载',
      'watches.forward': '监听转发',
      'watches.created': '实时监听已接收。',
      'watches.deleted': '实时监听已移除。',
      'watches.edit': '编辑',
      'watches.updated': '实时监听已更新。',
      'watches.events': '转发记录',
      'watches.noEvents': '暂无转发记录',
      'watches.eventForwarded': '转发成功',
      'watches.eventSkipped': '已过滤',
      'watches.eventLoading': '加载中…',
      'watches.loadMore': '加载更多',
      'watches.targetRequired': '目标频道为必填项。',
      'action.cancel': '取消',
      'action.save': '保存',
      'channel.title': '频道下载',
      'channel.meta': '筛选后创建下载',
      'channel.link': '频道链接',
      'channel.startDate': '起始时间',
      'channel.endDate': '结束时间',
      'channel.types': '下载类型',
      'channel.keywords': '关键词',
      'channel.keywordsPlaceholder': '逗号分隔，可留空',
      'channel.includeComment': '包含评论区',
      'channel.hint': '频道下载会检索匹配消息并创建下载任务，执行时间取决于频道历史消息数量。',
      'channel.create': '创建频道下载',
      'channel.accepted': '频道下载已接收。',
      'uploads.title': '本地上传',
      'uploads.meta': '服务器路径',
      'uploads.path': '本地路径',
      'uploads.target': '目标频道',
      'uploads.recursive': '递归上传文件夹',
      'uploads.serverPathHint': '路径位于运行 TRMD 的服务器或容器，不是当前浏览器所在电脑。关闭递归时，文件夹只上传第一层文件；开启递归时包含子文件夹。',
      'uploads.create': '创建上传',
      'uploads.accepted': '上传任务已接收。',
      'statistics.title': '统计与导出',
      'statistics.meta': '运行态数据',
      'statistics.table': '表格',
      'statistics.available': '可用',
      'statistics.rows': '数量',
      'statistics.yes': '是',
      'statistics.no': '否',
      'statistics.link': '链接统计表',
      'statistics.count': '计数统计表',
      'statistics.upload': '上传统计表',
      'statistics.exportLink': '导出链接统计表',
      'statistics.exportCount': '导出计数统计表',
      'statistics.exportUpload': '导出上传统计表',
      'statistics.exported': '统计表已导出到：{directory}',
      'tasks.title': '转存任务',
      'tasks.notSynced': '尚未同步',
      'tasks.id': 'ID',
      'tasks.status': '状态',
      'tasks.source': '来源',
      'tasks.target': '目标',
      'tasks.progress': '进度',
      'tasks.actions': '操作',
      'tasks.pause': '暂停',
      'tasks.resume': '继续',
      'tasks.retryFailed': '重试失败',
      'tasks.delete': '删除',
      'tasks.empty': '还没有转存任务。',
      'items.title': '文件进度',
      'items.selectTask': '选择一个任务',
      'items.empty': '该任务还没有文件记录。',
      'items.tabsLabel': '文件状态分类',
      'items.tab.running': '进行中',
      'items.tab.success': '已完成',
      'items.tab.skipped': '跳过',
      'items.tab.failure': '失败',
      'items.empty.running': '当前没有进行中的文件。',
      'items.empty.success': '当前没有已完成的文件。',
      'items.empty.skipped': '当前没有跳过的文件。',
      'items.empty.failure': '当前没有失败的文件。',
      'items.retryFailed': '重试当前任务失败项',
      'items.page.previous': '上一页',
      'items.page.next': '下一页',
      'items.page.status': '第 {page} / {pages} 页',
      'items.page.range': '{start}-{end} / {total}',
      'items.download': '下载',
      'items.upload': '上传',
      'items.loadMore': '加载更多文件',
      'items.remaining': '条剩余',
      'events.title': '最近事件',
      'events.empty': '没有事件记录。',
      'events.loadMore': '加载更多事件',
      'events.remaining': '条剩余',
      'settings.title': '设置',
      'settings.safeNote': '敏感字段只显示是否已配置',
      'settings.paths': '路径与任务',
      'settings.saveDirectory': '保存目录',
      'settings.tempDirectory': '临时目录',
      'settings.sessionDirectory': '会话目录',
      'settings.maxDownload': '最大下载任务',
      'settings.maxUpload': '最大上传任务',
      'settings.retryDownload': '下载重试',
      'settings.retryUpload': '上传重试',
      'settings.pikpakMaxFileSize': 'PikPak大小上限(字节)',
      'settings.pikpakArchive': 'PikPak 归档',
      'settings.pikpakArchiveEnable': 'PikPak按来源频道归档',
      'settings.pikpakArchiveRemote': 'PikPak rclone remote',
      'settings.pikpakArchiveSource': 'PikPak入库目录',
      'settings.pikpakArchiveRoot': 'PikPak归档根目录',
      'settings.pikpakArchivePoll': '入库轮询秒数',
      'settings.pikpakArchiveInterval': '轮询间隔秒数',
      'settings.pikpakArchiveWindow': '匹配时间窗口秒数',
      'settings.behavior': '行为',
      'settings.notice': '机器人通知',
      'settings.shutdown': '退出后关机',
      'settings.downloadUpload': '受限转发时下载后上传',
      'settings.uploadDelete': '上传完成删除本地文件',
      'settings.pendingLimit': '下载后上传队列',
      'settings.sensitive': '账号与代理',
      'settings.proxyPassword': '代理密码',
      'settings.secretConfigured': '已配置，如需更换请填写',
      'settings.secretNotConfigured': '未配置',
      'settings.downloadTypes': '下载类型',
      'settings.forwardTypes': '转发类型',
      'settings.messageFilter': '消息过滤',
      'settings.mediaTypes': '媒体类型',
      'settings.dateRange': '日期范围',
      'settings.keywords': '关键词',
      'settings.enabled': '启用',
      'settings.startDate': '起始日期',
      'settings.endDate': '结束日期',
      'settings.keywordList': '关键词列表（逗号分隔）',
      'settings.keywordPlaceholder': '输入关键词,用逗号分隔',
      'settings.exports': '导出表格',
      'settings.exportLink': '链接统计表',
      'settings.exportCount': '计数统计表',
      'settings.exportUpload': '上传统计表',
      'settings.save': '保存设置',
      'settings.saved': '设置已保存。',
      'records.title': '下载成功记录',
      'records.chat': '频道 ID',
      'records.message': '消息 ID',
      'records.file': '文件',
      'records.size': '大小',
      'records.updated': '更新时间',
      'records.empty': '还没有下载成功记录。',
      'form.createFailed': '创建任务失败。',
      'form.requestFailed': '请求失败。',
      'form.creatingTransfer': '正在分析来源消息范围，Telegram 限流时可能需要等待。请保持页面打开。',
      'form.creatingTransferShort': '正在分析',
      'form.createSuccess': '任务已创建并开始排队。可以关闭页面，也可以继续查看进度。',
      'error.auth_required': '需要登录。',
      'error.invalid_task_id': '任务 ID 无效。',
      'error.task_not_found': '找不到任务。',
      'error.not_found': '找不到请求的资源。',
      'error.source_link_required': '请填写来源链接。',
      'error.target_link_required': '请填写目标链接。',
      'error.range_ids_required': '起始 ID 和结束 ID 必须同时填写。',
      'error.range_end_before_start': '结束 ID 必须大于或等于起始 ID。',
      'error.range_source_must_be_chat_link': '范围转存的来源必须是频道链接，不能是单条消息链接。',
      'error.transfer_range_detection_unavailable': '当前运行模式无法自动探测消息范围。',
      'error.transfer_range_detection_failed': '自动探测消息范围失败。',
      'error.transfer_range_empty': '来源中没有可访问的消息。',
      'error.create_task_failed': '创建任务失败。',
      'error.update_settings_failed': '更新设置失败。',
      'error.watch_source_conflict': '同一来源不能同时存在监听下载和监听转发。',
      'error.watch_already_exists': '实时监听已存在。',
      'error.watch_source_required': '请填写监听来源。',
      'error.watch_target_required': '请填写监听目标。',
      'error.invalid_payload': '请求内容无效。',
      'error.invalid_watch_type': '实时监听类型无效。',
      'error.invalid_watch_source': '监听来源必须以 https://t.me/ 开头。',
      'error.invalid_watch_target': '监听目标必须以 https://t.me/ 开头。',
      'error.watch_operations_unavailable': '实时监听操作不可用。',
      'error.upload_path_not_found': '服务器或容器中找不到该路径。',
      'error.upload_path_required': '请填写上传路径。',
      'error.upload_target_required': '请填写上传目标。',
      'error.upload_recursive_requires_directory': '递归上传需要选择文件夹路径。',
      'error.invalid_upload_target': '上传目标必须是 Telegram 链接、me 或 self。',
      'error.upload_operations_unavailable': '上传操作不可用。',
      'error.invalid_table_type': '统计表类型无效。',
      'error.table_operations_unavailable': '统计表操作不可用。',
      'error.invalid_channel_link': '频道链接必须以 https://t.me/ 开头。',
      'error.channel_link_required': '请填写频道链接。',
      'error.channel_download_type_required': '请至少选择一种下载类型。',
      'error.invalid_channel_download_type': '频道下载类型无效。',
      'error.channel_download_operations_unavailable': '频道下载操作不可用。',
      'action.taskUpdated': '任务操作已提交。',
      'error.invalid_date_range': '时间范围格式无效。',
      'error.date_range_end_before_start': '结束时间必须大于或等于起始时间。',
      'event.level.info': '信息',
      'event.level.warning': '警告',
      'event.level.error': '错误',
      'event.fileReady': '文件已准备上传到目标：{name}',
      'event.sentToTarget': '已发送到目标：{name}',
      'event.uploadFailed': '上传失败：{reason}',
      'event.reusedDownload': '已复用下载成功记录：{name}',
      'event.directForward': '已直接发送到目标：{link}',
      'event.rangeAssigned': '范围转存已分配：{range}',
      'event.rangeAssignedWithFallback': '范围转存已分配：{range}，回退下载 {count} 条。',
      'event.singleAssigned': '单条消息转存已分配。',
      'event.singleAssignedWithFallback': '单条消息转存已分配，回退下载 {count} 条。',
      'status.pending': '等待',
      'status.running': '运行中',
      'status.paused': '已暂停',
      'status.success': '成功',
      'status.failure': '失败',
      'status.skipped': '跳过',
      'nav.media': '媒体管理',
      'media.title': '媒体管理',
      'media.meta': '扫描并清理磁盘上的残留媒体文件',
      'media.scan': '扫描可清理文件',
      'media.scanning': '正在扫描...',
      'media.totalFiles': '可清理文件',
      'media.totalSize': '总大小',
      'media.retentionDays': '保留天数',
      'media.transferItems': '转存任务文件',
      'media.orphanFiles': '遗留文件 (超过保留天数)',
      'media.file': '文件',
      'media.size': '大小',
      'media.status': '任务状态',
      'media.source': '来源',
      'media.path': '路径',
      'media.mtime': '最后修改',
      'media.cleanup': '清理选中文件',
      'media.cleaning': '清理中...',
      'media.selected': '已选',
      'media.files': '个文件',
      'media.noSelection': '请先选择要清理的文件。',
      'media.confirmCleanup': '确定要删除选中的文件吗？此操作不可撤销。',
      'media.cleanupDone': '清理完成：已删除 {count} 个文件 ({size})。',
      'media.cleanupHistory': '清理历史',
      'media.reason': '原因',
      'media.time': '时间',
      'media.filterByTask': '按任务筛选：',
      'media.allTasks': '全部任务'
    },
    en: {
      'app.subtitle': 'Transfer Console',
      'app.title': 'TRMD Transfer Console',
      'nav.transfers': 'Transfer tasks',
      'nav.watches': 'Live watches',
      'nav.channelDownloads': 'Channel downloads',
      'nav.uploads': 'Local uploads',
      'nav.statistics': 'Statistics',
      'nav.settings': 'Settings',
      'nav.records': 'Download records',
      'nav.logout': 'Log out',
      'nav.primary': 'Primary navigation',
'side.failed': 'Failed',
      'hero.title': 'PikPak transfer queue',
      'hero.body': 'Create, monitor, and configure Telegram restricted content transfer tasks. State, file progress, failure events, and download success records are persisted.',
      'action.refresh': 'Refresh',
      'language.label': 'Language',
      'new.title': 'New transfer',
      'new.profileNote': 'Target profile',
      'new.source': 'Source link',
      'new.target': 'Target',
      'new.targetProfile': 'Target profile',
      'profile.pikpak': 'PikPak document transfer',
      'profile.generic': 'Generic Telegram target',
      'new.startId': 'Start ID',
      'new.endId': 'End ID',
      'new.optional': 'Optional',
      'new.includeComment': 'Include discussion replies',
      'new.hint': 'Leave the range empty for a message link. For a channel or group link, empty IDs auto-detect the accessible range, or you can set start and end IDs manually.',
      'new.create': 'Create task',
      'watches.title': 'Current live watches',
      'watches.downloadTitle': 'Download watch',
      'watches.downloadMeta': 'Transfer new messages',
      'watches.forwardTitle': 'Forward watch',
      'watches.forwardMeta': 'Forward new messages',
      'watches.sources': 'Source channels',
      'watches.sourcesHint': 'One Telegram channel link per line. Download watches handle new video and photo messages.',
      'watches.source': 'Source channel',
      'watches.target': 'Target channel',
      'watches.includeComment': 'Include discussion replies',
      'watches.forwardHint': 'The same source cannot have a download watch and a forward watch at the same time.',
      'watches.createDownload': 'Add download watch',
      'watches.createForward': 'Add forward watch',
      'watches.type': 'Type',
      'watches.empty': 'No live watches yet.',
      'watches.delete': 'Remove watch',
      'watches.download': 'Download watch',
      'watches.forward': 'Forward watch',
      'watches.created': 'Live watch accepted.',
      'watches.deleted': 'Live watch removed.',
      'watches.edit': 'Edit',
      'watches.updated': 'Live watch updated.',
      'watches.events': 'Forwarding log',
      'watches.noEvents': 'No forwarding events yet.',
      'watches.eventForwarded': 'Forwarded',
      'watches.eventSkipped': 'Filtered',
      'watches.eventLoading': 'Loading…',
      'watches.loadMore': 'Load more',
      'watches.targetRequired': 'Target link is required.',
      'action.cancel': 'Cancel',
      'action.save': 'Save',
      'channel.title': 'Channel download',
      'channel.meta': 'Create downloads after filtering',
      'channel.link': 'Channel link',
      'channel.startDate': 'Start time',
      'channel.endDate': 'End time',
      'channel.types': 'Download types',
      'channel.keywords': 'Keywords',
      'channel.keywordsPlaceholder': 'Comma-separated, optional',
      'channel.includeComment': 'Include discussion replies',
      'channel.hint': 'Channel download scans matching messages and creates download tasks. Runtime depends on channel history size.',
      'channel.create': 'Create channel download',
      'channel.accepted': 'Channel download accepted.',
      'uploads.title': 'Local upload',
      'uploads.meta': 'Server path',
      'uploads.path': 'Local path',
      'uploads.target': 'Target channel',
      'uploads.recursive': 'Upload folder recursively',
      'uploads.serverPathHint': 'The path is on the server or container running TRMD, not on this browser device. With recursion off, a folder uploads only its top-level files; with recursion on, subfolders are included.',
      'uploads.create': 'Create upload',
      'uploads.accepted': 'Upload request accepted.',
      'statistics.title': 'Statistics and export',
      'statistics.meta': 'Runtime data',
      'statistics.table': 'Table',
      'statistics.available': 'Available',
      'statistics.rows': 'Rows',
      'statistics.yes': 'Yes',
      'statistics.no': 'No',
      'statistics.link': 'Link table',
      'statistics.count': 'Count table',
      'statistics.upload': 'Upload table',
      'statistics.exportLink': 'Export link table',
      'statistics.exportCount': 'Export count table',
      'statistics.exportUpload': 'Export upload table',
      'statistics.exported': 'Table exported to: {directory}',
      'tasks.title': 'Transfer tasks',
      'tasks.notSynced': 'Not synced',
      'tasks.id': 'ID',
      'tasks.status': 'Status',
      'tasks.source': 'Source',
      'tasks.target': 'Target',
      'tasks.progress': 'Progress',
      'tasks.actions': 'Actions',
      'tasks.pause': 'Pause',
      'tasks.resume': 'Resume',
      'tasks.retryFailed': 'Retry failed',
      'tasks.delete': 'Delete',
      'tasks.empty': 'No transfer tasks yet.',
      'items.title': 'File progress',
      'items.selectTask': 'Select a task',
      'items.empty': 'No file records for this task yet.',
      'items.tabsLabel': 'File status categories',
      'items.tab.running': 'Running',
      'items.tab.success': 'Completed',
      'items.tab.skipped': 'Skipped',
      'items.tab.failure': 'Failed',
      'items.empty.running': 'No running files in this task.',
      'items.empty.success': 'No completed files in this task.',
      'items.empty.skipped': 'No skipped files in this task.',
      'items.empty.failure': 'No failed files in this task.',
      'items.retryFailed': 'Retry failed items in this task',
      'items.page.previous': 'Previous',
      'items.page.next': 'Next',
      'items.page.status': 'Page {page} / {pages}',
      'items.page.range': '{start}-{end} / {total}',
      'items.download': 'Download',
      'items.upload': 'Upload',
      'items.loadMore': 'Load more files',
      'items.remaining': 'remaining',
      'events.title': 'Latest events',
      'events.empty': 'No events recorded.',
      'events.loadMore': 'Load more events',
      'events.remaining': 'remaining',
      'settings.title': 'Settings',
      'settings.safeNote': 'Sensitive fields only show configured state',
      'settings.paths': 'Paths and tasks',
      'settings.saveDirectory': 'Save directory',
      'settings.tempDirectory': 'Temp directory',
      'settings.sessionDirectory': 'Session directory',
      'settings.maxDownload': 'Max download tasks',
      'settings.maxUpload': 'Max upload tasks',
      'settings.retryDownload': 'Download retries',
      'settings.retryUpload': 'Upload retries',
      'settings.pikpakMaxFileSize': 'PikPak size limit (bytes)',
      'settings.pikpakArchive': 'PikPak archive',
      'settings.pikpakArchiveEnable': 'Archive PikPak by source channel',
      'settings.pikpakArchiveRemote': 'PikPak rclone remote',
      'settings.pikpakArchiveSource': 'PikPak source folder',
      'settings.pikpakArchiveRoot': 'PikPak archive root',
      'settings.pikpakArchivePoll': 'Ingest poll seconds',
      'settings.pikpakArchiveInterval': 'Poll interval seconds',
      'settings.pikpakArchiveWindow': 'Match window seconds',
      'settings.behavior': 'Behavior',
      'settings.notice': 'Bot notifications',
      'settings.shutdown': 'Shutdown after exit',
      'settings.downloadUpload': 'Download then upload restricted forwards',
      'settings.uploadDelete': 'Delete local file after upload',
      'settings.pendingLimit': 'Upload-after-download queue',
      'settings.sensitive': 'Account and proxy',
      'settings.proxyPassword': 'Proxy password',
      'settings.secretConfigured': 'Configured; enter a new value to replace',
      'settings.secretNotConfigured': 'Not configured',
      'settings.downloadTypes': 'Download types',
      'settings.forwardTypes': 'Forward types',
      'settings.messageFilter': 'Message filter',
      'settings.mediaTypes': 'Media types',
      'settings.dateRange': 'Date range',
      'settings.keywords': 'Keywords',
      'settings.enabled': 'Enabled',
      'settings.startDate': 'Start date',
      'settings.endDate': 'End date',
      'settings.keywordList': 'Keywords (comma separated)',
      'settings.keywordPlaceholder': 'Enter keywords, separated by commas',
      'settings.exports': 'Table exports',
      'settings.exportLink': 'Link table',
      'settings.exportCount': 'Count table',
      'settings.exportUpload': 'Upload table',
      'settings.save': 'Save settings',
      'settings.saved': 'Settings saved.',
      'records.title': 'Download success records',
      'records.chat': 'Channel ID',
      'records.message': 'Message ID',
      'records.file': 'File',
      'records.size': 'Size',
      'records.updated': 'Updated',
      'records.empty': 'No download success records yet.',
      'form.createFailed': 'Create task failed.',
      'form.requestFailed': 'Request failed.',
      'form.creatingTransfer': 'Analyzing the source message range. Telegram flood waits can take a while; keep this page open.',
      'form.creatingTransferShort': 'Analyzing',
      'form.createSuccess': 'Task created and queued. You can close this page or keep watching progress.',
      'error.auth_required': 'Authentication required.',
      'error.invalid_task_id': 'Invalid task ID.',
      'error.task_not_found': 'Task not found.',
      'error.not_found': 'Resource not found.',
      'error.source_link_required': 'Source link is required.',
      'error.target_link_required': 'Target link is required.',
      'error.range_ids_required': 'Start ID and End ID must be provided together.',
      'error.range_end_before_start': 'End ID must be greater than or equal to Start ID.',
      'error.range_source_must_be_chat_link': 'Range transfer source must be a chat link, not a message link.',
      'error.transfer_range_detection_unavailable': 'Automatic message range detection is unavailable in this runtime.',
      'error.transfer_range_detection_failed': 'Automatic message range detection failed.',
      'error.transfer_range_empty': 'No accessible messages were found for the source.',
      'error.create_task_failed': 'Create task failed.',
      'error.update_settings_failed': 'Update settings failed.',
      'error.watch_source_conflict': 'The same source cannot have a download watch and a forward watch at the same time.',
      'error.watch_already_exists': 'Live watch already exists.',
      'error.watch_source_required': 'Watch source is required.',
      'error.watch_target_required': 'Watch target is required.',
      'error.invalid_payload': 'Invalid request payload.',
      'error.invalid_watch_type': 'Invalid live watch type.',
      'error.invalid_watch_source': 'Watch source must start with https://t.me/.',
      'error.invalid_watch_target': 'Watch target must start with https://t.me/.',
      'error.watch_operations_unavailable': 'Live watch operations are unavailable.',
      'error.upload_path_not_found': 'Path not found on the server or container.',
      'error.upload_path_required': 'Upload path is required.',
      'error.upload_target_required': 'Upload target is required.',
      'error.upload_recursive_requires_directory': 'Recursive upload requires a folder path.',
      'error.invalid_upload_target': 'Upload target must be a Telegram link, me, or self.',
      'error.upload_operations_unavailable': 'Upload operations are unavailable.',
      'error.invalid_table_type': 'Invalid table type.',
      'error.table_operations_unavailable': 'Table operations are unavailable.',
      'error.invalid_channel_link': 'Channel link must start with https://t.me/.',
      'error.channel_link_required': 'Channel link is required.',
      'error.channel_download_type_required': 'Select at least one download type.',
      'error.invalid_channel_download_type': 'Invalid channel download type.',
      'error.channel_download_operations_unavailable': 'Channel download operations are unavailable.',
      'error.invalid_date_range': 'Invalid date range.',
      'error.date_range_end_before_start': 'End time must be greater than or equal to start time.',
      'action.taskUpdated': 'Task action submitted.',
      'event.level.info': 'info',
      'event.level.warning': 'warning',
      'event.level.error': 'error',
      'event.fileReady': 'File ready for target upload: {name}',
      'event.sentToTarget': 'Sent to target: {name}',
      'event.uploadFailed': 'Upload failed: {reason}',
      'event.reusedDownload': 'Reused download success record: {name}',
      'event.directForward': 'Directly sent to target: {link}',
      'event.rangeAssigned': 'Range transfer assigned: {range}',
      'event.rangeAssignedWithFallback': 'Range transfer assigned: {range}; fallback downloads: {count}.',
      'event.singleAssigned': 'Single-message transfer assigned.',
      'event.singleAssignedWithFallback': 'Single-message transfer assigned; fallback downloads: {count}.',
      'status.pending': 'pending',
      'status.running': 'running',
      'status.paused': 'paused',
      'status.success': 'success',
      'status.failure': 'failure',
      'status.skipped': 'skipped',
      'nav.media': 'Media',
      'media.title': 'Media Management',
      'media.meta': 'Scan and clean residual media files on disk',
      'media.scan': 'Scan for cleanable files',
      'media.scanning': 'Scanning...',
      'media.totalFiles': 'Cleanable files',
      'media.totalSize': 'Total size',
      'media.retentionDays': 'Retention days',
      'media.transferItems': 'Transfer task files',
      'media.orphanFiles': 'Orphan files (exceeding retention)',
      'media.file': 'File',
      'media.size': 'Size',
      'media.status': 'Task status',
      'media.source': 'Source',
      'media.path': 'Path',
      'media.mtime': 'Last modified',
      'media.cleanup': 'Clean selected',
      'media.cleaning': 'Cleaning...',
      'media.selected': 'Selected',
      'media.files': 'files',
      'media.noSelection': 'Select files to clean first.',
      'media.confirmCleanup': 'Are you sure you want to delete selected files? This cannot be undone.',
      'media.cleanupDone': 'Cleanup done: {count} files deleted ({size}).',
      'media.cleanupHistory': 'Cleanup history',
      'media.reason': 'Reason',
      'media.time': 'Time',
      'media.filterByTask': 'Filter by task:',
      'media.allTasks': 'All tasks'
    }
  };

  const state = {
    lang: localStorage.getItem('trmd-lang') || 'zh',
    selectedTaskId: null,
    settings: null,
    schema: null,
    tasks: [],
    items: [],
    events: [],
    records: [],
    watches: [],
    statistics: null,
    lastSync: null,
    activeItemStatus: 'running',
    itemPages: {
      running: 1,
      success: 1,
      skipped: 1,
      failure: 1
    },
    itemsTotal: 0,
    eventsTotal: 0,
    itemsOffset: 0,
    eventsOffset: 0,
    hasMoreItems: false,
    hasMoreEvents: false,
    taskPollTimer: null,
    loadingDetail: false
  };

  const $ = selector => document.querySelector(selector);
  const $$ = selector => Array.from(document.querySelectorAll(selector));
  const ITEMS_PAGE_SIZE = 10;
  const ITEM_STATUS_TABS = ['running', 'success', 'skipped', 'failure'];

  function t(key) {
    return (i18n[state.lang] && i18n[state.lang][key]) || i18n.zh[key] || key;
  }

  function interpolate(template, values) {
    return String(template).replace(/\{(\w+)}/g, (_, key) => values[key] ?? '');
  }

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  function pct(current, total) {
    current = Number(current || 0);
    total = Number(total || 0);
    return total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  }

  function formatBytes(value) {
    value = Number(value || 0);
    const units = ['B', 'KiB', 'MiB', 'GiB'];
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value = value / 1024;
      unit += 1;
    }
    return `${value.toFixed(unit ? 1 : 0)} ${units[unit]}`;
  }

  function translateApiError(payload, fallbackKey = 'form.requestFailed') {
    if (payload && payload.error_code) {
      const key = `error.${payload.error_code}`;
      const message = t(key);
      return message === key ? (payload.error || t(fallbackKey)) : message;
    }
    return (payload && payload.error) || t(fallbackKey);
  }

  function showNotice(selector, message, ok = true) {
    const notice = $(selector);
    if (!notice) return;
    notice.textContent = message;
    notice.classList.toggle('ok', ok);
    notice.classList.add('is-visible');
  }

  function showFormMessage(message, ok = true) {
    const formNotice = $('#form-error');
    formNotice.textContent = message;
    formNotice.classList.toggle('ok', ok);
    formNotice.classList.add('is-visible');
  }

  async function withLoading(button, task) {
    const previous = button ? button.disabled : false;
    if (button) button.disabled = true;
    try {
      return await task();
    } finally {
      if (button) button.disabled = previous;
    }
  }

  async function fetchJson(path) {
    const res = await fetch(path);
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  async function postJson(path, payload) {
    const res = await fetch(path, {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  function localizeEventMessage(event) {
    const message = String((event && event.message) || '');
    let match = message.match(/^File ready for target upload: (.+)$/);
    if (match) return interpolate(t('event.fileReady'), {name: match[1]});
    match = message.match(/^Sent to target: (.+)$/);
    if (match) return interpolate(t('event.sentToTarget'), {name: match[1]});
    match = message.match(/^Upload failed: (.+)$/);
    if (match) return interpolate(t('event.uploadFailed'), {reason: match[1]});
    match = message.match(/^Reused download success record: (.+)$/);
    if (match) return interpolate(t('event.reusedDownload'), {name: match[1]});
    match = message.match(/^Direct forward succeeded: (.+)$/);
    if (match) return interpolate(t('event.directForward'), {link: match[1]});
    match = message.match(/^Range transfer assigned: (.+)\. Fallback downloads: (\d+)\.$/);
    if (match) return interpolate(t('event.rangeAssignedWithFallback'), {range: match[1], count: match[2]});
    match = message.match(/^Range transfer assigned: (.+)\.$/);
    if (match) return interpolate(t('event.rangeAssigned'), {range: match[1]});
    match = message.match(/^Single-message transfer assigned\. Fallback downloads: (\d+)\.$/);
    if (match) return interpolate(t('event.singleAssignedWithFallback'), {count: match[1]});
    if (message === 'Single-message transfer assigned.') return t('event.singleAssigned');
    return message;
  }

  function localizeEventLevel(level) {
    const key = `event.level.${level}`;
    const translated = t(key);
    return translated === key ? level : translated;
  }

  function applyLanguage() {
    document.documentElement.lang = state.lang === 'zh' ? 'zh-CN' : 'en';
    document.title = t('app.title');
    $('#language-select').value = state.lang;
    $$('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
    $$('[data-i18n-placeholder]').forEach(el => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    $$('[data-i18n-aria-label]').forEach(el => {
      el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel));
    });
    $$('[data-i18n-title]').forEach(el => {
      el.setAttribute('title', t(el.dataset.i18nTitle));
    });
  }

  function refreshVisibleDynamicText() {
    renderTasks();
    $('#selected-task').textContent = state.selectedTaskId ? `#${state.selectedTaskId}` : t('items.selectTask');
    renderItems(state.items);
    renderEvents(state.events);
    renderRecords();
    if (state.settings) fillSettingsForm();
  }

  function applyLanguageAndRefresh() {
    applyLanguage();
    refreshVisibleDynamicText();
  }

  async function handleLogout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (_) { /* proceed regardless */ }
    window.location.href = '/';
  }

  function switchView(view) {
    $$('.view').forEach(el => el.classList.toggle('active', el.id === `view-${view}`));
    $$('[data-nav]').forEach(el => el.classList.toggle('active', el.dataset.nav === view));
    if (view === 'settings') loadSettings();
    if (view === 'records') loadRecords();
    if (view === 'watches') loadWatches();
    if (view === 'statistics') loadStatistics();
  }

  function badge(status) {
    return `<span class="badge ${esc(status)}">${esc(t(`status.${status}`))}</span>`;
  }

  function taskProgress(task) {
    const total = Number(task.total_items || 0);
    const done = Number(task.completed_items || 0);
    const failed = Number(task.failed_items || 0);
    const percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;
    const progressLabel = `${percent}% · ${done}/${total}${failed ? ` · ${failed} ${t('side.failed')}` : ''}`;
    return `
      <div class="task-progress" aria-label="${esc(progressLabel)}">
        <div class="task-progress__head">
          <span class="task-progress__percent">${percent}%</span>
          <span class="task-progress__detail">
            ${done}/${total}${failed ? ` <span class="task-progress__failed">${failed} ${esc(t('side.failed'))}</span>` : ''}
          </span>
        </div>
        <div class="progress" title="${esc(progressLabel)}"><div style="width:${percent}%"></div></div>
      </div>
    `;
  }

  function renderTasks() {
    const tasks = state.tasks || [];
$('#metric-failed').textContent = tasks.filter(task => task.status === 'failure').length;
    if (state.lastSync) $('#last-sync').textContent = state.lastSync;
    $('#empty').style.display = tasks.length ? 'none' : 'block';
    $('#tasks').innerHTML = tasks.map(task => `
      <tr data-task-id="${task.id}">
        <td class="mono">#${task.id}</td>
        <td>${badge(task.status)}</td>
        <td class="mono">${esc(task.source_link)}</td>
        <td class="mono">${esc(task.target_link)}</td>
        <td>${taskProgress(task)}</td>
        <td>
           <div class="task-actions">
            ${task.status === 'running' || task.status === 'paused'
            ? `<button class="secondary icon-only" type="button" title="${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}" aria-label="${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}" onclick="${task.status === 'paused' ? `resumeTask(event, ${task.id})` : `pauseTask(event, ${task.id})`}">
              ${task.status === 'paused'
                ? '<svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14l11-7L8 5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14M16 5v14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'}
              <span class="sr-only">${esc(t(task.status === 'paused' ? 'tasks.resume' : 'tasks.pause'))}</span>
            </button>`
            : ''}
            <button class="secondary icon-only" type="button" title="${esc(t('tasks.retryFailed'))}" aria-label="${esc(t('tasks.retryFailed'))}" onclick="retryFailedTask(event, ${task.id})" ${Number(task.failed_items || 0) ? '' : 'disabled'}>
              <svg viewBox="0 0 24 24" fill="none"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 8v4l3 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
              <span class="sr-only">${esc(t('tasks.retryFailed'))}</span>
            </button>
            <button class="danger icon-only" type="button" title="${esc(t('tasks.delete'))}" aria-label="${esc(t('tasks.delete'))}" onclick="deleteTask(event, ${task.id})">
              <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span class="sr-only" data-i18n="tasks.delete">${esc(t('tasks.delete'))}</span>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
    $$('tr[data-task-id]').forEach(row => {
      row.addEventListener('click', () => loadTask(row.dataset.taskId));
    });
  }

  async function loadTasks() {
    const res = await fetch('/api/tasks');
    const data = await res.json();
    state.tasks = data.tasks || [];
    state.lastSync = new Date().toLocaleTimeString();
    renderTasks();
    if (!state.selectedTaskId && state.tasks[0]) {
      await loadTaskDetail(state.tasks[0].id, true);
    } else if (state.selectedTaskId) {
      await loadTaskSummary(state.selectedTaskId);
    } else {
      state.items = [];
      state.events = [];
      state.itemsTotal = 0;
      state.eventsTotal = 0;
      $('#selected-task').textContent = t('items.selectTask');
      renderItems();
      renderEvents();
    }
  }

  async function loadTaskSummary(id) {
    const taskId = Number(id);
    const res = await fetch(`/api/tasks/${taskId}/summary`);
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.task) {
      state.selectedTaskId = taskId;
      state.itemsTotal = data.item_count || 0;
      state.eventsTotal = data.event_count || 0;
      updateTaskSummaryDisplay(data.task);
      if (data.recent_events && data.recent_events.length) {
        mergeRecentEvents(data.recent_events);
      }
    }
  }

  function updateTaskSummaryDisplay(task) {
    $('#selected-task').textContent = `#${task.id}`;
    renderEventCount();
  }

  async function loadTaskDetail(id, keepExistingItems) {
    const taskId = Number(id);
    if (state.selectedTaskId !== taskId) {
      resetItemPages();
      state.items = [];
      state.events = [];
      state.itemsOffset = 0;
      state.eventsOffset = 0;
      state.hasMoreItems = false;
      state.hasMoreEvents = false;
    }
    state.selectedTaskId = taskId;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=200&items_offset=0&events_limit=100&events_offset=0`);
      if (!res.ok) {
        state.selectedTaskId = null;
        state.items = [];
        state.events = [];
        $('#selected-task').textContent = t('items.selectTask');
        renderItems();
        renderEvents();
        return;
      }
      const data = await res.json();
      $('#selected-task').textContent = `#${taskId}`;
      state.items = data.items || [];
      state.events = data.events || [];
      state.itemsTotal = data.item_count || 0;
      state.eventsTotal = data.event_count || 0;
      state.itemsOffset = data.items_offset || 0;
      state.eventsOffset = data.events_offset || 0;
      state.hasMoreItems = data.has_more_items || false;
      state.hasMoreEvents = data.has_more_events || false;
      renderItems();
      renderEvents();
    } finally {
      state.loadingDetail = false;
    }
  }

  async function loadMoreItems() {
    if (state.loadingDetail) return;
    const taskId = state.selectedTaskId;
    if (!taskId) return;
    const offset = state.itemsOffset + 200;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=200&items_offset=${offset}&events_limit=0&events_offset=0`);
      if (!res.ok) return;
      const data = await res.json();
      state.items = state.items.concat(data.items || []);
      state.itemsTotal = data.item_count || state.itemsTotal;
      state.itemsOffset = offset;
      state.hasMoreItems = data.has_more_items || false;
      renderItems();
    } finally {
      state.loadingDetail = false;
    }
  }

  async function loadMoreEvents() {
    if (state.loadingDetail) return;
    const taskId = state.selectedTaskId;
    if (!taskId) return;
    const offset = state.eventsOffset + 100;
    state.loadingDetail = true;
    try {
      const res = await fetch(`/api/tasks/${taskId}?items_limit=0&items_offset=0&events_limit=100&events_offset=${offset}`);
      if (!res.ok) return;
      const data = await res.json();
      state.events = state.events.concat(data.events || []);
      state.eventsTotal = data.event_count || state.eventsTotal;
      state.eventsOffset = offset;
      state.hasMoreEvents = data.has_more_events || false;
      renderEvents();
    } finally {
      state.loadingDetail = false;
    }
  }

  // 保留 loadTask 作为点击任务时的入口
  async function loadTask(id) {
    await loadTaskDetail(id, false);
  }

  function progressLine(label, current, total) {
    const percent = pct(current, total);
    return `<div><div>${esc(label)} ${percent}%</div><div class="progress"><div style="width:${percent}%"></div></div><div class="mono">${formatBytes(current)} / ${formatBytes(total)}</div></div>`;
  }

  function itemStatusGroup(item) {
    const status = String((item && item.status) || 'pending');
    if (status === 'success' || status === 'skipped' || status === 'failure') return status;
    if (['pending', 'running'].includes(status)) return 'running';
    return 'running';
  }

  function categorizedItems(items) {
    const groups = {
      running: [],
      success: [],
      skipped: [],
      failure: []
    };
    (items || []).forEach(item => {
      groups[itemStatusGroup(item)].push(item);
    });
    return groups;
  }

  function itemPageState(total) {
    const pages = Math.max(1, Math.ceil(total / ITEMS_PAGE_SIZE));
    const current = Math.min(Math.max(Number(state.itemPages[state.activeItemStatus] || 1), 1), pages);
    state.itemPages[state.activeItemStatus] = current;
    const startIndex = (current - 1) * ITEMS_PAGE_SIZE;
    const endIndex = Math.min(startIndex + ITEMS_PAGE_SIZE, total);
    return {current, pages, startIndex, endIndex};
  }

  function renderItemTabs(groups) {
    ITEM_STATUS_TABS.forEach(status => {
      const tab = $(`[data-item-tab="${status}"]`);
      const count = $(`[data-item-count="${status}"]`);
      if (!tab || !count) return;
      const active = state.activeItemStatus === status;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      count.textContent = groups[status].length;
    });
  }

  function renderItems(items) {
    items = items || state.items;
    const groups = categorizedItems(items);
    const activeItems = groups[state.activeItemStatus] || [];
    const page = itemPageState(activeItems.length);
    const visibleItems = activeItems.slice(page.startIndex, page.endIndex);
    renderItemTabs(groups);
    const retryButton = $('#retry-selected-failed');
    if (retryButton) {
      retryButton.disabled = !(state.selectedTaskId && groups.failure.length);
      retryButton.style.display = state.activeItemStatus === 'failure' ? 'inline-flex' : 'none';
    }
    const loadMoreHtml = state.hasMoreItems
      ? `<div class="load-more-row"><button type="button" class="load-more-btn" onclick="loadMoreItems()">
          ${esc(t('items.loadMore'))} (${state.itemsTotal - items.length} ${esc(t('items.remaining'))})
        </button></div>`
      : '';
    $('#items').innerHTML = (visibleItems.length ? visibleItems.map(item => `
      <div class="file-row">
        <div>
          <div>${esc(item.file_name || item.local_path || item.source_link || `#${item.source_message_id || item.id}`)}</div>
          <div class="mono">${esc(item.source_chat_id || '')} ${esc(item.source_message_id || '')}</div>
        </div>
        <div>${badge(item.status)}</div>
        ${progressLine(t('items.download'), item.download_current, item.download_total)}
        ${progressLine(t('items.upload'), item.upload_current, item.upload_total)}
      </div>
    `).join('') : `<div class="empty">${esc(t(`items.empty.${state.activeItemStatus}`))}</div>`) + loadMoreHtml;

    const range = activeItems.length
      ? interpolate(t('items.page.range'), {
        start: page.startIndex + 1,
        end: page.endIndex,
        total: activeItems.length
      })
      : interpolate(t('items.page.range'), {start: 0, end: 0, total: 0});
    $('#items-page-range').textContent = range;
    $('#items-page-summary').textContent = interpolate(t('items.page.status'), {
      page: page.current,
      pages: page.pages
    });
    $('#items-page-prev').disabled = page.current <= 1;
    $('#items-page-next').disabled = page.current >= page.pages;
  }

  function resetItemPages() {
    ITEM_STATUS_TABS.forEach(status => {
      state.itemPages[status] = 1;
    });
  }

  function switchItemTab(status) {
    if (!ITEM_STATUS_TABS.includes(status)) return;
    state.activeItemStatus = status;
    renderItems(state.items);
  }

  function renderEvents() {
    const events = state.events || [];
    const countText = state.eventsTotal > events.length
      ? `${events.length} / ${state.eventsTotal}`
      : String(events.length);
    $('#event-count').textContent = countText;
    const loadMoreHtml = state.hasMoreEvents
      ? `<div class="load-more-row"><button type="button" class="load-more-btn" onclick="loadMoreEvents()">
          ${esc(t('events.loadMore'))} (${state.eventsTotal - events.length} ${esc(t('events.remaining'))})
        </button></div>`
      : '';
    $('#events').innerHTML = (events.length ? events.map(event => `
      <div class="event">
        <time>${esc(event.created_at)}</time>
        <span>${esc(localizeEventLevel(event.level))}</span>
        <div>${esc(localizeEventMessage(event))}</div>
      </div>
    `).join('') : `<div class="empty">${esc(t('events.empty'))}</div>`) + loadMoreHtml;
  }

  function renderEventCount() {
    if (state.events && state.events.length) {
      const countText = state.eventsTotal > state.events.length
        ? `${state.events.length} / ${state.eventsTotal}`
        : String(state.events.length);
      $('#event-count').textContent = countText;
    }
  }

  function mergeRecentEvents(recentEvents) {
    const existingIds = new Set((state.events || []).map(function(e) { return e.id; }));
    var newEvents = recentEvents.filter(function(e) { return !existingIds.has(e.id); });
    if (!newEvents.length) return;
    var merged = state.events || [];
    newEvents.sort(function(a, b) { return (b.id || 0) - (a.id || 0); });
    merged = newEvents.concat(merged);
    merged.sort(function(a, b) { return (b.id || 0) - (a.id || 0); });
    var maxKeep = Math.max(state.eventsTotal || 0, merged.length, 200);
    state.events = merged.slice(0, maxKeep);
    renderEvents();
  }

  async function loadWatches() {
    const res = await fetch('/api/watches');
    const data = await res.json();
    state.watches = data.watches || [];
    renderWatches();
  }

  async function refreshWatchesAfterMutation() {
    try {
      await loadWatches();
    } catch (error) {
      console.warn('Failed to refresh watches after mutation.', error);
    }
  }

  function renderWatches() {
    const watches = state.watches || [];
    $('#watch-count').textContent = watches.length;
    $('#watches-empty').style.display = watches.length ? 'none' : 'block';
    $('#watches').innerHTML = watches.map(watch => {
      const sanitized = (watch.id || '').replace(/:/g, '_');
      const ec = watch.event_count || 0;
      const eventBadge = watch.type === 'forward' && ec ? ` <span class="badge info">${ec}</span>` : '';
      const rowClick = watch.type === 'forward' ? ` class="watch-row" onclick="toggleWatchEvents('${encodeURIComponent(watch.id)}')"` : '';
      const eventsRow = watch.type === 'forward' ? `
      <tr class="watch-events-row" id="watch-events-${sanitized}">
        <td colspan="5"><div class="watch-events-panel" id="watch-events-panel-${sanitized}"></div></td>
      </tr>` : '';
      return `<tr${rowClick}>
        <td>${esc(t(`watches.${watch.type}`))}</td>
        <td>${badge(watch.status || 'running')}${eventBadge}</td>
        <td class="mono">${esc(watch.source_link || '')}</td>
        <td class="mono">${esc(watch.target_link || '')}${watch.include_comment ? `<div>${esc(t('watches.includeComment'))}</div>` : ''}${watch.error_message ? `<div>${esc(watch.error_message)}</div>` : ''}</td>
        <td>
          ${watch.type === 'forward' ? `<button class="secondary" type="button" onclick="event.stopPropagation(); openEditWatchModal('${encodeURIComponent(watch.id)}','${encodeURIComponent(watch.source_link || '')}','${encodeURIComponent(watch.target_link || '')}','${watch.include_comment ? '1' : '0'}')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="watches.edit">${esc(t('watches.edit'))}</span>
          </button>` : ''}
          <button class="danger" type="button" onclick="event.stopPropagation(); deleteWatch('${encodeURIComponent(watch.id)}')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span data-i18n="watches.delete">${esc(t('watches.delete'))}</span>
          </button>
        </td>
      </tr>${eventsRow}`;
    }).join('');
  }

  async function toggleWatchEvents(encodedId) {
    const watchId = decodeURIComponent(encodedId);
    const sanitized = watchId.replace(/:/g, '_');
    const row = document.getElementById(`watch-events-${sanitized}`);
    if (!row) return;
    const isOpen = row.classList.contains('open');
    if (isOpen) {
      row.classList.remove('open');
      return;
    }
    row.classList.add('open');
    await loadWatchEvents(watchId, sanitized, 0);
  }
  window.toggleWatchEvents = toggleWatchEvents;

  async function loadWatchEvents(watchId, sanitized, offset) {
    const panel = document.getElementById(`watch-events-panel-${sanitized}`);
    if (!panel) return;
    if (offset === 0) panel.innerHTML = `<div class="watch-event-item">${esc(t('watches.eventLoading'))}</div>`;
    try {
      const res = await fetch(`/api/watches/${encodeURIComponent(watchId)}/events?limit=50&offset=${offset}`);
      const data = await res.json();
      if (!res.ok) { panel.innerHTML = `<div class="watch-event-item">${esc(data.error || 'Load failed')}</div>`; return; }
      const items = data.events || [];
      if (offset === 0) panel.innerHTML = '';
      if (!items.length && offset === 0) {
        panel.innerHTML = `<div class="watch-event-item">${esc(t('watches.noEvents'))}</div>`;
        return;
      }
      items.forEach(evt => {
        const time = new Date(evt.created_at + 'Z').toLocaleString();
        const statusClass = evt.status === 'success' ? 'success' : 'warning';
        const statusLabel = evt.status === 'success' ? t('watches.eventForwarded') : t('watches.eventSkipped');
        const div = document.createElement('div');
        div.className = 'watch-event-item';
        div.innerHTML = `<span class="watch-event-time">${esc(time)}</span>`
          + `<span class="watch-event-badge"><span class="badge ${statusClass}">${esc(statusLabel)}</span></span>`
          + `<span class="watch-event-info">${esc(evt.message)} ${esc(t('watches.source'))}: #${esc(String(evt.source_message_id || ''))} → ${esc(t('watches.target'))}: ${esc(evt.target_link || evt.target_chat_id || '')}</span>`;
        panel.appendChild(div);
      });
      if (data.has_more) {
        const btn = document.createElement('button');
        btn.className = 'watch-events-load-more small';
        btn.textContent = t('watches.loadMore');
        btn.onclick = () => loadWatchEvents(watchId, sanitized, offset + items.length);
        panel.appendChild(btn);
      }
    } catch (e) {
      panel.innerHTML = `<div class="watch-event-item">${esc(t('form.requestFailed'))}</div>`;
    }
  }

  async function deleteWatch(encodedId) {
    if (!window.confirm(t('watches.delete'))) return;
    const res = await fetch(`/api/watches/${encodedId}`, {method: 'DELETE'});
    const data = await res.json();
    if (!res.ok) {
      showNotice('#watch-download-notice', translateApiError(data), false);
      return;
    }
    showNotice('#watch-download-notice', t('watches.deleted'), true);
    await loadWatches();
  }
  window.deleteWatch = deleteWatch;

  let editingWatchId = null;

  function openEditWatchModal(encodedId, encodedSource, encodedTarget, includeCommentFlag) {
    editingWatchId = decodeURIComponent(encodedId);
    document.getElementById('watch-edit-type').value = t('watches.forward');
    document.getElementById('watch-edit-source').value = decodeURIComponent(encodedSource);
    document.getElementById('watch-edit-target').value = decodeURIComponent(encodedTarget);
    document.getElementById('watch-edit-include-comment').checked = includeCommentFlag === '1';
    document.getElementById('watch-edit-notice').style.display = 'none';
    document.getElementById('watch-edit-notice').textContent = '';
    document.getElementById('watch-edit-overlay').classList.add('open');
    document.getElementById('watch-edit-target').focus();
  }
  window.openEditWatchModal = openEditWatchModal;

  function closeEditWatchModal() {
    editingWatchId = null;
    document.getElementById('watch-edit-overlay').classList.remove('open');
  }
  window.closeEditWatchModal = closeEditWatchModal;

  async function submitEditWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    const target = document.getElementById('watch-edit-target').value.trim();
    const includeComment = document.getElementById('watch-edit-include-comment').checked;
    if (!target) {
      showEditWatchNotice(t('watches.targetRequired'), false);
      return;
    }
    await withLoading(button, async () => {
      try {
        await fetch(`/api/watches/${encodeURIComponent(editingWatchId)}`, {
          method: 'PUT',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({target_link: target, include_comment: includeComment})
        }).then(res => res.json().then(data => res.ok ? data : Promise.reject(data)));
      } catch (payload) {
        showEditWatchNotice(translateApiError(payload), false);
        return;
      }
      showEditWatchNotice(t('watches.updated'), true);
      closeEditWatchModal();
      await refreshWatchesAfterMutation();
    });
  }
  window.submitEditWatch = submitEditWatch;

  function showEditWatchNotice(message, success) {
    const el = document.getElementById('watch-edit-notice');
    el.textContent = message;
    el.className = 'notice is-visible' + (success ? ' ok' : '');
  }

  async function loadStatistics() {
    const res = await fetch('/api/statistics');
    const data = await res.json();
    state.statistics = data;
    renderStatistics();
  }

  function renderStatistics() {
    const tables = (state.statistics && state.statistics.tables) || {};
    const rows = ['link', 'count', 'upload'];
    $('#statistics').innerHTML = rows.map(type => {
      const table = tables[type] || {};
      const exportKey = type === 'link' ? 'statistics.exportLink' : type === 'count' ? 'statistics.exportCount' : 'statistics.exportUpload';
      return `
        <tr>
          <td>${esc(t(`statistics.${type}`))}</td>
          <td>${esc(table.available ? t('statistics.yes') : t('statistics.no'))}</td>
          <td class="mono">${esc(table.rows || 0)}</td>
          <td>
            <button type="button" onclick="exportTable('${type}')">
              <svg viewBox="0 0 24 24" fill="none"><path d="M12 5v10M8 11l4 4 4-4M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span>${esc(t(exportKey))}</span>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }

  async function exportTable(tableType) {
    try {
      const data = await postJson('/api/tables/export', {table_type: tableType});
      showNotice('#statistics-notice', interpolate(t('statistics.exported'), {directory: data.directory || ''}), true);
      await loadStatistics();
    } catch (payload) {
      showNotice('#statistics-notice', translateApiError(payload), false);
    }
  }
  window.exportTable = exportTable;

  async function postTaskAction(taskId, action) {
    const res = await fetch(`/api/tasks/${taskId}/${action}`, {method: 'POST'});
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  }

  async function runTaskAction(event, taskId, action) {
    event.stopPropagation();
    const button = event.currentTarget;
    await withLoading(button, async () => {
      try {
        await postTaskAction(taskId, action);
        showFormMessage(t('action.taskUpdated'), true);
        await loadTasks();
      } catch (payload) {
        showFormMessage(translateApiError(payload), false);
      }
    });
  }

  function pauseTask(event, taskId) {
    return runTaskAction(event, taskId, 'pause');
  }
  window.pauseTask = pauseTask;

  function resumeTask(event, taskId) {
    return runTaskAction(event, taskId, 'resume');
  }
  window.resumeTask = resumeTask;

  function retryFailedTask(event, taskId) {
    return runTaskAction(event, taskId, 'retry-failed');
  }
  window.retryFailedTask = retryFailedTask;

  async function deleteTask(event, taskId) {
    event.stopPropagation();
    const res = await fetch(`/api/tasks/${taskId}`, {method: 'DELETE'});
    if (res.ok && state.selectedTaskId === taskId) {
      state.selectedTaskId = null;
      state.items = [];
      state.events = [];
      resetItemPages();
      $('#selected-task').textContent = t('items.selectTask');
      renderItems();
      renderEvents();
    }
    await loadTasks();
  }
  window.deleteTask = deleteTask;

  function getPath(obj, path) {
    return path.split('.').reduce((cur, key) => cur && cur[key], obj);
  }

  function setPath(obj, path, value) {
    const parts = path.split('.');
    let cur = obj;
    parts.slice(0, -1).forEach(key => {
      cur[key] = cur[key] || {};
      cur = cur[key];
    });
    cur[parts[parts.length - 1]] = value;
  }

  async function loadSettings() {
    const res = await fetch('/api/settings');
    const data = await res.json();
    state.settings = data.settings || {};
    state.schema = data.schema || {};
    renderTypeSettings();
    fillSettingsForm();
  }

  function renderTypeSettings() {
    const downloadTypes = state.schema.download_type || [];
    const forwardTypes = state.schema.forward_type || [];
    const filterMediaTypes = (state.schema.message_filter && state.schema.message_filter.media_types) || forwardTypes;
    $('#download-type-settings').innerHTML = downloadTypes.map(type => `
      <label class="check-card"><input name="user.download_type" value="${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
    `).join('');
    var fwdEl = $('#forward-type-settings');
    if (fwdEl) {
      fwdEl.innerHTML = forwardTypes.map(type => `
        <label class="check-card"><input name="global.forward_type.${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
      `).join('');
    }
    // 消息过滤 — 媒体类型
    var filterEl = $('#filter-media-types');
    if (filterEl) {
      filterEl.innerHTML = filterMediaTypes.map(type => `
        <label class="check-card"><input name="global.message_filter.media_types.${esc(type)}" type="checkbox"><span>${esc(type)}</span></label>
      `).join('');
    }
  }

  function fillSettingsForm() {
    const form = $('#settings-form');
    Array.from(form.elements).forEach(el => {
      if (!el.name) return;
      if (el.name === 'user.download_type') {
        el.checked = (getPath(state.settings, 'user.download_type') || []).includes(el.value);
        return;
      }
      // 消息过滤 — 日期范围：timestamp → datetime-local
      if (el.name === 'global.message_filter.date_range.start_date' || el.name === 'global.message_filter.date_range.end_date') {
        const ts = getPath(state.settings, el.name);
        el.value = ts ? new Date(ts * 1000).toISOString().slice(0, 16) : '';
        return;
      }
      // 消息过滤 — 关键词：数组 → 逗号分隔字符串
      if (el.name === 'global.message_filter.keywords.words') {
        const words = getPath(state.settings, el.name);
        el.value = Array.isArray(words) ? words.join(', ') : '';
        return;
      }
      const value = getPath(state.settings, el.name);
      if (el.type === 'checkbox') {
        el.checked = Boolean(value);
      } else if (value && typeof value === 'object' && 'configured' in value) {
        el.placeholder = value.configured ? t('settings.secretConfigured') : t('settings.secretNotConfigured');
        el.value = '';
      } else {
        el.value = value ?? '';
      }
    });
  }

  function settingsPayload() {
    const payload = {};
    const downloadTypes = [];
    Array.from($('#settings-form').elements).forEach(el => {
      if (!el.name) return;
      if (el.name === 'user.download_type') {
        if (el.checked) downloadTypes.push(el.value);
        return;
      }
      // 消息过滤 — 日期范围：datetime-local → timestamp
      if (el.name === 'global.message_filter.date_range.start_date' || el.name === 'global.message_filter.date_range.end_date') {
        const v = el.value;
        setPath(payload, el.name, v ? (new Date(v).getTime() / 1000) : null);
        return;
      }
      // 消息过滤 — 关键词：逗号分隔字符串 → 数组
      if (el.name === 'global.message_filter.keywords.words') {
        const words = el.value ? el.value.split(',').map(function(s) { return s.trim(); }).filter(Boolean) : [];
        setPath(payload, el.name, words);
        return;
      }
      let value = el.type === 'checkbox' ? el.checked : el.value;
      if (el.type === 'number') value = value === '' ? null : Number(value);
      if (el.type === 'password' && value === '') return;
      setPath(payload, el.name, value);
    });
    setPath(payload, 'user.download_type', downloadTypes);
    return payload;
  }

  async function saveSettings(event) {
    event.preventDefault();
    const res = await fetch('/api/settings', {
      method: 'PATCH',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify(settingsPayload())
    });
    const data = await res.json();
    const notice = $('#settings-notice');
    notice.style.display = 'block';
    notice.classList.toggle('ok', res.ok);
    notice.textContent = res.ok ? t('settings.saved') : translateApiError(data, 'error.update_settings_failed');
    if (res.ok) {
      state.settings = data.settings || {};
      state.schema = data.schema || state.schema;
      fillSettingsForm();
    }
  }

  async function createDownloadWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const sourceLinks = new FormData(event.currentTarget)
        .get('source_links')
        .split(/\r?\n/)
        .map(value => value.trim())
        .filter(Boolean);
      try {
        await postJson('/api/watches', {type: 'download', source_links: sourceLinks});
      } catch (payload) {
        showNotice('#watch-download-notice', translateApiError(payload), false);
        return;
      }
      showNotice('#watch-download-notice', t('watches.created'), true);
      event.currentTarget.reset();
      await refreshWatchesAfterMutation();
    });
  }

  async function createForwardWatch(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      try {
        await postJson('/api/watches', {
          type: 'forward',
          source_link: form.get('source_link'),
          target_link: form.get('target_link'),
          include_comment: Boolean(form.get('include_comment'))
        });
      } catch (payload) {
        showNotice('#watch-forward-notice', translateApiError(payload), false);
        return;
      }
      showNotice('#watch-forward-notice', t('watches.created'), true);
      event.currentTarget.reset();
      await refreshWatchesAfterMutation();
    });
  }

  async function createChannelDownload(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      const downloadType = Array.from(event.currentTarget.querySelectorAll('input[name="download_type"]:checked')).map(el => el.value);
      const keywords = String(form.get('keywords') || '').split(',').map(value => value.trim()).filter(Boolean);
      try {
        await postJson('/api/channel-downloads', {
          chat_link: form.get('chat_link'),
          date_range: {
            start_date: form.get('start_date') || null,
            end_date: form.get('end_date') || null
          },
          download_type: downloadType,
          keywords,
          include_comment: Boolean(form.get('include_comment'))
        });
        showNotice('#channel-download-notice', t('channel.accepted'), true);
      } catch (payload) {
        showNotice('#channel-download-notice', translateApiError(payload), false);
      }
    });
  }

  async function createUpload(event) {
    event.preventDefault();
    const button = event.submitter;
    await withLoading(button, async () => {
      const form = new FormData(event.currentTarget);
      try {
        await postJson('/api/uploads', {
          path: form.get('path'),
          target_link: form.get('target_link'),
          recursive: Boolean(form.get('recursive'))
        });
        showNotice('#upload-notice', t('uploads.accepted'), true);
      } catch (payload) {
        showNotice('#upload-notice', translateApiError(payload), false);
      }
    });
  }

  async function loadRecords() {
    const res = await fetch('/api/download-records');
    const data = await res.json();
    state.records = data.records || [];
    renderRecords();
  }

  function renderRecords() {
    const records = state.records || [];
    $('#record-count').textContent = records.length;
    $('#records-empty').style.display = records.length ? 'none' : 'block';
    $('#records').innerHTML = records.map(record => `
      <tr>
        <td class="mono">${esc(record.source_chat_id)}</td>
        <td class="mono">${esc(record.source_message_id)}</td>
        <td><div>${esc(record.file_name || '')}</div><div class="mono">${esc(record.local_path || '')}</div></td>
        <td>${formatBytes(record.file_size)}</td>
        <td class="mono">${esc(record.updated_at || record.downloaded_at)}</td>
      </tr>
    `).join('');
  }

  /* ====== 退出登录 ====== */
  var btnLogout = $('#btn-logout');
  if (btnLogout) btnLogout.addEventListener('click', handleLogout);
  var mobBtnLogout = $('#mob-btn-logout');
  if (mobBtnLogout) mobBtnLogout.addEventListener('click', handleLogout);
