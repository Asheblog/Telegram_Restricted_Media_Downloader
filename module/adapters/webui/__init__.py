# coding=UTF-8
try:
    from module.web_ui import (
        WebUiServer,
        get_web_host_from_env,
        get_web_password_from_env,
        get_web_port_from_env,
        get_web_username_from_env,
        merge_allowed_settings,
    )
except ImportError:
    pass

try:
    from module.adapters.webui.assets import WEB_UI_HTML, WEB_UI_MOBILE_HTML
except ImportError:
    pass

try:
    from module.web_task_manager import WebUITaskManager
except ImportError:
    pass
