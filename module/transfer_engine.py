# coding=UTF-8
import os
import sys
import random
import asyncio
from functools import partial
from typing import Optional, Union, Dict, List

import pyrogram
from pyrogram.errors import FloodWait, FloodPremiumWait

from module import console, log
from module.language import _t
from module.parser import PARSE_ARGS
from module.enums import DownloadStatus, UploadStatus, KeyWord, DownloadType, SaveDirectoryPrefix
from module.task import DownloadTask, UploadTask
from module.transfer_registry import transfer_registry
from module.transfer_store import TransferStatus
from module.target_profiles import target_profile_limit, target_profile_size_error
from module.path_tool import (
    split_path,
    get_file_size,
    compare_file_size,
    move_to_save_directory,
    validate_title
)
from module.stdio import MetaData
from module.util import is_allow_upload, parse_link
from module.source_folders import source_folder_from_link, source_folder_from_message
from module.local_storage_guard import LocalStorageGuard
from module.filter import MessageFilter


class TransferEngine:
    def __init__(
        self,
        ctx,
        diagnostic=None,
        env_save_directory_getter=None,
        get_final_save_directory_getter=None,
        get_final_file_path_getter=None,
        infer_target_profile_getter=None,
        normalize_download_upload_meta_getter=None,
        is_pikpak_target_getter=None,
        build_transfer_upload_meta_getter=None,
        notify_bot_transfer_download_progress_getter=None,
        notify_bot_transfer_downloaded_getter=None,
        record_transfer_download_success_getter=None,
        try_reuse_transfer_download_record_getter=None,
        on_transfer_file_ready_getter=None,
        on_transfer_item_skipped_getter=None,
        on_transfer_item_failed_getter=None,
        on_transfer_upload_progress_getter=None,
        on_transfer_upload_status_getter=None,
        notify_bot_transfer_upload_progress_getter=None,
        notify_bot_transfer_upload_status_getter=None,
        release_download_upload_window_getter=None,
        release_transfer_local_storage_getter=None,
        mark_transfer_local_storage_materialized_getter=None,
        transfer_send_interval_getter=None,
        ensure_uploader_getter=None,
        build_bot_transfer_progress_text_getter=None,
        schedule_bot_transfer_progress_update_getter=None,
        bot_task_link_getter=None,
        queue_getter=None,
        pb_progress_getter=None,
        event_getter=None,
        create_download_task_getter=None,
        detect_transfer_range_async_getter=None,
    ):
        from module.comp import TransferContext
        self.ctx: TransferContext = ctx if isinstance(ctx, TransferContext) else TransferContext()
        self.diagnostic = diagnostic or self.ctx.diagnostic

        self._env_save_directory = env_save_directory_getter
        self._get_final_save_directory = get_final_save_directory_getter
        self._get_final_file_path = get_final_file_path_getter
        self._infer_target_profile = infer_target_profile_getter
        self._normalize_download_upload_meta = normalize_download_upload_meta_getter
        self._is_pikpak_target = is_pikpak_target_getter
        self._build_transfer_upload_meta = build_transfer_upload_meta_getter
        self._notify_dl_progress = notify_bot_transfer_download_progress_getter
        self._notify_downloaded = notify_bot_transfer_downloaded_getter
        self._record_dl_success = record_transfer_download_success_getter
        self._try_reuse_dl_record = try_reuse_transfer_download_record_getter
        self._on_file_ready = on_transfer_file_ready_getter
        self._on_item_skipped = on_transfer_item_skipped_getter
        self._on_item_failed = on_transfer_item_failed_getter
        self._on_ul_progress = on_transfer_upload_progress_getter
        self._on_ul_status = on_transfer_upload_status_getter
        self._notify_ul_progress = notify_bot_transfer_upload_progress_getter
        self._notify_ul_status = notify_bot_transfer_upload_status_getter
        self._release_window = release_download_upload_window_getter
        self._release_storage = release_transfer_local_storage_getter
        self._mark_storage_materialized = mark_transfer_local_storage_materialized_getter
        self._transfer_send_interval = transfer_send_interval_getter
        self._ensure_uploader = ensure_uploader_getter
        self._build_bot_progress_text = build_bot_transfer_progress_text_getter
        self._schedule_bot_progress_update = schedule_bot_transfer_progress_update_getter
        self._bot_task_link = bot_task_link_getter
        self._queue = queue_getter
        self._pb_progress = pb_progress_getter
        self._event = event_getter
        self._create_download_task = create_download_task_getter
        self._detect_tr_range_async = detect_transfer_range_async_getter

    @property
    def app(self):
        return self.ctx.app

    @property
    def gc(self):
        return self.ctx.gc

    @property
    def loop(self):
        return self.ctx.loop

    @property
    def transfer_store(self):
        return self.ctx.transfer_store

    @property
    def my_id(self):
        return self.ctx.my_id

    @property
    def uploader(self):
        return self.ctx.uploader

    @property
    def progress_tracker(self):
        return self.ctx.progress_tracker

    @property
    def pikpak_manager(self):
        return self.ctx.pikpak_manager

    @property
    def watch_manager(self):
        return self.ctx.watch_manager

    @property
    def web_task_manager(self):
        return self.ctx.web_task_manager

    @property
    def local_storage_guard(self):
        return self.ctx.local_storage_guard

    @property
    def download_upload_window(self):
        return self.ctx.download_upload_window

    def env_save_directory(self, *args, **kwargs):
        return self._env_save_directory()(*args, **kwargs)

    def get_final_save_directory(self, *args, **kwargs):
        return self._get_final_save_directory()(*args, **kwargs)

    def get_final_file_path(self, *args, **kwargs):
        return self._get_final_file_path()(*args, **kwargs)

    def infer_target_profile(self, *args, **kwargs):
        return self._infer_target_profile()(*args, **kwargs)

    def normalize_download_upload_meta(self, *args, **kwargs):
        return self._normalize_download_upload_meta()(*args, **kwargs)

    def is_pikpak_target(self, *args, **kwargs):
        return self._is_pikpak_target()(*args, **kwargs)

    def build_transfer_upload_meta(self, *args, **kwargs):
        return self._build_transfer_upload_meta()(*args, **kwargs)

    def ensure_uploader(self, *args, **kwargs):
        return self._ensure_uploader()(*args, **kwargs)

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

    # ── 核心 transfer 操作 ──

    def detect_transfer_range(self, source_link: str) -> Optional[dict]:
        future = asyncio.run_coroutine_threadsafe(
            self._detect_tr_range_async()(source_link),
            self.loop
        )
        return future.result(timeout=60)

    def start_download_upload(
        self,
        with_upload: Optional[dict],
        message: pyrogram.types.Message,
        file_path: str
    ) -> bool:
        if not isinstance(with_upload, dict):
            self._release_window()(with_upload)
            return False
        try:
            try:
                media_group = message.get_media_group()
            except Exception:
                media_group = None
            with_upload['message_id'] = getattr(message, 'id', None)
            with_upload['media_group'] = media_group
            with_upload.setdefault('_local_storage_release', None)
            self.ensure_uploader().download_upload(
                with_upload=with_upload,
                file_path=file_path
            )
            return True
        except Exception as e:
            error = f'创建上传任务失败:{e}'
            log.error(error, exc_info=True)
            callback = with_upload.get('failure_callback')
            if callable(callback):
                callback(with_upload, error)
            self._release_storage()(with_upload)
            self._release_window()(with_upload)
            return False

    # ── 下载/上传编排 ──

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
            temp_path=final_path,
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
        profile = self.infer_target_profile(target_link, target_profile)
        return {
            'link': target_link,
            'file_name': None,
            'with_delete': True if profile == 'pikpak' else self.gc.upload_delete,
            'send_as_media_group': (False if profile == 'pikpak' else True) if send_as_media_group is None else send_as_media_group,
            'task_id': task_id,
            'source_link': source_link,
            'source_folder': source_folder or source_folder_from_link(source_link),
            'target_profile': profile,
            'media_type': media_type,
            'on_file_ready': self._on_file_ready(),
            'status_callback': self._on_ul_status(),
            'progress_callback': self._on_ul_progress(),
            'skip_callback': self._on_item_skipped(),
            'failure_callback': self._on_item_failed()
        }

    def telegram_upload_size_limit_error(self, file_size: int) -> Optional[str]:
        is_premium = bool(getattr(getattr(self.app.client, 'me', None), 'is_premium', False))
        if is_allow_upload(file_size, is_premium):
            return None
        return '上传大小超过限制(普通用户2000MiB,会员用户4000MiB)'

    def get_download_upload_size_limit_error(
        self,
        task_with_upload: Optional[dict],
        file_size: int
    ) -> Optional[str]:
        if not isinstance(task_with_upload, dict):
            return None
        target_profile = task_with_upload.get('target_profile')
        limit = target_profile_limit(getattr(self, 'gc', None), target_profile)
        if limit is not None and file_size > limit:
            return target_profile_size_error(target_profile, file_size, limit)
        return self.telegram_upload_size_limit_error(file_size)

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
        console.log(
            f'{_t(KeyWord.DOWNLOAD_TASK)}'
            f'{_t(KeyWord.FILE)}:"{file_name}",'
            f'{_t(KeyWord.SIZE)}:{format_file_size},'
            f'{_t(KeyWord.TYPE)}:{_t(valid_dtype)},'
            f'{_t(KeyWord.STATUS)}:{_t(DownloadStatus.SKIP)}。'
            f'{error_message}'
        )
        DownloadTask.set_error(link=link, key=file_name, value=error_message)
        callback = task_with_upload.get('skip_callback') if isinstance(task_with_upload, dict) else None
        if callable(callback):
            task_with_upload['message_id'] = getattr(message, 'id', None)
            task_with_upload['media_type'] = valid_dtype
            task_with_upload['file_name'] = file_name
            task_with_upload['file_size'] = file_size
            callback(task_with_upload, error_message)
        self.notify_bot_transfer_upload_precheck_skipped(task_with_upload, file_name, file_size, error_message)
        self._release_window()(task_with_upload)

    def notify_bot_transfer_upload_precheck_skipped(
        self,
        task_with_upload: Optional[dict],
        file_name: str,
        file_size: int,
        error_message: str
    ) -> None:
        if not isinstance(task_with_upload, dict):
            return
        progress = task_with_upload.get('bot_progress')
        if not isinstance(progress, dict):
            return
        progress['file_name'] = file_name
        text = self._build_bot_progress_text()(
            progress,
            phase='skipped',
            current=file_size,
            total=file_size,
            error_message=error_message
        )
        self._schedule_bot_progress_update()(progress, text, force=True)

    def skip_transfer_item_for_target_limit(
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
            phase='skipped',
            status=TransferStatus.SKIPPED,
            error_message=limit_error.get('message')
        )
        self.transfer_store.add_event(task_id, limit_error.get('message'), level='warning', item_id=item_id)
        self.refresh_transfer_task_counts(task_id)
        return item_id

    @staticmethod
    def transfer_single_link(source_link: str) -> str:
        return source_link if '?single' in source_link else f'{source_link}?single'

    # ── 范围检测辅助 ──

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

    # ── 辅助方法 ──

    @property
    def message_filter(self) -> MessageFilter:
        """获取共享消息过滤器实例。config reload 时自动重建。"""
        current_mf = getattr(self.gc, 'message_filter', None)
        if not hasattr(self, '_message_filter') or self._msg_filter_config_id != id(current_mf):
            self._message_filter = MessageFilter(current_mf)
            self._msg_filter_config_id = id(current_mf)
        return self._message_filter

    def check_type(self, message: pyrogram.types.Message):
        """检查消息媒体类型是否允许（兼容旧接口，内部调用 MessageFilter）。"""
        return self.message_filter.should_pass_media_type(message)

    def get_media_meta(self, message: pyrogram.types.Message, dtype) -> Dict[str, Union[int, str]]:
        file_id: int = getattr(message, 'id')
        title_override = self.get_download_message_title(message)
        temp_file_path: str = self.app.get_temp_file_path(message, dtype, title_override=title_override)
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

    def __check_download_finish(
        self,
        message: pyrogram.types.Message,
        sever_file_size: int,
        temp_file_path: str,
        save_directory: str,
        with_move: bool = True
    ) -> bool:
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
        if task_id is not None and callable(getattr(_future, 'cancelled', None)) and _future.cancelled():
            self.app.current_task_num -= 1
            self._event().set()
            self._release_storage()(with_upload)
            self._release_window()(with_upload)
            try:
                self._queue().task_done()
            except (AttributeError, ValueError):
                pass
            try:
                self._pb_progress().remove_task(task_id=task_id)
            except AttributeError:
                pass
            return None, None
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
                self._record_dl_success()(
                    with_upload=with_upload,
                    message=message,
                    file_path=self.get_final_file_path(message, file_name, with_upload)
                )
                if not self.start_download_upload(
                    with_upload=with_upload,
                    message=message,
                    file_path=self.get_final_file_path(message, file_name, with_upload)
                ):
                    self._release_window()(with_upload)
            else:
                self._release_window()(with_upload)
        else:
            self.app.current_task_num -= 1
            self._event().set()
            if self.__check_download_finish(
                message=message,
                sever_file_size=sever_file_size,
                temp_file_path=temp_file_path,
                save_directory=self.get_final_save_directory(message, with_upload),
                with_move=True
            ):
                self._mark_storage_materialized()(with_upload)
                final_path = self.get_final_file_path(message, file_name, with_upload)
                self._record_dl_success()(
                    with_upload=with_upload,
                    message=message,
                    file_path=final_path
                )
                MetaData.print_current_task_num(
                    prompt=_t(KeyWord.CURRENT_DOWNLOAD_TASK),
                    num=self.app.current_task_num
                )
                if not self.start_download_upload(
                    with_upload=with_upload,
                    message=message,
                    file_path=final_path
                ):
                    self._release_window()(with_upload)
                self._queue().task_done()
            else:
                if retry_count < self.app.max_download_retries:
                    retry_count += 1
                    task = self.loop.create_task(
                        self._create_download_task()(
                            message_ids=link if isinstance(link, str) else message,
                            retry={'id': file_id, 'count': retry_count},
                            with_upload=with_upload,
                            diy_download_type=diy_download_type
                        )
                    )
                    task.add_done_callback(
                        partial(
                            self._retry_call,
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
                    self._bot_task_link().discard(link)
                    callback = with_upload.get('failure_callback') if isinstance(with_upload, dict) else None
                    if callable(callback):
                        with_upload['message_id'] = getattr(message, 'id', None)
                        callback(with_upload, _error)
                    self._release_window()(with_upload)
                    self._queue().task_done()
                link, file_name = None, None
            self._pb_progress().remove_task(task_id=task_id)
        return link, file_name

    def _process_links(self, link: Union[str, list]) -> Union[set, None]:
        start_content: str = 'https://t.me/'
        links: set = set()
        if isinstance(link, str):
            if link.endswith('.txt') and os.path.isfile(link):
                with open(file=link, mode='r', encoding='UTF-8') as _:
                    _links: list = [content.strip() for content in _.readlines()]
                for i in _links:
                    if i.startswith(start_content):
                        links.add(i)
                        self._bot_task_link().add(i)
                    elif i == '' or '#':
                        continue
                    else:
                        log.warning(f'"{i}"是一个非法链接,{_t(KeyWord.STATUS)}:{_t(DownloadStatus.SKIP)}。')
            elif link.startswith(start_content):
                links.add(link)
        elif isinstance(link, list):
            for i in link:
                _link: Union[set, None] = self._process_links(link=i)
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

    def _retry_call(self, notice, _future):
        self._queue().task_done()
        console.log(notice, style='#FF4689')
