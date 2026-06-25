# coding=UTF-8
from typing import Optional


PIKPAK_TARGET_PROFILE = 'pikpak'
PIKPAK_DEFAULT_MAX_FILE_SIZE = 4 * 1024 ** 3

DEFAULT_TARGET_PROFILES = {
    PIKPAK_TARGET_PROFILE: {
        'max_file_size': PIKPAK_DEFAULT_MAX_FILE_SIZE
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
