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
from module.filter import Filter, MessageFilter
from module.app import Application
from module.app import DownloadFileName
from module.config import GlobalConfig, UserConfig
from module.parser import PARSE_ARGS
from module.async_window import DynamicAsyncWindow
from module.diagnostics import RichDiagnosticAdapter
from module.local_storage_guard import LocalStorageGuard
from module.media_manager import MediaManager
from module.web_task_manager import WebUITaskManager
from module.live_watch_manager import LiveWatchManager
from module.bot import (
    Bot,
    KeyboardButton,
    CallbackData
)
from module.callback_handler import CallbackHandler
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
    validate_title,
    extract_full_extension,
    is_compressed_file
)
from module.target_profiles import (
    target_profile_limit,
    target_profile_size_error
)
from module.pikpak_archive import build_pikpak_archive_client
from module.pikpak_integration import PikpakIntegrationManager
from module.transfer_progress import TransferProgressTracker
from module.source_folders import source_folder_from_link, source_folder_from_message
from module.task import DownloadTask, UploadTask
from module.transfer_store import TransferStore, TransferStatus
from module.persistence.system_log import SystemLogTracer
from module.stdio import ProgressBar, MetaData
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
    parse_forward_watch_rule,
    is_allow_upload,
    iter_discussion_reply_forward_units,
)
from module.transfer_engine import TransferEngine
from module.comp import TransferContext, TransferPorts
from module.transfer.runner import WebTransferRunner
from module.live_watch_applicator import LiveWatchApplicator




from module.composition_root import TrmdCompositionRoot
from module.web_operations import WebOperationsMixin
from module.bot_host import BotHostMixin


class TelegramRestrictedMediaDownloader(TrmdCompositionRoot, WebOperationsMixin, BotHostMixin):

    @property
    def is_bot_running(self) -> bool:
        return bool(getattr(self.bot, 'is_bot_running', False))

    @staticmethod
    def transfer_send_interval() -> float:
        return WebTransferRunner.transfer_send_interval()


    async def wait_between_transfer_messages(self) -> None:
        return await self._ensure_transfer_runner().wait_between_transfer_messages()


    async def wait_for_interruptible(self, seconds: float, task_id: Optional[int] = None) -> bool:
        loop = getattr(self, 'loop', None)
        if loop is None:
            await asyncio.sleep(max(0.0, float(seconds)))
            return True
        deadline = loop.time() + max(0.0, float(seconds))
        while True:
            if task_id and not self.should_continue_web_transfer_task(task_id):
                return False
            remaining = deadline - loop.time()
            if remaining <= 0:
                return True
            await asyncio.sleep(min(remaining, 1.0))

    async def wait_for_telegram_flood(self, error, task_id: Optional[int] = None, action: str = 'request') -> None:
        amount = max(0, int(getattr(error, 'value', 0) or 0))
        jitter = random.uniform(0.5, 2.0) if amount > 0 else 0
        wait_seconds = amount + jitter
        message = f'Telegram flood wait during {action}: waiting {amount} seconds before retry.'
        console.log(message, style='#FF4689')
        log.warning(message)
        if self.transfer_store and task_id:
            self.transfer_store.add_event(task_id, message, level='warning')
        if not await self.wait_for_interruptible(wait_seconds, task_id=task_id):
            raise asyncio.CancelledError()


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

    def infer_target_profile(
            self,
            target_link: Optional[str],
            target_profile: Optional[str] = None
    ) -> Optional[str]:
        return target_profile or ('pikpak' if self.is_pikpak_target(target_link, target_profile) else None)

    def normalize_download_upload_meta(self, with_upload: dict) -> dict:
        task_with_upload = with_upload.copy()
        target_link = task_with_upload.get('link')
        profile = self.infer_target_profile(target_link, task_with_upload.get('target_profile'))
        task_with_upload['target_profile'] = profile
        task_with_upload.setdefault('file_name', None)
        task_with_upload['with_delete'] = (
            True
            if profile == 'pikpak'
            else task_with_upload.get('with_delete', self.gc.upload_delete)
        )
        task_with_upload.setdefault('send_as_media_group', False if profile == 'pikpak' else True)
        if profile == 'pikpak':
            task_with_upload.setdefault('on_file_ready', self.on_transfer_file_ready)
            task_with_upload.setdefault('status_callback', self.on_transfer_upload_status)
            task_with_upload.setdefault('progress_callback', self.on_transfer_upload_progress)
            task_with_upload.setdefault('skip_callback', self.on_transfer_item_skipped)
            task_with_upload.setdefault('failure_callback', self.on_transfer_item_failed)
        return task_with_upload

    async def prepare_download_upload_meta(self, with_upload: Optional[dict]) -> Optional[dict]:
        if not isinstance(with_upload, dict):
            return with_upload
        task_with_upload = self.normalize_download_upload_meta(with_upload)
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

    async def reserve_transfer_local_storage(
            self,
            with_upload: Optional[dict],
            final_path: str,
            file_size: Optional[int]
    ) -> None:
        if not isinstance(with_upload, dict):
            return
        if with_upload.get('_local_storage_release') is not None:
            return
        guard = getattr(self, 'local_storage_guard', None)
        if not guard:
            return
        token = (
            with_upload.get('task_id'),
            with_upload.get('item_id'),
            with_upload.get('source_chat_id'),
            with_upload.get('message_id'),
            final_path
        )
        with_upload['_local_storage_token'] = token
        with_upload['_local_storage_release'] = await guard.acquire(
            token=token,
            path=final_path,
            size=file_size
        )

    def mark_transfer_local_storage_materialized(self, with_upload: Optional[dict]) -> None:
        if not isinstance(with_upload, dict):
            return
        guard = getattr(self, 'local_storage_guard', None)
        if guard and with_upload.get('_local_storage_token') is not None:
            guard.mark_materialized(with_upload.get('_local_storage_token'))

    @staticmethod
    def release_transfer_local_storage(with_upload: Optional[dict]) -> None:
        if not isinstance(with_upload, dict):
            return
        release = with_upload.get('_local_storage_release')
        if callable(release):
            release()
            with_upload['_local_storage_release'] = None
            with_upload['_local_storage_token'] = None

    def create_uploader(self) -> TelegramUploader:
        return TelegramUploader(upload_context=self)

    def ensure_uploader(self) -> TelegramUploader:
        if not self.uploader:
            self.uploader = self.create_uploader()
        return self.uploader

    def start_download_upload(
            self,
            with_upload: Optional[dict],
            message: pyrogram.types.Message,
            file_path: str
    ) -> bool:
        return self.transfer_engine.start_download_upload(with_upload, message, file_path)


    async def get_upload_link_from_bot(
            self,
            client: pyrogram.Client,
            message: pyrogram.types.Message,
            delete: bool = False,
            save_directory: str = None,
            recursion: bool = False,
            valid_link_cache: dict = None
    ):
        link_meta: Union[dict, None] = await self.bot.get_upload_link_from_bot(
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
        return self.transfer_engine.refresh_transfer_task_counts(task_id)

    def find_resumable_transfer_item(self, task_id: int, source_message_id: int, source_chat_id=None):
        return self.transfer_engine.find_resumable_transfer_item(
            task_id,
            source_message_id,
            source_chat_id=source_chat_id
        )

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
        return self.transfer_engine.create_transfer_item_for_download(
            task_with_upload, chat_id, link, message,
            media_type, file_name, final_path, file_size
        )

    async def create_bot_transfer_progress(
            self,
            source_link: Optional[str],
            target_link: Optional[str],
            source_message_id: Optional[int],
            file_name: Optional[str] = None
    ) -> Optional[dict]:
        client = getattr(self, 'last_client', None)
        message = getattr(self, 'last_message', None)
        if not all([client, message, getattr(message, 'from_user', None)]):
            return None
        chat_id = message.from_user.id
        progress = {
            'client': client,
            'chat_id': chat_id,
            'source_message_id': source_message_id,
            'source_link': source_link,
            'target_link': target_link,
            'file_name': file_name,
            'min_interval': 8,
            'last_update_at': 0,
            'last_text': None
        }
        text = self.build_bot_transfer_progress_text(progress, phase='pending')
        try:
            sent = await client.send_message(
                chat_id=chat_id,
                reply_parameters=ReplyParameters(message_id=message.id),
                link_preview_options=LINK_PREVIEW_OPTIONS,
                text=text
            )
            progress['message_id'] = sent.id
            progress['last_text'] = text
            progress['last_update_at'] = datetime.datetime.now(datetime.UTC).timestamp()
            return progress
        except Exception as e:
            log.warning(f'无法创建监听转存进度消息,{_t(KeyWord.REASON)}:"{e}"')
            return None

    def build_transfer_upload_meta(self, task: dict, source_link: str = None, media_type: str = None, range_message_id: Optional[int] = None) -> dict:
        source_link = source_link or task.get('source_link')
        return self.build_download_upload_meta(
            target_link=task.get('target_link'),
            target_profile=task.get('target_profile'),
            source_link=source_link,
            source_folder=source_folder_from_link(source_link),
            task_id=task.get('id'),
            media_type=media_type,
            range_message_id=range_message_id
        )


    def telegram_upload_size_limit_error(self, file_size: int) -> Optional[str]:
        return self.transfer_engine.telegram_upload_size_limit_error(file_size)

    def get_download_upload_size_limit_error(
            self,
            task_with_upload: Optional[dict],
            file_size: int
    ) -> Optional[str]:
        return self.transfer_engine.get_download_upload_size_limit_error(task_with_upload, file_size)

    def skip_download_before_transfer_upload(
            self,
            link: str,
            file_name: str,
            format_file_size: str,
            valid_dtype: str,
            task_with_upload: Optional[dict],
            message,
            file_size: int,
            error_message: str
    ) -> None:
        self.transfer_engine.skip_download_before_transfer_upload(
            link, file_name, format_file_size, valid_dtype,
            task_with_upload, message, file_size, error_message
        )

    def notify_bot_transfer_upload_precheck_skipped(
            self,
            task_with_upload: Optional[dict],
            file_name: str,
            file_size: int,
            error_message: str
    ) -> None:
        self.transfer_engine.notify_bot_transfer_upload_precheck_skipped(
            task_with_upload, file_name, file_size, error_message
        )

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

    @property
    def pikpak_target(self):
        return self.pikpak_manager

    async def wait_for_pikpak_ingest_confirmation(
            self,
            target_chat_id,
            forwarded_message=None,
            timeout_seconds: float = 15,
            poll_interval: float = 3
    ) -> bool:
        return await self.pikpak_manager.wait_for_pikpak_ingest_confirmation(
            target_chat_id=target_chat_id,
            forwarded_message=forwarded_message,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval
        )

    def is_pikpak_target(self, target_link: Optional[str], target_profile: Optional[str] = None) -> bool:
        return PikpakIntegrationManager.is_pikpak_target(target_link, target_profile)

    def archive_pikpak_item(self, *args, **kwargs):
        return self.pikpak_manager.archive_pikpak_item(*args, **kwargs)

    def complete_forwarded_pikpak_item(self, *args, **kwargs) -> bool:
        return self.pikpak_manager.complete_forwarded_pikpak_item(*args, **kwargs)

    def skip_empty_transfer_source_message(self, *args, **kwargs) -> int:
        return self.pikpak_manager.skip_empty_transfer_source_message(*args, **kwargs)

    def get_task_target_size_limit_error(self, task: dict, message) -> Optional[dict]:
        return self.pikpak_manager.get_task_target_size_limit_error(task, message)

    def get_message_media_target_limit_meta(self, message) -> Optional[dict]:
        return self.pikpak_manager.get_message_media_target_limit_meta(message)

    def get_message_media_archive_filename(self, message) -> Optional[str]:
        return PikpakIntegrationManager.get_message_media_archive_filename(message)

    def forwarded_message_has_identity(self, forwarded_message) -> bool:
        return PikpakIntegrationManager.forwarded_message_has_identity(forwarded_message)

    def is_pikpak_ingest_success_message(self, message) -> bool:
        return PikpakIntegrationManager.is_pikpak_ingest_success_message(message)

    def is_pikpak_ingest_failure_message(self, message) -> bool:
        return PikpakIntegrationManager.is_pikpak_ingest_failure_message(message)

    def fail_transfer_item(self, task_id: int, item_id: int, message: str) -> None:
        return self.pikpak_manager.fail_transfer_item(task_id, item_id, message)

    def get_deep_link_resolver(self):
        if getattr(self, '_deep_link_resolver', None) is None:
            from module.transfer.deep_link import DeepLinkResolver
            self._deep_link_resolver = DeepLinkResolver()
        return self._deep_link_resolver

    def skip_transfer_item_for_target_limit(
            self,
            task: dict,
            message,
            source_link: str,
            origin_chat_id,
            limit_error: dict
    ) -> int:
        return self.transfer_engine.skip_transfer_item_for_target_limit(
            task, message, source_link, origin_chat_id, limit_error
        )

    @staticmethod
    def transfer_single_link(source_link: str) -> str:
        return TransferEngine.transfer_single_link(source_link)

    async def create_web_transfer_fallback_download(self, *args, **kwargs) -> None:
        return await self._ensure_transfer_runner().create_web_transfer_fallback_download(*args, **kwargs)

    async def transfer_message_to_web_target(self, *args, **kwargs) -> bool:
        return await self._ensure_transfer_runner().transfer_message_to_web_target(*args, **kwargs)

    async def transfer_web_discussion_replies_to_target(self, *args, **kwargs) -> tuple[int, int]:
        return await self._ensure_transfer_runner().transfer_web_discussion_replies_to_target(*args, **kwargs)

    async def get_web_transfer_single_message(self, source_link: str):
        return await self._ensure_transfer_runner().get_web_transfer_single_message(source_link)

    async def get_web_transfer_range_message(self, chat_id, message_id: int, task_id: int):
        return await self._ensure_transfer_runner().get_web_transfer_range_message(chat_id, message_id, task_id)

    async def parse_web_transfer_link(self, client, link: str) -> dict:
        return await parse_link(client=client, link=link)

    def skip_missing_web_transfer_range_message(
            self,
            task: dict,
            origin_chat_id,
            source_link: str,
            message_id: int
    ) -> None:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.skip_missing_web_transfer_range_message(
                task, origin_chat_id, source_link, message_id
            )
        self.transfer_engine.skip_missing_web_transfer_range_message(
            task, origin_chat_id, source_link, message_id
        )

    async def process_web_transfer_task(self, task_id: int) -> None:
        return await self._ensure_transfer_runner().process_task(task_id)


    def _record_watch_event(self, watch_id, origin_chat_id, message_id, target_chat_id, target_link, status, message):
        try:
            ts = getattr(self, 'transfer_store', None)
            if ts:
                ts.add_live_watch_event(
                    watch_id=watch_id,
                    source_chat_id=str(origin_chat_id),
                    source_message_id=int(message_id),
                    target_chat_id=str(target_chat_id),
                    target_link=str(target_link),
                    status=status,
                    message=message
                )
        except Exception as e:
            log.debug(f'记录实时监听事件失败(watch_id={watch_id}, status={status}): {e}')

    def _watch_forward_media_label(self, message, media_group=None) -> str:
        if media_group:
            return '媒体组'
        dtype = next((_ for _ in DownloadType() if getattr(message, _, None)), None)
        if dtype is None and getattr(message, 'text', None):
            return '文本'
        labels = {
            'video': '视频',
            'photo': '图片',
            'document': '文件',
            'audio': '音频',
            'voice': '语音',
            'animation': '动图',
            'video_note': '视频留言',
        }
        return labels.get(dtype, '消息')

    def _forward_success_event_message(self, message, media_group=None) -> str:
        return f'转发成功：{self._watch_forward_media_label(message, media_group)}'

    def _message_chain_context(
            self,
            message: pyrogram.types.Message,
            watch_id: Optional[str] = None
    ) -> tuple[str, str, int]:
        origin_chat_id = str(getattr(getattr(message, 'chat', None), 'id', ''))
        message_id = int(getattr(message, 'id', 0) or 0)
        trace_id = SystemLogTracer.make_trace_id(watch_id, origin_chat_id, message_id)
        return trace_id, origin_chat_id, message_id

    def _log_system_chain(self, **kwargs) -> None:
        tracer = getattr(self, 'system_log', None)
        if tracer is not None:
            tracer.log(**kwargs)

    async def _run_pikpak_archive_after_forward(
            self,
            message: pyrogram.types.Message,
            origin_chat_id: Union[str, int],
            message_id: int,
            media_group: Optional[list] = None,
            transferred_at: Optional[float] = None,
            source_folder: Optional[str] = None,
            source_link: Optional[str] = None,
    ) -> None:
        transferred_at = transferred_at or datetime.datetime.now(datetime.UTC).timestamp()
        messages = [message]
        if media_group:
            try:
                group_messages = await message.get_media_group()
                if group_messages:
                    self.inherit_media_group_title(group_messages)
                    messages = list(group_messages)
            except Exception as e:
                log.debug(f'Unable to resolve media group for PikPak archive: {e}')
        for group_message in messages:
            group_source_link = (
                source_link
                or getattr(group_message, 'link', None)
                or getattr(message, 'link', None)
            )
            archive_folder = source_folder or source_folder_from_message(
                group_message,
                fallback_chat_id=origin_chat_id,
                fallback_link=group_source_link
            )
            archive_result = self.archive_pikpak_item(
                target_profile='pikpak',
                item_id=None,
                task_id=None,
                message=group_message,
                source_link=group_source_link,
                source_folder=archive_folder,
                transferred_at=transferred_at
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
                        'file_name': getattr(archive_result, 'file_name', None),
                    }
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
            archive_after_success: Optional[bool] = True,
            watch_id: Optional[str] = None,
            trace_id: Optional[str] = None,
            source_folder: Optional[str] = None,
            archive_source_link: Optional[str] = None,
    ):
        try:
            if trace_id is None:
                trace_id, _, _ = self._message_chain_context(message, watch_id)
            channel_source_folder = source_folder or source_folder_from_message(
                message,
                fallback_chat_id=origin_chat_id,
                fallback_link=archive_source_link or getattr(message, 'link', None)
            )
            channel_source_link = archive_source_link or getattr(message, 'link', None)
            if not ignore_type_filter and not self.message_filter.should_pass(message):
                reject_reason = self.message_filter.get_reject_reason(message) or '消息过滤器拒绝'
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
                    self._record_watch_event(watch_id, origin_chat_id, message_id, target_chat_id, target_link, 'skipped', f'跳过转发(已被消息过滤器过滤: {reject_reason})。')
                if done_notice:
                    await asyncio.create_task(
                        self.done_notice(
                            f'"{origin_chat_id}",{_t(KeyWord.MESSAGE_ID)}:{message_id}'
                            f' ➡️ '
                            f'"{target_chat_id}",{_t(KeyWord.FORWARD_SKIP)}(已被消息过滤器过滤)。'
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

    async def get_forward_link_from_bot(
            self, client: pyrogram.Client,
            message: pyrogram.types.Message
    ) -> Union[dict, None]:
        meta: Union[dict, None] = await self.bot.get_forward_link_from_bot(client, message)
        if meta is None:
            return None
        self.bot.last_client = client
        self.bot.last_message = message
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
                        with_upload=self.build_download_upload_meta(
                            target_link=target_link,
                            source_link=origin_link,
                            source_folder=source_folder_from_link(origin_link)
                        )
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
            if not self.message_filter.should_pass(message):
                reject_reason = self.message_filter.get_reject_reason(message) or '消息过滤器拒绝'
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

    def check_type(self, message: pyrogram.types.Message):
        te = getattr(self, 'transfer_engine', None)
        if te is not None:
            try:
                return te.check_type(message)
            except Exception:
                pass
        ft = getattr(getattr(self, 'gc', None), 'forward_type', None)
        if isinstance(ft, dict):
            for media in ('video', 'photo', 'audio', 'document', 'voice', 'animation', 'video_note'):
                if getattr(message, media, None):
                    return bool(ft.get(media, False))
            if getattr(message, 'text', None) or getattr(message, 'caption', None):
                return bool(ft.get('text', False))
        return False

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
    ) -> int:
        from module.transfer.deep_link import (
            DeepLinkResolveError,
            message_has_whitelisted_deep_link,
            normalize_resolved_messages,
        )
        count = 0
        whitelist = self.gc.get_deep_link_bot_whitelist() if resolve_deep_link else []

        def include_discussion_message(item) -> bool:
            # Deep-link mode: discussion replies are deep-link-only (no bare text/media dump).
            if resolve_deep_link:
                return message_has_whitelisted_deep_link(item, whitelist)
            return self.check_type(item)

        try:
            async for comment, media_group in iter_discussion_reply_forward_units(
                    client=self.app.client,
                    chat_id=source_chat_id,
                    message_id=source_message_id,
                    include_message=include_discussion_message
            ):
                messages_to_forward = [(comment, media_group)]
                if resolve_deep_link:
                    resolver = self.get_deep_link_resolver()
                    try:
                        resolved_list = normalize_resolved_messages(
                            await resolver.resolve(
                                client=self.app.client,
                                message=comment,
                                whitelist=whitelist,
                                timeout_seconds=self.gc.get_deep_link_timeout_seconds(),
                                min_interval_seconds=self.gc.get_deep_link_min_interval_seconds(),
                                settle_seconds=self.gc.get_deep_link_settle_seconds(),
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
                                'comment_id': getattr(comment, 'id', None),
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
                for forward_message, forward_group in messages_to_forward:
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
                    channel_source_folder = source_folder_from_message(
                        comment,
                        fallback_chat_id=source_chat_id,
                    )
                    await self.forward(
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
                        source_folder=channel_source_folder,
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
                        }
                    )
                    forward_origin_chat_id = _listen_chat_id
                    forward_message_id = message.id
                    channel_source_link = link
                    channel_source_folder = source_folder_from_message(
                        message,
                        fallback_chat_id=_listen_chat_id,
                        fallback_link=link,
                    )
                    messages_to_forward = [message]
                    if resolve_deep_link:
                        from module.transfer.deep_link import (
                            DeepLinkResolveError,
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
                        if resolved_list is not None:
                            messages_to_forward = resolved_list
                    for forward_unit in messages_to_forward:
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
                        try:
                            media_group_ids = await forward_unit.get_media_group()
                            if not media_group_ids:
                                raise ValueError
                            if (
                                    not self.gc.forward_type.get('video') or
                                    not self.gc.forward_type.get('photo')
                            ):
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
                                await self.forward(
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
                        await self.forward(
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
                        )
                    if include_comment:
                        await self.schedule_or_forward_discussion_replies(
                            client=client,
                            source_chat_id=_listen_chat_id,
                            source_message_id=message_id,
                            target_chat_id=_target_chat_id,
                            target_link=target_link,
                            watch_id=watch_id
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
            compare_size: Union[int, None] = None,  # 不为None时,将通过大小比对判断是否为完整文件。
            progress_timeout_seconds: Optional[float] = 120,
            max_stall_retries: int = 3,
            transfer_task_id: Optional[int] = None
    ) -> str:
        if transfer_task_id and not self.should_continue_web_transfer_task(int(transfer_task_id)):
            raise asyncio.CancelledError()
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
        if downloaded > 0:
            safe_downloaded = (downloaded // chunk_size) * chunk_size
            if safe_downloaded != downloaded:
                with open(file=temp_path, mode='r+b') as cache_file:
                    cache_file.truncate(safe_downloaded)
                log.warning(
                    f'缓存文件"{temp_path}"大小未对齐,'
                    f'已截断到安全断点:{downloaded} -> {safe_downloaded}。'
                )
                downloaded = safe_downloaded
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
            stall_retries = 0
            while True:
                stream = None
                try:
                    stream = self.app.client.stream_media(message=message, offset=skip_chunks)
                    while True:
                        if transfer_task_id and not self.should_continue_web_transfer_task(int(transfer_task_id)):
                            raise asyncio.CancelledError()
                        if progress_timeout_seconds and progress_timeout_seconds > 0:
                            chunk = await asyncio.wait_for(
                                anext(stream),
                                timeout=float(progress_timeout_seconds)
                            )
                        else:
                            chunk = await anext(stream)
                        f.write(chunk)
                        downloaded += len(chunk)
                        stall_retries = 0
                        if callable(progress):
                            progress(downloaded, *progress_args)
                    break
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    stall_retries += 1
                    log.warning(
                        f'下载流超过{progress_timeout_seconds}秒无进展,'
                        f'正在重建连接继续断点续传:{stall_retries}/{max_stall_retries}。'
                    )
                    with_upload = progress_args[-1] if progress_args else None
                    item_id = with_upload.get('item_id') if isinstance(with_upload, dict) else None
                    if item_id:
                        store = getattr(self, 'transfer_store', None)
                        if store:
                            store.update_item_progress(
                                item_id=int(item_id),
                                phase='downloading',
                                download_current=downloaded,
                                download_total=int(compare_size or 0),
                                download_speed_bps=0
                            )
                        tracker = getattr(self, 'progress_tracker', None)
                        samples = getattr(tracker, '_speed_samples', None) if tracker else None
                        if isinstance(samples, dict):
                            samples.pop(('download', int(item_id)), None)
                    if stall_retries > max_stall_retries:
                        break
                    skip_chunks = downloaded // chunk_size
                    f.seek(downloaded)
                    await asyncio.sleep(min(stall_retries, 5))
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
                finally:
                    close_stream = getattr(stream, 'aclose', None)
                    if callable(close_stream):
                        try:
                            await close_stream()
                        except Exception:
                            pass
        if compare_size is None or compare_file_size(a_size=downloaded, b_size=compare_size):
            result: str = safe_replace(origin_file=temp_path, overwrite_file=file_name).get('e_code')
            log.warning(result) if result is not None else None
            log.info(
                f'"{temp_path}"下载完成,更改文件名:[{temp_path}]({get_file_size(temp_path)}) -> [{file_name}]({compare_size})')
        return file_name

    def get_media_meta(self, message: pyrogram.types.Message, dtype) -> Dict[str, Union[int, str]]:
        return self.transfer_engine.get_media_meta(message, dtype)

    @staticmethod
    def get_download_message_title(message: pyrogram.types.Message) -> Optional[str]:
        for attr in ('caption', 'text'):
            title = getattr(message, attr, None)
            if isinstance(title, str):
                title = next((line.strip() for line in title.splitlines() if line.strip()), '')
                if title:
                    return title
        inherited_title = getattr(message, '_trmd_source_title', None)
        return inherited_title if isinstance(inherited_title, str) and inherited_title.strip() else None

    @staticmethod
    def inherit_media_group_title(messages: Union[list, None]) -> None:
        if not isinstance(messages, list):
            return
        title = None
        for message in messages:
            title = TelegramRestrictedMediaDownloader.get_download_message_title(message)
            if title:
                break
        if not title:
            return
        for message in messages:
            if not TelegramRestrictedMediaDownloader.get_download_message_title(message):
                try:
                    setattr(message, '_trmd_source_title', title)
                except Exception:
                    pass

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
            self.inherit_media_group_title(message)
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
                if isinstance(task_with_upload, dict):
                    task_with_upload['temp_path'] = temp_file_path
                    item_id_for_temp = task_with_upload.get('item_id')
                    if self.transfer_store and item_id_for_temp:
                        self.transfer_store.update_item(
                            int(item_id_for_temp),
                            local_path=save_directory,
                            temp_path=temp_file_path
                        )
                limit_error = self.get_download_upload_size_limit_error(task_with_upload, sever_file_size)
                if limit_error:
                    self.skip_download_before_transfer_upload(
                        link=link,
                        file_name=file_name,
                        format_file_size=format_file_size,
                        valid_dtype=valid_dtype,
                        task_with_upload=task_with_upload,
                        message=message,
                        file_size=sever_file_size,
                        error_message=limit_error
                    )
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
                    await self.reserve_transfer_local_storage(
                        with_upload=task_with_upload,
                        final_path=save_directory,
                        file_size=sever_file_size
                    )
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
                            compare_size=sever_file_size,
                            transfer_task_id=(
                                int(task_with_upload.get('task_id'))
                                if isinstance(task_with_upload, dict) and task_with_upload.get('task_id') is not None
                                else None
                            )
                        )
                    )
                    self._register_transfer_download_task(task_with_upload, _task)
                    _task.add_done_callback(
                        partial(
                            self._unregister_transfer_download_task,
                            task_with_upload
                        )
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
                    MetaData.print_current_task_num(
                        prompt=_t(KeyWord.CURRENT_DOWNLOAD_TASK),
                        num=self.app.current_task_num
                    )
            else:
                _error = '不支持或被忽略的类型(已取消)。'
                if isinstance(with_upload, dict):
                    with_upload['message_id'] = getattr(message, 'id', None)
                    with_upload['media_type'] = valid_dtype
                    callback = with_upload.get('skip_callback')
                    if callable(callback):
                        callback(with_upload, _error)
                    self.release_transfer_local_storage(with_upload)
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
        return self.transfer_engine.__check_download_finish(
            message, sever_file_size, temp_file_path, save_directory, with_move
        )

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
        return self.transfer_engine.download_complete_callback(
            sever_file_size, temp_file_path, link, message, file_name,
            retry_count, file_id, format_file_size, task_id,
            with_upload, diy_download_type, _future
        )


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

    def _process_links(self, link: Union[str, list]) -> Union[set, None]:
        return self.transfer_engine._process_links(link)

    def _retry_call(self, notice, _future):
        self.transfer_engine._retry_call(notice, _future)

    async def __ensure_client_authorized(self) -> None:
        """确保 Telegram Client 已登录；模仿 pyrogram.Client.start() 的完整流程。"""
        if self.web_ui_auth:
            # WebUI 模式
            is_authorized = await self.app.client.connect()
            if not is_authorized:
                user = await self.app.client.authorize_webui(self.web_ui_auth)
                self.web_ui_auth.set_done(f'{user.first_name} {user.last_name or ""}'.strip())
                console.log(f'[#B1DB74]登录成功: {user.first_name}[/#B1DB74]')
            else:
                try:
                    self.app.client.me = await self.app.client.get_me()
                    await self.app.client.initialize()
                    self.web_ui_auth.set_done('')
                    return
                except (SessionRevoked, AuthKeyUnregistered, SessionExpired, Unauthorized):
                    log.warning('会话已过期，请在 WebUI 中重新登录。')
                except Exception as e:
                    log.error(f'验证会话时出错: {e}')
                await self.app.client.disconnect()
                await self.app.client.connect()
                user = await self.app.client.authorize_webui(self.web_ui_auth)
                self.web_ui_auth.set_done(f'{user.first_name} {user.last_name or ""}'.strip())
                console.log(f'[#B1DB74]登录成功: {user.first_name}[/#B1DB74]')
            # 登录后初始化（等价于 pyrogram.Client.start() 中的 self.me + initialize）
            self.app.client.me = await self.app.client.get_me()
            await self.app.client.initialize()
        else:
            # CLI 模式
            self.start_web_ui()
            await self.app.client.start(use_qr=False)

    async def __download_media_from_links(self) -> None:
        if PARSE_ARGS.web is not None:
            self.start_web_ui(with_auth_provider=True)
        await self.__ensure_client_authorized()
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
                self.uploader = TelegramUploader(upload_context=self)
                self.cd = CallbackData()
                if self.gc.upload_delete:
                    console.log(
                        f'在使用转发(/forward)、监听转发(/listen_forward)、上传(/upload)、递归上传(/upload_r)时:\n'
                        f'当检测到"受限转发"时,自动采用"下载后上传"的方式,并在完成后删除本地文件。\n'
                        f'如需关闭,前往机器人[帮助页面]->[设置]->[上传设置]进行修改。\n',
                        style='#FF4689'
                    )
        if self.web_ui and not self.uploader:
            self.uploader = TelegramUploader(upload_context=self)
        links: Union[set, None] = self._process_links(link=self.app.links)
        # 将初始任务添加到队列中。
        [await self.loop.create_task(self.create_download_task(message_ids=link, retry=None)) for link in
         sorted(links)] if links else None
        # 处理队列中的任务与机器人事件。
        while not self.queue.empty() or self.is_bot_running or self.web_ui:
            self.maybe_run_scheduled_media_cleanup()
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
                self.app.process_shutdown(60) if len(self.running_log) == 2 else None  # v1.2.8如果并未打开客户端执行任何下载,则不执行关机。
            self.app.ctrl_c()


__all__ = ['TelegramRestrictedMediaDownloader']
