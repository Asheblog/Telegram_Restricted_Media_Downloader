# coding=UTF-8
import datetime
import os

from typing import Any, Dict, List, Optional


class WebCommand:
    DOWNLOAD = 'download'
    FORWARD = 'forward'
    LISTEN_DOWNLOAD = 'listen_download'
    LISTEN_FORWARD = 'listen_forward'
    LISTEN_INFO = 'listen_info'
    UPLOAD = 'upload'
    UPLOAD_R = 'upload_r'
    DOWNLOAD_CHAT = 'download_chat'
    TABLE = 'table'
    HELP = 'help'
    EXIT = 'exit'

    MUTATING = {
        DOWNLOAD,
        FORWARD,
        LISTEN_DOWNLOAD,
        LISTEN_FORWARD,
        UPLOAD,
        UPLOAD_R,
        DOWNLOAD_CHAT,
        EXIT,
    }

    DISPLAY_ONLY = {
        HELP,
        TABLE,
        LISTEN_INFO,
    }

    @classmethod
    def all(cls) -> set:
        return cls.MUTATING | cls.DISPLAY_ONLY


DOWNLOAD_TYPES = (
    'video',
    'photo',
    'document',
    'audio',
    'voice',
    'animation',
    'video_note',
)


COMMAND_HELP = [
    {
        'command': WebCommand.DOWNLOAD,
        'title': 'Download',
        'usage': '/download https://t.me/x/x 起始ID 结束ID',
        'description': '创建下载任务，支持单消息链接、多链接、txt 路径和频道范围。',
    },
    {
        'command': WebCommand.FORWARD,
        'title': 'Forward',
        'usage': '/forward https://t.me/A https://t.me/B 1 100',
        'description': '将频道 A 的消息范围发送到频道 B，受限内容走下载后上传。',
    },
    {
        'command': WebCommand.LISTEN_DOWNLOAD,
        'title': 'Listen Download',
        'usage': '/listen_download https://t.me/A https://t.me/B',
        'description': '监听频道的新视频和图片并下载。',
    },
    {
        'command': WebCommand.LISTEN_FORWARD,
        'title': 'Listen Forward',
        'usage': '/listen_forward 监听频道 转发频道',
        'description': '监听频道的新消息并转发到目标频道。',
    },
    {
        'command': WebCommand.LISTEN_INFO,
        'title': 'Listen Info',
        'usage': '/listen_info',
        'description': '查看当前运行中的监听规则。',
    },
    {
        'command': WebCommand.UPLOAD,
        'title': 'Upload',
        'usage': '/upload 本地文件 目标频道',
        'description': '上传本地文件到目标频道，目标可为 me/self。',
    },
    {
        'command': WebCommand.UPLOAD_R,
        'title': 'Upload Recursive',
        'usage': '/upload_r 本地文件夹 目标频道',
        'description': '递归上传文件夹内的文件。',
    },
    {
        'command': WebCommand.DOWNLOAD_CHAT,
        'title': 'Download Chat',
        'usage': '/download_chat 频道链接',
        'description': '下载指定频道，并用 Web 表单设置日期、类型、关键词和评论过滤。',
    },
    {
        'command': WebCommand.TABLE,
        'title': 'Table',
        'usage': '/table',
        'description': '查看下载、上传、Web 任务和监听统计。',
    },
    {
        'command': WebCommand.HELP,
        'title': 'Help',
        'usage': '/help',
        'description': '展示全部 Web 命令入口和参数。',
    },
    {
        'command': WebCommand.EXIT,
        'title': 'Exit',
        'usage': '/exit',
        'description': '请求当前程序优雅退出。',
    },
]


def parse_int(value: Any, name: str, required: bool = False) -> Optional[int]:
    if value in (None, ''):
        if required:
            raise ValueError(f'{name} is required.')
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f'{name} must be an integer.') from e


def parse_date(value: Any, name: str) -> Optional[str]:
    if value in (None, ''):
        return None
    text = str(value).strip()
    try:
        datetime.date.fromisoformat(text)
    except ValueError as e:
        raise ValueError(f'{name} must use YYYY-MM-DD.') from e
    return text


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ''):
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in ('1', 'true', 'yes', 'y', 'on')


def list_from_text(value: Any) -> List[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value or '').replace('\n', ' ').split()
    return [str(item).strip() for item in raw if str(item).strip()]


def normalize_download_types(value: Any) -> Dict[str, bool]:
    if isinstance(value, dict):
        selected = {key for key, enabled in value.items() if enabled}
    elif isinstance(value, list):
        selected = {str(item) for item in value}
    elif value in (None, ''):
        selected = set(DOWNLOAD_TYPES)
    else:
        selected = set(str(value).replace(',', ' ').split())
    invalid = selected - set(DOWNLOAD_TYPES)
    if invalid:
        raise ValueError(f'Unsupported download types: {", ".join(sorted(invalid))}.')
    if not selected:
        raise ValueError('At least one download type is required.')
    return {dtype: dtype in selected for dtype in DOWNLOAD_TYPES}


def require_text(payload: Dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or '').strip()
    if not value:
        raise ValueError(f'{key} is required.')
    return value


def normalize_command_payload(command: str, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if command not in WebCommand.all():
        raise ValueError(f'Unsupported command: {command}.')
    payload = payload.copy() if isinstance(payload, dict) else {}

    if command == WebCommand.DOWNLOAD:
        links = list_from_text(payload.get('links') or payload.get('source_link'))
        file_path = str(payload.get('file_path') or '').strip()
        start_id = parse_int(payload.get('start_id'), 'start_id')
        end_id = parse_int(payload.get('end_id'), 'end_id')
        if (start_id is None) != (end_id is None):
            raise ValueError('start_id and end_id must be provided together.')
        if start_id is not None and end_id is not None and end_id < start_id:
            raise ValueError('end_id must be greater than or equal to start_id.')
        if not links and not file_path:
            raise ValueError('links or file_path is required.')
        return {
            'links': links,
            'file_path': file_path,
            'start_id': start_id,
            'end_id': end_id,
            'target_link': str(payload.get('target_link') or '').strip(),
            'target_profile': str(payload.get('target_profile') or 'generic').strip(),
        }

    if command == WebCommand.FORWARD:
        start_id = parse_int(payload.get('start_id'), 'start_id', required=True)
        end_id = parse_int(payload.get('end_id'), 'end_id', required=True)
        if end_id < start_id:
            raise ValueError('end_id must be greater than or equal to start_id.')
        return {
            'origin_link': require_text(payload, 'origin_link'),
            'target_link': require_text(payload, 'target_link'),
            'start_id': start_id,
            'end_id': end_id,
        }

    if command == WebCommand.LISTEN_DOWNLOAD:
        links = list_from_text(payload.get('links'))
        if not links:
            raise ValueError('links is required.')
        return {'links': links}

    if command == WebCommand.LISTEN_FORWARD:
        return {
            'listen_link': require_text(payload, 'listen_link'),
            'target_link': require_text(payload, 'target_link'),
        }

    if command in (WebCommand.UPLOAD, WebCommand.UPLOAD_R):
        file_key = 'directory_path' if command == WebCommand.UPLOAD_R else 'file_path'
        path_value = os.path.normpath(require_text(payload, file_key))
        return {
            file_key: path_value,
            'target_link': require_text(payload, 'target_link'),
            'delete_after_upload': parse_bool(payload.get('delete_after_upload')),
        }

    if command == WebCommand.DOWNLOAD_CHAT:
        return {
            'chat_link': require_text(payload, 'chat_link'),
            'start_date': parse_date(payload.get('start_date'), 'start_date'),
            'end_date': parse_date(payload.get('end_date'), 'end_date'),
            'download_type': normalize_download_types(payload.get('download_type')),
            'keywords': list_from_text(payload.get('keywords')),
            'include_comment': parse_bool(payload.get('include_comment')),
        }

    if command == WebCommand.EXIT:
        return {
            'reason': str(payload.get('reason') or 'Requested from WebUI.').strip()
        }

    return {}


def primary_links_for_task(command: str, payload: Dict[str, Any]) -> Dict[str, str]:
    if command == WebCommand.DOWNLOAD:
        source = payload.get('file_path') or ' '.join(payload.get('links') or [])
        return {
            'source_link': source,
            'target_link': payload.get('target_link') or '',
            'target_profile': payload.get('target_profile') or 'generic',
        }
    if command == WebCommand.FORWARD:
        return {
            'source_link': payload.get('origin_link') or '',
            'target_link': payload.get('target_link') or '',
            'target_profile': 'generic',
        }
    if command == WebCommand.LISTEN_DOWNLOAD:
        return {
            'source_link': ' '.join(payload.get('links') or []),
            'target_link': '',
            'target_profile': 'listener',
        }
    if command == WebCommand.LISTEN_FORWARD:
        return {
            'source_link': payload.get('listen_link') or '',
            'target_link': payload.get('target_link') or '',
            'target_profile': 'listener',
        }
    if command == WebCommand.UPLOAD:
        return {
            'source_link': payload.get('file_path') or '',
            'target_link': payload.get('target_link') or '',
            'target_profile': 'upload',
        }
    if command == WebCommand.UPLOAD_R:
        return {
            'source_link': payload.get('directory_path') or '',
            'target_link': payload.get('target_link') or '',
            'target_profile': 'upload',
        }
    if command == WebCommand.DOWNLOAD_CHAT:
        return {
            'source_link': payload.get('chat_link') or '',
            'target_link': '',
            'target_profile': 'chat',
        }
    return {'source_link': command, 'target_link': '', 'target_profile': 'runtime'}
