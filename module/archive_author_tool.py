# coding=UTF-8
"""Scan/execute Post Author reorganization on PikPak Archive via rclone.

Designed for slow, serial operation to avoid PikPak / Telegram rate limits.
"""
from typing import Callable, Optional
import re
import time

from module.archive_reorganize import (
    AuthorHint,
    actions_for_execute_mode,
    known_authors_from_directory_paths,
    plan_author_reorganize,
    preserved_author_hints_from_plan,
)
from module.author_hashtag_match import (
    extract_hashtags_from_text,
    match_author_from_hashtags,
)
from module.pikpak_archive import (
    DisabledPikPakArchiveClient,
    join_remote_path,
    normalize_source_folder_path,
)
from module.source_folders import (
    is_post_folder_segment,
    message_id_from_post_folder_segment,
    post_author_from_message,
    post_author_from_telegram_message,
)


# Conservative pacing — serial moves; short pauses to avoid PikPak rate limits.
TELEGRAM_FETCH_BATCH = 1
TELEGRAM_BATCH_PAUSE_SECONDS = 2.0
RCLONE_LIST_PAUSE_SECONDS = 0.8
RCLONE_MOVE_PAUSE_SECONDS = 1.0
ProgressCallback = Optional[Callable[..., None]]
LogCallback = Optional[Callable[..., None]]
StopCallback = Optional[Callable[[], bool]]
CheckpointCallback = Optional[Callable[..., None]]
MISS_LOG_LIMIT = 40
ERROR_LOG_LIMIT = 40
MISS_SAMPLE_LIMIT = 20


def move_item_key(item: dict) -> str:
    """Stable checkpoint key for one planned directory move."""
    relative = str(item.get('from_relative') or '').replace('\\', '/').strip('/')
    if relative:
        return relative
    mid = item.get('message_id')
    if mid is not None:
        return f'mid:{mid}'
    return str(item.get('to_relative') or '').replace('\\', '/').strip('/')


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
            on_log: LogCallback = None,
    ):
        self.archive_client = archive_client
        self.telegram_client = telegram_client
        self.transfer_store = transfer_store
        self.run_coro = run_coro
        self.on_log = on_log

    def _log(
            self,
            *,
            stage: str,
            message: str,
            level: str = 'info',
            source_message_id: Optional[int] = None,
            details: Optional[dict] = None,
    ) -> None:
        if self.on_log is None:
            return
        try:
            self.on_log(
                stage=stage,
                message=message,
                level=level,
                source_message_id=source_message_id,
                details=details,
            )
        except Exception:
            pass

    @staticmethod
    def _message_full_text(message) -> str:
        if message is None:
            return ''
        parts = []
        for attr in ('caption', 'text'):
            text = getattr(message, attr, None)
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
        return '\n'.join(parts)

    @classmethod
    def _hashtags_from_message_body(cls, message) -> list[str]:
        """Extract #tags from caption/text and Telegram hashtag entities."""
        from module.author_hashtag_match import normalize_author_label

        tags = extract_hashtags_from_text(cls._message_full_text(message))
        if message is None:
            return tags
        seen = {normalize_author_label(tag) for tag in tags}
        for attr in ('caption', 'text'):
            body = getattr(message, attr, None)
            if not isinstance(body, str) or not body:
                continue
            entity_attr = 'caption_entities' if attr == 'caption' else 'entities'
            for entity in getattr(message, entity_attr, None) or []:
                type_name = type(entity).__name__
                entity_type = str(getattr(entity, 'type', '') or '')
                if (
                    'Hashtag' not in type_name
                    and entity_type.lower() not in ('hashtag', 'messageentityhashtag')
                ):
                    continue
                try:
                    offset = int(getattr(entity, 'offset', 0) or 0)
                    length = int(getattr(entity, 'length', 0) or 0)
                except (TypeError, ValueError):
                    continue
                if length <= 0:
                    continue
                chunk = body[offset:offset + length]
                source = chunk if '#' in chunk or '＃' in chunk else f'#{chunk}'
                for tag in extract_hashtags_from_text(source):
                    key = normalize_author_label(tag)
                    if key and key not in seen:
                        seen.add(key)
                        tags.append(tag)
        return tags

    @classmethod
    async def _collect_hashtags_for_resolve(
            cls,
            message,
            *,
            client=None,
            chat_id=None,
    ) -> list[str]:
        """Collect hashtags from the post, including media-group sibling captions."""
        from module.author_hashtag_match import normalize_author_label

        ordered: list[str] = []
        seen: set[str] = set()

        def _add_all(values):
            for tag in values or []:
                key = normalize_author_label(tag)
                if key and key not in seen:
                    seen.add(key)
                    ordered.append(tag)

        _add_all(cls._hashtags_from_message_body(message))
        if message is None or getattr(message, 'empty', False):
            return ordered

        group_messages = None
        get_media_group = getattr(message, 'get_media_group', None)
        if callable(get_media_group):
            try:
                group_messages = await get_media_group()
            except Exception:
                group_messages = None
        if not group_messages and client is not None and getattr(message, 'media_group_id', None):
            getter = getattr(client, 'get_media_group', None)
            if callable(getter):
                try:
                    group_messages = await getter(
                        chat_id=chat_id,
                        message_id=getattr(message, 'id', None),
                    )
                except Exception:
                    group_messages = None
        for item in group_messages or []:
            if item is None or item is message:
                continue
            _add_all(cls._hashtags_from_message_body(item))
        return ordered

    @classmethod
    def _message_text_preview(cls, message, limit: int = 180) -> str:
        text = cls._message_full_text(message)
        if not text:
            return ''
        compact = re.sub(r'\s+', ' ', text).strip()
        if len(compact) > limit:
            return compact[:limit] + '…'
        return compact

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
            resolve_scope: str = 'all',
    ) -> dict:
        """Resolve authors from Telegram using folder message ids — no rclone listing.

        ``resolve_scope='unresolved'`` keeps already-recognized authors from
        ``prior_plan`` and only refetches ``needs_review`` / ``_未知作者`` rows.
        """
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
        scope = str(resolve_scope or 'all').strip().lower() or 'all'
        preserved: dict[int, AuthorHint] = {}
        if scope in ('unresolved', 'review', 'needs_review', 'miss'):
            preserved = preserved_author_hints_from_plan(prior_plan)
            if not preserved and not (isinstance(prior_plan, dict) and prior_plan.get('moves')):
                raise RuntimeError(
                    '没有可复用的解析计划。请先完整「重新解析作者」一次，'
                    '之后才能「仅解析未识别」。'
                )
        fetch_ids = [mid for mid in unique_ids if mid not in preserved]
        known_seed = known_authors_from_directory_paths(channel, paths)
        for hint in preserved.values():
            if hint.name:
                known_seed.add(hint.name)

        if self.telegram_client is None:
            if require_telegram:
                raise RuntimeError('Telegram 客户端未就绪，无法按主贴 ID 解析作者。')
            author_by_id = {mid: AuthorHint() for mid in unique_ids}
            author_by_id.update(preserved)
            resolved = sum(1 for mid in unique_ids if getattr(author_by_id.get(mid), 'name', None))
            miss_samples = []
            resolve_stats = {
                'fetched': 0,
                'empty': 0,
                'matched': 0,
                'errors': 0,
                'missed': 0,
                'media_group_hits': 0,
                'neighbor_hits': 0,
                'hashtag_exact_hits': 0,
                'hashtag_substring_hits': 0,
                'hashtag_candidate_hits': 0,
                'preserved': len(preserved),
                'refetch': len(fetch_ids),
                'resolve_scope': scope,
            }
        else:
            self._report(
                on_progress,
                phase='resolving',
                current=0,
                total=max(len(fetch_ids), 1),
                message=(
                    f'按主贴 ID 回查 Telegram 作者 0/{len(fetch_ids)}'
                    f'（保留已识别 {len(preserved)}，不扫网盘）…'
                    if preserved
                    else f'按主贴 ID 回查 Telegram 作者 0/{len(unique_ids)}（不扫网盘）…'
                ),
            )
            resolve_payload = self._resolve_authors(
                channel,
                fetch_ids,
                on_progress=on_progress,
                known_authors=known_seed,
            )
            author_by_id = dict(preserved)
            author_by_id.update(resolve_payload.get('resolutions') or {})
            for mid in unique_ids:
                author_by_id.setdefault(mid, AuthorHint())
            resolve_stats = dict(resolve_payload.get('stats') or {})
            resolve_stats['preserved'] = len(preserved)
            resolve_stats['refetch'] = len(fetch_ids)
            resolve_stats['resolve_scope'] = scope
            miss_samples = resolve_payload.get('miss_samples') or []
            resolved = sum(
                1 for mid in unique_ids
                if getattr(author_by_id.get(mid), 'name', None)
                or (isinstance(author_by_id.get(mid), str) and author_by_id.get(mid))
            )
        self._report(
            on_progress,
            phase='planning',
            current=len(unique_ids),
            total=max(len(unique_ids), 1),
            message=(
                f'已解析作者 {resolved}/{len(unique_ids)}'
                f'（抓取 {resolve_stats.get("fetched") or 0}，'
                f'空消息 {resolve_stats.get("empty") or 0}，'
                f'未命中 {resolve_stats.get("missed") or 0}，'
                f'相册补齐 {resolve_stats.get("media_group_hits") or 0}，'
                f'邻条补齐 {resolve_stats.get("neighbor_hits") or 0}，'
                f'标签精确 {resolve_stats.get("hashtag_exact_hits") or 0}，'
                f'标签待确认 {resolve_stats.get("hashtag_substring_hits") or 0}），'
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
        payload['resolve_scope'] = scope
        payload['resolve_stats'] = resolve_stats
        payload['miss_samples'] = miss_samples if self.telegram_client is not None else []
        self._report(
            on_progress,
            phase='done',
            current=payload.get('executable_count') or payload.get('move_count') or 0,
            total=max(
                int(payload.get('executable_count') or 0)
                + int(payload.get('review_count') or 0)
                + int(payload.get('skip_count') or 0),
                1,
            ),
            message=(
                f'{done_label}：解析到作者 {resolved}/{len(unique_ids)}'
                f'（抓取 {resolve_stats.get("fetched") or 0}，'
                f'空 {resolve_stats.get("empty") or 0}，'
                f'未命中 {resolve_stats.get("missed") or 0}，'
                f'相册 {resolve_stats.get("media_group_hits") or 0}，'
                f'邻条 {resolve_stats.get("neighbor_hits") or 0}，'
                f'标签精确 {resolve_stats.get("hashtag_exact_hits") or 0}，'
                f'标签待确认 {resolve_stats.get("hashtag_substring_hits") or 0}），'
                f'{payload.get("author_count") or 0} 个作者目录，'
                f'待移动 {payload.get("move_count") or 0}，'
                f'待确认 {payload.get("confirm_count") or 0}，'
                f'未识别 {payload.get("review_count") or 0}，'
                f'跳过 {payload.get("skip_count") or 0}'
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

    def execute_plan(
            self,
            plan: dict,
            on_progress: ProgressCallback = None,
            *,
            execute_mode: str = 'all',
            completed_keys: Optional[set] = None,
            should_stop: StopCallback = None,
            on_checkpoint: CheckpointCallback = None,
    ) -> dict:
        client = self._require_client()
        channel = plan.get('channel_folder') or ''
        root = plan.get('channel_remote_root') or self._channel_remote_root(client, channel)
        mode = str(execute_mode or 'all').strip().lower() or 'all'
        allowed = actions_for_execute_mode(mode)
        move_items = [
            item for item in (plan.get('moves') or [])
            if item.get('action') in allowed
        ]
        done_keys = {
            str(key).replace('\\', '/').strip('/')
            for key in (completed_keys or set())
            if str(key).strip()
        }
        moved = []
        errors = []
        skipped_already = []
        total = len(move_items)
        ensured_parents: set[str] = set()
        listing_cache: dict[str, set[str]] = {}
        stopped = False
        processed = 0
        self._report(
            on_progress,
            phase='moving',
            current=len(done_keys),
            total=total,
            message=(
                f'串行移动目录 {len(done_keys)}/{total}'
                f'（间隔 {RCLONE_MOVE_PAUSE_SECONDS:.1f}s）…'
            ),
        )

        def emit_checkpoint(*, stopped_now: bool = False) -> None:
            if on_checkpoint is None:
                return
            try:
                on_checkpoint(
                    completed_keys=sorted(done_keys),
                    moved_count=len(moved),
                    error_count=len(errors),
                    skipped_already_count=len(skipped_already),
                    current=processed,
                    total=total,
                    stopped=stopped_now,
                    execute_mode=mode,
                    channel_folder=channel,
                    errors=list(errors),
                )
            except Exception:
                pass

        for item in move_items:
            if should_stop is not None and should_stop():
                stopped = True
                break
            key = move_item_key(item)
            from_rel = item['from_relative']
            to_rel = item['to_relative']
            source = join_remote_path(root, from_rel)
            target = join_remote_path(root, to_rel)
            processed += 1

            if key and key in done_keys:
                skipped_already.append(item)
                self._report(
                    on_progress,
                    phase='moving',
                    current=processed,
                    total=total,
                    message=f'正在移动目录 {processed}/{total}（跳过已完成）…',
                )
                continue

            if self._directory_exists(client, source, listing_cache):
                parent = '/'.join(str(to_rel).replace('\\', '/').split('/')[:-1])
                if parent and parent not in ensured_parents:
                    try:
                        client.ensure_directory(join_remote_path(root, parent))
                        ensured_parents.add(parent)
                        listing_cache.pop(join_remote_path(root, parent), None)
                        self._pace(RCLONE_LIST_PAUSE_SECONDS)
                    except Exception:
                        pass
                try:
                    client.move_directory(source, target)
                    moved.append(item)
                    if key:
                        done_keys.add(key)
                    self._invalidate_listing_cache(listing_cache, source)
                    self._invalidate_listing_cache(listing_cache, target)
                    if self.transfer_store is not None:
                        self._rewrite_store_paths(channel, from_rel, to_rel)
                except Exception as error:
                    # Idempotent: source vanished while target already present.
                    self._invalidate_listing_cache(listing_cache, source)
                    self._invalidate_listing_cache(listing_cache, target)
                    if (
                        not self._directory_exists(client, source, listing_cache)
                        and self._directory_exists(client, target, listing_cache)
                    ):
                        skipped_already.append(item)
                        if key:
                            done_keys.add(key)
                    else:
                        errors.append({
                            'from_relative': from_rel,
                            'to_relative': to_rel,
                            'error': str(error),
                        })
            elif self._directory_exists(client, target, listing_cache):
                skipped_already.append(item)
                if key:
                    done_keys.add(key)
            else:
                errors.append({
                    'from_relative': from_rel,
                    'to_relative': to_rel,
                    'error': '源目录与目标目录均不存在',
                })

            self._report(
                on_progress,
                phase='moving',
                current=processed,
                total=total,
                message=f'正在移动目录 {processed}/{total}（串行）…',
            )
            emit_checkpoint()
            if processed < total and not (should_stop is not None and should_stop()):
                self._pace(RCLONE_MOVE_PAUSE_SECONDS)

        if stopped:
            emit_checkpoint(stopped_now=True)
            result = {
                'channel_folder': channel,
                'author_count': plan.get('author_count'),
                'authors': plan.get('authors') or [],
                'planned_moves': len(move_items),
                'execute_mode': mode,
                'moved_count': len(moved),
                'error_count': len(errors),
                'skipped_already_count': len(skipped_already),
                'moved': moved,
                'errors': errors,
                'skipped_already': skipped_already,
                'completed_from_relatives': sorted(done_keys),
                'stopped': True,
                'skips': [
                    item for item in (plan.get('moves') or [])
                    if item.get('action') not in allowed
                ],
                'channel_remote_root': root,
            }
            self._report(
                on_progress,
                phase='stopped',
                current=processed,
                total=max(total, 1),
                message=(
                    f'已停止：完成 {processed}/{total}，'
                    f'新移动 {len(moved)}，已就位跳过 {len(skipped_already)}，'
                    f'失败 {len(errors)}'
                ),
            )
            return result

        result = {
            'channel_folder': channel,
            'author_count': plan.get('author_count'),
            'authors': plan.get('authors') or [],
            'planned_moves': len(move_items),
            'execute_mode': mode,
            'moved_count': len(moved),
            'error_count': len(errors),
            'skipped_already_count': len(skipped_already),
            'moved': moved,
            'errors': errors,
            'skipped_already': skipped_already,
            'completed_from_relatives': sorted(done_keys),
            'stopped': False,
            'skips': [
                item for item in (plan.get('moves') or [])
                if item.get('action') not in allowed
            ],
            'channel_remote_root': root,
        }
        self._report(
            on_progress,
            phase='done',
            current=total,
            total=max(total, 1),
            message=(
                f'整理完成：新移动 {len(moved)}，'
                f'已就位跳过 {len(skipped_already)}，失败 {len(errors)}'
            ),
        )
        emit_checkpoint()
        return result

    @staticmethod
    def _invalidate_listing_cache(cache: dict[str, set[str]], remote_path: str) -> None:
        path = str(remote_path or '').replace('\\', '/').strip('/')
        if not path:
            return
        parent = path.rsplit('/', 1)[0] if '/' in path else ''
        cache.pop(parent, None)
        cache.pop(path, None)

    @classmethod
    def _directory_exists(
            cls,
            client,
            remote_path: str,
            cache: Optional[dict[str, set[str]]] = None,
    ) -> bool:
        path = str(remote_path or '').replace('\\', '/').strip('/')
        if not path:
            return False
        exists_fn = getattr(client, 'directory_exists', None)
        if callable(exists_fn) and cache is None:
            try:
                return bool(exists_fn(path))
            except Exception:
                return False
        parent, _, leaf = path.rpartition('/')
        if not leaf:
            return False
        names: Optional[set[str]] = None
        if cache is not None and parent in cache:
            names = cache[parent]
        else:
            list_fn = getattr(client, 'list_directories', None)
            if not callable(list_fn):
                if callable(exists_fn):
                    try:
                        return bool(exists_fn(path))
                    except Exception:
                        return False
                return False
            try:
                listed = list_fn(parent, recursive=False) if parent else list_fn('', recursive=False)
            except TypeError:
                try:
                    listed = list_fn(parent) if parent else list_fn('')
                except Exception:
                    listed = []
            except Exception:
                listed = []
            names = set()
            for item in listed or []:
                text = str(item or '').replace('\\', '/').strip('/')
                if not text:
                    continue
                names.add(text.rsplit('/', 1)[-1])
            if cache is not None:
                cache[parent] = names
        return leaf in (names or set())

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
            *,
            known_authors: Optional[set[str]] = None,
    ) -> dict:
        empty_stats = {
            'fetched': 0,
            'empty': 0,
            'matched': 0,
            'errors': 0,
            'missed': 0,
            'media_group_hits': 0,
            'neighbor_hits': 0,
            'hashtag_exact_hits': 0,
            'hashtag_substring_hits': 0,
            'hashtag_candidate_hits': 0,
        }
        if not message_ids:
            return {'authors': {}, 'resolutions': {}, 'stats': empty_stats, 'miss_samples': []}
        if self.telegram_client is None:
            self._log(
                stage='author_resolve',
                message=f'{channel_folder}: Telegram 客户端为空，无法解析作者',
                level='error',
            )
            return {
                'authors': {mid: None for mid in message_ids},
                'resolutions': {mid: AuthorHint() for mid in message_ids},
                'stats': {
                    **empty_stats,
                    'errors': len(message_ids),
                    'missed': len(message_ids),
                },
                'miss_samples': [],
            }

        import asyncio

        flood_types: tuple = ()
        try:
            from pyrogram.errors import FloodWait, FloodPremiumWait
            flood_types = (FloodWait, FloodPremiumWait)
        except Exception:  # pragma: no cover - stub environments
            flood_types = ()

        resolutions: dict[int, AuthorHint] = {mid: AuthorHint() for mid in message_ids}
        pending_tags: dict[int, list[str]] = {}
        client = self.telegram_client
        total = len(message_ids)
        stats = dict(empty_stats)
        miss_samples: list[dict] = []
        chat_id = channel_folder
        self._log(
            stage='author_resolve',
            message=f'{channel_folder}: 开始按主贴 ID 解析作者，共 {total} 条',
            level='info',
            details={'message_id_count': total},
        )

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
                    self._log(
                        stage='author_resolve',
                        message=(
                            f'{channel_folder}: FloodWait {wait_seconds}s '
                            f'@ {progress_current}/{total}'
                        ),
                        level='warning',
                        details={'wait_seconds': wait_seconds},
                    )
                    await asyncio.sleep(wait_seconds + 1)

        def _as_list(value):
            if value is None:
                return []
            if isinstance(value, list):
                return value
            return [value]

        def _record_miss(mid: int, *, reason: str, preview: str = '', via: str = 'primary'):
            stats['missed'] += 1
            sample = {
                'message_id': mid,
                'reason': reason,
                'via': via,
                'preview': preview or '',
            }
            if len(miss_samples) < MISS_SAMPLE_LIMIT:
                miss_samples.append(sample)
            should_log = (
                stats['missed'] <= MISS_LOG_LIMIT
                or stats['missed'] % 50 == 0
            )
            if should_log:
                self._log(
                    stage='author_resolve',
                    message=(
                        f'{channel_folder}: 未解析到作者 message_id={mid} '
                        f'reason={reason} via={via}'
                    ),
                    level='warning',
                    source_message_id=mid,
                    details=sample,
                )

        def _record_error(mid: int, error: Exception):
            stats['errors'] += 1
            if stats['errors'] <= ERROR_LOG_LIMIT or stats['errors'] % 50 == 0:
                self._log(
                    stage='author_resolve',
                    message=(
                        f'{channel_folder}: 拉取失败 message_id={mid} '
                        f'{error.__class__.__name__}: {error}'
                    ),
                    level='error',
                    source_message_id=mid,
                    details={
                        'error': str(error),
                        'error_type': error.__class__.__name__,
                    },
                )

        async def _resolve_one(mid: int, *, progress_current: int) -> AuthorHint:
            try:
                raw = await _fetch_messages([mid], progress_current=progress_current)
            except Exception as error:
                _record_error(mid, error)
                return AuthorHint()
            messages = _as_list(raw)
            message = messages[0] if messages else None
            if message is None or getattr(message, 'empty', False):
                stats['empty'] += 1
                neighbor_ids = [mid + offset for offset in range(1, 6)]
                try:
                    raw_neighbors = await _fetch_messages(
                        neighbor_ids,
                        progress_current=progress_current,
                    )
                except Exception as error:
                    _record_error(mid, error)
                    _record_miss(mid, reason='empty_primary', via='empty')
                    return AuthorHint()
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
                        return AuthorHint(
                            name=author,
                            confidence='medium',
                            method='neighbor',
                        )
                _record_miss(mid, reason='empty_primary_and_neighbors', via='empty')
                return AuthorHint()

            stats['fetched'] += 1
            preview = self._message_text_preview(message)
            tags = await self._collect_hashtags_for_resolve(
                message,
                client=client,
                chat_id=chat_id,
            )
            author = await post_author_from_telegram_message(
                message,
                client=client,
                chat_id=chat_id,
            )
            if author:
                method = 'signature' if post_author_from_message(message) else 'media_group'
                if method == 'media_group':
                    stats['media_group_hits'] += 1
                stats['matched'] += 1
                return AuthorHint(
                    name=author,
                    confidence='high',
                    method=method,
                    preview=preview,
                )

            neighbor_ids = [mid + offset for offset in range(1, 4)]
            try:
                raw_neighbors = await _fetch_messages(
                    neighbor_ids,
                    progress_current=progress_current,
                )
            except Exception as error:
                _record_error(mid, error)
                if tags:
                    pending_tags[mid] = tags
                _record_miss(
                    mid,
                    reason='no_author_marker',
                    preview=preview,
                    via='primary',
                )
                return AuthorHint(preview=preview)
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
                    return AuthorHint(
                        name=author,
                        confidence='medium',
                        method='neighbor',
                        preview=preview,
                    )
            neighbor_preview = self._message_text_preview(
                next((m for m in _as_list(raw_neighbors) if m is not None), None)
            )
            if tags:
                pending_tags[mid] = tags
            _record_miss(
                mid,
                reason='no_author_marker',
                preview=preview or neighbor_preview,
                via='primary+neighbors',
            )
            return AuthorHint(preview=preview or neighbor_preview)

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
                authors = {key: hint.name for key, hint in resolutions.items()}
                return {
                    'authors': authors,
                    'resolutions': resolutions,
                    'stats': stats,
                    'miss_samples': miss_samples,
                }
            try:
                resolutions[int(mid)] = self.run_coro(
                    _resolve_one(mid, progress_current=offset),
                    timeout=None,
                )
            except Exception as error:
                _record_error(mid, error)
                resolutions[int(mid)] = AuthorHint()
            done = min(offset + len(batch), total)
            self._report(
                on_progress,
                phase='resolving',
                current=done,
                total=total,
                message=(
                    f'按主贴 ID 回查 Telegram 作者 {done}/{total}'
                    f'（已命中 {stats["matched"]}，空消息 {stats["empty"]}，'
                    f'未命中 {stats["missed"]}，失败 {stats["errors"]}）…'
                ),
            )
            if done < total:
                self._pace(TELEGRAM_BATCH_PAUSE_SECONDS)

        known = set(known_authors or set())
        for hint in resolutions.values():
            if hint.name:
                known.add(hint.name)
        if pending_tags and known:
            self._report(
                on_progress,
                phase='resolving',
                current=total,
                total=total,
                message=f'用已知作者回连标签（候选 {len(pending_tags)}）…',
            )
            for mid, tags in pending_tags.items():
                if resolutions.get(mid) and resolutions[mid].name:
                    continue
                matched = match_author_from_hashtags(
                    tags,
                    known,
                    extra_deny=[channel_folder],
                )
                if not matched.author:
                    continue
                resolutions[mid] = AuthorHint(
                    name=matched.author,
                    confidence=matched.confidence,
                    method=matched.method,
                    matched_tag=matched.matched_tag,
                    preview=resolutions[mid].preview if mid in resolutions else '',
                )
                stats['matched'] += 1
                stats['missed'] = max(0, stats['missed'] - 1)
                if matched.method == 'hashtag_exact':
                    stats['hashtag_exact_hits'] += 1
                elif matched.method == 'hashtag_candidate':
                    stats['hashtag_candidate_hits'] += 1
                    stats['hashtag_substring_hits'] += 1
                else:
                    stats['hashtag_substring_hits'] += 1

        authors = {mid: hint.name for mid, hint in resolutions.items()}
        self._log(
            stage='author_resolve',
            message=(
                f'{channel_folder}: 解析结束 '
                f'matched={stats["matched"]}/{total} '
                f'fetched={stats["fetched"]} empty={stats["empty"]} '
                f'missed={stats["missed"]} errors={stats["errors"]} '
                f'media_group={stats["media_group_hits"]} '
                f'neighbor={stats["neighbor_hits"]} '
                f'hashtag_exact={stats["hashtag_exact_hits"]} '
                f'hashtag_substring={stats["hashtag_substring_hits"]}'
            ),
            level='info' if stats['matched'] else 'warning',
            details=dict(stats),
        )
        return {
            'authors': authors,
            'resolutions': resolutions,
            'stats': stats,
            'miss_samples': miss_samples,
        }

    def _rewrite_store_paths(self, channel_folder: str, from_relative: str, to_relative: str) -> None:
        store = self.transfer_store
        if store is None or not hasattr(store, 'rewrite_source_folder_path'):
            return
        store.rewrite_source_folder_path(
            channel_folder=channel_folder,
            from_relative=from_relative,
            to_relative=to_relative,
        )
