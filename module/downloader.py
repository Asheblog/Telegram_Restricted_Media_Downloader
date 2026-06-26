# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2023/10/3 1:00:03
# File:downloader.py
import os
import sys
import random
import asyncio
import datetime

from copy import deepcopy
from functools import partial
from sqlite3 import OperationalError
from typing import Union, Callable, Optional, Dict, Set

import pyrogram
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.errors import (
    BadMsgNotification,
    FileReferenceExpired,
    FloodWait,
    FloodPremiumWait
)
from pyrogram.errors.exceptions.bad_request_400 import (
    MsgIdInvalid,
    UsernameInvalid,
    ChannelInvalid,
    BotMethodInvalid,
    UsernameNotOccupied,
    PeerIdInvalid,
    MessageNotModified,
    ChannelPrivate as ChannelPrivate_400,
    ChatForwardsRestricted as ChatForwardsRestricted_400,
    MediaCaptionTooLong as MediaCaptionTooLong_400,
    MessageIdInvalid
)
from pyrogram.errors.exceptions.not_acceptable_406 import (
    ChannelPrivate as ChannelPrivate_406,
    ChatForwardsRestricted as ChatForwardsRestricted_406
)
from pyrogram.errors.exceptions.unauthorized_401 import (
    SessionRevoked,
    AuthKeyUnregistered,
    SessionExpired,
    Unauthorized
)
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.handlers import MessageHandler
from pyrogram.types.messages_and_media import ReplyParameters
from pyrogram.types.bots_and_keyboards import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from module import (
    console,
    log,
    LINK_PREVIEW_OPTIONS,
    SLEEP_THRESHOLD
)
from module.filter import Filter
from module.app import Application
from module.parser import PARSE_ARGS
from module.async_window import DynamicAsyncWindow
from module.bot import (
    Bot,
    KeyboardButton,
    CallbackData
)
from module.enums import (
    DownloadStatus,
    UploadStatus,
    LinkType,
    KeyWord,
    BotCallbackText,
    BotButton,
    BotMessage,
    DownloadType,
    CalenderKeyboard,
    SaveDirectoryPrefix
)
from module.language import _t
from module.path_tool import (
    is_file_duplicate,
    safe_delete,
    get_file_size,
    split_path,
    compare_file_size,
    move_to_save_directory,
    safe_replace,
    validate_title
)
from module.target_profiles import (
    target_profile_limit,
    target_profile_size_error
)
from module.pikpak_archive import build_pikpak_archive_client
from module.source_folders import source_folder_from_link, source_folder_from_message
from module.task import DownloadTask, UploadTask
from module.transfer_store import TransferStore, TransferStatus
from module.stdio import ProgressBar, Base64Image, MetaData
from module.uploader import TelegramUploader
from module.web_ui import (
    WebUiServer,
    get_web_host_from_env,
    get_web_password_from_env,
    get_web_port_from_env,
    get_web_username_from_env,
    merge_allowed_settings
)
from module.util import (
    is_docker,
    parse_link,
    format_chat_link,
    get_my_id,
    get_message_by_link,
    get_chat_with_notify,
    safe_message,
    safe_delete_message,
    truncate_display_filename,
    Issues,
    make_forward_watch_rule,
    parse_forward_watch_rule
)


class TelegramRestrictedMediaDownloader(Bot):

    def __init__(self):
        super().__init__()
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.event: asyncio.Event = asyncio.Event()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.app: Application = Application()
        self.download_upload_window = DynamicAsyncWindow(
            limit_provider=lambda: self.gc.upload_pending_limit,
            minimum=1,
            maximum=5
        )
        self.is_running: bool = False
        self.running_log: Set[bool] = set()
        self.running_log.add(self.is_running)
        self.pb: ProgressBar = ProgressBar()
        self.uploader: Union[TelegramUploader, None] = None
        self.cd: Union[CallbackData, None] = None
        self.my_id: int = 0
        self.transfer_store: Union[TransferStore, None] = None
        self.web_ui: Union[WebUiServer, None] = None
        self.web_task_queue: asyncio.Queue = asyncio.Queue()
        self.web_submitted_task_ids: Set[int] = set()
        self.web_running_task: Optional[asyncio.Task] = None
        self.web_running_task_id: Optional[int] = None
        self.web_operation_queue: asyncio.Queue = asyncio.Queue()
        self.web_operation_counter: int = 0
        self.web_operations: dict = {}
        self.web_pending_watches: dict = {}
        self.web_watch_handler_clients: dict = {}
        self.pikpak_archive_client = None

    @staticmethod
    def transfer_send_interval() -> float:
        return random.uniform(0.8, 2.4)

    async def wait_between_transfer_messages(self) -> None:
        await asyncio.sleep(self.transfer_send_interval())

    async def wait_for_telegram_flood(self, error, task_id: Optional[int] = None, action: str = 'request') -> None:
        amount = max(0, int(getattr(error, 'value', 0) or 0))
        jitter = random.uniform(0.5, 2.0) if amount > 0 else 0
        wait_seconds = amount + jitter
        message = f'Telegram flood wait during {action}: waiting {amount} seconds before retry.'
        console.log(message, style='#FF4689')
        log.warning(message)
        if self.transfer_store and task_id:
            self.transfer_store.add_event(task_id, message, level='warning')
        await asyncio.sleep(wait_seconds)

    def submit_web_task(self, task_id: int) -> None:
        if task_id in self.web_submitted_task_ids:
            return
        self.web_submitted_task_ids.add(task_id)
        try:
            if asyncio.get_running_loop() is self.loop:
                self.web_task_queue.put_nowait(task_id)
                return
        except RuntimeError:
            pass
        self.loop.call_soon_threadsafe(self.web_task_queue.put_nowait, task_id)

    def discard_web_task_submission(self, task_id: int, cancel_running: bool = True) -> None:
        def cleanup() -> None:
            self.web_submitted_task_ids.discard(task_id)
            self.drop_web_task_from_queue(task_id)
            if (
                    cancel_running
                    and self.web_running_task_id == task_id
                    and self.web_running_task
                    and not self.web_running_task.done()
            ):
                self.web_running_task.cancel()

        try:
            if asyncio.get_running_loop() is self.loop:
                cleanup()
                return
        except RuntimeError:
            pass
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(cleanup)
        else:
            cleanup()

    def drop_web_task_from_queue(self, task_id: int) -> None:
        kept_task_ids = []
        while True:
            try:
                queued_task_id = self.web_task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if queued_task_id != task_id:
                kept_task_ids.append(queued_task_id)
            self.web_task_queue.task_done()
        for queued_task_id in kept_task_ids:
            self.web_task_queue.put_nowait(queued_task_id)

    def delete_web_task(self, task_id: int) -> bool:
        if not self.transfer_store:
            return False
        deleted = self.transfer_store.delete_task(task_id)
        if deleted:
            self.discard_web_task_submission(task_id, cancel_running=True)
        return deleted

    def pause_web_task(self, task_id: int) -> bool:
        if not self.transfer_store or not self.transfer_store.get_task(task_id):
            return False
        self.transfer_store.update_task(task_id, status=TransferStatus.PAUSED)
        self.transfer_store.add_event(task_id, 'Transfer task paused.', level='warning')
        self.discard_web_task_submission(task_id, cancel_running=False)
        return True

    def resume_web_task(self, task_id: int) -> bool:
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        if not task or task.get('status') != TransferStatus.PAUSED:
            return False
        self.transfer_store.update_task(task_id, status=TransferStatus.PENDING)
        self.transfer_store.add_event(task_id, 'Transfer task resumed.')
        self.submit_web_task(task_id)
        return True

    def retry_failed_web_task(self, task_id: int) -> int:
        if not self.transfer_store:
            return 0
        task = self.transfer_store.get_task(task_id)
        if not task:
            return 0
        failed_items = [
            item for item in self.transfer_store.list_items(task_id)
            if item.get('status') == TransferStatus.FAILURE
        ]
        retry_item_ids = [
            int(item['id'])
            for item in failed_items
            if not self.recover_pikpak_failed_item_before_retry(task, item)
        ]
        reset_items = self.transfer_store.retry_failed_item_ids(task_id, retry_item_ids)
        if reset_items:
            self.submit_web_task(task_id)
        return reset_items

    def recover_pikpak_failed_item_before_retry(self, task: dict, item: dict) -> bool:
        if not self.is_pikpak_target(item.get('target_link') or task.get('target_link'), task.get('target_profile')):
            return False
        if 'PikPak ingest confirmation' not in str(item.get('error_message') or ''):
            return False
        if not item.get('file_name') and item.get('file_size') is None:
            return False
        item_id = int(item.get('id'))
        task_id = int(task.get('id'))
        result = self.archive_pikpak_item(
            target_profile='pikpak',
            item_id=item_id,
            task_id=task_id,
            message=None,
            source_link=item.get('source_link') or task.get('source_link'),
            source_folder=(
                item.get('source_folder')
                or source_folder_from_link(item.get('source_link') or task.get('source_link'))
            ),
            file_name=item.get('file_name'),
            file_size=item.get('file_size'),
            transferred_at=datetime.datetime.now(datetime.UTC).timestamp()
        )
        if not bool(getattr(result, 'ok', False)):
            return False
        self.transfer_store.update_item(
            item_id,
            phase='forwarded',
            status=TransferStatus.SUCCESS,
            error_message=''
        )
        self.transfer_store.add_event(
            task_id,
            f'PikPak ingest confirmation recovered before retry: {item.get("source_link") or task.get("source_link")}',
            item_id=item_id
        )
        self.refresh_transfer_task_counts(task_id)
        return True

    def next_web_operation_id(self, operation_type: str) -> str:
        self.web_operation_counter += 1
        return f'{operation_type}-{self.web_operation_counter}'

    def submit_web_operation(self, operation_type: str, payload: dict) -> dict:
        operation_id = self.next_web_operation_id(operation_type)
        operation = {
            'id': operation_id,
            'type': operation_type,
            'status': TransferStatus.PENDING,
            'payload': payload,
            'error_message': None,
            'created_at': TransferStore.utc_now(),
            'updated_at': TransferStore.utc_now()
        }
        self.web_operations[operation_id] = operation
        self.loop.call_soon_threadsafe(self.web_operation_queue.put_nowait, operation_id)
        return operation

    def detect_transfer_range(self, source_link: str) -> Optional[dict]:
        future = asyncio.run_coroutine_threadsafe(
            self.detect_transfer_range_async(source_link),
            self.loop
        )
        return future.result(timeout=60)

    async def detect_transfer_range_async(self, source_link: str) -> Optional[dict]:
        origin_meta = await parse_link(client=self.app.client, link=source_link)
        chat_id = origin_meta.get('chat_id')
        if not chat_id:
            raise ValueError('Invalid source link.')
        detected = await self.detect_transfer_range_fast(chat_id)
        if detected:
            return detected
        return await self.detect_transfer_range_by_history_scan(chat_id)

    async def detect_transfer_range_by_history_scan(self, chat_id) -> Optional[dict]:
        oldest = None
        newest = None
        async for message in self.iter_transfer_range_history(chat_id=chat_id):
            newest = newest or message
            oldest = message
        if not newest or not oldest:
            return None
        return {
            'start_id': int(getattr(oldest, 'id')),
            'end_id': int(getattr(newest, 'id'))
        }

    async def detect_transfer_range_fast(self, chat_id) -> Optional[dict]:
        client = self.app.client
        history_count = getattr(client, 'get_chat_history_count', None)
        if not callable(history_count):
            return None
        try:
            newest = await self.get_first_transfer_range_history_message(chat_id=chat_id, limit=1)
            if not newest:
                return None
            count = int(await history_count(chat_id))
            if count <= 1:
                oldest = newest
            else:
                oldest = await self.get_first_transfer_range_history_message(
                    chat_id=chat_id,
                    limit=1,
                    offset=count - 1
                )
            if not oldest:
                return None
            start_id = int(getattr(oldest, 'id'))
            end_id = int(getattr(newest, 'id'))
            if start_id > end_id:
                return None
            if count > 1 and start_id == end_id:
                return None
        except (FloodWait, FloodPremiumWait) as e:
            await self.wait_for_telegram_flood(e, action='detect transfer range')
            return None
        except Exception:
            return None
        return {
            'start_id': start_id,
            'end_id': end_id
        }

    async def get_first_transfer_range_history_message(self, chat_id, limit: int = 1, **kwargs):
        async for message in self.app.client.get_chat_history(
                chat_id=chat_id,
                limit=limit,
                **kwargs
        ):
            return message
        return None

    async def iter_transfer_range_history(self, chat_id, limit: int = 100):
        offset_id = 0
        while True:
            last_message_id = None
            try:
                async for message in self.app.client.get_chat_history(
                        chat_id=chat_id,
                        limit=limit,
                        offset_id=offset_id
                ):
                    last_message_id = getattr(message, 'id', None)
                    yield message
            except (FloodWait, FloodPremiumWait) as e:
                await self.wait_for_telegram_flood(e, action='detect transfer range')
                continue
            if last_message_id is None:
                return
            next_offset_id = int(last_message_id)
            if next_offset_id <= 0 or next_offset_id == offset_id:
                return
            offset_id = next_offset_id

    @staticmethod
    def download_watch_id(source_link: str) -> str:
        return f'download:{source_link}'

    @staticmethod
    def forward_watch_id(rule: str) -> str:
        return f'forward:{rule}'

    @staticmethod
    def watch_payload_from_record(watch: dict) -> dict:
        payload = {
            'watch_type': watch.get('type'),
            'source_link': watch.get('source_link')
        }
        if watch.get('type') == 'forward':
            payload['target_link'] = watch.get('target_link')
            payload['include_comment'] = bool(watch.get('include_comment'))
        return payload

    def persisted_watches(self) -> list:
        transfer_store = getattr(self, 'transfer_store', None)
        if not transfer_store:
            return []
        return transfer_store.list_live_transfer_watches()

    def persist_watch(self, watch: dict) -> dict:
        transfer_store = getattr(self, 'transfer_store', None)
        if not transfer_store:
            return watch
        return transfer_store.upsert_live_transfer_watch(
            watch_id=watch.get('id'),
            watch_type=watch.get('type'),
            source_link=watch.get('source_link'),
            target_link=watch.get('target_link'),
            include_comment=bool(watch.get('include_comment')),
            status=watch.get('status') or TransferStatus.PENDING,
            error_message=watch.get('error_message')
        )

    def set_live_watch_status(self, watch_id: str, status: str, error_message: str = None) -> None:
        if watch_id in self.web_pending_watches:
            self.web_pending_watches[watch_id]['status'] = status
            self.web_pending_watches[watch_id]['error_message'] = error_message
        transfer_store = getattr(self, 'transfer_store', None)
        if transfer_store:
            transfer_store.update_live_transfer_watch_status(
                watch_id=watch_id,
                status=status,
                error_message=error_message
            )

    def list_watches(self) -> list:
        watches_by_id = {
            watch.get('id'): watch
            for watch in self.persisted_watches()
            if watch.get('id')
        }
        for link in sorted(self.listen_download_chat):
            watch_id = self.download_watch_id(link)
            watches_by_id[watch_id] = {
                **watches_by_id.get(watch_id, {}),
                'id': watch_id,
                'type': 'download',
                'source_link': link,
                'target_link': None,
                'include_comment': False,
                'status': TransferStatus.RUNNING
            }
        for rule in sorted(self.listen_forward_chat):
            parsed = parse_forward_watch_rule(rule)
            watch_id = self.forward_watch_id(rule)
            watches_by_id[watch_id] = {
                **watches_by_id.get(watch_id, {}),
                'id': watch_id,
                'type': 'forward',
                'source_link': parsed.get('source_link'),
                'target_link': parsed.get('target_link'),
                'include_comment': bool(parsed.get('include_comment')),
                'status': TransferStatus.RUNNING
            }
        running_ids = set(watches_by_id)
        for watch_id, watch in sorted(self.web_pending_watches.items()):
            if watch_id not in running_ids:
                watches_by_id[watch_id] = watch
        return sorted(watches_by_id.values(), key=lambda watch: str(watch.get('id') or ''))

    def pending_watch_sources(self, watch_type: str) -> set:
        return {
            watch.get('source_link')
            for watch in self.web_pending_watches.values()
            if watch.get('type') == watch_type and watch.get('source_link')
        }

    def persisted_watch_sources(self, watch_type: str) -> set:
        return {
            watch.get('source_link')
            for watch in self.persisted_watches()
            if watch.get('type') == watch_type and watch.get('source_link')
        }

    def has_download_watch_source(self, source_link: str) -> bool:
        return (
            source_link in self.listen_download_chat
            or source_link in self.pending_watch_sources('download')
            or source_link in self.persisted_watch_sources('download')
        )

    def has_forward_watch_source(self, source_link: str) -> bool:
        running_sources = {
            parse_forward_watch_rule(rule).get('source_link')
            for rule in self.listen_forward_chat
        }
        return (
            source_link in running_sources
            or source_link in self.pending_watch_sources('forward')
            or source_link in self.persisted_watch_sources('forward')
        )

    def create_watch(self, payload: dict) -> dict:
        watch_type = payload.get('type')
        if watch_type == 'download':
            created = []
            for link in payload.get('source_links') or []:
                if self.has_forward_watch_source(link):
                    raise ValueError('watch_source_conflict')
                if self.has_download_watch_source(link):
                    raise ValueError('watch_already_exists')
                watch = {
                    'id': f'download:{link}',
                    'type': 'download',
                    'source_link': link,
                    'target_link': None,
                    'include_comment': False,
                    'status': TransferStatus.PENDING
                }
                watch = self.persist_watch(watch)
                self.web_pending_watches[watch['id']] = watch
                self.create_live_watch_operation('download', {'source_link': link})
                created.append(watch)
            return {'watches': created}
        if watch_type == 'forward':
            source_link = payload.get('source_link')
            target_link = payload.get('target_link')
            include_comment = bool(payload.get('include_comment'))
            if self.has_download_watch_source(source_link):
                raise ValueError('watch_source_conflict')
            rule = make_forward_watch_rule(source_link, target_link, include_comment)
            same_target_exists = any(
                parse_forward_watch_rule(existing).get('source_link') == source_link and
                parse_forward_watch_rule(existing).get('target_link') == target_link
                for existing in self.listen_forward_chat
            )
            same_persisted_exists = any(
                watch.get('type') == 'forward' and
                watch.get('source_link') == source_link and
                watch.get('target_link') == target_link
                for watch in self.persisted_watches()
            )
            same_pending_exists = any(
                watch.get('type') == 'forward' and
                watch.get('source_link') == source_link and
                watch.get('target_link') == target_link
                for watch in self.web_pending_watches.values()
            )
            if same_target_exists or same_persisted_exists or same_pending_exists:
                raise ValueError('watch_already_exists')
            watch = {
                'id': f'forward:{rule}',
                'type': 'forward',
                'source_link': source_link,
                'target_link': target_link,
                'include_comment': include_comment,
                'status': TransferStatus.PENDING
            }
            watch = self.persist_watch(watch)
            self.web_pending_watches[watch['id']] = watch
            self.create_live_watch_operation(
                'forward',
                {'source_link': source_link, 'target_link': target_link, 'include_comment': include_comment}
            )
            return {
                'watches': [watch]
            }
        raise ValueError('Unsupported watch type.')

    def create_live_watch_operation(self, watch_type: str, payload: dict) -> str:
        operation = self.submit_web_operation('watch', {'watch_type': watch_type, **payload})
        return operation['id']

    def delete_watch(self, watch_id: str) -> bool:
        watch_type, separator, value = watch_id.partition(':')
        if not separator:
            return False
        if watch_type == 'download':
            handler = self.listen_download_chat.get(value)
            if not handler:
                pending_deleted = self.web_pending_watches.pop(watch_id, None) is not None
                transfer_store = getattr(self, 'transfer_store', None)
                store_deleted = transfer_store.delete_live_transfer_watch(watch_id) if transfer_store else False
                return pending_deleted or store_deleted
            client = self.web_watch_handler_clients.pop(watch_id, None) or self.user or self.app.client
            client.remove_handler(handler)
            self.listen_download_chat.pop(value, None)
            self.web_pending_watches.pop(watch_id, None)
            transfer_store = getattr(self, 'transfer_store', None)
            if transfer_store:
                transfer_store.delete_live_transfer_watch(watch_id)
            log.info(f'已通过WebUI删除监听下载,频道链接:"{value}"。')
            return True
        if watch_type == 'forward':
            handler = self.listen_forward_chat.get(value)
            if not handler:
                pending_deleted = self.web_pending_watches.pop(watch_id, None) is not None
                transfer_store = getattr(self, 'transfer_store', None)
                store_deleted = transfer_store.delete_live_transfer_watch(watch_id) if transfer_store else False
                return pending_deleted or store_deleted
            client = self.web_watch_handler_clients.pop(watch_id, None) or self.user or self.app.client
            client.remove_handler(handler)
            self.listen_forward_chat.pop(value, None)
            self.web_pending_watches.pop(watch_id, None)
            transfer_store = getattr(self, 'transfer_store', None)
            if transfer_store:
                transfer_store.delete_live_transfer_watch(watch_id)
            log.info(f'已通过WebUI删除监听转发,转发规则:"{value}"。')
            return True
        return False

    def statistics(self) -> dict:
        return {
            'tables': {
                'link': {
                    'available': bool(DownloadTask.LINK_INFO),
                    'rows': len(DownloadTask.LINK_INFO)
                },
                'count': {
                    'available': bool(DownloadTask.LINK_INFO),
                    'rows': len(DownloadTask.LINK_INFO)
                },
                'upload': {
                    'available': bool(UploadTask.TASKS),
                    'rows': len(UploadTask.TASKS)
                }
            },
            'operations': list(self.web_operations.values())[-50:]
        }

    def export_table(self, table_type: str) -> dict:
        if table_type == 'link':
            exported = self.app.print_link_table(
                link_info=DownloadTask.LINK_INFO,
                export=True,
                only_export=True
            )
            folder = 'form' if is_docker() else 'DownloadRecordForm'
        elif table_type == 'count':
            exported = self.app.print_count_table(export=True, only_export=True)
            folder = 'form' if is_docker() else 'DownloadRecordForm'
        else:
            exported = self.app.print_upload_table(
                upload_tasks=UploadTask.TASKS,
                export=True,
                only_export=True
            )
            folder = 'form' if is_docker() else 'UploadRecordForm'
        return {
            'exported': bool(exported),
            'table_type': table_type,
            'directory': folder
        }

    def create_upload(self, payload: dict) -> dict:
        operation = self.submit_web_operation('upload', payload)
        return {'accepted': True, 'operation_id': operation['id']}

    def create_channel_download(self, payload: dict) -> dict:
        operation = self.submit_web_operation('channel_download', payload)
        return {'accepted': True, 'operation_id': operation['id']}

    def get_web_settings(self) -> dict:
        return {
            'user': {
                'config_path': self.app.config_path,
                'api_id': self.app.config.get('api_id'),
                'api_hash': self.app.config.get('api_hash'),
                'bot_token': self.app.config.get('bot_token'),
                'session_directory': self.app.config.get('session_directory'),
                'save_directory': self.app.config.get('save_directory'),
                'temp_directory': self.app.config.get('temp_directory'),
                'max_tasks': self.app.config.get('max_tasks'),
                'max_retries': self.app.config.get('max_retries'),
                'download_type': self.app.config.get('download_type'),
                'is_shutdown': self.app.config.get('is_shutdown'),
                'proxy': self.app.config.get('proxy')
            },
            'global': self.gc.config
        }

    def update_web_settings(self, payload: dict) -> dict:
        user_config = merge_allowed_settings(
            target=deepcopy(self.app.config),
            patch=payload.get('user', {}) if isinstance(payload, dict) else {},
            allowed={
                'api_id', 'api_hash', 'bot_token', 'session_directory', 'save_directory',
                'temp_directory', 'max_tasks', 'max_retries', 'download_type', 'is_shutdown',
                'proxy'
            }
        )
        global_config = merge_allowed_settings(
            target=deepcopy(self.gc.config),
            patch=payload.get('global', {}) if isinstance(payload, dict) else {},
            allowed={'notice', 'export_table', 'upload', 'forward_type', 'target_profiles'}
        )
        self.app.save_config(user_config)
        self.app.config = user_config
        self.app.download_type = user_config.get('download_type')
        self.app.is_shutdown = user_config.get('is_shutdown')
        self.app.max_download_task = (user_config.get('max_tasks') or {}).get('download', 1) or 1
        self.app.max_upload_task = (user_config.get('max_tasks') or {}).get('upload', 3) or 3
        self.app.max_download_retries = user_config.get('max_retries', {'download': 5}).get('download')
        self.app.max_upload_retries = (user_config.get('max_retries') or {}).get('upload', 3) or 3
        self.app.save_directory = user_config.get('save_directory')
        self.app.temp_directory = PARSE_ARGS.temp or (user_config.get('temp_directory') or self.app.TEMP_DIRECTORY)
        self.app.work_directory = PARSE_ARGS.session or (
                user_config.get('session_directory') or self.app.WORK_DIRECTORY)
        self.gc.save_config(global_config)
        self.download_upload_window.notify_limit_changed()
        return self.get_web_settings()

    def start_web_ui(self) -> None:
        if PARSE_ARGS.web is None:
            return
        self.transfer_store = TransferStore(directory=self.app.temp_directory)
        self.web_ui = WebUiServer(
            store=self.transfer_store,
            task_submitter=self.submit_web_task,
            settings_provider=self.get_web_settings,
            settings_updater=self.update_web_settings,
            operations=self,
            host=get_web_host_from_env(),
            port=get_web_port_from_env(),
            username=get_web_username_from_env(),
            password=get_web_password_from_env()
        )
        self.web_ui.start(open_browser=True)
        for task in self.transfer_store.list_tasks():
            if task.get('status') in (TransferStatus.PENDING, TransferStatus.RUNNING, TransferStatus.FAILURE):
                self.submit_web_task(int(task.get('id')))
        console.log(f'WebUI已启动: {self.web_ui.url}', style='#B1DB74')

    def env_save_directory(
            self,
            message: pyrogram.types.Message,
            source_folder: Optional[str] = None
    ) -> str:
        save_directory = self.app.save_directory
        for placeholder in SaveDirectoryPrefix():
            if placeholder in save_directory:
                if placeholder == SaveDirectoryPrefix.CHAT_ID:
                    save_directory = save_directory.replace(
                        placeholder,
                        str(getattr(getattr(message, 'chat'), 'id', 'UNKNOWN_CHAT_ID'))
                    )
                if placeholder == SaveDirectoryPrefix.CHAT_NAME:
                    save_directory = save_directory.replace(
                        placeholder,
                        validate_title(str(getattr(getattr(message, 'chat'), 'full_name', 'UNKNOWN_CHAT_NAME')))
                    )
                if placeholder == SaveDirectoryPrefix.MIME_TYPE:
                    for dtype in DownloadType():
                        if getattr(message, dtype, None):
                            save_directory = save_directory.replace(
                                placeholder,
                                dtype
                            )
        if source_folder:
            save_directory = os.path.join(save_directory, source_folder)
        return save_directory

    def get_final_save_directory(self, message, with_upload: Optional[dict] = None) -> str:
        source_folder = with_upload.get('source_folder') if isinstance(with_upload, dict) else None
        return self.env_save_directory(message, source_folder=source_folder)

    def get_final_file_path(self, message, file_name: str, with_upload: Optional[dict] = None) -> str:
        return os.path.join(self.get_final_save_directory(message, with_upload), file_name)

    async def prepare_download_upload_meta(self, with_upload: Optional[dict]) -> Optional[dict]:
        if not isinstance(with_upload, dict):
            return with_upload
        task_with_upload = with_upload.copy()
        if '_window_release' not in task_with_upload:
            task_with_upload['_window_release'] = await self.download_upload_window.acquire()
        return task_with_upload

    @staticmethod
    def release_download_upload_window(with_upload: Optional[dict]) -> None:
        if not isinstance(with_upload, dict):
            return
        release = with_upload.get('_window_release')
        if callable(release):
            release()
            with_upload['_window_release'] = None

    async def get_download_link_from_bot(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message,
            with_upload: Union[dict, None] = None
    ):
        link_meta: Union[dict, None] = await super().get_download_link_from_bot(client, message)
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
        links: Union[set, None] = self.__process_links(link=list(right_link))

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

    async def get_upload_link_from_bot(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message,
            delete: bool = False,
            save_directory: str = None,
            recursion: bool = False,
            valid_link_cache: dict = None
    ):
        link_meta: Union[dict, None] = await super().get_upload_link_from_bot(
            client=client,
            message=message,
            delete=delete,
            save_directory=save_directory,
            recursion=recursion,
            valid_link_cache=valid_link_cache
        )
        if link_meta is None:
            return None
        target_link: str = link_meta.get('target_link')
        valid_link_cache: dict = link_meta.get('valid_link_cache')
        upload_task = link_meta.get('upload_task')
        upload_task.with_delete = self.gc.upload_delete
        await self.uploader.create_upload_task(
            link=valid_link_cache.get(target_link, None) or target_link if valid_link_cache else target_link,
            upload_task=upload_task,
        )

    def refresh_transfer_task_counts(self, task_id: int) -> None:
        if not self.transfer_store:
            return
        self.transfer_store.refresh_task_counts(task_id)

    def create_transfer_item_for_download(
            self,
            task_with_upload: Optional[dict],
            chat_id: Union[str, int],
            link: str,
            message: pyrogram.types.Message,
            media_type: str,
            file_name: str,
            final_path: str,
            file_size: int
    ) -> Optional[dict]:
        if not isinstance(task_with_upload, dict):
            return task_with_upload
        source_chat_id = str(getattr(getattr(message, 'chat', None), 'id', chat_id))
        source_folder = task_with_upload.get('source_folder') or source_folder_from_message(
            message,
            fallback_chat_id=chat_id,
            fallback_link=link
        )
        final_path = os.path.join(os.path.dirname(final_path), source_folder, os.path.basename(final_path))
        task_with_upload['message_id'] = getattr(message, 'id', None)
        task_with_upload['source_chat_id'] = source_chat_id
        task_with_upload['source_link'] = getattr(message, 'link', None) or link
        task_with_upload['source_folder'] = source_folder
        task_with_upload['media_type'] = media_type
        task_with_upload['file_name'] = file_name
        task_with_upload['file_size'] = file_size
        if not self.transfer_store or not task_with_upload.get('task_id'):
            return task_with_upload
        task_id = int(task_with_upload.get('task_id'))
        item_id = self.transfer_store.add_item(
            task_id=task_id,
            source_chat_id=source_chat_id,
            source_message_id=getattr(message, 'id', None),
            source_link=getattr(message, 'link', None) or link,
            target_link=task_with_upload.get('link'),
            media_type=media_type,
            file_name=file_name,
            file_size=file_size,
            local_path=final_path,
            source_folder=source_folder,
            archive_status='pending' if task_with_upload.get('target_profile') == 'pikpak' else None,
            phase='downloading',
            status=TransferStatus.RUNNING
        )
        self.transfer_store.update_item_progress(
            item_id=item_id,
            phase='downloading',
            download_current=0,
            download_total=file_size
        )
        task_with_upload['item_id'] = item_id
        self.refresh_transfer_task_counts(task_id)
        return task_with_upload

    def transfer_download_progress(
            self,
            current: int,
            total: int,
            progress,
            task_id: int,
            with_upload: Optional[dict] = None
    ) -> None:
        self.pb.download(current, total, progress, task_id)
        if not self.transfer_store or not isinstance(with_upload, dict):
            return
        item_id = with_upload.get('item_id')
        if item_id:
            self.transfer_store.update_item_progress(
                item_id=int(item_id),
                phase='downloading',
                download_current=current,
                download_total=total
            )

    def record_transfer_download_success(
            self,
            with_upload: Optional[dict],
            message: pyrogram.types.Message,
            file_path: str
    ) -> None:
        if not self.transfer_store or not isinstance(with_upload, dict):
            return
        item_id = with_upload.get('item_id')
        file_size = with_upload.get('file_size')
        if file_size is None and os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
        if item_id:
            self.transfer_store.update_item(
                int(item_id),
                local_path=file_path,
                file_name=with_upload.get('file_name') or os.path.basename(file_path),
                file_size=file_size,
                phase='downloaded'
            )
            self.transfer_store.update_item_progress(
                int(item_id),
                phase='downloaded',
                download_current=file_size or 0,
                download_total=file_size or 0
            )
        source_chat_id = with_upload.get('source_chat_id')
        source_message_id = with_upload.get('message_id') or getattr(message, 'id', None)
        if source_chat_id and source_message_id and os.path.isfile(file_path):
            self.transfer_store.upsert_download_success_record(
                source_chat_id=str(source_chat_id),
                source_message_id=int(source_message_id),
                source_link=with_upload.get('source_link') or getattr(message, 'link', None),
                media_type=with_upload.get('media_type'),
                local_path=file_path,
                file_size=file_size,
                file_name=with_upload.get('file_name') or os.path.basename(file_path)
            )

    def try_reuse_transfer_download_record(
            self,
            task_with_upload: Optional[dict],
            message: pyrogram.types.Message,
            expected_size: int
    ) -> Optional[str]:
        if (
                not isinstance(task_with_upload, dict)
                or not self.transfer_store
                or not task_with_upload.get('source_chat_id')
                or not task_with_upload.get('message_id')
        ):
            return None
        record = self.transfer_store.get_download_success_record(
            source_chat_id=str(task_with_upload.get('source_chat_id')),
            source_message_id=int(task_with_upload.get('message_id')),
            expected_size=expected_size
        )
        if not record:
            return None
        local_path = record.get('local_path')
        item_id = task_with_upload.get('item_id')
        if item_id:
            self.transfer_store.update_item(
                int(item_id),
                local_path=local_path,
                file_name=record.get('file_name'),
                file_size=record.get('file_size'),
                phase='downloaded'
            )
            self.transfer_store.update_item_progress(
                int(item_id),
                phase='downloaded',
                download_current=expected_size,
                download_total=expected_size
            )
            self.transfer_store.add_event(
                int(task_with_upload.get('task_id')),
                f'Reused download success record: {record.get("file_name") or os.path.basename(local_path)}',
                item_id=int(item_id)
            )
        if self.uploader:
            try:
                media_group = message.get_media_group()
            except ValueError:
                media_group = None
            task_with_upload['media_group'] = media_group
            self.uploader.download_upload(
                with_upload=task_with_upload,
                file_path=local_path
            )
        else:
            self.release_download_upload_window(task_with_upload)
        return local_path

    def on_transfer_upload_progress(self, upload_task: UploadTask, current: int, total: int) -> None:
        if not self.transfer_store:
            return
        meta = getattr(upload_task, 'transfer_meta', {}) or {}
        item_id = meta.get('item_id')
        if not item_id:
            return
        self.transfer_store.update_item_progress(
            item_id=int(item_id),
            phase='uploading',
            upload_current=current,
            upload_total=total
        )

    def on_transfer_file_ready(self, file_path: str, with_upload: dict) -> int:
        if not self.transfer_store:
            return 0
        task_id = int(with_upload.get('task_id'))
        item_id = self.transfer_store.add_item(
            task_id=task_id,
            source_chat_id=with_upload.get('source_chat_id'),
            source_message_id=with_upload.get('message_id'),
            source_link=with_upload.get('source_link'),
            target_link=with_upload.get('link'),
            media_type=with_upload.get('media_type'),
            file_name=with_upload.get('file_name') or os.path.basename(file_path),
            file_size=with_upload.get('file_size') or (os.path.getsize(file_path) if os.path.isfile(file_path) else None),
            local_path=file_path,
            phase='uploading',
            status=TransferStatus.RUNNING
        )
        self.transfer_store.add_event(task_id, f'File ready for target upload: {os.path.basename(file_path)}', item_id=item_id)
        self.refresh_transfer_task_counts(task_id)
        return item_id

    def on_transfer_item_skipped(self, with_upload: dict, message: str) -> None:
        if not self.transfer_store or not isinstance(with_upload, dict) or not with_upload.get('task_id'):
            return
        task_id = int(with_upload.get('task_id'))
        item_id = self.transfer_store.add_item(
            task_id=task_id,
            source_chat_id=with_upload.get('source_chat_id'),
            source_message_id=with_upload.get('message_id'),
            source_link=with_upload.get('source_link'),
            target_link=with_upload.get('link'),
            media_type=with_upload.get('media_type'),
            file_name=with_upload.get('file_name'),
            file_size=with_upload.get('file_size'),
            phase='skipped',
            status=TransferStatus.SKIPPED
        )
        self.transfer_store.add_event(task_id, message, level='warning', item_id=item_id)
        self.refresh_transfer_task_counts(task_id)

    def on_transfer_item_failed(self, with_upload: dict, message: str) -> None:
        if not self.transfer_store or not isinstance(with_upload, dict) or not with_upload.get('task_id'):
            return
        task_id = int(with_upload.get('task_id'))
        item_id = self.transfer_store.add_item(
            task_id=task_id,
            source_chat_id=with_upload.get('source_chat_id'),
            source_message_id=with_upload.get('message_id'),
            source_link=with_upload.get('source_link'),
            target_link=with_upload.get('link'),
            media_type=with_upload.get('media_type'),
            file_name=with_upload.get('file_name'),
            file_size=with_upload.get('file_size'),
            phase='failure',
            status=TransferStatus.FAILURE,
            error_message=message
        )
        self.transfer_store.add_event(task_id, message, level='error', item_id=item_id)
        self.refresh_transfer_task_counts(task_id)

    def on_transfer_upload_status(self, upload_task: UploadTask) -> None:
        if not self.transfer_store:
            return
        meta = getattr(upload_task, 'transfer_meta', {}) or {}
        task_id = meta.get('task_id')
        item_id = meta.get('item_id')
        if not task_id or not item_id:
            return
        if upload_task.status == UploadStatus.SENT:
            self.transfer_store.update_item(item_id, status=TransferStatus.SUCCESS, phase='sent')
            self.transfer_store.add_event(task_id, f'Sent to target: {upload_task.file_name}', item_id=item_id)
            self.archive_pikpak_item(
                target_profile=meta.get('target_profile'),
                item_id=item_id,
                task_id=task_id,
                message=None,
                source_link=meta.get('source_link'),
                source_folder=meta.get('source_folder'),
                file_name=upload_task.file_name,
                file_size=getattr(upload_task, 'file_size', None),
                transferred_at=datetime.datetime.now(datetime.UTC).timestamp()
            )
        elif upload_task.status == UploadStatus.FAILURE:
            self.transfer_store.update_item(
                item_id,
                status=TransferStatus.FAILURE,
                phase='failure',
                error_message=upload_task.error_msg
            )
            self.transfer_store.add_event(task_id, f'Upload failed: {upload_task.error_msg}', level='error', item_id=item_id)
        self.refresh_transfer_task_counts(int(task_id))

    def build_transfer_upload_meta(self, task: dict, source_link: str = None, media_type: str = None) -> dict:
        source_link = source_link or task.get('source_link')
        return {
            'link': task.get('target_link'),
            'file_name': None,
            'with_delete': True if task.get('target_profile') == 'pikpak' else self.gc.upload_delete,
            'send_as_media_group': False if task.get('target_profile') == 'pikpak' else True,
            'task_id': task.get('id'),
            'source_link': source_link,
            'source_folder': source_folder_from_link(source_link),
            'target_profile': task.get('target_profile'),
            'media_type': media_type,
            'on_file_ready': self.on_transfer_file_ready,
            'status_callback': self.on_transfer_upload_status,
            'progress_callback': self.on_transfer_upload_progress,
            'skip_callback': self.on_transfer_item_skipped,
            'failure_callback': self.on_transfer_item_failed
        }

    def get_pikpak_archive_client(self):
        if getattr(self, 'pikpak_archive_client', None) is not None:
            return self.pikpak_archive_client
        profile = (getattr(getattr(self, 'gc', None), 'config', {}) or {}).get('target_profiles', {}).get('pikpak', {})
        self.pikpak_archive_client = build_pikpak_archive_client(profile.get('archive'))
        return self.pikpak_archive_client

    def archive_pikpak_item(
            self,
            target_profile: Optional[str],
            item_id: Optional[int],
            task_id: Optional[int],
            message,
            source_link: Optional[str],
            source_folder: Optional[str] = None,
            file_name: Optional[str] = None,
            file_size: Optional[int] = None,
            transferred_at: Optional[float] = None
    ):
        if target_profile != 'pikpak':
            return None
        folder = source_folder or source_folder_from_message(
            message,
            fallback_chat_id=getattr(getattr(message, 'chat', None), 'id', None),
            fallback_link=source_link
        )
        media_meta = self.get_message_media_target_limit_meta(message) if message is not None else None
        file_name = file_name or (media_meta or {}).get('file_name')
        file_size = file_size if file_size is not None else (media_meta or {}).get('file_size')
        if not file_name and (file_size is None or transferred_at is None):
            return None
        result = self.get_pikpak_archive_client().archive_file(
            source_folder=folder,
            file_name=file_name,
            file_size=file_size,
            transferred_at=transferred_at
        )
        archive_status = getattr(result, 'status', 'error')
        archive_path = getattr(result, 'archive_path', None)
        archive_message = getattr(result, 'message', '')
        archive_ok = bool(getattr(result, 'ok', False))
        if self.transfer_store and item_id:
            self.transfer_store.update_item(
                int(item_id),
                source_folder=folder,
                archive_status=archive_status,
                archive_path=archive_path,
                archive_error=None if archive_ok else archive_message
            )
        if self.transfer_store and task_id and archive_status != 'disabled':
            level = 'info' if archive_ok else 'warning'
            detail = archive_path or archive_message or archive_status
            self.transfer_store.add_event(
                int(task_id),
                f'PikPak archive {archive_status}: {detail}',
                level=level,
                item_id=int(item_id) if item_id else None
            )
        return result

    def fail_transfer_item(
            self,
            task_id: int,
            item_id: int,
            message: str
    ) -> None:
        self.transfer_store.update_item(
            item_id,
            phase='failure',
            status=TransferStatus.FAILURE,
            error_message=message
        )
        self.transfer_store.add_event(
            task_id,
            message,
            level='error',
            item_id=item_id
        )
        self.refresh_transfer_task_counts(task_id)

    def skip_empty_transfer_source_message(
            self,
            task: dict,
            origin_chat_id,
            source_link: str,
            message_id: Optional[int]
    ) -> int:
        task_id = int(task.get('id'))
        error_message = f'Telegram API returned an empty source message: {source_link}'
        item_id = self.transfer_store.add_item(
            task_id=task_id,
            source_chat_id=origin_chat_id,
            source_message_id=message_id,
            source_link=source_link,
            target_link=task.get('target_link'),
            media_type='empty',
            phase='skipped',
            status=TransferStatus.SKIPPED,
            error_message=error_message
        )
        self.transfer_store.add_event(
            task_id,
            error_message,
            level='warning',
            item_id=item_id
        )
        self.refresh_transfer_task_counts(task_id)
        return item_id

    def complete_forwarded_pikpak_item(
            self,
            task: dict,
            item_id: int,
            task_id: int,
            message,
            source_link: str,
            transferred_at: float
    ) -> bool:
        archive_result = self.archive_pikpak_item(
            target_profile=task.get('target_profile'),
            item_id=item_id,
            task_id=task_id,
            message=message,
            source_link=source_link,
            transferred_at=transferred_at
        )
        if (
                archive_result is not None
                and getattr(archive_result, 'status', None) != 'disabled'
                and not bool(getattr(archive_result, 'ok', False))
        ):
            archive_status = getattr(archive_result, 'status', 'error')
            archive_message = getattr(archive_result, 'message', '')
            error_message = f'PikPak archive {archive_status}: {archive_message or source_link}'
            self.fail_transfer_item(task_id, item_id, error_message)
            return False
        self.transfer_store.update_item(
            item_id,
            phase='forwarded',
            status=TransferStatus.SUCCESS,
            error_message=''
        )
        self.transfer_store.add_event(
            task_id,
            f'Direct forward succeeded: {source_link}',
            item_id=item_id
        )
        self.refresh_transfer_task_counts(task_id)
        return True

    def get_message_media_target_limit_meta(self, message) -> Optional[dict]:
        for dtype in DownloadType():
            media = getattr(message, dtype, None)
            if not media:
                continue
            file_size = getattr(media, 'file_size', None)
            if file_size is None:
                continue
            return {
                'media_type': dtype,
                'file_size': int(file_size),
                'file_name': getattr(media, 'file_name', None)
            }
        return None

    def get_task_target_size_limit_error(self, task: dict, message) -> Optional[dict]:
        target_profile = task.get('target_profile')
        limit = target_profile_limit(getattr(self, 'gc', None), target_profile)
        media_meta = self.get_message_media_target_limit_meta(message)
        if not media_meta or limit is None or media_meta.get('file_size') <= limit:
            return None
        return {
            **media_meta,
            'message': target_profile_size_error(target_profile, media_meta.get('file_size'), limit)
        }

    @staticmethod
    def is_pikpak_target(target_link: Optional[str], target_profile: Optional[str] = None) -> bool:
        return (
                str(target_profile or '').lower() == 'pikpak'
                or 'pikpak' in str(target_link or '').lower()
        )

    @staticmethod
    def forwarded_message_has_identity(forwarded_message) -> bool:
        if isinstance(forwarded_message, list):
            return any(getattr(message, 'id', None) is not None for message in forwarded_message)
        return getattr(forwarded_message, 'id', None) is not None

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
    def is_pikpak_ingest_success_message(message) -> bool:
        text = str(
            getattr(message, 'text', None)
            or getattr(message, 'caption', None)
            or ''
        ).lower()
        return any(keyword in text for keyword in (
            '保存成功',
            'save success',
            'saved successfully',
            'successfully saved'
        ))

    @staticmethod
    def is_pikpak_ingest_failure_message(message) -> bool:
        text = str(
            getattr(message, 'text', None)
            or getattr(message, 'caption', None)
            or ''
        ).lower()
        return any(keyword in text for keyword in (
            '保存失败',
            '转存失败',
            'failed',
            'error'
        ))

    async def wait_for_pikpak_ingest_confirmation(
            self,
            target_chat_id,
            forwarded_message=None,
            timeout_seconds: float = 15,
            poll_interval: float = 3
    ) -> bool:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_seconds
        if isinstance(forwarded_message, list):
            forwarded_message_ids = {
                int(getattr(message, 'id'))
                for message in forwarded_message
                if getattr(message, 'id', None) is not None
            }
        else:
            forwarded_message_ids = {
                int(getattr(forwarded_message, 'id'))
            } if getattr(forwarded_message, 'id', None) is not None else set()
        if not forwarded_message_ids:
            return False
        first_forwarded_message_id = min(forwarded_message_ids) if forwarded_message_ids else None
        while loop.time() < deadline:
            async for target_message in self.app.client.get_chat_history(target_chat_id, limit=10):
                target_message_id = getattr(target_message, 'id', None)
                if first_forwarded_message_id and target_message_id is not None:
                    if int(target_message_id) <= first_forwarded_message_id:
                        continue
                reply_to = getattr(target_message, 'reply_to_message', None)
                reply_to_id = getattr(reply_to, 'id', None)
                if forwarded_message_ids and reply_to_id is not None and int(reply_to_id) not in forwarded_message_ids:
                    continue
                if self.is_pikpak_ingest_success_message(target_message):
                    return True
                if self.is_pikpak_ingest_failure_message(target_message):
                    return False
            await asyncio.sleep(poll_interval)
        return False

    def fail_transfer_item_for_target_limit(
            self,
            task: dict,
            message,
            source_link: str,
            origin_chat_id,
            limit_error: dict
    ) -> int:
        task_id = int(task.get('id'))
        item_id = self.transfer_store.add_item(
            task_id=task_id,
            source_chat_id=origin_chat_id,
            source_message_id=getattr(message, 'id', None),
            source_link=source_link,
            target_link=task.get('target_link'),
            media_type=limit_error.get('media_type'),
            file_name=limit_error.get('file_name'),
            file_size=limit_error.get('file_size'),
            phase='failure',
            status=TransferStatus.FAILURE,
            error_message=limit_error.get('message')
        )
        self.transfer_store.add_event(task_id, limit_error.get('message'), level='error', item_id=item_id)
        self.refresh_transfer_task_counts(task_id)
        return item_id

    @staticmethod
    def transfer_single_link(source_link: str) -> str:
        return source_link if '?single' in source_link else f'{source_link}?single'

    async def create_web_transfer_fallback_download(
            self,
            task: dict,
            source_link: Optional[str] = None,
            message: Optional[pyrogram.types.Message] = None
    ) -> None:
        message_ids = message if message is not None else self.transfer_single_link(source_link)
        task_result = await self.create_download_task(
            message_ids=message_ids,
            retry=None,
            single_link=True,
            with_upload=self.build_transfer_upload_meta(task=task, source_link=source_link),
            diy_download_type=[_ for _ in DownloadType()]
        )
        if task_result.get('status') == DownloadStatus.FAILURE:
            error = task_result.get('e_code') or {}
            raise RuntimeError(error.get('error_msg') or error.get('all_member') or 'Failed to create transfer item.')

    async def transfer_message_to_web_target(
            self,
            task: dict,
            message,
            origin_chat_id,
            target_chat_id,
            source_link: str
    ) -> bool:
        message_id = getattr(message, 'id', None)
        if getattr(message, 'empty', False):
            self.skip_empty_transfer_source_message(
                task=task,
                origin_chat_id=origin_chat_id,
                source_link=source_link,
                message_id=message_id
            )
            return False
        limit_error = self.get_task_target_size_limit_error(task, message)
        if limit_error:
            self.fail_transfer_item_for_target_limit(
                task=task,
                message=message,
                source_link=source_link,
                origin_chat_id=origin_chat_id,
                limit_error=limit_error
            )
            return False
        while True:
            try:
                forwarded_message = await self.forward(
                    client=self.app.client,
                    message=message,
                    message_id=message_id,
                    origin_chat_id=origin_chat_id,
                    target_chat_id=target_chat_id,
                    target_link=task.get('target_link'),
                    download_upload=False,
                    done_notice=False,
                    ignore_type_filter=True,
                    archive_after_success=False
                )
                media_meta = self.get_message_media_target_limit_meta(message)
                task_id = int(task.get('id'))
                item_id = self.transfer_store.add_item(
                    task_id=task_id,
                    source_chat_id=origin_chat_id,
                    source_message_id=message_id,
                    source_link=source_link,
                    target_link=task.get('target_link'),
                    media_type='forward',
                    file_name=(media_meta or {}).get('file_name'),
                    file_size=(media_meta or {}).get('file_size'),
                    source_folder=source_folder_from_message(
                        message,
                        fallback_chat_id=origin_chat_id,
                        fallback_link=source_link
                    ),
                    archive_status='pending' if task.get('target_profile') == 'pikpak' and media_meta else None,
                    phase='forwarded',
                    status=TransferStatus.RUNNING
                )
                if self.is_pikpak_target(task.get('target_link'), task.get('target_profile')):
                    if not self.forwarded_message_has_identity(forwarded_message):
                        self.fail_transfer_item(
                            task_id,
                            item_id,
                            f'Direct forward did not produce a target message: {source_link}'
                        )
                        return False
                    confirmed = await self.wait_for_pikpak_ingest_confirmation(
                        target_chat_id=target_chat_id,
                        forwarded_message=forwarded_message
                    )
                    if not confirmed:
                        archive_result = self.archive_pikpak_item(
                            target_profile=task.get('target_profile'),
                            item_id=item_id,
                            task_id=task_id,
                            message=message,
                            source_link=source_link,
                            transferred_at=datetime.datetime.now(datetime.UTC).timestamp()
                        )
                        if bool(getattr(archive_result, 'ok', False)):
                            self.transfer_store.update_item(
                                item_id,
                                phase='forwarded',
                                status=TransferStatus.SUCCESS,
                                error_message=''
                            )
                            self.transfer_store.add_event(
                                task_id,
                                f'PikPak ingest confirmation recovered by archive: {source_link}',
                                item_id=item_id
                            )
                            self.refresh_transfer_task_counts(task_id)
                            return False
                        error_message = f'PikPak ingest confirmation timeout or failure: {source_link}'
                        self.fail_transfer_item(task_id, item_id, error_message)
                        return False
                    self.complete_forwarded_pikpak_item(
                        task=task,
                        item_id=item_id,
                        task_id=task_id,
                        message=message,
                        source_link=source_link,
                        transferred_at=datetime.datetime.now(datetime.UTC).timestamp()
                    )
                    return False
                self.transfer_store.update_item(
                    item_id,
                    phase='forwarded',
                    status=TransferStatus.SUCCESS,
                    error_message=''
                )
                self.transfer_store.add_event(
                    task_id,
                    f'Direct forward succeeded: {source_link}',
                    item_id=item_id
                )
                self.refresh_transfer_task_counts(task_id)
                return False
            except (FloodWait, FloodPremiumWait) as e:
                await self.wait_for_telegram_flood(e, task_id=int(task.get('id')), action='web transfer forward')
            except (ChatForwardsRestricted_400, ChatForwardsRestricted_406, MediaCaptionTooLong_400) as e:
                if not self.gc.download_upload:
                    raise
                fallback_link = getattr(message, 'link', None) or source_link
                self.transfer_store.add_event(
                    int(task.get('id')),
                    f'Direct forward fallback for {source_link}: {e}',
                    level='warning'
                )
                await self.create_web_transfer_fallback_download(
                    task=task,
                    source_link=fallback_link,
                    message=None if fallback_link else message
                )
                return True

    async def transfer_web_discussion_replies_to_target(
            self,
            task: dict,
            source_chat_id,
            source_message_id: int,
            target_chat_id,
            expected_total: int
    ) -> tuple[int, int]:
        task_id = int(task.get('id'))
        reply_count = 0
        fallback_count = 0
        try:
            async for comment in self.app.client.get_discussion_replies(
                    chat_id=source_chat_id,
                    message_id=source_message_id
            ):
                if not self.check_type(comment):
                    continue
                reply_count += 1
                self.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=expected_total + reply_count,
                    assignment_completed=False
                )
                comment_chat_id = getattr(getattr(comment, 'chat', None), 'id', source_chat_id)
                comment_link = getattr(comment, 'link', None)
                used_fallback = await self.transfer_message_to_web_target(
                    task=task,
                    message=comment,
                    origin_chat_id=comment_chat_id,
                    target_chat_id=target_chat_id,
                    source_link=comment_link
                )
                fallback_count += 1 if used_fallback else 0
        except (ValueError, AttributeError, MsgIdInvalid):
            pass
        return reply_count, fallback_count

    async def get_web_transfer_single_message(self, source_link: str):
        while True:
            try:
                meta = await get_message_by_link(
                    client=self.app.client,
                    link=self.transfer_single_link(source_link),
                    single_link=True
                )
                break
            except (FloodWait, FloodPremiumWait) as e:
                await self.wait_for_telegram_flood(e, action='load single transfer message')
        messages = meta.get('message') if isinstance(meta, dict) else None
        if isinstance(messages, list):
            return messages[0] if messages else None
        return messages

    async def get_web_transfer_range_message(self, chat_id, message_id: int, task_id: int):
        while True:
            try:
                return await self.app.client.get_messages(
                    chat_id=chat_id,
                    message_ids=message_id
                )
            except (FloodWait, FloodPremiumWait) as e:
                await self.wait_for_telegram_flood(e, task_id=task_id, action='load range transfer message')

    def skip_missing_web_transfer_range_message(
            self,
            task: dict,
            origin_chat_id,
            source_link: str,
            message_id: int
    ) -> None:
        task_id = int(task.get('id'))
        message_link = f'{source_link.rstrip("/")}/{message_id}'
        item_id = self.transfer_store.add_item(
            task_id=task_id,
            source_chat_id=origin_chat_id,
            source_message_id=message_id,
            source_link=message_link,
            target_link=task.get('target_link'),
            phase='skipped',
            status=TransferStatus.SKIPPED,
            error_message=f'Source message not found: {message_id}.'
        )
        self.transfer_store.add_event(
            task_id,
            f'Source message not found, skipped: {message_id}.',
            level='warning',
            item_id=item_id
        )
        self.refresh_transfer_task_counts(task_id)

    async def process_web_transfer_task(self, task_id: int) -> None:
        if not self.transfer_store:
            return
        task = self.transfer_store.get_task(task_id)
        if not task:
            return
        if task.get('status') not in (TransferStatus.PENDING, TransferStatus.RUNNING, TransferStatus.FAILURE):
            return
        self.transfer_store.update_task(task_id, status=TransferStatus.RUNNING, started=True)
        self.transfer_store.add_event(task_id, 'Transfer task started.')
        try:
            if not self.uploader:
                self.uploader = TelegramUploader(download_object=self)
            source_link = task.get('source_link')
            start_id = task.get('start_id')
            end_id = task.get('end_id')
            include_comment = bool(task.get('include_comment'))
            origin_meta = await parse_link(client=self.app.client, link=source_link)
            target_meta = await parse_link(client=self.app.client, link=task.get('target_link'))
            origin_chat_id = origin_meta.get('chat_id')
            target_chat_id = target_meta.get('chat_id')
            if not all([origin_chat_id, target_chat_id]):
                raise ValueError('Invalid source or target link.')
            fallback_count = 0
            if start_id is not None and end_id is not None:
                source_prefix = source_link.rstrip('/')
                expected_total = int(end_id) - int(start_id) + 1
                completed_message_ids = self.transfer_store.completed_source_message_ids(task_id)
                self.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=expected_total,
                    assignment_completed=False
                )
                for message_id in range(int(start_id), int(end_id) + 1):
                    latest_task = self.transfer_store.get_task(task_id)
                    if latest_task and latest_task.get('status') == TransferStatus.PAUSED:
                        self.transfer_store.add_event(task_id, f'Transfer task paused before message: {message_id}.')
                        return
                    if message_id in completed_message_ids:
                        continue
                    await self.wait_between_transfer_messages()
                    message = await self.get_web_transfer_range_message(origin_chat_id, message_id, task_id)
                    if not message:
                        self.skip_missing_web_transfer_range_message(
                            task=task,
                            origin_chat_id=origin_chat_id,
                            source_link=source_link,
                            message_id=message_id
                        )
                        continue
                    message_link = f'{source_prefix}/{getattr(message, "id", "")}'
                    used_fallback = await self.transfer_message_to_web_target(
                        task=task,
                        message=message,
                        origin_chat_id=origin_chat_id,
                        target_chat_id=target_chat_id,
                        source_link=message_link
                    )
                    fallback_count += 1 if used_fallback else 0
                    if include_comment:
                        reply_count, reply_fallback_count = await self.transfer_web_discussion_replies_to_target(
                            task=task,
                            source_chat_id=origin_chat_id,
                            source_message_id=message_id,
                            target_chat_id=target_chat_id,
                            expected_total=expected_total
                        )
                        expected_total += reply_count
                        fallback_count += reply_fallback_count
                self.transfer_store.add_event(
                    task_id,
                    f'Range transfer assigned: {start_id}-{end_id}. Fallback downloads: {fallback_count}.'
                )
                self.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=expected_total,
                    assignment_completed=True
                )
            else:
                self.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=1,
                    assignment_completed=False
                )
                message = await self.get_web_transfer_single_message(source_link)
                if not message:
                    raise RuntimeError('Failed to load transfer message.')
                completed_message_ids = self.transfer_store.completed_source_message_ids(task_id)
                message_id = getattr(message, 'id', None)
                fallback_count = 0
                expected_total = 1
                if message_id not in completed_message_ids:
                    fallback_count = 1 if await self.transfer_message_to_web_target(
                        task=task,
                        message=message,
                        origin_chat_id=origin_chat_id,
                        target_chat_id=target_chat_id,
                        source_link=source_link
                    ) else 0
                    if include_comment:
                        reply_count, reply_fallback_count = await self.transfer_web_discussion_replies_to_target(
                            task=task,
                            source_chat_id=origin_chat_id,
                            source_message_id=message_id,
                            target_chat_id=target_chat_id,
                            expected_total=1
                        )
                        fallback_count += reply_fallback_count
                        expected_total += reply_count
                        self.transfer_store.refresh_task_counts(
                            task_id,
                            expected_total=expected_total,
                            assignment_completed=False
                        )
                self.transfer_store.add_event(
                    task_id,
                    f'Single-message transfer assigned. Fallback downloads: {fallback_count}.'
                )
                self.transfer_store.refresh_task_counts(
                    task_id,
                    expected_total=expected_total,
                    assignment_completed=True
                )
        except Exception as e:
            self.transfer_store.update_task(
                task_id,
                status=TransferStatus.FAILURE,
                error_message=str(e),
                finished=True
            )
            self.transfer_store.add_event(task_id, f'Transfer task failed: {e}', level='error')

    async def process_web_operation(self, operation_id: str) -> None:
        operation = self.web_operations.get(operation_id)
        if not operation:
            return
        operation['status'] = TransferStatus.RUNNING
        operation['updated_at'] = TransferStore.utc_now()
        try:
            operation_type = operation.get('type')
            payload = operation.get('payload') or {}
            if operation_type == 'watch':
                await self.apply_web_watch(payload)
            elif operation_type == 'upload':
                await self.apply_web_upload(payload)
            elif operation_type == 'channel_download':
                await self.apply_web_channel_download(payload)
            else:
                raise ValueError(f'Unsupported WebUI operation: {operation_type}')
            operation['status'] = TransferStatus.SUCCESS
        except Exception as e:
            operation['status'] = TransferStatus.FAILURE
            operation['error_message'] = str(e)
            payload = operation.get('payload') or {}
            if operation.get('type') == 'watch':
                self.mark_pending_watch(payload, TransferStatus.FAILURE, str(e))
            log.exception(f'WebUI操作失败:{operation_id},{_t(KeyWord.REASON)}:"{e}"')
        finally:
            operation['updated_at'] = TransferStore.utc_now()

    async def restore_live_transfer_watches(self) -> None:
        for watch in self.persisted_watches():
            watch_id = watch.get('id')
            if not watch_id:
                continue
            if watch.get('type') == 'download' and watch.get('source_link') in self.listen_download_chat:
                continue
            if watch.get('type') == 'forward':
                rule = make_forward_watch_rule(
                    watch.get('source_link'),
                    watch.get('target_link'),
                    bool(watch.get('include_comment'))
                )
                if rule in self.listen_forward_chat:
                    continue
            self.web_pending_watches[watch_id] = {
                **watch,
                'status': TransferStatus.PENDING,
                'error_message': None
            }
            self.set_live_watch_status(watch_id, TransferStatus.PENDING)
            try:
                await self.apply_web_watch(self.watch_payload_from_record(watch))
            except Exception as e:
                self.mark_pending_watch(self.watch_payload_from_record(watch), TransferStatus.FAILURE, str(e))
                log.exception(f'恢复WebUI实时监听失败:{watch_id},{_t(KeyWord.REASON)}:"{e}"')

    async def apply_web_watch(self, payload: dict) -> None:
        watch_type = payload.get('watch_type')
        user_client = self.user or self.app.client
        if watch_type == 'download':
            link = payload.get('source_link')
            watch_id = self.download_watch_id(link)
            if link in self.listen_download_chat:
                self.set_live_watch_status(watch_id, TransferStatus.RUNNING)
                self.web_pending_watches.pop(watch_id, None)
                return
            chat = await user_client.get_chat(link)
            if getattr(chat, 'is_forum', False):
                raise PeerIdInvalid
            handler = MessageHandler(self.listen_download, filters=pyrogram.filters.chat(chat.id))
            self.listen_download_chat[link] = handler
            user_client.add_handler(handler)
            self.web_watch_handler_clients[watch_id] = user_client
            self.set_live_watch_status(watch_id, TransferStatus.RUNNING)
            self.web_pending_watches.pop(watch_id, None)
            log.info(f'已通过WebUI新增监听下载,频道链接:"{link}"。')
            return
        if watch_type == 'forward':
            source_link = payload.get('source_link')
            target_link = payload.get('target_link')
            include_comment = bool(payload.get('include_comment'))
            rule = make_forward_watch_rule(source_link, target_link, include_comment)
            watch_id = self.forward_watch_id(rule)
            if rule in self.listen_forward_chat:
                self.set_live_watch_status(watch_id, TransferStatus.RUNNING)
                self.web_pending_watches.pop(watch_id, None)
                return
            try:
                chat = await user_client.get_chat(source_link)
                if getattr(chat, 'is_forum', False):
                    raise PeerIdInvalid
                filters = pyrogram.filters.chat(chat.id)
            except PeerIdInvalid:
                meta = await parse_link(client=self.app.client, link=source_link)
                topic_id = meta.get('topic_id')
                chat_id = meta.get('chat_id')
                filters = pyrogram.filters.chat(chat_id) & pyrogram.filters.topic(topic_id) if topic_id else pyrogram.filters.chat(chat_id)
            handler = MessageHandler(self.listen_forward, filters=filters)
            self.listen_forward_chat[rule] = handler
            user_client.add_handler(handler)
            self.web_watch_handler_clients[watch_id] = user_client
            self.set_live_watch_status(watch_id, TransferStatus.RUNNING)
            self.web_pending_watches.pop(watch_id, None)
            comment_status = '包含评论区' if include_comment else '不包含评论区'
            log.info(f'已通过WebUI新增监听转发,转发规则:"{source_link} -> {target_link}",{comment_status}。')
            return
        raise ValueError('Unsupported watch type.')

    def mark_pending_watch(self, payload: dict, status: str, error_message: str = None) -> None:
        watch_type = payload.get('watch_type')
        if watch_type == 'download':
            watch_id = f'download:{payload.get("source_link")}'
        elif watch_type == 'forward':
            rule = make_forward_watch_rule(
                payload.get('source_link'),
                payload.get('target_link'),
                bool(payload.get('include_comment'))
            )
            watch_id = f'forward:{rule}'
        else:
            return
        self.set_live_watch_status(watch_id, status, error_message)

    async def apply_web_upload(self, payload: dict) -> None:
        if not self.uploader:
            self.uploader = TelegramUploader(download_object=self)
        upload_path = payload.get('path')
        target_link = payload.get('target_link')
        recursive = bool(payload.get('recursive'))
        if os.path.isdir(upload_path):
            if recursive:
                upload_files = [
                    os.path.join(root, filename)
                    for root, _dirs, files in os.walk(upload_path)
                    for filename in files
                ]
            else:
                upload_files = [
                    os.path.join(upload_path, filename)
                    for filename in os.listdir(upload_path)
                    if os.path.isfile(os.path.join(upload_path, filename))
                ]
        else:
            upload_files = [upload_path]
        if not upload_files:
            raise ValueError('Upload path contains no files.')
        for file_path in upload_files:
            file_size = os.path.getsize(file_path)
            upload_task = UploadTask(
                chat_id=None,
                file_path=file_path,
                file_id=self.app.client.rnd_id(),
                file_size=file_size,
                file_part=[],
                status=UploadStatus.PENDING,
                with_delete=self.gc.upload_delete
            )
            await self.uploader.create_upload_task(link=target_link, upload_task=upload_task)

    async def apply_web_channel_download(self, payload: dict) -> None:
        chat_link = payload.get('chat_link')
        meta = await parse_link(client=self.app.client, link=chat_link)
        chat_id = meta.get('chat_id')
        date_range = payload.get('date_range') or {}
        start_date = date_range.get('start_date')
        end_date = date_range.get('end_date')
        download_type = {
            dtype: dtype in set(payload.get('download_type') or [])
            for dtype in DownloadType()
        }
        keywords = payload.get('keywords') or []
        include_comment = bool(payload.get('include_comment'))
        filter_obj = Filter()
        links = []
        async for message in self.app.client.get_chat_history(chat_id=chat_id, reverse=True):
            if (
                    filter_obj.date_range(message, start_date, end_date)
                    and filter_obj.dtype(message, download_type)
                    and filter_obj.keyword_filter(message, keywords)
            ):
                links.append(message.link if getattr(message, 'link', None) else message)
                if include_comment:
                    try:
                        async for comment in self.app.client.get_discussion_replies(chat_id=chat_id, message_id=message.id):
                            if filter_obj.dtype(comment, download_type):
                                links.append(comment.link if getattr(comment, 'link', None) else comment)
                    except (ValueError, AttributeError, MsgIdInvalid):
                        pass
        for link in links:
            await self.create_download_task(
                message_ids=link,
                single_link=True,
                diy_download_type=[_ for _ in DownloadType()]
            )

    async def process_web_task_queue(self) -> None:
        self.start_next_web_transfer_task()
        while not self.web_task_queue.empty():
            if self.web_running_task and not self.web_running_task.done():
                break
            self.start_next_web_transfer_task()
            if self.web_running_task and not self.web_running_task.done():
                break
        while not self.web_operation_queue.empty():
            operation_id = await self.web_operation_queue.get()
            try:
                await self.process_web_operation(operation_id)
            finally:
                self.web_operation_queue.task_done()

    def start_next_web_transfer_task(self) -> None:
        if self.web_running_task and not self.web_running_task.done():
            return
        if self.web_running_task and self.web_running_task.done():
            self.finish_web_transfer_task(self.web_running_task_id, self.web_running_task)
        while not self.web_task_queue.empty():
            try:
                task_id = int(self.web_task_queue.get_nowait())
            except asyncio.QueueEmpty:
                return
            try:
                if not self.is_web_transfer_task_schedulable(task_id):
                    self.web_submitted_task_ids.discard(task_id)
                    continue
                runner = self.loop.create_task(self.process_web_transfer_task(task_id))
                self.web_running_task = runner
                self.web_running_task_id = task_id
                runner.add_done_callback(
                    lambda completed_task, completed_task_id=task_id: self.finish_web_transfer_task(
                        completed_task_id,
                        completed_task
                    )
                )
                return
            finally:
                self.web_task_queue.task_done()

    def is_web_transfer_task_schedulable(self, task_id: int) -> bool:
        if not self.transfer_store:
            return False
        task = self.transfer_store.get_task(task_id)
        return bool(
            task
            and task.get('status') in (TransferStatus.PENDING, TransferStatus.RUNNING, TransferStatus.FAILURE)
        )

    def finish_web_transfer_task(self, task_id: Optional[int], completed_task: asyncio.Task) -> None:
        if task_id is not None:
            self.web_submitted_task_ids.discard(task_id)
        if self.web_running_task is completed_task:
            self.web_running_task = None
            self.web_running_task_id = None
        if not completed_task.cancelled():
            error = completed_task.exception()
            if error:
                log.error(
                    f'WebUI转存任务执行失败:{task_id},{_t(KeyWord.REASON)}:"{error}"',
                    exc_info=(type(error), error, error.__traceback__)
                )
        if not self.web_task_queue.empty():
            self.loop.create_task(self.process_web_task_queue())

    @staticmethod
    async def __send_pay_qr(
            client: pyrogram.Client,
            chat_id: Union[int, str],
            load_name: str
    ) -> Union[list, str, None]:
        try:
            last_msg = await client.send_message(
                chat_id=chat_id,
                text=f'🚛请稍后{load_name}加载中. . .',
                link_preview_options=LINK_PREVIEW_OPTIONS
            )
            tasks = [client.send_photo(
                chat_id=chat_id,
                photo=Base64Image.base64_to_binary_io(Base64Image.pay),
                disable_notification=True
            ),
                client.edit_message_text(
                    chat_id=chat_id,
                    message_id=last_msg.id,
                    text=f'✅{load_name}加载成功!'
                )]
            await asyncio.gather(*tasks)
        except Exception as e:
            return str(e)

    async def start(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message
    ):
        self.last_client: pyrogram.Client = client
        self.last_message: pyrogram.types.Message = message
        if self.gc.config.get(BotCallbackText.NOTICE):
            chat_id = message.from_user.id
            await asyncio.gather(
                self.__send_pay_qr(
                    client=client,
                    chat_id=chat_id,
                    load_name='机器人'
                ),
                super().start(client, message),
                client.send_message(
                    chat_id=chat_id,
                    text='😊欢迎使用,您的支持是我持续更新的动力。',
                    link_preview_options=LINK_PREVIEW_OPTIONS)
            )

    async def callback_data(self, client: pyrogram.Client, callback_query: pyrogram.types.CallbackQuery):
        callback_data = await super().callback_data(client, callback_query)
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
        elif callback_data == BotCallbackText.PAY:
            res: Union[str, None] = await self.__send_pay_qr(
                client=client,
                chat_id=callback_query.from_user.id,  # v1.6.5 修复发送图片时chat_id错误问题。
                load_name='收款码'
            )
            MetaData.pay()
            if res:
                msg = '🥰🥰🥰\n收款「二维码」已发送至您的「终端」十分感谢您的支持!'
            else:
                msg = '🥰🥰🥰\n收款「二维码」已发送至您的「终端」与「对话框」十分感谢您的支持!'
            await callback_query.message.reply_text(msg)
        elif callback_data == BotCallbackText.BACK_HELP:
            meta: dict = await self.help()
            await callback_query.message.edit_text(meta.get('text'))
            await callback_query.message.edit_reply_markup(meta.get('keyboard'))
        elif callback_data == BotCallbackText.BACK_TABLE:
            meta: dict = await self.table()
            await callback_query.message.edit_text(meta.get('text'))
            await callback_query.message.edit_reply_markup(meta.get('keyboard'))
        elif callback_data in (BotCallbackText.DOWNLOAD, BotCallbackText.DOWNLOAD_UPLOAD):
            if not isinstance(self.cd.data, dict):
                return None
            meta: Union[dict, None] = self.cd.data.copy()
            self.cd.data = None
            origin_link: str = meta.get('origin_link')
            target_link: str = meta.get('target_link')
            start_id: Union[int, None] = meta.get('start_id')
            end_id: Union[int, None] = meta.get('end_id')
            if callback_data == BotCallbackText.DOWNLOAD:
                self.last_message.text = f'/download {origin_link} {start_id} {end_id}'
                await self.get_download_link_from_bot(
                    client=self.last_client,
                    message=self.last_message
                )
            elif callback_data == BotCallbackText.DOWNLOAD_UPLOAD:
                self.last_message.text = f'/download {origin_link} {start_id} {end_id}'
                await self.get_download_link_from_bot(
                    client=self.last_client,
                    message=self.last_message,
                    with_upload={
                        'link': target_link,
                        'file_name': None,
                        'with_delete': self.gc.upload_delete,
                        'send_as_media_group': True
                    }
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
            async def _toggle_button(_table_type):
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
                await _toggle_button('link')
            elif callback_data == BotCallbackText.TOGGLE_COUNT_TABLE:
                await _toggle_button('count')
            elif callback_data == BotCallbackText.TOGGLE_UPLOAD_TABLE:
                await _toggle_button('upload')
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
                self.download_upload_window.notify_limit_changed()
                await kb.toggle_upload_setting_button(global_config=self.gc.config)
            except ValueError:
                await callback_query.message.reply_text('下载后上传队列数量必须在1到5之间。')
            except Exception as e:
                await callback_query.message.reply_text(
                    '下载后上传队列设置失败\n(具体原因请前往终端查看报错信息)')
                log.error(f'下载后上传队列设置失败,{_t(KeyWord.REASON)}:"{e}"')
        elif callback_data in (BotCallbackText.UPLOAD_DOWNLOAD, BotCallbackText.UPLOAD_DOWNLOAD_DELETE):
            def _toggle_button(_param: str):
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

            try:
                if callback_data == BotCallbackText.UPLOAD_DOWNLOAD:
                    _toggle_button('download_upload')
                elif callback_data == BotCallbackText.UPLOAD_DOWNLOAD_DELETE:
                    _toggle_button('delete')
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
            def _toggle_download_type_button(_param: str):
                if _param in self.app.download_type:
                    if len(self.app.download_type) == 1:
                        raise ValueError
                    f_s = '禁用'
                    self.app.download_type.remove(_param)
                else:
                    f_s = '启用'
                    self.app.download_type.append(_param)

                f_p = f'已{f_s}"{_param}"类型的下载。'
                console.log(f_p, style='#FF4689')
                log.info(f_p)

            try:
                if callback_data == BotCallbackText.TOGGLE_DOWNLOAD_VIDEO:
                    _toggle_download_type_button('video')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_PHOTO:
                    _toggle_download_type_button('photo')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_AUDIO:
                    _toggle_download_type_button('audio')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_VOICE:
                    _toggle_download_type_button('voice')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_ANIMATION:
                    _toggle_download_type_button('animation')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_DOCUMENT:
                    _toggle_download_type_button('document')
                elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_VIDEO_NOTE:
                    _toggle_download_type_button('video_note')
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
            def _toggle_forward_type_button(_param: str):
                _forward_type: dict = self.gc.config.get('forward_type', self.gc.default_forward_type_nesting)
                _status: bool = self.gc.get_nesting_config(
                    default_nesting=self.gc.default_forward_type_nesting,
                    param='forward_type',
                    nesting_param=_param
                )
                if list(_forward_type.values()).count(True) == 1 and _status:
                    raise ValueError
                _forward_type[_param] = not _status
                f_s = '禁用' if _status else '启用'
                f_p = f'已{f_s}"{_param}"类型的转发。'
                console.log(f_p, style='#FF4689')
                log.info(f_p)

            try:
                if callback_data == BotCallbackText.TOGGLE_FORWARD_VIDEO:
                    _toggle_forward_type_button('video')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_PHOTO:
                    _toggle_forward_type_button('photo')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_AUDIO:
                    _toggle_forward_type_button('audio')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_VOICE:
                    _toggle_forward_type_button('voice')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_ANIMATION:
                    _toggle_forward_type_button('animation')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_DOCUMENT:
                    _toggle_forward_type_button('document')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_TEXT:
                    _toggle_forward_type_button('text')
                elif callback_data == BotCallbackText.TOGGLE_FORWARD_VIDEO_NOTE:
                    _toggle_forward_type_button('video_note')
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
                self.app.client.remove_handler(self.listen_download_chat.get(link))
                self.listen_download_chat.pop(link)
                watch_id = self.download_watch_id(link)
                self.web_watch_handler_clients.pop(watch_id, None)
                self.web_pending_watches.pop(watch_id, None)
                if self.transfer_store:
                    self.transfer_store.delete_live_transfer_watch(watch_id)
                await callback_query.message.edit_text(link)
                await callback_query.message.edit_reply_markup(
                    KeyboardButton.single_button(text=BotButton.ALREADY_REMOVE, callback_data=BotCallbackText.NULL)
                )
                p = f'已删除监听下载,频道链接:"{link}"。'
                console.log(p, style='#FF4689')
                log.info(f'{p}当前的监听下载信息:{self.listen_download_chat}')
                return None
            if not isinstance(self.cd.data, dict):
                return None
            meta: Union[dict, None] = self.cd.data.copy()
            self.cd.data = None
            link: str = meta.get('link')
            self.app.client.remove_handler(self.listen_forward_chat.get(link))
            self.listen_forward_chat.pop(link)
            watch_id = self.forward_watch_id(link)
            self.web_watch_handler_clients.pop(watch_id, None)
            self.web_pending_watches.pop(watch_id, None)
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
            log.info(f'{p}当前的监听转发信息:{self.listen_forward_chat}')
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

            def _get_update_time():
                _start_timestamp = self.download_chat_filter[chat_id]['date_range'][
                    'start_date']
                _end_timestamp = self.download_chat_filter[chat_id]['date_range']['end_date']
                _start_time = datetime.datetime.fromtimestamp(_start_timestamp) if _start_timestamp else '未定义'
                _end_time = datetime.datetime.fromtimestamp(_end_timestamp) if _end_timestamp else '未定义'
                return _start_time, _end_time

            def _get_format_dtype():
                _download_type = []
                for _dtype, _status in self.download_chat_filter[chat_id]['download_type'].items():
                    if _status:
                        _download_type.append(_t(_dtype))
                return ','.join(_download_type)

            def _get_format_keywords():
                _keywords = self.download_chat_filter[chat_id]['keyword']
                if not _keywords:
                    return '未定义'
                return ','.join(_keywords.keys())

            def _get_format_comment_status():
                _status = self.download_chat_filter[chat_id]['comment']
                return '开' if _status else '关'

            def _remove_chat_id(_chat_id):
                if _chat_id in self.download_chat_filter:
                    self.download_chat_filter.pop(_chat_id)
                    log.info(f'"{_chat_id}"已从{self.download_chat_filter}中移除。')

            def _filter_prompt():
                return (
                    f'💬下载频道:`{chat_id}`\n'
                    f'⏮️当前选择的起始日期为:{_get_update_time()[0]}\n'
                    f'⏭️当前选择的结束日期为:{_get_update_time()[1]}\n'
                    f'📝当前选择的下载类型为:{_get_format_dtype()}\n'
                    f'🔑当前匹配的关键词为:{_get_format_keywords()}\n'
                    f'👥包含评论区:{_get_format_comment_status()}'
                )

            async def _verification_time(_start_time, _end_time) -> bool:
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

            if callback_data in (BotCallbackText.DOWNLOAD_CHAT_ID, BotCallbackText.DOWNLOAD_CHAT_ID_CANCEL):  # 执行或取消任务。
                BotCallbackText.DOWNLOAD_CHAT_ID = 'download_chat_id'
                self.adding_keywords.clear()
                self.add_keyword_mode_handler(
                    chat_id=chat_id,
                    callback_query=callback_query,
                    callback_prompt=_filter_prompt,
                    enable=False
                )  # 关闭关键词输入handler。
                if callback_data == chat_id:
                    await self.download_chat(chat_id=chat_id, callback_query=callback_query)
                    _remove_chat_id(chat_id)
                elif callback_data == BotCallbackText.DOWNLOAD_CHAT_ID_CANCEL:
                    _remove_chat_id(chat_id)
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
                    start_time, end_time = _get_update_time()
                    if not await _verification_time(start_time, end_time):
                        return None
                # 返回或点击。
                await callback_query.message.edit_text(
                    text=_filter_prompt(),
                    reply_markup=kb.download_chat_filter_button(
                        self.download_chat_filter[chat_id][
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
                    text=f'📅选择{p_s_d}日期:\n{_filter_prompt()}'
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
                self.download_chat_filter[chat_id]['date_range']['adjust_step'] = new_step
                current_date = datetime.datetime.fromtimestamp(
                    self.download_chat_filter[chat_id]['date_range'][f'{dtype}_date']
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
                self.download_chat_filter[chat_id]['date_range'][date_type] = timestamp
                await callback_query.message.edit_text(
                    text=f'📅选择{p_s_d}日期:\n{_filter_prompt()}',
                    reply_markup=kb.time_keyboard(
                        dtype=dtype,
                        date=date,
                        adjust_step=self.download_chat_filter[chat_id]['date_range']['adjust_step']
                    )
                )
                log.info(f'日期设置,起始日期:{_get_update_time()[0]},结束日期:{_get_update_time()[1]}。')
            elif callback_data.startswith(('drop_keyword_', 'ignore_keyword')):
                if callback_data.startswith('drop_keyword_'):
                    parts = callback_data.split('_')
                    keyword = parts[-1]
                    _keyword = self.download_chat_filter.get(chat_id, {}).get('keyword', {})
                    _keyword.pop(keyword)
                    self.adding_keywords.remove(keyword)
                await callback_query.message.edit_text(
                    text=_filter_prompt(),
                    reply_markup=KeyboardButton.keyword_filter_button(self.adding_keywords)
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
                def _toggle_dtype_filter_button(_param: str):
                    _dtype: dict = self.download_chat_filter[chat_id]['download_type']
                    _status: bool = _dtype[_param]
                    if list(_dtype.values()).count(True) == 1 and _status:
                        raise ValueError
                    _dtype[_param] = not _status
                    f_s = '禁用' if _status else '启用'
                    f_p = f'已{f_s}"{_param}"类型用于/download_chat命令的下载。'
                    log.info(
                        f'{f_p}当前的/download_chat下载类型设置:{_dtype}')

                try:
                    if callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO:
                        _toggle_dtype_filter_button('video')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_PHOTO:
                        _toggle_dtype_filter_button('photo')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_AUDIO:
                        _toggle_dtype_filter_button('audio')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VOICE:
                        _toggle_dtype_filter_button('voice')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_ANIMATION:
                        _toggle_dtype_filter_button('animation')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_DOCUMENT:
                        _toggle_dtype_filter_button('document')
                    elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO_NOTE:
                        _toggle_dtype_filter_button('video_note')
                    await callback_query.message.edit_text(
                        text=_filter_prompt(),
                        reply_markup=kb.toggle_download_chat_type_filter_button(self.download_chat_filter)
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
                            text=_filter_prompt(),
                            reply_markup=kb.keyword_filter_button(self.adding_keywords)
                        )
                    except MessageNotModified:
                        pass
                    self.add_keyword_mode_handler(
                        enable=True,
                        chat_id=chat_id,
                        callback_query=callback_query,
                        callback_prompt=_filter_prompt
                    )  # 进入添加关键词模式。
                elif callback_data == BotCallbackText.CONFIRM_KEYWORD:
                    self.add_keyword_mode_handler(
                        enable=False,
                        chat_id=chat_id,
                        callback_query=callback_query,
                        callback_prompt=_filter_prompt
                    )
                    await callback_query.message.edit_text(
                        text=_filter_prompt(),
                        reply_markup=kb.download_chat_filter_button(self.download_chat_filter[chat_id]['comment'])
                    )
                elif callback_data == BotCallbackText.CANCEL_KEYWORD_INPUT:
                    self.adding_keywords.clear()
                    self.add_keyword_mode_handler(
                        enable=False,
                        chat_id=chat_id,
                        callback_query=callback_query,
                        callback_prompt=_filter_prompt
                    )
                    self.download_chat_filter[chat_id]['keyword'] = {}
                    await callback_query.message.edit_text(
                        text=_filter_prompt(),
                        reply_markup=kb.download_chat_filter_button(self.download_chat_filter[chat_id]['comment'])
                    )
            elif callback_data == BotCallbackText.TOGGLE_DOWNLOAD_CHAT_COMMENT:
                status: bool = self.download_chat_filter[chat_id]['comment']
                self.download_chat_filter[chat_id]['comment'] = not status
                await callback_query.message.edit_text(
                    text=_filter_prompt(),
                    reply_markup=kb.download_chat_filter_button(self.download_chat_filter[chat_id]['comment'])
                )

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
            archive_after_success: Optional[bool] = True
    ):
        try:
            if not ignore_type_filter and not self.check_type(message):
                console.log(
                    f'{_t(KeyWord.CHANNEL)}:"{origin_chat_id}",{_t(KeyWord.MESSAGE_ID)}:"{message_id}"'
                    f' -> '
                    f'{_t(KeyWord.CHANNEL)}:"{target_chat_id}",'
                    f'{_t(KeyWord.STATUS)}:{_t(KeyWord.FORWARD_SKIP)}。'
                )
                if done_notice:
                    await asyncio.create_task(
                        self.done_notice(
                            f'"{origin_chat_id}",{_t(KeyWord.MESSAGE_ID)}:{message_id}'
                            f' ➡️ '
                            f'"{target_chat_id}",{_t(KeyWord.FORWARD_SKIP)}(该类型已过滤)。'
                        )
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
            if archive_after_success and target_link and 'pikpak' in str(target_link).lower():
                self.archive_pikpak_item(
                    target_profile='pikpak',
                    item_id=None,
                    task_id=None,
                    message=message,
                    source_link=getattr(message, 'link', None),
                    source_folder=source_folder_from_message(
                        message,
                        fallback_chat_id=origin_chat_id,
                        fallback_link=getattr(message, 'link', None)
                    ),
                    transferred_at=datetime.datetime.now(datetime.UTC).timestamp()
                )
            return forwarded_message
        except (ChatForwardsRestricted_400, ChatForwardsRestricted_406):
            if not download_upload:
                if (
                        getattr(getattr(message, 'chat', None), 'is_creator', False) or
                        getattr(getattr(message, 'chat', None), 'is_admin', False)
                ) and (
                        getattr(getattr(message, 'from_user', None), 'id', -1) ==
                        getattr(getattr(client, 'me', None), 'id', None)
                ):
                    return None
                raise
            link = getattr(message, 'link', None)
            if not self.gc.download_upload:
                await self.bot.send_message(
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
            upload_meta = {
                'link': target_link,
                'file_name': None,
                'with_delete': self.gc.upload_delete,
                'send_as_media_group': True,
                'target_profile': 'pikpak' if 'pikpak' in str(target_link).lower() else None,
                'source_link': link,
                'source_folder': source_folder_from_message(
                    message,
                    fallback_chat_id=origin_chat_id,
                    fallback_link=link
                )
            }
            if link:
                self.last_message.text = f'/download {link}?single'
                await self.get_download_link_from_bot(
                    client=self.last_client,
                    message=self.last_message,
                    with_upload=upload_meta
                )
            else:
                await self.create_download_task(
                    message_ids=message,
                    retry=None,
                    single_link=True,
                    with_upload=upload_meta,
                    diy_download_type=[_ for _ in DownloadType()]
                )
            p = f'{_t(KeyWord.DOWNLOAD_AND_UPLOAD_TASK)}{_t(KeyWord.CHANNEL)}:"{target_chat_id}",{_t(KeyWord.LINK)}:"{link}"。'
            console.log(p, style='#FF4689')
            log.info(p)

    async def get_forward_link_from_bot(
            self, client: pyrogram.Client,
            message: pyrogram.types.Message
    ) -> Union[dict, None]:
        meta: Union[dict, None] = await super().get_forward_link_from_bot(client, message)
        if meta is None:
            return None
        self.last_client: pyrogram.Client = client
        self.last_message: pyrogram.types.Message = message
        origin_link: str = meta.get('origin_link')
        target_link: str = meta.get('target_link')
        start_id: int = meta.get('message_range')[0]
        end_id: int = meta.get('message_range')[1]
        include_comment: bool = bool(meta.get('include_comment'))
        last_message: Union[pyrogram.types.Message, None] = None
        loading = '🚛消息转发中,请稍候...'
        try:
            origin_meta: Union[dict, None] = await parse_link(
                client=self.app.client,
                link=origin_link
            )
            target_meta: Union[dict, None] = await parse_link(
                client=self.app.client,
                link=target_link
            )
            if not all([origin_meta, target_meta]):
                raise Exception('Invalid origin_link or target_link.')
            origin_chat_id = origin_meta.get('chat_id')
            target_chat_id = target_meta.get('chat_id')
            origin_chat: Union[pyrogram.types.Chat, None] = await get_chat_with_notify(
                user_client=self.app.client,
                bot_client=client,
                bot_message=message,
                chat_id=origin_chat_id,
                error_msg=f'⬇️⬇️⬇️原始频道不存在⬇️⬇️⬇️\n{origin_link}'
            )
            target_chat: Union[pyrogram.types.Chat, None] = await get_chat_with_notify(
                user_client=self.app.client,
                bot_client=client,
                bot_message=message,
                chat_id=target_chat_id,
                error_msg=f'⬇️⬇️⬇️目标频道不存在⬇️⬇️⬇️\n{target_link}'
            )
            if not all([origin_chat, target_chat]):
                return None
            my_id = await get_my_id(client)
            if target_chat.id == my_id:
                await client.send_message(
                    chat_id=message.from_user.id,
                    text='⚠️⚠️⚠️无法转发到此机器人⚠️⚠️⚠️',
                    reply_parameters=ReplyParameters(message_id=message.id),
                )
                return None
            record_id: list = []
            last_message = await client.send_message(
                chat_id=message.from_user.id,
                reply_parameters=ReplyParameters(message_id=message.id),
                link_preview_options=LINK_PREVIEW_OPTIONS,
                text=loading
            )
            async for i in self.app.client.get_chat_history(
                    chat_id=origin_chat.id,
                    offset_id=start_id,
                    max_id=end_id,
                    reverse=True
            ):
                try:
                    message_id = i.id
                    await self.forward(
                        client=client,
                        message=i,
                        message_id=message_id,
                        origin_chat_id=origin_chat_id,
                        target_chat_id=target_chat_id,
                        target_link=target_link,
                        download_upload=include_comment,
                        done_notice=False
                    )
                    if include_comment:
                        await self.forward_discussion_replies(
                            client=client,
                            source_chat_id=origin_chat_id,
                            source_message_id=message_id,
                            target_chat_id=target_chat_id,
                            target_link=target_link,
                            done_notice=False
                        )
                    record_id.append(message_id)
                except (ChatForwardsRestricted_400, ChatForwardsRestricted_406):
                    # TODO 存在内容保护限制时，文本类型的消息无需下载，而是直接send_message。
                    # TODO 存在内容保护限制时，下载后上传的消息转发时无法过滤类型。
                    self.cd.data = {
                        'origin_link': origin_link,
                        'target_link': target_link,
                        'start_id': start_id,
                        'end_id': end_id
                    }
                    channel = '@' + origin_chat.username if isinstance(
                        getattr(origin_chat, 'username'),
                        str) else ''
                    if not self.gc.download_upload:
                        await client.send_message(
                            chat_id=message.from_user.id,
                            text=f'⚠️⚠️⚠️无法转发⚠️⚠️⚠️\n`{origin_link}`\n{channel}存在内容保护限制。',
                            parse_mode=ParseMode.MARKDOWN,
                            reply_parameters=ReplyParameters(message_id=message.id),
                            reply_markup=KeyboardButton.restrict_forward_button()
                        )
                        return None
                    await client.send_message(
                        chat_id=message.from_user.id,
                        text=f'`{origin_link}`\n{channel}存在内容保护限制(已自动使用下载后上传)。\n⚠️通过`/forward`命令发送的下载后上传的消息,无法按照`[转发设置]`过滤类型。',
                        parse_mode=ParseMode.MARKDOWN,
                        reply_parameters=ReplyParameters(message_id=message.id)
                    )
                    self.last_message.text = f'/download {origin_link} {start_id} {end_id}'
                    await self.get_download_link_from_bot(
                        client=self.last_client,
                        message=self.last_message,
                        with_upload={
                            'link': target_link,
                            'file_name': None,
                            'with_delete': self.gc.upload_delete,
                            'send_as_media_group': True,
                            'target_profile': 'pikpak' if 'pikpak' in str(target_link).lower() else None,
                            'source_link': origin_link,
                            'source_folder': source_folder_from_link(origin_link)
                        }
                    )
                    break
                except Exception as e:
                    log.warning(
                        f'{_t(KeyWord.CHANNEL)}:"{origin_chat_id}",{_t(KeyWord.MESSAGE_ID)}:"{i.id}"'
                        f' -> '
                        f'{_t(KeyWord.CHANNEL)}:"{target_chat_id}",'
                        f'{_t(KeyWord.STATUS)}:{_t(KeyWord.FORWARD_FAILURE)},'
                        f'{_t(KeyWord.REASON)}:"{e}"')
                    await asyncio.create_task(
                        self.done_notice(
                            f'"{origin_chat_id}",{_t(KeyWord.MESSAGE_ID)}:{i.id}'
                            f' ➡️ '
                            f'"{target_chat_id}",{_t(KeyWord.FORWARD_FAILURE)}。'
                            f'\n(具体原因请前往终端查看报错信息)'
                        )
                    )
            else:
                if not record_id:
                    last_message = await self.safe_edit_message(
                        client=client,
                        message=message,
                        last_message_id=last_message.id,
                        text=safe_message(f'😅😅😅没有找到任何有效的消息😅😅😅')
                    )
                    return None
                invalid_id: list = []
                for i in range(start_id, end_id + 1):
                    if i not in record_id:
                        invalid_id.append(i)
                if invalid_id:
                    last_message = await self.safe_edit_message(
                        client=client,
                        message=message,
                        last_message_id=last_message.id,
                        text=safe_message(BotMessage.INVALID)
                    )
                    invalid_chat = await format_chat_link(
                        link=origin_link,
                        client=self.app.client,
                        topic=origin_chat.is_forum
                    )
                    invalid_chat = invalid_chat if invalid_chat else 'Your Saved Messages'
                    invalid_text = '\n'.join(f'{invalid_chat}/{i}' for i in invalid_id)
                    await safe_delete_message(last_message) if len(invalid_text) >= 3969 else None
                    last_message = await self.safe_edit_message(
                        client=client,
                        message=message,
                        last_message_id=last_message.id,
                        text=safe_message(f'{last_message.text}\n{invalid_text}')
                    )
                direct_url: str = await format_chat_link(
                    link=target_link,
                    client=self.app.client,
                    topic=target_chat.is_forum
                )
                last_message = await self.safe_edit_message(
                    client=client,
                    message=message,
                    last_message_id=last_message.id,
                    text=safe_message(
                        f'{last_message.text.strip(loading)}\n🌟🌟🌟转发任务已完成🌟🌟🌟\n(若设置了转发过滤规则,请前往终端查看转发记录,此处不做展示)'),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    BotButton.CLICK_VIEW,
                                    url=direct_url
                                )
                            ]
                        ]
                    ) if direct_url else None
                )
        except AttributeError as e:
            log.exception(f'转发时遇到错误,{_t(KeyWord.REASON)}:"{e}"')
            await client.send_message(
                chat_id=message.from_user.id,
                reply_parameters=ReplyParameters(message_id=message.id),
                text='⬇️⬇️⬇️出错了⬇️⬇️⬇️\n(具体原因请前往终端查看报错信息)'
            )
        except (ValueError, KeyError, UsernameInvalid, ChatWriteForbidden):
            msg: str = ''
            if any('/c' in link for link in (origin_link, target_link)):
                msg = '(私密频道或话题频道必须让当前账号加入转发频道,并且目标频道需有上传文件的权限)'
            await client.send_message(
                chat_id=message.from_user.id,
                reply_parameters=ReplyParameters(message_id=message.id),
                text='❌❌❌没有找到有效链接❌❌❌\n' + msg
            )
        except Exception as e:
            log.exception(f'转发时遇到错误,{_t(KeyWord.REASON)}:"{e}"')
            await client.send_message(
                chat_id=message.from_user.id,
                reply_parameters=ReplyParameters(message_id=message.id),
                text='⬇️⬇️⬇️出错了⬇️⬇️⬇️\n(具体原因请前往终端查看报错信息)'
            )
        finally:
            if last_message and getattr(last_message, 'text', '') == loading:
                await safe_delete_message(last_message)

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
        meta: Union[dict, None] = await super().on_listen(client, message)
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
            await self.create_download_task(message_ids=message.link, single_link=True)
        except Exception as e:
            log.exception(f'监听下载出现错误,{_t(KeyWord.REASON)}:"{e}"')

    def check_type(self, message: pyrogram.types.Message):
        for dtype, is_forward in self.gc.forward_type.items():
            if is_forward:
                result = getattr(message, dtype, None)
                if result:
                    return True
        return False

    async def forward_discussion_replies(
            self,
            client: pyrogram.Client,
            source_chat_id: Union[str, int],
            source_message_id: int,
            target_chat_id: Union[str, int],
            target_link: str,
            done_notice: Optional[bool] = True
    ) -> int:
        count = 0
        try:
            async for comment in self.app.client.get_discussion_replies(
                    chat_id=source_chat_id,
                    message_id=source_message_id
            ):
                if not self.check_type(comment):
                    continue
                comment_chat_id = getattr(getattr(comment, 'chat', None), 'id', source_chat_id)
                await self.forward(
                    client=client,
                    message=comment,
                    message_id=comment.id,
                    origin_chat_id=comment_chat_id,
                    target_chat_id=target_chat_id,
                    target_link=target_link,
                    download_upload=True,
                    done_notice=done_notice
                )
                count += 1
        except (ValueError, AttributeError, MsgIdInvalid):
            pass
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
            for m in self.listen_forward_chat:
                rule = parse_forward_watch_rule(m)
                listen_link = rule.get('source_link')
                target_link = rule.get('target_link')
                include_comment = bool(rule.get('include_comment'))
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
                    try:
                        media_group_ids = await message.get_media_group()
                        if not media_group_ids:
                            raise ValueError
                        if (
                                not self.gc.forward_type.get('video') or
                                not self.gc.forward_type.get('photo')
                        ):
                            log.warning('由于过滤了图片或视频类型的转发,将不再以媒体组方式发送。')
                            raise ValueError
                        if (
                                getattr(getattr(message, 'chat', None), 'is_creator', False) or
                                getattr(getattr(message, 'chat', None), 'is_admin', False)
                        ) and (
                                getattr(getattr(message, 'from_user', None), 'id', -1) ==
                                getattr(getattr(client, 'me', None), 'id', None)
                        ):
                            pass
                        elif (
                                getattr(getattr(message, 'chat', None), 'has_protected_content', False) or
                                getattr(getattr(message, 'sender_chat', None), 'has_protected_content', False) or
                                getattr(message, 'has_protected_content', False)
                        ):
                            raise ValueError
                        if not self.handle_media_groups.get(listen_chat_id):
                            self.handle_media_groups[listen_chat_id] = set()
                        if listen_chat_id in self.handle_media_groups and message.id not in self.handle_media_groups.get(
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
                            await self.forward(
                                client=client,
                                message=message,
                                message_id=message.id,
                                origin_chat_id=_listen_chat_id,
                                target_chat_id=_target_chat_id,
                                target_link=target_link,
                                download_upload=False,
                                media_group=sorted(ids)
                            )
                            if include_comment:
                                await self.forward_discussion_replies(
                                    client=client,
                                    source_chat_id=_listen_chat_id,
                                    source_message_id=message.id,
                                    target_chat_id=_target_chat_id,
                                    target_link=target_link
                                )
                            break
                        break
                    except ValueError:
                        pass
                    await self.forward(
                        client=client,
                        message=message,
                        message_id=message.id,
                        origin_chat_id=_listen_chat_id,
                        target_chat_id=_target_chat_id,
                        target_link=target_link,
                        download_upload=True
                    )
                    if include_comment:
                        await self.forward_discussion_replies(
                            client=client,
                            source_chat_id=_listen_chat_id,
                            source_message_id=message.id,
                            target_chat_id=_target_chat_id,
                            target_link=target_link
                        )
        except (ValueError, KeyError, UsernameInvalid, ChatWriteForbidden) as e:
            log.error(
                f'监听转发出现错误,{_t(KeyWord.REASON)}:{e}频道性质可能发生改变,包括但不限于(频道解散、频道名改变、频道类型改变、该账户没有在目标频道上传的权限、该账号被当前频道移除)。')
        except Exception as e:
            log.exception(f'监听转发出现错误,{_t(KeyWord.REASON)}:"{e}"')

    async def handle_forwarded_media(
            self,
            user_client: pyrogram.Client,
            user_message: pyrogram.types.Message
    ):
        chat_id = user_message.from_user.id
        message_id = user_message.id
        last_message = await self.bot.send_message(
            chat_id=chat_id,
            text=f'🔄正在处理转发内容`{message_id}`...'
        )
        try:
            task = await self.create_download_task(
                message_ids=user_message,
                diy_download_type=[_ for _ in DownloadType()],
                single_link=True
            )
            if task.get('status') == DownloadStatus.DOWNLOADING:
                await last_message.edit_text(text=f'✅已创建下载任务`{message_id}`。')
            else:
                error_msg = task.get('e_code', {}).get('error_msg', '未知错误。')
                await last_message.edit_text(text=f'❌❌❌无法创建下载任务`{message_id}`❌❌❌\n{error_msg}')
        except Exception as e:
            log.error(f'获取原始消息失败,{_t(KeyWord.REASON)}:"{e}"')
            await last_message.edit_text(text=f'❌❌❌无法创建下载任务`{message_id}`❌❌❌\n{e}')

    async def resume_download(
            self,
            message: pyrogram.types.Message,
            file_name: str,
            progress: Callable = None,
            progress_args: tuple = (),
            chunk_size: int = 1024 * 1024,
            compare_size: Union[int, None] = None  # 不为None时,将通过大小比对判断是否为完整文件。
    ) -> str:
        temp_path = f'{file_name}.temp'
        if os.path.exists(file_name) and compare_size:
            local_file_size: int = get_file_size(file_path=file_name)
            if compare_file_size(a_size=local_file_size, b_size=compare_size):
                console.log(
                    f'{_t(KeyWord.DOWNLOAD_TASK)}'
                    f'{_t(KeyWord.RESUME)}:"{file_name}",'
                    f'{_t(KeyWord.STATUS)}:{_t(KeyWord.ALREADY_EXIST)}')
                return file_name
            else:
                result: str = safe_replace(origin_file=file_name, overwrite_file=temp_path).get('e_code')
                log.warning(result) if result is not None else None
                log.warning(
                    f'不完整的文件"{file_name}",'
                    f'更改文件名作为缓存:[{file_name}]({get_file_size(file_name)}) -> [{temp_path}]({compare_size})。')
        if os.path.exists(temp_path) and compare_size:
            local_file_size: int = get_file_size(file_path=temp_path)
            if compare_file_size(a_size=local_file_size, b_size=compare_size):
                console.log(
                    f'{_t(KeyWord.DOWNLOAD_TASK)}'
                    f'{_t(KeyWord.RESUME)}:"{temp_path}",'
                    f'{_t(KeyWord.STATUS)}:{_t(KeyWord.ALREADY_EXIST)}')
                result: str = safe_replace(origin_file=temp_path, overwrite_file=file_name).get('e_code')
                log.warning(result) if result is not None else None
                return file_name
            elif local_file_size > compare_size:
                safe_delete(temp_path)
                log.warning(
                    f'错误的缓存文件"{temp_path}",'
                    f'已清除({_t(KeyWord.ERROR_SIZE)}:{local_file_size} > {_t(KeyWord.ACTUAL_SIZE)}:{compare_size})。')
        downloaded = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0  # 获取已下载的字节数。
        if downloaded == 0:
            mode = 'wb'
        else:
            mode = 'r+b'
            console.log(
                f'{_t(KeyWord.DOWNLOAD_TASK)}'
                f'{_t(KeyWord.RESUME)}:"{file_name}",'
                f'{_t(KeyWord.ERROR_SIZE)}:{MetaData.suitable_units_display(downloaded)}。')
        with open(file=temp_path, mode=mode) as f:
            skip_chunks: int = downloaded // chunk_size  # 计算要跳过的块数。
            f.seek(downloaded)
            while True:
                try:
                    async for chunk in self.app.client.stream_media(message=message, offset=skip_chunks):
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress(downloaded, *progress_args)
                    break
                except FileReferenceExpired as e:
                    log.warning(
                        f'文件引用已过期,正在重新获取消息以刷新引用,{_t(KeyWord.REASON)}:"{e}"')
                    chat_id = message.chat.id
                    message_id = message.id
                    try:
                        message = await self.app.client.get_messages(chat_id=chat_id, message_ids=message_id)
                        skip_chunks: int = downloaded // chunk_size
                        f.seek(downloaded)
                    except Exception as refresh_error:
                        log.error(f'重新获取消息失败,{_t(KeyWord.REASON)}:"{refresh_error}"')
                        break
                except (FloodWait, FloodPremiumWait) as e:
                    amount = e.value
                    console.log(
                        f'[{self.app.client.name}]下载请求频繁,要求等待{amount}秒后继续运行。',
                        style='#FF4689'
                    )
                    await asyncio.sleep(amount)
        if compare_size is None or compare_file_size(a_size=downloaded, b_size=compare_size):
            result: str = safe_replace(origin_file=temp_path, overwrite_file=file_name).get('e_code')
            log.warning(result) if result is not None else None
            log.info(
                f'"{temp_path}"下载完成,更改文件名:[{temp_path}]({get_file_size(temp_path)}) -> [{file_name}]({compare_size})')
        return file_name

    def get_media_meta(self, message: pyrogram.types.Message, dtype) -> Dict[str, Union[int, str]]:
        """获取媒体元数据。"""
        file_id: int = getattr(message, 'id')
        temp_file_path: str = self.app.get_temp_file_path(message, dtype)
        _sever_meta = getattr(message, dtype)
        sever_file_size: int = getattr(_sever_meta, 'file_size')
        file_name: str = split_path(temp_file_path).get('file_name')
        save_directory: str = os.path.join(self.env_save_directory(message), file_name)
        format_file_size: str = MetaData.suitable_units_display(sever_file_size)
        return {
            'file_id': file_id,
            'temp_file_path': temp_file_path,
            'sever_file_size': sever_file_size,
            'file_name': file_name,
            'save_directory': save_directory,
            'format_file_size': format_file_size
        }

    async def __add_task(
            self,
            chat_id: Union[str, int],
            link_type: str,
            link: str,
            message: Union[pyrogram.types.Message, list],
            retry: dict,
            with_upload: Optional[dict] = None,
            diy_download_type: Optional[list] = None
    ) -> None:
        retry_count = retry.get('count')
        retry_id = retry.get('id')
        if isinstance(message, list):
            for _message in message:
                if retry_count != 0:
                    if _message.id == retry_id:
                        await self.__add_task(chat_id, link_type, link, _message, retry, with_upload, diy_download_type)
                        break
                else:
                    await self.__add_task(chat_id, link_type, link, _message, retry, with_upload, diy_download_type)
        else:
            _task = None
            valid_dtype: str = next((_ for _ in DownloadType() if getattr(message, _, None)), None)  # 判断该链接是否为有支持的类型。
            download_type: list = diy_download_type if diy_download_type else self.app.download_type
            if valid_dtype in download_type:
                # 如果是匹配到的消息类型就创建任务。
                console.log(
                    f'{_t(KeyWord.DOWNLOAD_TASK)}'
                    f'{_t(KeyWord.CHANNEL)}:"{chat_id}",'  # 频道名。
                    f'{_t(KeyWord.LINK)}:"{link}",'  # 链接。
                    f'{_t(KeyWord.LINK_TYPE)}:{_t(link_type)}。'  # 链接类型。
                )
                while self.app.current_task_num >= self.app.max_download_task:  # v1.0.7 增加下载任务数限制。
                    await self.event.wait()
                    self.event.clear()
                file_id, temp_file_path, sever_file_size, file_name, save_directory, format_file_size = \
                    self.get_media_meta(
                        message=message,
                        dtype=valid_dtype).values()
                task_with_upload = await self.prepare_download_upload_meta(with_upload)
                task_with_upload = self.create_transfer_item_for_download(
                    task_with_upload=task_with_upload,
                    chat_id=chat_id,
                    link=link,
                    message=message,
                    media_type=valid_dtype,
                    file_name=file_name,
                    final_path=save_directory,
                    file_size=sever_file_size
                )
                if isinstance(task_with_upload, dict) and task_with_upload.get('source_folder'):
                    save_directory = self.get_final_file_path(message, file_name, task_with_upload)
                target_profile = task_with_upload.get('target_profile') if isinstance(task_with_upload, dict) else None
                limit = target_profile_limit(getattr(self, 'gc', None), target_profile)
                if limit is not None and sever_file_size > limit:
                    _error = target_profile_size_error(target_profile, sever_file_size, limit)
                    console.log(
                        f'{_t(KeyWord.DOWNLOAD_TASK)}'
                        f'{_t(KeyWord.FILE)}:"{file_name}",'
                        f'{_t(KeyWord.SIZE)}:{format_file_size},'
                        f'{_t(KeyWord.STATUS)}:{_t(DownloadStatus.FAILURE)}'
                        f'{_error}'
                    )
                    DownloadTask.set_error(link=link, key=file_name, value=_error)
                    callback = task_with_upload.get('failure_callback') if isinstance(task_with_upload, dict) else None
                    if callable(callback):
                        task_with_upload['message_id'] = getattr(message, 'id', None)
                        task_with_upload['media_type'] = valid_dtype
                        task_with_upload['file_name'] = file_name
                        task_with_upload['file_size'] = sever_file_size
                        callback(task_with_upload, _error)
                    self.release_download_upload_window(task_with_upload)
                    return None
                retry['id'] = file_id
                if is_file_duplicate(
                        save_directory=save_directory,
                        sever_file_size=sever_file_size
                ):  # 检测是否存在。
                    self.download_complete_callback(
                        sever_file_size=sever_file_size,
                        temp_file_path=temp_file_path,
                        link=link,
                        message=message,
                        file_name=file_name,
                        retry_count=retry_count,
                        file_id=file_id,
                        format_file_size=format_file_size,
                        task_id=None,
                        with_upload=task_with_upload,
                        diy_download_type=diy_download_type,
                        _future=save_directory
                    )
                elif self.try_reuse_transfer_download_record(
                        task_with_upload=task_with_upload,
                        message=message,
                        expected_size=sever_file_size
                ):
                    DownloadTask.COMPLETE_LINK.add(link)
                    if isinstance(task_with_upload, dict) and task_with_upload.get('task_id'):
                        self.refresh_transfer_task_counts(int(task_with_upload.get('task_id')))
                else:
                    console.log(
                        f'{_t(KeyWord.DOWNLOAD_TASK)}'
                        f'{_t(KeyWord.FILE)}:"{file_name}",'
                        f'{_t(KeyWord.SIZE)}:{format_file_size},'
                        f'{_t(KeyWord.TYPE)}:{_t(self.app.get_file_type(message, file_name, DownloadStatus.DOWNLOADING))},'
                        f'{_t(KeyWord.STATUS)}:{_t(DownloadStatus.DOWNLOADING)}。'
                    )
                    task_id = self.pb.progress.add_task(
                        description='📥',
                        filename=truncate_display_filename(file_name),
                        info=f'0.00B/{format_file_size}',
                        total=sever_file_size
                    )
                    _task = self.loop.create_task(
                        self.resume_download(
                            message=message,
                            file_name=temp_file_path,
                            progress=self.transfer_download_progress,
                            progress_args=(
                                sever_file_size,
                                self.pb.progress,
                                task_id,
                                task_with_upload
                            ),
                            compare_size=sever_file_size
                        )
                    )
                    MetaData.print_current_task_num(
                        prompt=_t(KeyWord.CURRENT_DOWNLOAD_TASK),
                        num=self.app.current_task_num
                    )
                    _task.add_done_callback(
                        partial(
                            self.download_complete_callback,
                            sever_file_size,
                            temp_file_path,
                            link,
                            message,
                            file_name,
                            retry_count,
                            file_id,
                            format_file_size,
                            task_id,
                            task_with_upload,
                            diy_download_type
                        )
                    )
            else:
                _error = '不支持或被忽略的类型(已取消)。'
                if isinstance(with_upload, dict):
                    with_upload['message_id'] = getattr(message, 'id', None)
                    with_upload['media_type'] = valid_dtype
                    callback = with_upload.get('skip_callback')
                    if callable(callback):
                        callback(with_upload, _error)
                try:
                    _, __, ___, file_name, ____, format_file_size = self.get_media_meta(
                        message=message,
                        dtype=valid_dtype
                    ).values()
                    if file_name:
                        console.log(
                            f'{_t(KeyWord.DOWNLOAD_TASK)}'
                            f'{_t(KeyWord.FILE)}:"{file_name}",'
                            f'{_t(KeyWord.SIZE)}:{format_file_size},'
                            f'{_t(KeyWord.TYPE)}:{_t(self.app.get_file_type(message, file_name, DownloadStatus.SKIP))},'
                            f'{_t(KeyWord.STATUS)}:{_t(DownloadStatus.SKIP)}。'
                        )
                        DownloadTask.set_error(link=link, key=file_name, value=_error.replace('。', ''))
                    else:
                        raise Exception('不支持或被忽略的类型。')
                except Exception as _:
                    DownloadTask.set_error(link=link, value=_error.replace('。', ''))
                    console.log(
                        f'{_t(KeyWord.DOWNLOAD_TASK)}'
                        f'{_t(KeyWord.CHANNEL)}:"{chat_id}",'  # 频道名。
                        f'{_t(KeyWord.LINK)}:"{link}",'  # 链接。
                        f'{_t(KeyWord.LINK_TYPE)}:{_error}'  # 链接类型。
                    )
            self.queue.put_nowait(_task) if _task else None

    def __check_download_finish(
            self,
            message: pyrogram.types.Message,
            sever_file_size: int,
            temp_file_path: str,
            save_directory: str,
            with_move: bool = True
    ) -> bool:
        """检测文件是否下完。"""
        temp_ext: str = '.temp'
        local_file_size: int = get_file_size(file_path=temp_file_path, temp_ext=temp_ext)
        format_local_size: str = MetaData.suitable_units_display(local_file_size)
        format_sever_size: str = MetaData.suitable_units_display(sever_file_size)
        _file_path: str = os.path.join(save_directory, split_path(temp_file_path).get('file_name'))
        file_path: str = _file_path[:-len(temp_ext)] if _file_path.endswith(temp_ext) else _file_path
        if compare_file_size(a_size=local_file_size, b_size=sever_file_size):
            if with_move:
                result: str = move_to_save_directory(
                    temp_file_path=temp_file_path,
                    save_directory=save_directory
                ).get('e_code')
                log.warning(result) if result is not None else None
            console.log(
                f'{_t(KeyWord.DOWNLOAD_TASK)}'
                f'{_t(KeyWord.FILE)}:"{file_path}",'
                f'{_t(KeyWord.SIZE)}:{format_local_size},'
                f'{_t(KeyWord.TYPE)}:{_t(self.app.get_file_type(message, temp_file_path, DownloadStatus.SUCCESS))},'
                f'{_t(KeyWord.STATUS)}:{_t(DownloadStatus.SUCCESS)}。',
            )
            return True
        console.log(
            f'{_t(KeyWord.DOWNLOAD_TASK)}'
            f'{_t(KeyWord.FILE)}:"{file_path}",'
            f'{_t(KeyWord.ERROR_SIZE)}:{format_local_size},'
            f'{_t(KeyWord.ACTUAL_SIZE)}:{format_sever_size},'
            f'{_t(KeyWord.TYPE)}:{_t(self.app.get_file_type(message, temp_file_path, DownloadStatus.FAILURE))},'
            f'{_t(KeyWord.STATUS)}:{_t(DownloadStatus.FAILURE)}。'
        )
        return False

    @DownloadTask.on_complete
    def download_complete_callback(
            self,
            sever_file_size,
            temp_file_path,
            link,
            message,
            file_name,
            retry_count,
            file_id,
            format_file_size,
            task_id,
            with_upload,
            diy_download_type,
            _future
    ):
        if task_id is None:
            if retry_count == 0:
                console.log(
                    f'{_t(KeyWord.DOWNLOAD_TASK)}'
                    f'{_t(KeyWord.ALREADY_EXIST)}:"{_future}"'
                )
                console.log(
                    f'{_t(KeyWord.DOWNLOAD_TASK)}'
                    f'{_t(KeyWord.FILE)}:"{file_name}",'
                    f'{_t(KeyWord.SIZE)}:{format_file_size},'
                    f'{_t(KeyWord.TYPE)}:{_t(self.app.get_file_type(message, file_name, DownloadStatus.SKIP))},'
                    f'{_t(KeyWord.STATUS)}:{_t(DownloadStatus.SKIP)}。', style='#e6db74'
                )
                DownloadTask.COMPLETE_LINK.add(link)
                self.record_transfer_download_success(
                    with_upload=with_upload,
                    message=message,
                    file_path=self.get_final_file_path(message, file_name, with_upload)
                )
                if self.uploader:
                    if with_upload and isinstance(with_upload, dict):
                        try:
                            media_group = message.get_media_group()
                        except ValueError:
                            media_group = None
                        with_upload['message_id'] = message.id
                        with_upload['media_group'] = media_group
                        self.uploader.download_upload(
                            with_upload=with_upload,
                            file_path=self.get_final_file_path(message, file_name, with_upload)
                        )
                else:
                    self.release_download_upload_window(with_upload)
            else:
                self.release_download_upload_window(with_upload)
        else:
            self.app.current_task_num -= 1
            self.event.set()  # v1.3.4 修复重试下载被阻塞的问题。
            if self.__check_download_finish(
                    message=message,
                    sever_file_size=sever_file_size,
                    temp_file_path=temp_file_path,
                    save_directory=self.get_final_save_directory(message, with_upload),
                    with_move=True
            ):
                final_path = self.get_final_file_path(message, file_name, with_upload)
                self.record_transfer_download_success(
                    with_upload=with_upload,
                    message=message,
                    file_path=final_path
                )
                MetaData.print_current_task_num(
                    prompt=_t(KeyWord.CURRENT_DOWNLOAD_TASK),
                    num=self.app.current_task_num
                )
                if self.uploader:
                    if with_upload and isinstance(with_upload, dict):
                        try:
                            media_group = message.get_media_group()
                        except ValueError:
                            media_group = None
                        with_upload['message_id'] = message.id
                        with_upload['media_group'] = media_group
                        self.uploader.download_upload(
                            with_upload=with_upload,
                            file_path=final_path
                        )
                else:
                    self.release_download_upload_window(with_upload)
                self.queue.task_done()
            else:
                if retry_count < self.app.max_download_retries:
                    retry_count += 1
                    task = self.loop.create_task(
                        self.create_download_task(
                            message_ids=link if isinstance(link, str) else message,
                            retry={'id': file_id, 'count': retry_count},
                            with_upload=with_upload,
                            diy_download_type=diy_download_type
                        )
                    )
                    task.add_done_callback(
                        partial(
                            self.__retry_call,
                            f'{_t(KeyWord.RE_DOWNLOAD)}:"{file_name}",'
                            f'{_t(KeyWord.RETRY_TIMES)}:{retry_count}/{self.app.max_download_retries}。'
                        )
                    )
                else:
                    _error = f'(达到最大重试次数:{self.app.max_download_retries}次)。'
                    console.log(
                        f'{_t(KeyWord.DOWNLOAD_TASK)}'
                        f'{_t(KeyWord.FILE)}:"{file_name}",'
                        f'{_t(KeyWord.SIZE)}:{format_file_size},'
                        f'{_t(KeyWord.TYPE)}:{_t(self.app.get_file_type(message, file_name, DownloadStatus.FAILURE))},'
                        f'{_t(KeyWord.STATUS)}:{_t(DownloadStatus.FAILURE)}'
                        f'{_error}'
                    )
                    DownloadTask.set_error(link=link, key=file_name, value=_error.replace('。', ''))
                    self.bot_task_link.discard(link)
                    callback = with_upload.get('failure_callback') if isinstance(with_upload, dict) else None
                    if callable(callback):
                        with_upload['message_id'] = getattr(message, 'id', None)
                        callback(with_upload, _error)
                    self.release_download_upload_window(with_upload)
                    self.queue.task_done()
                link, file_name = None, None
            self.pb.progress.remove_task(task_id=task_id)
        return link, file_name

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

                if (_filter.date_range(message, start_date, end_date) and
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

    @DownloadTask.on_create_task
    async def create_download_task(
            self,
            message_ids: Union[pyrogram.types.Message, str],
            retry: Union[dict, None] = None,
            single_link: bool = False,
            with_upload: Union[dict, None] = None,
            diy_download_type: Optional[list] = None
    ) -> dict:
        retry = retry if retry else {'id': -1, 'count': 0}
        diy_download_type = [_ for _ in DownloadType()] if with_upload else diy_download_type
        try:
            if isinstance(message_ids, pyrogram.types.Message):
                chat_id = message_ids.chat.id
                meta: dict = {
                    'link_type': LinkType.SINGLE,
                    'chat_id': chat_id,
                    'message': message_ids,
                    'member_num': 1
                }
                link = message_ids.link if message_ids.link else message_ids.id
            else:
                meta: dict = await get_message_by_link(
                    client=self.app.client,
                    link=message_ids,
                    single_link=single_link
                )
                link = message_ids

            link_type, chat_id, message, member_num = meta.values()
            DownloadTask.set(link, 'link_type', link_type)
            DownloadTask.set(link, 'member_num', member_num)
            await self.__add_task(chat_id, link_type, link, message, retry, with_upload, diy_download_type)
            return {
                'chat_id': chat_id,
                'member_num': member_num,
                'link_type': link_type,
                'status': DownloadStatus.DOWNLOADING,
                'e_code': None
            }
        except UnicodeEncodeError as e:
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e),
                    'error_msg':
                        '频道标题存在特殊字符,请移步终端下载'
                }
            }
        except MsgIdInvalid as e:
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e),
                    'error_msg':
                        '消息不存在,可能已删除'
                }
            }
        except UsernameInvalid as e:
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e),
                    'error_msg':
                        '频道用户名无效,该链接的频道用户名可能已更改或频道已解散'
                }
            }
        except ChannelInvalid as e:
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e),
                    'error_msg':
                        '频道可能为私密频道或话题频道,请让当前账号加入该频道后再重试'
                }
            }
        except ChannelPrivate_400 as e:
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e),
                    'error_msg':
                        '频道可能为私密频道或话题频道,当前账号可能已不在该频道,请让当前账号加入该频道后再重试'
                }
            }
        except ChannelPrivate_406 as e:
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e),
                    'error_msg':
                        '频道为私密频道,无法访问'
                }
            }
        except BotMethodInvalid as e:
            res: bool = safe_delete(file_p_d=os.path.join(self.app.DIRECTORY_NAME, 'sessions'))
            error_msg: str = '已删除旧会话文件' if res else '请手动删除软件目录下的sessions文件夹'
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e),
                    'error_msg':
                        '检测到使用了「bot_token」方式登录了主账号的行为,'
                        f'{error_msg},重启软件以「手机号码」方式重新登录'
                }
            }
        except ValueError as e:
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e),
                    'error_msg': '没有找到有效链接'
                }
            }
        except UsernameNotOccupied as e:
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e), 'error_msg': '频道不存在'
                }
            }
        except Exception as e:
            log.exception(e)
            return {
                'chat_id': None,
                'member_num': 0,
                'link_type': None,
                'status': DownloadStatus.FAILURE,
                'e_code': {
                    'all_member': str(e),
                    'error_msg': '未收录到的错误'
                }
            }

    def __process_links(self, link: Union[str, list]) -> Union[set, None]:
        """将链接(文本格式或链接)处理成集合。"""
        start_content: str = 'https://t.me/'
        links: set = set()
        if isinstance(link, str):
            if link.endswith('.txt') and os.path.isfile(link):
                with open(file=link, mode='r', encoding='UTF-8') as _:
                    _links: list = [content.strip() for content in _.readlines()]
                for i in _links:
                    if i.startswith(start_content):
                        links.add(i)
                        self.bot_task_link.add(i)
                    elif i == '' or '#':
                        continue
                    else:
                        log.warning(f'"{i}"是一个非法链接,{_t(KeyWord.STATUS)}:{_t(DownloadStatus.SKIP)}。')
            elif link.startswith(start_content):
                links.add(link)
        elif isinstance(link, list):
            for i in link:
                _link: Union[set, None] = self.__process_links(link=i)
                if _link is not None:
                    links.update(_link)
        if links:
            return links
        elif PARSE_ARGS.web is not None:
            console.log('🔗 WebUI模式未配置初始链接,等待浏览器创建转存任务。', style='#B1DB74')
            return None
        elif not self.app.bot_token:
            console.log('🔗 没有找到有效链接,程序已退出。', style='#FF4689')
            sys.exit(1)
        else:
            console.log('🔗 没有找到有效链接。', style='#FF4689')
            return None

    def __retry_call(self, notice, _future):
        self.queue.task_done()
        console.log(notice, style='#FF4689')

    async def __download_media_from_links(self) -> None:
        self.start_web_ui()
        await self.app.client.start(use_qr=False)
        self.my_id = await get_my_id(self.app.client)
        await self.restore_live_transfer_watches()
        self.pb.progress.start()  # v1.1.8修复登录输入手机号不显示文本问题。
        self.is_running = True
        self.running_log.add(self.is_running)
        if self.app.bot_token is not None:
            result = await self.start_bot(
                self.app,
                self.app.client,
                pyrogram.Client(
                    name=self.BOT_NAME,
                    api_hash=self.app.api_hash,
                    api_id=self.app.api_id,
                    bot_token=self.app.bot_token,
                    workdir=self.app.work_directory,
                    proxy=self.app.proxy if self.app.enable_proxy else None,
                    sleep_threshold=SLEEP_THRESHOLD
                )
            )
            console.log(result, style='#B1DB74' if self.is_bot_running else '#FF4689')
            if self.is_bot_running:
                self.uploader = TelegramUploader(download_object=self)
                self.cd = CallbackData()
                if self.gc.upload_delete:
                    console.log(
                        f'在使用转发(/forward)、监听转发(/listen_forward)、上传(/upload)、递归上传(/upload_r)时:\n'
                        f'当检测到"受限转发"时,自动采用"下载后上传"的方式,并在完成后删除本地文件。\n'
                        f'如需关闭,前往机器人[帮助页面]->[设置]->[上传设置]进行修改。\n',
                        style='#FF4689'
                    )
        if self.web_ui and not self.uploader:
            self.uploader = TelegramUploader(download_object=self)
        links: Union[set, None] = self.__process_links(link=self.app.links)
        # 将初始任务添加到队列中。
        [await self.loop.create_task(self.create_download_task(message_ids=link, retry=None)) for link in
         sorted(links)] if links else None
        # 处理队列中的任务与机器人事件。
        while not self.queue.empty() or self.is_bot_running or self.web_ui:
            await self.process_web_task_queue()
            if self.queue.empty():
                await asyncio.sleep(0.5)
                continue
            result = await self.queue.get()
            try:
                await result
            except PermissionError as e:
                log.error(
                    '临时文件无法移动至下载路径:\n'
                    '1.可能存在使用网络路径、挂载硬盘行为(本软件不支持);\n'
                    '2.可能存在多开软件时,同时操作同一文件或目录导致冲突;\n'
                    '3.由于软件设计缺陷,没有考虑到不同频道文件名相同的情况(若调整将会导致部分用户更新后重复下载已有文件),当保存路径下文件过多时,可能恰巧存在相同文件名的文件,导致相同文件名无法正常移动,故请定期整理归档下载链接与保存路径下的文件。'
                    f'{_t(KeyWord.REASON)}:"{e}"')
        # 等待所有任务完成。
        await self.queue.join()
        await self.app.client.stop() if self.app.client.is_connected else None

    def run(self) -> None:
        record_error: bool = False
        try:
            MetaData.print_helper()
            MetaData.print_meta()
            self.app.print_env_table(self.app)
            self.app.print_config_table(self.app)
            self.loop.run_until_complete(self.__download_media_from_links())
        except KeyError as e:
            record_error: bool = True
            if str(e) == '0':
                log.error('「网络」或「代理问题」,在确保当前网络连接正常情况下检查:\n「VPN」是否可用,「软件代理」是否配置正确。')
                console.print(Issues.PROXY_NOT_CONFIGURED)
                raise SystemExit(1)
            log.exception(f'运行出错,{_t(KeyWord.REASON)}:"{e}"')
        except BadMsgNotification as e:
            record_error: bool = True
            if str(e) in (str(BadMsgNotification(16)), str(BadMsgNotification(17))):
                console.print(Issues.SYSTEM_TIME_NOT_SYNCHRONIZED)
                raise SystemExit(1)
            log.exception(f'运行出错,{_t(KeyWord.REASON)}:"{e}"')
        except (SessionRevoked, AuthKeyUnregistered, SessionExpired, Unauthorized) as e:
            log.error(f'登录时遇到错误,{_t(KeyWord.REASON)}:"{e}"')
            res: bool = safe_delete(file_p_d=os.path.join(self.app.DIRECTORY_NAME, 'sessions'))
            record_error: bool = True
            if res:
                log.warning('账号已失效,已删除旧会话文件,请重启软件。')
            else:
                log.error('账号已失效,请手动删除软件目录下的sessions文件夹后重启软件。')
        except (ConnectionError, TimeoutError) as e:
            record_error: bool = True
            if not self.app.enable_proxy:
                log.error(f'网络连接失败,请尝试配置代理,{_t(KeyWord.REASON)}:"{e}"')
                console.print(Issues.PROXY_NOT_CONFIGURED)
            else:
                log.error(f'网络连接失败,请检查VPN是否可用,{_t(KeyWord.REASON)}:"{e}"')
        except AttributeError as e:
            record_error: bool = True
            log.error(f'登录超时,请重新打开软件尝试登录,{_t(KeyWord.REASON)}:"{e}"')
        except KeyboardInterrupt:
            console.log('⌨️ 用户键盘中断。')
        except OperationalError as e:
            record_error: bool = True
            log.error(
                f'检测到多开软件时,由于在上一个实例中「下载完成」后窗口没有被关闭的行为,请在关闭后重试,{_t(KeyWord.REASON)}:"{e}"')
        except Exception as e:
            record_error: bool = True
            log.exception(msg=f'运行出错,{_t(KeyWord.REASON)}:"{e}"')
        finally:
            self.is_running = False
            self.pb.progress.stop()
            if not record_error:
                self.app.print_link_table(
                    link_info=DownloadTask.LINK_INFO,
                    export=self.gc.get_config('export_table').get('link')
                )
                self.app.print_count_table(
                    export=self.gc.get_config('export_table').get('count')
                )
                self.app.print_upload_table(
                    upload_tasks=UploadTask.TASKS,
                    export=self.gc.get_config('export_table').get('upload')
                )
                MetaData.pay()
                self.app.process_shutdown(60) if len(self.running_log) == 2 else None  # v1.2.8如果并未打开客户端执行任何下载,则不执行关机。
            self.app.ctrl_c()
