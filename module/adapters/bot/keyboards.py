# coding=UTF-8
"""Bot 的回复键盘与回调数据构造。

从 ``bot.py`` **逐字搬移**：`KeyboardButton`（17 个键盘构造器，约 700 行）与
`CallbackData` 只依赖 pyrogram 的键盘类型、枚举与少量工具函数，与 `Bot` 的
命令处理逻辑无关。分开后 ``bot.py`` 只留命令/消息处理。

``bot.py`` 会 import 回来，因此既有 ``from module.adapters.bot.bot import KeyboardButton``
写法仍然可用；新代码请直接从本模块导入。
"""
from __future__ import annotations

import calendar
import datetime
from typing import Optional, Union

import pyrogram
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified
from pyrogram.types.bots_and_keyboards import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from module import log
from module.core.enums import (
    BotButton,
    BotCallbackText,
    CalenderKeyboard,
    DownloadType,
    KeyWord,
)
from module.utils.language import _t


class KeyboardButton:
    def __init__(self, callback_query: pyrogram.types.CallbackQuery):
        self.callback_query = callback_query

    async def choice_export_table_button(
            self,
            choice: Union[BotCallbackText, str]
    ) -> None:
        export_callback_data: str = ''
        if choice == BotCallbackText.EXPORT_LINK_TABLE:
            export_callback_data = BotCallbackText.EXPORT_LINK_TABLE
        elif choice == BotCallbackText.EXPORT_COUNT_TABLE:
            export_callback_data = BotCallbackText.EXPORT_COUNT_TABLE
        elif choice == BotCallbackText.EXPORT_UPLOAD_TABLE:
            export_callback_data = BotCallbackText.EXPORT_UPLOAD_TABLE
        try:
            await self.callback_query.message.edit_reply_markup(InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=BotButton.EXPORT_TABLE,
                            callback_data=export_callback_data
                        ),
                        InlineKeyboardButton(
                            text=BotButton.RESELECT,
                            callback_data=BotCallbackText.BACK_TABLE
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=BotButton.HELP_PAGE,
                            callback_data=BotCallbackText.BACK_HELP
                        )
                    ]
                ]
            )
            )
        except MessageNotModified:
            pass

    async def toggle_setting_button(
            self,
            global_config: dict,
            user_config: dict
    ) -> None:
        try:
            await self.callback_query.message.edit_reply_markup(
                InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            text=BotButton.CLOSE_NOTICE if global_config.get(
                                BotCallbackText.NOTICE) else BotButton.OPEN_NOTICE,
                            callback_data=BotCallbackText.NOTICE
                        ),
                        InlineKeyboardButton(
                            text=BotButton.EXPORT_TABLE,
                            callback_data=BotCallbackText.EXPORT_TABLE
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=BotButton.CLOSE_EXIT_SHUTDOWN if user_config.get(
                                'is_shutdown') else BotButton.OPEN_EXIT_SHUTDOWN,
                            callback_data=BotCallbackText.SHUTDOWN
                        ),
                        InlineKeyboardButton(
                            text=BotButton.FORWARD_SETTING,
                            callback_data=BotCallbackText.FORWARD_SETTING
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=BotButton.DOWNLOAD_SETTING,
                            callback_data=BotCallbackText.DOWNLOAD_SETTING
                        ),
                        InlineKeyboardButton(
                            text=BotButton.UPLOAD_SETTING,
                            callback_data=BotCallbackText.UPLOAD_SETTING
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=BotButton.HELP_PAGE,
                            callback_data=BotCallbackText.BACK_HELP
                        )
                    ]
                ])
            )
        except MessageNotModified:
            pass
        except Exception as e:
            await self.callback_query.message.reply_text('切换按钮状态失败\n(具体原因请前往终端查看报错信息)')
            log.error(f'切换按钮状态失败,{_t(KeyWord.REASON)}:"{e}"')

    async def toggle_upload_setting_button(
            self,
            global_config: dict
    ):
        upload_config = global_config.get('upload', {})
        try:
            pending_limit = int(upload_config.get('pending_limit', 3))
        except (TypeError, ValueError):
            pending_limit = 3
        pending_limit = min(max(pending_limit, 1), 5)
        pending_limit_buttons = [
            InlineKeyboardButton(
                text=f'队列{i}{" ✅" if pending_limit == i else ""}',
                callback_data=f'{BotCallbackText.UPLOAD_PENDING_LIMIT}:{i}'
            )
            for i in range(1, 6)
        ]
        try:
            await self.callback_query.message.edit_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=BotButton.CLOSE_UPLOAD_DOWNLOAD if global_config.get('upload').get(
                                    'download_upload') else BotButton.OPEN_UPLOAD_DOWNLOAD,
                                callback_data=BotCallbackText.UPLOAD_DOWNLOAD
                            ),
                            InlineKeyboardButton(
                                text=BotButton.CLOSE_UPLOAD_DOWNLOAD_DELETE if global_config.get('upload').get(
                                    'delete') else BotButton.OPEN_UPLOAD_DOWNLOAD_DELETE,
                                callback_data=BotCallbackText.UPLOAD_DOWNLOAD_DELETE
                            )
                        ],
                        pending_limit_buttons,
                        [
                            InlineKeyboardButton(
                                text=BotButton.RETURN,
                                callback_data=BotCallbackText.SETTING
                            )
                        ]
                    ]
                )
            )
        except MessageNotModified:
            pass

    async def toggle_download_setting_button(
            self,
            user_config: dict
    ):
        try:
            await self.callback_query.message.edit_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=BotButton.VIDEO_ON if DownloadType.VIDEO in user_config.get(
                                    'download_type') else BotButton.VIDEO_OFF,
                                callback_data=BotCallbackText.TOGGLE_DOWNLOAD_VIDEO
                            ),
                            InlineKeyboardButton(
                                text=BotButton.PHOTO_ON if DownloadType.PHOTO in user_config.get(
                                    'download_type') else BotButton.PHOTO_OFF,
                                callback_data=BotCallbackText.TOGGLE_DOWNLOAD_PHOTO
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.AUDIO_ON if DownloadType.AUDIO in user_config.get(
                                    'download_type') else BotButton.AUDIO_OFF,
                                callback_data=BotCallbackText.TOGGLE_DOWNLOAD_AUDIO
                            ),
                            InlineKeyboardButton(
                                text=BotButton.VOICE_ON if DownloadType.VOICE in user_config.get(
                                    'download_type') else BotButton.VOICE_OFF,
                                callback_data=BotCallbackText.TOGGLE_DOWNLOAD_VOICE
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.ANIMATION_ON if DownloadType.ANIMATION in user_config.get(
                                    'download_type') else BotButton.ANIMATION_OFF,
                                callback_data=BotCallbackText.TOGGLE_DOWNLOAD_ANIMATION
                            ),
                            InlineKeyboardButton(
                                text=BotButton.DOCUMENT_ON if DownloadType.DOCUMENT in user_config.get(
                                    'download_type') else BotButton.DOCUMENT_OFF,
                                callback_data=BotCallbackText.TOGGLE_DOWNLOAD_DOCUMENT
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.VIDEO_NOTE_ON if DownloadType.VIDEO_NOTE in user_config.get(
                                    'download_type') else BotButton.VIDEO_NOTE_OFF,
                                callback_data=BotCallbackText.TOGGLE_DOWNLOAD_VIDEO_NOTE
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.RETURN,
                                callback_data=BotCallbackText.SETTING
                            )
                        ]
                    ]
                )
            )
        except MessageNotModified:
            pass

    async def toggle_forward_setting_button(
            self,
            global_config: dict
    ):
        try:
            await self.callback_query.message.edit_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=BotButton.VIDEO_ON if global_config.get('forward_type').get(
                                    'video') else BotButton.VIDEO_OFF,
                                callback_data=BotCallbackText.TOGGLE_FORWARD_VIDEO
                            ),
                            InlineKeyboardButton(
                                text=BotButton.PHOTO_ON if global_config.get('forward_type').get(
                                    'photo') else BotButton.PHOTO_OFF,
                                callback_data=BotCallbackText.TOGGLE_FORWARD_PHOTO
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.AUDIO_ON if global_config.get('forward_type').get(
                                    'audio') else BotButton.AUDIO_OFF,
                                callback_data=BotCallbackText.TOGGLE_FORWARD_AUDIO
                            ),
                            InlineKeyboardButton(
                                text=BotButton.VOICE_ON if global_config.get('forward_type').get(
                                    'voice') else BotButton.VOICE_OFF,
                                callback_data=BotCallbackText.TOGGLE_FORWARD_VOICE
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.ANIMATION_ON if global_config.get('forward_type').get(
                                    'animation') else BotButton.ANIMATION_OFF,
                                callback_data=BotCallbackText.TOGGLE_FORWARD_ANIMATION
                            ),
                            InlineKeyboardButton(
                                text=BotButton.DOCUMENT_ON if global_config.get('forward_type').get(
                                    'document') else BotButton.DOCUMENT_OFF,
                                callback_data=BotCallbackText.TOGGLE_FORWARD_DOCUMENT
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.TEXT_ON if global_config.get('forward_type').get(
                                    'text') else BotButton.TEXT_OFF,
                                callback_data=BotCallbackText.TOGGLE_FORWARD_TEXT
                            ),
                            InlineKeyboardButton(
                                text=BotButton.VIDEO_NOTE_ON if global_config.get('forward_type').get(
                                    'video_note') else BotButton.VIDEO_NOTE_OFF,
                                callback_data=BotCallbackText.TOGGLE_FORWARD_VIDEO_NOTE
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.RETURN,
                                callback_data=BotCallbackText.SETTING
                            )
                        ]
                    ]
                )
            )
        except MessageNotModified:
            pass

    @staticmethod
    def toggle_download_chat_type_filter_button(
            download_chat_filter: dict
    ):
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=BotButton.VIDEO_ON if
                        download_chat_filter[BotCallbackText.DOWNLOAD_CHAT_ID]['download_type'][
                            DownloadType.VIDEO] else BotButton.VIDEO_OFF,
                        callback_data=BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO
                    ),
                    InlineKeyboardButton(
                        text=BotButton.PHOTO_ON if
                        download_chat_filter[BotCallbackText.DOWNLOAD_CHAT_ID]['download_type'][
                            DownloadType.PHOTO] else BotButton.PHOTO_OFF,
                        callback_data=BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_PHOTO
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=BotButton.AUDIO_ON if
                        download_chat_filter[BotCallbackText.DOWNLOAD_CHAT_ID]['download_type'][
                            DownloadType.AUDIO] else BotButton.AUDIO_OFF,
                        callback_data=BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_AUDIO
                    ),
                    InlineKeyboardButton(
                        text=BotButton.VOICE_ON if
                        download_chat_filter[BotCallbackText.DOWNLOAD_CHAT_ID]['download_type'][
                            DownloadType.VOICE] else BotButton.VOICE_OFF,
                        callback_data=BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VOICE
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=BotButton.ANIMATION_ON if
                        download_chat_filter[BotCallbackText.DOWNLOAD_CHAT_ID]['download_type'][
                            DownloadType.ANIMATION] else BotButton.ANIMATION_OFF,
                        callback_data=BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_ANIMATION
                    ),
                    InlineKeyboardButton(
                        text=BotButton.DOCUMENT_ON if
                        download_chat_filter[BotCallbackText.DOWNLOAD_CHAT_ID]['download_type'][
                            DownloadType.DOCUMENT] else BotButton.DOCUMENT_OFF,
                        callback_data=BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_DOCUMENT
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=BotButton.VIDEO_NOTE_ON if
                        download_chat_filter[BotCallbackText.DOWNLOAD_CHAT_ID]['download_type'][
                            DownloadType.VIDEO_NOTE] else BotButton.VIDEO_NOTE_OFF,
                        callback_data=BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO_NOTE
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=BotButton.RETURN,
                        callback_data=BotCallbackText.DOWNLOAD_CHAT_FILTER
                    )
                ]
            ]
        )

    async def toggle_table_button(
            self,
            config: dict,
            choice: Union[str, None] = None
    ) -> None:
        try:
            await self.callback_query.message.edit_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=BotButton.CLOSE_LINK_TABLE if config.get(
                                    'export_table').get('link') else BotButton.OPEN_LINK_TABLE,
                                callback_data=BotCallbackText.TOGGLE_LINK_TABLE
                            ),
                            InlineKeyboardButton(
                                text=BotButton.CLOSE_COUNT_TABLE if config.get(
                                    'export_table').get('count') else BotButton.OPEN_COUNT_TABLE,
                                callback_data=BotCallbackText.TOGGLE_COUNT_TABLE
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.CLOSE_UPLOAD_TABLE if config.get(
                                    'export_table').get('upload') else BotButton.OPEN_UPLOAD_TABLE,
                                callback_data=BotCallbackText.TOGGLE_UPLOAD_TABLE
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.RETURN,
                                callback_data=BotCallbackText.SETTING
                            )
                        ]
                    ]
                )
            )
        except MessageNotModified:
            pass
        except Exception as _e:
            if choice:
                if choice == 'link':
                    prompt: str = '链接'
                elif choice == 'count':
                    prompt: str = '计数'
                elif choice == 'upload':
                    prompt: str = '上传'
                else:
                    prompt: str = ''
                await self.callback_query.message.reply_text(
                    f'设置启用或禁用导出{prompt}统计表失败\n(具体原因请前往终端查看报错信息)'
                )
                log.error(f'设置启用或禁用导出{prompt}统计表失败,{_t(KeyWord.REASON)}:"{_e}"')
            else:
                log.error(f'设置启用或禁用导出统计表失败,{_t(KeyWord.REASON)}:"{_e}"')

    async def back_table_button(self):
        try:
            await self.callback_query.message.edit_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=BotButton.RESELECT,
                                callback_data=BotCallbackText.BACK_TABLE
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text=BotButton.HELP_PAGE,
                                callback_data=BotCallbackText.BACK_HELP
                            )
                        ]
                    ]
                ))
        except MessageNotModified:
            pass

    async def task_assign_button(self):
        try:
            await self.callback_query.message.edit_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text=BotButton.TASK_ASSIGN,
                                callback_data=BotCallbackText.NULL
                            )
                        ]
                    ]
                )
            )
        except MessageNotModified:
            pass

    @staticmethod
    def restrict_forward_button():
        return (
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            BotButton.DOWNLOAD,
                            callback_data=BotCallbackText.DOWNLOAD
                        ),
                        InlineKeyboardButton(
                            BotButton.DOWNLOAD_UPLOAD,
                            callback_data=BotCallbackText.DOWNLOAD_UPLOAD
                        ),
                    ]
                ]
            )
        )

    @staticmethod
    def single_button(text: str, callback_data: str):
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=text,
                        callback_data=callback_data
                    )
                ]
            ]
        )

    @staticmethod
    def download_chat_filter_button(
            include_comment: bool
    ):
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=BotButton.DATE_RANGE_SETTING,
                        callback_data=BotCallbackText.DOWNLOAD_CHAT_DATE_FILTER
                    ),
                    InlineKeyboardButton(
                        text=BotButton.DOWNLOAD_DTYPE_SETTING,
                        callback_data=BotCallbackText.DOWNLOAD_CHAT_DTYPE_FILTER
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=BotButton.KEYWORD_FILTER_SETTING,
                        callback_data=BotCallbackText.DOWNLOAD_CHAT_KEYWORD_FILTER
                    ),
                    InlineKeyboardButton(
                        text=BotButton.INCLUDE_COMMENT if include_comment else BotButton.IGNORE_COMMENT,
                        callback_data=BotCallbackText.TOGGLE_DOWNLOAD_CHAT_COMMENT
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=BotButton.EXECUTE_TASK,
                        callback_data=BotCallbackText.DOWNLOAD_CHAT_ID
                    ),
                    InlineKeyboardButton(
                        text=BotButton.CANCEL_TASK,
                        callback_data=BotCallbackText.DOWNLOAD_CHAT_ID_CANCEL
                    )
                ]
            ]
        )

    @staticmethod
    def filter_date_range_button():
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=BotButton.SELECT_START_DATE,
                        callback_data=BotCallbackText.FILTER_START_DATE
                    ),
                    InlineKeyboardButton(
                        text=BotButton.SELECT_END_DATE,
                        callback_data=BotCallbackText.FILTER_END_DATE
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=BotButton.RETURN,
                        callback_data=BotCallbackText.DOWNLOAD_CHAT_FILTER
                    )
                ]
            ]
        )

    async def calendar_keyboard(
            self,
            dtype: Union[CalenderKeyboard, str],
            year: Optional[int] = datetime.datetime.now().year,
            month: Optional[int] = datetime.datetime.now().month
    ):
        keyboard: list = []
        prev_month: int = month - 1 if month > 1 else 12
        prev_year: int = year if month > 1 else year - 1
        next_month: int = month + 1 if month < 12 else 1
        next_year: int = year if month < 12 else year + 1
        if dtype == CalenderKeyboard.START_TIME_BUTTON:
            _dtype = 'start'
        elif dtype == CalenderKeyboard.END_TIME_BUTTON:
            _dtype = 'end'
        else:
            return None
        nav_row = [
            InlineKeyboardButton('◀️', callback_data=f'time_dec_month_{_dtype}_{prev_year}_{prev_month}'),
            InlineKeyboardButton(f'{year}-{month:02d}', callback_data=BotCallbackText.NULL),
            InlineKeyboardButton('▶️', callback_data=f'time_inc_month_{_dtype}_{next_year}_{next_month}')
        ]
        keyboard.append(nav_row)

        week_days = ['一', '二', '三', '四', '五', '六', '日']
        week_row = [InlineKeyboardButton(day, callback_data=BotCallbackText.NULL) for day in week_days]
        keyboard.append(week_row)

        cal = calendar.monthcalendar(year, month)
        for week in cal:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(' ', callback_data=BotCallbackText.NULL))
                else:
                    date_str = f'{year}-{month:02d}-{day:02d} 00:00:00'
                    row.append(InlineKeyboardButton(str(day), callback_data=f'set_specific_time_{_dtype}_{date_str}'))
            keyboard.append(row)

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=BotButton.CONFIRM_AND_RETURN,
                    callback_data=BotCallbackText.DOWNLOAD_CHAT_DATE_FILTER
                ),
                InlineKeyboardButton(
                    text=BotButton.CANCEL_TASK,
                    callback_data=BotCallbackText.DOWNLOAD_CHAT_ID_CANCEL
                )
            ]
        )
        try:
            await self.callback_query.message.edit_reply_markup(InlineKeyboardMarkup(keyboard))
        except MessageNotModified:
            pass

    @staticmethod
    def time_keyboard(
            dtype: Union[CalenderKeyboard, str],
            date: str,
            adjust_step: Optional[int] = 1
    ):
        dt = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        _dtype = dtype if isinstance(dtype, str) else 'start' if dtype == CalenderKeyboard.START_TIME_BUTTON else 'end'
        hour, minute, second = 'hour', 'minute', 'second'

        def _get_updated_time(field: str, delta: int) -> str:
            new_dt = dt.replace(
                hour=(dt.hour + delta) % 24 if field == hour else dt.hour,
                minute=(dt.minute + delta) % 60 if field == minute else dt.minute,
                second=(dt.second + delta) % 60 if field == second else dt.second
            )
            return new_dt.strftime('%Y-%m-%d %H:%M:%S')

        time_keyboard = [
            [
                InlineKeyboardButton(
                    text=f'步进值:{adjust_step}',
                    callback_data=f'adjust_step_{dtype}_{adjust_step}'
                )
            ],
            [
                InlineKeyboardButton(
                    text='◀️',
                    callback_data=f'set_time_{_dtype}_{_get_updated_time(hour, -adjust_step)}'
                ),
                InlineKeyboardButton(
                    text='时', callback_data=BotCallbackText.NULL
                ),
                InlineKeyboardButton(
                    text='▶️',
                    callback_data=f'set_time_{_dtype}_{_get_updated_time(hour, adjust_step)}'
                )
            ],
            [
                InlineKeyboardButton(
                    text='◀️',
                    callback_data=f'set_time_{_dtype}_{_get_updated_time(minute, -adjust_step)}'
                ),
                InlineKeyboardButton(
                    text='分', callback_data=BotCallbackText.NULL
                ),
                InlineKeyboardButton(
                    text='▶️',
                    callback_data=f'set_time_{_dtype}_{_get_updated_time(minute, adjust_step)}'
                )
            ],
            [
                InlineKeyboardButton(
                    text='◀️',
                    callback_data=f'set_time_{_dtype}_{_get_updated_time(second, -adjust_step)}'
                ),
                InlineKeyboardButton(
                    text='秒', callback_data=BotCallbackText.NULL
                ),
                InlineKeyboardButton(
                    text='▶️',
                    callback_data=f'set_time_{_dtype}_{_get_updated_time(second, adjust_step)}'
                )
            ],
            [
                InlineKeyboardButton(
                    text=BotButton.CONFIRM_AND_RETURN,
                    callback_data=BotCallbackText.DOWNLOAD_CHAT_DATE_FILTER
                ),
                InlineKeyboardButton(
                    text=BotButton.CANCEL_TASK,
                    callback_data=BotCallbackText.DOWNLOAD_CHAT_ID_CANCEL
                )
            ]
        ]

        return InlineKeyboardMarkup(time_keyboard)

    @staticmethod
    def keyword_filter_button(
            adding_keywords: Optional[list] = None
    ):
        """关键词过滤设置按钮。"""
        if adding_keywords:
            keyword_buttons = [
                [
                    InlineKeyboardButton(
                        text=BotButton.INPUT_KEYWORD,
                        callback_data=BotCallbackText.NULL
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=BotButton.CONFIRM_KEYWORD,
                        callback_data=BotCallbackText.CONFIRM_KEYWORD
                    ),
                    InlineKeyboardButton(
                        text=BotButton.CANCEL,
                        callback_data=BotCallbackText.CANCEL_KEYWORD_INPUT
                    )
                ]
            ]
        else:
            keyword_buttons = [
                [
                    InlineKeyboardButton(
                        text=BotButton.INPUT_KEYWORD,
                        callback_data=BotCallbackText.NULL
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=BotButton.RETURN,
                        callback_data=BotCallbackText.CANCEL_KEYWORD_INPUT
                    )
                ]
            ]
        return InlineKeyboardMarkup(keyword_buttons)


class CallbackData:
    def __init__(self, data: Union[dict, None] = None):
        self.data: Union[dict, None] = data
