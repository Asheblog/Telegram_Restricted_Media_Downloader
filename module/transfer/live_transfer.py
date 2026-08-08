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
from pyrogram.errors import FloodWait, FloodPremiumWait
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
from module.enums import (
    KeyWord,
    BotCallbackText,
    BotButton,
    DownloadType,
)
from module.language import _t
from module.pikpak_integration import PikpakIntegrationManager
from module.source_folders import (
    archive_source_folder,
    archive_source_folder_for_messages,
    media_group_post_message_id,
    resolve_forward_archive_source_folder,
)
from module.util import (
    parse_link,
    safe_message,
    make_forward_watch_rule,
    parse_forward_watch_rule,
    iter_discussion_reply_forward_units,
)


class LiveTransferService:
    """Listen/forward transfer behaviour extracted from the downloader facade."""

    def __init__(self, host):
        object.__setattr__(self, '_host', host)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, '_host'), name)

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
    ) -> None:
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
    ):
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
                    )
                else:
                    channel_source_folder = archive_source_folder(
                        message,
                        fallback_chat_id=origin_chat_id,
                        fallback_link=archive_source_link or getattr(message, 'link', None),
                        archive_by_author=archive_by_author,
                    )
            channel_source_link = archive_source_link or getattr(message, 'link', None)
            if not ignore_type_filter:
                te = getattr(self, 'transfer_engine', None)
                if te is not None and hasattr(te, 'runtime_message_filter'):
                    runtime_filter = te.runtime_message_filter(media_types_override)
                elif media_types_override is not None:
                    from module.core.media_types import build_runtime_message_filter
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
                    and not PikpakIntegrationManager.message_has_pikpak_ingestible_media(message)
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
                while True:
                    try:
                        forwarded_message = await self.app.client.copy_media_group(
                            chat_id=target_chat_id,
                            from_chat_id=origin_chat_id,
                            message_id=message_id,
                            disable_notification=True
                        )
                        break
                    except (FloodWait, FloodPremiumWait) as e:
                        await self.wait_for_telegram_flood(e, action='copy media group')
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
                    while True:
                        try:
                            forwarded_message = await message.copy(
                                chat_id=target_chat_id,
                                disable_notification=True,
                                protect_content=False,
                            )
                            break
                        except (FloodWait, FloodPremiumWait) as e:
                            await self.wait_for_telegram_flood(e, action='copy held message')
                if not self.forwarded_message_has_identity(forwarded_message):
                    while True:
                        try:
                            forwarded_message = await self.app.client.copy_message(
                                chat_id=target_chat_id,
                                from_chat_id=origin_chat_id,
                                message_id=message_id,
                                disable_notification=True,
                                protect_content=False
                            )
                            break
                        except (FloodWait, FloodPremiumWait) as e:
                            await self.wait_for_telegram_flood(e, action='copy message')
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
                source_folder=channel_source_folder
            )
            if self.transfer_store and link and target_link:
                from module.transfer.watch_inline import ensure_download_fallback_transfer_task
                fallback_task_id = ensure_download_fallback_transfer_task(
                    store=self.transfer_store,
                    source_link=link,
                    target_link=target_link,
                    target_profile=upload_meta.get('target_profile') or 'pikpak',
                    watch_id=watch_id,
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
            watch_id = self.watch_manager._download_chat_watch_id.get(origin_chat_id)
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
    ) -> int:
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
                    watch_id = self.watch_manager.forward_watch_id(m)
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
                        )
                    else:
                        channel_source_folder = archive_source_folder(
                            message,
                            fallback_chat_id=_listen_chat_id,
                            fallback_link=link,
                            archive_by_author=archive_by_author,
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

