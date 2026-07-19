# coding=UTF-8
"""Scan/execute Post Author reorganization on PikPak Archive via rclone.

Designed for slow, serial operation to avoid PikPak / Telegram rate limits.
"""
from typing import Callable, Optional
import time

from module.archive_reorganize import plan_author_reorganize
from module.pikpak_archive import (
    DisabledPikPakArchiveClient,
    join_remote_path,
    normalize_source_folder_path,
)
from module.source_folders import (
    is_post_folder_segment,
    message_id_from_post_folder_segment,
    post_author_from_telegram_message,
)


# Conservative pacing — background jobs may take hours; prefer not to trip limits.
TELEGRAM_FETCH_BATCH = 1
TELEGRAM_BATCH_PAUSE_SECONDS = 2.0
RCLONE_LIST_PAUSE_SECONDS = 2.5
RCLONE_MOVE_PAUSE_SECONDS = 3.5
ProgressCallback = Optional[Callable[..., None]]


def clean_leaf_name(path: Optional[str]) -> str:
    text = str(path or '').replace('\\', '/').strip('/')
    if not text:
        return ''
    return text.rsplit('/', 1)[-1]


def directory_paths_from_plan(plan: Optional[dict]) -> list[str]:
    """Rebuild ``channel/from_relative`` listing from a prior scan/resolve plan."""
    if not isinstance(plan, dict):
        return []
    channel = str(plan.get('channel_folder') or '').strip().strip('/')
    if not channel:
        return []
    cached = plan.get('directory_paths')
    if isinstance(cached, list) and cached:
        return [str(item).replace('\\', '/').strip('/') for item in cached if str(item).strip()]
    paths: list[str] = []
    seen: set[str] = set()
    for item in plan.get('moves') or []:
        if not isinstance(item, dict):
            continue
        relative = str(item.get('from_relative') or '').replace('\\', '/').strip('/')
        if not relative:
            continue
        full = f'{channel}/{relative}'
        if full in seen:
            continue
        seen.add(full)
        paths.append(full)
    return paths


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

    @staticmethod
    def _pace(seconds: float) -> None:
        if seconds and seconds > 0:
            time.sleep(float(seconds))

    def scan(self, channel_folder: str, on_progress: ProgressCallback = None) -> dict:
        channel = normalize_source_folder_path(channel_folder)
        if not channel or '/' in channel:
            raise ValueError('请输入单个频道文件夹名（Source Channel Folder）。')
        client = self._require_client()
        root = self._channel_remote_root(client, channel)
        self._report(
            on_progress,
            phase='listing',
            message='慢速串行列出网盘目录（仅列目录，作者稍后从 Telegram 主贴解析）…',
        )
        directory_paths = self._list_channel_directories(
            client=client,
            channel=channel,
            root=root,
            on_progress=on_progress,
        )
        return self.resolve_from_listing(
            channel,
            directory_paths=directory_paths,
            channel_remote_root=root,
            on_progress=on_progress,
            done_label='扫描完成',
            require_telegram=False,
        )

    def resolve_from_listing(
            self,
            channel_folder: str,
            *,
            directory_paths: Optional[list[str]] = None,
            prior_plan: Optional[dict] = None,
            channel_remote_root: Optional[str] = None,
            on_progress: ProgressCallback = None,
            done_label: str = '解析完成',
            require_telegram: bool = True,
    ) -> dict:
        """Resolve authors from Telegram using folder message ids — no rclone listing."""
        channel = normalize_source_folder_path(channel_folder)
        if not channel or '/' in channel:
            raise ValueError('请输入单个频道文件夹名（Source Channel Folder）。')
        paths = list(directory_paths or [])
        if not paths:
            paths = directory_paths_from_plan(prior_plan)
        if not paths:
            raise RuntimeError(
                '没有可复用的目录清单。请先执行一次「扫描作者分布」列出网盘目录；'
                '之后可用「重新解析作者」只回查 Telegram，不必再扫网盘。'
            )
        client = self._require_client()
        root = channel_remote_root or (
            (prior_plan or {}).get('channel_remote_root')
            if isinstance(prior_plan, dict)
            else None
        ) or self._channel_remote_root(client, channel)

        message_ids = []
        for path in paths:
            parts = [part for part in path.replace('\\', '/').split('/') if part]
            if len(parts) >= 2 and is_post_folder_segment(parts[-1]):
                mid = message_id_from_post_folder_segment(parts[-1])
                if mid is not None:
                    message_ids.append(mid)
        unique_ids = sorted(set(message_ids))
        if self.telegram_client is None:
            if require_telegram:
                raise RuntimeError('Telegram 客户端未就绪，无法按主贴 ID 解析作者。')
            author_by_id = {mid: None for mid in unique_ids}
            resolved = 0
            resolve_stats = {
                'fetched': 0,
                'empty': 0,
                'matched': 0,
                'errors': 0,
                'media_group_hits': 0,
                'neighbor_hits': 0,
            }
        else:
            self._report(
                on_progress,
                phase='resolving',
                current=0,
                total=len(unique_ids),
                message=f'按主贴 ID 回查 Telegram 作者 0/{len(unique_ids)}（不扫网盘）…',
            )
            resolve_payload = self._resolve_authors(
                channel,
                unique_ids,
                on_progress=on_progress,
            )
            author_by_id = resolve_payload.get('authors') or {}
            resolve_stats = resolve_payload.get('stats') or {}
            resolved = sum(1 for mid in unique_ids if author_by_id.get(mid))
        self._report(
            on_progress,
            phase='planning',
            current=len(unique_ids),
            total=max(len(unique_ids), 1),
            message=(
                f'已解析作者 {resolved}/{len(unique_ids)}'
                f'（抓取 {resolve_stats.get("fetched") or 0}，'
                f'空消息 {resolve_stats.get("empty") or 0}，'
                f'相册补齐 {resolve_stats.get("media_group_hits") or 0}，'
                f'邻条补齐 {resolve_stats.get("neighbor_hits") or 0}），'
                f'正在生成移动计划…'
            ),
        )
        plan = plan_author_reorganize(
            channel_folder=channel,
            directory_paths=paths,
            author_by_message_id=author_by_id,
        )
        payload = plan.to_dict()
        payload['channel_remote_root'] = root
        payload['directory_paths'] = paths
        payload['resolved_author_count'] = resolved
        payload['message_id_count'] = len(unique_ids)
        payload['resolve_stats'] = resolve_stats
        self._report(
            on_progress,
            phase='done',
            current=payload.get('move_count') or 0,
            total=max(int(payload.get('move_count') or 0) + int(payload.get('skip_count') or 0), 1),
            message=(
                f'{done_label}：解析到作者 {resolved}/{len(unique_ids)}'
                f'（抓取 {resolve_stats.get("fetched") or 0}，'
                f'空 {resolve_stats.get("empty") or 0}，'
                f'相册 {resolve_stats.get("media_group_hits") or 0}，'
                f'邻条 {resolve_stats.get("neighbor_hits") or 0}），'
                f'{payload.get("author_count") or 0} 个作者目录，'
                f'待移动 {payload.get("move_count") or 0}，跳过 {payload.get("skip_count") or 0}'
            ),
        )
        return payload

    def _list_channel_directories(
            self,
            *,
            client,
            channel: str,
            root: str,
            on_progress: ProgressCallback = None,
    ) -> list[str]:
        """List post folders with layered rclone lsjson (no full-tree --recursive)."""
        self._report(
            on_progress,
            phase='listing',
            message='正在列出频道顶层目录…',
        )
        top_level = client.list_directories(root, recursive=False)
        self._pace(RCLONE_LIST_PAUSE_SECONDS)
        post_paths: list[str] = []
        author_dirs: list[str] = []
        for raw in top_level:
            name = clean_leaf_name(raw)
            if not name:
                continue
            if is_post_folder_segment(name):
                post_paths.append(f'{channel}/{name}')
            else:
                author_dirs.append(name)

        total_steps = max(len(author_dirs), 1)
        self._report(
            on_progress,
            phase='listing',
            current=0,
            total=total_steps,
            message=(
                f'顶层主贴 {len(post_paths)} 个，作者目录 {len(author_dirs)} 个；'
                f'开始逐个慢速列出作者子目录…'
            ),
        )
        for index, author in enumerate(author_dirs, start=1):
            self._report(
                on_progress,
                phase='listing',
                current=index - 1,
                total=total_steps,
                message=f'正在列出作者目录 {index}/{len(author_dirs)}：{author}',
            )
            author_root = join_remote_path(root, author)
            children = client.list_directories(author_root, recursive=False)
            self._pace(RCLONE_LIST_PAUSE_SECONDS)
            for child in children:
                leaf = clean_leaf_name(child)
                if leaf and is_post_folder_segment(leaf):
                    post_paths.append(f'{channel}/{author}/{leaf}')
            self._report(
                on_progress,
                phase='listing',
                current=index,
                total=total_steps,
                message=(
                    f'已处理作者目录 {index}/{len(author_dirs)}，'
                    f'累计主贴目录 {len(post_paths)}'
                ),
            )
        self._report(
            on_progress,
            phase='listing',
            current=len(post_paths),
            total=max(len(post_paths), 1),
            message=f'已列出 {len(post_paths)} 个主贴目录',
        )
        return post_paths

    def execute(
            self,
            channel_folder: str,
            on_progress: ProgressCallback = None,
            plan: Optional[dict] = None,
    ) -> dict:
        """Move folders. Prefer a prior scan ``plan`` to avoid re-hitting APIs."""
        if plan is None:
            plan = self.scan(channel_folder, on_progress=on_progress)
        return self.execute_plan(plan, on_progress=on_progress)

    def execute_plan(self, plan: dict, on_progress: ProgressCallback = None) -> dict:
        client = self._require_client()
        channel = plan.get('channel_folder') or ''
        root = plan.get('channel_remote_root') or self._channel_remote_root(client, channel)
        move_items = [item for item in (plan.get('moves') or []) if item.get('action') == 'move']
        moved = []
        errors = []
        total = len(move_items)
        ensured_parents: set[str] = set()
        self._report(
            on_progress,
            phase='moving',
            current=0,
            total=total,
            message=f'慢速串行移动目录 0/{total}（间隔 {RCLONE_MOVE_PAUSE_SECONDS:.0f}s）…',
        )
        for index, item in enumerate(move_items, start=1):
            from_rel = item['from_relative']
            to_rel = item['to_relative']
            source = join_remote_path(root, from_rel)
            target = join_remote_path(root, to_rel)
            parent = '/'.join(str(to_rel).replace('\\', '/').split('/')[:-1])
            if parent and parent not in ensured_parents:
                try:
                    client.ensure_directory(join_remote_path(root, parent))
                    ensured_parents.add(parent)
                    self._pace(RCLONE_LIST_PAUSE_SECONDS)
                except Exception:
                    pass
            try:
                client.move_directory(source, target)
                moved.append(item)
                if self.transfer_store is not None:
                    self._rewrite_store_paths(channel, from_rel, to_rel)
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
                message=f'正在移动目录 {index}/{total}（串行慢速）…',
            )
            if index < total:
                self._pace(RCLONE_MOVE_PAUSE_SECONDS)
        result = {
            'channel_folder': channel,
            'author_count': plan.get('author_count'),
            'authors': plan.get('authors') or [],
            'planned_moves': plan.get('move_count') or total,
            'moved_count': len(moved),
            'error_count': len(errors),
            'moved': moved,
            'errors': errors,
            'skips': [item for item in (plan.get('moves') or []) if item.get('action') != 'move'],
            'channel_remote_root': root,
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
            return {'authors': {}, 'stats': {}}
        if self.telegram_client is None:
            return {
                'authors': {mid: None for mid in message_ids},
                'stats': {
                    'fetched': 0,
                    'empty': 0,
                    'matched': 0,
                    'errors': len(message_ids),
                    'media_group_hits': 0,
                    'neighbor_hits': 0,
                },
            }

        import asyncio

        flood_types: tuple = ()
        try:
            from pyrogram.errors import FloodWait, FloodPremiumWait
            flood_types = (FloodWait, FloodPremiumWait)
        except Exception:  # pragma: no cover - stub environments
            flood_types = ()

        authors = {mid: None for mid in message_ids}
        client = self.telegram_client
        total = len(message_ids)
        stats = {
            'fetched': 0,
            'empty': 0,
            'matched': 0,
            'errors': 0,
            'media_group_hits': 0,
            'neighbor_hits': 0,
        }
        chat_id = channel_folder

        async def _fetch_messages(ids: list[int], *, progress_current: int):
            while True:
                try:
                    return await client.get_messages(
                        chat_id=chat_id,
                        message_ids=ids if len(ids) > 1 else ids[0],
                    )
                except TypeError:
                    return await client.get_messages(chat_id, ids)
                except Exception as error:
                    if not flood_types or not isinstance(error, flood_types):
                        raise
                    wait_seconds = int(
                        getattr(error, 'value', None)
                        or getattr(error, 'x', None)
                        or 30
                    )
                    wait_seconds = max(wait_seconds, 1)
                    self._report(
                        on_progress,
                        phase='resolving',
                        current=progress_current,
                        total=total,
                        message=(
                            f'Telegram 限流，等待 {wait_seconds}s 后继续'
                            f'（{progress_current}/{total}）…'
                        ),
                    )
                    await asyncio.sleep(wait_seconds + 1)

        def _as_list(value):
            if value is None:
                return []
            if isinstance(value, list):
                return value
            return [value]

        async def _resolve_one(mid: int, *, progress_current: int) -> Optional[str]:
            try:
                raw = await _fetch_messages([mid], progress_current=progress_current)
            except Exception:
                stats['errors'] += 1
                return None
            messages = _as_list(raw)
            message = messages[0] if messages else None
            if message is None or getattr(message, 'empty', False):
                stats['empty'] += 1
                # Folder id may point at a media-only album member; probe nearby ids once.
                neighbor_ids = [mid + offset for offset in range(1, 6)]
                try:
                    raw_neighbors = await _fetch_messages(
                        neighbor_ids,
                        progress_current=progress_current,
                    )
                except Exception:
                    return None
                for item in _as_list(raw_neighbors):
                    if item is None or getattr(item, 'empty', False):
                        continue
                    author = await post_author_from_telegram_message(
                        item,
                        client=client,
                        chat_id=chat_id,
                    )
                    if author:
                        stats['neighbor_hits'] += 1
                        stats['matched'] += 1
                        stats['fetched'] += 1
                        return author
                return None

            stats['fetched'] += 1
            from module.source_folders import post_author_from_message as direct_author
            author = await post_author_from_telegram_message(
                message,
                client=client,
                chat_id=chat_id,
            )
            if author:
                if not direct_author(message):
                    stats['media_group_hits'] += 1
                stats['matched'] += 1
                return author

            # Still nothing — probe a few following messages (text often follows album).
            neighbor_ids = [mid + offset for offset in range(1, 4)]
            try:
                raw_neighbors = await _fetch_messages(
                    neighbor_ids,
                    progress_current=progress_current,
                )
            except Exception:
                return None
            for item in _as_list(raw_neighbors):
                if item is None or getattr(item, 'empty', False):
                    continue
                author = await post_author_from_telegram_message(
                    item,
                    client=client,
                    chat_id=chat_id,
                )
                if author:
                    stats['neighbor_hits'] += 1
                    stats['matched'] += 1
                    return author
            return None

        for offset in range(0, len(message_ids), TELEGRAM_FETCH_BATCH):
            batch = message_ids[offset:offset + TELEGRAM_FETCH_BATCH]
            mid = batch[0]
            self._report(
                on_progress,
                phase='resolving',
                current=offset,
                total=total,
                message=(
                    f'按主贴 ID 回查 Telegram 作者 {offset}/{total}'
                    f'（已命中 {stats["matched"]}，相册补齐 {stats["media_group_hits"]}，'
                    f'邻条补齐 {stats["neighbor_hits"]}）…'
                ),
            )
            if self.run_coro is None:
                return {'authors': authors, 'stats': stats}
            try:
                authors[int(mid)] = self.run_coro(
                    _resolve_one(mid, progress_current=offset),
                    timeout=None,
                )
            except Exception:
                stats['errors'] += 1
                authors[int(mid)] = None
            done = min(offset + len(batch), total)
            self._report(
                on_progress,
                phase='resolving',
                current=done,
                total=total,
                message=(
                    f'按主贴 ID 回查 Telegram 作者 {done}/{total}'
                    f'（已命中 {stats["matched"]}，空消息 {stats["empty"]}，'
                    f'失败 {stats["errors"]}）…'
                ),
            )
            if done < total:
                self._pace(TELEGRAM_BATCH_PAUSE_SECONDS)
        return {'authors': authors, 'stats': stats}

    def _rewrite_store_paths(self, channel_folder: str, from_relative: str, to_relative: str) -> None:
        store = self.transfer_store
        if store is None or not hasattr(store, 'rewrite_source_folder_path'):
            return
        store.rewrite_source_folder_path(
            channel_folder=channel_folder,
            from_relative=from_relative,
            to_relative=to_relative,
        )
