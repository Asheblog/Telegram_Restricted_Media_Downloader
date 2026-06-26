# coding=UTF-8
import argparse
import asyncio
import json
import os
import shutil
import sqlite3
import sys
import tempfile
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
    session_directory = None
    copied_session_directory = None
    if not args.live_session:
        copied_session_directory = copy_session_to_temp_directory(config)
        session_directory = copied_session_directory
    try:
        source_meta = await parse_link_for_config(config, source_link, session_directory=session_directory)
        target_meta = await parse_link_for_config(config, target_link, session_directory=session_directory)
        return await diagnose(
            config,
            source_link,
            target_link,
            source_meta,
            target_meta,
            args.copy,
            args.forward,
            session_directory=session_directory,
            copied_session_directory=copied_session_directory
        )
    finally:
        if copied_session_directory:
            shutil.rmtree(copied_session_directory, ignore_errors=True)


async def parse_link_for_config(config: dict, link: str, session_directory: Path | None = None) -> dict:
    async with build_client(config, session_directory=session_directory) as client:
        from module.util import parse_link

        return await parse_link(client=client, link=link)


def session_name() -> str:
    from module import SOFTWARE_FULL_NAME

    return SOFTWARE_FULL_NAME.replace(' ', '')


def configured_session_directory(config: dict) -> Path:
    return Path(config.get('session_directory') or Path.home() / '.config' / 'TRMD').expanduser()


def copy_session_to_temp_directory(config: dict) -> Path:
    source_directory = configured_session_directory(config)
    source_session = source_directory / f'{session_name()}.session'
    if not source_session.exists():
        raise FileNotFoundError(f'Session file not found: {source_session}')
    target_directory = Path(tempfile.mkdtemp(prefix='trmd_diag_session_'))
    target_session = target_directory / source_session.name
    with sqlite3.connect(f'file:{source_session}?mode=ro', uri=True, timeout=30) as source:
        with sqlite3.connect(target_session) as target:
            source.backup(target)
    return target_directory


def build_client(config: dict, session_directory: Path | None = None):
    import pyrogram
    from module import SLEEP_THRESHOLD

    workdir = session_directory or configured_session_directory(config)
    return pyrogram.Client(
        name=session_name(),
        api_id=config.get('api_id'),
        api_hash=config.get('api_hash'),
        proxy=config.get('proxy') if (config.get('proxy') or {}).get('enable_proxy') else None,
        workdir=str(workdir),
        sleep_threshold=SLEEP_THRESHOLD
    )


async def diagnose(
        config: dict,
        source_link: str,
        target_link: str,
        source_meta: dict,
        target_meta: dict,
        do_copy: bool,
        do_forward: bool,
        session_directory: Path | None = None,
        copied_session_directory: Path | None = None
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
        'copy_requested': do_copy,
        'forward_requested': do_forward,
        'session_directory': str(session_directory or configured_session_directory(config)),
        'copied_session_directory': str(copied_session_directory) if copied_session_directory else None
    }
    async with build_client(config, session_directory=session_directory) as client:
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
        if do_forward:
            try:
                forwarded = await client.forward_messages(
                    chat_id=target_chat_id,
                    from_chat_id=source_chat_id,
                    message_ids=source_message_id,
                    disable_notification=True
                )
                result['forward_result'] = message_summary(forwarded)
            except Exception as e:
                result['forward_error'] = exception_summary(e)
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
    parser.add_argument(
        '--forward',
        action='store_true',
        help='Actually call forward_messages to the target.'
    )
    parser.add_argument(
        '--live-session',
        action='store_true',
        help='Use the configured session file directly instead of a temporary read-only backup.'
    )
    return parser.parse_args()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(run(parse_args())))
