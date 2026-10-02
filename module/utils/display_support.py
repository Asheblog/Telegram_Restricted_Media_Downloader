# coding=UTF-8
"""终端展示辅助（宽度探测与文件名截断）。

从 ``utils/util.py`` **逐字搬移**：与网络、配置、运行环境都无关的纯展示逻辑。
``utils/util.py`` 仍 re-export，既有导入不必改。
"""
from __future__ import annotations

import os


from rich.text import Text



def get_terminal_width() -> int:
    terminal_width: int = 120
    try:
        terminal_width: int = os.get_terminal_size().columns
    except OSError:
        pass
    return terminal_width


def truncate_display_filename(file_name: str) -> Text:
    terminal_width: int = get_terminal_width()
    max_width: int = max(int(terminal_width * 0.3), 1)
    text = Text(file_name)
    text.truncate(max_width=max_width, overflow="ellipsis")
    return text
