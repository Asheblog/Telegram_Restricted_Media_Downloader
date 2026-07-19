# coding=UTF-8
import asyncio
import datetime
from typing import Callable, Optional, Union

from module.core.app import DownloadFileName
from module.diagnostics import RichDiagnosticAdapter
from module.enums import DownloadType
from module.transfer_store import TransferStatus
from module.path_tool import extract_full_extension, is_compressed_file
from module.source_folders import (
    archive_source_folder,
    resolve_forward_archive_source_folder,
    source_folder_from_link,
)
from module.core.target_profiles import target_profile_limit, target_profile_size_error


class PikpakIntegrationManager:
    def __init__(
            self,
            transfer_store_getter: Callable,
            pikpak_archive_client_getter: Callable,
            diagnostic: RichDiagnosticAdapter,
            gc_getter: Callable,
            refresh_counts: Callable[[int], None],
            cleanup_item_file: Callable[[int], bool] = None,
            app_getter: Callable = None,
            system_log=None,
    ):
        self._transfer_store_getter = transfer_store_getter
        self._pikpak_archive_client_getter = pikpak_archive_client_getter
        self.diagnostic = diagnostic
        self._gc_getter = gc_getter
        self._refresh_counts = refresh_counts
        self._cleanup_item_file = cleanup_item_file
        self._app_getter = app_getter
        self._system_log = system_log
        self._pikpak_archive_client = None

    @property
    def transfer_store(self):
        return self._transfer_store_getter()

    def get_pikpak_archive_client(self):
        if self._pikpak_archive_client is not None:
            return self._pikpak_archive_client
        self._pikpak_archive_client = self._pikpak_archive_client_getter()
        return self._pikpak_archive_client

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
            transferred_at: Optional[float] = None,
            match_original_name: Optional[bool] = None
    ):
        if target_profile != 'pikpak':
            return None
        folder = source_folder
        store = self.transfer_store
        item = None
        post_message_id = None
        archive_by_author = False
        task = None
        if store and task_id:
            task = store.get_task(int(task_id))
            if task:
                archive_by_author = bool(task.get('archive_by_author'))
        if store and item_id:
            item = store.get_item(int(item_id))
            if item:
                if not folder:
                    folder = item.get('source_folder')
                post_message_id = item.get('range_message_id')
        if not folder and store and task_id:
            if task is None:
                task = store.get_task(int(task_id))
            if task:
                task_source_link = task.get('source_link')
                item_source_link = (item or {}).get('source_link')
                if post_message_id is None:
                    post_message_id = (item or {}).get('range_message_id')
                task_source_folder = source_folder_from_link(task_source_link)
                item_source_folder = source_folder_from_link(item_source_link)
                if (
                        post_message_id is None
                        and item_source_link
                        and task_source_folder
                        and item_source_folder == task_source_folder
                ):
                    post_message_id = (item or {}).get('source_message_id')
                if task_source_link:
                    folder = archive_source_folder(
                        fallback_link=task_source_link,
                        post_message_id=post_message_id,
                        archive_by_author=archive_by_author,
                    )
        if post_message_id is None and item:
            item_source_link = item.get('source_link')
            if task is None and store and task_id:
                task = store.get_task(int(task_id))
            task_source_link = (task or {}).get('source_link')
            task_source_folder = source_folder_from_link(task_source_link)
            item_source_folder = source_folder_from_link(item_source_link)
            if (
                    item_source_link
                    and task_source_folder
                    and item_source_folder == task_source_folder
            ):
                post_message_id = item.get('source_message_id')
            elif not task_source_link and item.get('source_message_id') is not None:
                post_message_id = item.get('source_message_id')
        if not folder:
            # Prefer channel identity from source_link (deep-link/bot media must not become the folder).
            if source_folder_from_link(source_link):
                folder = archive_source_folder(
                    fallback_link=source_link,
                    post_message_id=post_message_id,
                    archive_by_author=archive_by_author,
                )
            else:
                folder = archive_source_folder(
                    message,
                    fallback_chat_id=getattr(getattr(message, 'chat', None), 'id', None),
                    fallback_link=source_link,
                    post_message_id=post_message_id,
                    archive_by_author=archive_by_author,
                )
        if message is not None:
            folder = resolve_forward_archive_source_folder(
                source_folder=folder,
                messages=[message],
                post_message_id=post_message_id if post_message_id is not None else getattr(message, 'id', None),
                fallback_chat_id=getattr(getattr(message, 'chat', None), 'id', None),
                fallback_link=source_link,
                archive_by_author=archive_by_author,
            )
        media_meta = self.get_message_media_target_limit_meta(
            message,
            post_message_id=post_message_id,
        ) if message is not None else None
        title_file_name = self.get_message_media_archive_filename(
            message,
            post_message_id=post_message_id,
        )
        file_name = file_name or title_file_name or (media_meta or {}).get('file_name')
        file_size = file_size if file_size is not None else (media_meta or {}).get('file_size')
        # Text-only / no-media messages must not create empty archive folders.
        if not file_name and (file_size is None or transferred_at is None):
            return None
        result = self.get_pikpak_archive_client().archive_file(
            source_folder=folder,
            file_name=file_name,
            file_size=file_size,
            transferred_at=transferred_at,
            match_original_name=(
                bool(match_original_name)
                if match_original_name is not None
                else not bool(title_file_name and file_name == title_file_name)
            )
        )
        archive_status = getattr(result, 'status', 'error')
        archive_path = getattr(result, 'archive_path', None)
        archive_message = getattr(result, 'message', '')
        archive_ok = bool(getattr(result, 'ok', False))
        if store and item_id:
            store.update_item(
                int(item_id),
                source_folder=folder,
                archive_status=archive_status,
                archive_path=archive_path,
                archive_error=None if archive_ok else archive_message
            )
        if store and task_id and archive_status != 'disabled':
            level = 'info' if archive_ok else 'warning'
            detail = archive_path or archive_message or archive_status
            store.add_event(
                int(task_id),
                f'PikPak archive {archive_status}: {detail}',
                level=level,
                item_id=int(item_id) if item_id else None
            )
        return result

    @staticmethod
    def transfer_item_archive_match_original_name(item: dict) -> Optional[bool]:
        value = item.get('archive_match_original_name')
        if value is None:
            return None
        return bool(int(value))

    @staticmethod
    def transfer_item_archive_timestamp(item: dict) -> float:
        for key in ('updated_at', 'created_at'):
            value = item.get(key)
            if not value:
                continue
            try:
                return datetime.datetime.fromisoformat(str(value)).timestamp()
            except ValueError:
                continue
        return datetime.datetime.now(datetime.UTC).timestamp()

    @staticmethod
    def get_message_media_archive_filename(
            message,
            post_message_id: Optional[Union[int, str]] = None,
    ) -> Optional[str]:
        if message is None:
            return None
        for dtype in DownloadType():
            media = getattr(message, dtype, None)
            if not media:
                continue
            try:
                if dtype == DownloadType.DOCUMENT and is_compressed_file(getattr(media, 'file_name', None)):
                    return None
                title = DownloadFileName(
                    message,
                    dtype,
                    message_id_override=post_message_id,
                ).get_message_title()
                if not title:
                    return None
                extension = PikpakIntegrationManager.get_message_media_archive_extension(dtype, media)
                message_id = post_message_id if post_message_id is not None else getattr(message, 'id', '0')
                try:
                    message_id = str(int(message_id))
                except (TypeError, ValueError):
                    message_id = str(message_id or '0')
                return '{} - {}.{}'.format(message_id, title, extension)
            except Exception:
                return None
        return None

    @staticmethod
    def get_message_media_archive_extension(dtype: str, media) -> str:
        origin_extension = extract_full_extension(getattr(media, 'file_name', None))
        if origin_extension:
            return origin_extension
        mime_type = str(getattr(media, 'mime_type', '') or '').lower()
        if dtype in (DownloadType.VIDEO, DownloadType.VIDEO_NOTE) or 'video' in mime_type:
            return 'mp4'
        if dtype == DownloadType.PHOTO or 'image' in mime_type:
            if 'png' in mime_type:
                return 'png'
            if 'webp' in mime_type:
                return 'webp'
            return 'jpg'
        if dtype == DownloadType.AUDIO or 'audio' in mime_type:
            return 'mp3'
        if dtype == DownloadType.VOICE:
            return 'ogg'
        if dtype == DownloadType.ANIMATION:
            return 'mp4'
        return 'unknown'

    @staticmethod
    def is_pikpak_archive_recoverable_item(item: dict) -> bool:
        if item.get('status') == TransferStatus.SUCCESS:
            return item.get('archive_status') in ('pending', 'not_found', 'error')
        if item.get('status') != TransferStatus.FAILURE:
            return False
        error_message = str(item.get('error_message') or '')
        return 'PikPak ingest confirmation' in error_message or 'PikPak archive' in error_message

    def _log_item_failure_system_chain(
            self,
            *,
            task_id: int,
            item_id: int,
            message: str,
            item: Optional[dict] = None,
    ) -> None:
        tracer = self._system_log
        if tracer is None or not callable(getattr(tracer, 'log', None)):
            return
        row = item or {}
        if not row and self.transfer_store:
            row = self.transfer_store.get_item(int(item_id)) or {}
        tracer.log(
            category='transfer',
            stage='item_failure',
            message=message,
            level='error',
            source_chat_id=row.get('source_chat_id'),
            source_message_id=row.get('source_message_id'),
            target_link=row.get('target_link'),
            details={
                'task_id': int(task_id),
                'item_id': int(item_id),
                'source_link': row.get('source_link') or '',
            },
        )

    def fail_transfer_item(
            self,
            task_id: int,
            item_id: int,
            message: str
    ) -> None:
        store = self.transfer_store
        item = store.get_item(int(item_id)) if store else None
        store.update_item(
            item_id,
            phase='failure',
            status=TransferStatus.FAILURE,
            error_message=message
        )
        store.add_event(
            task_id,
            message,
            level='error',
            item_id=item_id
        )
        self._log_item_failure_system_chain(
            task_id=int(task_id),
            item_id=int(item_id),
            message=message,
            item=item,
        )
        self._refresh_counts(task_id)
        if callable(self._cleanup_item_file):
            try:
                self._cleanup_item_file(int(item_id))
            except Exception as e:
                self.diagnostic.warning(f'PikPak failure cleanup failed: {e}')

    def skip_empty_transfer_source_message(
            self,
            task: dict,
            origin_chat_id,
            source_link: str,
            message_id: Optional[int]
    ) -> int:
        task_id = int(task.get('id'))
        error_message = f'Telegram API returned an empty source message: {source_link}'
        store = self.transfer_store
        item_id = store.add_item(
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
        store.add_event(
            task_id,
            error_message,
            level='warning',
            item_id=item_id
        )
        self._refresh_counts(task_id)
        return item_id

    def complete_forwarded_pikpak_item(
            self,
            task: dict,
            item_id: int,
            task_id: int,
            message,
            source_link: str,
            transferred_at: float,
            source_folder: Optional[str] = None,
    ) -> bool:
        archive_result = self.archive_pikpak_item(
            target_profile=task.get('target_profile'),
            item_id=item_id,
            task_id=task_id,
            message=message,
            source_link=source_link,
            source_folder=source_folder,
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
        store = self.transfer_store
        store.update_item(
            item_id,
            phase='forwarded',
            status=TransferStatus.SUCCESS,
            error_message=''
        )
        store.add_event(
            task_id,
            f'Direct forward succeeded: {source_link}',
            item_id=item_id
        )
        self._refresh_counts(task_id)
        return True

    def get_message_media_target_limit_meta(
            self,
            message,
            post_message_id: Optional[Union[int, str]] = None,
    ) -> Optional[dict]:
        for dtype in DownloadType():
            media = getattr(message, dtype, None)
            if not media:
                continue
            file_size = getattr(media, 'file_size', None)
            if file_size is None:
                continue
            archive_file_name = PikpakIntegrationManager.get_message_media_archive_filename(
                message,
                post_message_id=post_message_id,
            )
            return {
                'media_type': dtype,
                'file_size': int(file_size),
                'file_name': archive_file_name or getattr(media, 'file_name', None)
            }
        return None

    def get_task_target_size_limit_error(self, task: dict, message) -> Optional[dict]:
        target_profile = task.get('target_profile')
        gc = self._gc_getter()
        limit = target_profile_limit(gc, target_profile)
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
            '不支持',
            'unsupported',
            'not supported',
            'failed',
            'error'
        ))

    @staticmethod
    def message_has_pikpak_ingestible_media(message) -> bool:
        """True when the message carries media PikPak can typically save (not bare text)."""
        if message is None:
            return False
        from module.core.media_types import DOWNLOAD_MEDIA_TYPES
        for dtype in DOWNLOAD_MEDIA_TYPES:
            if getattr(message, dtype, None):
                return True
        return False

    async def wait_for_pikpak_ingest_confirmation(
            self,
            target_chat_id,
            forwarded_message=None,
            timeout_seconds: float = 15,
            poll_interval: float = 3
    ) -> bool:
        app = self._app_getter() if self._app_getter else None
        if not app or not getattr(app, 'client', None):
            return False
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
            async for target_message in app.client.get_chat_history(target_chat_id, limit=10):
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
