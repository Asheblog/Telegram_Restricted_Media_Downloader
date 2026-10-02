# coding=UTF-8
"""Live listen/forward transfer operations.

Deep module behind the TelegramRestrictedMediaDownloader facade: owns forward,
listen_download / listen_forward handlers, on_listen registration, and discussion
reply forwarding. Host remains the composition root for shared deps.
"""
from __future__ import annotations

import asyncio
import datetime
import time
from typing import Callable, Optional, Union

import pyrogram
from pyrogram.errors import (
    FileReferenceEmpty,
    FileReferenceExpired,
    FileReferenceInvalid,
    FilerefUpgradeNeeded,
    FloodWait,
    FloodPremiumWait,
)
from pyrogram.errors.exceptions.bad_request_400 import (
    MsgIdInvalid,
    UsernameInvalid,
    PeerIdInvalid,
    ChatForwardsRestricted as ChatForwardsRestricted_400,
    MediaCaptionTooLong as MediaCaptionTooLong_400,
    MessageIdInvalid,
)
from pyrogram.errors.exceptions.not_acceptable_406 import (
    ChatForwardsRestricted as ChatForwardsRestricted_406,
)
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.handlers import MessageHandler
from pyrogram.types.messages_and_media import ReplyParameters
from pyrogram.types.bots_and_keyboards import InlineKeyboardButton, InlineKeyboardMarkup

from module import console, log, LINK_PREVIEW_OPTIONS
from module.core.enums import (
    KeyWord,
    BotCallbackText,
    BotButton,
    DownloadType,
)
from module.utils.language import _t
from module.transfer.pikpak_rules import message_has_pikpak_ingestible_media
from module.domain.archive_naming.source_folders import (
    archive_source_folder,
    archive_source_folder_for_messages,
    media_group_post_message_id,
    normalize_archive_title_source,
    resolve_forward_archive_source_folder,
)
from module.utils.flag_support import (
    make_forward_watch_rule,
    parse_forward_watch_rule,
)
from module.utils.util import (
    parse_link,
    safe_message,
    iter_discussion_reply_forward_units,
)

# Telegram file references expire (~1h, and can be invalidated at any time):
# a copy/send reusing a stale one fails with FILE_REFERENCE_X_EXPIRED. The
# documented remedy is to re-fetch the message for a fresh reference and retry.
FILE_REFERENCE_REFRESH_RETRIES = 2
# 单次 FloodWait 超过该秒数后, 内存里的 file_reference 大概率已过期, 发送前主动刷新。
FILE_REFERENCE_FLOOD_REFRESH_SECONDS = 1800
FILE_REFERENCE_EXPIRED_ERRORS = (
    FileReferenceExpired,
    FileReferenceInvalid,
    FileReferenceEmpty,
    FilerefUpgradeNeeded,
)
_FILE_REFERENCE_EVENT_KEYS = (
    'trace_id',
    'watch_id',
    'source_chat_id',
    'source_message_id',
    'target_link',
)


class LiveTransferService:
    """Listen/forward transfer behaviour extracted from the downloader facade."""

    def __init__(self, host):
        object.__setattr__(self, '_host', host)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, '_host'), name)

    def _watch_manager(self):
        host = object.__getattribute__(self, '_host')
        manager = getattr(host, 'watch_manager', None)
        if manager is None and hasattr(host, '_require_watch_manager'):
            manager = host._require_watch_manager()
        return manager

    async def _invoke(self, name: str, *args, **kwargs):
        """Prefer host instance monkeypatch; otherwise call local implementation.

        Only used for `forward`: unit tests historically patch `host.forward`.
        Sibling listen helpers call `self.X` directly (production-equivalent).
        """
        host = object.__getattribute__(self, '_host')
        if name in getattr(host, '__dict__', {}):
            method = host.__dict__[name]
            result = method(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
        method = getattr(type(self), name)
        result = method(self, *args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    async def forward_messages_with_flood_retry(
            self,
            target_chat_id: Union[str, int],
            origin_chat_id: Union[str, int],
            message_id: int
    ):
        while True:
            try:
                return await self.app.client.forward_messages(
                    chat_id=target_chat_id,
                    from_chat_id=origin_chat_id,
                    message_ids=message_id,
                    disable_notification=True
                )
            except (FloodWait, FloodPremiumWait) as e:
                await self.wait_for_telegram_flood(e, action='forward message')

    @staticmethod
    def file_reference_refresh_retries() -> int:
        return FILE_REFERENCE_REFRESH_RETRIES

    @staticmethod
    def _copy_source_client(message, client):
        """消息自带的 client 才是执行 Message.copy 的账号, 刷新引用必须用同一个账号。"""
        return getattr(message, '_client', None) or client

    @staticmethod
    def _flood_expires_file_reference(error) -> bool:
        """长 FloodWait 之后内存里的 file_reference 大概率已过期。"""
        try:
            seconds = int(getattr(error, 'value', 0) or 0)
        except (TypeError, ValueError):
            return False
        return seconds >= FILE_REFERENCE_FLOOD_REFRESH_SECONDS

    async def fetch_message_with_fresh_file_reference(
            self,
            *,
            client,
            chat_id,
            message_id,
            action: str = 'refresh message',
    ):
        """用执行复制的同一个 client 重新拉取消息, 取新的 file_reference；失败返回 None。

        Telegram 的 file_reference 会过期（约 1 小时，也可能被服务端随时作废），
        messages.SendMedia 因此返回 FILE_REFERENCE_X_EXPIRED；官方要求在源上下文中
        重新获取消息来刷新引用。FloodWait 属于"等一会就能取到"，等待后重试而不放弃。
        """
        if client is None or chat_id is None or message_id is None:
            return None
        if not callable(getattr(client, 'get_messages', None)):
            return None
        while True:
            try:
                refreshed = await client.get_messages(
                    chat_id=chat_id,
                    message_ids=message_id,
                )
                break
            except (FloodWait, FloodPremiumWait) as e:
                # 主客户端(自定义 session)通常会在会话内部消化 FloodWait; 这里兜底,
                # 其它 client 若把 FloodWait 抛出来, 等待后重试而不是当成"取不到消息"。
                await self.wait_for_telegram_flood(e, action=action)
            except Exception as e:
                log.warning(f'刷新消息文件引用失败,{_t(KeyWord.REASON)}:"{e}"')
                return None
        if refreshed is None or getattr(refreshed, 'empty', False):
            return None
        return refreshed

    @staticmethod
    def _file_reference_event_context(event_context: Optional[dict]) -> dict:
        """白名单取上下文: event_context 混入 category/stage 会与固定 kwargs 冲突。"""
        return {
            key: value
            for key, value in (event_context or {}).items()
            if key in _FILE_REFERENCE_EVENT_KEYS
        }

    def _log_file_reference_refresh(
            self,
            *,
            error,
            outcome: str,
            action: str,
            refresh_attempt: int,
            refreshed: Optional[bool] = None,
            event_context: Optional[dict] = None,
    ) -> None:
        prompt = (
            f'转发文件引用已过期({action}),{outcome}'
            f'({refresh_attempt}/{self.file_reference_refresh_retries()}),'
            f'{_t(KeyWord.REASON)}:"{error}"'
        )
        log.warning(prompt)
        context = self._file_reference_event_context(event_context)
        if not context:
            return
        details = {
            'action': action,
            'refresh_attempt': refresh_attempt,
            'error': str(error),
        }
        if refreshed is not None:
            details['refreshed'] = bool(refreshed)
        self._log_system_chain(
            category='forward',
            stage='file_reference_refreshed',
            message=f'文件引用已过期,{outcome}({action})',
            level='warning',
            details=details,
            **context,
        )

    def _log_file_reference_preemptive_refresh(
            self,
            *,
            error,
            action: str,
            event_context: Optional[dict] = None,
    ) -> None:
        """长限流等待后主动刷新引用: 与"发送被拒后再刷新"区分, 便于线上复盘。"""
        flood_seconds = getattr(error, 'value', 0)
        prompt = (
            f'等待 Telegram 限流{flood_seconds}秒后主动刷新源消息文件引用({action}),'
            f'避免复用已过期的 file_reference。'
        )
        log.warning(prompt)
        context = self._file_reference_event_context(event_context)
        if not context:
            return
        self._log_system_chain(
            category='forward',
            stage='file_reference_refreshed',
            message=f'长限流等待后主动刷新源消息引用({action})',
            level='warning',
            details={
                'action': action,
                'preemptive': True,
                'flood_seconds': flood_seconds,
                'error': str(error),
            },
            **context,
        )

    async def copy_source_message(
            self,
            *,
            client,
            message: pyrogram.types.Message,
            origin_chat_id: Union[str, int],
            message_id: int,
            target_chat_id: Union[str, int],
            prefer_held_message: bool = True,
            action: str = 'copy message',
            event_context: Optional[dict] = None,
    ):
        """复制源消息到目标频道，遇到 file_reference 过期时刷新引用后重试。

        长时间运行的监听转发（FloodWait 等待、深链解析、延迟抓取评论区）会在消息
        解析很久之后才真正发送，此时内存里的 file_reference 可能已过期，直接复制
        会以 FILE_REFERENCE_X_EXPIRED 失败。这里在失败时用同一个账号重新获取源消息
        （取不到时退回 client.copy_message 按 id 重新拉取）后重试；刷新与重试都
        无望时保留原始错误让上层可见，绝不静默丢帖。
        """
        # 复制与刷新必须同账号: A 账号刷出来的引用给 B 账号发送仍然会失败,
        # 刷新成功后也不能把发送账号静默切到 refreshed 消息自己的 client。
        copy_client = (
            self._copy_source_client(message, client)
            if prefer_held_message else client
        )
        held_message = message if prefer_held_message else None
        attempts_left = self.file_reference_refresh_retries()
        last_file_reference_error = None
        while True:
            try:
                if held_message is not None:
                    result = await held_message.copy(
                        chat_id=target_chat_id,
                        disable_notification=True,
                        protect_content=False,
                    )
                else:
                    result = await client.copy_message(
                        chat_id=target_chat_id,
                        from_chat_id=origin_chat_id,
                        message_id=message_id,
                        disable_notification=True,
                        protect_content=False,
                    )
            except (FloodWait, FloodPremiumWait) as e:
                await self.wait_for_telegram_flood(e, action=action)
                if held_message is not None and self._flood_expires_file_reference(e):
                    # 在引用 TTL 量级里等过限流, 内存引用基本已作废: 主动刷新,
                    # 免得下一次发送必然失败并白白吃掉一次刷新预算。
                    refreshed = await self.fetch_message_with_fresh_file_reference(
                        client=copy_client,
                        chat_id=origin_chat_id,
                        message_id=message_id,
                        action=action,
                    )
                    if refreshed is not None:
                        held_message = refreshed
                        self._log_file_reference_preemptive_refresh(
                            error=e,
                            action=action,
                            event_context=event_context,
                        )
                continue
            except FILE_REFERENCE_EXPIRED_ERRORS as e:
                last_file_reference_error = e
                if attempts_left <= 0:
                    raise
                attempts_left -= 1
                refresh_attempt = self.file_reference_refresh_retries() - attempts_left
                refreshed = await self.fetch_message_with_fresh_file_reference(
                    client=copy_client,
                    chat_id=origin_chat_id,
                    message_id=message_id,
                    action=action,
                )
                if refreshed is None and held_message is None:
                    # 已经走的是"按 id 重新拉取"这条路, 取不到就没有刷新手段了。
                    raise
                # None 表示源消息取不到, 下一轮退回 client.copy_message 按 id 重新拉取。
                held_message = refreshed
                self._log_file_reference_refresh(
                    error=e,
                    outcome=(
                        '已重新获取源消息并重试' if refreshed is not None
                        else '未能重新获取源消息, 按 id 重新拉取再试'
                    ),
                    refreshed=refreshed is not None,
                    action=action,
                    refresh_attempt=refresh_attempt,
                    event_context=event_context,
                )
                continue
            if (
                    last_file_reference_error is not None
                    and not self.forwarded_message_has_identity(result)
            ):
                # 按 id 重新拉取也没产出消息(MessageEmpty): 保留原始 file_reference 错误,
                # 否则会退化成只写一条 log.error 的静默丢帖。
                raise last_file_reference_error
            return result

    async def copy_media_group_with_file_reference_refresh(
            self,
            *,
            chat_id: Union[str, int],
            from_chat_id: Union[str, int],
            message_id: int,
            action: str = 'copy media group',
            event_context: Optional[dict] = None,
    ):
        """复制媒体组；copy_media_group 每次都重新拉取成员，重试即可刷新 file_reference。"""
        attempts_left = self.file_reference_refresh_retries()
        while True:
            try:
                return await self.app.client.copy_media_group(
                    chat_id=chat_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                    disable_notification=True
                )
            except (FloodWait, FloodPremiumWait) as e:
                await self.wait_for_telegram_flood(e, action=action)
            except FILE_REFERENCE_EXPIRED_ERRORS as e:
                if attempts_left <= 0:
                    raise
                attempts_left -= 1
                refresh_attempt = self.file_reference_refresh_retries() - attempts_left
                self._log_file_reference_refresh(
                    error=e,
                    outcome='已重新拉取媒体组成员并重试',
                    action=action,
                    refresh_attempt=refresh_attempt,
                    event_context=event_context,
                )

    async def _run_pikpak_archive_after_forward(
            self,
            message: pyrogram.types.Message,
            origin_chat_id: Union[str, int],
            message_id: int,
            media_group: Optional[list] = None,
            transferred_at: Optional[float] = None,
            source_folder: Optional[str] = None,
            source_link: Optional[str] = None,
            archive_by_author: bool = False,
            archive_title_source: str = 'auto',
    ) -> None:
        title_source = normalize_archive_title_source(archive_title_source)
        transferred_at = transferred_at or datetime.datetime.now(datetime.UTC).timestamp()
        messages = [message]
        if media_group:
            try:
                group_messages = await message.get_media_group()
                if group_messages:
                    self.inherit_media_group_title(group_messages, propagate_to=message)
                    messages = list(group_messages)
            except Exception as e:
                log.debug(f'Unable to resolve media group for PikPak archive: {e}')
        shared_source_link = (
            source_link
            or getattr(message, 'link', None)
        )
        shared_post_id = media_group_post_message_id(messages) or message_id
        archive_folder = resolve_forward_archive_source_folder(
            source_folder=source_folder,
            messages=messages,
            post_message_id=shared_post_id,
            fallback_chat_id=origin_chat_id,
            fallback_link=shared_source_link,
            archive_by_author=archive_by_author,
            archive_title_source=title_source,
        )
        for group_message in messages:
            group_source_link = (
                shared_source_link
                or getattr(group_message, 'link', None)
                or getattr(message, 'link', None)
            )

            def _archive_one(
                    group_message=group_message,
                    group_source_link=group_source_link,
                    archive_folder=archive_folder,
                    transferred_at=transferred_at,
                    origin_chat_id=origin_chat_id,
                    message_id=message_id,
                    archive_by_author=archive_by_author,
                    archive_title_source=title_source,
            ):
                archive_result = self.archive_pikpak_item(
                    target_profile='pikpak',
                    item_id=None,
                    task_id=None,
                    message=group_message,
                    source_link=group_source_link,
                    source_folder=archive_folder,
                    transferred_at=transferred_at,
                    archive_by_author=archive_by_author,
                    archive_title_source=title_source,
                )
                if (
                        archive_result is not None
                        and getattr(archive_result, 'status', None) != 'disabled'
                        and not bool(getattr(archive_result, 'ok', False))
                ):
                    archive_status = getattr(archive_result, 'status', 'error')
                    archive_message = getattr(archive_result, 'message', '')
                    log.warning(
                        f'PikPak archive {archive_status}: '
                        f'{archive_message or group_source_link or getattr(group_message, "id", None) or message_id}'
                    )
                if archive_result is not None:
                    archive_status = getattr(archive_result, 'status', 'unknown')
                    archive_ok = bool(getattr(archive_result, 'ok', False))
                    title_file_name = self.get_message_media_archive_filename(
                        group_message,
                        post_message_id=shared_post_id,
                    )
                    media_meta = self.get_message_media_target_limit_meta(
                        group_message,
                        post_message_id=shared_post_id,
                    )
                    archive_file_name = title_file_name or (media_meta or {}).get('file_name')
                    self._log_system_chain(
                        category='archive',
                        stage='archive_success' if archive_ok else f'archive_{archive_status}',
                        message=(
                            f'rclone 归档成功: {getattr(archive_result, "archive_path", "") or group_source_link}'
                            if archive_ok else
                            f'rclone 归档失败({archive_status}): {getattr(archive_result, "message", "")}'
                        ),
                        level='info' if archive_ok else 'warning',
                        source_chat_id=origin_chat_id,
                        source_message_id=getattr(group_message, 'id', message_id),
                        target_link=group_source_link,
                        details={
                            'archive_path': getattr(archive_result, 'archive_path', None),
                            'source_folder': archive_folder,
                            'file_name': archive_file_name,
                            'match_original_name': not bool(
                                title_file_name and archive_file_name == title_file_name
                            ),
                        }
                    )

            # Fire-and-forget: listen/forward must not wait on rclone poll.
            asyncio.create_task(asyncio.to_thread(_archive_one))

    async def forward(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message,
            message_id: int,
            origin_chat_id: Union[str, int],
            target_chat_id: Union[str, int],
            target_link: str,
            download_upload: Optional[bool] = False,
            media_group: Optional[list] = None,
            done_notice: Optional[bool] = True,
            ignore_type_filter: Optional[bool] = False,
            archive_after_success: Optional[bool] = True,
            watch_id: Optional[str] = None,
            trace_id: Optional[str] = None,
            source_folder: Optional[str] = None,
            archive_source_link: Optional[str] = None,
            media_types_override=None,
            archive_by_author: bool = False,
            archive_title_source: str = 'auto',
    ):
        title_source = normalize_archive_title_source(archive_title_source)
        try:
            if trace_id is None:
                trace_id, _, _ = self._message_chain_context(message, watch_id)
            if media_group:
                try:
                    group_messages = await message.get_media_group()
                    if group_messages:
                        self.inherit_media_group_title(group_messages, propagate_to=message)
                except Exception as e:
                    log.debug(f'Unable to inherit media group title before archive path: {e}')
            if source_folder:
                channel_source_folder = source_folder
            else:
                group_messages = None
                if media_group or getattr(message, 'media_group_id', None):
                    try:
                        group_messages = await message.get_media_group()
                    except Exception:
                        group_messages = None
                if group_messages:
                    self.inherit_media_group_title(group_messages, propagate_to=message)
                    channel_source_folder = archive_source_folder_for_messages(
                        group_messages,
                        fallback_chat_id=origin_chat_id,
                        fallback_link=archive_source_link or getattr(message, 'link', None),
                        archive_by_author=archive_by_author,
                        archive_title_source=title_source,
                    )
                else:
                    channel_source_folder = archive_source_folder(
                        message,
                        fallback_chat_id=origin_chat_id,
                        fallback_link=archive_source_link or getattr(message, 'link', None),
                        archive_by_author=archive_by_author,
                        archive_title_source=title_source,
                    )
            channel_source_link = archive_source_link or getattr(message, 'link', None)
            if not ignore_type_filter:
                te = getattr(self, 'transfer_engine', None)
                if te is not None and hasattr(te, 'runtime_message_filter'):
                    runtime_filter = te.runtime_message_filter(media_types_override)
                elif media_types_override is not None:
                    from module.core.message_filter_factory import build_runtime_message_filter
                    runtime_filter = build_runtime_message_filter(
                        getattr(getattr(self, 'gc', None), 'message_filter', None),
                        media_types_override,
                    )
                else:
                    runtime_filter = self.message_filter
                if not runtime_filter.should_pass(message):
                    reject_reason = runtime_filter.get_reject_reason(message) or '消息过滤器拒绝'
                    self._log_system_chain(
                        category='filter',
                        stage='filter_reject',
                        message=f'消息被过滤器拦截: {reject_reason}',
                        level='info',
                        trace_id=trace_id,
                        watch_id=watch_id,
                        source_chat_id=origin_chat_id,
                        source_message_id=message_id,
                        target_link=target_link,
                        details={'reject_reason': reject_reason}
                    )
                    console.log(
                        f'{_t(KeyWord.CHANNEL)}:"{origin_chat_id}",{_t(KeyWord.MESSAGE_ID)}:"{message_id}"'
                        f' -> '
                        f'{_t(KeyWord.CHANNEL)}:"{target_chat_id}",'
                        f'{_t(KeyWord.STATUS)}:{_t(KeyWord.FORWARD_SKIP)}。'
                    )
                    if watch_id:
                        self._record_watch_event(
                            watch_id,
                            origin_chat_id,
                            message_id,
                            target_chat_id,
                            target_link,
                            'skipped',
                            f'跳过转发(已被消息过滤器过滤: {reject_reason})。',
                        )
                    if done_notice:
                        await asyncio.create_task(
                            self.done_notice(
                                f'"{origin_chat_id}",{_t(KeyWord.MESSAGE_ID)}:{message_id}'
                                f' ➡️ '
                                f'"{target_chat_id}",{_t(KeyWord.FORWARD_SKIP)}(已被消息过滤器过滤)。'
                            )
                        )
                    return None
            if (
                    self.is_pikpak_target(target_link)
                    and not media_group
                    and not message_has_pikpak_ingestible_media(message)
            ):
                reject_reason = 'PikPak 不支持无媒体消息'
                self._log_system_chain(
                    category='filter',
                    stage='filter_reject',
                    message=f'消息被过滤器拦截: {reject_reason}',
                    level='info',
                    trace_id=trace_id,
                    watch_id=watch_id,
                    source_chat_id=origin_chat_id,
                    source_message_id=message_id,
                    target_link=target_link,
                    details={'reject_reason': reject_reason}
                )
                if watch_id:
                    self._record_watch_event(
                        watch_id,
                        origin_chat_id,
                        message_id,
                        target_chat_id,
                        target_link,
                        'skipped',
                        f'跳过转发({reject_reason})。',
                    )
                return None
            forwarded_message = None
            if media_group:
                forwarded_message = await self.copy_media_group_with_file_reference_refresh(
                    chat_id=target_chat_id,
                    from_chat_id=origin_chat_id,
                    message_id=message_id,
                    event_context={
                        'trace_id': trace_id,
                        'watch_id': watch_id,
                        'source_chat_id': origin_chat_id,
                        'source_message_id': message_id,
                        'target_link': target_link,
                    },
                )
            elif getattr(message, 'text', False):
                while True:
                    try:
                        forwarded_message = await self.app.client.send_message(
                            chat_id=target_chat_id,
                            text=message.text,
                            disable_notification=True,
                            protect_content=False
                        )
                        break
                    except (FloodWait, FloodPremiumWait) as e:
                        await self.wait_for_telegram_flood(e, action='send text')
                    except Exception as e:
                        log.error(f'无法转发"{message.text}"消息,{_t(KeyWord.REASON)}:"{e}"')
            else:
                # Prefer in-memory Message.copy for deep-link bot media: client.copy_message
                # re-fetches by id and often gets MessageEmpty after the bot expires the pack.
                can_copy_held = (
                    message is not None
                    and not bool(getattr(message, 'empty', False))
                    and any(
                        getattr(message, attr, None)
                        for attr in (
                            'video', 'photo', 'document', 'audio', 'voice',
                            'animation', 'video_note', 'sticker',
                        )
                    )
                    and callable(getattr(message, 'copy', None))
                )
                if can_copy_held:
                    forwarded_message = await self.copy_source_message(
                        client=self.app.client,
                        message=message,
                        origin_chat_id=origin_chat_id,
                        message_id=message_id,
                        target_chat_id=target_chat_id,
                        prefer_held_message=True,
                        action='copy held message',
                        event_context={
                            'trace_id': trace_id,
                            'watch_id': watch_id,
                            'source_chat_id': origin_chat_id,
                            'source_message_id': message_id,
                            'target_link': target_link,
                        },
                    )
                if not self.forwarded_message_has_identity(forwarded_message):
                    forwarded_message = await self.copy_source_message(
                        client=self.app.client,
                        message=message,
                        origin_chat_id=origin_chat_id,
                        message_id=message_id,
                        target_chat_id=target_chat_id,
                        prefer_held_message=False,
                        action='copy message',
                        event_context={
                            'trace_id': trace_id,
                            'watch_id': watch_id,
                            'source_chat_id': origin_chat_id,
                            'source_message_id': message_id,
                            'target_link': target_link,
                        },
                    )
                if not self.forwarded_message_has_identity(forwarded_message):
                    try:
                        forwarded_message = await self.forward_messages_with_flood_retry(
                            target_chat_id=target_chat_id,
                            origin_chat_id=origin_chat_id,
                            message_id=message_id
                        )
                    except MessageIdInvalid as e:
                        log.error(
                            f'Unable to forward invalid source message: '
                            f'{getattr(message, "link", None) or message_id},{_t(KeyWord.REASON)}:"{e}"'
                        )
            if not self.forwarded_message_has_identity(forwarded_message):
                log.error(
                    f'Direct forward did not produce a target message: {getattr(message, "link", None) or message_id}'
                )
                return None
            p_message_id = ','.join(map(str, media_group)) if media_group else message_id
            console.log(
                f'{_t(KeyWord.CHANNEL)}:"{origin_chat_id}",{_t(KeyWord.MESSAGE_ID)}:"{p_message_id}"'
                f' -> '
                f'{_t(KeyWord.CHANNEL)}:"{target_chat_id}",'
                f'{_t(KeyWord.STATUS)}:{_t(KeyWord.FORWARD_SUCCESS)}。'
            )
            if done_notice:
                await asyncio.create_task(
                    self.done_notice(
                        f'"{origin_chat_id}",{_t(KeyWord.MESSAGE_ID)}:{p_message_id}'
                        f' ➡️ '
                        f'"{target_chat_id}",{_t(KeyWord.FORWARD_SUCCESS)}。'
                    )
                )
            if watch_id:
                self._record_watch_event(
                    watch_id,
                    origin_chat_id,
                    message_id,
                    target_chat_id,
                    target_link,
                    'success',
                    self._forward_success_event_message(message, media_group),
                )
            self._log_system_chain(
                category='forward',
                stage='forward_success',
                message='直接转发成功',
                trace_id=trace_id,
                watch_id=watch_id,
                source_chat_id=origin_chat_id,
                source_message_id=message_id,
                target_link=target_link,
                details={
                    'target_chat_id': str(target_chat_id),
                    'media_group': bool(media_group)
                }
            )
            if archive_after_success and target_link and 'pikpak' in str(target_link).lower():
                await self._run_pikpak_archive_after_forward(
                    message=message,
                    origin_chat_id=origin_chat_id,
                    message_id=message_id,
                    media_group=media_group,
                    source_folder=channel_source_folder,
                    source_link=channel_source_link,
                    archive_by_author=archive_by_author,
                    archive_title_source=title_source,
                )
            return forwarded_message
        except (ChatForwardsRestricted_400, ChatForwardsRestricted_406, MediaCaptionTooLong_400) as e:
            if not download_upload:
                if isinstance(e, MediaCaptionTooLong_400):
                    raise
                if (
                        getattr(getattr(message, 'chat', None), 'is_creator', False) or
                        getattr(getattr(message, 'chat', None), 'is_admin', False)
                ) and (
                        getattr(getattr(message, 'from_user', None), 'id', -1) ==
                        getattr(getattr(client, 'me', None), 'id', None)
                ):
                    return None
                raise
            link = channel_source_link or getattr(message, 'link', None)
            if not self.gc.download_upload:
                self._log_system_chain(
                    category='forward',
                    stage='forward_restricted',
                    message='转发受限且未启用下载后上传，已跳过',
                    level='warning',
                    trace_id=trace_id,
                    watch_id=watch_id,
                    source_chat_id=origin_chat_id,
                    source_message_id=message_id,
                    target_link=target_link,
                    details={'source_link': link, 'error': str(e)}
                )
                await self.bot.bot.send_message(
                    chat_id=client.me.id,
                    text=f'⚠️⚠️⚠️无法转发⚠️⚠️⚠️\n'
                         f'`{link}`\n'
                         f'存在内容保护限制(可在[设置]->[上传设置]中设置转发时遇到受限转发进行下载后上传)。',
                    reply_parameters=ReplyParameters(message_id=message_id),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        BotButton.SETTING,
                        callback_data=BotCallbackText.SETTING
                    )]]))
                return None
            upload_meta = self.build_download_upload_meta(
                target_link=target_link,
                source_link=link,
                source_folder=channel_source_folder,
                archive_by_author=archive_by_author,
                archive_title_source=title_source,
            )
            transfer_store = getattr(self, "transfer_store", None)
            if transfer_store and link and target_link:
                from module.transfer.watch_inline import ensure_download_fallback_transfer_task
                fallback_task_id = ensure_download_fallback_transfer_task(
                    store=transfer_store,
                    source_link=link,
                    target_link=target_link,
                    target_profile=upload_meta.get('target_profile') or 'pikpak',
                    watch_id=watch_id,
                    archive_by_author=archive_by_author,
                    archive_title_source=title_source,
                )
                if fallback_task_id:
                    upload_meta['task_id'] = fallback_task_id
            self._log_system_chain(
                category='transfer',
                stage='download_fallback_start',
                message='转发受限，回退为下载后上传',
                trace_id=trace_id,
                watch_id=watch_id,
                source_chat_id=origin_chat_id,
                source_message_id=message_id,
                target_link=target_link,
                details={
                    'source_link': link,
                    'task_id': upload_meta.get('task_id'),
                    'error': str(e)
                }
            )
            upload_meta['bot_progress'] = await self.create_bot_transfer_progress(
                source_link=link,
                target_link=target_link,
                source_message_id=message_id
            )
            if isinstance(message, pyrogram.types.Message):
                await self.create_download_task(
                    message_ids=message,
                    retry=None,
                    single_link=True,
                    with_upload=upload_meta,
                    diy_download_type=[_ for _ in DownloadType()]
                )
            elif link and self.last_client and self.last_message:
                self.last_message.text = f'/download {link}?single'
                await self.get_download_link_from_bot(
                    client=self.last_client,
                    message=self.last_message,
                    with_upload=upload_meta
                )
            elif link:
                await self.create_download_task(
                    message_ids=link,
                    retry=None,
                    single_link=True,
                    with_upload=upload_meta,
                    diy_download_type=[_ for _ in DownloadType()]
                )
            p = f'{_t(KeyWord.DOWNLOAD_AND_UPLOAD_TASK)}{_t(KeyWord.CHANNEL)}:"{target_chat_id}",{_t(KeyWord.LINK)}:"{link}"。'
            console.log(p, style='#FF4689')
            log.info(p)

    async def cancel_listen(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message,
            link: str,
            command: str
    ):
        if command == '/listen_forward':
            self.cd.data = {
                'link': link
            }
        rule = parse_forward_watch_rule(link)
        args: list = [part for part in (rule.get('source_link'), rule.get('target_link')) if part]
        forward_emoji = ' ➡️ '
        include_text = ' 👥' if rule.get('include_comment') else ''
        await client.send_message(
            chat_id=message.from_user.id,
            reply_parameters=ReplyParameters(message_id=message.id),
            text=f'`{link if len(args) == 1 else forward_emoji.join(args) + include_text}`\n🚛已经在监听列表中。',
            link_preview_options=LINK_PREVIEW_OPTIONS,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        BotButton.DROP,
                        callback_data=f'{BotCallbackText.REMOVE_LISTEN_DOWNLOAD} {link}' if command == '/listen_download' else BotCallbackText.REMOVE_LISTEN_FORWARD
                    )
                ]
            ]
            )
        )

    async def on_listen(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message
    ):
        meta: Union[dict, None] = await self.bot.on_listen(client, message)
        if meta is None:
            return None

        async def add_listen_chat(_link: str, _listen_chat: dict, _callback: Callable) -> bool:
            if _link not in _listen_chat:
                try:
                    chat = await self.user.get_chat(_link)
                    if chat.is_forum:
                        raise PeerIdInvalid
                    handler = MessageHandler(_callback, filters=pyrogram.filters.chat(chat.id))
                    _listen_chat[_link] = handler
                    self.user.add_handler(handler)
                    return True
                except PeerIdInvalid:
                    try:
                        link_meta: list = _link.split()
                        link_length: int = len(link_meta)
                        if link_length >= 1:  # v1.6.7 修复内部函数add_listen_chat中,抛出PeerIdInvalid后,在获取链接时抛出ValueError错误。
                            l_link = link_meta[0]
                        else:
                            return False
                        m: dict = await parse_link(client=self.app.client, link=l_link)
                        topic_id = m.get('topic_id')
                        chat_id = m.get('chat_id')
                        if topic_id:
                            filters = pyrogram.filters.chat(
                                chat_id) & pyrogram.filters.topic(topic_id)
                        else:
                            filters = pyrogram.filters.chat(chat_id)
                        handler = MessageHandler(
                            _callback,
                            filters=filters
                        )
                        _listen_chat[_link] = handler
                        self.user.add_handler(handler)
                        return True
                    except ValueError as e:
                        await client.send_message(
                            chat_id=message.from_user.id,
                            reply_parameters=ReplyParameters(message_id=message.id),
                            link_preview_options=LINK_PREVIEW_OPTIONS,
                            text=f'⚠️⚠️⚠️无法读取⚠️⚠️⚠️\n`{_link}`\n(具体原因请前往终端查看报错信息)'
                        )
                        log.error(f'频道"{_link}"解析失败,{_t(KeyWord.REASON)}:"{e}"')
                        return False
                except Exception as e:
                    await client.send_message(
                        chat_id=message.from_user.id,
                        reply_parameters=ReplyParameters(message_id=message.id),
                        link_preview_options=LINK_PREVIEW_OPTIONS,
                        text=f'⚠️⚠️⚠️无法读取⚠️⚠️⚠️\n`{_link}`\n(具体原因请前往终端查看报错信息)'
                    )
                    log.error(f'读取频道"{_link}"时遇到错误,{_t(KeyWord.REASON)}:"{e}"')
                    return False
            else:
                await self.cancel_listen(client, message, _link, command)
                return False

        links: list = meta.get('links')
        command: str = meta.get('command')
        include_comment: bool = bool(meta.get('include_comment'))
        if command == '/listen_download':
            last_message: Union[pyrogram.types.Message, None] = None
            for link in links:
                if await add_listen_chat(link, self.listen_download_chat, self.listen_download):
                    if not last_message:
                        last_message: Union[pyrogram.types.Message, str, None] = await client.send_message(
                            chat_id=message.from_user.id,
                            reply_parameters=ReplyParameters(message_id=message.id),
                            link_preview_options=LINK_PREVIEW_OPTIONS,
                            text=f'✅新增`监听下载频道`频道:\n')
                    last_message: Union[pyrogram.types.Message, None] = await self.safe_edit_message(
                        client=client,
                        message=message,
                        last_message_id=last_message.id,
                        text=safe_message(f'{last_message.text}\n{link}'),
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(
                                BotButton.LOOKUP_LISTEN_INFO,
                                callback_data=BotCallbackText.LOOKUP_LISTEN_INFO
                            )
                        ]])
                    )
                    p = f'已新增监听下载,频道链接:"{link}"。'
                    console.log(p, style='#FF4689')
                    log.info(f'{p}当前的监听下载信息:{self.listen_download_chat}')
        elif command == '/listen_forward':
            listen_link, target_link = links
            rule = make_forward_watch_rule(listen_link, target_link, include_comment)
            if await add_listen_chat(rule, self.listen_forward_chat, self.listen_forward):
                comment_status = '\n👥包含评论区:开' if include_comment else ''
                await client.send_message(
                    chat_id=message.from_user.id,
                    reply_parameters=ReplyParameters(message_id=message.id),
                    link_preview_options=LINK_PREVIEW_OPTIONS,
                    text=f'✅新增`监听转发`频道:\n{listen_link} ➡️ {target_link}{comment_status}',
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    BotButton.LOOKUP_LISTEN_INFO,
                                    callback_data=BotCallbackText.LOOKUP_LISTEN_INFO
                                )
                            ]
                        ]
                    )
                )
                p = f'已新增监听转发,转发规则:"{listen_link} -> {target_link}",包含评论区:{include_comment}。'
                console.log(p, style='#FF4689')
                log.info(f'{p}当前的监听转发信息:{self.listen_forward_chat}')

    async def listen_download(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message
    ):
        try:
            origin_chat_id = str(getattr(getattr(message, 'chat', None), 'id', ''))
            watch_manager = self._watch_manager()
            watch_id = (
                watch_manager._download_chat_watch_id.get(origin_chat_id)
                if watch_manager is not None
                else None
            )
            trace_id, _, message_id = self._message_chain_context(message, watch_id)
            self._log_system_chain(
                category='watch',
                stage='message_received',
                message='监听下载收到新消息',
                trace_id=trace_id,
                watch_id=watch_id,
                source_chat_id=origin_chat_id,
                source_message_id=message_id,
                details={'source_link': getattr(message, 'link', None)}
            )
            media_types_override = self._watch_media_types_override(watch_id)
            runtime_filter = self.runtime_message_filter(media_types_override)
            if not runtime_filter.should_pass(message):
                reject_reason = runtime_filter.get_reject_reason(message) or '消息过滤器拒绝'
                msg_id = getattr(message, 'id', '?')
                log.info(f'监听下载:消息已被过滤器过滤,跳过。message_id={msg_id}')
                self._log_system_chain(
                    category='filter',
                    stage='filter_reject',
                    message=f'监听下载被过滤器拦截: {reject_reason}',
                    trace_id=trace_id,
                    watch_id=watch_id,
                    source_chat_id=origin_chat_id,
                    source_message_id=message_id,
                    details={'reject_reason': reject_reason}
                )
                if watch_id:
                    self._record_watch_event(
                        watch_id, origin_chat_id,
                        getattr(message, 'id', 0), '', '',
                        'skipped', f'消息被过滤器过滤,跳过下载。原因: {reject_reason}'
                    )
                return
            self._log_system_chain(
                category='transfer',
                stage='download_start',
                message='监听下载触发下载任务',
                trace_id=trace_id,
                watch_id=watch_id,
                source_chat_id=origin_chat_id,
                source_message_id=message_id,
                details={'source_link': getattr(message, 'link', None)}
            )
            await self.create_download_task(message_ids=message.link, single_link=True)
            # Archive Title Source / Archive By Author are persisted on download
            # watches for parity with forward watches, but this local-download path
            # does not nest under Source Post Archive Path (same as archive_by_author).
            # watch_inline fallback and transfer tasks read the field when archiving.
        except Exception as e:
            log.exception(f'监听下载出现错误,{_t(KeyWord.REASON)}:"{e}"')
            self._log_system_chain(
                category='watch',
                stage='error',
                message=f'监听下载异常: {e}',
                level='error',
                source_chat_id=str(getattr(getattr(message, 'chat', None), 'id', '')),
                source_message_id=getattr(message, 'id', None)
            )

    async def forward_discussion_replies(
            self,
            client: pyrogram.Client,
            source_chat_id: Union[str, int],
            source_message_id: int,
            target_chat_id: Union[str, int],
            target_link: str,
            done_notice: Optional[bool] = True,
            watch_id: Optional[str] = None,
            resolve_deep_link: bool = False,
            archive_by_author: bool = False,
            archive_title_source: str = 'auto',
    ) -> int:
        title_source = normalize_archive_title_source(archive_title_source)
        from module.transfer.deep_link import (
            DeepLinkResolveError,
            message_has_whitelisted_deep_link,
            normalize_resolved_messages,
        )
        count = 0
        whitelist = self.gc.get_deep_link_bot_whitelist() if resolve_deep_link else []

        media_types_override = self._watch_media_types_override(watch_id)

        def include_discussion_message(item) -> bool:
            # Deep-link mode: discussion replies are deep-link-only (no bare text/media dump).
            if resolve_deep_link:
                return message_has_whitelisted_deep_link(item, whitelist)
            try:
                return self.check_type(item, media_types_override=media_types_override)
            except TypeError:
                return self.check_type(item)

        parent_message = None
        try:
            parent_message = await self.app.client.get_messages(
                chat_id=source_chat_id,
                message_ids=source_message_id,
            )
            if getattr(parent_message, 'empty', False):
                parent_message = None
        except Exception:
            parent_message = None
        post_archive_folder = archive_source_folder(
            post_message=parent_message,
            fallback_chat_id=source_chat_id,
            post_message_id=source_message_id,
            archive_by_author=archive_by_author,
            archive_title_source=title_source,
        )

        fetch_started = time.time()
        matched_deep_link_comments = 0
        fetch_error = None
        try:
            async for comment, media_group in iter_discussion_reply_forward_units(
                    client=self.app.client,
                    chat_id=source_chat_id,
                    message_id=source_message_id,
                    include_message=include_discussion_message
            ):
                matched_deep_link_comments += 1
                messages_to_forward = [(comment, media_group)]
                if resolve_deep_link:
                    resolver = self.get_deep_link_resolver()
                    comment_id = getattr(comment, 'id', None)
                    try:
                        resolved_list = normalize_resolved_messages(
                            await resolver.resolve(
                                client=self.app.client,
                                message=comment,
                                whitelist=whitelist,
                                timeout_seconds=self.gc.get_deep_link_timeout_seconds(),
                                min_interval_seconds=self.gc.get_deep_link_min_interval_seconds(),
                                settle_seconds=self.gc.get_deep_link_settle_seconds(),
                                max_pages=self.gc.get_deep_link_max_pages(),
                                page_click_interval_seconds=(
                                    self.gc.get_deep_link_page_click_interval_seconds()
                                ),
                                event_logger=self._log_system_chain,
                                event_context={
                                    'category': 'watch',
                                    'watch_id': watch_id,
                                    'source_chat_id': source_chat_id,
                                    'source_message_id': comment_id,
                                    'target_link': target_link,
                                    'post_message_id': int(source_message_id),
                                    'comment_id': comment_id,
                                },
                            )
                        )
                    except DeepLinkResolveError as e:
                        self._log_system_chain(
                            category='watch',
                            stage='deep_link_failed',
                            message=f'Discussion deep link resolve failed: {e}',
                            level='error',
                            watch_id=watch_id,
                            source_chat_id=source_chat_id,
                            source_message_id=source_message_id,
                            target_link=target_link,
                            details={
                                'comment_id': comment_id,
                                'error': str(e),
                            },
                        )
                        continue
                    if not resolved_list:
                        continue
                    messages_to_forward = []
                    by_group: dict = {}
                    singles = []
                    for resolved in resolved_list:
                        group_id = getattr(resolved, 'media_group_id', None)
                        if group_id is None:
                            singles.append(resolved)
                        else:
                            by_group.setdefault(group_id, []).append(resolved)
                    for group_members in by_group.values():
                        group_members.sort(key=lambda item: getattr(item, 'id', 0) or 0)
                        messages_to_forward.append((group_members[0], group_members))
                    for resolved in singles:
                        messages_to_forward.append((resolved, None))
                runtime_filter = self.runtime_message_filter(media_types_override)
                for forward_message, forward_group in messages_to_forward:
                    # 深链取回媒体跳过关键词；未开深链时评论仍走完整过滤。
                    if not runtime_filter.should_pass(
                            forward_message, ignore_keywords=resolve_deep_link,
                    ):
                        continue
                    forward_chat = getattr(forward_message, 'chat', None)
                    forward_chat_id = getattr(forward_chat, 'id', None)
                    if forward_chat_id is None:
                        meta = getattr(forward_message, '_deep_link_meta', {}) or {}
                        forward_chat_id = meta.get('bot') or getattr(
                            getattr(comment, 'chat', None), 'id', source_chat_id
                        )
                    media_group_ids = (
                        sorted(member.id for member in forward_group) if forward_group else None
                    )
                    await self._invoke('forward', 
                        client=client,
                        message=forward_message,
                        message_id=getattr(forward_message, 'id', comment.id),
                        origin_chat_id=forward_chat_id,
                        target_chat_id=target_chat_id,
                        target_link=target_link,
                        download_upload=True,
                        done_notice=done_notice,
                        watch_id=watch_id,
                        media_group=media_group_ids,
                        source_folder=post_archive_folder,
                        archive_source_link=getattr(parent_message, 'link', None) if parent_message else None,
                        media_types_override=media_types_override,
                        archive_by_author=archive_by_author,
                        archive_title_source=title_source,
                    )
                    count += 1
        except (ValueError, AttributeError, MsgIdInvalid) as e:
            fetch_error = type(e).__name__
        finally:
            elapsed = time.time() - fetch_started
            error_suffix = f'，错误={fetch_error}' if fetch_error else ''
            slow_empty = (
                matched_deep_link_comments == 0
                and elapsed >= 5.0
                and not fetch_error
            )
            comment_label = (
                '白名单深链评论' if resolve_deep_link else '可转发评论'
            )
            self._log_system_chain(
                category='watch',
                stage='discussion_fetch',
                message=(
                    f'评论区拉取完成: {comment_label} {matched_deep_link_comments} 条'
                    f'（{elapsed:.1f}s）{error_suffix}'
                ),
                level='warning' if (fetch_error or slow_empty) else 'info',
                watch_id=watch_id,
                source_chat_id=source_chat_id,
                source_message_id=source_message_id,
                target_link=target_link,
                details={
                    'post_message_id': int(source_message_id),
                    'matched_comments': matched_deep_link_comments,
                    'elapsed_seconds': round(elapsed, 3),
                    'error': fetch_error,
                    'resolve_deep_link': resolve_deep_link,
                },
            )
        return count

    async def listen_forward(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message
    ):
        try:
            link: str = message.link
            meta = await parse_link(client=self.app.client, link=link)
            listen_chat_id = meta.get('chat_id')
            trace_id, origin_chat_id, message_id = self._message_chain_context(message)
            self._log_system_chain(
                category='watch',
                stage='message_received',
                message='监听转发收到新消息',
                trace_id=trace_id,
                source_chat_id=origin_chat_id,
                source_message_id=message_id,
                details={
                    'source_link': link,
                    'resolved_chat_id': listen_chat_id,
                    'active_rules': list(self.listen_forward_chat)
                }
            )
            matched = False
            for m in self.listen_forward_chat:
                rule = parse_forward_watch_rule(m)
                listen_link = rule.get('source_link')
                target_link = rule.get('target_link')
                include_comment = bool(rule.get('include_comment'))
                archive_by_author = bool(rule.get('archive_by_author'))
                archive_title_source = normalize_archive_title_source(
                    rule.get('archive_title_source')
                )
                _listen_link_meta = await parse_link(
                    client=self.app.client,
                    link=listen_link
                )
                _target_link_meta = await parse_link(
                    client=self.app.client,
                    link=target_link
                )
                _listen_chat_id = _listen_link_meta.get('chat_id')
                _target_chat_id = _target_link_meta.get('chat_id')
                if listen_chat_id == _listen_chat_id:
                    matched = True
                    watch_manager = self._watch_manager()
                    watch_id = (
                        watch_manager.forward_watch_id(m)
                        if watch_manager is not None
                        else f"forward:{m}"
                    )
                    resolve_deep_link = bool(rule.get('resolve_deep_link'))
                    self._log_system_chain(
                        category='watch',
                        stage='rule_matched',
                        message=f'命中监听规则: {listen_link} -> {target_link}',
                        trace_id=trace_id,
                        watch_id=watch_id,
                        source_chat_id=origin_chat_id,
                        source_message_id=message_id,
                        target_link=target_link,
                        details={
                            'listen_link': listen_link,
                            'include_comment': include_comment,
                            'resolve_deep_link': resolve_deep_link,
                            'archive_by_author': archive_by_author,
                            'archive_title_source': archive_title_source,
                        }
                    )
                    forward_origin_chat_id = _listen_chat_id
                    forward_message_id = message.id
                    channel_source_link = link
                    group_messages = None
                    if getattr(message, 'media_group_id', None):
                        try:
                            group_messages = await message.get_media_group()
                        except Exception:
                            group_messages = None
                    if group_messages:
                        self.inherit_media_group_title(group_messages, propagate_to=message)
                        channel_source_folder = archive_source_folder_for_messages(
                            group_messages,
                            fallback_chat_id=_listen_chat_id,
                            fallback_link=link,
                            archive_by_author=archive_by_author,
                            archive_title_source=archive_title_source,
                        )
                    else:
                        channel_source_folder = archive_source_folder(
                            message,
                            fallback_chat_id=_listen_chat_id,
                            fallback_link=link,
                            archive_by_author=archive_by_author,
                            archive_title_source=archive_title_source,
                        )
                    media_types_override = self._watch_media_types_override(watch_id)
                    runtime_filter = self.runtime_message_filter(media_types_override)
                    # Keyword Blacklist on the Source Post (incl. album title) before
                    # deep-link resolve — resolved bot media often has a clean caption.
                    if not runtime_filter.should_pass(message):
                        reject_reason = (
                            runtime_filter.get_reject_reason(message) or '消息过滤器拒绝'
                        )
                        self._log_system_chain(
                            category='filter',
                            stage='filter_reject',
                            message=f'消息被过滤器拦截: {reject_reason}',
                            level='info',
                            trace_id=trace_id,
                            watch_id=watch_id,
                            source_chat_id=origin_chat_id,
                            source_message_id=message_id,
                            target_link=target_link,
                            details={'reject_reason': reject_reason, 'phase': 'source_post'},
                        )
                        self._record_watch_event(
                            watch_id, origin_chat_id, message_id,
                            _target_chat_id, target_link,
                            'skipped', f'跳过转发({reject_reason})。'
                        )
                        return
                    messages_to_forward = [message]
                    if resolve_deep_link:
                        from module.transfer.deep_link import (
                            DEEP_LINK_NO_LINK_AWAIT_COMMENT_MESSAGE,
                            DeepLinkResolveError,
                            messages_after_deep_link_resolve,
                            normalize_resolved_messages,
                        )
                        resolver = self.get_deep_link_resolver()
                        try:
                            resolved_list = normalize_resolved_messages(
                                await resolver.resolve(
                                    client=self.app.client,
                                    message=message,
                                    whitelist=self.gc.get_deep_link_bot_whitelist(),
                                    timeout_seconds=self.gc.get_deep_link_timeout_seconds(),
                                    min_interval_seconds=self.gc.get_deep_link_min_interval_seconds(),
                                    settle_seconds=self.gc.get_deep_link_settle_seconds(),
                                    max_pages=self.gc.get_deep_link_max_pages(),
                                    page_click_interval_seconds=(
                                        self.gc.get_deep_link_page_click_interval_seconds()
                                    ),
                                    event_logger=self._log_system_chain,
                                    event_context={
                                        'category': 'watch',
                                        'watch_id': watch_id,
                                        'source_chat_id': origin_chat_id,
                                        'source_message_id': message_id,
                                        'target_link': target_link,
                                    },
                                )
                            )
                        except DeepLinkResolveError as e:
                            self._log_system_chain(
                                category='watch',
                                stage='deep_link_failed',
                                message=f'Deep link resolve failed: {e}',
                                level='error',
                                trace_id=trace_id,
                                watch_id=watch_id,
                                source_chat_id=origin_chat_id,
                                source_message_id=message_id,
                                target_link=target_link,
                                details={'error': str(e)},
                            )
                            continue
                        messages_to_forward = messages_after_deep_link_resolve(
                            resolve_enabled=True,
                            source_message=message,
                            resolved_list=resolved_list,
                        )
                        if messages_to_forward is None:
                            # 不转发封面；双开评论区时继续延迟抓取，不记「跳过」以免误判整帖结束。
                            self._log_system_chain(
                                category='watch',
                                stage='deep_link_await_comment',
                                message=DEEP_LINK_NO_LINK_AWAIT_COMMENT_MESSAGE,
                                level='info',
                                trace_id=trace_id,
                                watch_id=watch_id,
                                source_chat_id=origin_chat_id,
                                source_message_id=message_id,
                                target_link=target_link,
                                details={'include_comment': include_comment},
                            )
                            messages_to_forward = []
                    for forward_unit in messages_to_forward:
                        ignore_kw = (
                            resolve_deep_link and forward_unit is not message
                        )
                        if not runtime_filter.should_pass(
                                forward_unit, ignore_keywords=ignore_kw,
                        ):
                            reject_reason = (
                                runtime_filter.get_reject_reason(
                                    forward_unit, ignore_keywords=ignore_kw,
                                ) or '媒体类型未允许'
                            )
                            self._log_system_chain(
                                category='filter',
                                stage='filter_reject',
                                message=f'消息被过滤器拦截: {reject_reason}',
                                level='info',
                                trace_id=trace_id,
                                watch_id=watch_id,
                                source_chat_id=origin_chat_id,
                                source_message_id=message_id,
                                target_link=target_link,
                                details={
                                    'reject_reason': reject_reason,
                                    'phase': 'forward_unit',
                                    'forward_message_id': getattr(forward_unit, 'id', None),
                                },
                            )
                            self._record_watch_event(
                                watch_id, origin_chat_id, message_id,
                                _target_chat_id, target_link,
                                'skipped', f'跳过转发({reject_reason})。'
                            )
                            continue
                        forward_origin_chat_id = _listen_chat_id
                        forward_message_id = getattr(forward_unit, 'id', message.id)
                        if resolve_deep_link and forward_unit is not message:
                            resolved_chat = getattr(forward_unit, 'chat', None)
                            resolved_chat_id = getattr(resolved_chat, 'id', None)
                            if resolved_chat_id is not None:
                                forward_origin_chat_id = resolved_chat_id
                            else:
                                meta = getattr(forward_unit, '_deep_link_meta', {}) or {}
                                if meta.get('bot'):
                                    forward_origin_chat_id = meta['bot']
                        allowed = runtime_filter.media_types or {}
                        try:
                            media_group_ids = await forward_unit.get_media_group()
                            if not media_group_ids:
                                raise ValueError
                            if not allowed.get('video') or not allowed.get('photo'):
                                log.warning('由于过滤了图片或视频类型的转发,将不再以媒体组方式发送。')
                                raise ValueError
                            if (
                                    getattr(getattr(forward_unit, 'chat', None), 'is_creator', False) or
                                    getattr(getattr(forward_unit, 'chat', None), 'is_admin', False)
                            ) and (
                                    getattr(getattr(forward_unit, 'from_user', None), 'id', -1) ==
                                    getattr(getattr(client, 'me', None), 'id', None)
                            ):
                                pass
                            elif (
                                    getattr(getattr(forward_unit, 'chat', None), 'has_protected_content', False) or
                                    getattr(getattr(forward_unit, 'sender_chat', None), 'has_protected_content', False) or
                                    getattr(forward_unit, 'has_protected_content', False)
                            ):
                                raise ValueError
                            if not self.handle_media_groups.get(listen_chat_id):
                                self.handle_media_groups[listen_chat_id] = set()
                            unit_key = getattr(forward_unit, 'id', None)
                            if listen_chat_id in self.handle_media_groups and unit_key not in self.handle_media_groups.get(
                                    listen_chat_id):
                                ids: set = set()
                                for peer_message in media_group_ids:
                                    peer_id = peer_message.id
                                    ids.add(peer_id)
                                if ids:
                                    old_ids: Union[None, set] = self.handle_media_groups.get(listen_chat_id)
                                    if old_ids and isinstance(old_ids, set):
                                        old_ids.update(ids)
                                        self.handle_media_groups[listen_chat_id] = old_ids
                                    else:
                                        self.handle_media_groups[listen_chat_id] = ids
                                await self._invoke('forward', 
                                    client=client,
                                    message=forward_unit,
                                    message_id=forward_message_id,
                                    origin_chat_id=forward_origin_chat_id,
                                    target_chat_id=_target_chat_id,
                                    target_link=target_link,
                                    download_upload=False,
                                    media_group=sorted(ids),
                                    watch_id=watch_id,
                                    trace_id=trace_id,
                                    source_folder=channel_source_folder,
                                    archive_source_link=channel_source_link,
                                    media_types_override=media_types_override,
                                    archive_by_author=archive_by_author,
                                    archive_title_source=archive_title_source,
                                )
                                continue
                            continue
                        except ValueError:
                            self._log_system_chain(
                                category='forward',
                                stage='media_group_fallback',
                                message='媒体组直转不可用，回退单条转发(允许下载上传)',
                                trace_id=trace_id,
                                watch_id=watch_id,
                                source_chat_id=origin_chat_id,
                                source_message_id=message_id,
                                target_link=target_link
                            )
                        await self._invoke('forward', 
                            client=client,
                            message=forward_unit,
                            message_id=forward_message_id,
                            origin_chat_id=forward_origin_chat_id,
                            target_chat_id=_target_chat_id,
                            target_link=target_link,
                            download_upload=True,
                            watch_id=watch_id,
                            trace_id=trace_id,
                            source_folder=channel_source_folder,
                            archive_source_link=channel_source_link,
                            media_types_override=media_types_override,
                            archive_by_author=archive_by_author,
                            archive_title_source=archive_title_source,
                        )
                    if include_comment:
                        await self.schedule_or_forward_discussion_replies(
                            client=client,
                            source_chat_id=_listen_chat_id,
                            source_message_id=message_id,
                            target_chat_id=_target_chat_id,
                            target_link=target_link,
                            watch_id=watch_id,
                        )
                    return
            if not matched:
                self._log_system_chain(
                    category='watch',
                    stage='rule_not_matched',
                    message='消息来源频道未匹配任何监听转发规则',
                    level='warning',
                    trace_id=trace_id,
                    source_chat_id=origin_chat_id,
                    source_message_id=message_id,
                    details={
                        'source_link': link,
                        'resolved_chat_id': listen_chat_id,
                        'active_rules': list(self.listen_forward_chat)
                    }
                )
        except (ValueError, KeyError, UsernameInvalid, ChatWriteForbidden) as e:
            log.error(
                f'监听转发出现错误,{_t(KeyWord.REASON)}:{e}频道性质可能发生改变,包括但不限于(频道解散、频道名改变、频道类型改变、该账户没有在目标频道上传的权限、该账号被当前频道移除)。')
            self._log_system_chain(
                category='watch',
                stage='error',
                message=f'监听转发错误: {e}',
                level='error',
                source_chat_id=str(getattr(getattr(message, 'chat', None), 'id', '')),
                source_message_id=getattr(message, 'id', None)
            )
        except Exception as e:
            log.exception(f'监听转发出现错误,{_t(KeyWord.REASON)}:"{e}"')
            self._log_system_chain(
                category='watch',
                stage='error',
                message=f'监听转发异常: {e}',
                level='error',
                source_chat_id=str(getattr(getattr(message, 'chat', None), 'id', '')),
                source_message_id=getattr(message, 'id', None)
            )

