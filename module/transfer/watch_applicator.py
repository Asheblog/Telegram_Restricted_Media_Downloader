# coding=UTF-8
from typing import Optional, Protocol, runtime_checkable

import pyrogram
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid
from pyrogram.handlers import MessageHandler

from module import log
from module.domain.archive_naming.source_folders import normalize_archive_title_source
from module.persistence.transfer_store import TransferStatus
from module.utils.util import make_forward_watch_rule, parse_link


@runtime_checkable
class WatchApplicatorHost(Protocol):
    app: object
    user: object
    watch_manager: object
    listen_download_chat: dict
    listen_forward_chat: dict
    web_watch_handler_clients: dict
    web_pending_watches: dict

    def download_watch_id(self, link: str) -> str: ...
    def forward_watch_id(self, rule: str) -> str: ...
    def set_live_watch_status(self, watch_id: str, status: str, error_message: str = None) -> None: ...
    async def listen_download(self, client, message) -> None: ...
    async def listen_forward(self, client, message) -> None: ...


class LiveWatchApplicator:
    """Applies live watch handlers to Telegram clients (separate from LiveWatchManager CRUD)."""

    def __init__(self, host: WatchApplicatorHost):
        self._host = host

    @staticmethod
    def _set_live_watch_status(host, watch_id: str, status: str, error_message: str = None) -> None:
        watch_manager = getattr(host, "watch_manager", None)
        if watch_manager is not None:
            watch_manager.set_live_watch_status(watch_id, status, error_message)
            return
        LiveWatchApplicator._set_live_watch_status(host,watch_id, status, error_message)

    async def apply_watch(self, payload: dict) -> None:
        host = self._host
        watch_type = payload.get('watch_type')
        user_client = host.user or host.app.client
        if watch_type == 'download':
            link = payload.get('source_link')
            watch_id = host.download_watch_id(link)
            if link in host.listen_download_chat:
                LiveWatchApplicator._set_live_watch_status(host,watch_id, TransferStatus.RUNNING)
                host.web_pending_watches.pop(watch_id, None)
                return
            chat = await user_client.get_chat(link)
            if getattr(chat, 'is_forum', False):
                raise PeerIdInvalid
            handler = MessageHandler(host.listen_download, filters=pyrogram.filters.chat(chat.id))
            host.listen_download_chat[link] = handler
            host.watch_manager._download_chat_watch_id[str(chat.id)] = watch_id
            user_client.add_handler(handler)
            host.web_watch_handler_clients[watch_id] = user_client
            LiveWatchApplicator._set_live_watch_status(host,watch_id, TransferStatus.RUNNING)
            host.web_pending_watches.pop(watch_id, None)
            log.info(f'已通过WebUI新增监听下载,频道链接:"{link}"。')
            return
        if watch_type == 'forward':
            source_link = payload.get('source_link')
            target_link = payload.get('target_link')
            include_comment = bool(payload.get('include_comment'))
            resolve_deep_link = bool(payload.get('resolve_deep_link'))
            archive_by_author = bool(payload.get('archive_by_author'))
            archive_title_source = normalize_archive_title_source(
                payload.get('archive_title_source')
            )
            rule = make_forward_watch_rule(
                source_link, target_link, include_comment, resolve_deep_link,
                archive_by_author, archive_title_source,
            )
            watch_id = host.forward_watch_id(rule)
            if rule in host.listen_forward_chat:
                LiveWatchApplicator._set_live_watch_status(host,watch_id, TransferStatus.RUNNING)
                host.web_pending_watches.pop(watch_id, None)
                return
            try:
                chat = await user_client.get_chat(source_link)
                if getattr(chat, 'is_forum', False):
                    raise PeerIdInvalid
                filters = pyrogram.filters.chat(chat.id)
            except PeerIdInvalid:
                meta = await parse_link(client=host.app.client, link=source_link)
                topic_id = meta.get('topic_id')
                chat_id = meta.get('chat_id')
                filters = pyrogram.filters.chat(chat_id) & pyrogram.filters.topic(topic_id) if topic_id else pyrogram.filters.chat(chat_id)
            handler = MessageHandler(host.listen_forward, filters=filters)
            host.listen_forward_chat[rule] = handler
            user_client.add_handler(handler)
            host.web_watch_handler_clients[watch_id] = user_client
            LiveWatchApplicator._set_live_watch_status(host,watch_id, TransferStatus.RUNNING)
            host.web_pending_watches.pop(watch_id, None)
            comment_status = '包含评论区' if include_comment else '不包含评论区'
            log.info(f'已通过WebUI新增监听转发,转发规则:"{source_link} -> {target_link}",{comment_status}。')
            return
        raise ValueError('Unsupported watch type.')

    def remove_watch(self, watch_id: str) -> bool:
        return self._host.watch_manager.delete_watch(watch_id)
