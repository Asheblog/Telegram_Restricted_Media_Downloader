# coding=UTF-8
import json
import os
import posixpath
import re
import subprocess
import time
import unicodedata

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional


DEFAULT_ARCHIVE_CONFIG = {
    'enable': False,
    'remote': '',
    'source_directory': 'My Telegram',
    'root_directory': 'Telegram',
    'poll_seconds': 180,
    'poll_interval_seconds': 5,
    'match_window_seconds': 3600,
    'poll_cap_seconds': 1800,
    'archive_delay_seconds': 600,
    'archive_retry_interval_seconds': 300
}


@dataclass
class PikPakArchiveResult:
    ok: bool
    status: str
    message: str = ''
    archive_path: Optional[str] = None


class DisabledPikPakArchiveClient:
    def ensure_source_folder(self, *args, **kwargs) -> PikPakArchiveResult:
        return PikPakArchiveResult(False, 'disabled', 'PikPak archive is disabled.')

    def archive_file(self, *args, **kwargs) -> PikPakArchiveResult:
        return PikPakArchiveResult(False, 'disabled', 'PikPak archive is disabled.')

    def upload_to_ingest(self, *args, **kwargs) -> PikPakArchiveResult:
        return PikPakArchiveResult(False, 'disabled', 'PikPak rclone remote is not configured.')

    def list_directories(self, *args, **kwargs) -> list:
        return []

    def move_directory(self, *args, **kwargs) -> None:
        raise RuntimeError('PikPak archive is disabled or remote is missing.')

    def list_archive_channel_folders(self) -> list:
        return []


class RclonePikPakArchiveClient:
    def __init__(
            self,
            config: dict,
            runner: Optional[Callable] = None,
            now: Optional[Callable[[], float]] = None
    ):
        self.config = normalize_archive_config(config)
        self.runner = runner or subprocess.run
        self.now = now or time.time

    @property
    def enabled(self) -> bool:
        return bool(self.config.get('enable') and self.config.get('remote'))

    def resolve_poll_seconds(self, file_size: Optional[int] = None) -> float:
        base = max(float(self.config.get('poll_seconds') or 0), 0)
        cap = max(float(self.config.get('poll_cap_seconds') or 0), base)
        if not file_size or file_size <= 0:
            return min(base, cap) if cap else base
        megabytes = file_size / (1024 * 1024)
        scaled = megabytes * 2.0
        return min(max(base, scaled), cap)

    def archive_file(
            self,
            source_folder: str,
            file_name: Optional[str],
            file_size: Optional[int] = None,
            transferred_at: Optional[float] = None,
            match_original_name: bool = True
    ) -> PikPakArchiveResult:
        if not self.enabled:
            return PikPakArchiveResult(False, 'disabled', 'PikPak archive is disabled or remote is missing.')
        if not source_folder:
            return PikPakArchiveResult(False, 'missing_metadata', 'Source folder is missing.')
        if not file_name and (file_size is None or transferred_at is None):
            return PikPakArchiveResult(False, 'missing_metadata', 'File name is missing and size/time matching is unavailable.')

        try:
            source_folder = normalize_source_folder_path(source_folder)
            target_name = clean_remote_segment(file_name) if file_name else None
            match_name = target_name if match_original_name else None
            source_root = clean_remote_path(self.config.get('source_directory') or '')
            target_root = clean_remote_path(self.config.get('root_directory') or '')
            target_dir = join_remote_path(target_root, source_folder)
            self.ensure_directory(target_dir)
            poll_seconds = self.resolve_poll_seconds(file_size)
            candidates, poll_elapsed = self.find_candidates(
                root=source_root,
                file_name=match_name,
                file_size=file_size,
                transferred_at=transferred_at,
                poll_seconds=poll_seconds
            )
            if not candidates and target_name and not match_original_name:
                candidates = self._list_matching_candidates(
                    root=source_root,
                    file_name=target_name,
                    file_size=file_size,
                    transferred_at=transferred_at
                )
            if not candidates:
                archived_candidates = self._list_matching_candidates(
                    root=target_dir,
                    file_name=target_name,
                    file_size=file_size,
                    transferred_at=transferred_at
                )
                if len(archived_candidates) == 1:
                    archived_name = clean_remote_segment(target_name or archived_candidates[0].get('Name'))
                    if not archived_name:
                        return PikPakArchiveResult(False, 'not_found', 'No archived PikPak file name was available.')
                    archived_path = candidate_remote_path(
                        target_dir,
                        archived_candidates[0].get('Path') or archived_name
                    )
                    return PikPakArchiveResult(True, 'already_archived', archive_path=archived_path)
                if len(archived_candidates) > 1:
                    return PikPakArchiveResult(False, 'ambiguous', f'Multiple archived PikPak files matched {target_name}.')
                return PikPakArchiveResult(False, 'not_found', f'No PikPak file matched {target_name}.')
            if len(candidates) > 1:
                return PikPakArchiveResult(False, 'ambiguous', f'Multiple PikPak files matched {target_name}.')
            source_path = candidate_remote_path(source_root, candidates[0].get('Path') or candidates[0].get('Name'))
            target_name = target_name or clean_remote_segment(candidates[0].get('Name'))
            target_path = join_remote_path(target_dir, target_name)
            if not source_path:
                return PikPakArchiveResult(False, 'not_found', f'No PikPak file path matched {target_name}.')
            if not target_name:
                return PikPakArchiveResult(False, 'not_found', 'No PikPak file name was available for archive.')
            if source_path == target_path:
                return PikPakArchiveResult(True, 'already_archived', archive_path=target_path)
            self.moveto(source_path, target_path)
            return PikPakArchiveResult(True, 'success', archive_path=target_path)
        except Exception as e:
            return PikPakArchiveResult(False, 'error', str(e))

    def ensure_source_folder(self, source_folder: str) -> PikPakArchiveResult:
        if not self.enabled:
            return PikPakArchiveResult(False, 'disabled', 'PikPak archive is disabled or remote is missing.')
        if not source_folder:
            return PikPakArchiveResult(False, 'missing_metadata', 'Source folder is missing.')
        try:
            folder = normalize_source_folder_path(source_folder)
            target_root = clean_remote_path(self.config.get('root_directory') or '')
            target_dir = join_remote_path(target_root, folder)
            self.ensure_directory(target_dir)
            return PikPakArchiveResult(True, 'folder_ready', archive_path=target_dir)
        except Exception as e:
            return PikPakArchiveResult(False, 'error', str(e))

    def ensure_directory(self, remote_path: str) -> None:
        self._run(['mkdir', self.remote(remote_path)])

    def find_candidates(
            self,
            root: str,
            file_name: Optional[str],
            file_size: Optional[int],
            transferred_at: Optional[float],
            poll_seconds: Optional[float] = None
    ) -> tuple[list[dict], float]:
        started_at = self.now()
        deadline = started_at + max(
            float(poll_seconds if poll_seconds is not None else self.config.get('poll_seconds') or 0),
            0
        )
        interval = max(float(self.config.get('poll_interval_seconds') or 0), 0)
        name_fallback_candidates = []
        last_size_matches = 0
        while True:
            candidates, fallback_candidates, size_matches = self._list_matching_candidate_groups(
                root,
                file_name,
                file_size,
                transferred_at
            )
            last_size_matches = size_matches
            if candidates:
                elapsed = self.now() - started_at
                return candidates, elapsed
            if fallback_candidates:
                name_fallback_candidates = fallback_candidates
            if self.now() >= deadline:
                elapsed = self.now() - started_at
                return name_fallback_candidates, elapsed
            time.sleep(interval)

    def _list_matching_candidates(
            self,
            root: str,
            file_name: Optional[str],
            file_size: Optional[int],
            transferred_at: Optional[float]
    ) -> list[dict]:
        candidates, fallback_candidates, _size_matches = self._list_matching_candidate_groups(
            root,
            file_name,
            file_size,
            transferred_at
        )
        return candidates or fallback_candidates

    def _list_matching_candidate_groups(
            self,
            root: str,
            file_name: Optional[str],
            file_size: Optional[int],
            transferred_at: Optional[float]
    ) -> tuple[list[dict], list[dict], int]:
        result = self._run(['lsjson', self.remote(root), '--recursive', '--files-only'])
        try:
            items = json.loads(result.stdout or '[]')
        except json.JSONDecodeError as e:
            raise RuntimeError(f'Unable to parse rclone lsjson output: {e}')
        return self._matching_candidate_groups(items, file_name, file_size, transferred_at)

    def _matching_candidate_groups(
            self,
            items: list[dict],
            file_name: Optional[str],
            file_size: Optional[int],
            transferred_at: Optional[float]
    ) -> tuple[list[dict], list[dict], int]:
        files = [item for item in items if not item.get('IsDir')]
        if file_name:
            name_matches = [
                item for item in files
                if candidate_name_matches(
                    item.get('Name'),
                    file_name,
                    has_disambiguator=file_size is not None or transferred_at is not None
                )
            ]
            metadata_matches = [
                item for item in name_matches
                if self._candidate_metadata_matches(item, file_size, transferred_at)
            ]
            if metadata_matches:
                return metadata_matches, name_matches, len(name_matches)
            if len(name_matches) == 1:
                return name_matches, name_matches, len(name_matches)
            return [], name_matches, len(name_matches)
        size_matches = [
            item for item in files
            if file_size is None or item.get('Size') is None or int(item.get('Size')) == int(file_size)
        ]
        return [
            item for item in size_matches
            if self._candidate_metadata_matches(item, file_size, transferred_at)
        ], [], len(size_matches)

    def _candidate_matches(
            self,
            item: dict,
            file_name: Optional[str],
            file_size: Optional[int],
            transferred_at: Optional[float]
    ) -> bool:
        if item.get('IsDir'):
            return False
        if file_name and not candidate_name_matches(
                item.get('Name'),
                file_name,
                has_disambiguator=file_size is not None or transferred_at is not None
        ):
            return False
        return self._candidate_metadata_matches(item, file_size, transferred_at)

    def _candidate_metadata_matches(
            self,
            item: dict,
            file_size: Optional[int],
            transferred_at: Optional[float]
    ) -> bool:
        if file_size is not None and item.get('Size') is not None and int(item.get('Size')) != int(file_size):
            return False
        if transferred_at is None:
            return True
        mod_time = parse_rclone_time(item.get('ModTime') or item.get('Modified'))
        if mod_time is None:
            return False
        window = max(float(self.config.get('match_window_seconds') or 0), 0)
        return abs(mod_time - float(transferred_at)) <= window

    def moveto(self, source_path: str, target_path: str) -> None:
        self._run(['moveto', self.remote(source_path), self.remote(target_path)])

    def list_directories(
            self,
            remote_path: str,
            *,
            recursive: bool = False,
            timeout: Optional[float] = None,
    ) -> list[str]:
        """Return directory paths relative to ``remote_path`` (rclone lsjson --dirs-only).

        Prefer non-recursive listing for large trees; recursive listing can take
        far longer than the default archive command timeout.
        """
        args = ['lsjson', self.remote(remote_path), '--dirs-only']
        if recursive:
            args.append('--recursive')
        # Large PikPak trees routinely exceed the generic 300s archive timeout.
        if timeout is None:
            timeout = 3600.0 if recursive else 900.0
        result = self._run(args, timeout=timeout)
        try:
            items = json.loads(result.stdout or '[]')
        except json.JSONDecodeError as e:
            raise RuntimeError(f'Unable to parse rclone lsjson output: {e}')
        paths = []
        for item in items or []:
            if item.get('IsDir') is False:
                continue
            path = item.get('Path') or item.get('Name')
            if path:
                paths.append(clean_remote_path(path))
        return paths

    def move_directory(self, source_path: str, target_path: str) -> None:
        """Server-side move/rename of a remote directory via rclone moveto."""
        source = clean_remote_path(source_path)
        target = clean_remote_path(target_path)
        if not source or not target:
            raise RuntimeError('Source and target directory paths are required.')
        parent = posixpath.dirname(target)
        if parent:
            self.ensure_directory(parent)
        self.moveto(source, target)

    def list_archive_channel_folders(self) -> list[str]:
        """List top-level Source Channel Folder names under the archive root."""
        if not self.config.get('remote'):
            return []
        root = clean_remote_path(self.config.get('root_directory') or '')
        if not root:
            return []
        return sorted(self.list_directories(root, recursive=False))

    def upload_to_ingest(
            self,
            local_path: str,
            file_name: Optional[str] = None,
    ) -> PikPakArchiveResult:
        """Upload a local file into PikPak Ingest Folder (My Telegram) via rclone."""
        if not self.config.get('remote'):
            return PikPakArchiveResult(False, 'disabled', 'PikPak rclone remote is missing.')
        if not local_path or not os.path.isfile(local_path):
            return PikPakArchiveResult(False, 'missing_metadata', 'Local upload file is missing.')
        try:
            file_size = os.path.getsize(local_path)
            if file_size <= 0:
                return PikPakArchiveResult(False, 'missing_metadata', '上传文件大小为0')
            remote_path = self.resolve_ingest_path(file_name or os.path.basename(local_path))
            if not remote_path:
                return PikPakArchiveResult(False, 'missing_metadata', 'Upload file name is missing.')
            ingest_root = clean_remote_path(self.config.get('source_directory') or '')
            if ingest_root:
                self.ensure_directory(ingest_root)
            timeout = self._upload_timeout_seconds(file_size)
            self._run(self.copyto_command(local_path, remote_path)[1:], timeout=timeout)
            return PikPakArchiveResult(True, 'uploaded', archive_path=remote_path)
        except Exception as e:
            return PikPakArchiveResult(False, 'error', str(e))

    def resolve_ingest_path(self, file_name: Optional[str]) -> Optional[str]:
        ingest_root = clean_remote_path(self.config.get('source_directory') or '')
        name = clean_remote_segment(file_name or '')
        if not name:
            return None
        return join_remote_path(ingest_root, name)

    def copyto_command(self, local_path: str, remote_path: str) -> list[str]:
        # Keep rclone quiet so async PIPE cannot fill up and deadlock the process.
        return ['rclone', 'copyto', local_path, self.remote(remote_path), '-q', '--stats', '0']

    @staticmethod
    def _upload_timeout_seconds(file_size: int) -> int:
        # Allow slow uplinks; floor 5 minutes, scale ~2s/MB, cap 2 hours.
        megabytes = max(int(file_size or 0), 0) / (1024 * 1024)
        return int(min(max(300, megabytes * 2.0), 7200))

    def remote(self, path: str) -> str:
        remote = str(self.config.get('remote') or '').rstrip(':')
        path = clean_remote_path(path)
        return f'{remote}:{path}' if path else f'{remote}:'

    def _run(self, args: list[str], timeout: Optional[float] = 300):
        command = ['rclone', *args]
        result = self.runner(command, capture_output=True, text=True, timeout=timeout)
        if getattr(result, 'returncode', 0) != 0:
            stderr = getattr(result, 'stderr', '') or ''
            raise RuntimeError(stderr.strip() or f'Command failed: {command}')
        return result


def build_pikpak_archive_client(config: Optional[dict]):
    """Build archive/ingest client when remote is configured.

    `enable` only gates archive_file/moveto; rclone ingest into My Telegram
    remains available whenever remote is set.
    """
    normalized = normalize_archive_config(config)
    if not normalized.get('remote'):
        return DisabledPikPakArchiveClient()
    return RclonePikPakArchiveClient(normalized)


def normalize_archive_config(config: Optional[dict]) -> dict:
    result = DEFAULT_ARCHIVE_CONFIG.copy()
    if isinstance(config, dict):
        result.update(config)
    result['enable'] = bool(result.get('enable'))
    result['remote'] = str(result.get('remote') or '').strip().rstrip(':')
    result['source_directory'] = clean_remote_path(str(result.get('source_directory') or ''))
    result['root_directory'] = clean_remote_path(str(result.get('root_directory') or ''))
    for key in (
            'poll_seconds',
            'poll_interval_seconds',
            'match_window_seconds',
            'poll_cap_seconds',
            'archive_delay_seconds',
            'archive_retry_interval_seconds'
    ):
        try:
            result[key] = max(float(result.get(key)), 0)
        except (TypeError, ValueError):
            result[key] = DEFAULT_ARCHIVE_CONFIG[key]
    cap = result.get('poll_cap_seconds') or 0
    window = result.get('match_window_seconds') or 0
    if window:
        result['poll_cap_seconds'] = min(cap or window, window) if cap else window
    return result


def parse_rclone_time(value) -> Optional[float]:
    if not value:
        return None
    text = str(value).replace('Z', '+00:00')
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def clean_remote_segment(value: str) -> str:
    return str(value).replace('/', '_').replace('\\', '_').strip()


def clean_remote_path(value: str) -> str:
    return str(value or '').replace('\\', '/').strip('/')


def normalize_source_folder_path(value: str) -> str:
    """Allow nested archive folders like channel/post; sanitize each segment."""
    parts = []
    for part in clean_remote_path(value).split('/'):
        cleaned = clean_remote_segment(part)
        if cleaned:
            parts.append(cleaned)
    return '/'.join(parts)


def join_remote_path(*parts: str) -> str:
    clean_parts = [clean_remote_path(part) for part in parts if clean_remote_path(part)]
    return posixpath.join(*clean_parts) if clean_parts else ''


def candidate_remote_path(root: str, candidate_path: str) -> str:
    root = clean_remote_path(root)
    candidate_path = clean_remote_path(candidate_path)
    if not root or not candidate_path or candidate_path == root or candidate_path.startswith(f'{root}/'):
        return candidate_path
    return join_remote_path(root, candidate_path)


def candidate_name_matches(candidate_name: Optional[str], target_name: str, has_disambiguator: bool = False) -> bool:
    candidate_name = clean_remote_segment(candidate_name or '')
    target_name = clean_remote_segment(target_name or '')
    if not candidate_name or not target_name:
        return False
    if candidate_name == target_name:
        return True
    if not has_disambiguator:
        return False
    return normalized_archive_name_key(candidate_name) == normalized_archive_name_key(target_name)


def normalized_archive_name_key(file_name: str) -> tuple[str, str]:
    file_name = unicodedata.normalize('NFKC', clean_remote_segment(file_name))
    stem, extension = posixpath.splitext(file_name)
    stem = re.sub(r'[\s._-]+', '_', stem).strip('_').casefold()
    return stem, extension.casefold()
