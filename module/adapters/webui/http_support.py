# coding=UTF-8
"""WebUI 的 HTTP 请求解析与校验辅助。

从 ``server.py`` **逐字搬移**：这些函数只依赖 ``contracts`` 与标准库，
不碰服务器状态，因此与 `WebUiServer` 分开可以让 server 只留请求编排。

`MAX_JSON_BODY_BYTES` 也搬到这里 —— 它只被 ``declared_length`` 使用；
``server.py`` 会 import 回来以保持既有名字可用。
"""
from __future__ import annotations

import datetime
from http import HTTPStatus
from typing import Optional
from urllib.parse import urlparse

from module.adapters.webui.contracts import WebUiApiError

# JSON 请求体上限：WebUI 只收发控制数据（路径 / 链接 / 监听备份），不上传媒体本体。
MAX_JSON_BODY_BYTES = 8 * 1024 * 1024


def declared_length(handler) -> int:
    """校验并返回 Content-Length 声明的请求体长度。

    单一真源：``_consume_request_body``（决定读多少）与 ``_read_json``（回 400/413）
    都走这里，避免上限变更后两处不一致。
    """
    raw_length = handler.headers.get("content-length") if handler.headers else None
    try:
        length = int(raw_length or "0")
    except (TypeError, ValueError):
        raise WebUiApiError(
            "invalid_content_length",
            "Invalid Content-Length header.",
            HTTPStatus.BAD_REQUEST,
        )
    if length < 0:
        raise WebUiApiError(
            "invalid_content_length",
            "Invalid Content-Length header.",
            HTTPStatus.BAD_REQUEST,
        )
    if length > MAX_JSON_BODY_BYTES:
        raise WebUiApiError(
            "request_body_too_large",
            "Request body is too large.",
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )
    return length


def normalize_optional_int(value):
    return int(value) if value not in (None, "") else None


def is_message_link(link: str) -> bool:
    try:
        parsed = urlparse(str(link).strip())
    except ValueError:
        return False
    paths = [part for part in parsed.path.split("/") if part]
    if not paths:
        return False
    if paths[0] == "c":
        return len(paths) >= 3 and paths[-1].isdigit()
    return len(paths) >= 2 and paths[-1].isdigit()


def normalize_detected_transfer_range(value) -> Optional[tuple[int, int]]:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        start_id = value.get("start_id")
        end_id = value.get("end_id")
    else:
        try:
            start_id, end_id = value
        except (TypeError, ValueError):
            return None
    if start_id in (None, "") or end_id in (None, ""):
        return None
    return int(start_id), int(end_id)


def parse_optional_timestamp(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        pass
    try:
        return datetime.datetime.fromisoformat(text).timestamp()
    except ValueError:
        raise WebUiApiError(
            "invalid_date_range",
            "Date range values must be timestamps or ISO datetimes.",
            HTTPStatus.BAD_REQUEST,
        )


def normalize_date_range(value) -> dict:
    if not isinstance(value, dict):
        return {"start_date": None, "end_date": None}
    start_date = parse_optional_timestamp(value.get("start_date"))
    end_date = parse_optional_timestamp(value.get("end_date"))
    if start_date is not None and end_date is not None and end_date < start_date:
        raise WebUiApiError(
            "date_range_end_before_start",
            "Date range end must be greater than or equal to start.",
            HTTPStatus.BAD_REQUEST,
        )
    return {"start_date": start_date, "end_date": end_date}
