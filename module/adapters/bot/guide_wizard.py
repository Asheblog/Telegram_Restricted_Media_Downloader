# coding=UTF-8
"""Bot 傻瓜式分步引导向导。"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Callable, Optional, Union

import pyrogram
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.types.messages_and_media import ReplyParameters

from module import LINK_PREVIEW_OPTIONS
from module.core.enums import BotButton, BotCallbackText
from module.utils.telegram_links import (
    channels_match,  # noqa: F401  (re-exported for back-compat)
    extract_post_id,  # noqa: F401  (re-exported for back-compat)
    normalize_telegram_link,  # noqa: F401  (re-exported for back-compat)
    to_channel_root,
)

WIZARD_TIMEOUT_SECONDS = 600


class WizardCommand(StrEnum):
    DOWNLOAD = "download"
    FORWARD = "forward"
    LISTEN_DOWNLOAD = "listen_download"
    LISTEN_FORWARD = "listen_forward"
    DOWNLOAD_CHAT = "download_chat"


class WizardStep(StrEnum):
    SOURCE_CHANNEL = "source_channel"
    TARGET_CHANNEL = "target_channel"
    RANGE_DETECTED = "range_detected"
    START_MESSAGE_LINK = "start_message_link"
    END_MESSAGE_LINK = "end_message_link"
    INCLUDE_COMMENT = "include_comment"
    LISTEN_CHANNEL = "listen_channel"
    LISTEN_COLLECT = "listen_collect"
    CONFIRM = "confirm"


@dataclass
class GuideWizardSession:
    user_id: int
    command: WizardCommand
    step: WizardStep
    source_link: str = ""
    target_link: str = ""
    start_id: Optional[int] = None
    end_id: Optional[int] = None
    include_comment: bool = False
    listen_links: list[str] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)


def build_range_download_command(source_link: str, start_id: int, end_id: int) -> str:
    return f"/download {source_link.rstrip('/')} {int(start_id)} {int(end_id)}"


def build_forward_command(
    source_link: str,
    target_link: str,
    start_id: int,
    end_id: int,
    include_comment: bool = False,
) -> str:
    command = (
        f"/forward {source_link.rstrip('/')} {target_link.rstrip('/')} "
        f"{int(start_id)} {int(end_id)}"
    )
    if include_comment:
        command += " --include-comment"
    return command


def build_listen_download_command(links: list[str]) -> str:
    return "/listen_download " + " ".join(link.rstrip("/") for link in links)


def build_listen_forward_command(
    source_link: str,
    target_link: str,
    include_comment: bool = False,
) -> str:
    command = f"/listen_forward {source_link.rstrip('/')} {target_link.rstrip('/')}"
    if include_comment:
        command += " --include-comment"
    return command


def initial_step(command: WizardCommand) -> WizardStep:
    if command == WizardCommand.LISTEN_DOWNLOAD:
        return WizardStep.LISTEN_CHANNEL
    return WizardStep.SOURCE_CHANNEL


def _cancel_row() -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(
            BotButton.CANCEL, callback_data=BotCallbackText.GUIDE_WIZARD_CANCEL
        )
    ]


def _markup(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([*rows, _cancel_row()])


class BotGuideWizard:
    def __init__(self, bot, host_getter: Optional[Callable[[], object]] = None):
        self._bot = bot
        self._host_getter = host_getter
        self._sessions: dict[int, GuideWizardSession] = {}

    def _host(self):
        if self._host_getter:
            return self._host_getter()
        return getattr(self._bot, "downloader", None)

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [
            user_id
            for user_id, session in self._sessions.items()
            if now - session.updated_at > WIZARD_TIMEOUT_SECONDS
        ]
        for user_id in expired:
            self._sessions.pop(user_id, None)

    def has_active_session(self, user_id: int) -> bool:
        self._purge_expired()
        return user_id in self._sessions

    def get_session(self, user_id: int) -> Optional[GuideWizardSession]:
        self._purge_expired()
        return self._sessions.get(user_id)

    def _touch(self, session: GuideWizardSession) -> None:
        session.updated_at = time.time()

    def _set_session(self, session: GuideWizardSession) -> None:
        self._purge_expired()
        self._sessions[session.user_id] = session

    def can_start(self, user_id: int) -> tuple[bool, str]:
        self._purge_expired()
        if user_id in self._sessions:
            return False, "⚠️你已有进行中的引导任务，请先完成或发送 `/cancel` 取消。"
        if BotCallbackText.DOWNLOAD_CHAT_ID != "download_chat_id":
            return False, "⚠️请先完成或取消上一次「频道下载」过滤器设置。"
        return True, ""

    async def try_start(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        command: Union[str, WizardCommand],
    ) -> bool:
        user_id = message.from_user.id
        ok, reason = self.can_start(user_id)
        if not ok:
            await client.send_message(
                chat_id=user_id,
                reply_parameters=ReplyParameters(message_id=message.id),
                text=reason,
                link_preview_options=LINK_PREVIEW_OPTIONS,
            )
            return True
        wizard_command = WizardCommand(str(command))
        session = GuideWizardSession(
            user_id=user_id,
            command=wizard_command,
            step=initial_step(wizard_command),
        )
        self._set_session(session)
        await self._prompt_current_step(client, message, session)
        return True

    async def handle_cancel(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
    ) -> bool:
        user_id = message.from_user.id
        if not self.has_active_session(user_id):
            await client.send_message(
                chat_id=user_id,
                reply_parameters=ReplyParameters(message_id=message.id),
                text="ℹ️当前没有进行中的引导任务。",
                link_preview_options=LINK_PREVIEW_OPTIONS,
            )
            return True
        self._sessions.pop(user_id, None)
        await client.send_message(
            chat_id=user_id,
            reply_parameters=ReplyParameters(message_id=message.id),
            text="✅引导任务已取消。",
            link_preview_options=LINK_PREVIEW_OPTIONS,
        )
        return True

    async def handle_message(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
    ) -> bool:
        if not message.text or message.text.startswith("/"):
            return False
        session = self.get_session(message.from_user.id)
        if session is None:
            return False
        await self._consume_text(client, message, session)
        return True

    async def handle_callback(
        self,
        client: pyrogram.Client,
        callback_query: pyrogram.types.CallbackQuery,
    ) -> bool:
        data = callback_query.data
        if not isinstance(data, str) or not data.startswith("gw_"):
            return False
        await callback_query.answer()
        session = self.get_session(callback_query.from_user.id)
        if session is None:
            await callback_query.message.edit_text(
                "⚠️引导任务已结束或超时，请重新发送命令。"
            )
            return True
        message = callback_query.message
        if data == BotCallbackText.GUIDE_WIZARD_CANCEL:
            self._sessions.pop(session.user_id, None)
            await message.edit_text("✅引导任务已取消。", reply_markup=None)
            return True
        if data == BotCallbackText.GUIDE_WIZARD_CONFIRM_RANGE:
            if session.step != WizardStep.RANGE_DETECTED:
                return True
            session.step = WizardStep.CONFIRM
            self._touch(session)
            await self._prompt_current_step(client, message, session, edit=True)
            return True
        if data == BotCallbackText.GUIDE_WIZARD_CUSTOM_RANGE:
            session.step = WizardStep.START_MESSAGE_LINK
            self._touch(session)
            await self._prompt_current_step(client, message, session, edit=True)
            return True
        if data == BotCallbackText.GUIDE_WIZARD_ADD_LISTEN:
            session.step = WizardStep.LISTEN_CHANNEL
            self._touch(session)
            await self._prompt_current_step(client, message, session, edit=True)
            return True
        if data == BotCallbackText.GUIDE_WIZARD_FINISH_LISTEN:
            if not session.listen_links:
                await callback_query.answer("请先添加至少一个频道。", show_alert=True)
                return True
            await self._execute_listen_download(client, message, session)
            self._sessions.pop(session.user_id, None)
            return True
        if data == BotCallbackText.GUIDE_WIZARD_COMMENT_YES:
            session.include_comment = True
            session.step = WizardStep.CONFIRM
            self._touch(session)
            await self._prompt_current_step(client, message, session, edit=True)
            return True
        if data == BotCallbackText.GUIDE_WIZARD_COMMENT_NO:
            session.include_comment = False
            session.step = WizardStep.CONFIRM
            self._touch(session)
            await self._prompt_current_step(client, message, session, edit=True)
            return True
        if data == BotCallbackText.GUIDE_WIZARD_CONFIRM_EXECUTE:
            await self._execute_command(client, message, session)
            self._sessions.pop(session.user_id, None)
            return True
        return False

    async def _consume_text(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        session: GuideWizardSession,
    ) -> None:
        text = message.text.strip()
        if session.step == WizardStep.SOURCE_CHANNEL:
            channel = to_channel_root(text)
            if not channel:
                await self._reply_invalid_link(client, message, "频道")
                return
            session.source_link = channel
            self._touch(session)
            if session.command == WizardCommand.DOWNLOAD_CHAT:
                self._sessions.pop(session.user_id, None)
                await self._bot.begin_download_chat_setup(client, message, channel)
                return
            if session.command == WizardCommand.FORWARD:
                session.step = WizardStep.TARGET_CHANNEL
            elif session.command in (WizardCommand.LISTEN_FORWARD,):
                session.step = WizardStep.TARGET_CHANNEL
            else:
                await self._advance_after_source(client, message, session)
                return
            await self._prompt_current_step(client, message, session)
            return

        if session.step == WizardStep.TARGET_CHANNEL:
            channel = to_channel_root(text)
            if not channel:
                await self._reply_invalid_link(client, message, "频道")
                return
            session.target_link = channel
            self._touch(session)
            if session.command == WizardCommand.LISTEN_FORWARD:
                session.step = WizardStep.INCLUDE_COMMENT
            else:
                await self._advance_after_source(client, message, session)
                return
            await self._prompt_current_step(client, message, session)
            return

        if session.step == WizardStep.LISTEN_CHANNEL:
            channel = to_channel_root(text)
            if not channel:
                await self._reply_invalid_link(client, message, "频道")
                return
            if channel not in session.listen_links:
                session.listen_links.append(channel)
            session.step = WizardStep.LISTEN_COLLECT
            self._touch(session)
            await self._prompt_current_step(client, message, session)
            return

        if session.step == WizardStep.START_MESSAGE_LINK:
            post_id = extract_post_id(text)
            if post_id is None or not channels_match(session.source_link, text):
                await client.send_message(
                    chat_id=message.from_user.id,
                    reply_parameters=ReplyParameters(message_id=message.id),
                    text="❌请发送**起始消息**的「复制链接」，且须属于前面提供的频道。\n"
                    "操作：长按消息 → 复制链接",
                    link_preview_options=LINK_PREVIEW_OPTIONS,
                    reply_markup=_markup(),
                )
                return
            session.start_id = post_id
            session.step = WizardStep.END_MESSAGE_LINK
            self._touch(session)
            await self._prompt_current_step(client, message, session)
            return

        if session.step == WizardStep.END_MESSAGE_LINK:
            post_id = extract_post_id(text)
            if post_id is None or not channels_match(session.source_link, text):
                await client.send_message(
                    chat_id=message.from_user.id,
                    reply_parameters=ReplyParameters(message_id=message.id),
                    text="❌请发送**结束/最新消息**的「复制链接」，且须属于前面提供的频道。\n"
                    "操作：长按消息 → 复制链接",
                    link_preview_options=LINK_PREVIEW_OPTIONS,
                    reply_markup=_markup(),
                )
                return
            session.end_id = post_id
            if session.start_id is not None and session.end_id < session.start_id:
                await client.send_message(
                    chat_id=message.from_user.id,
                    reply_parameters=ReplyParameters(message_id=message.id),
                    text="❌结束消息 ID 不能小于起始消息 ID，请重新发送结束消息链接。",
                    link_preview_options=LINK_PREVIEW_OPTIONS,
                    reply_markup=_markup(),
                )
                session.step = WizardStep.END_MESSAGE_LINK
                return
            if session.command == WizardCommand.FORWARD:
                session.step = WizardStep.INCLUDE_COMMENT
            else:
                session.step = WizardStep.CONFIRM
            self._touch(session)
            await self._prompt_current_step(client, message, session)
            return

    async def _advance_after_source(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        session: GuideWizardSession,
    ) -> None:
        detected = await self._detect_range(session.source_link)
        if detected:
            session.start_id = int(detected["start_id"])
            session.end_id = int(detected["end_id"])
            session.step = WizardStep.RANGE_DETECTED
            self._touch(session)
            await self._prompt_current_step(client, message, session)
            return
        session.step = WizardStep.START_MESSAGE_LINK
        self._touch(session)
        await self._prompt_current_step(client, message, session)

    async def _detect_range(self, source_link: str) -> Optional[dict]:
        host = self._host()
        if host is None:
            return None
        detect_async = getattr(host, "detect_transfer_range_async", None)
        if callable(detect_async):
            try:
                return await detect_async(source_link)
            except Exception:
                return None
        detect_sync = getattr(host, "detect_transfer_range", None)
        if callable(detect_sync):
            try:
                return detect_sync(source_link)
            except Exception:
                return None
        return None

    async def _prompt_current_step(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        session: GuideWizardSession,
        *,
        edit: bool = False,
    ) -> None:
        text, markup = self._build_prompt(session)
        chat_id = message.chat.id if edit else message.from_user.id
        if edit and hasattr(message, "edit_text"):
            await message.edit_text(
                text=text,
                link_preview_options=LINK_PREVIEW_OPTIONS,
                reply_markup=markup,
            )
            return
        await client.send_message(
            chat_id=chat_id,
            reply_parameters=ReplyParameters(message_id=message.id),
            text=text,
            link_preview_options=LINK_PREVIEW_OPTIONS,
            reply_markup=markup,
        )

    def _build_prompt(
        self, session: GuideWizardSession
    ) -> tuple[str, InlineKeyboardMarkup]:
        if session.step == WizardStep.SOURCE_CHANNEL:
            return self._source_prompt(session), _markup()
        if session.step == WizardStep.TARGET_CHANNEL:
            return self._target_prompt(session), _markup()
        if session.step == WizardStep.RANGE_DETECTED:
            return (
                f"🔎 已探测到可访问范围：消息 ID `{session.start_id}` ~ `{session.end_id}`\n"
                f"频道：`{session.source_link}`\n\n"
                "确认使用该范围，或自行指定起止消息链接。",
                _markup(
                    [
                        InlineKeyboardButton(
                            "✅ 确认范围",
                            callback_data=BotCallbackText.GUIDE_WIZARD_CONFIRM_RANGE,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✏️ 自己指定",
                            callback_data=BotCallbackText.GUIDE_WIZARD_CUSTOM_RANGE,
                        )
                    ],
                ),
            )
        if session.step == WizardStep.START_MESSAGE_LINK:
            return (
                f"📌 频道：`{session.source_link}`\n\n"
                "请发送**起始消息**的「复制链接」。\n"
                "操作：在 Telegram 中长按该频道最早要处理的消息 → 复制链接",
                _markup(),
            )
        if session.step == WizardStep.END_MESSAGE_LINK:
            return (
                f"📌 频道：`{session.source_link}`\n"
                f"起始 ID：`{session.start_id}`\n\n"
                "请发送**结束/最新消息**的「复制链接」。\n"
                "操作：长按该频道最后要处理的消息 → 复制链接",
                _markup(),
            )
        if session.step == WizardStep.INCLUDE_COMMENT:
            return (
                f"👥 是否同时处理评论区？\n源频道：`{session.source_link}`",
                _markup(
                    [
                        InlineKeyboardButton(
                            "✅ 包含评论区",
                            callback_data=BotCallbackText.GUIDE_WIZARD_COMMENT_YES,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ 不含评论区",
                            callback_data=BotCallbackText.GUIDE_WIZARD_COMMENT_NO,
                        )
                    ],
                ),
            )
        if session.step == WizardStep.LISTEN_CHANNEL:
            return (
                "🕵️ 请发送要**监听下载**的频道链接。\n"
                "可直接发频道地址，或任意一条消息的「复制链接」。",
                _markup(),
            )
        if session.step == WizardStep.LISTEN_COLLECT:
            joined = "\n".join(f"• `{link}`" for link in session.listen_links)
            return (
                f"已添加 {len(session.listen_links)} 个监听频道：\n{joined}\n\n"
                "可继续添加，或完成并开始监听。",
                _markup(
                    [
                        InlineKeyboardButton(
                            "➕ 再添加一个",
                            callback_data=BotCallbackText.GUIDE_WIZARD_ADD_LISTEN,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✅ 完成并开始监听",
                            callback_data=BotCallbackText.GUIDE_WIZARD_FINISH_LISTEN,
                        )
                    ],
                ),
            )
        return self._confirm_prompt(session), _markup(
            [
                InlineKeyboardButton(
                    "▶️ 确认执行",
                    callback_data=BotCallbackText.GUIDE_WIZARD_CONFIRM_EXECUTE,
                )
            ],
        )

    def _source_prompt(self, session: GuideWizardSession) -> str:
        labels = {
            WizardCommand.DOWNLOAD: "范围下载",
            WizardCommand.FORWARD: "范围转发",
            WizardCommand.DOWNLOAD_CHAT: "频道过滤下载",
            WizardCommand.LISTEN_FORWARD: "监听转发",
        }
        label = labels.get(session.command, "引导任务")
        return (
            f"🧭 **{label}** 引导\n\n"
            "第 1 步：请发送**源频道**链接。\n"
            "可发频道地址（如 `https://t.me/channel`），或任意一条消息的「复制链接」。"
        )

    def _target_prompt(self, session: GuideWizardSession) -> str:
        if session.command == WizardCommand.LISTEN_FORWARD:
            hint = "请发送**转发目标频道**链接。"
        else:
            hint = "请发送**转发目标频道**链接（消息将转发到该频道）。"
        return f"📌 源频道：`{session.source_link}`\n\n第 2 步：{hint}"

    def _confirm_prompt(self, session: GuideWizardSession) -> str:
        if session.command == WizardCommand.DOWNLOAD:
            return (
                f"📋 请确认范围下载任务：\n"
                f"• 源频道：`{session.source_link}`\n"
                f"• 范围：消息 `{session.start_id}` ~ `{session.end_id}`\n"
                f"• 目标：使用系统默认目标"
            )
        if session.command == WizardCommand.FORWARD:
            comment = "是" if session.include_comment else "否"
            return (
                f"📋 请确认范围转发任务：\n"
                f"• 源频道：`{session.source_link}`\n"
                f"• 目标频道：`{session.target_link}`\n"
                f"• 范围：消息 `{session.start_id}` ~ `{session.end_id}`\n"
                f"• 包含评论区：{comment}"
            )
        if session.command == WizardCommand.LISTEN_FORWARD:
            comment = "是" if session.include_comment else "否"
            return (
                f"📋 请确认监听转发：\n"
                f"• 监听源：`{session.source_link}`\n"
                f"• 转发到：`{session.target_link}`\n"
                f"• 包含评论区：{comment}"
            )
        return "请确认执行任务。"

    async def _reply_invalid_link(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        label: str,
    ) -> None:
        await client.send_message(
            chat_id=message.from_user.id,
            reply_parameters=ReplyParameters(message_id=message.id),
            text=f"❌无法识别{label}链接，请发送有效的 `https://t.me/...` 链接。",
            link_preview_options=LINK_PREVIEW_OPTIONS,
            reply_markup=_markup(),
        )

    async def _execute_command(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        session: GuideWizardSession,
    ) -> None:
        if session.command == WizardCommand.DOWNLOAD:
            await self._execute_download(client, message, session)
        elif session.command == WizardCommand.FORWARD:
            await self._execute_forward(client, message, session)
        elif session.command == WizardCommand.LISTEN_FORWARD:
            await self._execute_listen_forward(client, message, session)

    async def _execute_download(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        session: GuideWizardSession,
    ) -> None:
        host = self._host()
        if host is None:
            await message.edit_text("❌内部错误：无法执行任务。", reply_markup=None)
            return
        proxy_message = copy.copy(message)
        proxy_message.text = build_range_download_command(
            session.source_link,
            session.start_id,
            session.end_id,
        )
        await message.edit_text("🚛 正在创建下载任务...", reply_markup=None)
        await host.get_download_link_from_bot(client, proxy_message)

    async def _execute_forward(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        session: GuideWizardSession,
    ) -> None:
        host = self._host()
        if host is None:
            await message.edit_text("❌内部错误：无法执行任务。", reply_markup=None)
            return
        proxy_message = copy.copy(message)
        proxy_message.text = build_forward_command(
            session.source_link,
            session.target_link,
            session.start_id,
            session.end_id,
            include_comment=session.include_comment,
        )
        await message.edit_text("🚛 正在创建转发任务...", reply_markup=None)
        await host.get_forward_link_from_bot(client, proxy_message)

    async def _execute_listen_download(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        session: GuideWizardSession,
    ) -> None:
        host = self._host()
        if host is None:
            await message.edit_text("❌内部错误：无法执行任务。", reply_markup=None)
            return
        proxy_message = copy.copy(message)
        proxy_message.text = build_listen_download_command(session.listen_links)
        await message.edit_text("🚛 正在创建监听下载...", reply_markup=None)
        await host.on_listen(client, proxy_message)

    async def _execute_listen_forward(
        self,
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        session: GuideWizardSession,
    ) -> None:
        host = self._host()
        if host is None:
            await message.edit_text("❌内部错误：无法执行任务。", reply_markup=None)
            return
        proxy_message = copy.copy(message)
        proxy_message.text = build_listen_forward_command(
            session.source_link,
            session.target_link,
            include_comment=session.include_comment,
        )
        await message.edit_text("🚛 正在创建监听转发...", reply_markup=None)
        await host.on_listen(client, proxy_message)
