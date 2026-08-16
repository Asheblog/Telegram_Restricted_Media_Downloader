# coding=UTF-8
"""Pure PikPak transfer rules shared by the transfer layer.

Kept here so ``transfer.*`` does not import the ``adapters.pikpak``
integration manager. The adapter re-exports / delegates to these helpers
for back-compat.
"""
import datetime
from typing import Optional


def transfer_item_archive_match_original_name(item: dict) -> Optional[bool]:
    value = item.get("archive_match_original_name")
    if value is None:
        return None
    return bool(int(value))


def transfer_item_archive_timestamp(item: dict) -> float:
    for key in ("updated_at", "created_at"):
        value = item.get(key)
        if not value:
            continue
        try:
            return datetime.datetime.fromisoformat(str(value)).timestamp()
        except ValueError:
            continue
    return datetime.datetime.now(datetime.UTC).timestamp()


def message_has_pikpak_ingestible_media(message) -> bool:
    """True when the message carries media PikPak can typically save (not bare text)."""
    if message is None:
        return False
    from module.core.media_types import DOWNLOAD_MEDIA_TYPES

    for dtype in DOWNLOAD_MEDIA_TYPES:
        if getattr(message, dtype, None):
            return True
    return False
