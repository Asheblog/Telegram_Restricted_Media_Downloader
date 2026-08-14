# coding=UTF-8
"""Archive title source: canonical enum values + normalization.

Moved out of ``module/source_folders`` so ``persistence`` no longer depends on
the top-level kitchen-sink module (arch-decouple Phase 2c). ``source_folders``
re-exports these for back-compat.
"""

# Per-task preference for the descriptive leaf of Source Post Archive Path.
ARCHIVE_TITLE_SOURCE_AUTO = "auto"
ARCHIVE_TITLE_SOURCE_TITLE = "title"
ARCHIVE_TITLE_SOURCE_HASHTAG = "hashtag"
ARCHIVE_TITLE_SOURCE_BODY = "body"
ARCHIVE_TITLE_SOURCES = frozenset(
    {
        ARCHIVE_TITLE_SOURCE_AUTO,
        ARCHIVE_TITLE_SOURCE_TITLE,
        ARCHIVE_TITLE_SOURCE_HASHTAG,
        ARCHIVE_TITLE_SOURCE_BODY,
    }
)


def normalize_archive_title_source(value) -> str:
    """Return a valid archive title source; unknown/empty → ``auto``."""
    if not isinstance(value, str):
        return ARCHIVE_TITLE_SOURCE_AUTO
    key = value.strip().casefold()
    if key in ARCHIVE_TITLE_SOURCES:
        return key
    return ARCHIVE_TITLE_SOURCE_AUTO


__all__ = [
    "ARCHIVE_TITLE_SOURCE_AUTO",
    "ARCHIVE_TITLE_SOURCE_TITLE",
    "ARCHIVE_TITLE_SOURCE_HASHTAG",
    "ARCHIVE_TITLE_SOURCE_BODY",
    "ARCHIVE_TITLE_SOURCES",
    "normalize_archive_title_source",
]
