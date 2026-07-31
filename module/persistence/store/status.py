# coding=UTF-8

class TransferStatus:
    PENDING = 'pending'
    RUNNING = 'running'
    PAUSING = 'pausing'
    PAUSED = 'paused'
    SKIPPED = 'skipped'
    SUCCESS = 'success'
    FAILURE = 'failure'


class ExecutionMode:
    """Transfer Task 的执行归属：web 队列编排 vs 监听内联下载回退。"""
    WEB_QUEUE = 'web_queue'
    WATCH_INLINE = 'watch_inline'


class DeferredDiscussionCaptureStatus:
    PENDING = 'pending'
    RUNNING = 'running'
    DONE = 'done'
    CANCELLED = 'cancelled'
    FAILURE = 'failure'
