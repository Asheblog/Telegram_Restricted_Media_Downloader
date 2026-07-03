# coding=UTF-8
try:
    from module.client import TelegramRestrictedMediaDownloaderClient
except ImportError:
    pass

try:
    from module.uploader import TelegramUploader
except ImportError:
    pass

try:
    from module.async_window import DynamicAsyncWindow
except ImportError:
    pass
