# coding=UTF-8
import datetime
import os

from typing import Callable, Optional

import pyrogram
from pyrogram.errors.exceptions.bad_request_400 import (
    MsgIdInvalid,
    PeerIdInvalid,
    ChatForwardsRestricted as ChatForwardsRestricted_400
)
from pyrogram.errors.exceptions.not_acceptable_406 import ChatForwardsRestricted as ChatForwardsRestricted_406
from pyrogram.handlers import MessageHandler

from module import log
from module.filter import Filter
from module.enums import DownloadStatus, UploadStatus, DownloadType
from module.task import DownloadTask, UploadTask
from module.transfer_store import TransferStatus
from module.uploader import TelegramUploader
from module.util import parse_link, get_chat_with_notify, is_allow_upload
from module.web_commands import WebCommand


class WebTaskExecutor:
    def __init__(self, downloader):
        self.downloader = downloader

    @property
    def store(self):
        return self.downloader.transfer_store

    def runtime_summary(self) -> dict:
        d = self.downloader
        download_rows = []
        for link, info in DownloadTask.LINK_INFO.items():
            download_rows.append({
                'link': str(link),
                'link_type': info.get('link_type'),
                'member_num': info.get('member_num', 0),
                'complete_num': info.get('complete_num', 0),
                'error_msg': info.get('error_msg') or {},
            })
        upload_rows = []
        for task in UploadTask.TASKS:
            status = task.status.value if isinstance(task.status, UploadStatus) else str(task.status)
            upload_rows.append({
                'file_path': task.file_path,
                'file_name': task.file_name,
                'chat_id': task.chat_id,
                'file_size': task.file_size,
                'status': status,
                'error_msg': task.error_msg,
                'with_delete': task.with_delete,
            })
        return {
            'downloads': download_rows,
            'uploads': upload_rows,
            'listeners': self.listener_payload(),
            'counts': {
                'downloads': len(download_rows),
                'uploads': len(upload_rows),
                'listen_download': len(d.listen_download_chat),
                'listen_forward': len(d.listen_forward_chat),
                'web_tasks': len(self.store.list_tasks()) if self.store else 0,
            },
            'shutdown_requested': getattr(d, 'web_shutdown_requested', False),
        }

    def listener_payload(self) -> list:
        d = self.downloader
        listeners = []
        for link in d.listen_download_chat:
            listeners.append({
                'id': link,
                'command': WebCommand.LISTEN_DOWNLOAD,
                'listen_link': link,
                'target_link': '',
            })
        for link in d.listen_forward_chat:
            args = str(link).split()
            listeners.append({
                'id': link,
                'command': WebCommand.LISTEN_FORWARD,
                'listen_link': args[0] if args else '',
                'target_link': args[1] if len(args) > 1 else '',
            })
        return listeners

    def remove_listener(self, listener_id: str) -> bool:
        d = self.downloader
        if listener_id in d.listen_download_chat:
            handler = d.listen_download_chat.pop(listener_id)
            d.app.client.remove_handler(handler)
            log.info(f'已通过WebUI删除监听下载:"{listener_id}"。')
            return True
        if listener_id in d.listen_forward_chat:
            handler = d.listen_forward_chat.pop(listener_id)
            d.app.client.remove_handler(handler)
            log.info(f'已通过WebUI删除监听转发:"{listener_id}"。')
            return True
        return False

    def add_event(self, task_id: int, message: str, level: str = 'info') -> None:
        if self.store:
            self.store.add_event(task_id, message, level=level)

    async def ensure_uploader(self) -> TelegramUploader:
        d = self.downloader
        if not d.uploader:
            d.uploader = TelegramUploader(download_object=d)
        return d.uploader

    async def process_download_task(self, task: dict) -> None:
        d = self.downloader
        payload = task.get('payload') or {}
        if not payload and task.get('source_link'):
            payload = {
                'links': [task.get('source_link')],
                'start_id': task.get('start_id'),
                'end_id': task.get('end_id'),
                'target_link': task.get('target_link'),
                'target_profile': task.get('target_profile'),
            }
        if payload.get('target_profile'):
            task['target_profile'] = payload.get('target_profile')
        if payload.get('target_link'):
            task['target_link'] = payload.get('target_link')
        links = list(payload.get('links') or [])
        file_path = payload.get('file_path')
        if file_path:
            links.append(file_path)
        start_id = payload.get('start_id')
        end_id = payload.get('end_id')
        target_link = payload.get('target_link')
        has_upload_target = bool(target_link)
        if has_upload_target:
            await self.ensure_uploader()
        assigned = 0
        for link in links:
            if start_id is not None and end_id is not None:
                source_prefix = str(link).rstrip('/')
                for message_id in range(int(start_id), int(end_id) + 1):
                    message_link = f'{source_prefix}/{message_id}?single'
                    task_with_upload = d.build_transfer_upload_meta(
                        task=task,
                        source_link=message_link
                    ) if has_upload_target else None
                    result = await d.create_download_task(
                        message_ids=message_link,
                        retry=None,
                        single_link=True,
                        with_upload=task_with_upload,
                        diy_download_type=[_ for _ in DownloadType()] if task_with_upload else None
                    )
                    if result.get('status') == DownloadStatus.FAILURE:
                        error = result.get('e_code') or {}
                        self.add_event(task['id'], f'Download item failed: {message_link} {error}', level='error')
                    else:
                        assigned += 1
            else:
                task_with_upload = d.build_transfer_upload_meta(
                    task=task,
                    source_link=link
                ) if has_upload_target else None
                result = await d.create_download_task(
                    message_ids=link,
                    retry=None,
                    single_link='?single' in str(link),
                    with_upload=task_with_upload,
                    diy_download_type=[_ for _ in DownloadType()] if task_with_upload else None
                )
                if result.get('status') == DownloadStatus.FAILURE:
                    error = result.get('e_code') or {}
                    self.add_event(task['id'], f'Download item failed: {link} {error}', level='error')
                else:
                    assigned += 1
        self.add_event(task['id'], f'Download task assigned {assigned} item(s).')

    async def process_forward_task(self, task: dict) -> None:
        d = self.downloader
        payload = task.get('payload') or {}
        origin_link = payload.get('origin_link')
        target_link = payload.get('target_link')
        start_id = int(payload.get('start_id'))
        end_id = int(payload.get('end_id'))
        origin_meta = await parse_link(client=d.app.client, link=origin_link)
        target_meta = await parse_link(client=d.app.client, link=target_link)
        origin_chat_id = origin_meta.get('chat_id')
        target_chat_id = target_meta.get('chat_id')
        origin_chat = await get_chat_with_notify(user_client=d.app.client, chat_id=origin_chat_id)
        target_chat = await get_chat_with_notify(user_client=d.app.client, chat_id=target_chat_id)
        if not all([origin_chat, target_chat]):
            raise ValueError('origin_link or target_link is not available.')
        forwarded = 0
        fallback_started = False
        async for message in d.app.client.get_chat_history(
                chat_id=origin_chat.id,
                offset_id=start_id,
                max_id=end_id,
                reverse=True
        ):
            try:
                await d.forward(
                    client=d.app.client,
                    message=message,
                    message_id=message.id,
                    origin_chat_id=origin_chat_id,
                    target_chat_id=target_chat_id,
                    target_link=target_link,
                    done_notice=False
                )
                forwarded += 1
            except (ChatForwardsRestricted_400, ChatForwardsRestricted_406):
                await self.ensure_uploader()
                fallback_started = True
                self.add_event(task['id'], 'Forward restricted; assigning download-upload fallback.', level='warning')
                source_prefix = str(origin_link).rstrip('/')
                for message_id in range(start_id, end_id + 1):
                    message_link = f'{source_prefix}/{message_id}?single'
                    await d.create_download_task(
                        message_ids=message_link,
                        retry=None,
                        single_link=True,
                        with_upload=d.build_transfer_upload_meta(task=task, source_link=message_link),
                        diy_download_type=[_ for _ in DownloadType()]
                    )
                break
        if forwarded:
            self.add_event(task['id'], f'Forwarded {forwarded} message(s).')
        if fallback_started:
            self.add_event(task['id'], 'Restricted forward fallback assigned.')

    async def add_listener(self, task_id: int, listen_key: str, callback: Callable, listen_chat: dict) -> bool:
        d = self.downloader
        if listen_key in listen_chat:
            self.add_event(task_id, f'Listener already exists: {listen_key}', level='warning')
            return False
        link_meta = str(listen_key).split()
        listen_link = link_meta[0]
        try:
            try:
                chat = await d.app.client.get_chat(listen_link)
                if chat.is_forum:
                    raise PeerIdInvalid
                filters = pyrogram.filters.chat(chat.id)
            except PeerIdInvalid:
                meta = await parse_link(client=d.app.client, link=listen_link)
                topic_id = meta.get('topic_id')
                chat_id = meta.get('chat_id')
                filters = pyrogram.filters.chat(chat_id)
                if topic_id:
                    filters = filters & pyrogram.filters.topic(topic_id)
            handler = MessageHandler(callback, filters=filters)
            listen_chat[listen_key] = handler
            d.app.client.add_handler(handler)
            self.add_event(task_id, f'Listener registered: {listen_key}')
            return True
        except Exception as e:
            self.add_event(task_id, f'Listener registration failed: {listen_key} {e}', level='error')
            raise

    async def process_listen_download_task(self, task: dict) -> None:
        d = self.downloader
        payload = task.get('payload') or {}
        registered = 0
        for link in payload.get('links') or []:
            if await self.add_listener(task['id'], link, d.listen_download, d.listen_download_chat):
                registered += 1
        self.add_event(task['id'], f'listen_download registered {registered} listener(s).')

    async def process_listen_forward_task(self, task: dict) -> None:
        d = self.downloader
        payload = task.get('payload') or {}
        listen_key = f"{payload.get('listen_link')} {payload.get('target_link')}"
        if await self.add_listener(task['id'], listen_key, d.listen_forward, d.listen_forward_chat):
            self.add_event(task['id'], 'listen_forward registered.')

    async def process_upload_task(self, task: dict) -> None:
        d = self.downloader
        payload = task.get('payload') or {}
        file_path = payload.get('file_path')
        target_link = payload.get('target_link')
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f'Upload file does not exist: {file_path}')
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError('Upload file size is 0.')
        if not is_allow_upload(file_size=file_size, is_premium=d.app.client.me.is_premium):
            raise ValueError('Upload file exceeds Telegram size limit.')
        uploader = await self.ensure_uploader()
        item_id = self.store.add_item(
            task_id=task['id'],
            source_message_id=None,
            source_link=file_path,
            target_link=target_link,
            media_type='file',
            local_path=file_path,
            status=TransferStatus.RUNNING
        )
        upload_task = UploadTask(
            chat_id=None,
            file_path=file_path,
            file_id=d.app.client.rnd_id(),
            file_size=file_size,
            file_part=[],
            status=UploadStatus.PENDING,
            with_delete=bool(payload.get('delete_after_upload')),
            transfer_meta={
                'task_id': task['id'],
                'item_id': item_id,
                'target_profile': task.get('target_profile')
            },
            status_callback=d.on_transfer_upload_status
        )
        await uploader.create_upload_task(link=target_link, upload_task=upload_task)
        self.add_event(task['id'], f'Upload queued: {os.path.basename(file_path)}')
        d.refresh_transfer_task_counts(task['id'])

    async def process_upload_recursive_task(self, task: dict) -> None:
        payload = task.get('payload') or {}
        directory_path = payload.get('directory_path')
        target_link = payload.get('target_link')
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f'Upload directory does not exist: {directory_path}')
        files = []
        for root, _, filenames in os.walk(directory_path):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        if not files:
            raise ValueError('Upload directory is empty.')
        self.add_event(task['id'], f'Recursive upload discovered {len(files)} file(s).')
        for file_path in files:
            self.add_event(task['id'], f'Recursive upload queued file: {file_path}')
            child_task = task.copy()
            child_task['payload'] = {
                'file_path': file_path,
                'target_link': target_link,
                'delete_after_upload': payload.get('delete_after_upload')
            }
            await self.process_upload_task(child_task)

    @staticmethod
    def iso_date_to_timestamp(value: Optional[str], end_of_day: bool = False) -> Optional[float]:
        if not value:
            return None
        date_value = datetime.date.fromisoformat(value)
        time_value = datetime.time.max if end_of_day else datetime.time.min
        return datetime.datetime.combine(date_value, time_value).timestamp()

    async def process_download_chat_task(self, task: dict) -> None:
        d = self.downloader
        payload = task.get('payload') or {}
        chat_link = payload.get('chat_link')
        meta = await parse_link(client=d.app.client, link=chat_link)
        chat_id = meta.get('chat_id')
        if not chat_id:
            raise ValueError('Unable to resolve chat link.')
        start_date = self.iso_date_to_timestamp(payload.get('start_date'))
        end_date = self.iso_date_to_timestamp(payload.get('end_date'), end_of_day=True)
        download_type = payload.get('download_type') or {dtype: True for dtype in DownloadType()}
        keywords = payload.get('keywords') or []
        include_comment = bool(payload.get('include_comment'))
        filter_object = Filter()
        links = []
        media_group_matched = set()
        async for message in d.app.client.get_chat_history(chat_id=chat_id, reverse=True):
            if getattr(message, 'media_group_id', None) and message.media_group_id in media_group_matched:
                links.append(message.link if message.link else message)
                continue
            if (
                    filter_object.date_range(message, start_date, end_date)
                    and filter_object.dtype(message, download_type)
                    and filter_object.keyword_filter(message, keywords)
            ):
                links.append(message.link if message.link else message)
                if message.media_group_id:
                    media_group_matched.add(message.media_group_id)
                if include_comment:
                    try:
                        async for comment in d.app.client.get_discussion_replies(chat_id=chat_id, message_id=message.id):
                            if filter_object.dtype(comment, download_type):
                                links.append(comment.link if comment.link else comment)
                    except (ValueError, AttributeError, MsgIdInvalid):
                        pass
        assigned = 0
        for link in links:
            result = await d.create_download_task(
                message_ids=link,
                single_link=True,
                diy_download_type=[_ for _ in DownloadType()]
            )
            if result.get('status') == DownloadStatus.FAILURE:
                self.add_event(task['id'], f'Download chat item failed: {link}', level='error')
            else:
                assigned += 1
        self.add_event(task['id'], f'Download chat matched {len(links)} item(s), assigned {assigned}.')

    async def process_exit_task(self, task: dict) -> None:
        d = self.downloader
        payload = task.get('payload') or {}
        d.web_shutdown_requested = True
        d.is_bot_running = False
        if d.web_ui:
            d.web_ui.stop()
            d.web_ui = None
        self.add_event(task['id'], f"Shutdown requested: {payload.get('reason')}")

    async def process_task(self, task_id: int) -> None:
        task = self.store.get_task(task_id) if self.store else None
        if not task:
            return
        if task.get('status') not in (TransferStatus.PENDING, TransferStatus.FAILURE):
            return
        self.store.update_task(task_id, status=TransferStatus.RUNNING, started=True)
        command = task.get('command') or 'transfer'
        self.store.add_event(task_id, f'{command} task started.')
        try:
            if command in ('transfer', WebCommand.DOWNLOAD):
                await self.process_download_task(task)
            elif command == WebCommand.FORWARD:
                await self.process_forward_task(task)
            elif command == WebCommand.LISTEN_DOWNLOAD:
                await self.process_listen_download_task(task)
            elif command == WebCommand.LISTEN_FORWARD:
                await self.process_listen_forward_task(task)
            elif command == WebCommand.UPLOAD:
                await self.process_upload_task(task)
            elif command == WebCommand.UPLOAD_R:
                await self.process_upload_recursive_task(task)
            elif command == WebCommand.DOWNLOAD_CHAT:
                await self.process_download_chat_task(task)
            elif command == WebCommand.EXIT:
                await self.process_exit_task(task)
            else:
                raise ValueError(f'Unsupported Web command: {command}')
            self.store.update_task(task_id, status=TransferStatus.SUCCESS, finished=True)
            self.store.add_event(task_id, f'{command} task accepted.')
        except Exception as e:
            self.store.update_task(
                task_id,
                status=TransferStatus.FAILURE,
                error_message=str(e),
                finished=True
            )
            self.store.add_event(task_id, f'{command} task failed: {e}', level='error')
