# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/3/10 0:45
# File:util.py
import os
import re
import sys
import stat
import string
import random

from typing import Tuple, List, Union, Optional, Callable, AsyncIterator

import pyrogram
from pyrogram import utils
from pyrogram.errors.exceptions.bad_request_400 import MsgIdInvalid
from pyrogram.types.messages_and_media import ReplyParameters
from rich.text import Text

from module import log
from module.utils.parser import PARSE_ARGS
from module.utils.telegram_links import extract_info_from_link  # noqa: F401  (re-exported for back-compat)
from module.core.enums import LinkType, DownloadType, ENVIRON

# 以下名字按内聚拆到子模块；此处 re-export，既有 `from module.utils.util import X` 继续可用。
from module.utils.flag_support import (  # noqa: F401
    ARCHIVE_BY_AUTHOR_FLAGS,
    ARCHIVE_TITLE_SOURCE_PREFIXES,
    INCLUDE_COMMENT_FLAGS,
    RESOLVE_DEEP_LINK_FLAGS,
    make_forward_watch_rule,
    parse_forward_watch_rule,
    safe_index,
    split_archive_by_author_flag,
    split_archive_title_source_flag,
    split_include_comment_flag,
    split_resolve_deep_link_flag,
)
from module.utils.display_support import (  # noqa: F401
    get_terminal_width,
    truncate_display_filename,
)
from module.utils.runtime_support import (  # noqa: F401
    add_executable_permission,
    check_environ,
    gen_random_credential,
    get_subprocess_args,
    is_docker,
    is_nuitka,
)























def safe_message(text: str, max_length: int = 3969) -> List[str]:
    if len(text) <= max_length:
        return [text]
    else:
        part1 = text[:max_length]
        part2 = text[max_length:]
        return [part1] + safe_message(part2, max_length)


async def safe_delete_message(message: pyrogram.types.Message) -> bool:
    try:
        await message.delete()
        return True
    except Exception:
        return False


async def parse_link(client: pyrogram.Client, link: str) -> dict:
    # https://github.com/tangyoha/telegram_media_downloader/blob/master/module/pyrogram_extension.py#L1092
    try:
        link = extract_info_from_link(link)
        if link.comment_id:
            chat = await client.get_chat(link.group_id)
            if chat:
                return {
                    "chat_id": chat.linked_chat.id,
                    "comment_id": link.comment_id,
                    "topic_id": link.topic_id,
                }

        return {
            "chat_id": link.group_id,
            "comment_id": link.post_id,
            "topic_id": link.topic_id,
        }
    except Exception:
        raise ValueError("Invalid message link.")


async def _resolve_discussion_thread(
    client: pyrogram.Client,
    chat_id: Union[int, str],
    message_id: int,
) -> tuple[Union[int, str], int, Optional[int]]:
    """Resolve linked discussion group thread for a channel post."""
    try:
        discussion = await client.get_discussion_message(chat_id, message_id)
        discussion_chat_id = getattr(getattr(discussion, "chat", None), "id", None)
        discussion_message_id = getattr(discussion, "id", None)
        if discussion_chat_id is not None and discussion_message_id is not None:
            return discussion_chat_id, discussion_message_id, discussion_message_id
    except (ValueError, AttributeError, MsgIdInvalid):
        pass
    return chat_id, message_id, None


async def _collect_discussion_replies(
    client: pyrogram.Client,
    reply_chat_id: Union[int, str],
    reply_message_id: int,
    root_message_id: Optional[int] = None,
    *,
    channel_chat_id: Optional[Union[int, str]] = None,
    channel_message_id: Optional[int] = None,
) -> list:
    async def _fetch(peer_chat_id: Union[int, str], peer_message_id: int) -> list:
        replies: list = []
        async for comment in client.get_discussion_replies(
            peer_chat_id, peer_message_id
        ):
            if (
                root_message_id is not None
                and getattr(comment, "id", None) == root_message_id
            ):
                continue
            replies.append(comment)
        return replies

    try:
        return await _fetch(reply_chat_id, reply_message_id)
    except MsgIdInvalid:
        if (
            channel_chat_id is None
            or channel_message_id is None
            or (
                reply_chat_id == channel_chat_id
                and reply_message_id == channel_message_id
            )
        ):
            raise
        return await _fetch(channel_chat_id, channel_message_id)


def _index_replies_by_media_group(replies: list) -> dict:
    grouped: dict = {}
    for message in replies:
        media_group_id = getattr(message, "media_group_id", None)
        if media_group_id is None:
            continue
        grouped.setdefault(media_group_id, []).append(message)
    for media_group_id in grouped:
        grouped[media_group_id].sort(key=lambda item: getattr(item, "id", 0) or 0)
    return grouped


async def _resolve_discussion_reply_members(
    message,
    replies_by_media_group: Optional[dict] = None,
) -> list:
    media_group_id = getattr(message, "media_group_id", None)
    if media_group_id is not None and replies_by_media_group:
        grouped = replies_by_media_group.get(media_group_id) or []
        if len(grouped) > 1:
            return grouped
    get_media_group = getattr(message, "get_media_group", None)
    if callable(get_media_group):
        try:
            group_messages = await get_media_group()
            if group_messages:
                return list(group_messages)
        except (ValueError, AttributeError, TypeError):
            pass
    if media_group_id is not None and replies_by_media_group:
        grouped = replies_by_media_group.get(media_group_id) or []
        if grouped:
            return grouped
    return [message]


async def iter_discussion_reply_messages(
    client: pyrogram.Client,
    chat_id: Union[int, str],
    message_id: int,
    *,
    target_message_id: Optional[int] = None,
    include_message: Optional[Callable[[pyrogram.types.Message], bool]] = None,
) -> AsyncIterator[pyrogram.types.Message]:
    """Iterate discussion replies, expanding media groups into individual messages."""
    reply_chat_id, reply_message_id, root_message_id = await _resolve_discussion_thread(
        client, chat_id, message_id
    )
    raw_replies = await _collect_discussion_replies(
        client,
        reply_chat_id,
        reply_message_id,
        root_message_id,
        channel_chat_id=chat_id,
        channel_message_id=message_id,
    )
    replies_by_media_group = _index_replies_by_media_group(raw_replies)
    seen_media_group_ids: set = set()
    seen_message_ids: set = set()

    for comment in raw_replies:
        media_group_id = getattr(comment, "media_group_id", None)
        if media_group_id is not None:
            if media_group_id in seen_media_group_ids:
                continue
            seen_media_group_ids.add(media_group_id)

        members = await _resolve_discussion_reply_members(
            comment, replies_by_media_group
        )
        if not members:
            continue

        member_ids = {getattr(member, "id", None) for member in members}
        if target_message_id is not None and target_message_id not in member_ids:
            continue

        for member in members:
            member_id = getattr(member, "id", None)
            if member_id is None or member_id in seen_message_ids:
                continue
            if include_message and not include_message(member):
                continue
            seen_message_ids.add(member_id)
            yield member


async def iter_discussion_reply_forward_units(
    client: pyrogram.Client,
    chat_id: Union[int, str],
    message_id: int,
    *,
    include_message: Optional[Callable[[pyrogram.types.Message], bool]] = None,
) -> AsyncIterator[tuple[pyrogram.types.Message, Optional[list]]]:
    """Iterate discussion replies as forward units; media groups are yielded once."""
    reply_chat_id, reply_message_id, root_message_id = await _resolve_discussion_thread(
        client, chat_id, message_id
    )
    raw_replies = await _collect_discussion_replies(
        client,
        reply_chat_id,
        reply_message_id,
        root_message_id,
        channel_chat_id=chat_id,
        channel_message_id=message_id,
    )
    replies_by_media_group = _index_replies_by_media_group(raw_replies)
    seen_media_group_ids: set = set()
    seen_message_ids: set = set()

    for comment in raw_replies:
        media_group_id = getattr(comment, "media_group_id", None)
        if media_group_id is not None:
            if media_group_id in seen_media_group_ids:
                continue
            seen_media_group_ids.add(media_group_id)
            members = await _resolve_discussion_reply_members(
                comment, replies_by_media_group
            )
            if include_message and not any(
                include_message(member) for member in members
            ):
                continue
            if len(members) > 1:
                yield comment, members
            else:
                yield members[0], None
            continue

        member = comment
        member_id = getattr(member, "id", None)
        if member_id is None or member_id in seen_message_ids:
            continue
        if include_message and not include_message(member):
            continue
        seen_message_ids.add(member_id)
        yield member, None


async def get_message_by_link(
    client: pyrogram.Client,
    link: str,
    single_link: bool = False,  # 为True时,将每个链接都视作是单文件。
) -> Union[dict, None]:
    origin_link: str = link
    record_type: set = set()
    link: str = link[:-1] if link.endswith("/") else link
    if "?single&comment" in link:  # v1.1.0修复讨论组中附带?single时不下载的问题。
        record_type.add(LinkType.COMMENT)
        single_link = True
    if "?single" in link:
        link: str = link.split("?single")[0]
        single_link = True
    if "?comment" in link:  # 链接中包含?comment表示用户需要同时下载评论中的媒体。
        link = link.split("?comment")[0]
        record_type.add(LinkType.COMMENT)
    if link.count("/") >= 5 or "t.me/c/" in link:
        if link.startswith("https://t.me/c/"):
            count: int = link.split("https://t.me/c/")[1].count("/")
            record_type.add(LinkType.TOPIC) if count == 2 else None
        elif link.startswith("https://t.me"):
            record_type.add(LinkType.TOPIC)

    # https://github.com/KurimuzonAkuma/pyrogram/blob/dev/pyrogram/methods/messages/get_messages.py#L101
    match = re.match(
        r"^(?:https?://)?(?:www\.)?(?:t(?:elegram)?\.(?:org|me|dog)/(?:c/)?)([\w]+)(?:/\d+)*/(\d+)/?$",
        link.lower(),
    )
    if not match:
        raise ValueError("Invalid message link.")

    try:
        chat_id = utils.get_channel_id(int(match.group(1)))
    except ValueError:
        chat_id = match.group(1)
    message_id: int = int(match.group(2))
    comment_message: list = []
    if LinkType.COMMENT in record_type:
        # 如果用户需要同时下载媒体下面的评论,把评论中的所有信息放入列表一起返回。
        target_message_id = None
        if single_link and "=" in origin_link:
            try:
                target_message_id = int(origin_link.split("=")[-1])
            except ValueError:
                target_message_id = None
        async for comment in iter_discussion_reply_messages(
            client=client,
            chat_id=chat_id,
            message_id=message_id,
            target_message_id=target_message_id,
            include_message=lambda item: any(
                getattr(item, dtype) for dtype in DownloadType()
            ),
        ):
            comment_message.append(comment)
    message = await client.get_messages(chat_id=chat_id, message_ids=message_id)
    is_group, group_message = await __is_group(message)
    if single_link:
        is_group = False
        group_message: Union[list, None] = None
    if is_group or comment_message:  # 组或评论区。
        try:  # v1.1.2解决当group返回None时出现comment无法下载的问题。
            group_message.extend(comment_message) if comment_message else None
        except AttributeError:
            if comment_message and group_message is None:
                group_message: list = []
                group_message.extend(comment_message)
        if comment_message:
            return {
                "link_type": LinkType.TOPIC
                if LinkType.TOPIC in record_type
                else LinkType.COMMENT,
                "chat_id": chat_id,
                "message": group_message,
                "member_num": len(group_message),
            }
        else:
            return {
                "link_type": LinkType.TOPIC
                if LinkType.TOPIC in record_type
                else LinkType.GROUP,
                "chat_id": chat_id,
                "message": group_message,
                "member_num": len(group_message),
            }
    elif is_group is False and group_message is None:  # 单文件。
        return {
            "link_type": LinkType.TOPIC
            if LinkType.TOPIC in record_type
            else LinkType.SINGLE,
            "chat_id": chat_id,
            "message": message,
            "member_num": 1,
        }
    elif is_group is None and group_message is None:
        raise MsgIdInvalid(
            "The message does not exist, the channel has been disbanded or is not in the channel."
        )
    elif is_group is None and group_message == 0:
        raise Exception("Link parsing error.")
    else:
        raise Exception("Unknown error.")


async def __is_group(message) -> Tuple[Union[bool, None], Union[list, None]]:
    try:
        return True, await message.get_media_group()
    except ValueError:
        return False, None  # v1.0.4 修改单文件无法下载问题。
    except AttributeError:
        return None, None


async def get_chat_with_notify(
    user_client: pyrogram.Client,
    chat_id: Union[int, str],
    error_msg: Optional[str] = None,
    bot_client: Optional[pyrogram.Client] = None,
    bot_message: Optional[pyrogram.types.Message] = None,
) -> Union[pyrogram.types.Chat, None]:
    try:
        chat = await user_client.get_chat(chat_id)
        return chat
    except Exception:
        if all([bot_client, bot_message]):
            await bot_client.send_message(
                chat_id=bot_message.from_user.id,
                reply_parameters=ReplyParameters(message_id=bot_message.id),
                text=error_msg if error_msg else "",
            )
        return None


async def get_valid_chat_id(
    link: Union[int, str],
    user_client: pyrogram.Client,
    bot_client: Union[pyrogram.Client] = None,
    bot_message: Union[pyrogram.types.Message] = None,
    error_msg: Union[str] = None,
) -> Union[int, str, None]:
    m = await parse_link(client=user_client, link=link)
    if not await get_chat_with_notify(
        user_client=user_client,
        chat_id=m.get("chat_id"),
        bot_client=bot_client,
        bot_message=bot_message,
        error_msg=error_msg if error_msg else "",
    ):
        return None
    return m.get("chat_id")


def is_allow_upload(file_size: int, is_premium: bool) -> bool:
    file_size_limit_mib: int = 4000 * 1024 * 1024 if is_premium else 2000 * 1024 * 1024
    if file_size > file_size_limit_mib:
        return False
    return True


async def format_chat_link(
    link: str, client: pyrogram.Client, topic: bool = False
) -> str:
    if link in ("me", "self"):
        chat = await client.get_chat(link)
        return "https://t.me/" + chat.username if chat.username else None
    parts: list = link.strip("/").split("/")
    len_parts: int = len(parts)
    result: Union[str, None] = None
    if len_parts > 3 and topic is False:
        # 判断是否是/c/类型的频道链接(确保是独立的'c'部分)。
        if parts[3] == "c" and len_parts >= 5:  # 对于/c/类型。
            if len_parts >= 6:
                # 6个部分时,保留前5个部分 (去掉最后一个)。
                result = "/".join(
                    parts[:5]
                )  # https://t.me/c/2530641322/1 -> https://t.me/c/2530641322

        else:  # 对于普通类型。
            if len_parts >= 5:
                # 5个部分时,保留前4个部分(去掉最后一个)。
                result = "/".join(
                    parts[:4]
                )  # https://t.me/customer/144 -> https://t.me/customer
    else:  # 话题格式化。
        if parts[3] == "c" and len_parts >= 5:  # 对于/c/类型。
            if len_parts >= 7:
                # 7个部分时,保留前6个部分(去掉最后一个)。
                result = "/".join(
                    parts[:6]
                )  # https://t.me/c/2495197831/100/200 -> https://t.me/c/2495197831/100
        elif len_parts >= 6:
            # 6个部分时,保留前5个部分(去掉最后一个)。
            result = "/".join(
                parts[:5]
            )  # https://t.me/customer/5/1 -> https://t.me/customer/5

    return result if result else link


async def get_my_id(client: pyrogram.Client) -> int:
    me = await client.get_me()
    return me.id














class Issues:
    PROXY_NOT_CONFIGURED = '[#79FCD4]代理配置方法[/#79FCD4][#FF79D4]请访问:[/#FF79D4]\n[link=https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader/wiki#问题14-error-运行出错原因0-keyerror-0]https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader/wiki#问题14-error-运行出错原因0-keyerror-0[/link]\n[#FCFF79]若[/#FCFF79][#FF4689]无法[/#FF4689][#FF7979]访问[/#FF7979][#79FCD4],[/#79FCD4][#FCFF79]可[/#FCFF79][#d4fc79]查阅[/#d4fc79][#FC79A5]软件压缩包所提供的[/#FC79A5][#79E2FC]"使用手册"[/#79E2FC][#79FCD4]文件夹下的[/#79FCD4][#FFB579]"常见问题及解决方案汇总.pdf"[/#FFB579][#79FCB5]中的[/#79FCB5][#D479FC]【问题14】[/#D479FC][#FCE679]进行操作[/#FCE679][#FC79A6]。[/#FC79A6]'
    SYSTEM_TIME_NOT_SYNCHRONIZED = '[#FCFF79]检测到[/#FCFF79][#FF7979]系统时间[/#FF7979][#FC79A5]未同步[/#FC79A5][#79E2FC],[/#79E2FC][#79FCD4]解决方法[/#79FCD4][#FF79D4]请访问:[/#FF79D4]\nhttps://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader/issues/5#issuecomment-2580677184\n[#FCFF79]若[/#FCFF79][#FF4689]无法[/#FF4689][#FF7979]访问[/#FF7979][#79FCD4],[/#79FCD4][#FCFF79]可[/#FCFF79][#d4fc79]查阅[/#d4fc79][#FC79A5]软件压缩包所提供的[/#FC79A5][#79E2FC]"使用手册"[/#79E2FC][#79FCB5]中的[/#79FCB5][#D479FC]【问题4】[/#D479FC][#FCE679]进行操作[/#FCE679][#FC79A6],[/#FC79A6][#79FCD4]并[/#79FCD4][#79FCB5]重启软件[/#79FCB5]。'
