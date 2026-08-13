# coding=UTF-8
from typing import Optional


PIKPAK_TARGET_PROFILE = 'pikpak'
PIKPAK_DEFAULT_MAX_FILE_SIZE = 4 * 1024 ** 3
PIKPAK_MAX_ACCOUNTS = 5

DEFAULT_TARGET_PROFILES = {
    PIKPAK_TARGET_PROFILE: {
        'max_file_size': PIKPAK_DEFAULT_MAX_FILE_SIZE,
        # Bound PikPak accounts (one rclone remote per account). ``archive.remote``
        # points at the currently active remote; switching only rewrites that
        # pointer. Credentials live exclusively in rclone.conf (never here).
        'accounts': [],
        'archive': {
            # New installs keep archive off until First-run Setup Wizard
            # successfully probes rclone (ADR-0012). Existing configs keep
            # their persisted enable flag.
            'enable': False,
            'remote': 'pikpak',
            'source_directory': 'My Telegram',
            'root_directory': 'Telegram',
            'poll_seconds': 180,
            'poll_interval_seconds': 5,
            'match_window_seconds': 3600,
            'poll_cap_seconds': 1800,
            'archive_delay_seconds': 600,
            'archive_retry_interval_seconds': 300
        }
    }
}


def target_profile_limit(settings, target_profile: Optional[str]) -> Optional[int]:
    if not target_profile:
        return None
    config = getattr(settings, 'config', settings) or {}
    profiles = config.get('target_profiles') if isinstance(config, dict) else None
    profile = (profiles or DEFAULT_TARGET_PROFILES).get(target_profile)
    if not isinstance(profile, dict):
        return None
    value = profile.get('max_file_size')
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TARGET_PROFILES.get(target_profile, {}).get('max_file_size')
    return limit if limit > 0 else None


def target_profile_size_error(target_profile: str, file_size: int, limit: int) -> str:
    label = 'PikPak' if target_profile == PIKPAK_TARGET_PROFILE else target_profile
    return f'{label}目标大小上限为{limit}字节,当前文件大小为{file_size}字节。'
