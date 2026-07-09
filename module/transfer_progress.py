# coding=UTF-8
import asyncio
import datetime
import os
import time
from typing import Callable, Optional

from pyrogram.errors import (
    FloodWait,
    FloodPremiumWait
)
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

from module import LINK_PREVIEW_OPTIONS
from module.diagnostics import RichDiagnosticAdapter
from module.enums import UploadStatus, KeyWord
from module.language import _t
from module.stdio import MetaData
from module.transfer_store import TransferStatus


class TransferProgressTracker:
    def __init__(
            self,
            transfer_store_getter: Callable,
            diagnostic: RichDiagnosticAdapter,
            app_getter: Callable,
            gc_getter: Callable,
            loop_getter: Callable,
            pb_getter: Callable,
            release_storage: Callable,
            release_window: Callable,
            start_download_upload: Callable,
            archive_pikpak_item: Callable,
            fail_transfer_item: Callable,
            refresh_counts: Callable,
            schedule_override: Callable = None,
            notify_status_override: Callable = None,
            notify_progress_override: Callable = None,
            cleanup_local_file: Callable = None,
    ):
        self._transfer_store_getter = transfer_store_getter
        self.diagnostic = diagnostic
        self._app_getter = app_getter
        self._gc_getter = gc_getter
        self._loop_getter = loop_getter
        self._pb_getter = pb_getter
        self._release_storage = release_storage
        self._release_window = release_window
        self._start_download_upload = start_download_upload
        self._archive_pikpak_item = archive_pikpak_item
        self._fail_transfer_item = fail_transfer_item
        self._refresh_counts = refresh_counts
        self._schedule_override = schedule_override
        self._notify_status_override = notify_status_override
        self._notify_progress_override = notify_progress_override
        self._cleanup_local_file = cleanup_local_file
        self._speed_samples = {}

    @property
    def transfer_store(self):
        return self._transfer_store_getter()

    @property
    def pb(self):
        return self._pb_getter()

    @property
    def loop(self):
        return self._loop_getter()

    def transfer_download_progress(
            self,
            current: int,
            total: int,
            progress,
            task_id: int,
            with_upload: Optional[dict] = None
    ) -> None:
        self.pb.download(current, total, progress, task_id)
        self.notify_bot_transfer_download_progress(with_upload, current, total)
        store = self.transfer_store
        if not store or not isinstance(with_upload, dict):
            return
        item_id = with_upload.get('item_id')
        if item_id:
            speed_bps = self._sample_speed(('download', int(item_id)), current)
            store.update_item_progress(
                item_id=int(item_id),
                phase='downloading',
                download_current=current,
                download_total=total,
                download_speed_bps=speed_bps
            )

    @staticmethod
    def transfer_percent(current: int, total: int) -> str:
        if not total:
            return '0.0%'
        return f'{min(max(current / total, 0), 1) * 100:.1f}%'

    @staticmethod
    def transfer_size_text(current: int, total: int) -> str:
        return f'{MetaData.suitable_units_display(current)}/{MetaData.suitable_units_display(total)}'

    def build_bot_transfer_progress_text(
            self,
            progress: dict,
            phase: str,
            current: int = 0,
            total: int = 0,
            error_message: Optional[str] = None
    ) -> str:
        file_name = progress.get('file_name') or '等待识别文件名'
        source = progress.get('source_link') or f'消息 {progress.get("source_message_id")}'
        target = progress.get('target_link') or progress.get('target_chat_id') or '目标会话'
        if phase == 'downloading':
            status = f'📥 下载中 {self.transfer_percent(current, total)}'
            detail = self.transfer_size_text(current, total)
        elif phase == 'downloaded':
            status = '📥 下载完成，等待上传'
            detail = self.transfer_size_text(total or current, total or current) if (current or total) else ''
        elif phase == 'uploading':
            status = f'📤 上传中 {self.transfer_percent(current, total)}'
            detail = self.transfer_size_text(current, total)
        elif phase == 'uploaded':
            status = '📤 上传完成，等待发送到目标'
            detail = self.transfer_size_text(total or current, total or current) if (current or total) else ''
        elif phase == 'sent':
            status = '✅ 已发送到目标'
            detail = ''
        elif phase == 'failed':
            status = '❌ 上传失败'
            detail = error_message or '未知错误'
        elif phase == 'skipped':
            status = '⚠️ 已跳过'
            detail = error_message or ''
        else:
            status = '⏳ 转存处理中'
            detail = ''
        lines = [
            '📦 监听转存进度',
            f'状态: {status}',
            f'文件: {file_name}',
            f'来源: {source}',
            f'目标: {target}'
        ]
        if detail:
            lines.append(f'进度: {detail}')
        return '\n'.join(lines)

    def schedule_bot_transfer_progress_update(self, progress: Optional[dict], text: str, force: bool = False) -> None:
        if self._schedule_override is not None:
            self._schedule_override(progress, text, force)
            return
        if not isinstance(progress, dict):
            return
        client = progress.get('client')
        chat_id = progress.get('chat_id')
        message_id = progress.get('message_id')
        if not all([client, chat_id, message_id]):
            return
        now = datetime.datetime.now(datetime.UTC).timestamp()
        min_interval = float(progress.get('min_interval', 8) or 0)
        if not force and now - float(progress.get('last_update_at') or 0) < min_interval:
            return
        if text == progress.get('last_text'):
            return
        progress['last_update_at'] = now
        progress['last_text'] = text

        async def _edit_progress_message() -> None:
            while True:
                try:
                    await client.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        link_preview_options=LINK_PREVIEW_OPTIONS
                    )
                    break
                except MessageNotModified:
                    break
                except (FloodWait, FloodPremiumWait) as e:
                    await asyncio.sleep(max(0, int(getattr(e, 'value', 0) or 0)))
                except Exception as e:
                    self.diagnostic.warning(f'无法更新监听转存进度消息,{_t(KeyWord.REASON)}:"{e}"')
                    break

        try:
            loop = self.loop or asyncio.get_running_loop()
            loop.create_task(_edit_progress_message())
        except RuntimeError:
            self.diagnostic.warning('无法更新监听转存进度消息,当前没有运行中的事件循环。')

    def notify_bot_transfer_download_progress(self, with_upload: Optional[dict], current: int, total: int) -> None:
        if not isinstance(with_upload, dict):
            return
        progress = with_upload.get('bot_progress')
        if not isinstance(progress, dict):
            return
        if with_upload.get('file_name') and not progress.get('file_name'):
            progress['file_name'] = with_upload.get('file_name')
        text = self.build_bot_transfer_progress_text(progress, phase='downloading', current=current, total=total)
        self.schedule_bot_transfer_progress_update(progress, text)

    def notify_bot_transfer_downloaded(self, with_upload: Optional[dict], file_size: Optional[int]) -> None:
        if not isinstance(with_upload, dict):
            return
        progress = with_upload.get('bot_progress')
        if not isinstance(progress, dict):
            return
        if with_upload.get('file_name') and not progress.get('file_name'):
            progress['file_name'] = with_upload.get('file_name')
        size = int(file_size or 0)
        text = self.build_bot_transfer_progress_text(progress, phase='downloaded', current=size, total=size)
        self.schedule_bot_transfer_progress_update(progress, text, force=True)

    def notify_bot_transfer_upload_progress(self, upload_task, current: int, total: int) -> None:
        if self._notify_progress_override is not None:
            self._notify_progress_override(upload_task, current, total)
            return
        meta = getattr(upload_task, 'transfer_meta', {}) or {}
        progress = meta.get('bot_progress')
        if not isinstance(progress, dict):
            return
        if getattr(upload_task, 'file_name', None):
            progress['file_name'] = getattr(upload_task, 'file_name')
        text = self.build_bot_transfer_progress_text(progress, phase='uploading', current=current, total=total)
        self.schedule_bot_transfer_progress_update(progress, text)

    def notify_bot_transfer_upload_status(self, upload_task) -> None:
        if self._notify_status_override is not None:
            self._notify_status_override(upload_task)
            return
        meta = getattr(upload_task, 'transfer_meta', {}) or {}
        progress = meta.get('bot_progress')
        if not isinstance(progress, dict):
            return
        if getattr(upload_task, 'file_name', None):
            progress['file_name'] = getattr(upload_task, 'file_name')
        size = int(getattr(upload_task, 'file_size', 0) or 0)
        if upload_task.status == UploadStatus.SUCCESS:
            text = self.build_bot_transfer_progress_text(progress, phase='uploaded', current=size, total=size)
            self.schedule_bot_transfer_progress_update(progress, text, force=True)
        elif upload_task.status == UploadStatus.SENT:
            text = self.build_bot_transfer_progress_text(progress, phase='sent', current=size, total=size)
            self.schedule_bot_transfer_progress_update(progress, text, force=True)
        elif upload_task.status == UploadStatus.FAILURE:
            text = self.build_bot_transfer_progress_text(
                progress,
                phase='failed',
                current=size,
                total=size,
                error_message=getattr(upload_task, 'error_msg', None)
            )
            self.schedule_bot_transfer_progress_update(progress, text, force=True)

    def record_transfer_download_success(
            self,
            with_upload: Optional[dict],
            message,
            file_path: str
    ) -> None:
        if not isinstance(with_upload, dict):
            return
        file_size = with_upload.get('file_size')
        if file_size is None and os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
        self.notify_bot_transfer_downloaded(with_upload, file_size)
        store = self.transfer_store
        if not store:
            return
        item_id = with_upload.get('item_id')
        if item_id:
            store.update_item(
                int(item_id),
                local_path=file_path,
                file_name=with_upload.get('file_name') or os.path.basename(file_path),
                file_size=file_size,
                phase='downloaded'
            )
            store.update_item_progress(
                int(item_id),
                phase='downloaded',
                download_current=file_size or 0,
                download_total=file_size or 0,
                download_speed_bps=0
            )
        source_chat_id = with_upload.get('source_chat_id')
        source_message_id = with_upload.get('message_id') or getattr(message, 'id', None)
        if source_chat_id and source_message_id and os.path.isfile(file_path):
            store.upsert_download_success_record(
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
            message,
            expected_size: int
    ) -> Optional[str]:
        store = self.transfer_store
        if (
                not isinstance(task_with_upload, dict)
                or not store
                or not task_with_upload.get('source_chat_id')
                or not task_with_upload.get('message_id')
        ):
            return None
        record = store.get_download_success_record(
            source_chat_id=str(task_with_upload.get('source_chat_id')),
            source_message_id=int(task_with_upload.get('message_id')),
            expected_size=expected_size
        )
        if not record:
            return None
        local_path = record.get('local_path')
        item_id = task_with_upload.get('item_id')
        if item_id:
            store.update_item(
                int(item_id),
                local_path=local_path,
                file_name=record.get('file_name'),
                file_size=record.get('file_size'),
                phase='downloaded'
            )
            store.update_item_progress(
                int(item_id),
                phase='downloaded',
                download_current=expected_size,
                download_total=expected_size,
                download_speed_bps=0
            )
            store.add_event(
                int(task_with_upload.get('task_id')),
                f'Reused download success record: {record.get("file_name") or os.path.basename(local_path)}',
                item_id=int(item_id)
            )
        if not self._start_download_upload(
                with_upload=task_with_upload,
                message=message,
                file_path=local_path
        ):
            self._release_storage(task_with_upload)
            self._release_window(task_with_upload)
        return local_path

    def on_transfer_upload_progress(self, upload_task, current: int, total: int) -> None:
        self.notify_bot_transfer_upload_progress(upload_task, current, total)
        store = self.transfer_store
        if not store:
            return
        meta = getattr(upload_task, 'transfer_meta', {}) or {}
        item_id = meta.get('item_id')
        if not item_id:
            return
        speed_bps = self._sample_speed(('upload', int(item_id)), current)
        store.update_item_progress(
            item_id=int(item_id),
            phase='uploading',
            upload_current=current,
            upload_total=total,
            upload_speed_bps=speed_bps
        )

    def _sample_speed(self, key, current: int) -> int:
        now = time.monotonic()
        current = int(current or 0)
        previous = self._speed_samples.get(key)
        self._speed_samples[key] = (now, current)
        if not previous:
            return 0
        previous_at, previous_current = previous
        elapsed = max(now - previous_at, 0)
        if elapsed <= 0:
            return 0
        delta = max(0, current - int(previous_current or 0))
        return int(delta / elapsed)

    def on_transfer_file_ready(self, file_path: str, with_upload: dict) -> int:
        store = self.transfer_store
        if not store:
            return 0
        task_id = int(with_upload.get('task_id'))
        item_id = store.add_item(
            task_id=task_id,
            source_chat_id=with_upload.get('source_chat_id'),
            source_message_id=with_upload.get('message_id'),
            source_link=with_upload.get('source_link'),
            target_link=with_upload.get('link'),
            media_type=with_upload.get('media_type'),
            file_name=with_upload.get('file_name') or os.path.basename(file_path),
            file_size=with_upload.get('file_size') or (os.path.getsize(file_path) if os.path.isfile(file_path) else None),
            local_path=file_path,
            temp_path=with_upload.get('temp_path'),
            source_folder=with_upload.get('source_folder'),
            archive_status='pending' if with_upload.get('target_profile') == 'pikpak' else None,
            archive_match_original_name=True if with_upload.get('target_profile') == 'pikpak' else None,
            phase='uploading',
            status=TransferStatus.RUNNING
        )
        store.add_event(task_id, f'File ready for target upload: {os.path.basename(file_path)}', item_id=item_id)
        self._refresh_counts(task_id)
        return item_id

    def on_transfer_item_skipped(self, with_upload: dict, message: str) -> None:
        self._release_storage(with_upload)
        store = self.transfer_store
        if not store or not isinstance(with_upload, dict) or not with_upload.get('task_id'):
            return
        task_id = int(with_upload.get('task_id'))
        item_id = with_upload.get('item_id')
        if item_id:
            item_id = int(item_id)
            store.update_item(
                item_id,
                media_type=with_upload.get('media_type'),
                file_name=with_upload.get('file_name'),
                file_size=with_upload.get('file_size'),
                phase='skipped',
                status=TransferStatus.SKIPPED,
                error_message=message
            )
        else:
            item_id = store.add_item(
                task_id=task_id,
                source_chat_id=with_upload.get('source_chat_id'),
                source_message_id=with_upload.get('message_id'),
                source_link=with_upload.get('source_link'),
                target_link=with_upload.get('link'),
                media_type=with_upload.get('media_type'),
                file_name=with_upload.get('file_name'),
                file_size=with_upload.get('file_size'),
                phase='skipped',
                status=TransferStatus.SKIPPED,
                error_message=message
            )
        store.add_event(task_id, message, level='warning', item_id=item_id)
        self._refresh_counts(task_id)
        self._try_cleanup(item_id)

    def on_transfer_item_failed(self, with_upload: dict, message: str) -> None:
        self._release_storage(with_upload)
        store = self.transfer_store
        if not store or not isinstance(with_upload, dict) or not with_upload.get('task_id'):
            return
        task_id = int(with_upload.get('task_id'))
        item_id = store.add_item(
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
        store.add_event(task_id, message, level='error', item_id=item_id)
        self._refresh_counts(task_id)
        self._try_cleanup(item_id)

    def on_transfer_upload_status(self, upload_task) -> None:
        self.notify_bot_transfer_upload_status(upload_task)
        meta = getattr(upload_task, 'transfer_meta', {}) or {}
        task_id = meta.get('task_id')
        item_id = meta.get('item_id')
        if upload_task.status == UploadStatus.SENT:
            archive_result = self._archive_pikpak_item(
                target_profile=meta.get('target_profile'),
                item_id=item_id,
                task_id=task_id,
                message=None,
                source_link=meta.get('source_link'),
                source_folder=meta.get('source_folder'),
                file_name=upload_task.file_name,
                file_size=getattr(upload_task, 'file_size', None),
                transferred_at=datetime.datetime.now(datetime.UTC).timestamp(),
                match_original_name=False
            )
            if (
                    archive_result is not None
                    and getattr(archive_result, 'status', None) != 'disabled'
                    and not bool(getattr(archive_result, 'ok', False))
            ):
                archive_status = getattr(archive_result, 'status', 'error')
                archive_message = getattr(archive_result, 'message', '')
                error_message = (
                    f'PikPak archive {archive_status}: '
                    f'{archive_message or meta.get("source_link") or upload_task.file_name}'
                )
                store = self.transfer_store
                if store and task_id and item_id:
                    self._fail_transfer_item(int(task_id), int(item_id), error_message)
                else:
                    self.diagnostic.warning(error_message)
                return
            store = self.transfer_store
            if store and task_id and item_id:
                store.update_item(item_id, status=TransferStatus.SUCCESS, phase='sent', error_message='')
                store.add_event(task_id, f'Sent to target: {upload_task.file_name}', item_id=item_id)
                self._try_cleanup(int(item_id))
        elif upload_task.status == UploadStatus.FAILURE:
            store = self.transfer_store
            if store and task_id and item_id:
                store.update_item(
                    item_id,
                    status=TransferStatus.FAILURE,
                    phase='failure',
                    error_message=upload_task.error_msg
                )
                store.add_event(task_id, f'Upload failed: {upload_task.error_msg}', level='error', item_id=item_id)
                self._try_cleanup(int(item_id))
        store = self.transfer_store
        if store and task_id:
            self._refresh_counts(int(task_id))

    def _try_cleanup(self, item_id) -> None:
        """尝试清理 transfer item 对应的本地文件（预防性清理）。"""
        if not callable(self._cleanup_local_file):
            return
        try:
            item_id = int(item_id)
        except (TypeError, ValueError):
            return
        try:
            self._cleanup_local_file(item_id)
        except Exception:
            pass  # 清理失败不应阻断主流程
