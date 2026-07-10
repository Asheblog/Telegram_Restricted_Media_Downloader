# coding=UTF-8
"""Bot host methods — IBotHost seam for CallbackHandler."""
import asyncio
import random
from typing import Union, Optional

import pyrogram
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified, MsgIdInvalid

from module import log
from module.filter import Filter
from module.bot import KeyboardButton
from module.enums import BotCallbackText, BotButton, DownloadType, KeyWord
from module.language import _t
from module.live_watch_manager import LiveWatchManager
from module.task import DownloadTask


class BotHostMixin:
    async def get_download_link_from_bot(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message,
            with_upload: Union[dict, None] = None
    ):
        link_meta: Union[dict, None] = await self.bot.get_download_link_from_bot(client, message)
        if link_meta is None:
            return None
        right_link: set = link_meta.get('right_link')
        invalid_link: set = link_meta.get('invalid_link')
        last_bot_message: Union[pyrogram.types.Message, None] = link_meta.get('last_bot_message')
        exist_link: set = set([_ for _ in right_link if _ in self.bot_task_link])
        exist_link.update(right_link & DownloadTask.COMPLETE_LINK)
        if not with_upload:
            right_link -= exist_link
        if last_bot_message:
            await self.safe_edit_message(
                client=client,
                message=message,
                last_message_id=last_bot_message.id,
                text=self.update_text(
                    right_link=right_link,
                    exist_link=exist_link if not with_upload else None,
                    invalid_link=invalid_link
                )
            )
        else:
            log.warning('消息过长编辑频繁,暂时无法通过机器人显示通知。')
        links: Union[set, None] = self._process_links(link=list(right_link))

        if links is None:
            return None
        for link in links:
            task: dict = await self.create_download_task(
                message_ids=link,
                retry=None,
                with_upload=with_upload
            )
            invalid_link.add(link) if task.get('status') == DownloadStatus.FAILURE else self.bot_task_link.add(link)
        right_link -= invalid_link
        await self.safe_edit_message(
            client=client,
            message=message,
            last_message_id=last_bot_message.id,
            text=self.update_text(
                right_link=right_link,
                exist_link=exist_link if not with_upload else None,
                invalid_link=invalid_link
            )
        )
    def build_download_upload_meta(
            self,
            target_link: str,
            target_profile: Optional[str] = None,
            source_link: Optional[str] = None,
            source_folder: Optional[str] = None,
            task_id: Optional[int] = None,
            media_type: Optional[str] = None,
            send_as_media_group: Optional[bool] = None
    ) -> dict:
        return self.transfer_engine.build_download_upload_meta(
            target_link, target_profile, source_link, source_folder,
            task_id, media_type, send_as_media_group
        )

    @staticmethod
    def download_watch_id(link: str) -> str:
        return LiveWatchManager.download_watch_id(link)

    @staticmethod
    def forward_watch_id(rule: str) -> str:
        return LiveWatchManager.forward_watch_id(rule)

    async def help(self, *args, **kwargs) -> dict:
        return await self.bot.help(*args, **kwargs)

    async def table(self, *args, **kwargs) -> dict:
        return await self.bot.table(*args, **kwargs)

    def add_keyword_mode_handler(self, *args, **kwargs) -> None:
        return self.bot.add_keyword_mode_handler(*args, **kwargs)

    @property
    def download_chat_filter(self) -> dict:
        return self.bot.download_chat_filter

    @property
    def adding_keywords(self) -> list:
        return self.bot.adding_keywords

    @property
    def last_message(self):
        return self.bot.last_message

    @property
    def last_client(self):
        return self.bot.last_client
    async def start(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message
    ):
        self.last_client: pyrogram.Client = client
        self.last_message: pyrogram.types.Message = message
        if self.gc.config.get(BotCallbackText.NOTICE):
            await self.bot.start(client, message)

    async def callback_data(self, client: pyrogram.Client, callback_query: pyrogram.types.CallbackQuery):
        return await self.callback_handler.handle(client, callback_query)
    async def download_chat(
            self,
            chat_id: str,
            callback_query: pyrogram.types.CallbackQuery
    ) -> Union[list, None]:
        async def _progress(
                _text: str,
                _reply_markup: InlineKeyboardMarkup
        ) -> Union[pyrogram.types.Message, None]:
            try:
                return await callback_query.message.edit_text(
                    text=_text,
                    reply_markup=_reply_markup
                )
            except MessageNotModified:
                pass

        origin_callback_query_text: str = callback_query.message.text
        cq = await _progress(
            _text=f'{callback_query.message.text}\n'
                  f'⏳需要检索该频道所有匹配的消息,请耐心等待。\n'
                  f'💡请忽略终端中的请求频繁提示,不会影响下载。',
            _reply_markup=KeyboardButton.single_button(
                text=BotButton.RETRIEVE_MESSAGE,
                callback_data=BotCallbackText.NULL
            )
        )
        callback_query_text: str = cq.text
        last_displayed_count: int = -1  # 记录上次显示的数量,初始化为-1确保第一次一定更新。
        last_update_time: float = 0  # 记录上次更新的时间戳。
        update_interval: float = 1.0  # 更新时间间隔(秒),无论多少条消息,都只在这个时间间隔更新一次。

        try:
            _filter = Filter()
            download_chat_filter: Union[dict, None] = None
            for i in self.download_chat_filter:
                if chat_id == i:
                    download_chat_filter = self.download_chat_filter.get(chat_id)
            if not download_chat_filter:
                return None
            if not isinstance(download_chat_filter, dict):
                return None
            chat_id: Union[str, int] = int(chat_id) if chat_id.startswith('-') else chat_id
            date_filter = download_chat_filter.get('date_range')
            start_date = date_filter.get('start_date')
            end_date = date_filter.get('end_date')
            download_type: dict = download_chat_filter.get('download_type')
            keyword_filter: dict = download_chat_filter.get('keyword', {})
            include_comment: bool = download_chat_filter.get('comment', False)
            active_keywords = [k for k, v in keyword_filter.items() if v]
            links: list = []
            # 第一阶段：收集匹配的消息。
            messages_to_download = []
            media_group_matched = set()  # 记录已匹配的media_group_id。
            await _progress(
                _text=f'{callback_query_text}\n'
                      f'{random.choice(("🔎", "🔍"))}检索消息中,已匹配到0条消息。',
                _reply_markup=KeyboardButton.single_button(
                    text=BotButton.RETRIEVE_MESSAGE,
                    callback_data=BotCallbackText.NULL)
            )
            async for message in self.app.client.get_chat_history(
                    chat_id=chat_id,
                    reverse=True
            ):
                # 对于媒体组，如果该媒体组已匹配，直接添加。
                if getattr(message, 'media_group_id', None) and message.media_group_id in media_group_matched:
                    messages_to_download.append(message)
                    continue

                # 先过全局消息过滤器（预过滤），再过 per-chat 过滤
                if self.message_filter.should_pass(message) and (
                        _filter.date_range(message, start_date, end_date) and
                        _filter.dtype(message, download_type) and
                        _filter.keyword_filter(message, active_keywords)):
                    messages_to_download.append(message)
                    # 如果是媒体组的第一条消息，记录该media_group_id。
                    if message.media_group_id:
                        media_group_matched.add(message.media_group_id)
                    # 使用时间节流机制,只在指定时间间隔后才更新,避免频繁API调用。
                    current_time = asyncio.get_event_loop().time()
                    current_count = len(messages_to_download)
                    if current_time - last_update_time >= update_interval:
                        await _progress(
                            _text=f'{callback_query_text}\n'
                                  f'{random.choice(("🔎", "🔍"))}检索消息中,已匹配到{current_count}条消息。',
                            _reply_markup=KeyboardButton.single_button(
                                text=BotButton.RETRIEVE_MESSAGE,
                                callback_data=BotCallbackText.NULL)
                        )
                        last_displayed_count = current_count
                        last_update_time = current_time
            # 确保最后一次更新显示正确的消息数量。
            final_count = len(messages_to_download)
            if final_count != last_displayed_count:
                await _progress(
                    _text=f'{callback_query_text}\n'
                          f'{random.choice(("🔎", "🔍"))}检索消息中,已匹配到{final_count}条消息。',
                    _reply_markup=KeyboardButton.single_button(
                        text=BotButton.RETRIEVE_MESSAGE,
                        callback_data=BotCallbackText.NULL)
                )
            if not messages_to_download:
                await _progress(
                    _text=f'{callback_query.message.text}\n'
                          '❎没有找到任何匹配的消息。',
                    _reply_markup=KeyboardButton.single_button(
                        text=BotButton.TASK_CANCEL,
                        callback_data=BotCallbackText.NULL
                    )

                )
                return None
            message_count: int = len(messages_to_download)
            last_displayed_comment_count: int = -1  # 记录上次显示的评论数量,初始化为-1确保第一次一定更新。
            last_comment_update_time: float = 0  # 记录上次评论更新的时间戳。
            processed_message_count: int = 0  # 记录已处理的消息数量。
            # 第二阶段：对匹配的消息进行处理，获取评论区。
            if include_comment:
                await _progress(
                    _text=f'{callback_query_text}\n'
                          f'{random.choice(("🔎", "🔍"))}检索评论区中,已匹配到0条消息。',
                    _reply_markup=KeyboardButton.single_button(
                        text=BotButton.RETRIEVE_COMMENT,
                        callback_data=BotCallbackText.NULL)
                )
            for message in messages_to_download:
                message_link = message.link if message.link else message
                links.append(message_link)
                processed_message_count += 1
                if not include_comment:
                    continue
                # 检查并获取评论区。
                try:
                    async for comment in self.app.client.get_discussion_replies(
                            chat_id=chat_id,
                            message_id=message.id
                    ):
                        # 根据用户设置的download_type过滤评论中的媒体，但不过滤具体时间。
                        if not _filter.dtype(comment, download_type):
                            continue
                        comment_link = comment.link if comment.link else comment
                        links.append(comment_link)
                        # 使用时间节流机制,只在指定时间间隔后才更新,避免频繁API调用。
                        current_time = asyncio.get_event_loop().time()
                        # 计算评论数量: 总链接数减去已处理的消息数。
                        current_comment_count = len(links) - processed_message_count
                        if current_time - last_comment_update_time >= update_interval:
                            await _progress(
                                _text=f'{callback_query_text}\n'
                                      f'{random.choice(("🔎", "🔍"))}检索评论区中,已匹配到{current_comment_count}条消息。',
                                _reply_markup=KeyboardButton.single_button(
                                    text=BotButton.RETRIEVE_COMMENT,
                                    callback_data=BotCallbackText.NULL)
                            )
                            last_displayed_comment_count = current_comment_count
                            last_comment_update_time = current_time
                except (ValueError, AttributeError, MsgIdInvalid):
                    # 消息没有评论区或消息ID无效，跳过。
                    pass
            # 确保最后一次更新显示正确的评论数量。
            if include_comment:
                final_comment_count = len(links) - message_count
                if final_comment_count != last_displayed_comment_count:
                    await _progress(
                        _text=f'{callback_query_text}\n'
                              f'{random.choice(("🔎", "🔍"))}检索评论区中,已匹配到{final_comment_count}条消息。',
                        _reply_markup=KeyboardButton.single_button(
                            text=BotButton.RETRIEVE_COMMENT,
                            callback_data=BotCallbackText.NULL)
                    )
            diy_download_type: list = [_ for _ in DownloadType()]
            comment_count: int = (len(links) - message_count) if include_comment else 0
            total_count: int = message_count + comment_count
            assigned_count: int = 0
            last_progress_update_time: float = 0  # 记录上次分配任务更新的时间戳。
            for link in links:
                if assigned_count == total_count:
                    reply_markup = KeyboardButton.single_button(
                        text=BotButton.TASK_ASSIGN,
                        callback_data=BotCallbackText.NULL
                    )
                else:
                    reply_markup = KeyboardButton.single_button(
                        text=BotButton.ASSIGNING_TASK,
                        callback_data=BotCallbackText.NULL
                    )

                # 使用时间节流机制,只在指定时间间隔后才更新任务分配进度。
                current_time = asyncio.get_event_loop().time()
                if current_time - last_progress_update_time >= update_interval:
                    while True:
                        try:
                            await _progress(
                                _text=f'{origin_callback_query_text}\n'
                                      f'🔎匹配消息:{message_count}条,评论区消息:{comment_count}条,共{total_count}条。\n'
                                      f'⭐️[{assigned_count}/{total_count}]分配下载任务中。\n'
                                      f'{random.choice(("⏳", "⌛"))}{self.pb.bot(assigned_count, total_count)}',
                                _reply_markup=reply_markup
                            )
                            last_progress_update_time = current_time
                            break
                        except MessageNotModified:
                            break
                        except FloodWait as e:
                            await asyncio.sleep(e.value)
                        except Exception:
                            break
                await self.create_download_task(
                    message_ids=link,
                    single_link=True,
                    diy_download_type=diy_download_type
                )
                assigned_count += 1
            await _progress(
                _text=origin_callback_query_text,
                _reply_markup=KeyboardButton.single_button(
                    text=BotButton.TASK_ASSIGN,
                    callback_data=BotCallbackText.NULL
                )
            )
            return links
        except Exception as e:
            log.error(
                f'{_t(KeyWord.CHANNEL)}:"{chat_id}",无法进行下载,{_t(KeyWord.REASON)}:"{e}"',
                exc_info=True
            )
            asyncio.create_task(callback_query.message.edit_text(
                text=f'{origin_callback_query_text}`\n'
                     f'⚠️由于"{e}"无法执行频道下载任务。',
                reply_markup=KeyboardButton.single_button(
                    text=BotButton.TASK_CANCEL,
                    callback_data=BotCallbackText.NULL
                )
            ))

