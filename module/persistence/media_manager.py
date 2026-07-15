# coding=UTF-8
"""媒体管理模块 — 扫描磁盘残留文件、安全清理、清理历史记录。

清理策略：
  A) 基于 TransferStore transfer_items 状态 — status ∈ {success,failure,skipped} 且 local_path 存在
  A2) 幽灵 item — 已标记 local_file_deleted 但磁盘仍有对应文件
  A3) 僵尸活跃 item — 任务已终结但 item 仍 pending/running/paused
  B) 基于文件时间 — save/temp/TransferStore 目录下超过保留天数的文件，不在任何活跃 transfer_item 中
"""

import os
import time
from typing import Optional, List, Dict, Any

from module.path_tool import safe_delete
from module.persistence.transfer_store import TransferStore, TransferStatus

try:
    from module.enums import SaveDirectoryPrefix
except ImportError:  # pragma: no cover
    class SaveDirectoryPrefix:  # type: ignore
        CHAT_ID = '%CHAT_ID%'
        CHAT_NAME = '%CHAT_NAME%'
        MIME_TYPE = '%MIME_TYPE%'

        def __iter__(self):
            yield from (self.CHAT_ID, self.CHAT_NAME, self.MIME_TYPE)


class MediaManager:
    """扫描 save_directory 中的可清理媒体文件并提供安全删除。"""

    DEFAULT_RETENTION_DAYS = 7  # 遗留文件默认保留天数
    INTERNAL_FILE_NAMES = {
        TransferStore.FILE_NAME,
        f'{TransferStore.FILE_NAME}-wal',
        f'{TransferStore.FILE_NAME}-shm',
    }

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
        store_directory = getattr(transfer_store, 'directory', None) if transfer_store else None
        self._store_directory = os.path.abspath(store_directory) if store_directory else ''
        self._retention_days = max(1, retention_days)
        self._diagnostic = diagnostic

    @property
    def retention_days(self) -> int:
        return self._retention_days

    @staticmethod
    def _placeholder_scan_root(directory: str) -> str:
        """将含 %CHAT_ID% 等占位符的配置路径收束为可扫描的真实父目录。"""
        if not directory:
            return ''
        root = directory
        for placeholder in SaveDirectoryPrefix():
            if placeholder in root:
                root = root.split(placeholder, 1)[0]
        root = root.rstrip('\\/') or directory
        return os.path.abspath(root)

    def _allowed_directories(self) -> List[str]:
        """扫描与安全删除允许的根目录（含 TransferStore 实际所在目录）。"""
        directories = []
        seen = set()
        for directory in (self._save_directory, self._temp_directory, self._store_directory):
            if not directory:
                continue
            for candidate in (directory, self._placeholder_scan_root(directory)):
                if not candidate or candidate in seen:
                    continue
                seen.add(candidate)
                directories.append(candidate)
        return directories

    def _is_within_allowed_path(self, file_path: str) -> bool:
        """安全检查：文件路径必须在允许的根目录下。"""
        if not file_path:
            return False
        abs_path = os.path.abspath(file_path)
        for base in self._allowed_directories():
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

    @staticmethod
    def _candidate_temp_paths(temp_path: str) -> list:
        if not temp_path:
            return []
        paths = [temp_path]
        paths.append(f'{temp_path}.temp')
        return paths

    def _item_cleanup_paths(self, item: dict) -> List[str]:
        seen = set()
        paths = []
        local_path = (item.get('local_path') or '').strip()
        temp_path = (item.get('temp_path') or '').strip()
        candidates = [
            local_path,
            *self._candidate_temp_paths(temp_path)
        ]
        if local_path:
            candidates.append(f'{local_path}.temp')
        for candidate in candidates:
            if not candidate:
                continue
            abs_path = os.path.abspath(candidate)
            if abs_path in seen:
                continue
            seen.add(abs_path)
            paths.append(abs_path)
        return paths

    def _cleanup_item_paths(self, item: dict, reason: str) -> Dict[str, Any]:
        item_id = int(item.get('id') or 0)
        cleanup_paths = self._item_cleanup_paths(item)
        if not cleanup_paths:
            return {
                'deleted': None,
                'failed': {'item_id': item_id, 'file_path': '', 'error': 'No local_path'},
            }
        if any(not self._is_within_allowed_path(path) for path in cleanup_paths):
            return {
                'deleted': None,
                'failed': {
                    'item_id': item_id,
                    'file_path': ';'.join(cleanup_paths),
                    'error': 'Path outside allowed directories',
                },
            }

        deleted_size = 0
        for local_path in cleanup_paths:
            file_exists, file_size = self._get_file_info(local_path)
            if not file_exists:
                continue
            if not safe_delete(local_path):
                return {
                    'deleted': None,
                    'failed': {
                        'item_id': item_id,
                        'file_path': local_path,
                        'error': 'safe_delete returned False',
                    },
                }
            deleted_size += file_size

        self._store.mark_item_local_file_deleted(item_id)
        self._store.insert_cleanup_log(
            file_path=';'.join(cleanup_paths),
            file_size=deleted_size,
            source_task_id=item.get('task_id'),
            source_item_id=item_id,
            reason=reason,
        )
        return {
            'deleted': {
                'item_id': item_id,
                'file_path': ';'.join(cleanup_paths),
                'file_size': deleted_size,
            },
            'failed': None,
        }

    # --- 扫描 A: 基于 transfer_items 状态 ---

    def _scan_transfer_item_rows(self, rows: List[dict], include_missing_files: bool) -> Dict[str, Any]:
        items = []
        total_size = 0
        for item in rows:
            cleanup_paths = self._item_cleanup_paths(item)
            allowed_paths = [path for path in cleanup_paths if self._is_within_allowed_path(path)]
            if not allowed_paths:
                continue
            existing_paths = []
            item_size = 0
            for path in allowed_paths:
                file_exists, file_size = self._get_file_info(path)
                if file_exists:
                    existing_paths.append(path)
                    item_size += file_size
            if not include_missing_files and not existing_paths:
                continue

            items.append({
                'item_id': item.get('id'),
                'task_id': item.get('task_id'),
                'file_name': item.get('file_name'),
                'file_size': item_size or item.get('file_size') or 0,
                'local_path': item.get('local_path') or '',
                'temp_path': item.get('temp_path') or '',
                'paths': allowed_paths,
                'status': item.get('status'),
                'source_link': item.get('task_source_link') or item.get('source_link'),
                'target_link': item.get('task_target_link') or item.get('target_link'),
                'file_exists': bool(existing_paths),
                'ghost': bool(item.get('local_file_deleted')),
            })
            total_size += item_size
        return {'items': items, 'total_size': total_size}

    def scan_transfer_items(self, task_id: int = None, limit: int = None, offset: int = 0) -> Dict[str, Any]:
        """扫描 TransferStore 中已终结但本地文件仍未删除的 item。

        Returns:
            {
                'items': [{'item_id', 'task_id', 'file_name', 'file_size',
                           'local_path', 'status', 'source_link', 'target_link',
                           'file_exists': bool, 'ghost': bool}, ...],
                'total_count': int,
                'total_size': int,
            }
        """
        if self._store is None:
            return {'items': [], 'total_count': 0, 'total_size': 0}

        seen_ids = set()
        rows = []
        for item in self._store.list_cleanable_items(task_id=task_id):
            item_id = item.get('id')
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            rows.append(item)
        for item in self._store.list_stale_active_items(task_id=task_id):
            item_id = item.get('id')
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            rows.append(item)
        for item in self._store.list_ghost_items(task_id=task_id):
            item_id = item.get('id')
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            rows.append(item)

        scanned = self._scan_transfer_item_rows(rows, include_missing_files=False)
        items = scanned['items']
        total_size = scanned['total_size']
        total_count = len(items)
        if limit is not None and limit > 0:
            items = items[offset:offset + limit]

        return {
            'items': items,
            'total_count': total_count,
            'total_size': total_size,
        }

    # --- 扫描 B: 基于文件时间的遗留文件 ---

    def scan_orphan_files(self, limit: int = None, offset: int = 0) -> Dict[str, Any]:
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
        # 收集所有活跃 item 的 local_path
        active_paths = self._get_active_local_paths()

        cutoff = time.time() - self._retention_days * 86400
        orphan_files = []
        total_size = 0

        for directory in self._scan_directories():
            for root, _dirs, files in os.walk(directory):
                for filename in files:
                    if self._is_internal_file(filename):
                        continue
                    file_path = os.path.abspath(os.path.join(root, filename))
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

        total_count = len(orphan_files)
        if limit is not None and limit > 0:
            orphan_files = orphan_files[offset:offset + limit]

        return {
            'files': orphan_files,
            'total_count': total_count,
            'total_size': total_size,
        }

    def _scan_directories(self) -> List[str]:
        directories = []
        for directory in self._allowed_directories():
            if os.path.isdir(directory):
                directories.append(directory)
        return directories

    @classmethod
    def _is_internal_file(cls, filename: str) -> bool:
        return filename in cls.INTERNAL_FILE_NAMES

    def _get_active_local_paths(self) -> set:
        """收集仍需保留的活跃 item 路径（pending/running/paused）。

        已终结 item 即使挂在仍在跑的任务下，也不应挡住孤儿扫描。
        """
        active = set()
        if self._store is None:
            return active
        try:
            tasks = self._store.list_tasks()
            active_task_ids = {
                int(t.get('id'))
                for t in tasks
                if t.get('status') in (
                    TransferStatus.PENDING,
                    TransferStatus.RUNNING,
                    TransferStatus.PAUSING,
                    TransferStatus.PAUSED,
                )
            }
            active_item_statuses = {
                TransferStatus.PENDING,
                TransferStatus.RUNNING,
                TransferStatus.PAUSED,
            }
            for task_id in active_task_ids:
                for item in self._store.list_items(task_id):
                    if item.get('status') not in active_item_statuses:
                        continue
                    for path in self._item_cleanup_paths(item):
                        active.add(os.path.abspath(path))
        except Exception:
            pass
        return active

    # --- 综合扫描 ---

    def scan_all(
            self,
            task_id: int = None,
            items_limit: int = None,
            items_offset: int = 0,
            orphans_limit: int = None,
            orphans_offset: int = 0,
    ) -> Dict[str, Any]:
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
        ti_result = self.scan_transfer_items(
            task_id=task_id, limit=items_limit, offset=items_offset
        )
        orphan_result = self.scan_orphan_files(
            limit=orphans_limit, offset=orphans_offset
        )
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
        result = self._cleanup_item_paths(item, reason='auto_cleanup_on_transfer_complete')
        return result['deleted'] is not None and result['failed'] is None

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

            result = self._cleanup_item_paths(item, reason='transfer_item_cleanup')
            if result['failed']:
                failed.append(result['failed'])
                continue
            deleted.append(result['deleted'])
            total_deleted_size += result['deleted']['file_size']

        return {
            'deleted': deleted,
            'failed': failed,
            'total_deleted_count': len(deleted),
            'total_deleted_size': total_deleted_size,
        }

    def cleanup_task_files(self, task_id: int) -> Dict[str, Any]:
        """删除任务下所有 item 的本地文件和下载缓存，供任务删除前调用。"""
        if not self._store:
            return {
                'deleted': [],
                'failed': [{'item_id': 0, 'file_path': '', 'error': 'No transfer store'}],
                'total_deleted_count': 0,
                'total_deleted_size': 0,
            }
        deleted = []
        failed = []
        total_deleted_size = 0
        for item in self._store.list_items(int(task_id)):
            if not self._item_cleanup_paths(item):
                continue
            result = self._cleanup_item_paths(item, reason='transfer_task_delete_cleanup')
            if result['failed']:
                failed.append(result['failed'])
                continue
            deleted.append(result['deleted'])
            total_deleted_size += result['deleted']['file_size']
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

    def auto_cleanup_orphan_files(self) -> Dict[str, Any]:
        """Scan and delete orphan files that exceeded the retention threshold."""
        scan_result = self.scan_orphan_files()
        file_paths = [entry['path'] for entry in scan_result.get('files', [])]
        if not file_paths:
            return {
                'deleted': [],
                'failed': [],
                'total_deleted_count': 0,
                'total_deleted_size': 0,
                'scanned_count': 0,
            }
        cleanup_result = self.cleanup_orphan_files(file_paths)
        cleanup_result['scanned_count'] = scan_result.get('total_count', 0)
        return cleanup_result
