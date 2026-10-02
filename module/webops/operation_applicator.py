# coding=UTF-8
"""WebUI 操作应用编排：watch / upload / channel_download 三类异步操作的执行。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出。它消费
``web_operation_queue`` 里排队的操作（``process_web_operation``），
按类型分派到「应用监听」「应用上传」「应用频道下载」，并负责启动时恢复
持久化的监听规则（``restore_live_transfer_watches``）。

依赖以回调注入；``LiveWatchApplicator`` 与 ``TelegramUploader`` 由宿主提供
（它们需要宿主作为上下文），本类只做编排。

注意：``apply_web_watch`` / ``remove_web_watch`` 转发给宿主的 watch applicator，
但**不经宿主方法**而是经注入的回调，避免"宿主覆盖实例属性"的语义被绕过。
"""
from __future__ import annotations

import os
from typing import Callable

from module import log
from module.core.enums import DownloadType, KeyWord, UploadStatus
from module.core.filter import Filter
from module.domain.archive_naming.source_folders import normalize_archive_title_source
from module.domain.transfer_state.models import UploadTask
from module.persistence.transfer_store import TransferStatus, TransferStore
from module.utils.language import _t
from module.utils.util import iter_discussion_reply_messages, make_forward_watch_rule, parse_link

from pyrogram.errors.exceptions.bad_request_400 import MsgIdInvalid


class WebOperationApplicator:
    """把排队的 WebUI 操作落到实际动作上。"""

    def __init__(
        self,
        *,
        web_operations_getter: Callable[[], dict],
        app_getter: Callable[[], object],
        gc_getter: Callable[[], object],
        uploader_getter: Callable[[], object],
        set_uploader: Callable[[object], None],
        runtime_message_filter_getter: Callable[[], object],
        watch_applicator_getter: Callable[[], object],
        persisted_watch_records_getter: Callable[[], list],
        listen_download_chat_getter: Callable[[], dict],
        listen_forward_chat_getter: Callable[[], dict],
        web_pending_watches_getter: Callable[[], dict],
        set_live_watch_status: Callable[..., None],
        mark_pending_watch: Callable[..., None],
        watch_payload_from_record: Callable[[dict], dict],
        create_download_task: Callable[..., object],
        uploader_context: object,
    ) -> None:
        self._web_operations = web_operations_getter
        self._app = app_getter
        self._gc = gc_getter
        self._uploader = uploader_getter
        self._set_uploader = set_uploader
        self._runtime_message_filter = runtime_message_filter_getter
        self._watch_applicator = watch_applicator_getter
        self._persisted_watch_records = persisted_watch_records_getter
        self._listen_download_chat = listen_download_chat_getter
        self._listen_forward_chat = listen_forward_chat_getter
        self._web_pending_watches = web_pending_watches_getter
        self._set_live_watch_status = set_live_watch_status
        self._mark_pending_watch = mark_pending_watch
        self._watch_payload_from_record = watch_payload_from_record
        self._create_download_task = create_download_task
        self._uploader_context = uploader_context

    # ── 队列消费 ──

    async def process_web_operation(self, operation_id: str) -> None:
        operation = self._web_operations().get(operation_id)
        if not operation:
            return
        operation["status"] = TransferStatus.RUNNING
        operation["updated_at"] = TransferStore.utc_now()
        try:
            operation_type = operation.get("type")
            payload = operation.get("payload") or {}
            if operation_type == "watch":
                await self.apply_web_watch(payload)
            elif operation_type == "upload":
                await self.apply_web_upload(payload)
            elif operation_type == "channel_download":
                await self.apply_web_channel_download(payload)
            else:
                raise ValueError(f"Unsupported WebUI operation: {operation_type}")
            operation["status"] = TransferStatus.SUCCESS
        except Exception as e:  # noqa: BLE001 - 操作失败要落到 operation 状态与日志
            operation["status"] = TransferStatus.FAILURE
            operation["error_message"] = str(e)
            payload = operation.get("payload") or {}
            if operation.get("type") == "watch":
                self._mark_pending_watch(payload, TransferStatus.FAILURE, str(e))
            log.exception(f'WebUI操作失败:{operation_id},{_t(KeyWord.REASON)}:"{e}"')
        finally:
            operation["updated_at"] = TransferStore.utc_now()

    # ── 监听 ──

    async def apply_web_watch(self, payload: dict) -> None:
        return await self._watch_applicator().apply_watch(payload)

    def remove_web_watch(self, watch_id: str) -> bool:
        return self._watch_applicator().remove_watch(watch_id)

    async def restore_live_transfer_watches(self) -> None:
        """启动时把持久化的监听规则重新挂上（已在监听字典里的跳过）。"""
        download_chat = self._listen_download_chat()
        forward_chat = self._listen_forward_chat()
        pending = self._web_pending_watches()
        for watch in self._persisted_watch_records():
            watch_id = watch.get("id")
            if not watch_id:
                continue
            if watch.get("type") == "download" and watch.get("source_link") in download_chat:
                continue
            if watch.get("type") == "forward":
                rule = make_forward_watch_rule(
                    watch.get("source_link"),
                    watch.get("target_link"),
                    bool(watch.get("include_comment")),
                    bool(watch.get("resolve_deep_link")),
                    bool(watch.get("archive_by_author")),
                    normalize_archive_title_source(watch.get("archive_title_source")),
                )
                if rule in forward_chat:
                    continue
            pending[watch_id] = {
                **watch,
                "status": TransferStatus.PENDING,
                "error_message": None,
            }
            self._set_live_watch_status(watch_id, TransferStatus.PENDING)
            payload = self._watch_payload_from_record(watch)
            try:
                await self.apply_web_watch(payload)
            except Exception as e:  # noqa: BLE001 - 单条监听恢复失败不阻断其余
                self._mark_pending_watch(payload, TransferStatus.FAILURE, str(e))
                log.exception(f'恢复WebUI实时监听失败:{watch_id},{_t(KeyWord.REASON)}:"{e}"')

    # ── 上传 ──

    async def apply_web_upload(self, payload: dict) -> None:
        uploader = self._uploader()
        if not uploader:
            from module.infra.uploader import TelegramUploader

            uploader = TelegramUploader(upload_context=self._upload_context())
            self._set_uploader(uploader)
        app = self._app()
        upload_path = payload.get("path")
        target_link = payload.get("target_link")
        recursive = bool(payload.get("recursive"))
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
            raise ValueError("Upload path contains no files.")
        for file_path in upload_files:
            file_size = os.path.getsize(file_path)
            upload_task = UploadTask(
                chat_id=None,
                file_path=file_path,
                file_id=app.client.rnd_id(),
                file_size=file_size,
                file_part=[],
                status=UploadStatus.PENDING,
                with_delete=self._gc().upload_delete,
            )
            await uploader.create_upload_task(link=target_link, upload_task=upload_task)

    def _upload_context(self):
        """构造 TelegramUploader 时需要宿主作为上传上下文（IUploadContext）。"""
        return self._uploader_context
    # ── 频道下载（按日期/类型/关键词遍历历史，可含评论区）──

    async def apply_web_channel_download(self, payload: dict) -> None:
        app = self._app()
        chat_link = payload.get("chat_link")
        meta = await parse_link(client=app.client, link=chat_link)
        chat_id = meta.get("chat_id")
        date_range = payload.get("date_range") or {}
        start_date = date_range.get("start_date")
        end_date = date_range.get("end_date")
        selected = set(payload.get("download_type") or [])
        download_type = {dtype: dtype in selected for dtype in DownloadType()}
        # 表单里给了下载类型就整表覆盖媒体白名单，否则继承全局允许列表。
        media_types_override = None
        if payload.get("download_type") is not None:
            from module.core.media_types import DOWNLOAD_MEDIA_TYPES, MEDIA_TYPES

            media_types_override = {t: False for t in MEDIA_TYPES}
            for dtype in DOWNLOAD_MEDIA_TYPES:
                media_types_override[dtype] = bool(download_type.get(dtype))
        keywords = payload.get("keywords") or []
        include_comment = bool(payload.get("include_comment"))
        filter_obj = Filter()
        runtime_filter = self._runtime_message_filter()
        if runtime_filter is None:
            runtime_filter = Filter({"media_types": download_type})

        def _media_ok(item) -> bool:
            if hasattr(runtime_filter, "should_pass_media_type"):
                return runtime_filter.should_pass_media_type(item)
            return filter_obj.dtype(item, download_type)

        links = []
        async for message in app.client.get_chat_history(chat_id=chat_id, reverse=True):
            if (
                filter_obj.date_range(message, start_date, end_date)
                and _media_ok(message)
                and filter_obj.keyword_filter(message, keywords)
            ):
                links.append(message.link if getattr(message, "link", None) else message)
                if include_comment:
                    try:
                        async for comment in iter_discussion_reply_messages(
                            client=app.client,
                            chat_id=chat_id,
                            message_id=message.id,
                            include_message=_media_ok,
                        ):
                            links.append(
                                comment.link if getattr(comment, "link", None) else comment
                            )
                    except (ValueError, AttributeError, MsgIdInvalid):
                        pass
        for link in links:
            await self._create_download_task(
                message_ids=link,
                single_link=True,
                diy_download_type=[_ for _ in DownloadType()],
            )
