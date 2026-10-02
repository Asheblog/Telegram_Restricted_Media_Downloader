# coding=UTF-8
"""WebUI 业务操作编排 —— IWebUiOperations / IWatchOps / ITaskOps 的实现。

从 adapters/webui 迁出（原先与 HTTP 壳同目录）：本文件零 HTTP 原语，作为**宿主门面**
按名字暴露各编排协作者的能力；具体实现见同包的
stats / diagnostics / media_cleanup / watch_operations / settings_operations /
setup_wizard / task_queue / runtime_recovery / transfer_range /
operation_applicator / deferred_discussion，以及 archive_author_ops 等。

放在 webops 编排层是刻意的依赖方向：编排组合适配器，而不是反过来。
architecture_guard 的 test_no_layer_inversions 已登记该层（adapters 不得 import webops）。

注意：旧路径 ``module/adapters/webui/operations.py`` **已删除**（本层迁出时一起移走，
测试的 patch 目标也已同步更新）——不要再引用该路径。
"""
import asyncio
import os
from typing import Optional

import pyrogram
from pyrogram.errors import FloodWait

from module import console, log
from module.adapters.pikpak.integration import PikpakIntegrationManager
from module.adapters.webui.server import (
    WebUiServer,
    get_web_host_from_env,
    get_web_password_from_env,
    get_web_port_from_env,
    get_web_username_from_env,
)
from module.domain.archive_naming.source_folders import (
    archive_source_folder,
    normalize_archive_title_source,
)
from module.persistence.media_manager import MediaManager
from module.persistence.transfer_store import TransferStatus, TransferStore
from module.transfer.comment_delay import CommentDelayScheduler
from module.transfer.pikpak_rules import (
    transfer_item_archive_match_original_name,
    transfer_item_archive_timestamp,
)
from module.transfer.watch_applicator import LiveWatchApplicator
from module.utils.parser import PARSE_ARGS
from module.utils.util import parse_link



def _require_web_task_manager(host):
    """Return host.web_task_manager, lazily wiring a manager for bare test hosts."""
    wm = getattr(host, 'web_task_manager', None)
    if wm is not None:
        return wm
    from module.webops.task_manager import WebUITaskManager

    if getattr(host, 'web_task_queue', None) is None:
        host.web_task_queue = asyncio.Queue()
    if getattr(host, 'web_submitted_task_ids', None) is None:
        host.web_submitted_task_ids = set()
    if getattr(host, 'web_operation_queue', None) is None:
        host.web_operation_queue = asyncio.Queue()
    if getattr(host, 'web_operations', None) is None:
        host.web_operations = {}
    if not hasattr(host, 'web_running_task'):
        host.web_running_task = None
    if not hasattr(host, 'web_running_task_id'):
        host.web_running_task_id = None
    wm = WebUITaskManager(
        transfer_store_getter=lambda: getattr(host, 'transfer_store', None),
        diagnostic=getattr(host, 'diagnostic', None),
        loop_getter=lambda: getattr(host, 'loop', None),
        web_task_queue=host.web_task_queue,
        web_submitted_task_ids=host.web_submitted_task_ids,
        web_running_task_getter=lambda: getattr(host, 'web_running_task', None),
        web_running_task_setter=lambda v: setattr(host, 'web_running_task', v),
        web_running_task_id_getter=lambda: getattr(host, 'web_running_task_id', None),
        web_running_task_id_setter=lambda v: setattr(host, 'web_running_task_id', v),
        web_operation_queue=host.web_operation_queue,
        web_operations=host.web_operations,
        watch_manager_getter=lambda: getattr(host, 'watch_manager', None),
        pikpak_manager_getter=lambda: getattr(host, 'pikpak_manager', None),
        progress_tracker_getter=lambda: getattr(host, 'progress_tracker', None),
        archive_pikpak_item_getter=getattr(host, 'archive_pikpak_item', None),
        refresh_transfer_task_counts_getter=getattr(host, 'refresh_transfer_task_counts', None),
        process_web_transfer_task_getter=getattr(host, 'process_web_transfer_task', None),
        retry_watch_inline_task_getter=getattr(host, 'retry_watch_inline_task', None),
        process_web_task_queue_getter=getattr(host, 'process_web_task_queue', None),
        cleanup_task_files_getter=lambda task_id: (
            host._ensure_media_manager().cleanup_task_files(task_id)
            if hasattr(host, '_ensure_media_manager')
            else {'failed': []}
        ),
        uploader_getter=lambda: getattr(host, 'uploader', None),
    )
    host.web_task_manager = wm
    return wm


class WebOperationsMixin:
    # Fallback id counter for hosts assembled without a WebUITaskManager.
    web_operation_counter: int = 0

    def _ensure_transfer_store(self) -> TransferStore:
        store = getattr(self, 'transfer_store', None)
        if store is not None:
            self._bind_transfer_store_runtime(store)
            return store
        temp_directory = getattr(getattr(self, 'app', None), 'temp_directory', None)
        if not temp_directory:
            raise RuntimeError('temp_directory is required to create TransferStore')
        store = TransferStore(directory=temp_directory)
        self.transfer_store = store
        ctx = self.__dict__.get('ctx')
        if ctx is not None:
            ctx.transfer_store = store
        system_log = getattr(self, 'system_log', None)
        if system_log is not None:
            system_log.bind(store=store)
        self._bind_transfer_store_runtime(store)
        return store

    def _bind_transfer_store_runtime(self, store: TransferStore) -> None:
        gc = getattr(self, 'gc', None)
        if gc is not None and hasattr(store, 'set_item_stale_timeout_seconds_getter'):
            store.set_item_stale_timeout_seconds_getter(
                lambda: int(gc.get_item_stale_timeout_minutes()) * 60
            )
        log_system = getattr(self, '_log_system_chain', None)
        if callable(log_system) and hasattr(store, 'set_stale_item_logger'):

            def _stale_logger(item_id: int, task_id: int, message: str) -> None:
                log_system(
                    category='transfer',
                    stage='item_stale_timeout',
                    message=message,
                    level='warning',
                    details={
                        'task_id': int(task_id),
                        'item_id': int(item_id),
                    },
                )

            store.set_stale_item_logger(_stale_logger)

    def _persisted_watch_records(self) -> list:
        watch_manager = getattr(self, "watch_manager", None)
        if watch_manager is not None and hasattr(watch_manager, "persisted_watches"):
            return watch_manager.persisted_watches()
        return self.persisted_watches()

    def _set_live_watch_status(self, watch_id: str, status: str, error_message: str = None) -> None:
        watch_manager = getattr(self, "watch_manager", None)
        if watch_manager is not None and hasattr(watch_manager, "set_live_watch_status"):
            watch_manager.set_live_watch_status(watch_id, status, error_message)
            return
        self.set_live_watch_status(watch_id, status, error_message)

    def _watch_payload_from_record(self, watch: dict) -> dict:
        watch_manager = getattr(self, "watch_manager", None)
        if watch_manager is not None and hasattr(watch_manager, "watch_payload_from_record"):
            return watch_manager.watch_payload_from_record(watch)
        return self.watch_payload_from_record(watch)

    def _ensure_deferred_discussion_ops(self):
        """延迟抓取编排实例（懒建并缓存；实现见 module.webops.deferred_discussion）。"""
        ops = self.__dict__.get('_deferred_discussion_ops_impl')
        if ops is None:
            from module.webops.deferred_discussion import DeferredDiscussionOperations

            ops = DeferredDiscussionOperations(
                transfer_store_getter=self._ensure_transfer_store,
                user_getter=lambda: getattr(self, 'user', None),
                app_getter=lambda: getattr(self, 'app', None),
                gc_getter=lambda: getattr(self, 'gc', None),
                loop_getter=lambda: getattr(self, 'loop', None),
                # 经实例解析：宿主/测试替身会覆盖这些方法。
                forward_discussion_replies=lambda *a, **kw: self.forward_discussion_replies(
                    *a, **kw
                ),
                record_watch_event=lambda *a, **kw: self._record_watch_event(*a, **kw),
                delete_web_task=lambda task_id: self.delete_web_task(task_id),
            )
            self._deferred_discussion_ops_impl = ops
        return ops

    def _ensure_comment_delay_scheduler(self) -> CommentDelayScheduler:
        return self._ensure_deferred_discussion_ops().ensure_scheduler()

    def _has_active_derived_tasks_for_deferred_capture(self, capture: dict) -> bool:
        return self._ensure_deferred_discussion_ops().has_active_derived_tasks(capture)

    def _cancel_derived_tasks_for_deferred_capture(self, capture: dict) -> None:
        """Best-effort cancel web transfer tasks spawned by a running deferred capture."""
        return self._ensure_deferred_discussion_ops().cancel_derived_tasks(capture)

    async def schedule_or_forward_discussion_replies(
            self,
            *,
            client,
            source_chat_id,
            source_message_id: int,
            target_chat_id,
            target_link: str,
            watch_id: Optional[str] = None,
            done_notice: Optional[bool] = True,
    ) -> Optional[dict]:
        return await self._ensure_deferred_discussion_ops().schedule_or_forward(
            client=client,
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            target_chat_id=target_chat_id,
            target_link=target_link,
            watch_id=watch_id,
            done_notice=done_notice,
        )

    def _web_ui_operations(self) -> 'WebOperationsFacade':
        facade = self.__dict__.get('_web_operations_facade')
        if facade is None:
            facade = WebOperationsFacade(self)
            self._web_operations_facade = facade
        return facade

    def _require_web_task_manager(self):
        return _require_web_task_manager(self)

    def should_continue_web_transfer_task(self, task_id: int) -> bool:
        return _require_web_task_manager(self).should_continue_web_transfer_task(task_id)

    def should_continue_web_transfer_item(self, item_id: int) -> bool:
        """False once reconcile/UI marked the item failed — abort in-flight IO cooperatively."""
        return _require_web_task_manager(self).should_continue_web_transfer_item(item_id)

    def should_start_next_web_transfer_item(self, task_id: int) -> bool:
        """Whether a new Transfer Item may start. False while pausing/paused."""
        return _require_web_task_manager(self).should_start_next_web_transfer_item(task_id)

    def has_active_transfer_io(self, task_id: int) -> bool:
        return _require_web_task_manager(self).has_active_transfer_io(task_id)

    async def settle_web_task_pause_request(self, task_id: int, *, before: str | None = None) -> bool:
        """Wait out in-flight IO while pausing, then finalize to paused. Return True to stop."""
        return await _require_web_task_manager(self).settle_web_task_pause_request(
            task_id, before=before
        )

    def cancel_task_uploads(self, task_id: int) -> int:
        return _require_web_task_manager(self).cancel_task_uploads(task_id)

    def pause_task_uploads(self, task_id: int) -> int:
        return _require_web_task_manager(self).pause_task_uploads(task_id)

    def _transfer_download_registry(self) -> dict:
        return _require_web_task_manager(self)._transfer_download_registry()

    def _register_transfer_download_task(self, with_upload: Optional[dict], download_task: asyncio.Task) -> None:
        return _require_web_task_manager(self)._register_transfer_download_task(
            with_upload, download_task
        )

    def _unregister_transfer_download_task(self, with_upload: Optional[dict], download_task: asyncio.Task) -> None:
        return _require_web_task_manager(self)._unregister_transfer_download_task(
            with_upload, download_task
        )

    def cancel_task_downloads(self, task_id: int) -> int:
        return _require_web_task_manager(self).cancel_task_downloads(task_id)

    def submit_web_task(self, task_id: int) -> None:
        return _require_web_task_manager(self).submit_web_task(task_id)

    def discard_web_task_submission(
            self,
            task_id: int,
            cancel_running: bool = True,
            wait: bool = False,
    ) -> None:
        return _require_web_task_manager(self).discard_web_task_submission(
            task_id, cancel_running, wait=wait
        )

    def drop_web_task_from_queue(self, task_id: int) -> None:
        return _require_web_task_manager(self).drop_web_task_from_queue(task_id)

    def delete_web_task(self, task_id: int) -> bool:
        return _require_web_task_manager(self).delete_web_task(task_id)

    def pause_web_task(self, task_id: int) -> bool:
        return _require_web_task_manager(self).pause_web_task(task_id)

    def resume_web_task(self, task_id: int) -> bool:
        return _require_web_task_manager(self).resume_web_task(task_id)

    def retry_failed_web_task(self, task_id: int) -> int:
        return _require_web_task_manager(self).retry_failed_web_task(task_id)

    def _ensure_watch_ops(self):
        """监听编排实例（懒建并缓存；实现见 module.webops.watch_operations）。"""
        ops = self.__dict__.get('_watch_ops_impl')
        if ops is None:
            from module.webops.watch_operations import WatchOperations
            ops = WatchOperations(
                watch_manager_getter=lambda: getattr(self, 'watch_manager', None),
                # 必须经调度器工厂取**同一个已启动实例**：调度器的实例状态由
                # DeferredDiscussionOperations 持有（`_scheduler`），宿主上没有
                # `comment_delay_scheduler` 这个属性。此前写成读
                # `self.__dict__.get('comment_delay_scheduler')` → 恒为 None，
                # 导致删监听时"取消延迟抓取"静默失效、另三个入口 AttributeError。
                comment_delay_scheduler_getter=lambda: (
                    self._ensure_deferred_discussion_ops().scheduler_if_started()
                ),
                transfer_store_getter=self._ensure_transfer_store,
                loop_getter=lambda: getattr(self, 'loop', None),
            )
            self._watch_ops_impl = ops
        return ops

    def list_watches(self, tz_offset_minutes: int | None = None) -> list:
        return self._ensure_watch_ops().list_watches(tz_offset_minutes=tz_offset_minutes)

    def mark_pending_watch(self, payload: dict, status: str, error_message: str = None) -> None:
        return self._ensure_watch_ops().mark_pending_watch(payload, status, error_message)

    def set_live_watch_status(self, watch_id: str, status: str, error_message: str = None) -> None:
        return self._ensure_watch_ops().set_live_watch_status(watch_id, status, error_message)

    def persisted_watches(self) -> list:
        return self._ensure_watch_ops().persisted_watches()

    def watch_payload_from_record(self, watch: dict) -> dict:
        return self._ensure_watch_ops().watch_payload_from_record(watch)

    def create_watch(self, payload: dict) -> dict:
        return self._ensure_watch_ops().create_watch(payload)

    def export_forward_watches(self) -> dict:
        return self._ensure_watch_ops().export_forward_watches()

    def delete_watch(self, watch_id: str) -> bool:
        return self._ensure_watch_ops().delete_watch(watch_id)

    def update_watch(self, watch_id: str, payload: dict) -> dict:
        return self._ensure_watch_ops().update_watch(watch_id, payload)

    def list_watch_events(
            self,
            watch_id: str,
            limit: int = 50,
            offset: int = 0,
            today_only: bool = False,
            tz_offset_minutes: int | None = None,
            status: str | None = None
    ):
        return self._ensure_watch_ops().list_watch_events(
            watch_id,
            limit=limit,
            offset=offset,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes,
            status=status,
        )

    def recover_pikpak_failed_item_before_retry(self, task: dict, item: dict) -> bool:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.recover_pikpak_failed_item_before_retry(task, item)
        if not self.is_pikpak_target(item.get('target_link') or task.get('target_link'), task.get('target_profile')):
            return False
        if not PikpakIntegrationManager.is_pikpak_archive_recoverable_item(item):
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
                or archive_source_folder(
                    fallback_link=item.get('source_link') or task.get('source_link'),
                    post_message_id=item.get('range_message_id') or item.get('source_message_id'),
                    archive_by_author=bool(task.get('archive_by_author')),
                    archive_title_source=normalize_archive_title_source(
                        task.get('archive_title_source')
                    ),
                )
            ),
            file_name=item.get('file_name'),
            file_size=item.get('file_size'),
            transferred_at=transfer_item_archive_timestamp(item),
            match_original_name=transfer_item_archive_match_original_name(item)
        )
        if not bool(getattr(result, 'ok', False)):
            return False
        error_message = str(item.get('error_message') or '')
        existing_phase = item.get('phase')
        if existing_phase in ('forwarded', 'sent'):
            phase = existing_phase
        elif existing_phase == 'failure':
            phase = (
                'forwarded'
                if item.get('media_type') == 'forward' or 'PikPak archive' in error_message
                else 'sent'
            )
        else:
            phase = 'forwarded' if item.get('media_type') == 'forward' else 'sent'
        self.transfer_store.update_item(
            item_id,
            phase=phase,
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
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.next_web_operation_id(operation_type)
        self.web_operation_counter += 1
        return f'{operation_type}-{self.web_operation_counter}'

    def submit_web_operation(self, operation_type: str, payload: dict) -> dict:
        wm = getattr(self, 'web_task_manager', None)
        if wm is not None:
            return wm.submit_web_operation(operation_type, payload)
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
        return self.transfer_engine.detect_transfer_range(source_link)

    def _ensure_transfer_range_detector(self):
        """区间探测器（懒建并缓存；实现见 module.webops.transfer_range）。"""
        detector = self.__dict__.get('_transfer_range_detector_impl')
        if detector is None:
            from module.webops.transfer_range import TransferRangeDetector

            detector = TransferRangeDetector(
                app_getter=lambda: getattr(self, 'app', None),
                # 以下都经实例解析：宿主/测试替身会覆盖同名方法，
                # 类内直接调自身方法会绕过覆盖（实测导致 5 个用例失败）。
                wait_for_telegram_flood=lambda *a, **kw: self.wait_for_telegram_flood(
                    *a, **kw
                ),
                first_history_message=lambda *a, **kw: self.get_first_transfer_range_history_message(
                    *a, **kw
                ),
                iter_history=lambda *a, **kw: self.iter_transfer_range_history(*a, **kw),
                fast_detect=lambda *a, **kw: self.detect_transfer_range_fast(*a, **kw),
                history_scan=lambda *a, **kw: self.detect_transfer_range_by_history_scan(
                    *a, **kw
                ),
                # 经宿主模块解析：测试会 patch "module.webops.operations.parse_link"。
                parse_link=lambda *a, **kw: parse_link(*a, **kw),
            )
            self._transfer_range_detector_impl = detector
        return detector

    async def detect_transfer_range_async(self, source_link: str) -> Optional[dict]:
        return await self._ensure_transfer_range_detector().detect_transfer_range_async(
            source_link
        )

    async def detect_transfer_range_by_history_scan(self, chat_id) -> Optional[dict]:
        return await self._ensure_transfer_range_detector().detect_transfer_range_by_history_scan(
            chat_id
        )

    async def detect_transfer_range_fast(self, chat_id) -> Optional[dict]:
        return await self._ensure_transfer_range_detector().detect_transfer_range_fast(
            chat_id
        )

    async def get_first_transfer_range_history_message(self, chat_id, limit: int = 1, **kwargs):
        return await self._ensure_transfer_range_detector().get_first_transfer_range_history_message(
            chat_id, limit=limit, **kwargs
        )

    async def iter_transfer_range_history(self, chat_id, limit: int = 100):
        async for message in self._ensure_transfer_range_detector().iter_transfer_range_history(
            chat_id, limit=limit
        ):
            yield message

    def statistics(self, tz_offset_minutes: int | None = None) -> dict:
        return self._ensure_stats_ops().statistics(tz_offset_minutes)

    def _ensure_stats_ops(self):
        """统计编排实例（懒建并缓存；实现见 module.webops.stats）。"""
        ops = getattr(self, '_stats_ops', None)
        if ops is None:
            from module.webops.stats import StatsOperations
            ops = StatsOperations(
                transfer_store_getter=lambda: getattr(self, 'transfer_store', None),
                web_operations_getter=lambda: getattr(self, 'web_operations', None) or {},
                app_getter=lambda: getattr(self, 'app', None),
            )
            self._stats_ops = ops
        return ops

    def export_table(self, table_type: str) -> dict:
        return self._ensure_stats_ops().export_table(table_type)

    def _export_channel_statistics_table(self) -> dict:
        return self._ensure_stats_ops()._export_channel_statistics_table()

    def create_upload(self, payload: dict) -> dict:
        operation = self.submit_web_operation('upload', payload)
        return {'accepted': True, 'operation_id': operation['id']}

    def create_channel_download(self, payload: dict) -> dict:
        operation = self.submit_web_operation('channel_download', payload)
        return {'accepted': True, 'operation_id': operation['id']}

    def list_operations(self, limit: int = 50) -> list:
        """列出 WebUI 下载/上传操作记录（最近 N 条）。"""
        ops = [op for op in self.web_operations.values()
               if op.get('type') in ('channel_download', 'upload')]
        ops.sort(key=lambda o: o.get('created_at', ''), reverse=True)
        return ops[:limit]

    # --- 媒体管理 (Media Manager) ---

    def _ensure_media_manager(self) -> MediaManager:
        app = self.__dict__.get('app')
        store = self.__dict__.get('transfer_store')
        fallback_directory = getattr(store, 'directory', '') if store else ''
        save_directory = getattr(app, 'save_directory', None) or fallback_directory
        temp_directory = getattr(app, 'temp_directory', None) or fallback_directory
        media_manager = self.__dict__.get('media_manager')
        if media_manager is not None:
            current_roots = {
                media_manager._save_directory,
                media_manager._temp_directory,
                media_manager._store_directory,
            }
            next_roots = {
                os.path.abspath(save_directory) if save_directory else '',
                os.path.abspath(temp_directory) if temp_directory else '',
                os.path.abspath(getattr(store, 'directory', '') or '') if store else '',
            }
            if current_roots == next_roots:
                return media_manager
        self.media_manager = MediaManager(
            transfer_store=store,
            save_directory=save_directory,
            temp_directory=temp_directory,
            diagnostic=getattr(self, 'diagnostic', None)
        )
        return self.media_manager

    def _ensure_media_cleanup_ops(self):
        """媒体清理编排实例（懒建并缓存；实现见 module.webops.media_cleanup）。"""
        ops = self.__dict__.get('_media_cleanup_ops_impl')
        if ops is None:
            from module.webops.media_cleanup import MediaCleanupOperations
            ops = MediaCleanupOperations(
                media_manager_getter=self._ensure_media_manager,
                transfer_store_getter=lambda: getattr(self, 'transfer_store', None),
                diagnostic_getter=lambda: getattr(self, 'diagnostic', None),
            )
            self._media_cleanup_ops_impl = ops
        return ops

    def scan_media_for_cleanup(
            self,
            task_id: int = None,
            items_limit: int = None,
            items_offset: int = 0,
            orphans_limit: int = None,
            orphans_offset: int = 0,
    ) -> dict:
        """扫描可清理的媒体文件。"""
        return self._ensure_media_cleanup_ops().scan_media_for_cleanup(
            task_id=task_id,
            items_limit=items_limit,
            items_offset=items_offset,
            orphans_limit=orphans_limit,
            orphans_offset=orphans_offset,
        )

    def cleanup_media_files(self, payload: dict) -> dict:
        """执行媒体文件清理。payload: {'item_ids': [...], 'file_paths': [...]}"""
        return self._ensure_media_cleanup_ops().cleanup_media_files(payload)

    def maybe_run_scheduled_media_cleanup(self) -> None:
        return self._ensure_media_cleanup_ops().maybe_run_scheduled_media_cleanup()

    def list_cleanup_logs(self) -> list:
        return self._ensure_media_cleanup_ops().list_cleanup_logs()

    def _run_telegram_coro(self, coro, timeout: float | None = 300):
        """Run a coroutine on the Telegram loop from a worker thread.

        ``timeout=None`` waits indefinitely — required for long FloodWait-heavy
        archive author scans.
        """
        loop = getattr(self, 'loop', None)
        if loop is None:
            raise RuntimeError('Telegram event loop is unavailable.')
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=timeout)

    def _archive_author_ops(self):
        ops = self.__dict__.get('_archive_author_ops_impl')
        if ops is None:
            from module.webops.archive_author_ops import ArchiveAuthorOps
            ops = ArchiveAuthorOps(self)
            self._archive_author_ops_impl = ops
        return ops

    def list_archive_author_channels(self) -> dict:
        return self._archive_author_ops().list_archive_author_channels()

    def resume_interrupted_archive_author_jobs(self) -> int:
        return self._archive_author_ops().resume_interrupted_archive_author_jobs()

    def stop_archive_author_job(self, job_id: str) -> dict:
        return self._archive_author_ops().stop_archive_author_job(job_id)

    def scan_archive_author_reorganize(self, payload: dict) -> dict:
        return self._archive_author_ops().scan_archive_author_reorganize(payload)

    def resolve_archive_author_reorganize(self, payload: dict) -> dict:
        return self._archive_author_ops().resolve_archive_author_reorganize(payload)

    def execute_archive_author_reorganize(self, payload: dict) -> dict:
        return self._archive_author_ops().execute_archive_author_reorganize(payload)

    def list_archive_author_plan_moves(self, payload: dict | None = None) -> dict:
        return self._archive_author_ops().list_archive_author_plan_moves(payload)

    def get_archive_author_job(self, job_id: str) -> dict:
        return self._archive_author_ops().get_archive_author_job(job_id)

    def get_active_archive_author_job(self, channel_folder: str | None = None) -> dict:
        return self._archive_author_ops().get_active_archive_author_job(channel_folder)

    def _ensure_diagnostics_ops(self):
        """诊断导出编排实例（懒建并缓存；实现见 module.webops.diagnostics）。"""
        ops = self.__dict__.get('_diagnostics_ops_impl')
        if ops is None:
            from module.webops.diagnostics import DiagnosticsOperations
            ops = DiagnosticsOperations(
                transfer_store_getter=lambda: getattr(self, 'transfer_store', None),
                app_getter=lambda: getattr(self, 'app', None),
                loop_getter=lambda: getattr(self, 'loop', None),
                last_client_getter=lambda: getattr(self, 'last_client', None),
            )
            self._diagnostics_ops_impl = ops
        return ops

    def list_system_logs(
            self,
            limit: int = 50,
            offset: int = 0,
            category: str | None = None,
            level: str | None = None,
            trace_id: str | None = None,
            watch_id: str | None = None,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ) -> dict:
        return self._ensure_diagnostics_ops().list_system_logs(
            limit=limit,
            offset=offset,
            category=category,
            level=level,
            trace_id=trace_id,
            watch_id=watch_id,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes,
        )

    def retry_archive_from_system_log(self, log_id: int) -> dict:
        """Manually re-run PikPak archive for an archive_not_found system log."""
        ops = self.__dict__.get('_system_log_archive_retry_ops_impl')
        if ops is None:
            from module.webops.system_log_archive_retry_ops import SystemLogArchiveRetryOps
            ops = SystemLogArchiveRetryOps(self)
            self._system_log_archive_retry_ops_impl = ops
        return ops.retry_archive_from_system_log(log_id)

    def export_diagnostic_bundle(self, payload: dict | None = None) -> dict:
        return self._ensure_diagnostics_ops().export_diagnostic_bundle(payload)

    def export_system_logs(
            self,
            category: str | None = None,
            level: str | None = None,
            trace_id: str | None = None,
            watch_id: str | None = None,
            today_only: bool = False,
            tz_offset_minutes: int | None = None
    ) -> str:
        return self._ensure_diagnostics_ops().export_system_logs(
            category=category,
            level=level,
            trace_id=trace_id,
            watch_id=watch_id,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes,
        )

    def _ensure_settings_ops(self):
        """设置/PikPak 账号编排实例（懒建并缓存；实现见 module.webops.settings_operations）。"""
        ops = self.__dict__.get('_settings_ops_impl')
        if ops is None:
            from module.webops.settings_operations import SettingsOperations
            ops = SettingsOperations(
                app_getter=lambda: getattr(self, 'app', None),
                gc_getter=lambda: getattr(self, 'gc', None),
                download_upload_window_getter=lambda: getattr(
                    self, 'download_upload_window', None
                ),
                local_storage_guard_getter=lambda: getattr(
                    self, 'local_storage_guard', None
                ),
                pikpak_manager_getter=lambda: getattr(self, 'pikpak_manager', None),
                # 必须惰性：测试会预置 host.setup_coordinator（假协调器），
                # 绑定时求值会把假协调器当成缺失而重建真的。
                setup_coordinator_getter=lambda: self._setup_coordinator(),
            )
            self._settings_ops_impl = ops
        return ops

    def _setup_coordinator(self):
        """取（必要时创建）首启向导协调器。"""
        coordinator = getattr(self, 'setup_coordinator', None)
        if coordinator is None:
            from module.adapters.webui.setup import SetupCoordinator
            coordinator = SetupCoordinator()
            self.setup_coordinator = coordinator
        return coordinator

    def get_web_settings(self) -> dict:
        return self._ensure_settings_ops().get_web_settings()

    def update_web_settings(self, payload: dict) -> dict:
        return self._ensure_settings_ops().update_web_settings(payload)

    def start_web_ui(self, with_auth_provider: bool = False, defer_runtime_recovery: bool = False) -> None:
        if PARSE_ARGS.web is None:
            return
        os.makedirs(self.app.temp_directory or self.app.TEMP_DIRECTORY, exist_ok=True)
        self.transfer_store = TransferStore(directory=self.app.temp_directory)
        system_log = getattr(self, 'system_log', None)
        if system_log is not None:
            system_log.bind(store=self.transfer_store)
        self._bind_transfer_store_runtime(self.transfer_store)
        ctx = self.__dict__.get('ctx')
        if ctx is not None:
            ctx.transfer_store = self.transfer_store
        self.web_ui = WebUiServer(
            store=self.transfer_store,
            task_submitter=self.submit_web_task,
            settings_provider=self.get_web_settings,
            settings_updater=self.update_web_settings,
            operations=self._web_ui_operations(),
            host=get_web_host_from_env(),
            port=get_web_port_from_env(),
            username=get_web_username_from_env(),
            password=get_web_password_from_env(),
            diagnostic=getattr(self, 'diagnostic', None),
            deep_link_whitelist_getter=lambda: self.gc.get_deep_link_bot_whitelist(),
            setup_status_provider=self.get_setup_status,
            setup_api_saver=self.save_setup_api_credentials,
            setup_rclone_configurer=self.configure_setup_rclone,
            setup_rclone_skipper=self.skip_setup_rclone,
            setup_rclone_tester=self.test_setup_rclone,
            setup_bot_saver=self.save_setup_bot_token,
            setup_bot_skipper=self.skip_setup_bot_token,
            setup_ready_checker=self.is_setup_ready,
            pikpak_accounts_provider=self.list_pikpak_accounts,
            pikpak_account_adder=self.add_pikpak_account,
            pikpak_account_switcher=self.switch_pikpak_account,
            pikpak_account_remover=self.remove_pikpak_account,
        )
        if with_auth_provider:
            from module.adapters.webui.server import AuthProvider
            self.web_ui_auth = AuthProvider()
            self.web_ui.set_auth_provider(self.web_ui_auth)
        self.web_ui.start(open_browser=True)
        if not defer_runtime_recovery:
            self.recover_web_runtime()
        console.log(f'WebUI已启动: {self.web_ui.url}', style='#B1DB74')

    def _ensure_runtime_recovery_ops(self):
        """运行时恢复编排实例（懒建并缓存；实现见 module.webops.runtime_recovery）。"""
        ops = self.__dict__.get('_runtime_recovery_ops_impl')
        if ops is None:
            from module.webops.runtime_recovery import RuntimeRecoveryOperations

            ops = RuntimeRecoveryOperations(
                transfer_store_getter=lambda: getattr(self, 'transfer_store', None),
                diagnostic_getter=lambda: getattr(self, 'diagnostic', None),
                submit_web_task=self.submit_web_task,
                progress_tracker_getter=lambda: getattr(self, 'progress_tracker', None),
                ensure_comment_delay_scheduler=self._ensure_comment_delay_scheduler,
                resume_interrupted_archive_author_jobs=self.resume_interrupted_archive_author_jobs,
            )
            self._runtime_recovery_ops_impl = ops
        return ops

    def recover_web_runtime(self) -> None:
        """Resume pending web tasks / archives after Setup Ready."""
        return self._ensure_runtime_recovery_ops().recover()

    def _archive_settings(self) -> dict:
        return self._ensure_settings_ops()._archive_settings()

    def _set_archive_settings(self, *, enable: Optional[bool] = None, remote: Optional[str] = None) -> None:
        return self._ensure_settings_ops()._set_archive_settings(enable=enable, remote=remote)

    @staticmethod
    def _normalize_account_remote(value: str) -> str:
        from module.webops.settings_operations import SettingsOperations
        return SettingsOperations._normalize_account_remote(value)

    def _pikpak_accounts(self) -> list:
        return self._ensure_settings_ops()._pikpak_accounts()

    def _set_pikpak_accounts(self, accounts: list) -> None:
        return self._ensure_settings_ops()._set_pikpak_accounts(accounts)

    @staticmethod
    def _next_pikpak_remote_name(existing: set) -> str:
        from module.webops.settings_operations import SettingsOperations
        return SettingsOperations._next_pikpak_remote_name(existing)

    def _invalidate_pikpak_archive_client(self) -> None:
        return self._ensure_settings_ops()._invalidate_pikpak_archive_client()

    def _read_rclone_remotes(self) -> tuple:
        return self._ensure_settings_ops()._read_rclone_remotes()

    def list_pikpak_accounts(self) -> dict:
        return self._ensure_settings_ops().list_pikpak_accounts()

    def add_pikpak_account(self, payload: dict) -> dict:
        return self._ensure_settings_ops().add_pikpak_account(payload)

    def switch_pikpak_account(self, payload: dict) -> dict:
        return self._ensure_settings_ops().switch_pikpak_account(payload)

    def remove_pikpak_account(self, payload: dict) -> dict:
        return self._ensure_settings_ops().remove_pikpak_account(payload)

    def _ensure_setup_wizard_ops(self):
        """安装向导编排实例（懒建并缓存；实现见 module.webops.setup_wizard）。"""
        ops = self.__dict__.get('_setup_wizard_ops_impl')
        if ops is None:
            from module.webops.setup_wizard import SetupWizardOperations

            ops = SetupWizardOperations(
                app_getter=lambda: getattr(self, 'app', None),
                loop_getter=lambda: getattr(self, 'loop', None),
                setup_coordinator_getter=lambda: self._setup_coordinator(),
                auth_provider_getter=lambda: self.__dict__.get('web_ui_auth'),
                api_credentials_event_getter=lambda: self.__dict__.get(
                    '_api_credentials_event'
                ),
                archive_settings_getter=lambda: self._archive_settings(),
                set_archive_settings=lambda **kw: self._set_archive_settings(**kw),
                pikpak_accounts_getter=lambda: self._pikpak_accounts(),
                set_pikpak_accounts=lambda accounts: self._set_pikpak_accounts(accounts),
                invalidate_pikpak_archive_client=self._invalidate_pikpak_archive_client,
                # 必须经实例属性解析：宿主（含测试替身）可能覆盖 get_setup_status，
                # 直接调用类方法会绕过覆盖，把"宿主可替换"这一契约弄丢。
                setup_status_getter=lambda: self.get_setup_status(),
            )
            self._setup_wizard_ops_impl = ops
        return ops

    def is_setup_ready(self) -> bool:
        return self._ensure_setup_wizard_ops().is_setup_ready()

    def get_setup_status(self) -> dict:
        return self._ensure_setup_wizard_ops().get_setup_status()

    def save_setup_api_credentials(self, payload: dict) -> dict:
        return self._ensure_setup_wizard_ops().save_setup_api_credentials(payload)

    def configure_setup_rclone(self, payload: dict) -> dict:
        return self._ensure_setup_wizard_ops().configure_setup_rclone(payload)

    def skip_setup_rclone(self, payload: Optional[dict] = None) -> dict:
        return self._ensure_setup_wizard_ops().skip_setup_rclone(payload)

    def test_setup_rclone(self, payload: Optional[dict] = None) -> dict:
        return self._ensure_setup_wizard_ops().test_setup_rclone(payload)

    def save_setup_bot_token(self, payload: dict) -> dict:
        return self._ensure_setup_wizard_ops().save_setup_bot_token(payload)

    def skip_setup_bot_token(self, payload: Optional[dict] = None) -> dict:
        return self._ensure_setup_wizard_ops().skip_setup_bot_token(payload)

    def _ensure_watch_applicator(self) -> LiveWatchApplicator:
        """监听应用器（懒建并缓存）—— 它需要宿主作为上下文，故留在宿主侧。"""
        applicator = self.__dict__.get('_watch_applicator')
        if applicator is None:
            applicator = LiveWatchApplicator(host=self)
            self._watch_applicator = applicator
        return applicator

    def _ensure_operation_applicator(self):
        """操作应用编排实例（懒建并缓存；实现见 module.webops.operation_applicator）。"""
        ops = self.__dict__.get('_operation_applicator_impl')
        if ops is None:
            from module.webops.operation_applicator import WebOperationApplicator

            ops = WebOperationApplicator(
                web_operations_getter=lambda: getattr(self, 'web_operations', {}),
                app_getter=lambda: getattr(self, 'app', None),
                gc_getter=lambda: getattr(self, 'gc', None),
                uploader_getter=lambda: getattr(self, 'uploader', None),
                set_uploader=lambda value: setattr(self, 'uploader', value),
                runtime_message_filter_getter=lambda: (
                    self.runtime_message_filter()
                    if hasattr(self, 'runtime_message_filter')
                    else None
                ),
                watch_applicator_getter=self._ensure_watch_applicator,
                persisted_watch_records_getter=self._persisted_watch_records,
                listen_download_chat_getter=lambda: getattr(
                    self, 'listen_download_chat', {}
                ),
                listen_forward_chat_getter=lambda: getattr(
                    self, 'listen_forward_chat', {}
                ),
                web_pending_watches_getter=lambda: getattr(
                    self, 'web_pending_watches', {}
                ),
                set_live_watch_status=self._set_live_watch_status,
                mark_pending_watch=self.mark_pending_watch,
                watch_payload_from_record=self._watch_payload_from_record,
                create_download_task=self.create_download_task,
                uploader_context=self,
            )
            self._operation_applicator_impl = ops
        return ops

    async def process_web_operation(self, operation_id: str) -> None:
        return await self._ensure_operation_applicator().process_web_operation(operation_id)

    async def restore_live_transfer_watches(self) -> None:
        return await self._ensure_operation_applicator().restore_live_transfer_watches()

    async def apply_web_watch(self, payload: dict) -> None:
        return await self._ensure_operation_applicator().apply_web_watch(payload)

    def remove_web_watch(self, watch_id: str) -> bool:
        return self._ensure_operation_applicator().remove_web_watch(watch_id)

    async def apply_web_upload(self, payload: dict) -> None:
        return await self._ensure_operation_applicator().apply_web_upload(payload)

    async def apply_web_channel_download(self, payload: dict) -> None:
        return await self._ensure_operation_applicator().apply_web_channel_download(payload)

    def _ensure_task_queue_ops(self):
        """任务队列编排实例（懒建并缓存；实现见 module.webops.task_queue）。"""
        ops = self.__dict__.get('_task_queue_ops_impl')
        if ops is None:
            from module.webops.task_queue import TaskQueueOperations

            ops = TaskQueueOperations(
                web_task_manager_getter=lambda: getattr(self, 'web_task_manager', None),
                web_task_queue_getter=lambda: getattr(self, 'web_task_queue', None),
                web_operation_queue_getter=lambda: getattr(
                    self, 'web_operation_queue', None
                ),
                submitted_task_ids_getter=lambda: getattr(
                    self, 'web_submitted_task_ids', set()
                ),
                running_task_getter=lambda: getattr(self, 'web_running_task', None),
                running_task_setter=lambda value: setattr(
                    self, 'web_running_task', value
                ),
                running_task_id_getter=lambda: getattr(
                    self, 'web_running_task_id', None
                ),
                running_task_id_setter=lambda value: setattr(
                    self, 'web_running_task_id', value
                ),
                transfer_store_getter=lambda: getattr(self, 'transfer_store', None),
                loop_getter=lambda: getattr(self, 'loop', None),
                process_web_transfer_task=self.process_web_transfer_task,
                process_web_operation=self.process_web_operation,
            )
            self._task_queue_ops_impl = ops
        return ops

    async def process_web_task_queue(self) -> None:
        return await self._ensure_task_queue_ops().process_web_task_queue()

    def start_next_web_transfer_task(self) -> None:
        return self._ensure_task_queue_ops().start_next_web_transfer_task()

    def is_web_transfer_task_schedulable(self, task_id: int) -> bool:
        return self._ensure_task_queue_ops().is_web_transfer_task_schedulable(task_id)

    def finish_web_transfer_task(self, task_id: Optional[int], completed_task: asyncio.Task) -> None:
        return self._ensure_task_queue_ops().finish_web_transfer_task(task_id, completed_task)
    def list_deferred_discussion_captures(self, watch_id: str) -> dict:
        return self._ensure_watch_ops().list_deferred_discussion_captures(watch_id)

    def cancel_deferred_discussion_capture(self, watch_id: str, capture_id: int) -> bool:
        return self._ensure_watch_ops().cancel_deferred_discussion_capture(watch_id, capture_id)

    def run_deferred_discussion_capture_now(self, watch_id: str, capture_id: int) -> bool:
        return self._ensure_watch_ops().run_deferred_discussion_capture_now(watch_id, capture_id)

    def retry_deferred_discussion_capture(self, watch_id: str, capture_id: int) -> bool:
        return self._ensure_watch_ops().retry_deferred_discussion_capture(watch_id, capture_id)


_WEB_UI_DELEGATE_METHODS = (
    'should_continue_web_transfer_task', 'cancel_task_uploads', 'pause_task_uploads', 'cancel_task_downloads', 'submit_web_task',
    'delete_web_task', 'pause_web_task', 'resume_web_task', 'retry_failed_web_task',
    'list_watches', 'create_watch', 'export_forward_watches', 'update_watch', 'delete_watch', 'list_watch_events',
    'list_deferred_discussion_captures', 'cancel_deferred_discussion_capture', 'run_deferred_discussion_capture_now',
    'retry_deferred_discussion_capture',
    'detect_transfer_range', 'statistics', 'export_table', 'create_upload',
    'create_channel_download', 'list_operations', 'scan_media_for_cleanup',
    'cleanup_media_files', 'list_cleanup_logs',     'list_system_logs', 'export_system_logs', 'retry_archive_from_system_log',
    'export_diagnostic_bundle',
    'list_archive_author_channels', 'scan_archive_author_reorganize',
    'resolve_archive_author_reorganize', 'execute_archive_author_reorganize',
    'list_archive_author_plan_moves',
    'get_archive_author_job',
    'get_active_archive_author_job',
    'stop_archive_author_job',
)


class WebOperationsFacade:
    """Standalone IWebUiOperations adapter; delegates to host mixin methods."""

    def __init__(self, host):
        self._host = host


def _bind_web_delegate(name: str):
    def delegate(self, *args, **kwargs):
        return getattr(self._host, name)(*args, **kwargs)
    delegate.__name__ = name
    return delegate


for _method_name in _WEB_UI_DELEGATE_METHODS:
    setattr(WebOperationsFacade, _method_name, _bind_web_delegate(_method_name))
