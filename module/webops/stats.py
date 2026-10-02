# coding=UTF-8
"""WebUI 统计与报表导出的编排实现。

从 ``adapters/webui/operations.py`` 的 ``WebOperationsMixin`` 拆出的第一组，
目的是让宿主不再承载具体业务实现：mixin 只按名字转发到本类。

依赖显式注入（三个 getter），因此本类可以脱离"276 个方法的宿主"单独测试。
"""
from __future__ import annotations

import os
import sys
from typing import Callable, Optional

from module.utils.util import is_docker


class StatsOperations:
    """频道下载统计聚合与报表导出（原先内联在宿主 mixin 上）。"""

    def __init__(
        self,
        *,
        transfer_store_getter: Callable[[], object],
        web_operations_getter: Callable[[], dict],
        app_getter: Callable[[], object],
    ) -> None:
        self._transfer_store = transfer_store_getter
        self._web_operations = web_operations_getter
        self._app = app_getter

    # ── 统计聚合 ──

    def statistics(self, tz_offset_minutes: Optional[int] = None) -> dict:
        from module.adapters.webui.statistics_payload import (
            DEFAULT_STATISTICS_WINDOW_DAYS,
            build_statistics_payload,
        )

        rows = self._transfer_store().aggregate_channel_download_stats(
            days=DEFAULT_STATISTICS_WINDOW_DAYS,
            tz_offset_minutes=tz_offset_minutes,
        )
        payload = build_statistics_payload(
            rows,
            window_days=DEFAULT_STATISTICS_WINDOW_DAYS,
        )
        payload["operations"] = list(self._web_operations().values())[-50:]
        return payload

    # ── 报表导出 ──

    def export_table(self, table_type: str) -> dict:
        app = self._app()
        if table_type == "channel":
            return self._export_channel_statistics_table()
        if table_type == "link":
            from module.domain.transfer_state.models import DownloadTask

            exported = app.print_link_table(
                link_info=DownloadTask.LINK_INFO,
                export=True,
                only_export=True,
            )
            folder = "form" if is_docker() else "DownloadRecordForm"
        elif table_type == "count":
            exported = app.print_count_table(export=True, only_export=True)
            folder = "form" if is_docker() else "DownloadRecordForm"
        else:
            from module.domain.transfer_state.models import UploadTask

            exported = app.print_upload_table(
                upload_tasks=UploadTask.TASKS,
                export=True,
                only_export=True,
            )
            folder = "form" if is_docker() else "UploadRecordForm"
        return {
            "exported": bool(exported),
            "table_type": table_type,
            "directory": folder,
        }

    def _export_channel_statistics_table(self) -> dict:
        import csv
        import datetime

        from module.adapters.webui.statistics_payload import (
            DEFAULT_STATISTICS_WINDOW_DAYS,
            build_statistics_payload,
        )

        rows = self._transfer_store().aggregate_channel_download_stats(
            days=DEFAULT_STATISTICS_WINDOW_DAYS,
            tz_offset_minutes=None,
        )
        payload = build_statistics_payload(
            rows,
            window_days=DEFAULT_STATISTICS_WINDOW_DAYS,
        )
        if not payload["tables"]["channel"]["available"]:
            return {
                "exported": False,
                "table_type": "channel",
                "directory": "DownloadRecordForm",
            }
        if is_docker():
            directory = "/app/form/ChannelForm"
            folder = "form"
        else:
            directory = os.path.join(
                os.path.dirname(os.path.abspath(sys.argv[0])),
                "DownloadRecordForm",
                "ChannelForm",
            )
            folder = "DownloadRecordForm"
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(
            directory,
            f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_频道下载统计表.csv',
        )
        with open(path, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["频道", "成功", "失败", "跳过", "合计", "成功率"])
            for row in payload["channels"]:
                writer.writerow([
                    row["channel"],
                    row["success"],
                    row["failure"],
                    row["skip"],
                    row["total"],
                    row["success_rate"],
                ])
        return {
            "exported": True,
            "table_type": "channel",
            "directory": folder,
            "path": path,
        }
