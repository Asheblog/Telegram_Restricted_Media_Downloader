# coding=UTF-8
"""Build a full local-repro diagnostic zip (configs, session, db, logs, probes)."""
from __future__ import annotations

import json
import shutil
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

from module.persistence.transfer_store import TransferStatus

DEFAULT_PROBE_LIMIT = 5
MAX_PROBE_LIMIT = 20
PROBE_ERROR_MARKER = 'Direct forward did not produce a target message'
WARNING_TEXT = (
    'WARNING: This archive contains Telegram login state and API credentials '
    '(config.yaml, .CONFIG.yaml, *.session).\n'
    'Do NOT publish it, commit it, or share it publicly.\n'
    'Transfer privately only for debugging.\n'
)
LOCAL_RESTORE_TEXT = (
    'Local restore (developer):\n'
    '1. Unzip to a non-C: path, e.g. E:\\trmd-diag\\<stamp>\\\n'
    '2. Point --config at config/config.yaml\n'
    '3. Set session_directory / temp_directory / save_directory in that yaml '
    'to local folders (or keep relative paths under the unzip root).\n'
    '4. Copy session/* into the session_directory.\n'
    '5. Prefer reading probes/forward_probe.json first — it already ran '
    'copy/forward on production against the failing items.\n'
)


def clamp_probe_limit(value) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = DEFAULT_PROBE_LIMIT
    return max(1, min(limit, MAX_PROBE_LIMIT))


def message_summary(message: Any) -> dict:
    if message is None:
        return {'present': False}
    media_fields = (
        'video', 'photo', 'document', 'audio', 'voice',
        'animation', 'video_note', 'text', 'caption',
    )
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
        'from_user_id': getattr(getattr(message, 'from_user', None), 'id', None),
        'from_user_is_bot': bool(getattr(getattr(message, 'from_user', None), 'is_bot', False)),
        'media': [field for field in media_fields if getattr(message, field, None)],
    }
    chat = getattr(message, 'chat', None)
    if chat is not None:
        summary['chat_has_protected_content'] = bool(getattr(chat, 'has_protected_content', False))
    for field in ('video', 'document', 'audio', 'animation'):
        media = getattr(message, field, None)
        if media:
            summary[f'{field}_file_name'] = getattr(media, 'file_name', None)
            summary[f'{field}_file_size'] = getattr(media, 'file_size', None)
    return summary


def exception_summary(error: BaseException) -> dict:
    return {
        'type': type(error).__name__,
        'module': type(error).__module__,
        'message': str(error),
    }


def select_probe_items(
        store,
        *,
        task_id: Optional[int] = None,
        limit: int = DEFAULT_PROBE_LIMIT,
        marker: str = PROBE_ERROR_MARKER,
) -> List[dict]:
    limit = clamp_probe_limit(limit)
    selected: List[dict] = []
    if task_id is not None:
        task_ids = [int(task_id)]
    else:
        task_ids = [int(task['id']) for task in store.list_tasks(limit=50)]

    for tid in task_ids:
        for item in store.list_items(tid):
            if item.get('status') != TransferStatus.FAILURE:
                continue
            error = str(item.get('error_message') or '')
            if marker not in error:
                continue
            selected.append(dict(item))
            if len(selected) >= limit:
                return selected
    return selected


def backup_sqlite(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        raise FileNotFoundError(f'transfer db not found: {src}')
    with sqlite3.connect(f'file:{src}?mode=ro', uri=True, timeout=30) as source:
        with sqlite3.connect(str(dst)) as target:
            source.backup(target)


def collect_session_files(session_directory: Path) -> List[Path]:
    if not session_directory or not Path(session_directory).is_dir():
        return []
    root = Path(session_directory)
    files: List[Path] = []
    for path in sorted(root.iterdir()):
        name = path.name
        if path.is_file() and (
                name.endswith('.session')
                or name.endswith('.session-journal')
                or name.endswith('.session-wal')
                or name.endswith('.session-shm')
        ):
            files.append(path)
    return files


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding='utf-8',
    )


def build_diagnostic_bundle(
        *,
        work_dir: Path,
        version: str,
        config_yaml_path: Optional[Path],
        global_config_path: Optional[Path],
        session_directory: Optional[Path],
        transfer_db_path: Optional[Path],
        store,
        system_logs_text: str = '',
        app_log_path: Optional[Path] = None,
        probe_items: Optional[Sequence[dict]] = None,
        probe_results: Optional[dict] = None,
        task_id: Optional[int] = None,
        probe_limit: int = DEFAULT_PROBE_LIMIT,
        extra_meta: Optional[dict] = None,
) -> Path:
    """Assemble zip under work_dir and return the zip path."""
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    bundle_root = Path(work_dir) / f'trmd-diagnostic-{stamp}'
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    (bundle_root / 'WARNING.txt').write_text(WARNING_TEXT, encoding='utf-8')
    (bundle_root / 'LOCAL_RESTORE.txt').write_text(LOCAL_RESTORE_TEXT, encoding='utf-8')

    config_dir = bundle_root / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    copied_config = []
    if config_yaml_path and Path(config_yaml_path).is_file():
        shutil.copy2(config_yaml_path, config_dir / 'config.yaml')
        copied_config.append('config/config.yaml')
    if global_config_path and Path(global_config_path).is_file():
        shutil.copy2(global_config_path, config_dir / '.CONFIG.yaml')
        copied_config.append('config/.CONFIG.yaml')
    # Docker often keeps .CONFIG.yaml beside user config.yaml
    if config_yaml_path:
        beside = Path(config_yaml_path).parent / '.CONFIG.yaml'
        if beside.is_file() and (
                not global_config_path
                or Path(global_config_path).resolve() != beside.resolve()
        ):
            shutil.copy2(beside, config_dir / 'CONFIG.beside-user.yaml')
            copied_config.append('config/CONFIG.beside-user.yaml')

    session_dir = bundle_root / 'session'
    session_dir.mkdir(parents=True, exist_ok=True)
    session_files = []
    for src in collect_session_files(Path(session_directory) if session_directory else Path()):
        shutil.copy2(src, session_dir / src.name)
        session_files.append(f'session/{src.name}')

    transfer_dir = bundle_root / 'transfer'
    transfer_dir.mkdir(parents=True, exist_ok=True)
    db_copied = False
    if transfer_db_path and Path(transfer_db_path).is_file():
        backup_sqlite(Path(transfer_db_path), transfer_dir / 'transfer_tasks.sqlite3')
        db_copied = True

    probe_item_list = list(probe_items or [])
    task_summary = None
    if task_id is not None and store is not None:
        task_summary = store.get_task(int(task_id))
        items = store.list_items(int(task_id))
        events = []
        if hasattr(store, 'list_events'):
            try:
                events = store.list_events(int(task_id), limit=500)
            except TypeError:
                events = store.list_events(int(task_id))
        write_json(transfer_dir / f'task_{int(task_id)}_items.json', {
            'task': task_summary,
            'items': items,
            'events': events,
        })
    elif probe_item_list and store is not None:
        # Export each probed task once
        seen = set()
        for item in probe_item_list:
            tid = item.get('task_id')
            if tid in (None, '') or tid in seen:
                continue
            seen.add(tid)
            write_json(transfer_dir / f'task_{int(tid)}_items.json', {
                'task': store.get_task(int(tid)),
                'items': store.list_items(int(tid)),
            })

    logs_dir = bundle_root / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / 'system-logs.txt').write_text(system_logs_text or '', encoding='utf-8')
    if app_log_path and Path(app_log_path).is_file():
        try:
            shutil.copy2(app_log_path, logs_dir / Path(app_log_path).name)
        except OSError:
            pass

    probes_dir = bundle_root / 'probes'
    probes_dir.mkdir(parents=True, exist_ok=True)
    write_json(probes_dir / 'forward_probe.json', probe_results or {
        'probe_limit': clamp_probe_limit(probe_limit),
        'items': probe_item_list,
        'results': [],
        'note': 'probe not run',
    })

    meta = {
        'version': version,
        'exported_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'task_id': task_id,
        'probe_limit': clamp_probe_limit(probe_limit),
        'probe_item_ids': [item.get('id') for item in probe_item_list],
        'copied_config': copied_config,
        'session_files': session_files,
        'transfer_db_copied': db_copied,
        'contains_secrets': True,
    }
    if extra_meta:
        meta.update(extra_meta)
    write_json(bundle_root / 'META.json', meta)

    zip_path = Path(work_dir) / f'trmd-diagnostic-{stamp}.zip'
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in bundle_root.rglob('*'):
            if file_path.is_file():
                zf.write(file_path, arcname=str(file_path.relative_to(bundle_root)))
    shutil.rmtree(bundle_root, ignore_errors=True)
    return zip_path


async def probe_forward_items(
        client,
        items: Iterable[dict],
        *,
        target_chat_id: Any = 'pikpak_bot',
        do_copy: bool = True,
        do_forward: bool = True,
) -> dict:
    """Run get_messages + optional copy/forward for each failed item."""
    results = []
    me = None
    try:
        me = await client.get_me()
    except Exception as e:
        me = None
        account_error = exception_summary(e)
    else:
        account_error = None

    for item in items:
        chat_id = item.get('source_chat_id')
        message_id = item.get('source_message_id')
        entry = {
            'item_id': item.get('id'),
            'task_id': item.get('task_id'),
            'source_chat_id': chat_id,
            'source_message_id': message_id,
            'source_link': item.get('source_link'),
            'error_message': item.get('error_message'),
            'target_chat_id': target_chat_id,
        }
        try:
            message = await client.get_messages(chat_id=chat_id, message_ids=int(message_id))
            entry['source_message'] = message_summary(message)
        except Exception as e:
            entry['source_get_error'] = exception_summary(e)
            results.append(entry)
            continue

        if do_copy:
            try:
                copied = await client.copy_message(
                    chat_id=target_chat_id,
                    from_chat_id=chat_id,
                    message_id=int(message_id),
                    disable_notification=True,
                    protect_content=False,
                )
                entry['copy_result'] = message_summary(copied)
            except Exception as e:
                entry['copy_error'] = exception_summary(e)

        if do_forward:
            try:
                forwarded = await client.forward_messages(
                    chat_id=target_chat_id,
                    from_chat_id=chat_id,
                    message_ids=int(message_id),
                    disable_notification=True,
                )
                entry['forward_result'] = message_summary(forwarded)
            except Exception as e:
                entry['forward_error'] = exception_summary(e)

        results.append(entry)

    return {
        'account': {
            'id': getattr(me, 'id', None),
            'username': getattr(me, 'username', None),
            'is_bot': bool(getattr(me, 'is_bot', False)),
        } if me is not None else None,
        'account_error': account_error,
        'target_chat_id': target_chat_id,
        'results': results,
    }
