# coding=UTF-8
try:
    from module.util import (  # noqa: F401
        is_docker,
        parse_link,
        format_chat_link,
        get_my_id,
        get_message_by_link,
        get_chat_with_notify,
        safe_message,
        safe_delete_message,
        truncate_display_filename,
        Issues,
        make_forward_watch_rule,
        parse_forward_watch_rule,
        is_allow_upload,
        safe_index,
        get_valid_chat_id,
        split_include_comment_flag,
    )
except ImportError:
    pass

try:
    from module.path_tool import (  # noqa: F401
        is_file_duplicate,
        safe_delete,
        get_file_size,
        split_path,
        compare_file_size,
        move_to_save_directory,
        safe_replace,
        validate_title,
        extract_full_extension,
        is_compressed_file,
        safe_scan_directory_file,
        gen_backup_config,
        get_mime_from_extension,
    )
except ImportError:
    pass

try:
    from module.stdio import StatisticalTable, ProgressBar, MetaData  # noqa: F401
except ImportError:
    pass

try:
    from module.filter import Filter  # noqa: F401
except ImportError:
    pass

try:
    from module.source_folders import (  # noqa: F401
        source_folder_from_link,
        source_folder_from_message,
    )
except ImportError:
    pass

try:
    from module.diagnostics import RichDiagnosticAdapter, default_diagnostic  # noqa: F401
except ImportError:
    pass

try:
    from module.parser import PARSE_ARGS  # noqa: F401
except ImportError:
    pass

try:
    from module.language import _t  # noqa: F401
except ImportError:
    pass
