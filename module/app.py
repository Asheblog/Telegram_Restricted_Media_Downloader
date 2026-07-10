# coding=UTF-8
"""Compatibility shim — implementation in module.core.app."""
from module.path_tool import (  # noqa: F401
    extract_full_extension,
    get_extension,
    is_compressed_file,
    truncate_filename,
    validate_title,
)
from module.core.app import Application, DownloadFileName  # noqa: F401
