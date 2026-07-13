# coding=UTF-8
import asyncio
import datetime
import random
from typing import Optional, Protocol, Union, runtime_checkable

import pyrogram
from pyrogram.errors import FloodWait, FloodPremiumWait
from pyrogram.errors.exceptions.bad_request_400 import (
    MsgIdInvalid,
    ChannelInvalid,
    UsernameInvalid,
    ChatForwardsRestricted as ChatForwardsRestricted_400,
    MediaCaptionTooLong as MediaCaptionTooLong_400,
    ChannelPrivate as ChannelPrivate_400,
)
from pyrogram.errors.exceptions.not_acceptable_406 import (
    ChatForwardsRestricted as ChatForwardsRestricted_406,
    ChannelPrivate as ChannelPrivate_406,
)

from module import log
from module.enums import DownloadStatus, DownloadType
from module.source_folders import source_folder_from_message
from module.transfer.deep_link import DeepLinkResolveError
from module.transfer_store import TransferStatus
from module.uploader import TelegramUploader
from module.util import get_message_by_link, iter_discussion_reply_messages


@runtime_checkable
class WebTransferHost(Protocol):
    """Host dependencies for web transfer task execution."""
    app: object
    gc: object
    loop: asyncio.AbstractEventLoop
    transfer_store: object
    uploader: object
    transfer_engine: object

    def should_continue_web_transfer_task(self, task_id: int) -> bool: ...
    async def wait_for_telegram_flood(self, error, task_id: Optional[int] = None, action: str = 'request') -> None: ...
    async def forward(self, **kwargs): ...
    async def create_download_task(self, **kwargs) -> dict: ...
    def check_type(self, message) -> bool: ...
    def build_transfer_upload_meta(self, task: dict, source_link: str = None, media_type: str = None) -> dict: ...
    def skip_transfer_item_for_target_limit(self, task: dict, message, source_link: str, origin_chat_id, limit_error: dict) -> int: ...
    def refresh_transfer_task_counts(self, task_id: int) -> None: ...
    def find_resumable_transfer_item(self, task_id: int, source_message_id: int, source_chat_id=None): ...
    def skip_missing_web_transfer_range_message(self, task: dict, origin_chat_id, source_link: str, message_id: int) -> None: ...
    async def parse_web_transfer_link(self, client, link: str) -> dict: ...

    @property
    def pikpak_target(self): ...


class WebTransferRunner:
    def __init__(self, host: WebTransferHost):
        self._host = host

    def _resolve_method(self, name: str):
        host_type = type(self._host)
        instance_method = getattr(self._host, name)
        class_method = getattr(host_type, name, None)
        if instance_method is not class_method:
            return instance_method
        return getattr(self, name)

    @staticmethod
    def transfer_send_interval() -> float:
        return random.uniform(0.8, 2.4)

    async def wait_between_transfer_messages(self) -> None:
        await asyncio.sleep(self.transfer_send_interval())

    def should_continue_web_transfer_task(self, task_id: int) -> bool:
        wm = getattr(self._host, 'web_task_manager', None)
        if wm is not None:
            return wm.should_continue_web_transfer_task(task_id)
        transfer_store = self._host.transfer_store
        if not transfer_store or not task_id:
            return False
        task = transfer_store.get_task(int(task_id))
        return bool(task and task.get('status') != TransferStatus.PAUSED)

    async def process_task(self, task_id: int) -> None:
        host = self._host
        if not host.transfer_store:
            return
        task = host.transfer_store.get_task(task_id)
        if not task:
            return
        if task.get('status') not in (TransferStatus.PENDING, TransferStatus.RUNNING, TransferStatus.FAILURE):
            return
        host.transfer_store.update_task(task_id, status=TransferStatus.RUNNING, started=True)
        host.transfer_store.add_event(task_id, 'Transfer task started.')
        try:
            if not host.uploader:
                ensure_uploader = getattr(host, 'ensure_uploader', None)
                if callable(ensure_uploader):
                    ensure_uploader()
                else:
                    host.uploader = TelegramUploader(upload_context=host)
            source_link = task.get('source_link')
            start_id = task.get('start_id')
            end_id = task.get('end_id')
            include_comment = bool(task.get('include_comment'))
            origin_meta = await host.parse_web_transfer_link(host.app.client, source_link)
            target_meta = await host.parse_web_transfer_link(host.app.client, task.get('target_link'))
            origin_chat_id = origin_meta.get('chat_id')
            target_chat_id = target_meta.get('chat_id')
            if not all([origin_chat_id, target_chat_id]):
                raise ValueError('Invalid source or target link.')
            fallback_count = 0
            if start_id is not None and end_id is not None:
                source_prefix = source_link.rstrip('/')
                expected_total = int(end_id) - int(start_id) + 1
                existing_total = int(task.get('total_items') or 0)
                if existing_total > expected_total:
                    expected_total = existing_total
                completed_message_ids = host.transfer_store.completed_source_message_ids(task_id)
                host.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=expected_total,
                    assignment_completed=False
                )
                await self.resume_orphan_resumable_items(
                    task=task,
                    start_id=int(start_id),
                    end_id=int(end_id)
                )
                for message_id in range(int(start_id), int(end_id) + 1):
                    if not self.should_continue_web_transfer_task(task_id):
                        latest_task = host.transfer_store.get_task(task_id)
                        if latest_task and latest_task.get('status') == TransferStatus.PAUSED:
                            host.transfer_store.add_event(
                                task_id,
                                f'Transfer task paused before message: {message_id}.'
                            )
                        return
                    if host.transfer_store.is_range_message_complete(task_id, message_id):
                        continue
                    host.transfer_store.update_task_range_runtime(
                        task_id,
                        current_range_message_id=message_id,
                        current_range_video_captured=0,
                        current_range_video_index=0
                    )
                    range_video_seq = 0
                    resumed_count = await self.resume_interrupted_items_for_range_message(task, message_id)
                    if resumed_count:
                        fallback_count += resumed_count
                        if host.transfer_store.is_range_message_complete(task_id, message_id):
                            continue
                    main_post_done = message_id in completed_message_ids
                    if main_post_done and include_comment:
                        range_video_seq = len(host.transfer_store.list_items_for_range_message(task_id, message_id))
                        reply_count, reply_fallback_count = await self._resolve_method(
                            'transfer_web_discussion_replies_to_target'
                        )(
                            task=task,
                            source_chat_id=origin_chat_id,
                            source_message_id=message_id,
                            target_chat_id=target_chat_id,
                            expected_total=expected_total,
                            range_video_seq=range_video_seq
                        )
                        expected_total += reply_count
                        fallback_count += reply_fallback_count
                        continue
                    if main_post_done:
                        continue
                    if host.find_resumable_transfer_item(task_id, message_id, origin_chat_id):
                        try:
                            await self._resolve_method('wait_between_transfer_messages')()
                            message = await self._resolve_method('get_web_transfer_range_message')(
                                origin_chat_id, message_id, task_id
                            )
                            if message:
                                message_link = f'{source_prefix}/{getattr(message, "id", "")}'
                                await self.create_web_transfer_fallback_download(
                                    task=task,
                                    source_link=message_link,
                                    message=message,
                                    range_message_id=message_id
                                )
                                fallback_count += 1
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            log.error(
                                f'Web transfer resume download failed: task={task_id}, message={message_id}, reason="{e}"',
                                exc_info=True
                            )
                            host.transfer_store.add_event(
                                task_id,
                                f'Resume download failed: {message_id}: {e}',
                                level='error'
                            )
                        continue
                    try:
                        await self._resolve_method('wait_between_transfer_messages')()
                        message = await self._resolve_method('get_web_transfer_range_message')(
                            origin_chat_id, message_id, task_id
                        )
                        if not message:
                            self._resolve_method('skip_missing_web_transfer_range_message')(
                                task=task,
                                origin_chat_id=origin_chat_id,
                                source_link=source_link,
                                message_id=message_id
                            )
                            continue
                        message_link = f'{source_prefix}/{getattr(message, "id", "")}'
                        range_video_seq += 1
                        host.transfer_store.update_task_range_runtime(
                            task_id,
                            current_range_message_id=message_id,
                            current_range_video_captured=range_video_seq,
                            current_range_video_index=range_video_seq
                        )
                        used_fallback = await self._resolve_method('transfer_message_to_web_target')(
                            task=task,
                            message=message,
                            origin_chat_id=origin_chat_id,
                            target_chat_id=target_chat_id,
                            source_link=message_link,
                            range_message_id=message_id
                        )
                        fallback_count += 1 if used_fallback else 0
                        if include_comment:
                            reply_count, reply_fallback_count = await self._resolve_method(
                                'transfer_web_discussion_replies_to_target'
                            )(
                                task=task,
                                source_chat_id=origin_chat_id,
                                source_message_id=message_id,
                                target_chat_id=target_chat_id,
                                expected_total=expected_total,
                                range_video_seq=range_video_seq
                            )
                            expected_total += reply_count
                            fallback_count += reply_fallback_count
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        log.error(
                            f'Web transfer message failed: task={task_id}, message={message_id}, reason="{e}"',
                            exc_info=True
                        )
                        host.transfer_store.add_event(
                            task_id,
                            f'Transfer message failed: {message_id}: {e}',
                            level='error'
                        )
                        continue
                host.transfer_store.add_event(
                    task_id,
                    f'Range transfer assigned: {start_id}-{end_id}. Fallback downloads: {fallback_count}.'
                )
                host.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=expected_total,
                    assignment_completed=True
                )
            else:
                single_expected = 1
                existing_total = int(task.get('total_items') or 0)
                if existing_total > single_expected:
                    single_expected = existing_total
                host.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=single_expected,
                    assignment_completed=False
                )
                message = await self._resolve_method('get_web_transfer_single_message')(source_link)
                if not message:
                    raise RuntimeError('Failed to load transfer message.')
                completed_message_ids = host.transfer_store.completed_source_message_ids(task_id)
                message_id = getattr(message, 'id', None)
                fallback_count = 0
                expected_total = single_expected
                if message_id not in completed_message_ids:
                    if not self.should_continue_web_transfer_task(task_id):
                        return
                    if host.find_resumable_transfer_item(task_id, message_id, origin_chat_id):
                        try:
                            await self.create_web_transfer_fallback_download(
                                task=task,
                                source_link=source_link,
                                message=message,
                                range_message_id=message_id
                            )
                            fallback_count = 1
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            log.error(
                                f'Web transfer resume download failed: task={task_id}, message={message_id}, reason="{e}"',
                                exc_info=True
                            )
                            host.transfer_store.add_event(
                                task_id,
                                f'Resume download failed: {message_id}: {e}',
                                level='error'
                            )
                    else:
                        host.transfer_store.update_task_range_runtime(
                            task_id,
                            current_range_message_id=message_id,
                            current_range_video_captured=1,
                            current_range_video_index=1
                        )
                        fallback_count = 1 if await self._resolve_method('transfer_message_to_web_target')(
                            task=task,
                            message=message,
                            origin_chat_id=origin_chat_id,
                            target_chat_id=target_chat_id,
                            source_link=source_link,
                            range_message_id=message_id
                        ) else 0
                    if include_comment:
                        reply_count, reply_fallback_count = await self._resolve_method(
                            'transfer_web_discussion_replies_to_target'
                        )(
                            task=task,
                            source_chat_id=origin_chat_id,
                            source_message_id=message_id,
                            target_chat_id=target_chat_id,
                            expected_total=1,
                            range_video_seq=1 if message_id not in completed_message_ids else 0
                        )
                        fallback_count += reply_fallback_count
                        expected_total += reply_count
                        host.transfer_store.refresh_task_counts(
                            task_id,
                            expected_total=expected_total,
                            assignment_completed=False
                        )
                host.transfer_store.add_event(
                    task_id,
                    f'Single-message transfer assigned. Fallback downloads: {fallback_count}.'
                )
                host.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=expected_total,
                    assignment_completed=True
                )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.error(
                f'Web transfer task failed: task={task_id}, reason="{e}"',
                exc_info=True
            )
            if host.transfer_store.get_task(task_id):
                host.transfer_store.update_task(
                    task_id,
                    status=TransferStatus.FAILURE,
                    error_message=str(e),
                    finished=True
                )
                host.transfer_store.add_event(task_id, f'Transfer task failed: {e}', level='error')

    async def resume_transfer_item_download(
            self,
            task: dict,
            item: dict,
            range_message_id: Optional[int] = None
    ) -> None:
        source_link = item.get('source_link')
        if not source_link:
            raise RuntimeError(f'Missing source link for resumable item #{item.get("id")}.')
        await self.create_web_transfer_fallback_download(
            task=task,
            source_link=source_link,
            range_message_id=range_message_id or item.get('range_message_id')
        )

    async def resume_interrupted_items_for_range_message(
            self,
            task: dict,
            range_message_id: int
    ) -> int:
        host = self._host
        if not host.transfer_store:
            return 0
        task_id = int(task.get('id'))
        resumed = 0
        for item in host.transfer_store.list_resumable_items_for_range_message(task_id, range_message_id):
            try:
                await self._resolve_method('wait_between_transfer_messages')()
                await self.resume_transfer_item_download(
                    task=task,
                    item=item,
                    range_message_id=range_message_id
                )
                resumed += 1
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error(
                    f'Web transfer resume item failed: task={task_id}, item={item.get("id")}, reason="{e}"',
                    exc_info=True
                )
                host.transfer_store.add_event(
                    task_id,
                    f'Resume item failed: {item.get("file_name") or item.get("id")}: {e}',
                    level='error',
                    item_id=item.get('id')
                )
        return resumed

    async def resume_orphan_resumable_items(
            self,
            task: dict,
            start_id: int,
            end_id: int
    ) -> int:
        host = self._host
        if not host.transfer_store:
            return 0
        task_id = int(task.get('id'))
        anchor_id = task.get('current_range_message_id')
        if anchor_id is None:
            for message_id in range(int(start_id), int(end_id) + 1):
                if not host.transfer_store.is_range_message_complete(task_id, message_id):
                    anchor_id = message_id
                    break
        if anchor_id is None:
            return 0
        anchor_id = int(anchor_id)
        resumed = 0
        resumable_statuses = {TransferStatus.RUNNING, TransferStatus.PENDING}
        resumable_phases = host.transfer_store._resumable_item_phases()
        for item in host.transfer_store.list_items(task_id):
            if item.get('range_message_id') is not None:
                continue
            if str(item.get('status') or '') not in resumable_statuses:
                continue
            if str(item.get('phase') or '') not in resumable_phases:
                continue
            item_id = int(item.get('id') or 0)
            if not item_id:
                continue
            host.transfer_store.update_item(item_id, range_message_id=anchor_id)
            item = host.transfer_store.get_item(item_id) or item
            try:
                await self._resolve_method('wait_between_transfer_messages')()
                await self.resume_transfer_item_download(
                    task=task,
                    item=item,
                    range_message_id=anchor_id
                )
                resumed += 1
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error(
                    f'Web transfer resume orphan item failed: task={task_id}, item={item_id}, reason="{e}"',
                    exc_info=True
                )
                host.transfer_store.add_event(
                    task_id,
                    f'Resume orphan item failed: {item.get("file_name") or item_id}: {e}',
                    level='error',
                    item_id=item_id
                )
        return resumed

    async def create_web_transfer_fallback_download(
            self,
            task: dict,
            source_link: Optional[str] = None,
            message: Optional[pyrogram.types.Message] = None,
            range_message_id: Optional[int] = None
    ) -> None:
        host = self._host
        message_ids = message if message is not None else self.transfer_single_link(source_link)
        task_result = await host.create_download_task(
            message_ids=message_ids,
            retry=None,
            single_link=True,
            with_upload=host.build_transfer_upload_meta(
                task=task,
                source_link=source_link,
                range_message_id=range_message_id
            ),
            diy_download_type=[_ for _ in DownloadType()]
        )
        if task_result.get('status') == DownloadStatus.FAILURE:
            error = task_result.get('e_code') or {}
            raise RuntimeError(error.get('error_msg') or error.get('all_member') or 'Failed to create transfer item.')

    async def transfer_message_to_web_target(
            self,
            task: dict,
            message,
            origin_chat_id,
            target_chat_id,
            source_link: str,
            range_message_id: Optional[int] = None
    ) -> bool:
        host = self._host
        message_id = getattr(message, 'id', None)
        if getattr(message, 'empty', False):
            host.skip_empty_transfer_source_message(
                task=task,
                origin_chat_id=origin_chat_id,
                source_link=source_link,
                message_id=message_id
            )
            return False
        channel_message = message
        channel_source_folder = source_folder_from_message(
            channel_message,
            fallback_chat_id=origin_chat_id,
            fallback_link=source_link
        )
        forward_chat_id = origin_chat_id
        forward_message_id = message_id
        resolved_meta = None
        if bool(task.get('resolve_deep_link')):
            resolver = host.get_deep_link_resolver()
            try:
                resolved = await resolver.resolve(
                    client=host.app.client,
                    message=message,
                    whitelist=host.gc.get_deep_link_bot_whitelist(),
                    timeout_seconds=host.gc.get_deep_link_timeout_seconds(),
                    min_interval_seconds=host.gc.get_deep_link_min_interval_seconds(),
                )
            except DeepLinkResolveError as e:
                task_id = int(task.get('id'))
                item_id = host.transfer_store.add_item(
                    task_id=task_id,
                    source_chat_id=origin_chat_id,
                    source_message_id=message_id,
                    range_message_id=range_message_id,
                    source_link=source_link,
                    target_link=task.get('target_link'),
                    media_type='deep_link',
                    phase='failed',
                    status=TransferStatus.FAILURE,
                    error_message=str(e),
                )
                host.transfer_store.add_event(
                    task_id,
                    f'Deep link resolve failed: {e}',
                    level='error',
                    item_id=item_id,
                )
                log_system = getattr(host, '_log_system_chain', None)
                if callable(log_system):
                    log_system(
                        category='transfer',
                        stage='item_failure',
                        message=str(e),
                        level='error',
                        source_chat_id=origin_chat_id,
                        source_message_id=message_id,
                        target_link=task.get('target_link'),
                        details={
                            'task_id': task_id,
                            'item_id': int(item_id),
                            'source_link': source_link or '',
                        },
                    )
                host.refresh_transfer_task_counts(task_id)
                return False
            if resolved is not None:
                resolved_meta = getattr(resolved, '_deep_link_meta', {}) or {}
                message = resolved
                forward_message_id = getattr(resolved, 'id', message_id)
                resolved_chat = getattr(resolved, 'chat', None)
                resolved_chat_id = getattr(resolved_chat, 'id', None)
                if resolved_chat_id is not None:
                    forward_chat_id = resolved_chat_id
                elif resolved_meta.get('bot'):
                    forward_chat_id = resolved_meta['bot']
        limit_error = host.get_task_target_size_limit_error(task, message)
        if limit_error:
            host.skip_transfer_item_for_target_limit(
                task=task,
                message=channel_message,
                source_link=source_link,
                origin_chat_id=origin_chat_id,
                limit_error=limit_error,
                range_message_id=range_message_id
            )
            return False
        while True:
            try:
                forwarded_message = await host.forward(
                    client=host.app.client,
                    message=message,
                    message_id=forward_message_id,
                    origin_chat_id=forward_chat_id,
                    target_chat_id=target_chat_id,
                    target_link=task.get('target_link'),
                    download_upload=False,
                    done_notice=False,
                    ignore_type_filter=True,
                    archive_after_success=False
                )
                media_meta = host.get_message_media_target_limit_meta(message)
                archive_file_name = host.get_message_media_archive_filename(message)
                task_id = int(task.get('id'))
                item_id = host.transfer_store.add_item(
                    task_id=task_id,
                    source_chat_id=origin_chat_id,
                    source_message_id=message_id,
                    range_message_id=range_message_id,
                    source_link=source_link,
                    target_link=task.get('target_link'),
                    media_type='forward',
                    file_name=(media_meta or {}).get('file_name'),
                    file_size=(media_meta or {}).get('file_size'),
                    source_folder=channel_source_folder,
                    archive_status='pending' if task.get('target_profile') == 'pikpak' and media_meta else None,
                    archive_match_original_name=(
                        archive_file_name is None
                        if task.get('target_profile') == 'pikpak' and media_meta
                        else None
                    ),
                    phase='forwarded',
                    status=TransferStatus.RUNNING
                )
                if resolved_meta:
                    bot = resolved_meta.get('bot') or ''
                    start_param = resolved_meta.get('start_param') or ''
                    host.transfer_store.add_event(
                        task_id,
                        f'resolved_via=@{bot} start={start_param} source={source_link}',
                        item_id=item_id,
                    )
                if host.is_pikpak_target(task.get('target_link'), task.get('target_profile')):
                    if not host.forwarded_message_has_identity(forwarded_message):
                        host.fail_transfer_item(
                            task_id,
                            item_id,
                            f'Direct forward did not produce a target message: {source_link}'
                        )
                        return False
                    confirmed = await host.wait_for_pikpak_ingest_confirmation(
                        target_chat_id=target_chat_id,
                        forwarded_message=forwarded_message
                    )
                    if not confirmed:
                        archive_result = host.archive_pikpak_item(
                            target_profile=task.get('target_profile'),
                            item_id=item_id,
                            task_id=task_id,
                            message=message,
                            source_link=source_link,
                            source_folder=channel_source_folder,
                            transferred_at=datetime.datetime.now(datetime.UTC).timestamp()
                        )
                        if bool(getattr(archive_result, 'ok', False)):
                            host.transfer_store.update_item(
                                item_id,
                                phase='forwarded',
                                status=TransferStatus.SUCCESS,
                                error_message=''
                            )
                            host.transfer_store.add_event(
                                task_id,
                                f'PikPak ingest confirmation recovered by archive: {source_link}',
                                item_id=item_id
                            )
                            host.refresh_transfer_task_counts(task_id)
                            return False
                        error_message = f'PikPak ingest confirmation timeout or failure: {source_link}'
                        host.fail_transfer_item(task_id, item_id, error_message)
                        return False
                    host.complete_forwarded_pikpak_item(
                        task=task,
                        item_id=item_id,
                        task_id=task_id,
                        message=message,
                        source_link=source_link,
                        source_folder=channel_source_folder,
                        transferred_at=datetime.datetime.now(datetime.UTC).timestamp()
                    )
                    return False
                host.transfer_store.update_item(
                    item_id,
                    phase='forwarded',
                    status=TransferStatus.SUCCESS,
                    error_message=''
                )
                host.transfer_store.add_event(
                    task_id,
                    f'Direct forward succeeded: {source_link}',
                    item_id=item_id
                )
                host.refresh_transfer_task_counts(task_id)
                return False
            except (FloodWait, FloodPremiumWait) as e:
                await host.wait_for_telegram_flood(e, task_id=int(task.get('id')), action='web transfer forward')
            except (ChatForwardsRestricted_400, ChatForwardsRestricted_406, MediaCaptionTooLong_400) as e:
                if not host.gc.download_upload:
                    raise
                host.transfer_store.add_event(
                    int(task.get('id')),
                    f'Direct forward fallback for {source_link}: {e}',
                    level='warning'
                )
                if resolved_meta is not None:
                    # Deep-link media lives in bot DM — never re-fetch the channel teaser.
                    await self.create_web_transfer_fallback_download(
                        task=task,
                        source_link=source_link,
                        message=message,
                        range_message_id=range_message_id
                    )
                else:
                    fallback_link = getattr(message, 'link', None) or source_link
                    await self.create_web_transfer_fallback_download(
                        task=task,
                        source_link=fallback_link,
                        message=None if fallback_link else message,
                        range_message_id=range_message_id
                    )
                return True

    async def transfer_web_discussion_replies_to_target(
            self,
            task: dict,
            source_chat_id,
            source_message_id: int,
            target_chat_id,
            expected_total: int,
            range_video_seq: int = 0
    ) -> tuple[int, int]:
        host = self._host
        task_id = int(task.get('id'))
        reply_count = 0
        fallback_count = 0
        try:
            async for comment in iter_discussion_reply_messages(
                    client=host.app.client,
                    chat_id=source_chat_id,
                    message_id=source_message_id,
                    include_message=self._resolve_method('check_type')
            ):
                comment_chat_id = getattr(getattr(comment, 'chat', None), 'id', source_chat_id)
                comment_id = getattr(comment, 'id', None)
                comment_link = getattr(comment, 'link', None)
                if comment_id is not None and host.transfer_store.is_source_message_terminal(
                        task_id,
                        int(comment_id),
                        comment_chat_id
                ):
                    continue
                if comment_id is not None and host.find_resumable_transfer_item(
                        task_id,
                        int(comment_id),
                        comment_chat_id
                ):
                    resumable_item = host.find_resumable_transfer_item(
                        task_id,
                        int(comment_id),
                        comment_chat_id
                    )
                    reply_count += 1
                    range_video_seq += 1
                    host.transfer_store.update_task_range_runtime(
                        task_id,
                        current_range_message_id=source_message_id,
                        current_range_video_captured=range_video_seq,
                        current_range_video_index=range_video_seq
                    )
                    try:
                        await self._resolve_method('wait_between_transfer_messages')()
                        await self.resume_transfer_item_download(
                            task=task,
                            item=resumable_item,
                            range_message_id=source_message_id
                        )
                        fallback_count += 1
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        log.error(
                            f'Web transfer resume comment failed: task={task_id}, comment={comment_id}, reason="{e}"',
                            exc_info=True
                        )
                        host.transfer_store.add_event(
                            task_id,
                            f'Resume comment failed: {comment_id}: {e}',
                            level='error'
                        )
                    continue
                reply_count += 1
                range_video_seq += 1
                host.transfer_store.update_task_range_runtime(
                    task_id,
                    current_range_message_id=source_message_id,
                    current_range_video_captured=range_video_seq,
                    current_range_video_index=range_video_seq
                )
                host.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=expected_total + reply_count,
                    assignment_completed=False
                )
                used_fallback = await self._resolve_method('transfer_message_to_web_target')(
                    task=task,
                    message=comment,
                    origin_chat_id=comment_chat_id,
                    target_chat_id=target_chat_id,
                    source_link=comment_link,
                    range_message_id=source_message_id
                )
                fallback_count += 1 if used_fallback else 0
        except (ValueError, AttributeError, MsgIdInvalid):
            pass
        return reply_count, fallback_count

    async def get_web_transfer_single_message(self, source_link: str):
        host = self._host
        while True:
            try:
                meta = await get_message_by_link(
                    client=host.app.client,
                    link=self.transfer_single_link(source_link),
                    single_link=True
                )
                break
            except (FloodWait, FloodPremiumWait) as e:
                await host.wait_for_telegram_flood(e, action='load single transfer message')
        messages = meta.get('message') if isinstance(meta, dict) else None
        if isinstance(messages, list):
            return messages[0] if messages else None
        return messages

    async def get_web_transfer_range_message(self, chat_id, message_id: int, task_id: int):
        host = self._host
        while True:
            try:
                return await host.app.client.get_messages(
                    chat_id=chat_id,
                    message_ids=message_id
                )
            except (FloodWait, FloodPremiumWait) as e:
                await host.wait_for_telegram_flood(e, task_id=task_id, action='load range transfer message')
            except (
                MsgIdInvalid,
                ChannelInvalid,
                UsernameInvalid,
                ChannelPrivate_400,
                ChannelPrivate_406,
                ValueError,
                AttributeError,
            ) as e:
                log.warning(
                    f'Unable to load transfer message: chat={chat_id}, message={message_id}, reason="{e}"'
                )
                return None
            except Exception as e:
                log.warning(
                    f'Unable to load transfer message: chat={chat_id}, message={message_id}, reason="{e}"',
                    exc_info=True
                )
                return None

    def skip_missing_web_transfer_range_message(
            self,
            task: dict,
            origin_chat_id,
            source_link: str,
            message_id: int
    ) -> None:
        self._host.skip_missing_web_transfer_range_message(
            task, origin_chat_id, source_link, message_id
        )

    @staticmethod
    def transfer_single_link(source_link: str) -> str:
        from module.transfer_engine import TransferEngine
        return TransferEngine.transfer_single_link(source_link)
