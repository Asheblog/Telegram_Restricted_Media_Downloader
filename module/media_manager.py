# coding=UTF-8
"""媒体管理模块 — 扫描磁盘残留文件、安全清理、清理历史记录。

清理策略：
  A) 基于 TransferStore transfer_items 状态 — status ∈ {success,failure,skipped} 且 local_path 存在
  B) 基于文件时间 — save_directory 下超过保留天数的文件，不在任何活跃 transfer_item 中
"""

import os
import time
from typing import Optional, List, Dict, Any

from module import log
from module.path_tool import safe_delete


class MediaManager:
    """扫描 save_directory 中的可清理媒体文件并提供安全删除。"""

    DEFAULT_RETENTION_DAYS = 7  # 遗留文件默认保留天数

    def __init__(
            self,
            transfer_store,  # TransferStore
            save_directory: str,
            temp_directory: Optional[str] = None,
            retention_days: int = DEFAULT_RETENTION_DAYS,
            diagnostic=None,
    ):
        self._store = transfer_store
        self._save_directory = os.path.abspath(save_directory) if save_directory else ''
        self._temp_directory = os.path.abspath(temp_directory) if temp_directory else ''
        self._retention_days = max(1, retention_days)
        self._diagnostic = diagnostic

    @property
    def retention_days(self) -> int:
        return self._retention_days

    def _is_within_allowed_path(self, file_path: str) -> bool:
        """安全检查：文件路径必须在 save_directory 或 temp_directory 下。"""
        if not file_path:
            return False
        abs_path = os.path.abspath(file_path)
        allowed = []
        if self._save_directory:
            allowed.append(self._save_directory)
        if self._temp_directory:
            allowed.append(self._temp_directory)
        for base in allowed:
            if abs_path == base or abs_path.startswith(base + os.sep):
                return True
        return False

    # --- 内部工具 ---

    @staticmethod
    def _get_file_info(file_path: str) -> tuple:
        """返回 (file_exists: bool, file_size: int)。"""
        if not file_path or not os.path.isfile(file_path):
            return False, 0
        try:
            return True, os.path.getsize(file_path)
        except OSError:
            return False, 0

    # --- 扫描 A: 基于 transfer_items 状态 ---

    def scan_transfer_items(self, task_id: int = None) -> Dict[str, Any]:
        """扫描 TransferStore 中已终结但本地文件仍未删除的 item。

        Returns:
            {
                'items': [{'item_id', 'task_id', 'file_name', 'file_size',
                           'local_path', 'status', 'source_link', 'target_link',
                           'file_exists': bool}, ...],
                'total_count': int,
                'total_size': int,
            }
        """
        items = []
        total_size = 0
        cleanable = self._store.list_cleanable_items(task_id=task_id)

        for item in cleanable:
            local_path = item.get('local_path', '') or ''
            if not self._is_within_allowed_path(local_path):
                continue
            file_exists, file_size = self._get_file_info(local_path)

            items.append({
                'item_id': item.get('id'),
                'task_id': item.get('task_id'),
                'file_name': item.get('file_name'),
                'file_size': item.get('file_size') or file_size,
                'local_path': local_path,
                'status': item.get('status'),
                'source_link': item.get('task_source_link') or item.get('source_link'),
                'target_link': item.get('task_target_link') or item.get('target_link'),
                'file_exists': file_exists,
            })
            if file_exists:
                total_size += file_size

        return {
            'items': items,
            'total_count': len(items),
            'total_size': total_size,
        }

    # --- 扫描 B: 基于文件时间的遗留文件 ---

    def scan_orphan_files(self) -> Dict[str, Any]:
        """扫描 save_directory 下可能被遗留的孤立文件。

        孤立文件判定：
          - 文件最后修改时间超过 retention_days
          - 文件路径不在任何活跃（pending/running）transfer_item 的 local_path 中

        Returns:
            {
                'files': [{'path': str, 'size': int, 'mtime': float}, ...],
                'total_count': int,
                'total_size': int,
            }
        """
        if not self._save_directory or not os.path.isdir(self._save_directory):
            return {'files': [], 'total_count': 0, 'total_size': 0}

        # 收集所有活跃 item 的 local_path
        active_paths = self._get_active_local_paths()

        cutoff = time.time() - self._retention_days * 86400
        orphan_files = []
        total_size = 0

        for root, _dirs, files in os.walk(self._save_directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    stat = os.stat(file_path)
                except OSError:
                    continue
                if stat.st_mtime > cutoff:
                    continue
                if file_path in active_paths:
                    continue
                file_size = stat.st_size
                orphan_files.append({
                    'path': file_path,
                    'size': file_size,
                    'mtime': stat.st_mtime,
                })
                total_size += file_size

        return {
            'files': orphan_files,
            'total_count': len(orphan_files),
            'total_size': total_size,
        }

    def _get_active_local_paths(self) -> set:
        """收集所有活跃（pending/running）transfer_item 的 local_path。"""
        active = set()
        if self._store is None:
            return active
        try:
            tasks = self._store.list_tasks()
            active_task_ids = {
                int(t.get('id'))
                for t in tasks
                if t.get('status') in ('pending', 'running')
            }
            for task_id in active_task_ids:
                for item in self._store.list_items(task_id):
                    local_path = (item.get('local_path') or '').strip()
                    if local_path:
                        active.add(os.path.abspath(local_path))
        except Exception:
            pass
        return active

    # --- 综合扫描 ---

    def scan_all(self, task_id: int = None) -> Dict[str, Any]:
        """综合扫描：transfer_items + 孤儿文件。

        Returns:
            {
                'transfer_items': {...},
                'orphan_files': {...},
                'total_count': int,
                'total_size': int,
                'retention_days': int,
            }
        """
        ti_result = self.scan_transfer_items(task_id=task_id)
        orphan_result = self.scan_orphan_files()
        return {
            'transfer_items': ti_result,
            'orphan_files': orphan_result,
            'total_count': ti_result['total_count'] + orphan_result['total_count'],
            'total_size': ti_result['total_size'] + orphan_result['total_size'],
            'retention_days': self._retention_days,
        }

    # --- 预防性清理 (Transfer 完成钩子) ---

    def try_cleanup_item_file(self, item_id: int) -> bool:
        """Transfer 完成钩子 — 清理 item 对应的本地文件。

        由 TransferProgressTracker 在 item 到达终结状态时调用。
        安全幂等：如果文件不存在或已删除，仅标记 local_file_deleted。
        """
        if not self._store:
            return False
        item = self._store.get_item(item_id)
        if not item:
            return False
        local_path = (item.get('local_path') or '').strip()
        if not local_path:
            return False
        if not self._is_within_allowed_path(local_path):
            return False

        file_exists, file_size = self._get_file_info(local_path)
        if file_exists:
            if not safe_delete(local_path):
                return False

        self._store.mark_item_local_file_deleted(item_id)
        self._store.insert_cleanup_log(
            file_path=local_path,
            file_size=file_size if file_exists else (item.get('file_size') or 0),
            source_task_id=item.get('task_id'),
            source_item_id=item_id,
            reason='auto_cleanup_on_transfer_complete'
        )
        return True

    # --- 清理操作 ---

    def cleanup_by_item_ids(self, item_ids: List[int]) -> Dict[str, Any]:
        """按 transfer_item ID 清理对应本地文件。

        Returns:
            {'deleted': [{item_id, file_path, file_size}],
             'failed': [{item_id, file_path, error}],
             'total_deleted_count': int, 'total_deleted_size': int}
        """
        deleted = []
        failed = []
        total_deleted_size = 0

        for item_id in item_ids:
            item = self._store.get_item(item_id) if hasattr(self._store, 'get_item') else None
            if item is None:
                failed.append({
                    'item_id': item_id, 'file_path': '', 'error': 'Item not found'
                })
                continue

            local_path = (item.get('local_path') or '').strip()
            if not local_path:
                failed.append({
                    'item_id': item_id, 'file_path': '', 'error': 'No local_path'
                })
                continue

            if not self._is_within_allowed_path(local_path):
                failed.append({
                    'item_id': item_id, 'file_path': local_path,
                    'error': 'Path outside allowed directories'
                })
                continue

            file_exists, file_size = self._get_file_info(local_path)

            if file_exists:
                if safe_delete(local_path):
                    total_deleted_size += file_size
                else:
                    failed.append({
                        'item_id': item_id, 'file_path': local_path,
                        'error': 'safe_delete returned False'
                    })
                    continue

            # 标记 item 的本地文件已删除
            self._store.mark_item_local_file_deleted(item_id)
            self._store.insert_cleanup_log(
                file_path=local_path,
                file_size=file_size,
                source_task_id=item.get('task_id'),
                source_item_id=item_id,
                reason='transfer_item_cleanup'
            )
            deleted.append({
                'item_id': item_id,
                'file_path': local_path,
                'file_size': file_size,
            })

        return {
            'deleted': deleted,
            'failed': failed,
            'total_deleted_count': len(deleted),
            'total_deleted_size': total_deleted_size,
        }

    def cleanup_orphan_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """删除指定的孤儿文件。

        Returns:
            {'deleted': [{path, size}], 'failed': [{path, error}],
             'total_deleted_count': int, 'total_deleted_size': int}
        """
        deleted = []
        failed = []
        total_deleted_size = 0

        for file_path in file_paths:
            abs_path = os.path.abspath(file_path)

            if not self._is_within_allowed_path(abs_path):
                failed.append({'path': file_path, 'error': 'Path outside allowed directories'})
                continue

            _, file_size = self._get_file_info(abs_path)

            if safe_delete(abs_path):
                total_deleted_size += file_size
                self._store.insert_cleanup_log(
                    file_path=abs_path,
                    file_size=file_size,
                    reason='orphan_file_cleanup'
                )
                deleted.append({'path': abs_path, 'size': file_size})
            else:
                failed.append({'path': file_path, 'error': 'safe_delete returned False'})

        return {
            'deleted': deleted,
            'failed': failed,
            'total_deleted_count': len(deleted),
            'total_deleted_size': total_deleted_size,
        }
