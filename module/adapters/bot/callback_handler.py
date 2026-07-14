# coding=UTF-8
import asyncio
import datetime
from copy import deepcopy
from functools import partial
from typing import Union

import pyrogram
from pyrogram.errors.exceptions.bad_request_400 import (
    MessageNotModified,
)

from module import (
    console,
    log,
    LINK_PREVIEW_OPTIONS,
)
from module.adapters.bot.bot import Bot, KeyboardButton
from module.enums import (
    DownloadStatus,
    UploadStatus,
    KeyWord,
    BotCallbackText,
    BotButton,
    DownloadType,
    CalenderKeyboard,
)
from module.language import _t
from module.source_folders import archive_source_folder
from module.task import DownloadTask, UploadTask
from module.util import (
    is_docker,
    parse_forward_watch_rule,
)
from module.ports import IBotHost


class CallbackHandler:
    def __init__(
        self,
        app_getter,
        gc_getter,
        diagnostic,
        watch_manager_getter=None,
        transfer_store_getter=None,
        loop_getter=None,
        user_getter=None,
        my_id_getter=None,
        host: IBotHost = None,
        downloader_ref=None,
    ):
        self._app = app_getter
        self._gc = gc_getter
        self.diagnostic = diagnostic
        self._watch_manager = watch_manager_getter
        self._transfer_store = transfer_store_getter
        self._loop = loop_getter
        self._user = user_getter
        self._my_id = my_id_getter
        self._host = host if host is not None else downloader_ref
        self._downloader = self._host

    @property
    def app(self):
        return self._app()

    @property
    def gc(self):
        return self._gc()

    @property
    def watch_manager(self):
        return self._watch_manager() if self._watch_manager else None

    @property
    def transfer_store(self):
        return self._transfer_store() if self._transfer_store else None

    @property
    def loop(self):
        return self._loop() if self._loop else None

    @property
    def user(self):
        return self._user() if self._user else None

    @property
    def my_id(self):
        return self._my_id() if self._my_id else None

    def _toggle_button(self, kb, _param: str):
        param: bool = self.gc.get_nesting_config(
            default_nesting=self.gc.default_upload_nesting,
            param='upload',
            nesting_param=_param
        )
        self.gc.config.get('upload', self.gc.default_upload_nesting)[_param] = not param
        u_s: str = '禁用' if param else '开启'
        u_p: str = ''
        if _param == 'delete':
            u_p: str = f'遇到"受限转发"时,下载后上传并"删除上传完成的本地文件"的行为已{u_s}。'
        elif _param == 'download_upload':
            u_p: str = f'遇到"受限转发"时,下载后上传已{u_s}。'
        console.log(u_p, style='#FF4689')
        log.info(u_p)

    def _toggle_download_type_button(self, kb, _param: str):
        """Bot 设置里的下载类型开关：同步写入全局 Media Type Allowlist。"""
        from module.core.media_types import (
            DOWNLOAD_MEDIA_TYPES,
            MEDIA_TYPES_DEFAULT,
            media_types_to_download_type_list,
            resolve_allowed_media_types,
        )
        mf = self.gc.config.setdefault('message_filter', {})
        if not isinstance(mf, dict):
            mf = {}
            self.gc.config['message_filter'] = mf
        media_types = resolve_allowed_media_types(mf.get('media_types'), None)
        _status = bool(media_types.get(_param, False))
        enabled_download = [t for t in DOWNLOAD_MEDIA_TYPES if media_types.get(t)]
        if len(enabled_download) == 1 and _status and _param in DOWNLOAD_MEDIA_TYPES:
            raise ValueError
        media_types[_param] = not _status
        for key in MEDIA_TYPES_DEFAULT:
            media_types.setdefault(key, False)
        mf['media_types'] = media_types
        self.gc.config['forward_type'] = dict(media_types)
        self.gc.forward_type = dict(media_types)
        self.gc.message_filter = mf
        self.gc.save_config(self.gc.config)
        self.app.download_type = media_types_to_download_type_list(media_types)
        self.app.config['download_type'] = self.app.download_type
        f_s = '禁用' if _status else '启用'
        f_p = f'已{f_s}"{_param}"类型（全局媒体白名单）。'
        console.log(f_p, style='#FF4689')
        log.info(f_p)

    def _toggle_forward_type_button(self, kb, _param: str):
        from module.core.media_types import MEDIA_TYPES_DEFAULT, resolve_allowed_media_types
        mf = self.gc.config.setdefault('message_filter', {})
        if not isinstance(mf, dict):
            mf = {}
            self.gc.config['message_filter'] = mf
        media_types = mf.get('media_types')
        if not isinstance(media_types, dict):
            media_types = resolve_allowed_media_types(
                self.gc.config.get('forward_type'),
                None,
            )
        else:
            media_types = resolve_allowed_media_types(media_types, None)
        _status = bool(media_types.get(_param, False))
        if list(media_types.values()).count(True) == 1 and _status:
            raise ValueError
        media_types[_param] = not _status
        for key in MEDIA_TYPES_DEFAULT:
            media_types.setdefault(key, False)
        mf['media_types'] = media_types
        self.gc.config['forward_type'] = dict(media_types)
        self.gc.forward_type = dict(media_types)
        self.gc.message_filter = mf
        self.gc.save_config(self.gc.config)
        f_s = '禁用' if _status else '启用'
        f_p = f'已{f_s}"{_param}"类型（全局媒体白名单）。'
        console.log(f_p, style='#FF4689')
        log.info(f_p)

    def _get_update_time(self, chat_id):
        _start_timestamp = self._downloader.download_chat_filter[chat_id]['date_range'][
            'start_date']
        _end_timestamp = self._downloader.download_chat_filter[chat_id]['date_range']['end_date']
        _start_time = datetime.datetime.fromtimestamp(_start_timestamp) if _start_timestamp else '未定义'
        _end_time = datetime.datetime.fromtimestamp(_end_timestamp) if _end_timestamp else '未定义'
        return _start_time, _end_time

    def _get_format_dtype(self, chat_id):
        from module.core.media_types import DOWNLOAD_MEDIA_TYPES, resolve_allowed_media_types
        cfg = self._downloader.download_chat_filter[chat_id]
        override = cfg.get('media_types')
        mf = getattr(self.gc, 'message_filter', None) or {}
        allowed = resolve_allowed_media_types(
            mf.get('media_types') if isinstance(mf, dict) else None,
            override,
        )
        labels = [_t(dtype) for dtype in DOWNLOAD_MEDIA_TYPES if allowed.get(dtype)]
        if override is None:
            return (','.join(labels) + '（继承系统设置）') if labels else '继承系统设置'
        return ','.join(labels)

    def _get_format_keywords(self, chat_id):
        _keywords = self._downloader.download_chat_filter[chat_id]['keyword']
        if not _keywords:
            return '未定义'
        return ','.join(_keywords.keys())

    def _get_format_comment_status(self, chat_id):
        _status = self._downloader.download_chat_filter[chat_id]['comment']
        return '开' if _status else '关'

    def _remove_chat_id(self, _chat_id):
        if _chat_id in self._downloader.download_chat_filter:
            self._downloader.download_chat_filter.pop(_chat_id)
            log.info(f'"{_chat_id}"已从{self._downloader.download_chat_filter}中移除。')

    def _filter_prompt(self, chat_id):
        return (
            f'💬下载频道:`{chat_id}`\n'
            f'⏮️当前选择的起始日期为:{self._get_update_time(chat_id)[0]}\n'
            f'⏭️当前选择的结束日期为:{self._get_update_time(chat_id)[1]}\n'
            f'📝当前选择的下载类型为:{self._get_format_dtype(chat_id)}\n'
            f'🔑当前匹配的关键词为:{self._get_format_keywords(chat_id)}\n'
            f'👥包含评论区:{self._get_format_comment_status(chat_id)}'
        )

    async def _verification_time(self, callback_query, _start_time, _end_time) -> bool:
        if isinstance(_start_time, datetime.datetime) and isinstance(_end_time, datetime.datetime):
            if _start_time > _end_time:
                await callback_query.message.reply_text(
                    text=f'❌❌❌日期设置失败❌❌❌\n'
                         f'`起始日期({_start_time})`>`结束日期({_end_time})`\n'
                )
                return False
            elif _start_time == _end_time:
                await callback_query.message.reply_text(
                    text=f'❌❌❌日期设置失败❌❌❌\n'
                         f'`起始日期({_start_time})`=`结束日期({_end_time})`\n'
                )
                return False
        return True

    def _toggle_dtype_filter_button(self, chat_id, _param: str):
        from module.core.media_types import DOWNLOAD_MEDIA_TYPES, resolve_allowed_media_types
        cfg = self._downloader.download_chat_filter[chat_id]
        if cfg.get('media_types') is None:
            mf = getattr(self.gc, 'message_filter', None) or {}
            inherited = resolve_allowed_media_types(
                mf.get('media_types') if isinstance(mf, dict) else None,
                None,
            )
            cfg['media_types'] = {t: bool(inherited.get(t, False)) for t in DOWNLOAD_MEDIA_TYPES}
        _dtype: dict = cfg['media_types']
        _status: bool = bool(_dtype.get(_param))
        enabled_count = sum(1 for t in DOWNLOAD_MEDIA_TYPES if _dtype.get(t))
        if enabled_count == 1 and _status:
            raise ValueError
        _dtype[_param] = not _status
        cfg['download_type'] = {t: bool(_dtype.get(t, False)) for t in DOWNLOAD_MEDIA_TYPES}
        f_s = '禁用' if _status else '启用'
        f_p = f'已{f_s}"{_param}"类型用于/download_chat命令的下载（会话覆盖）。'
        log.info(
            f'{f_p}当前的/download_chat下载类型设置:{cfg["download_type"]}')

    async def handle(self, client, callback_query):
        callback_data = await Bot.callback_data(client, callback_query)
        kb = KeyboardButton(callback_query)
        if callback_data is None:
            return None
        elif callback_data == BotCallbackText.NOTICE:
            try:
                self.gc.config[BotCallbackText.NOTICE] = not self.gc.config.get(BotCallbackText.NOTICE)
                self.gc.save_config(self.gc.config)
                n_s: str = '启用' if self.gc.config.get(BotCallbackText.NOTICE) else '禁用'
                n_p: str = f'机器人消息通知已{n_s}。'
                log.info(n_p)
                console.log(n_p, style='#FF4689')
                await kb.toggle_setting_button(global_config=self.gc.config, user_config=self.app.config)
            except Exception as e:
                await callback_query.message.reply_text(
                    '启用或禁用机器人消息通知失败\n(具体原因请前往终端查看报错信息)')
                log.error(f'启用或禁用机器人消息通知失败,{_t(KeyWord.REASON)}:"{e}"')
        elif callback_data == BotCallbackText.BACK_HELP:
            meta: dict = await self._downloader.help()
            await callback_query.message.edit_text(meta.get('text'))
            await callback_query.message.edit_reply_markup(meta.get('keyboard'))
        elif callback_data == BotCallbackText.BACK_TABLE:
            meta: dict = await self._downloader.table()
            await callback_query.message.edit_text(meta.get('text'))
            await callback_query.message.edit_reply_markup(meta.get('keyboard'))
        elif callback_data in (BotCallbackText.DOWNLOAD, BotCallbackText.DOWNLOAD_UPLOAD):
            if not isinstance(self._downloader.cd.data, dict):
                return None
            meta: Union[dict, None] = self._downloader.cd.data.copy()
            self._downloader.cd.data = None
            origin_link: str = meta.get('origin_link')
            target_link: str = meta.get('target_link')
            start_id: Union[int, None] = meta.get('start_id')
            end_id: Union[int, None] = meta.get('end_id')
            if callback_data == BotCallbackText.DOWNLOAD:
                self._downloader.last_message.text = f'/download {origin_link} {start_id} {end_id}'
                await self._downloader.get_download_link_from_bot(
                    client=self._downloader.last_client,
                    message=self._downloader.last_message
                )
            elif callback_data == BotCallbackText.DOWNLOAD_UPLOAD:
                self._downloader.last_message.text = f'/download {origin_link} {start_id} {end_id}'
                await self._downloader.get_download_link_from_bot(
                    client=self._downloader.last_client,
                    message=self._downloader.last_message,
                    with_upload=self._downloader.build_download_upload_meta(
                        target_link=target_link,
                        source_link=origin_link,
                        source_folder=archive_source_folder(fallback_link=origin_link),
                        send_as_media_group=True
                    )
                )
            await kb.task_assign_button()
        elif callback_data == BotCallbackText.LOOKUP_LISTEN_INFO:
            await self.app.client.send_message(
                chat_id=callback_query.message.from_user.id,
                text='/listen_info',
                link_preview_options=LINK_PREVIEW_OPTIONS
            )
        elif callback_data == BotCallbackText.SHUTDOWN:
            try:
                self.app.config['is_shutdown'] = not self.app.config.get('is_shutdown')
                self.app.save_config(self.app.config)
                s_s: str = '启用' if self.app.config.get('is_shutdown') else '禁用'
                s_p: str = f'退出后关机已{s_s}。'
                log.info(s_p)
                console.log(s_p, style='#FF4689')
                await kb.toggle_setting_button(global_config=self.gc.config, user_config=self.app.config)
            except Exception as e:
                await callback_query.message.reply_text('启用或禁用自动关机失败\n(具体原因请前往终端查看报错信息)')
                log.error(f'启用或禁用自动关机失败,{_t(KeyWord.REASON)}:"{e}"')
        elif callback_data == BotCallbackText.SETTING:
            await kb.toggle_setting_button(global_config=self.gc.config, user_config=self.app.config)
        elif callback_data == BotCallbackText.EXPORT_TABLE:
            await kb.toggle_table_button(config=self.gc.config)
        elif callback_data == BotCallbackText.DOWNLOAD_SETTING:
            await kb.toggle_download_setting_button(user_config=self.app.config)
        elif callback_data == BotCallbackText.UPLOAD_SETTING:
            await kb.toggle_upload_setting_button(global_config=self.gc.config)
        elif callback_data == BotCallbackText.FORWARD_SETTING:
            await kb.toggle_forward_setting_button(global_config=self.gc.config)
        elif callback_data in (
                BotCallbackText.LINK_TABLE,
                BotCallbackText.COUNT_TABLE,
                BotCallbackText.UPLOAD_TABLE
        ):
            _prompt_string: str = ''
            _false_text: str = ''
            _choice: str = ''
            res: Union[bool, None] = None
            if callback_data == BotCallbackText.LINK_TABLE:
                _prompt_string: str = '链接统计表'
                _false_text: str = '😵😵😵没有链接需要统计。'
                _choice: str = BotCallbackText.EXPORT_LINK_TABLE
                res: Union[bool, None] = self.app.print_link_table(DownloadTask.LINK_INFO)
            elif callback_data == BotCallbackText.COUNT_TABLE:
                _prompt_string: str = '计数统计表'
                _false_text: str = '😵😵😵当前没有任何下载。'
                _choice: str = BotCallbackText.EXPORT_COUNT_TABLE
                res: Union[bool, None] = self.app.print_count_table()
            elif callback_data == BotCallbackText.UPLOAD_TABLE:
                _prompt_string: str = '上传统计表'
                _false_text: str = '😵😵😵当前没有任何上传。'
                _choice: str = BotCallbackText.EXPORT_UPLOAD_TABLE
                res: Union[bool, None] = self.app.print_upload_table(UploadTask.TASKS)
            if res:
                await callback_query.message.edit_text(f'👌👌👌`{_prompt_string}`已发送至您的「终端」请注意查收。')
                await kb.choice_export_table_button(choice=_choice)
                return None
            elif res is False:
                await callback_query.message.edit_text(_false_text)
            else:
                await callback_query.message.edit_text(
                    f'😵‍💫😵‍💫😵‍💫`{_prompt_string}`打印失败。\n(具体原因请前往终端查看报错信息)')
            await kb.back_table_button()
        elif callback_data in (
                BotCallbackText.TOGGLE_LINK_TABLE,
                BotCallbackText.TOGGLE_COUNT_TABLE,
                BotCallbackText.TOGGLE_UPLOAD_TABLE
        ):
            async def _toggle_table_button(_table_type):
                export_config: dict = self.gc.config.get('export_table')
                export_config[_table_type] = not export_config.get(_table_type)
                if _table_type == 'link':
                    t_t = '链接统计表'
                elif _table_type == 'count':
                    t_t = '计数统计表'
                elif _table_type == 'upload':
                    t_t = '上传统计表'
                else:
                    t_t = '统计表'
                s_t: str = '启用' if export_config.get(_table_type) else '禁用'
                t_p: str = f'退出后导出{t_t}已{s_t}。'
                console.log(t_p, style='#FF4689')
                log.info(t_p)
                self.gc.save_config(self.gc.config)
                await kb.toggle_table_button(
                    config=self.gc.config,
                    choice=_table_type
                )

            if callback_data == BotCallbackText.TOGGLE_LINK_TABLE:
                await _toggle_table_button('link')
            elif callback_data == BotCallbackText.TOGGLE_COUNT_TABLE:
                await _toggle_table_button('count')
            elif callback_data == BotCallbackText.TOGGLE_UPLOAD_TABLE:
                await _toggle_table_button('upload')
        elif callback_data in (
                BotCallbackText.EXPORT_LINK_TABLE,
                BotCallbackText.EXPORT_COUNT_TABLE,
                BotCallbackText.EXPORT_UPLOAD_TABLE
        ):
            _prompt_string: str = ''
            _folder: str = ''
            res: Union[bool, None] = False
            if callback_data == BotCallbackText.EXPORT_LINK_TABLE:
                _prompt_string: str = '链接统计表'
                _folder: str = 'DownloadRecordForm'
                res: Union[bool, None] = self.app.print_link_table(
                    link_info=DownloadTask.LINK_INFO,
                    export=True,
                    only_export=True
                )
            elif callback_data == BotCallbackText.EXPORT_COUNT_TABLE:
                _prompt_string: str = '计数统计表'
                _folder: str = 'DownloadRecordForm'
                res: Union[bool, None] = self.app.print_count_table(
                    export=True,
                    only_export=True
                )
            elif callback_data == BotCallbackText.EXPORT_UPLOAD_TABLE:
                _prompt_string: str = '上传统计表'
                _folder: str = 'UploadRecordForm'
                res: Union[bool, None] = self.app.print_upload_table(
                    upload_tasks=UploadTask.TASKS,
                    export=True,
                    only_export=True
                )
            if res:
                _folder: str = 'form' if is_docker() else _folder
                await callback_query.message.edit_text(
                    f'✅✅✅`{_prompt_string}`已发送至您的「终端」并已「导出」为表格请注意查收。\n(请查看软件目录下`{_folder}`文件夹)')
            elif res is False:
                await callback_query.message.edit_text('😵😵😵没有链接需要统计。')
            else:
                await callback_query.message.edit_text(
                    f'😵‍💫😵‍💫😵‍💫`{_prompt_string}`导出失败。\n(具体原因请前往终端查看报错信息)')
            await kb.back_table_button()
        elif callback_data.startswith(f'{BotCallbackText.UPLOAD_PENDING_LIMIT}:'):
            try:
                limit = int(callback_data.split(':', 1)[1])
                if limit < 1 or limit > 5:
                    raise ValueError
                self.gc.config.setdefault('upload', deepcopy(self.gc.default_upload_nesting))['pending_limit'] = limit
                self.gc.save_config(self.gc.config)
                self._downloader.download_upload_window.notify_limit_changed()
                await kb.toggle_upload_setting_button(global_config=self.gc.config)
            except ValueError:
                await callback_query.message.reply_text('下载后上传队列数量必须在1到5之间。')
            except Exception as e:
                await callback_query.message.reply_text(
                    '下载后上传队列设置失败\n(具体原因请前往终端查看报错信息)')
                log.error(f'下载后上传队列设置失败,{_t(KeyWord.REASON)}:"{e}"')
        elif callback_data in (BotCallbackText.UPLOAD_DOWNLOAD, BotCallbackText.UPLOAD_DOWNLOAD_DELETE):
            try:
                if callback_data == BotCallbackText.UPLOAD_DOWNLOAD:
                    self._toggle_button(kb, 'download_upload')
                elif callback_data == BotCallbackText.UPLOAD_DOWNLOAD_DELETE:
                    self._toggle_button(kb, 'delete')
                self.gc.save_config(self.gc.config)
                await kb.toggle_upload_setting_button(global_config=self.gc.config)
            except Exception as e:
                await callback_query.message.reply_text(
                    '上传设置失败\n(具体原因请前往终端查看报错信息)')
                log.error(f'上传设置失败,{_t(KeyWord.REASON)}:"{e}"')
        elif callback_data in (
                BotCallbackText.TOGGLE_DOWNLOAD_VIDEO,
                BotCallbackText.TOGGLE_DOWNLOAD_PHOTO,
                BotCallbackText.TOGGLE_DOWNLOAD_AUDIO,
                BotCallbackText.TOGGLE_DOWNLOAD_VOICE,
                BotCallbackText.TOGGLE_DOWNLOAD_ANIMATION,
                BotCallbackText.TOGGLE_DOWNLOAD_DOCUMENT,
                BotCallbackText.TOGGLE_DOWNLOAD_VIDEO_NOTE
        ):
            try:
                if callback_data == BotCallbackText.TOGGLE_DOWNLOAD_VIDEO:
                    self._toggle_download_type_button(kb, 'video')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_PHOTO:
                    self._toggle_download_type_button(kb, 'photo')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_AUDIO:
                    self._toggle_download_type_button(kb, 'audio')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_VOICE:
                    self._toggle_download_type_button(kb, 'voice')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_ANIMATION:
                    self._toggle_download_type_button(kb, 'animation')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_DOCUMENT:
                    self._toggle_download_type_button(kb, 'document')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_VIDEO_NOTE:
                    self._toggle_download_type_button(kb, 'video_note')
                self.app.config['download_type'] = self.app.download_type
                self.app.save_config(self.app.config)
                await kb.toggle_download_setting_button(self.app.config)
            except ValueError:
                await callback_query.message.reply_text('⚠️⚠️⚠️至少需要选择一个下载类型⚠️⚠️⚠️')
            except Exception as e:
                await callback_query.message.reply_text(
                    '下载类型设置失败\n(具体原因请前往终端查看报错信息)')
                log.error(f'下载类型设置失败,{_t(KeyWord.REASON)}:"{e}"')
        elif callback_data in (
                BotCallbackText.TOGGLE_FORWARD_VIDEO,
                BotCallbackText.TOGGLE_FORWARD_PHOTO,
                BotCallbackText.TOGGLE_FORWARD_AUDIO,
                BotCallbackText.TOGGLE_FORWARD_VOICE,
                BotCallbackText.TOGGLE_FORWARD_ANIMATION,
                BotCallbackText.TOGGLE_FORWARD_DOCUMENT,
                BotCallbackText.TOGGLE_FORWARD_TEXT,
                BotCallbackText.TOGGLE_FORWARD_VIDEO_NOTE
        ):
            try:
                if callback_data == BotCallbackText.TOGGLE_FORWARD_VIDEO:
                    self._toggle_forward_type_button(kb, 'video')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_PHOTO:
                    self._toggle_forward_type_button(kb, 'photo')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_AUDIO:
                    self._toggle_forward_type_button(kb, 'audio')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_VOICE:
                    self._toggle_forward_type_button(kb, 'voice')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_ANIMATION:
                    self._toggle_forward_type_button(kb, 'animation')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_DOCUMENT:
                    self._toggle_forward_type_button(kb, 'document')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_TEXT:
                    self._toggle_forward_type_button(kb, 'text')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_VIDEO_NOTE:
                    self._toggle_forward_type_button(kb, 'video_note')
                self.gc.save_config(self.gc.config)
                await kb.toggle_forward_setting_button(self.gc.config)
            except ValueError:
                await callback_query.message.reply_text('⚠️⚠️⚠️至少需要选择一个转发类型⚠️⚠️⚠️')
            except Exception as e:
                await callback_query.message.reply_text(
                    '转发设置失败\n(具体原因请前往终端查看报错信息)')
                log.error(f'转发设置失败,{_t(KeyWord.REASON)}:"{e}"')
        elif callback_data == BotCallbackText.REMOVE_LISTEN_FORWARD or callback_data.startswith(
                BotCallbackText.REMOVE_LISTEN_DOWNLOAD):
            if callback_data.startswith(BotCallbackText.REMOVE_LISTEN_DOWNLOAD):
                args: list = callback_data.split()
                link: str = args[1]
                self.app.client.remove_handler(self._downloader.listen_download_chat.get(link))
                self._downloader.listen_download_chat.pop(link)
                watch_id = self._downloader.download_watch_id(link)
                self._downloader.web_watch_handler_clients.pop(watch_id, None)
                self._downloader.web_pending_watches.pop(watch_id, None)
                if self.transfer_store:
                    self.transfer_store.delete_live_transfer_watch(watch_id)
                await callback_query.message.edit_text(link)
                await callback_query.message.edit_reply_markup(
                    KeyboardButton.single_button(text=BotButton.ALREADY_REMOVE, callback_data=BotCallbackText.NULL)
                )
                p = f'已删除监听下载,频道链接:"{link}"。'
                console.log(p, style='#FF4689')
                log.info(f'{p}当前的监听下载信息:{self._downloader.listen_download_chat}')
                return None
            if not isinstance(self._downloader.cd.data, dict):
                return None
            meta: Union[dict, None] = self._downloader.cd.data.copy()
            self._downloader.cd.data = None
            link: str = meta.get('link')
            self.app.client.remove_handler(self._downloader.listen_forward_chat.get(link))
            self._downloader.listen_forward_chat.pop(link)
            watch_id = self._downloader.forward_watch_id(link)
            self._downloader.web_watch_handler_clients.pop(watch_id, None)
            self._downloader.web_pending_watches.pop(watch_id, None)
            if self.transfer_store:
                self.transfer_store.delete_live_transfer_watch(watch_id)
            rule = parse_forward_watch_rule(link)
            m: list = [rule.get('source_link'), rule.get('target_link')]
            display_rule = ' -> '.join(m)
            include_text = ',包含评论区' if rule.get('include_comment') else ''
            p = f'已删除监听转发,转发规则:"{display_rule}{include_text}"。'
            await callback_query.message.edit_text(
                f'{" ➡️ ".join(m)}{" 👥" if rule.get("include_comment") else ""}'
            )
            await callback_query.message.edit_reply_markup(
                KeyboardButton.single_button(text=BotButton.ALREADY_REMOVE, callback_data=BotCallbackText.NULL)
            )
            console.log(p, style='#FF4689')
            log.info(f'{p}当前的监听转发信息:{self._downloader.listen_forward_chat}')
        elif callback_data in (
                BotCallbackText.DOWNLOAD_CHAT_FILTER,  # 主页面。
                BotCallbackText.DOWNLOAD_CHAT_DATE_FILTER,  # 下载日期范围设置页面。
                BotCallbackText.DOWNLOAD_CHAT_DTYPE_FILTER,  # 下载类型设置页面。
                BotCallbackText.DOWNLOAD_CHAT_KEYWORD_FILTER,  # 关键词过滤设置页面。
                BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO,
                BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_PHOTO,
                BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_AUDIO,
                BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VOICE,
                BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_ANIMATION,
                BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_DOCUMENT,
                BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO_NOTE,
                BotCallbackText.TOGGLE_DOWNLOAD_CHAT_COMMENT,
                BotCallbackText.DOWNLOAD_CHAT_ID,  # 执行任务。
                BotCallbackText.DOWNLOAD_CHAT_ID_CANCEL,  # 取消任务。
                BotCallbackText.FILTER_START_DATE,  # 设置下载起始日期。
                BotCallbackText.FILTER_END_DATE,  # 设置下载结束日期。
                BotCallbackText.CONFIRM_KEYWORD,  # 确认设置关键词。
                BotCallbackText.CANCEL_KEYWORD_INPUT  # 取消设置关键词。
        ) or callback_data.startswith(
            (
                    'time_inc_',
                    'time_dec_',
                    'set_time_',
                    'set_specific_time_',
                    'adjust_step_',
                    'drop_keyword_',  # 移除特定关键词。
                    'ignore_keyword'  # 忽略特定关键词。
            )  # 切换月份,选择日期。
        ):
            chat_id = BotCallbackText.DOWNLOAD_CHAT_ID

            if callback_data in (BotCallbackText.DOWNLOAD_CHAT_ID, BotCallbackText.DOWNLOAD_CHAT_ID_CANCEL):  # 执行或取消任务。
                BotCallbackText.DOWNLOAD_CHAT_ID = 'download_chat_id'
                self._downloader.adding_keywords.clear()
                self._downloader.add_keyword_mode_handler(
                    chat_id=chat_id,
                    callback_query=callback_query,
                    callback_prompt=partial(self._filter_prompt, chat_id=chat_id),
                    enable=False
                )  # 关闭关键词输入handler。
                if callback_data == chat_id:
                    await self._downloader.download_chat(chat_id=chat_id, callback_query=callback_query)
                    self._remove_chat_id(chat_id)
                elif callback_data == BotCallbackText.DOWNLOAD_CHAT_ID_CANCEL:
                    self._remove_chat_id(chat_id)
                    await callback_query.message.edit_text(
                        text=callback_query.message.text,
                        reply_markup=kb.single_button(
                            text=BotButton.TASK_CANCEL,
                            callback_data=BotCallbackText.NULL
                        )
                    )
            elif callback_data in (
                    BotCallbackText.DOWNLOAD_CHAT_FILTER,
                    BotCallbackText.DOWNLOAD_CHAT_DATE_FILTER
            ):
                if callback_data == BotCallbackText.DOWNLOAD_CHAT_DATE_FILTER:
                    start_time, end_time = self._get_update_time(chat_id)
                    if not await self._verification_time(callback_query, start_time, end_time):
                        return None
                # 返回或点击。
                await callback_query.message.edit_text(
                    text=self._filter_prompt(chat_id),
                    reply_markup=kb.download_chat_filter_button(
                        self._downloader.download_chat_filter[chat_id][
                            'comment']) if callback_data == BotCallbackText.DOWNLOAD_CHAT_FILTER else kb.filter_date_range_button()
                )
            elif callback_data in (BotCallbackText.FILTER_START_DATE, BotCallbackText.FILTER_END_DATE):
                dtype = None
                p_s_d = ''
                if callback_data == BotCallbackText.FILTER_START_DATE:
                    dtype = CalenderKeyboard.START_TIME_BUTTON
                    p_s_d = '起始'
                elif callback_data == BotCallbackText.FILTER_END_DATE:
                    dtype = CalenderKeyboard.END_TIME_BUTTON
                    p_s_d = '结束'
                await callback_query.message.edit_text(
                    text=f'📅选择{p_s_d}日期:\n{self._filter_prompt(chat_id)}'
                )
                await kb.calendar_keyboard(dtype=dtype)
            elif callback_data.startswith('adjust_step_'):
                # 获取当前步进值
                parts = callback_data.split('_')
                dtype = parts[-2]
                current_step = int(parts[-1])
                step_sequence = [1, 2, 5, 10, 15, 20]
                current_index = step_sequence.index(current_step)
                next_index = (current_index + 1) % len(step_sequence)
                new_step = step_sequence[next_index]
                self._downloader.download_chat_filter[chat_id]['date_range']['adjust_step'] = new_step
                current_date = datetime.datetime.fromtimestamp(
                    self._downloader.download_chat_filter[chat_id]['date_range'][f'{dtype}_date']
                ).strftime('%Y-%m-%d %H:%M:%S')
                await callback_query.message.edit_reply_markup(
                    reply_markup=kb.time_keyboard(
                        dtype=dtype,
                        date=current_date,
                        adjust_step=new_step
                    )
                )
            elif callback_data.startswith(('time_inc_', 'time_dec_')):
                parts = callback_data.split('_')
                dtype = None
                if 'start' in callback_data:
                    dtype = CalenderKeyboard.START_TIME_BUTTON
                elif 'end' in callback_data:
                    dtype = CalenderKeyboard.END_TIME_BUTTON

                if 'month' in callback_data:
                    year = int(parts[-2])
                    month = int(parts[-1])
                    await kb.calendar_keyboard(year=year, month=month, dtype=dtype)
                    log.info(f'日期切换为{year}年,{month}月。')

            elif callback_data.startswith(('set_time_', 'set_specific_time_')):
                parts = callback_data.split('_')
                date = parts[-1]
                dtype = parts[-2]
                date_type = ''
                p_s_d = ''
                timestamp = datetime.datetime.timestamp(datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S'))
                if 'start' in callback_data:
                    date_type = 'start_date'
                    p_s_d = '起始'
                elif 'end' in callback_data:
                    date_type = 'end_date'
                    p_s_d = '结束'
                self._downloader.download_chat_filter[chat_id]['date_range'][date_type] = timestamp
                await callback_query.message.edit_text(
                    text=f'📅选择{p_s_d}日期:\n{self._filter_prompt(chat_id)}',
                    reply_markup=kb.time_keyboard(
                        dtype=dtype,
                        date=date,
                        adjust_step=self._downloader.download_chat_filter[chat_id]['date_range']['adjust_step']
                    )
                )
                log.info(f'日期设置,起始日期:{self._get_update_time(chat_id)[0]},结束日期:{self._get_update_time(chat_id)[1]}。')
            elif callback_data.startswith(('drop_keyword_', 'ignore_keyword')):
                if callback_data.startswith('drop_keyword_'):
                    parts = callback_data.split('_')
                    keyword = parts[-1]
                    _keyword = self._downloader.download_chat_filter.get(chat_id, {}).get('keyword', {})
                    _keyword.pop(keyword)
                    self._downloader.adding_keywords.remove(keyword)
                await callback_query.message.edit_text(
                    text=self._filter_prompt(chat_id),
                    reply_markup=KeyboardButton.keyword_filter_button(self._downloader.adding_keywords)
                )

            elif callback_data in (
                    BotCallbackText.DOWNLOAD_CHAT_DTYPE_FILTER,
                    BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO,
                    BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_PHOTO,
                    BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_AUDIO,
                    BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VOICE,
                    BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_ANIMATION,
                    BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_DOCUMENT,
                    BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO_NOTE
            ):
                try:
                    if callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO:
                        self._toggle_dtype_filter_button(chat_id, 'video')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_PHOTO:
                        self._toggle_dtype_filter_button(chat_id, 'photo')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_AUDIO:
                        self._toggle_dtype_filter_button(chat_id, 'audio')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VOICE:
                        self._toggle_dtype_filter_button(chat_id, 'voice')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_ANIMATION:
                        self._toggle_dtype_filter_button(chat_id, 'animation')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_DOCUMENT:
                        self._toggle_dtype_filter_button(chat_id, 'document')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO_NOTE:
                        self._toggle_dtype_filter_button(chat_id, 'video_note')
                    await callback_query.message.edit_text(
                        text=self._filter_prompt(chat_id),
                        reply_markup=kb.toggle_download_chat_type_filter_button(self._downloader.download_chat_filter)
                    )
                except ValueError:
                    await callback_query.message.reply_text('⚠️⚠️⚠️至少需要选择一个下载类型⚠️⚠️⚠️')
                except Exception as e:
                    await callback_query.message.reply_text(
                        '下载类型设置失败\n(具体原因请前往终端查看报错信息)')
                    log.error(f'下载类型设置失败,{_t(KeyWord.REASON)}:"{e}"', exc_info=True)
            elif callback_data in (
                    BotCallbackText.DOWNLOAD_CHAT_KEYWORD_FILTER,
                    BotCallbackText.CONFIRM_KEYWORD,
                    BotCallbackText.CANCEL_KEYWORD_INPUT
            ):
                if callback_data == BotCallbackText.DOWNLOAD_CHAT_KEYWORD_FILTER:
                    try:
                        await callback_query.message.edit_text(
                            text=self._filter_prompt(chat_id),
                            reply_markup=kb.keyword_filter_button(self._downloader.adding_keywords)
                        )
                    except MessageNotModified:
                        pass
                    self._downloader.add_keyword_mode_handler(
                        enable=True,
                        chat_id=chat_id,
                        callback_query=callback_query,
                        callback_prompt=partial(self._filter_prompt, chat_id=chat_id)
                    )  # 进入添加关键词模式。
                elif callback_data == BotCallbackText.CONFIRM_KEYWORD:
                    self._downloader.add_keyword_mode_handler(
                        enable=False,
                        chat_id=chat_id,
                        callback_query=callback_query,
                        callback_prompt=partial(self._filter_prompt, chat_id=chat_id)
                    )
                    await callback_query.message.edit_text(
                        text=self._filter_prompt(chat_id),
                        reply_markup=kb.download_chat_filter_button(self._downloader.download_chat_filter[chat_id]['comment'])
                    )
                elif callback_data == BotCallbackText.CANCEL_KEYWORD_INPUT:
                    self._downloader.adding_keywords.clear()
                    self._downloader.add_keyword_mode_handler(
                        enable=False,
                        chat_id=chat_id,
                        callback_query=callback_query,
                        callback_prompt=partial(self._filter_prompt, chat_id=chat_id)
                    )
                    self._downloader.download_chat_filter[chat_id]['keyword'] = {}
                    await callback_query.message.edit_text(
                        text=self._filter_prompt(chat_id),
                        reply_markup=kb.download_chat_filter_button(self._downloader.download_chat_filter[chat_id]['comment'])
                    )
            elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_COMMENT:
                status: bool = self._downloader.download_chat_filter[chat_id]['comment']
                self._downloader.download_chat_filter[chat_id]['comment'] = not status
                await callback_query.message.edit_text(
                    text=self._filter_prompt(chat_id),
                    reply_markup=kb.download_chat_filter_button(self._downloader.download_chat_filter[chat_id]['comment'])
                )
