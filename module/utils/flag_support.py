# coding=UTF-8
"""命令行标志位拆分与监听规则编解码。

从 ``utils/util.py`` **逐字搬移**：这些都是"把 `[include_comment]` 这类方括号
前缀/后缀从参数里拆出来"的纯字符串操作，以及监听规则的编码/解码。

放在独立模块是为了让 `util.py` 不再同时承载标志位解析、终端展示与运行环境探测
三类互不相关的职责（`util.py` 有 16 个依赖方，混在一起会放大影响面）。
``utils/util.py`` 仍 re-export 这些名字，既有导入不必改。
"""
from __future__ import annotations

from typing import Tuple



INCLUDE_COMMENT_FLAGS = {"--include-comment", "--include-comments", "--comment"}

RESOLVE_DEEP_LINK_FLAGS = {"--resolve-deep-link", "--resolve_deep_link"}

ARCHIVE_BY_AUTHOR_FLAGS = {"--archive-by-author", "--archive_by_author"}

ARCHIVE_TITLE_SOURCE_PREFIXES = ("--archive-title-source=", "--archive_title_source=")


def safe_index(lst: list, index: int, default=None):
    try:
        return lst[index]
    except IndexError:
        return default


def split_include_comment_flag(args: list) -> Tuple[list, bool]:
    include_comment = False
    clean_args = []
    for arg in args:
        if str(arg).strip().lower() in INCLUDE_COMMENT_FLAGS:
            include_comment = True
        else:
            clean_args.append(arg)
    return clean_args, include_comment


def split_resolve_deep_link_flag(args: list) -> Tuple[list, bool]:
    resolve_deep_link = False
    clean_args = []
    for arg in args:
        if str(arg).strip().lower() in RESOLVE_DEEP_LINK_FLAGS:
            resolve_deep_link = True
        else:
            clean_args.append(arg)
    return clean_args, resolve_deep_link


def split_archive_by_author_flag(args: list) -> Tuple[list, bool]:
    archive_by_author = False
    clean_args = []
    for arg in args:
        if str(arg).strip().lower() in ARCHIVE_BY_AUTHOR_FLAGS:
            archive_by_author = True
        else:
            clean_args.append(arg)
    return clean_args, archive_by_author


def split_archive_title_source_flag(args: list) -> Tuple[list, str]:
    from module.domain.archive_naming.source_folders import (
        normalize_archive_title_source,
        ARCHIVE_TITLE_SOURCE_AUTO,
    )

    archive_title_source = ARCHIVE_TITLE_SOURCE_AUTO
    clean_args = []
    for arg in args:
        lowered = str(arg).strip().lower()
        matched = False
        for prefix in ARCHIVE_TITLE_SOURCE_PREFIXES:
            if lowered.startswith(prefix):
                archive_title_source = normalize_archive_title_source(
                    lowered[len(prefix) :]
                )
                matched = True
                break
        if not matched:
            clean_args.append(arg)
    return clean_args, archive_title_source


def make_forward_watch_rule(
    source_link: str,
    target_link: str,
    include_comment: bool = False,
    resolve_deep_link: bool = False,
    archive_by_author: bool = False,
    archive_title_source: str = "auto",
) -> str:
    from module.domain.archive_naming.source_folders import (
        normalize_archive_title_source,
        ARCHIVE_TITLE_SOURCE_AUTO,
    )

    rule = f"{source_link} {target_link}"
    if include_comment:
        rule += " --include-comment"
    if resolve_deep_link:
        rule += " --resolve-deep-link"
    if archive_by_author:
        rule += " --archive-by-author"
    title_source = normalize_archive_title_source(archive_title_source)
    if title_source != ARCHIVE_TITLE_SOURCE_AUTO:
        rule += f" --archive-title-source={title_source}"
    return rule


def parse_forward_watch_rule(rule: str) -> dict:
    args, include_comment = split_include_comment_flag(str(rule).split())
    args, resolve_deep_link = split_resolve_deep_link_flag(args)
    args, archive_by_author = split_archive_by_author_flag(args)
    args, archive_title_source = split_archive_title_source_flag(args)
    return {
        "source_link": safe_index(args, 0, ""),
        "target_link": safe_index(args, 1, ""),
        "include_comment": include_comment,
        "resolve_deep_link": resolve_deep_link,
        "archive_by_author": archive_by_author,
        "archive_title_source": archive_title_source,
    }
