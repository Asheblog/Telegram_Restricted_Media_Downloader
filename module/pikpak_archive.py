# coding=UTF-8
import json
import posixpath
import subprocess
import time

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional


DEFAULT_ARCHIVE_CONFIG = {
    'enable': False,
    'remote': '',
    'source_directory': 'My Telegram',
    'root_directory': 'Telegram',
    'poll_seconds': 60,
    'poll_interval_seconds': 5,
    'match_window_seconds': 3600
}


@dataclass
class PikPakArchiveResult:
    ok: bool
    status: str
    message: str = ''
    archive_path: Optional[str] = None


class DisabledPikPakArchiveClient:
    def archive_file(self, *args, **kwargs) -> PikPakArchiveResult:
        return PikPakArchiveResult(False, 'disabled', 'PikPak archive is disabled.')


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

    def archive_file(
            self,
            source_folder: str,
            file_name: Optional[str],
            file_size: Optional[int] = None,
            transferred_at: Optional[float] = None
    ) -> PikPakArchiveResult:
        if not self.enabled:
            return PikPakArchiveResult(False, 'disabled', 'PikPak archive is disabled or remote is missing.')
        if not source_folder:
            return PikPakArchiveResult(False, 'missing_metadata', 'Source folder is missing.')
        if not file_name and (file_size is None or transferred_at is None):
            return PikPakArchiveResult(False, 'missing_metadata', 'File name is missing and size/time matching is unavailable.')

        try:
            source_folder = clean_remote_segment(source_folder)
            file_name = clean_remote_segment(file_name) if file_name else None
            source_root = clean_remote_path(self.config.get('source_directory') or '')
            target_root = clean_remote_path(self.config.get('root_directory') or '')
            target_dir = join_remote_path(target_root, source_folder)
            self.ensure_directory(target_dir)
            candidates = self.find_candidates(
                root=source_root,
                file_name=file_name,
                file_size=file_size,
                transferred_at=transferred_at
            )
            if not candidates:
                archived_candidates = self._list_matching_candidates(
                    root=target_dir,
                    file_name=file_name,
                    file_size=file_size,
                    transferred_at=transferred_at
                )
                if len(archived_candidates) == 1:
                    archived_name = clean_remote_segment(file_name or archived_candidates[0].get('Name'))
                    if not archived_name:
                        return PikPakArchiveResult(False, 'not_found', 'No archived PikPak file name was available.')
                    archived_path = candidate_remote_path(
                        target_dir,
                        archived_candidates[0].get('Path') or archived_name
                    )
                    return PikPakArchiveResult(True, 'already_archived', archive_path=archived_path)
                if len(archived_candidates) > 1:
                    return PikPakArchiveResult(False, 'ambiguous', f'Multiple archived PikPak files matched {file_name}.')
                return PikPakArchiveResult(False, 'not_found', f'No PikPak file matched {file_name}.')
            if len(candidates) > 1:
                return PikPakArchiveResult(False, 'ambiguous', f'Multiple PikPak files matched {file_name}.')
            source_path = candidate_remote_path(source_root, candidates[0].get('Path') or candidates[0].get('Name'))
            target_name = clean_remote_segment(file_name or candidates[0].get('Name'))
            target_path = join_remote_path(target_dir, target_name)
            if not source_path:
                return PikPakArchiveResult(False, 'not_found', f'No PikPak file path matched {file_name}.')
            if not target_name:
                return PikPakArchiveResult(False, 'not_found', 'No PikPak file name was available for archive.')
            if source_path == target_path:
                return PikPakArchiveResult(True, 'already_archived', archive_path=target_path)
            self.moveto(source_path, target_path)
            return PikPakArchiveResult(True, 'success', archive_path=target_path)
        except Exception as e:
            return PikPakArchiveResult(False, 'error', str(e))

    def ensure_directory(self, remote_path: str) -> None:
        self._run(['mkdir', self.remote(remote_path)])

    def find_candidates(
            self,
            root: str,
            file_name: str,
            file_size: Optional[int],
            transferred_at: Optional[float]
    ) -> list[dict]:
        deadline = self.now() + max(float(self.config.get('poll_seconds') or 0), 0)
        interval = max(float(self.config.get('poll_interval_seconds') or 0), 0)
        while True:
            candidates = self._list_matching_candidates(root, file_name, file_size, transferred_at)
            if candidates or self.now() >= deadline:
                return candidates
            time.sleep(interval)

    def _list_matching_candidates(
            self,
            root: str,
            file_name: str,
            file_size: Optional[int],
            transferred_at: Optional[float]
    ) -> list[dict]:
        result = self._run(['lsjson', self.remote(root), '--recursive', '--files-only'])
        try:
            items = json.loads(result.stdout or '[]')
        except json.JSONDecodeError as e:
            raise RuntimeError(f'Unable to parse rclone lsjson output: {e}')
        return [
            item for item in items
            if self._candidate_matches(item, file_name, file_size, transferred_at)
        ]

    def _candidate_matches(
            self,
            item: dict,
            file_name: str,
            file_size: Optional[int],
            transferred_at: Optional[float]
    ) -> bool:
        if item.get('IsDir'):
            return False
        if file_name and item.get('Name') != file_name:
            return False
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

    def remote(self, path: str) -> str:
        remote = str(self.config.get('remote') or '').rstrip(':')
        path = clean_remote_path(path)
        return f'{remote}:{path}' if path else f'{remote}:'

    def _run(self, args: list[str]):
        command = ['rclone', *args]
        result = self.runner(command, capture_output=True, text=True, timeout=120)
        if getattr(result, 'returncode', 0) != 0:
            stderr = getattr(result, 'stderr', '') or ''
            raise RuntimeError(stderr.strip() or f'Command failed: {command}')
        return result


def build_pikpak_archive_client(config: Optional[dict]):
    normalized = normalize_archive_config(config)
    if not normalized.get('enable'):
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
    for key in ('poll_seconds', 'poll_interval_seconds', 'match_window_seconds'):
        try:
            result[key] = max(float(result.get(key)), 0)
        except (TypeError, ValueError):
            result[key] = DEFAULT_ARCHIVE_CONFIG[key]
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


def join_remote_path(*parts: str) -> str:
    clean_parts = [clean_remote_path(part) for part in parts if clean_remote_path(part)]
    return posixpath.join(*clean_parts) if clean_parts else ''


def candidate_remote_path(root: str, candidate_path: str) -> str:
    root = clean_remote_path(root)
    candidate_path = clean_remote_path(candidate_path)
    if not root or not candidate_path or candidate_path == root or candidate_path.startswith(f'{root}/'):
        return candidate_path
    return join_remote_path(root, candidate_path)
