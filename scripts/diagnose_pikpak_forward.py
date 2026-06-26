# coding=UTF-8
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def message_summary(message: Any) -> dict:
    if message is None:
        return {'present': False}
    media_fields = [
        'video',
        'photo',
        'document',
        'audio',
        'voice',
        'animation',
        'video_note',
        'text',
        'caption'
    ]
    summary = {
        'present': True,
        'id': getattr(message, 'id', None),
        'empty': bool(getattr(message, 'empty', False)),
        'service': bool(getattr(message, 'service', False)),
        'media_group_id': getattr(message, 'media_group_id', None),
        'has_protected_content': bool(getattr(message, 'has_protected_content', False)),
        'link': getattr(message, 'link', None),
        'chat_id': getattr(getattr(message, 'chat', None), 'id', None),
        'chat_username': getattr(getattr(message, 'chat', None), 'username', None),
        'media': [field for field in media_fields if getattr(message, field, None)]
    }
    for field in ('video', 'document', 'audio', 'animation'):
        media = getattr(message, field, None)
        if media:
            summary[f'{field}_file_name'] = getattr(media, 'file_name', None)
            summary[f'{field}_file_size'] = getattr(media, 'file_size', None)
    return summary


def config_path_from_args(path: str | None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get('TRMD_CONFIG')
    if env_path:
        return Path(env_path).expanduser()
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'TRMD' / '.CONFIG.yaml'


def load_config(path: Path) -> dict:
    with path.open('r', encoding='UTF-8') as file:
        return yaml.safe_load(file) or {}


async def run(args: argparse.Namespace) -> int:
    config_path = config_path_from_args(args.config)
    config = load_config(config_path)
    source_link = args.source
    target_link = args.target
    source_meta = await parse_link_for_config(config, source_link)
    target_meta = await parse_link_for_config(config, target_link)
    return await diagnose(config, source_link, target_link, source_meta, target_meta, args.copy)


async def parse_link_for_config(config: dict, link: str) -> dict:
    async with build_client(config) as client:
        from module.util import parse_link

        return await parse_link(client=client, link=link)


def build_client(config: dict):
    import pyrogram
    from module import SLEEP_THRESHOLD, SOFTWARE_FULL_NAME

    session_directory = config.get('session_directory') or Path.home() / '.config' / 'TRMD'
    return pyrogram.Client(
        name=SOFTWARE_FULL_NAME.replace(' ', ''),
        api_id=config.get('api_id'),
        api_hash=config.get('api_hash'),
        proxy=config.get('proxy') if (config.get('proxy') or {}).get('enable_proxy') else None,
        workdir=str(session_directory),
        sleep_threshold=SLEEP_THRESHOLD
    )


async def diagnose(
        config: dict,
        source_link: str,
        target_link: str,
        source_meta: dict,
        target_meta: dict,
        do_copy: bool
) -> int:
    source_chat_id = source_meta.get('chat_id')
    source_message_id = source_meta.get('comment_id')
    target_chat_id = target_meta.get('chat_id')
    result = {
        'source_link': source_link,
        'target_link': target_link,
        'source_chat_id': source_chat_id,
        'source_message_id': source_message_id,
        'target_chat_id': target_chat_id,
        'copy_requested': do_copy
    }
    async with build_client(config) as client:
        me = await client.get_me()
        result['account'] = {
            'id': getattr(me, 'id', None),
            'username': getattr(me, 'username', None),
            'is_bot': bool(getattr(me, 'is_bot', False))
        }
        try:
            source_message = await client.get_messages(
                chat_id=source_chat_id,
                message_ids=source_message_id
            )
            result['source_message'] = message_summary(source_message)
        except Exception as e:
            result['source_get_error'] = exception_summary(e)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        if do_copy:
            try:
                copied = await client.copy_message(
                    chat_id=target_chat_id,
                    from_chat_id=source_chat_id,
                    message_id=source_message_id,
                    disable_notification=True,
                    protect_content=False
                )
                result['copy_result'] = message_summary(copied)
            except Exception as e:
                result['copy_error'] = exception_summary(e)
        result['target_recent_messages'] = []
        try:
            async for message in client.get_chat_history(target_chat_id, limit=5):
                result['target_recent_messages'].append(message_summary(message))
        except Exception as e:
            result['target_history_error'] = exception_summary(e)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def exception_summary(error: Exception) -> dict:
    return {
        'type': type(error).__name__,
        'module': type(error).__module__,
        'message': str(error)
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Diagnose Telegram API copy_message behavior for a TRMD transfer link.'
    )
    parser.add_argument('source', help='Source message link, e.g. https://t.me/chengdudiyi8/74127')
    parser.add_argument(
        '--target',
        default='https://t.me/pikpak_bot',
        help='Target chat link. Defaults to https://t.me/pikpak_bot.'
    )
    parser.add_argument(
        '--config',
        help='TRMD config path. Defaults to TRMD_CONFIG or ~/.config/TRMD/.CONFIG.yaml.'
    )
    parser.add_argument(
        '--copy',
        action='store_true',
        help='Actually call copy_message to the target. Without this, only reads metadata.'
    )
    return parser.parse_args()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(run(parse_args())))
