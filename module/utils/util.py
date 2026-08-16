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


def safe_index(lst: list, index: int, default=None):
    try:
        return lst[index]
    except IndexError:
        return default


INCLUDE_COMMENT_FLAGS = {"--include-comment", "--include-comments", "--comment"}
RESOLVE_DEEP_LINK_FLAGS = {"--resolve-deep-link", "--resolve_deep_link"}
ARCHIVE_BY_AUTHOR_FLAGS = {"--archive-by-author", "--archive_by_author"}
ARCHIVE_TITLE_SOURCE_PREFIXES = ("--archive-title-source=", "--archive_title_source=")


def split_include_comment_flag(args: list) -> Tuple[list, bool]:
    include_comment = False
    clean_args = []
    for arg in args:
        if str(arg).strip().lower() in INCLUDE_COMMENT_FLAGS:
            include_comment = True
        else:
            clean_args.append(arg)
    return clean_args, include_comment


def split_resolve_deep_link_flag(args: list) -> Tuple[list, bool]:
    resolve_deep_link = False
    clean_args = []
    for arg in args:
        if str(arg).strip().lower() in RESOLVE_DEEP_LINK_FLAGS:
            resolve_deep_link = True
        else:
            clean_args.append(arg)
    return clean_args, resolve_deep_link


def split_archive_by_author_flag(args: list) -> Tuple[list, bool]:
    archive_by_author = False
    clean_args = []
    for arg in args:
        if str(arg).strip().lower() in ARCHIVE_BY_AUTHOR_FLAGS:
            archive_by_author = True
        else:
            clean_args.append(arg)
    return clean_args, archive_by_author


def split_archive_title_source_flag(args: list) -> Tuple[list, str]:
    from module.domain.archive_naming.source_folders import (
        normalize_archive_title_source,
        ARCHIVE_TITLE_SOURCE_AUTO,
    )

    archive_title_source = ARCHIVE_TITLE_SOURCE_AUTO
    clean_args = []
    for arg in args:
        lowered = str(arg).strip().lower()
        matched = False
        for prefix in ARCHIVE_TITLE_SOURCE_PREFIXES:
            if lowered.startswith(prefix):
                archive_title_source = normalize_archive_title_source(
                    lowered[len(prefix) :]
                )
                matched = True
                break
        if not matched:
            clean_args.append(arg)
    return clean_args, archive_title_source


def make_forward_watch_rule(
    source_link: str,
    target_link: str,
    include_comment: bool = False,
    resolve_deep_link: bool = False,
    archive_by_author: bool = False,
    archive_title_source: str = "auto",
) -> str:
    from module.domain.archive_naming.source_folders import (
        normalize_archive_title_source,
        ARCHIVE_TITLE_SOURCE_AUTO,
    )

    rule = f"{source_link} {target_link}"
    if include_comment:
        rule += " --include-comment"
    if resolve_deep_link:
        rule += " --resolve-deep-link"
    if archive_by_author:
        rule += " --archive-by-author"
    title_source = normalize_archive_title_source(archive_title_source)
    if title_source != ARCHIVE_TITLE_SOURCE_AUTO:
        rule += f" --archive-title-source={title_source}"
    return rule


def parse_forward_watch_rule(rule: str) -> dict:
    args, include_comment = split_include_comment_flag(str(rule).split())
    args, resolve_deep_link = split_resolve_deep_link_flag(args)
    args, archive_by_author = split_archive_by_author_flag(args)
    args, archive_title_source = split_archive_title_source_flag(args)
    return {
        "source_link": safe_index(args, 0, ""),
        "target_link": safe_index(args, 1, ""),
        "include_comment": include_comment,
        "resolve_deep_link": resolve_deep_link,
        "archive_by_author": archive_by_author,
        "archive_title_source": archive_title_source,
    }


def get_terminal_width() -> int:
    terminal_width: int = 120
    try:
        terminal_width: int = os.get_terminal_size().columns
    except OSError:
        pass
    return terminal_width


def truncate_display_filename(file_name: str) -> Text:
    terminal_width: int = get_terminal_width()
    max_width: int = max(int(terminal_width * 0.3), 1)
    text = Text(file_name)
    text.truncate(max_width=max_width, overflow="ellipsis")
    return text


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


def add_executable_permission(file_path: str) -> bool:
    """确保文件具有执行权限(仅Linux/macOS)。"""
    if sys.platform not in ("linux", "darwin"):
        return True
    try:
        st = os.stat(file_path)
        mode = st.st_mode
        if not (mode & stat.S_IXUSR):
            os.chmod(file_path, mode | stat.S_IXUSR)
            log.info(f'已为"{file_path}"添加执行权限。')
        return True
    except Exception as e:
        log.warning(f"添加执行权限失败:{e}。")
        return False


def get_subprocess_args(main_file: str) -> list:
    """获取子进程参数列表。"""
    args = [sys.argv[0]] if "__compiled__" in globals() else [sys.executable, main_file]
    # 添加非web参数
    if PARSE_ARGS.quiet:
        args.append("--quiet")
    if PARSE_ARGS.config:
        args.extend(["--config", PARSE_ARGS.config])
    if PARSE_ARGS.session:
        args.extend(["--session", PARSE_ARGS.session])
    if PARSE_ARGS.temp:
        args.extend(["--temp", PARSE_ARGS.temp])

    return args


def gen_random_credential() -> dict:
    chars = string.ascii_letters + string.digits
    username = "".join(random.choices(chars, k=8))
    password = "".join(random.choices(chars, k=12))
    return {"username": username, "password": password}


def check_environ() -> None:
    if PARSE_ARGS.web is not None:
        environ_name, environ_param = ENVIRON.TRMD_WEB_PORT, str(PARSE_ARGS.web)
        os.environ[environ_name] = environ_param
        log.info(f'添加系统环境变量:"{environ_name}={environ_param}"。')


def is_nuitka() -> bool:
    return "__compiled__" in globals()


def is_docker() -> bool:
    """检查是否在Docker容器中运行。"""
    # 检查/.dockerenv文件是否存在。
    if os.path.exists("/.dockerenv"):
        return True

    # 检查/proc/1/cgroup中是否包含"docker"。
    try:
        with open("/proc/1/cgroup", "r") as f:
            content = f.read()
            if "docker" in content or "kubepods" in content:
                return True
    except (FileNotFoundError, IOError):
        pass
    except Exception:
        pass

    return False


class Issues:
    PROXY_NOT_CONFIGURED = '[#79FCD4]代理配置方法[/#79FCD4][#FF79D4]请访问:[/#FF79D4]\n[link=https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader/wiki#问题14-error-运行出错原因0-keyerror-0]https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader/wiki#问题14-error-运行出错原因0-keyerror-0[/link]\n[#FCFF79]若[/#FCFF79][#FF4689]无法[/#FF4689][#FF7979]访问[/#FF7979][#79FCD4],[/#79FCD4][#FCFF79]可[/#FCFF79][#d4fc79]查阅[/#d4fc79][#FC79A5]软件压缩包所提供的[/#FC79A5][#79E2FC]"使用手册"[/#79E2FC][#79FCD4]文件夹下的[/#79FCD4][#FFB579]"常见问题及解决方案汇总.pdf"[/#FFB579][#79FCB5]中的[/#79FCB5][#D479FC]【问题14】[/#D479FC][#FCE679]进行操作[/#FCE679][#FC79A6]。[/#FC79A6]'
    SYSTEM_TIME_NOT_SYNCHRONIZED = '[#FCFF79]检测到[/#FCFF79][#FF7979]系统时间[/#FF7979][#FC79A5]未同步[/#FC79A5][#79E2FC],[/#79E2FC][#79FCD4]解决方法[/#79FCD4][#FF79D4]请访问:[/#FF79D4]\nhttps://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader/issues/5#issuecomment-2580677184\n[#FCFF79]若[/#FCFF79][#FF4689]无法[/#FF4689][#FF7979]访问[/#FF7979][#79FCD4],[/#79FCD4][#FCFF79]可[/#FCFF79][#d4fc79]查阅[/#d4fc79][#FC79A5]软件压缩包所提供的[/#FC79A5][#79E2FC]"使用手册"[/#79E2FC][#79FCB5]中的[/#79FCB5][#D479FC]【问题4】[/#D479FC][#FCE679]进行操作[/#FCE679][#FC79A6],[/#FC79A6][#79FCD4]并[/#79FCD4][#79FCB5]重启软件[/#79FCB5]。'
