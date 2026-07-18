# coding=UTF-8
"""Scan/execute Post Author reorganization on PikPak Archive via rclone."""
from typing import Callable, Optional

from module.archive_reorganize import plan_author_reorganize
from module.pikpak_archive import (
    DisabledPikPakArchiveClient,
    join_remote_path,
    normalize_source_folder_path,
)
from module.source_folders import (
    is_post_folder_segment,
    message_id_from_post_folder_segment,
    post_author_from_message,
)


MESSAGE_FETCH_BATCH = 80
ProgressCallback = Optional[Callable[..., None]]


class ArchiveAuthorReorganizeService:
    def __init__(
            self,
            *,
            archive_client,
            telegram_client=None,
            transfer_store=None,
            run_coro: Optional[Callable] = None,
    ):
        self.archive_client = archive_client
        self.telegram_client = telegram_client
        self.transfer_store = transfer_store
        self.run_coro = run_coro

    def list_channels(self) -> list[str]:
        client = self.archive_client
        if client is None or isinstance(client, DisabledPikPakArchiveClient):
            return []
        if not getattr(client, 'config', {}).get('remote'):
            return []
        return list(client.list_archive_channel_folders())

    @staticmethod
    def _report(
            on_progress: ProgressCallback,
            *,
            phase: str,
            current: int = 0,
            total: int = 0,
            message: str = '',
    ) -> None:
        if on_progress is None:
            return
        on_progress(phase=phase, current=current, total=total, message=message)

    def scan(self, channel_folder: str, on_progress: ProgressCallback = None) -> dict:
        channel = normalize_source_folder_path(channel_folder)
        if not channel or '/' in channel:
            raise ValueError('请输入单个频道文件夹名（Source Channel Folder）。')
        client = self._require_client()
        root = self._channel_remote_root(client, channel)
        self._report(
            on_progress,
            phase='listing',
            message='正在列出 PikPak 目录（大目录可能较久）…',
        )
        directory_paths = [
            f'{channel}/{path}' if path else channel
            for path in client.list_directories(root, recursive=True)
        ]
        # Also include top-level names when recursive returns relative paths only.
        if not directory_paths:
            directory_paths = [
                f'{channel}/{name}' for name in client.list_directories(root, recursive=False)
            ]
        self._report(
            on_progress,
            phase='listing',
            current=len(directory_paths),
            total=len(directory_paths),
            message=f'已列出 {len(directory_paths)} 个目录',
        )
        message_ids = []
        for path in directory_paths:
            parts = [part for part in path.replace('\\', '/').split('/') if part]
            if len(parts) >= 2 and is_post_folder_segment(parts[-1]):
                mid = message_id_from_post_folder_segment(parts[-1])
                if mid is not None:
                    message_ids.append(mid)
        unique_ids = sorted(set(message_ids))
        self._report(
            on_progress,
            phase='resolving',
            current=0,
            total=len(unique_ids),
            message=f'正在拉取 Telegram 主贴作者 0/{len(unique_ids)}…',
        )
        author_by_id = self._resolve_authors(
            channel,
            unique_ids,
            on_progress=on_progress,
        )
        self._report(
            on_progress,
            phase='planning',
            current=len(unique_ids),
            total=max(len(unique_ids), 1),
            message='正在生成移动计划…',
        )
        plan = plan_author_reorganize(
            channel_folder=channel,
            directory_paths=directory_paths,
            author_by_message_id=author_by_id,
        )
        payload = plan.to_dict()
        payload['channel_remote_root'] = root
        self._report(
            on_progress,
            phase='done',
            current=payload.get('move_count') or 0,
            total=max(int(payload.get('move_count') or 0) + int(payload.get('skip_count') or 0), 1),
            message=(
                f'扫描完成：{payload.get("author_count") or 0} 位作者，'
                f'待移动 {payload.get("move_count") or 0}，跳过 {payload.get("skip_count") or 0}'
            ),
        )
        return payload

    def execute(self, channel_folder: str, on_progress: ProgressCallback = None) -> dict:
        plan = self.scan(channel_folder, on_progress=on_progress)
        client = self._require_client()
        root = plan.get('channel_remote_root') or self._channel_remote_root(client, plan['channel_folder'])
        move_items = [item for item in (plan.get('moves') or []) if item.get('action') == 'move']
        moved = []
        errors = []
        total = len(move_items)
        self._report(
            on_progress,
            phase='moving',
            current=0,
            total=total,
            message=f'开始移动目录 0/{total}…',
        )
        for index, item in enumerate(move_items, start=1):
            from_rel = item['from_relative']
            to_rel = item['to_relative']
            source = join_remote_path(root, from_rel)
            target = join_remote_path(root, to_rel)
            try:
                client.move_directory(source, target)
                moved.append(item)
                if self.transfer_store is not None:
                    self._rewrite_store_paths(plan['channel_folder'], from_rel, to_rel)
            except Exception as error:
                errors.append({
                    'from_relative': from_rel,
                    'to_relative': to_rel,
                    'error': str(error),
                })
            self._report(
                on_progress,
                phase='moving',
                current=index,
                total=total,
                message=f'正在移动目录 {index}/{total}…',
            )
        result = {
            'channel_folder': plan['channel_folder'],
            'author_count': plan['author_count'],
            'authors': plan['authors'],
            'planned_moves': plan['move_count'],
            'moved_count': len(moved),
            'error_count': len(errors),
            'moved': moved,
            'errors': errors,
            'skips': [item for item in plan.get('moves') or [] if item.get('action') != 'move'],
        }
        self._report(
            on_progress,
            phase='done',
            current=total,
            total=max(total, 1),
            message=f'整理完成：已移动 {len(moved)}，失败 {len(errors)}',
        )
        return result

    def _require_client(self):
        client = self.archive_client
        if client is None or isinstance(client, DisabledPikPakArchiveClient):
            raise RuntimeError('PikPak rclone 未配置或归档未启用。')
        if not getattr(client, 'config', {}).get('remote'):
            raise RuntimeError('PikPak rclone remote 未配置。')
        return client

    @staticmethod
    def _channel_remote_root(client, channel: str) -> str:
        archive_root = (client.config or {}).get('root_directory') or ''
        return join_remote_path(archive_root, channel)

    def _resolve_authors(
            self,
            channel_folder: str,
            message_ids: list[int],
            on_progress: ProgressCallback = None,
    ) -> dict:
        if not message_ids:
            return {}
        if self.telegram_client is None:
            return {mid: None for mid in message_ids}

        async def _fetch():
            authors = {mid: None for mid in message_ids}
            client = self.telegram_client
            total = len(message_ids)
            done = 0
            for offset in range(0, len(message_ids), MESSAGE_FETCH_BATCH):
                batch = message_ids[offset:offset + MESSAGE_FETCH_BATCH]
                try:
                    messages = await client.get_messages(channel_folder, batch)
                except Exception:
                    # Fall back to one-by-one so a single bad id doesn't abort the scan.
                    messages = []
                    for mid in batch:
                        try:
                            messages.append(await client.get_messages(channel_folder, mid))
                        except Exception:
                            messages.append(None)
                if not isinstance(messages, list):
                    messages = [messages]
                for message in messages:
                    if message is None:
                        continue
                    mid = getattr(message, 'id', None)
                    if mid is None:
                        continue
                    authors[int(mid)] = post_author_from_message(message)
                done = min(offset + len(batch), total)
                self._report(
                    on_progress,
                    phase='resolving',
                    current=done,
                    total=total,
                    message=f'正在拉取 Telegram 主贴作者 {done}/{total}…',
                )
            return authors

        if self.run_coro is not None:
            return self.run_coro(_fetch())
        # Sync callers without an event loop helper cannot await Telegram.
        return {mid: None for mid in message_ids}

    def _rewrite_store_paths(self, channel_folder: str, from_relative: str, to_relative: str) -> None:
        store = self.transfer_store
        if store is None or not hasattr(store, 'rewrite_source_folder_path'):
            return
        store.rewrite_source_folder_path(
            channel_folder=channel_folder,
            from_relative=from_relative,
            to_relative=to_relative,
        )
