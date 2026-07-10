# coding=UTF-8
"""Diagnose discussion reply capture for a channel post."""
import argparse
import asyncio
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import yaml

# Isolate CLI args before TRMD's global argparse (module.utils.parser.PARSE_ARGS) runs on import.
CLI_ARGV = sys.argv[1:]
sys.argv = [sys.argv[0]]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def media_fields(message: Any) -> list[str]:
    fields = ('video', 'photo', 'document', 'audio', 'voice', 'animation', 'video_note')
    return [field for field in fields if getattr(message, field, None)]


def message_brief(message: Any) -> dict:
    return {
        'id': getattr(message, 'id', None),
        'media_group_id': getattr(message, 'media_group_id', None),
        'media': media_fields(message),
        'link': getattr(message, 'link', None),
    }


def config_path_from_args(path: str | None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get('TRMD_CONFIG')
    if env_path:
        return Path(env_path).expanduser()
    docker_default = Path('/app/TRMD/config.yaml')
    if docker_default.exists():
        return docker_default
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'TRMD' / '.CONFIG.yaml'


def load_config(path: Path) -> dict:
    with path.open('r', encoding='UTF-8') as file:
        return yaml.safe_load(file) or {}


def session_name() -> str:
    from module import SOFTWARE_FULL_NAME

    return SOFTWARE_FULL_NAME.replace(' ', '')


def configured_session_directory(config: dict) -> Path:
    raw = config.get('session_directory')
    if raw not in (None, '', '~', 'null', 'None'):
        return Path(str(raw)).expanduser()
    for candidate in (
        Path('/app/sessions'),
        Path(os.environ.get('XDG_CONFIG_HOME', Path.home())) / 'sessions',
        Path.home() / '.config' / 'TRMD',
    ):
        if candidate.exists():
            return candidate
    return Path('/app/sessions')


def _copy_session_sidecar_files(source_session: Path, target_session: Path) -> None:
    for suffix in ('', '-wal', '-shm'):
        source_path = Path(f'{source_session}{suffix}') if suffix else source_session
        if not source_path.exists():
            continue
        target_path = Path(f'{target_session}{suffix}') if suffix else target_session
        shutil.copy2(source_path, target_path)


def copy_session_to_temp_directory(config: dict) -> Path:
    source_directory = configured_session_directory(config)
    source_session = source_directory / f'{session_name()}.session'
    if not source_session.exists():
        raise FileNotFoundError(f'Session file not found: {source_session}')
    target_directory = Path(tempfile.mkdtemp(prefix='trmd_diag_session_'))
    target_session = target_directory / source_session.name
    try:
        with sqlite3.connect(f'file:{source_session}?mode=ro', uri=True, timeout=60) as source:
            source.execute('PRAGMA busy_timeout=60000')
            with sqlite3.connect(target_session) as target:
                source.backup(target)
    except sqlite3.OperationalError:
        _copy_session_sidecar_files(source_session, target_session)
    return target_directory


def build_client(config: dict, session_directory: Path):
    import pyrogram
    from module import SLEEP_THRESHOLD

    return pyrogram.Client(
        name=session_name(),
        api_id=config.get('api_id'),
        api_hash=config.get('api_hash'),
        proxy=config.get('proxy') if (config.get('proxy') or {}).get('enable_proxy') else None,
        workdir=str(session_directory),
        sleep_threshold=SLEEP_THRESHOLD,
        no_updates=True,
    )


def parse_cli(argv: list[str]) -> SimpleNamespace:
    parser = argparse.ArgumentParser(
        prog='trmd-diagnose-discussion',
        description='Diagnose discussion reply capture for one channel post.'
    )
    parser.add_argument('--channel', default='https://t.me/hdydydey', help='Channel link or username.')
    parser.add_argument('--post-id', type=int, required=True, help='Channel post message id.')
    parser.add_argument(
        '--config',
        dest='config',
        help='TRMD config path. Defaults to TRMD_CONFIG, /app/TRMD/config.yaml, or ~/.config/TRMD/.CONFIG.yaml.'
    )
    parser.add_argument(
        '--live-session',
        action='store_true',
        help='Use the live session file directly. Do not use this while TRMD is running.'
    )
    return parser.parse_args(argv)


def _session_locked(error: Exception) -> bool:
    return 'database is locked' in str(error).lower()


async def collect_diagnosis(client, discussion_util, channel: str, post_id: int) -> dict:
    reply_chat_id, reply_message_id, root_message_id = await discussion_util._resolve_discussion_thread(
        client,
        channel,
        post_id
    )
    channel_raw = []
    channel_peer_error = None
    try:
        async for message in client.get_discussion_replies(channel, post_id):
            channel_raw.append(message_brief(message))
    except Exception as error:
        channel_peer_error = {
            'type': type(error).__name__,
            'message': str(error),
        }
    raw_replies = await discussion_util._collect_discussion_replies(
        client,
        reply_chat_id,
        reply_message_id,
        root_message_id
    )
    grouped = discussion_util._index_replies_by_media_group(raw_replies)
    expanded = []
    async for message in discussion_util.iter_discussion_reply_messages(client, channel, post_id):
        expanded.append(message_brief(message))
    result = {
        'discussion_thread': {
            'reply_chat_id': reply_chat_id,
            'reply_message_id': reply_message_id,
            'root_message_id': root_message_id,
        },
        'channel_peer_raw_count': len(channel_raw),
        'channel_peer_raw': channel_raw[:20],
        'discussion_peer_raw_count': len(raw_replies),
        'discussion_peer_raw': [message_brief(item) for item in raw_replies[:20]],
        'media_groups': {
            str(key): [message_brief(item) for item in values]
            for key, values in grouped.items()
        },
        'expanded_count': len(expanded),
        'expanded': expanded,
    }
    if channel_peer_error:
        result['channel_peer_error'] = channel_peer_error
    return result


async def run_with_session(config: dict, session_directory: Path, channel: str, post_id: int) -> dict:
    from module.utils import util as discussion_util

    async with build_client(config, session_directory) as client:
        me = await client.get_me()
        diagnosis = await collect_diagnosis(client, discussion_util, channel, post_id)
        diagnosis['account'] = {
            'id': getattr(me, 'id', None),
            'username': getattr(me, 'username', None),
        }
        return diagnosis


async def run(args: SimpleNamespace) -> int:
    from module import __version__
    from module.utils import util as discussion_util  # noqa: F401 - warms util module

    config_path = config_path_from_args(args.config)
    config = load_config(config_path)
    channel = args.channel.rstrip('/')
    if channel.startswith('https://t.me/'):
        channel = channel.rsplit('/', 1)[-1]

    source_session_directory = configured_session_directory(config)
    copied_session_directory: Optional[Path] = None
    session_mode = 'copy'
    session_directory = source_session_directory

    if args.live_session:
        session_mode = 'live'
    else:
        copied_session_directory = copy_session_to_temp_directory(config)
        session_directory = copied_session_directory

    result = {
        'trmd_version': __version__,
        'channel': args.channel,
        'post_id': args.post_id,
        'config_path': str(config_path),
        'session_mode': session_mode,
        'session_directory': str(session_directory),
        'source_session_directory': str(source_session_directory),
    }

    try:
        try:
            result.update(await run_with_session(config, session_directory, channel, args.post_id))
        except (sqlite3.OperationalError, OSError) as error:
            if not args.live_session or not _session_locked(error):
                raise
            result['session_fallback'] = (
                'Live session is locked because TRMD is running; retrying with a temporary session copy.'
            )
            copied_session_directory = copy_session_to_temp_directory(config)
            session_directory = copied_session_directory
            result['session_mode'] = 'copy_after_live_lock'
            result['session_directory'] = str(session_directory)
            result.update(await run_with_session(config, session_directory, channel, args.post_id))

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        if copied_session_directory:
            shutil.rmtree(copied_session_directory, ignore_errors=True)


if __name__ == '__main__':
    raise SystemExit(asyncio.run(run(parse_cli(CLI_ARGV))))
