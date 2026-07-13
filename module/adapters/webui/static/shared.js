/* TRMD WebUI - Shared JavaScript (i18n + utilities) */

const i18n = {
  zh: {
    'app.title': 'TRMD · 转存控制台',
    'app.subtitle': '转存控制台',
    'nav.section.main': '主要功能',
    'nav.section.monitor': '监控与数据',
    'nav.section.system': '系统',
    'nav.transfers': '转存任务',
    'nav.watches': '实时监听',
    'nav.downloadsUploads': '下载与上传',
    'nav.statistics': '统计面板',
    'nav.settings': '系统设置',
    'nav.records': '下载记录',
    'nav.media': '媒体管理',
    'nav.systemLogs': '系统日志',
    'nav.profile': '我的',
    'nav.logout': '退出登录',
    'side.failed': '失败项',
    'side.status': '系统运行中',
    'hero.title': '转存控制台',
    'hero.body': '管理 Telegram 内容转存任务 — 实时监控、批量操作、智能过滤',
    'stats.total': '总任务',
    'stats.success': '已完成',
    'stats.running': '运行中',
    'stats.failed': '失败项',
    'stats.uploadSpeed': '实时上传网速',
    'stats.downloadSpeed': '实时下载网速',
    'stats.diskFree': '硬盘剩余空间',
    'action.refresh': '刷新',
    'new.title': '新建转存',
    'new.source': '来源链接',
    'new.target': '目标',
    'new.targetProfile': '目标配置',
    'profile.pikpak': 'PikPak 文档转存',
    'profile.generic': '通用 Telegram 目标',
    'new.startId': '起始 ID',
    'new.endId': '结束 ID',
    'new.optional': '可选',
    'new.includeComment': '包含评论区',
    'new.resolveDeepLink': '深链取片',
    'new.resolveDeepLinkHint': '勾选后，对白名单 bot 的 ?start= 链接取片再转存；需先在系统设置填写白名单。',
    'new.hint': '单条消息链接可留空。频道或群链接不填 ID 时会自动探测可访问范围，也可手动指定起止 ID。',
    'new.create': '创建任务',
    'watches.title': '活跃监听',
    'watches.downloadTitle': '监听下载',
    'watches.downloadMeta': '新消息自动下载',
    'watches.forwardTitle': '监听转发',
    'watches.forwardMeta': '新消息自动转发',
    'watches.type': '类型',
    'watches.source': '来源频道',
    'watches.target': '目标频道',
    'watches.sources': '来源频道（每行一个）',
    'watches.includeComment': '包含评论区',
    'watches.resolveDeepLink': '深链取片',
    'watches.resolveDeepLinkHint': '勾选后，对白名单 bot 的 ?start= 链接取片再转存；需先在系统设置填写白名单。',
    'watches.createDownload': '新增监听下载',
    'watches.createForward': '新增监听转发',
    'watches.empty': '还没有实时监听。',
    'watches.delete': '移除',
    'watches.edit': '编辑',
    'watches.download': '监听下载',
    'watches.forward': '监听转发',
    'watches.created': '实时监听已创建。',
    'watches.deleted': '实时监听已移除。',
    'watches.updated': '实时监听已更新。',
    'watches.events': '转发记录',
    'watches.todayEvents': '今日',
    'watches.allEvents': '完整记录',
    'watches.totalEvents': '总数',
    'watches.history': '记录',
    'watches.historyTitle': '监听转发记录',
    'watches.downloadRecords': '下载记录',
    'watches.downloadRecordsTitle': '监听下载记录',
    'watches.downloadRecordsEmpty': '暂无下载记录',
    'watches.downloadActive': '进行中',
    'watches.downloadCompleted': '已完成',
    'watches.downloadFailed': '失败',
    'watches.pageInfo': '第 {page} / {pages} 页 · 共 {total} 条',
    'watches.noEvents': '暂无转发记录',
    'watches.eventForwarded': '转发成功',
    'watches.eventFilterKeyword': '命中过滤关键词',
    'watches.eventFailed': '转发失败',
    'watches.eventSkipped': '已过滤',
    'watches.badgeSuccess': '成功',
    'watches.badgeFiltered': '已过滤',
    'watches.badgeFailure': '失败',
    'watches.task': '任务',
    'watches.moreActions': '更多操作',
    'watches.filterAll': '全部',
    'watches.filterSuccess': '成功',
    'watches.filterFiltered': '已过滤',
    'watches.filterFailure': '失败',
    'watches.detailExpandReason': '点击展开原因',
    'watches.eventLoading': '加载中…',
    'watches.loadMore': '加载更多',
    'watches.targetRequired': '目标频道为必填项。',
    'watches.sourceRequired': '来源频道为必填项。',
    'watches.deferredComments': '待抓评论区',
    'watches.noDeferredComments': '暂无待抓评论区任务',
    'watches.deferredDue': '计划执行',
    'watches.deferredRunNow': '立即执行',
    'watches.deferredCancel': '取消',
    'watches.deferredRetry': '重试',
    'watches.deferredPending': '等待中',
    'watches.deferredRunning': '执行中',
    'watches.deferredDone': '已完成',
    'watches.deferredCancelled': '已取消',
    'watches.deferredFailure': '失败',
    'action.cancel': '取消',
    'action.save': '保存',
    // merged downloads & uploads page
    'dl.title': '频道下载',
    'dl.meta': '从 Telegram 频道拉取文件',
    'dl.link': '频道链接',
    'dl.startDate': '起始时间',
    'dl.endDate': '结束时间',
    'dl.keywords': '关键词',
    'dl.keywordsPlaceholder': '逗号分隔，可留空',
    'dl.types': '下载类型',
    'dl.includeComment': '包含评论区',
    'dl.create': '创建下载任务',
    'dl.accepted': '频道下载任务已创建。',
    'dl.uploadTitle': '本地上传',
    'dl.uploadMeta': '推送到 Telegram 频道',
    'dl.uploadPath': '本地路径',
    'dl.uploadTarget': '目标频道',
    'dl.recursive': '递归上传文件夹',
    'dl.uploadPlaceholder': '占位区，待后续开发',
    'dl.createUpload': '创建上传任务',
    'dl.uploadAccepted': '上传任务已创建。',
    'dl.history': '操作历史',
    'dl.historyId': 'ID',
    'dl.historyType': '类型',
    'dl.historyDetail': '详情',
    'dl.historyStatus': '状态',
    'dl.historyError': '错误信息',
    'dl.historyTime': '创建时间',
    'dl.historyEmpty': '还没有下载或上传操作记录。',
    'dl.typeDownload': '频道下载',
    'dl.typeUpload': '本地上传',
    'statistics.title': '统计与导出',
    'statistics.table': '表格',
    'statistics.available': '可用',
    'statistics.rows': '行数',
    'statistics.yes': '是',
    'statistics.no': '否',
    'statistics.link': '链接统计表',
    'statistics.count': '计数统计表',
    'statistics.upload': '上传统计表',
    'statistics.exportLink': '导出链接统计表',
    'statistics.exportCount': '导出计数统计表',
    'statistics.exportUpload': '导出上传统计表',
    'statistics.exportChannel': '导出频道报表',
    'statistics.exported': '统计表已导出。',
    'statistics.kpiLinks': '监控链接',
    'statistics.kpiChannels': '频道数',
    'statistics.kpiDownloads': '条目总数',
    'statistics.kpiIssues': '失败 / 跳过',
    'statistics.kpiUploads': '上传任务',
    'statistics.kpiSuccessRate': '成功率 {rate}%',
    'statistics.kpiSuccessRateLabel': '成功率',
    'statistics.kpiUploadDone': '已完成 {count}',
    'statistics.mediaChartTitle': '媒体下载分布',
    'statistics.mediaChartMeta': '近 7 天 · 按频道 · 成功 / 失败 / 跳过',
    'statistics.linkChartTitle': '链接完成率',
    'statistics.linkChartMeta': '按来源链接',
    'statistics.tabLink': '链接统计',
    'statistics.tabCount': '计数统计',
    'statistics.tabUpload': '上传统计',
    'statistics.tabChannel': '按频道',
    'statistics.exportCurrent': '导出当前报表',
    'statistics.empty': '暂无统计数据。',
    'statistics.otherChannel': '其他',
    'statistics.legendSuccess': '成功',
    'statistics.legendFailure': '失败',
    'statistics.legendSkip': '跳过',
    'statistics.colLink': '链接',
    'statistics.colCompletion': '完成率',
    'statistics.colFiles': '文件数',
    'statistics.colStatus': '状态',
    'statistics.colError': '错误',
    'statistics.colType': '类型',
    'statistics.colSuccess': '成功',
    'statistics.colFailure': '失败',
    'statistics.colSkip': '跳过',
    'statistics.colTotal': '合计',
    'statistics.colSuccessRate': '成功率',
    'statistics.colChannel': '频道',
    'statistics.colFile': '文件',
    'statistics.colSize': '大小',
    'statistics.statusComplete': '完成',
    'statistics.statusProgress': '进行中',
    'statistics.statusError': '异常',
    'statistics.donutAvg': '平均完成',
    'statistics.donutComplete': '已完成',
    'statistics.donutProgress': '进行中',
    'statistics.donutError': '有错误',
    'statistics.media.video': '视频',
    'statistics.media.photo': '图片',
    'statistics.media.document': '文档',
    'statistics.media.audio': '音频',
    'statistics.media.voice': '语音',
    'statistics.media.animation': '动图',
    'statistics.media.video_note': '视频便笺',
    'statistics.upload.pending': '等待中',
    'statistics.upload.uploading': '上传中',
    'statistics.upload.success': '已完成',
    'statistics.upload.failure': '失败',
    'statistics.upload.sent': '已发送',
    'tasks.title': '转存任务列表',
    'tasks.notSynced': '尚未同步',
    'tasks.id': 'ID',
    'tasks.status': '状态',
    'tasks.source': '来源',
    'tasks.target': '目标',
    'tasks.progress': '进度',
    'tasks.progressIds': 'ID {done}/{total}',
    'tasks.progressCurrentId': 'ID {id}',
    'tasks.progressVideosCaptured': '已捕获 {count} 个视频',
    'tasks.progressVideoIndex': '正在处理第 {index} 个',
    'tasks.progressDownloading': '下载 {name} · {progress}',
    'tasks.actions': '操作',
    'tasks.pause': '暂停',
    'tasks.resume': '继续',
    'tasks.retryFailed': '重试失败',
    'tasks.delete': '删除',
    'tasks.empty': '还没有转存任务。',
    'tasks.emptyHint': '创建任务后在此查看进度',
    'items.title': '文件进度',
    'items.selectTask': '选择一个任务查看详情',
    'items.empty': '该任务还没有文件记录。',
    'items.colFile': '文件',
    'items.colSize': '大小',
    'items.colProgress': '进度/速度',
    'items.colSource': '来源',
    'items.colError': '原因',
    'items.colStatus': '状态',
    'items.tab.running': '进行中',
    'items.tab.success': '已完成',
    'items.tab.skipped': '跳过',
    'items.tab.failure': '失败',
    'items.retryFailed': '重试失败项',
    'items.page.previous': '上一页',
    'items.page.next': '下一页',
    'pagination.pageInfo': '第 {page} / {pages} 页 · 共 {total} 条',
    'events.title': '最近事件',
    'events.empty': '没有事件记录。',
    'events.loadMore': '加载更多',
    'settings.title': '系统设置',
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
    'settings.commentDelayMinutes': '评论区延迟抓取（分钟）',
    'settings.commentDelayHint': '监听转发开启包含评论区时，主贴立刻转发，评论区延迟该分钟数后再抓取一次。0 表示立刻抓取。',
    'settings.deepLinkTitle': '深链取片',
    'settings.deepLinkWhitelist': '资源 bot 白名单',
    'settings.deepLinkWhitelistHint': '每行一个 bot 用户名（可带 @）。仅名单内的 t.me/<bot>?start= 会触发取片。留空且任务未勾选时功能关闭。',
    'settings.deepLinkTimeout': '取片超时（秒）',
    'settings.deepLinkMinInterval': '取片最小间隔（秒）',
    'settings.deepLinkMinIntervalHint': '两次 StartBot 取片之间的最小冷却时间，用于降低 Telegram 限流。0 表示不主动冷却（仍会遵守 FloodWait）。',
    'settings.sensitive': '账号与代理',
    'settings.proxyPassword': '代理密码',
    'settings.secretConfigured': '已配置，如需更换请填写',
    'settings.downloadTypes': '下载类型',
    'settings.downloadTypesHint': '（勾选 = 允许下载，未勾选的类型将被忽略）',
    'settings.forwardTypes': '转发类型',
    'settings.forwardTypesHint': '（勾选 = 允许转发，未勾选的类型将被忽略）',
    'settings.messageFilter': '消息过滤',
    'settings.mediaTypes': '媒体类型',
    'settings.mediaTypesHint': '（勾选 = 允许处理，未勾选的类型将被过滤）',
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
    'records.title': '下载记录',
    'records.chat': '频道 ID',
    'records.message': '消息 ID',
    'records.file': '文件',
    'records.size': '大小',
    'records.updated': '更新时间',
    'records.empty': '还没有下载成功记录。',
    'records.clear': '清空记录',
    'records.confirmClear': '确定清空全部下载记录？此操作不可撤销。',
    'records.cleared': '下载记录已清空。',
    'systemLogs.title': '系统日志',
    'systemLogs.retentionHint': '全链路调试日志，自动保留 {days} 天',
    'systemLogs.filterAllCategories': '全部分类',
    'systemLogs.filterAllLevels': '全部级别',
    'systemLogs.categoryWatch': '监听',
    'systemLogs.categoryFilter': '过滤',
    'systemLogs.categoryForward': '转发',
    'systemLogs.categoryTransfer': '下载上传',
    'systemLogs.categoryArchive': '归档',
    'systemLogs.todayOnly': '仅今天',
    'systemLogs.autoRefresh': '自动刷新',
    'systemLogs.copyPage': '复制本页',
    'systemLogs.downloadAll': '下载日志',
    'systemLogs.downloading': '下载中…',
    'systemLogs.downloadEmpty': '没有可下载的日志。',
    'systemLogs.downloadFailed': '日志下载失败。',
    'systemLogs.copied': '已复制本页日志到剪贴板。',
    'systemLogs.detailTitle': '日志详情',
    'systemLogs.time': '时间',
    'systemLogs.level': '级别',
    'systemLogs.category': '分类',
    'systemLogs.stage': '阶段',
    'systemLogs.message': '消息',
    'systemLogs.context': '上下文',
    'systemLogs.details': '详情数据',
    'systemLogs.sourceChat': '来源会话',
    'systemLogs.sourceMessage': '来源消息',
    'systemLogs.target': '目标',
    'systemLogs.empty': '暂无系统日志。',
    'systemLogs.trace': '链路',
    'systemLogs.watch': '监听',
    'form.createFailed': '创建失败。',
    'form.requestFailed': '请求失败。',
    'form.creatingTransfer': '正在分析来源消息范围…',
    'form.creatingTransferShort': '分析中…',
    'form.createSuccess': '任务已创建，正在排队处理。',
    'media.title': '媒体管理',
    'media.scan': '扫描可清理文件',
    'media.scanning': '正在扫描…',
    'media.totalFiles': '可清理文件',
    'media.totalSize': '总大小',
    'media.retentionDays': '保留天数',
    'media.transferItems': '转存任务文件',
    'media.orphanFiles': '遗留文件',
    'media.file': '文件',
    'media.size': '大小',
    'media.status': '状态',
    'media.source': '来源',
    'media.path': '路径',
    'media.mtime': '最后修改',
    'media.cleanup': '清理选中文件',
    'media.cleaning': '清理中…',
    'media.selected': '已选',
    'media.files': '个文件',
    'media.noSelection': '请先选择要清理的文件。',
    'media.confirmCleanup': '确定要删除选中的文件吗？此操作不可撤销。',
    'media.cleanupDone': '清理完成：已删除 {count} 个文件 ({size})。',
    'media.cleanupHistory': '清理历史',
    'media.empty': '没有可清理文件',
    'media.reason': '原因',
    'media.time': '时间',
    'media.filterByTask': '按任务筛选：',
    'media.allTasks': '全部任务',
    'status.pending': '排队中',
    'status.running': '运行中',
    'status.paused': '已暂停',
    'status.success': '已完成',
    'status.failure': '失败',
    'status.skipped': '跳过',
    'event.level.info': '信息',
    'event.level.warning': '警告',
    'event.level.error': '错误',
    'error.auth_required': '需要登录。',
    'error.invalid_task_id': '任务 ID 无效。',
    'error.task_not_found': '找不到任务。',
    'error.source_link_required': '请填写来源链接。',
    'error.target_link_required': '请填写目标链接。',
    'error.range_ids_required': '起始 ID 和结束 ID 必须同时填写。',
    'error.range_end_before_start': '结束 ID 必须大于或等于起始 ID。',
    'error.invalid_payload': '请求内容无效。',
  },
  en: {
    'app.subtitle': 'Transfer Console',
    'nav.section.main': 'Main',
    'nav.section.monitor': 'Monitor & Data',
    'nav.section.system': 'System',
    'nav.transfers': 'Transfer Tasks',
    'nav.watches': 'Live Watches',
    'nav.downloadsUploads': 'DL & Upload',
    'nav.statistics': 'Statistics',
    'nav.settings': 'Settings',
    'nav.records': 'Records',
    'nav.media': 'Media Mgmt',
    'nav.systemLogs': 'System Logs',
    'nav.profile': 'Me',
    'nav.logout': 'Log Out',
    'side.failed': 'Failed items',
    'side.status': 'System running',
    'hero.title': 'Transfer Console',
    'hero.body': 'Manage Telegram content transfer tasks — live monitoring, batch operations, smart filtering',
    'stats.total': 'Total Tasks',
    'stats.success': 'Completed',
    'stats.running': 'Running',
    'stats.failed': 'Failed Items',
    'stats.uploadSpeed': 'Upload Speed',
    'stats.downloadSpeed': 'Download Speed',
    'stats.diskFree': 'Free Disk Space',
    'action.refresh': 'Refresh',
    'new.title': 'New Transfer',
    'new.source': 'Source link',
    'new.target': 'Target',
    'new.targetProfile': 'Target profile',
    'profile.pikpak': 'PikPak Document Transfer',
    'profile.generic': 'Generic Telegram Target',
    'new.startId': 'Start ID',
    'new.endId': 'End ID',
    'new.optional': 'Optional',
    'new.includeComment': 'Include comments',
    'new.resolveDeepLink': 'Resolve deep links',
    'new.resolveDeepLinkHint': 'When checked, fetch media from whitelisted bot ?start= links before transfer. Configure the whitelist in Settings first.',
    'new.hint': 'Leave IDs empty for message links. Channel links auto-detect range if IDs omitted.',
    'new.create': 'Create task',
    'watches.title': 'Active Watches',
    'watches.downloadTitle': 'Download Watch',
    'watches.downloadMeta': 'Auto-download new messages',
    'watches.forwardTitle': 'Forward Watch',
    'watches.forwardMeta': 'Auto-forward new messages',
    'watches.type': 'Type',
    'watches.source': 'Source channel',
    'watches.target': 'Target channel',
    'watches.sources': 'Source channels (one per line)',
    'watches.includeComment': 'Include comments',
    'watches.resolveDeepLink': 'Resolve deep links',
    'watches.resolveDeepLinkHint': 'When checked, fetch media from whitelisted bot ?start= links before transfer. Configure the whitelist in Settings first.',
    'watches.createDownload': 'Add download watch',
    'watches.createForward': 'Add forward watch',
    'watches.empty': 'No live watches yet.',
    'watches.delete': 'Remove',
    'watches.edit': 'Edit',
    'watches.download': 'Download watch',
    'watches.forward': 'Forward watch',
    'watches.created': 'Live watch created.',
    'watches.deleted': 'Live watch removed.',
    'watches.updated': 'Live watch updated.',
    'watches.events': 'Forward log',
    'watches.todayEvents': 'Today',
    'watches.allEvents': 'Full log',
    'watches.totalEvents': 'Total',
    'watches.history': 'Log',
    'watches.historyTitle': 'Forward watch log',
    'watches.downloadRecords': 'Downloads',
    'watches.downloadRecordsTitle': 'Watch download records',
    'watches.downloadRecordsEmpty': 'No download records yet.',
    'watches.downloadActive': 'In progress',
    'watches.downloadCompleted': 'Completed',
    'watches.downloadFailed': 'Failed',
    'watches.pageInfo': 'Page {page} / {pages} · {total} total',
    'watches.noEvents': 'No forwarding events yet.',
    'watches.eventForwarded': 'Forwarded',
    'watches.eventFilterKeyword': 'Filter keyword hit',
    'watches.eventFailed': 'Forward failed',
    'watches.eventSkipped': 'Filtered',
    'watches.badgeSuccess': 'OK',
    'watches.badgeFiltered': 'Filtered',
    'watches.badgeFailure': 'Failed',
    'watches.task': 'Task',
    'watches.moreActions': 'More actions',
    'watches.filterAll': 'All',
    'watches.filterSuccess': 'Success',
    'watches.filterFiltered': 'Filtered',
    'watches.filterFailure': 'Failure',
    'watches.detailExpandReason': 'Tap to expand reason',
    'watches.eventLoading': 'Loading…',
    'watches.loadMore': 'Load more',
    'watches.targetRequired': 'Target link is required.',
    'watches.sourceRequired': 'Source link is required.',
    'watches.deferredComments': 'Deferred comments',
    'watches.noDeferredComments': 'No deferred comment jobs',
    'watches.deferredDue': 'Due',
    'watches.deferredRunNow': 'Run now',
    'watches.deferredCancel': 'Cancel',
    'watches.deferredRetry': 'Retry',
    'watches.deferredPending': 'Pending',
    'watches.deferredRunning': 'Running',
    'watches.deferredDone': 'Done',
    'watches.deferredCancelled': 'Cancelled',
    'watches.deferredFailure': 'Failed',
    'action.cancel': 'Cancel',
    'action.save': 'Save',
    // merged downloads & uploads page
    'dl.title': 'Channel Download',
    'dl.meta': 'Pull files from Telegram channels',
    'dl.link': 'Channel link',
    'dl.startDate': 'Start time',
    'dl.endDate': 'End time',
    'dl.keywords': 'Keywords',
    'dl.keywordsPlaceholder': 'Comma-separated, optional',
    'dl.types': 'Download types',
    'dl.includeComment': 'Include comments',
    'dl.create': 'Create download',
    'dl.accepted': 'Channel download task created.',
    'dl.uploadTitle': 'Local Upload',
    'dl.uploadMeta': 'Push files to Telegram channel',
    'dl.uploadPath': 'Local path',
    'dl.uploadTarget': 'Target channel',
    'dl.recursive': 'Upload folder recursively',
    'dl.uploadPlaceholder': 'Placeholder, future work',
    'dl.createUpload': 'Create upload',
    'dl.uploadAccepted': 'Upload task created.',
    'dl.history': 'Operation History',
    'dl.historyId': 'ID',
    'dl.historyType': 'Type',
    'dl.historyDetail': 'Detail',
    'dl.historyStatus': 'Status',
    'dl.historyError': 'Error',
    'dl.historyTime': 'Created',
    'dl.historyEmpty': 'No download or upload operations yet.',
    'dl.typeDownload': 'Channel DL',
    'dl.typeUpload': 'Local Upload',
    'statistics.title': 'Statistics & Export',
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
    'statistics.exportChannel': 'Export channel report',
    'statistics.exported': 'Table exported.',
    'statistics.kpiLinks': 'Tracked links',
    'statistics.kpiChannels': 'Channels',
    'statistics.kpiDownloads': 'Total items',
    'statistics.kpiIssues': 'Failed / skipped',
    'statistics.kpiUploads': 'Upload tasks',
    'statistics.kpiSuccessRate': 'Success rate {rate}%',
    'statistics.kpiSuccessRateLabel': 'Success rate',
    'statistics.kpiUploadDone': 'Completed {count}',
    'statistics.mediaChartTitle': 'Media download breakdown',
    'statistics.mediaChartMeta': 'Last 7 days · by channel · success / failure / skip',
    'statistics.linkChartTitle': 'Link completion',
    'statistics.linkChartMeta': 'By source link',
    'statistics.tabLink': 'Links',
    'statistics.tabCount': 'Counts',
    'statistics.tabUpload': 'Uploads',
    'statistics.tabChannel': 'By channel',
    'statistics.exportCurrent': 'Export current report',
    'statistics.empty': 'No statistics yet.',
    'statistics.otherChannel': 'Other',
    'statistics.legendSuccess': 'Success',
    'statistics.legendFailure': 'Failure',
    'statistics.legendSkip': 'Skipped',
    'statistics.colLink': 'Link',
    'statistics.colCompletion': 'Completion',
    'statistics.colFiles': 'Files',
    'statistics.colStatus': 'Status',
    'statistics.colError': 'Error',
    'statistics.colType': 'Type',
    'statistics.colSuccess': 'Success',
    'statistics.colFailure': 'Failure',
    'statistics.colSkip': 'Skipped',
    'statistics.colTotal': 'Total',
    'statistics.colSuccessRate': 'Success rate',
    'statistics.colChannel': 'Channel',
    'statistics.colFile': 'File',
    'statistics.colSize': 'Size',
    'statistics.statusComplete': 'Complete',
    'statistics.statusProgress': 'In progress',
    'statistics.statusError': 'Error',
    'statistics.donutAvg': 'Avg completion',
    'statistics.donutComplete': 'Completed',
    'statistics.donutProgress': 'In progress',
    'statistics.donutError': 'With errors',
    'statistics.media.video': 'Video',
    'statistics.media.photo': 'Photo',
    'statistics.media.document': 'Document',
    'statistics.media.audio': 'Audio',
    'statistics.media.voice': 'Voice',
    'statistics.media.animation': 'Animation',
    'statistics.media.video_note': 'Video note',
    'statistics.upload.pending': 'Pending',
    'statistics.upload.uploading': 'Uploading',
    'statistics.upload.success': 'Completed',
    'statistics.upload.failure': 'Failed',
    'statistics.upload.sent': 'Sent',
    'tasks.title': 'Transfer Tasks',
    'tasks.notSynced': 'Not synced',
    'tasks.id': 'ID',
    'tasks.status': 'Status',
    'tasks.source': 'Source',
    'tasks.target': 'Target',
    'tasks.progress': 'Progress',
    'tasks.progressIds': 'ID {done}/{total}',
    'tasks.progressCurrentId': 'ID {id}',
    'tasks.progressVideosCaptured': '{count} videos captured',
    'tasks.progressVideoIndex': 'Processing #{index}',
    'tasks.progressDownloading': 'Download {name} · {progress}',
    'tasks.actions': 'Actions',
    'tasks.pause': 'Pause',
    'tasks.resume': 'Resume',
    'tasks.retryFailed': 'Retry failed',
    'tasks.delete': 'Delete',
    'tasks.empty': 'No transfer tasks yet.',
    'tasks.emptyHint': 'Create a task above to track progress here',
    'items.title': 'File Progress',
    'items.selectTask': 'Select a task to view details',
    'items.empty': 'No file records for this task yet.',
    'items.colFile': 'File',
    'items.colSize': 'Size',
    'items.colProgress': 'Progress / Speed',
    'items.colSource': 'Source',
    'items.colError': 'Reason',
    'items.colStatus': 'Status',
    'items.tab.running': 'Running',
    'items.tab.success': 'Completed',
    'items.tab.skipped': 'Skipped',
    'items.tab.failure': 'Failed',
    'items.retryFailed': 'Retry failed',
    'items.page.previous': 'Prev',
    'items.page.next': 'Next',
    'pagination.pageInfo': 'Page {page} / {pages} · {total} total',
    'events.title': 'Recent Events',
    'events.empty': 'No events.',
    'events.loadMore': 'Load more',
    'settings.title': 'Settings',
    'settings.safeNote': 'Sensitive fields show configured status only',
    'settings.paths': 'Paths & Tasks',
    'settings.saveDirectory': 'Save directory',
    'settings.tempDirectory': 'Temp directory',
    'settings.sessionDirectory': 'Session directory',
    'settings.maxDownload': 'Max download tasks',
    'settings.maxUpload': 'Max upload tasks',
    'settings.retryDownload': 'Download retries',
    'settings.retryUpload': 'Upload retries',
    'settings.pikpakMaxFileSize': 'PikPak max file size (bytes)',
    'settings.pikpakArchive': 'PikPak Archive',
    'settings.pikpakArchiveEnable': 'Archive by source channel',
    'settings.pikpakArchiveRemote': 'rclone remote',
    'settings.pikpakArchiveSource': 'Ingest directory',
    'settings.pikpakArchiveRoot': 'Archive root',
    'settings.pikpakArchivePoll': 'Poll seconds',
    'settings.pikpakArchiveInterval': 'Poll interval',
    'settings.pikpakArchiveWindow': 'Match window seconds',
    'settings.behavior': 'Behavior',
    'settings.notice': 'Bot notifications',
    'settings.shutdown': 'Shutdown on exit',
    'settings.downloadUpload': 'Download-then-upload for restricted',
    'settings.uploadDelete': 'Delete local after upload',
    'settings.pendingLimit': 'Upload queue limit',
    'settings.commentDelayMinutes': 'Comment capture delay (minutes)',
    'settings.commentDelayHint': 'For live forward with comments: forward the post immediately, then capture comments once after this delay. 0 means capture immediately.',
    'settings.deepLinkTitle': 'Deep link resolve',
    'settings.deepLinkWhitelist': 'Resource bot whitelist',
    'settings.deepLinkWhitelistHint': 'One bot username per line (optional @). Only t.me/<bot>?start= links for listed bots are resolved. Empty whitelist and unchecked tasks keep the feature off.',
    'settings.deepLinkTimeout': 'Resolve timeout (seconds)',
    'settings.deepLinkMinInterval': 'Min interval between resolves (seconds)',
    'settings.deepLinkMinIntervalHint': 'Minimum cooldown between StartBot calls to reduce Telegram flood waits. 0 disables proactive cooldown (FloodWait is still respected).',
    'settings.sensitive': 'Account & Proxy',
    'settings.proxyPassword': 'Proxy password',
    'settings.secretConfigured': 'Configured, fill to replace',
    'settings.downloadTypes': 'Download Types',
    'settings.downloadTypesHint': '(Check = allow download, unchecked types will be ignored)',
    'settings.forwardTypes': 'Forward Types',
    'settings.forwardTypesHint': '(Check = allow forward, unchecked types will be ignored)',
    'settings.messageFilter': 'Message Filter',
    'settings.mediaTypes': 'Media types',
    'settings.mediaTypesHint': '(Check = allow, unchecked types will be filtered out)',
    'settings.dateRange': 'Date range',
    'settings.keywords': 'Keywords',
    'settings.enabled': 'Enabled',
    'settings.startDate': 'Start date',
    'settings.endDate': 'End date',
    'settings.keywordList': 'Keywords (comma separated)',
    'settings.keywordPlaceholder': 'Enter keywords, separated by commas',
    'settings.exports': 'Export Tables',
    'settings.exportLink': 'Link table',
    'settings.exportCount': 'Count table',
    'settings.exportUpload': 'Upload table',
    'settings.save': 'Save settings',
    'settings.saved': 'Settings saved.',
    'records.title': 'Download Records',
    'records.chat': 'Chat ID',
    'records.message': 'Message ID',
    'records.file': 'File',
    'records.size': 'Size',
    'records.updated': 'Updated',
    'records.empty': 'No download records yet.',
    'records.clear': 'Clear All',
    'records.confirmClear': 'Clear all download records? This cannot be undone.',
    'records.cleared': 'Download records cleared.',
    'systemLogs.title': 'System Logs',
    'systemLogs.retentionHint': 'Full-chain debug logs, retained for {days} days',
    'systemLogs.filterAllCategories': 'All categories',
    'systemLogs.filterAllLevels': 'All levels',
    'systemLogs.categoryWatch': 'Watch',
    'systemLogs.categoryFilter': 'Filter',
    'systemLogs.categoryForward': 'Forward',
    'systemLogs.categoryTransfer': 'Download/Upload',
    'systemLogs.categoryArchive': 'Archive',
    'systemLogs.todayOnly': 'Today only',
    'systemLogs.autoRefresh': 'Auto refresh',
    'systemLogs.copyPage': 'Copy page',
    'systemLogs.downloadAll': 'Download logs',
    'systemLogs.downloading': 'Downloading…',
    'systemLogs.downloadEmpty': 'No logs to download.',
    'systemLogs.downloadFailed': 'Failed to download logs.',
    'systemLogs.copied': 'Page logs copied to clipboard.',
    'systemLogs.detailTitle': 'Log Detail',
    'systemLogs.time': 'Time',
    'systemLogs.level': 'Level',
    'systemLogs.category': 'Category',
    'systemLogs.stage': 'Stage',
    'systemLogs.message': 'Message',
    'systemLogs.context': 'Context',
    'systemLogs.details': 'Details',
    'systemLogs.sourceChat': 'Source chat',
    'systemLogs.sourceMessage': 'Source message',
    'systemLogs.target': 'Target',
    'systemLogs.empty': 'No system logs yet.',
    'systemLogs.trace': 'Trace',
    'systemLogs.watch': 'Watch',
    'form.createFailed': 'Creation failed.',
    'form.requestFailed': 'Request failed.',
    'form.creatingTransfer': 'Analyzing source message range…',
    'form.creatingTransferShort': 'Analyzing…',
    'form.createSuccess': 'Task created, queued for processing.',
    'media.title': 'Media Management',
    'media.scan': 'Scan cleanable files',
    'media.scanning': 'Scanning…',
    'media.totalFiles': 'Cleanable files',
    'media.totalSize': 'Total size',
    'media.retentionDays': 'Retention days',
    'media.transferItems': 'Transfer task files',
    'media.orphanFiles': 'Orphan files',
    'media.file': 'File',
    'media.size': 'Size',
    'media.status': 'Status',
    'media.source': 'Source',
    'media.path': 'Path',
    'media.mtime': 'Modified',
    'media.cleanup': 'Delete selected',
    'media.cleaning': 'Cleaning…',
    'media.selected': 'Selected',
    'media.files': 'files',
    'media.noSelection': 'Select files to delete first.',
    'media.confirmCleanup': 'Delete selected files? This cannot be undone.',
    'media.cleanupDone': 'Cleanup done: {count} files deleted ({size}).',
    'media.cleanupHistory': 'Cleanup history',
    'media.empty': 'No cleanable files',
    'media.reason': 'Reason',
    'media.time': 'Time',
    'media.filterByTask': 'Filter by task:',
    'media.allTasks': 'All tasks',
    'status.pending': 'Pending',
    'status.running': 'Running',
    'status.paused': 'Paused',
    'status.success': 'Completed',
    'status.failure': 'Failed',
    'status.skipped': 'Skipped',
    'event.level.info': 'Info',
    'event.level.warning': 'Warning',
    'event.level.error': 'Error',
    'error.auth_required': 'Authentication required.',
    'error.invalid_task_id': 'Invalid task ID.',
    'error.task_not_found': 'Task not found.',
    'error.source_link_required': 'Source link is required.',
    'error.target_link_required': 'Target link is required.',
    'error.range_ids_required': 'Start and end IDs required together.',
    'error.range_end_before_start': 'End ID must be >= Start ID.',
    'error.invalid_payload': 'Invalid payload.',
  }
};

const state = {
  lang: localStorage.getItem('trmd-lang') || 'zh',
  activeView: 'transfers',
  activeItemStatus: 'active',
  selectedTaskId: null,
  tasks: [],
  watches: [],
  settings: null,
  settingsSchema: {},
  settingsModel: {},
  items: [],
  events: [],
  records: [],
  statistics: null,
  statisticsTab: 'link',
  lastSync: null,
  itemPages: {},
  itemData: {},
  eventData: {},
  taskPollTimer: null,
  watchEventCache: {},
  expandedWatches: {},
  watchHistory: { watchId: null, page: 1, pageSize: 20, total: 0 },
  recordsPage: 1,
  recordsPageSize: 50,
  recordsTotal: 0,
  metrics: {},
};
window.state = state;

function $(sel) {
  return document.querySelector(sel);
}

function $$(sel) {
  return document.querySelectorAll(sel);
}

window.$ = $;
window.$$ = $$;

function t(key, replacements) {
  const dict = i18n[state.lang] || i18n.zh;
  let text = dict[key];
  if (text === undefined) {
    // fallback to zh
    text = (i18n.zh[key]) || key;
  }
  if (replacements) {
    for (const [k, v] of Object.entries(replacements)) {
      text = text.replace('{' + k + '}', v);
    }
  }
  return text;
}

function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

const DEFAULT_PAGE_SIZE = 50;

function paginationMeta(total, pageSize, page) {
  const safePageSize = Math.max(1, Number(pageSize || DEFAULT_PAGE_SIZE));
  const safeTotal = Math.max(0, Number(total || 0));
  const totalPages = Math.max(1, Math.ceil(safeTotal / safePageSize) || 1);
  const safePage = Math.min(Math.max(1, Number(page || 1)), totalPages);
  return {
    page: safePage,
    pageSize: safePageSize,
    total: safeTotal,
    totalPages: totalPages
  };
}

function renderPaginationBar(options) {
  options = options || {};
  const meta = paginationMeta(options.total, options.pageSize, options.page);
  if (meta.totalPages <= 1 && !options.alwaysShow) return '';
  const prefix = options.prefix || 'pagination';
  const variant = options.variant || 'desktop';
  const pageInfoKey = options.pageInfoKey || 'pagination.pageInfo';
  const pageInfo = t(pageInfoKey)
    .replace('{page}', meta.page)
    .replace('{pages}', meta.totalPages)
    .replace('{total}', meta.total);
  if (variant === 'mobile') {
    return '<div class="mob-sheet-pagination">' +
      '<span class="mob-pagination-info">' + esc(pageInfo) + '</span>' +
      '<div class="mob-pagination-actions flex gap-2">' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="' + prefix + '-prev" ' + (meta.page <= 1 ? 'disabled' : '') + '>' + esc(t('items.page.previous')) + '</button>' +
        '<button class="mob-btn mob-btn-sm mob-btn-muted" id="' + prefix + '-next" ' + (meta.page >= meta.totalPages ? 'disabled' : '') + '>' + esc(t('items.page.next')) + '</button>' +
      '</div></div>';
  }
  return '<div class="pagination-bar flex items-center justify-between px-[18px] py-2 pb-[14px] gap-3 flex-wrap">' +
    '<span class="text-xs text-muted">' + esc(pageInfo) + '</span>' +
    '<div class="flex gap-2">' +
      '<button class="btn btn-sm" id="' + prefix + '-prev" ' + (meta.page <= 1 ? 'disabled' : '') + '>' + esc(t('items.page.previous')) + '</button>' +
      '<button class="btn btn-sm" id="' + prefix + '-next" ' + (meta.page >= meta.totalPages ? 'disabled' : '') + '>' + esc(t('items.page.next')) + '</button>' +
    '</div></div>';
}

function bindPaginationBar(prefix, page, totalPages, onPageChange) {
  const prevBtn = $('#' + prefix + '-prev');
  const nextBtn = $('#' + prefix + '-next');
  if (prevBtn) {
    prevBtn.addEventListener('click', function() {
      if (page > 1) onPageChange(page - 1);
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener('click', function() {
      if (page < totalPages) onPageChange(page + 1);
    });
  }
}

function applyLanguage() {
  $$('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (key) el.textContent = t(key);
  });
  document.title = t('app.title') || 'TRMD · 转存控制台';
}

function applyLanguageAndRefresh() {
  applyLanguage();
  if (state.activeView === 'transfers' && typeof renderTasks === 'function') renderTasks();
  if (state.activeView === 'watches' && typeof renderWatches === 'function') renderWatches();
  if (state.activeView === 'settings' && typeof renderSettings === 'function') renderSettings();
  if (state.activeView === 'records' && typeof loadRecords === 'function') loadRecords();
  if (typeof renderMobTasks === 'function') renderMobTasks();
  if (typeof renderMobWatches === 'function') renderMobWatches();
}

function redirectToLoginPage() {
  if (window.__trmdRedirectingToLogin) return;
  window.__trmdRedirectingToLogin = true;
  window.location.assign('/');
}

function clientTzOffsetMinutes() {
  return new Date().getTimezoneOffset();
}

function withClientTzQuery(url) {
  var separator = url.indexOf('?') >= 0 ? '&' : '?';
  return url + separator + 'tz_offset=' + encodeURIComponent(String(clientTzOffsetMinutes()));
}

async function fetchJson(url) {
  const resp = await fetch(url);
  if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }
  if (!resp.ok) {
    let data;
    try { data = await resp.json(); } catch(e) { data = {}; }
    throw data;
  }
  return resp.json();
}

async function postJson(url, payload, method) {
  const resp = await fetch(url, {
    method: method || 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

async function patchJson(url, payload) {
  const resp = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (resp.status === 401) { redirectToLoginPage(); throw { error_code: 'auth_required' }; }
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

function translateApiError(data, fallbackKey) {
  if (data && data.error_code && data.error) {
    const key = 'error.' + data.error_code;
    const translated = t(key);
    if (translated !== key) return translated;
    return data.error;
  }
  return t(fallbackKey || 'form.requestFailed');
}

function fmtSize(bytes) {
  if (!bytes && bytes !== 0) return '-';
  bytes = Number(bytes);
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
  return (bytes / 1073741824).toFixed(2) + ' GB';
}

function formatBytes(bytes) {
  return fmtSize(bytes);
}

function fmtTime(iso) {
  if (!iso) return '-';
  try { return new Date(iso).toLocaleString(); } catch(e) { return iso; }
}

function fmtTimestamp(sec) {
  if (!sec) return '-';
  try { return new Date(sec * 1000).toLocaleString(); } catch(e) { return String(sec); }
}

function statusBadge(status) {
  const labels = { pending: 'status.pending', running: 'status.running', paused: 'status.paused', success: 'status.success', failure: 'status.failure', skipped: 'status.skipped' };
  const cls = status || 'pending';
  return '<span class="badge badge-' + cls + '"><span class="status-dot ' + cls + '"></span>' + t(labels[status] || 'status.pending') + '</span>';
}

function setLang(lang) {
  state.lang = lang || 'zh';
  localStorage.setItem('trmd-lang', state.lang);
  applyLanguageAndRefresh();
}

function optionValues(options) {
  return (options || []).map(function(option) {
    return typeof option === 'string' ? option : option.value;
  }).filter(Boolean);
}

function selectedKeys(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === 'object') {
    return Object.entries(value).filter(function(entry) { return Boolean(entry[1]); }).map(function(entry) { return entry[0]; });
  }
  return [];
}

function taskUsesRangeProgress(task) {
  return Boolean(task && task.uses_range_progress);
}

function taskProgressPercent(task) {
  if (taskUsesRangeProgress(task)) {
    return Number(task.range_progress_percent || 0);
  }
  return Number(task && task.progress_percent || 0);
}

function taskCompletedLabel(task) {
  if (!task) return '0/0';
  if (taskUsesRangeProgress(task)) {
    return t('tasks.progressIds')
      .replace('{done}', String(Number(task.range_completed_ids || 0)))
      .replace('{total}', String(Number(task.range_total_ids || 0)));
  }
  return String(Number(task.completed_items || 0)) + '/' + String(Number(task.total_items || 0));
}

function taskRangeDetailSummary(task) {
  if (!task || !taskUsesRangeProgress(task)) return '';
  const parts = [];
  const currentId = task.current_range_message_id;
  if (currentId) {
    parts.push(t('tasks.progressCurrentId').replace('{id}', String(currentId)));
  }
  const captured = Number(task.current_range_video_total || task.current_range_video_captured || 0);
  if (captured > 0) {
    parts.push(t('tasks.progressVideosCaptured').replace('{count}', String(captured)));
  }
  const videoIndex = Number(task.current_range_video_index || 0);
  if (videoIndex > 0) {
    parts.push(t('tasks.progressVideoIndex').replace('{index}', String(videoIndex)));
  }
  return parts.join(' · ');
}

function taskFileTransferDetail(task) {
  if (!task || !task.active_item_id) return '';
  const phase = task.active_phase || '';
  if (phase !== 'downloading' && phase !== 'uploading') return '';
  const name = task.active_file_name || ('#' + task.active_item_id);
  const progress = transferProgressLabel(task.active_progress_current, task.active_progress_total);
  const speed = formatSpeed(task.active_speed_bps);
  return t('tasks.progressDownloading')
    .replace('{name}', name)
    .replace('{progress}', progress + (speed !== '-' ? ' · ' + speed : ''));
}

function activeTransferSummary(task) {
  if (!task) return '';
  const rangeDetail = taskRangeDetailSummary(task);
  const fileDetail = taskFileTransferDetail(task);
  if (rangeDetail && fileDetail) return rangeDetail + ' · ' + fileDetail;
  return rangeDetail || fileDetail || '';
}

function taskFailedCount(task) {
  return Number(task && task.failed_items || 0);
}

function formatSpeed(bytesPerSecond) {
  const value = Number(bytesPerSecond || 0);
  if (!value || value < 0) return '-';
  return fmtSize(value) + '/s';
}

function formatSpeedStat(bytesPerSecond) {
  const value = Number(bytesPerSecond || 0);
  if (!value || value < 0) return '0 B/s';
  return fmtSize(value) + '/s';
}

function transferPhaseLabel(phase) {
  const labels = {
    downloading: '下载',
    downloaded: '下载完成',
    uploading: '上传',
    uploaded: '上传完成',
    sent: '已发送',
    forwarded: '已转发',
    failure: '失败',
    failed: '失败',
    skipped: '跳过',
    pending: '等待'
  };
  return labels[phase] || phase || '-';
}

function transferProgressLabel(current, total) {
  current = Number(current || 0);
  total = Number(total || 0);
  if (!total) return current ? fmtSize(current) : '-';
  const percent = Math.min(100, Math.round((current / total) * 100));
  return fmtSize(current) + '/' + fmtSize(total) + ' · ' + percent + '%';
}

function itemTransferSummary(item) {
  if (!item) return '-';
  const phase = transferPhaseLabel(item.phase || item.status);
  if (item.phase === 'uploading' || Number(item.upload_current || 0) > 0) {
    return phase + ' · ' + transferProgressLabel(item.upload_current, item.upload_total) +
      (Number(item.upload_speed_bps || 0) ? ' · ' + formatSpeed(item.upload_speed_bps) : '');
  }
  if (Number(item.download_total || 0) || Number(item.download_current || 0)) {
    return phase + ' · ' + transferProgressLabel(item.download_current, item.download_total) +
      (Number(item.download_speed_bps || 0) ? ' · ' + formatSpeed(item.download_speed_bps) : '');
  }
  return phase;
}

async function runTaskAction(event, taskId, action) {
  if (event && event.stopPropagation) event.stopPropagation();
  await postJson('/api/tasks/' + encodeURIComponent(taskId) + '/' + action, {});
  if (typeof loadMobileTasks === 'function') await loadMobileTasks();
  else if (typeof loadTasks === 'function') await loadTasks();
}

async function deleteTask(event, taskId) {
  if (event && event.stopPropagation) event.stopPropagation();
  if (!confirm('确定删除任务 #' + taskId + '？')) return;
  const resp = await fetch('/api/tasks/' + encodeURIComponent(taskId), { method: 'DELETE' });
  if (!resp.ok) {
    let data = {};
    try { data = await resp.json(); } catch(e) {}
    throw data;
  }
  state.tasks = (state.tasks || []).filter(function(task) { return Number(task.id) !== Number(taskId); });
  if (state.selectedTaskId === taskId) state.selectedTaskId = null;
  if (typeof renderMobTasks === 'function') renderMobTasks();
  if (typeof renderTasks === 'function') renderTasks();
  if (typeof resetTaskPolling === 'function') resetTaskPolling();
}

async function deleteWatch(watchId) {
  if (!confirm(t('watches.delete'))) return;
  const resp = await fetch('/api/watches/' + encodeURIComponent(watchId), { method: 'DELETE' });
  if (!resp.ok) {
    let data = {};
    try { data = await resp.json(); } catch(e) {}
    throw data;
  }
  state.watches = (state.watches || []).filter(function(watch) { return watch.id !== watchId; });
  if (typeof loadMobileWatches === 'function') await loadMobileWatches();
  else if (typeof loadWatches === 'function') await loadWatches();
}
