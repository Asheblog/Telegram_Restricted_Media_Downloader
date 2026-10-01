# coding=UTF-8
"""WebUI 诊断导出编排（系统日志读取/导出、诊断包）。

从 ``webops/operations.py`` 的 ``WebOperationsMixin`` 拆出的第二组。
依赖以 getter 显式注入，可脱离宿主单独测试。
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable, Optional


class DiagnosticsOperations:
    """系统日志与诊断包导出。"""

    def __init__(
        self,
        *,
        transfer_store_getter: Callable[[], object],
        app_getter: Callable[[], object],
        loop_getter: Callable[[], object],
        last_client_getter: Callable[[], object],
    ) -> None:
        self._transfer_store = transfer_store_getter
        self._app = app_getter
        self._loop = loop_getter
        self._last_client = last_client_getter

    def list_system_logs(
            self,
            limit: int = 50,
            offset: int = 0,
            category: Optional[str] = None,
            level: Optional[str] = None,
            trace_id: Optional[str] = None,
            watch_id: Optional[str] = None,
            today_only: bool = False,
            tz_offset_minutes: Optional[int] = None,
    ) -> dict:
        store = self._transfer_store()
        if not store:
            return {"logs": [], "total": 0, "limit": limit, "offset": offset}
        logs, total = store.list_system_logs(
            limit=limit,
            offset=offset,
            category=category,
            level=level,
            trace_id=trace_id,
            watch_id=watch_id,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes,
        )
        from module.persistence.system_log import annotate_system_logs_can_retry

        return {
            "logs": annotate_system_logs_can_retry(logs),
            "total": total,
            "limit": limit,
            "offset": offset,
            "retention_days": store.SYSTEM_LOGS_RETENTION_DAYS,
        }

    def export_system_logs(
            self,
            category: Optional[str] = None,
            level: Optional[str] = None,
            trace_id: Optional[str] = None,
            watch_id: Optional[str] = None,
            today_only: bool = False,
            tz_offset_minutes: Optional[int] = None,
    ) -> str:
        from module.persistence.system_log import build_system_logs_export_text

        store = self._transfer_store()
        if not store:
            return ""
        return build_system_logs_export_text(
            store,
            category=category,
            level=level,
            trace_id=trace_id,
            watch_id=watch_id,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes,
        )

    def export_diagnostic_bundle(self, payload: Optional[dict] = None) -> dict:
        """Build a secret-containing zip for local repro; returns path + filename."""
        from module import GLOBAL_CONFIG_PATH, LOG_PATH, __version__
        from module.persistence.diagnostic_bundle import (
            DEFAULT_PROBE_LIMIT,
            build_diagnostic_bundle,
            clamp_probe_limit,
            probe_forward_items,
            select_probe_items,
        )

        payload = payload or {}
        if not bool(payload.get("acknowledge_secrets")):
            raise ValueError("acknowledge_secrets_required")

        store = self._transfer_store()
        if not store:
            raise ValueError("transfer_store_unavailable")

        task_id = payload.get("task_id")
        if task_id not in (None, ""):
            task_id = int(task_id)
        else:
            task_id = None
        probe_limit = clamp_probe_limit(payload.get("probe_limit", DEFAULT_PROBE_LIMIT))
        run_probe = bool(payload.get("run_probe", True))
        target_chat = str(payload.get("target_chat_id") or "pikpak_bot")

        probe_items = select_probe_items(store, task_id=task_id, limit=probe_limit)
        if task_id is None and probe_items:
            task_id = int(probe_items[0].get("task_id"))

        probe_results = {
            "probe_limit": probe_limit,
            "run_probe": run_probe,
            "items": probe_items,
            "results": [],
        }
        if run_probe and probe_items:
            app = self._app()
            client = getattr(app, "client", None) or self._last_client()
            loop = self._loop()
            if client is None or loop is None:
                probe_results["error"] = "telegram_client_unavailable"
            else:
                future = asyncio.run_coroutine_threadsafe(
                    probe_forward_items(
                        client,
                        probe_items,
                        target_chat_id=target_chat,
                        do_copy=True,
                        do_forward=True,
                    ),
                    loop,
                )
                try:
                    probe_results.update(future.result(timeout=180))
                except Exception as e:  # noqa: BLE001 - 探测失败要如实记录进包
                    probe_results["error"] = f"{type(e).__name__}: {e}"

        app = self._app()
        config_path = Path(getattr(app, "config_path", "") or "")
        session_directory = Path(
            getattr(app, "work_directory", None)
            or (getattr(app, "config", {}) or {}).get("session_directory")
            or ""
        )
        temp_directory = Path(
            getattr(app, "temp_directory", None)
            or (getattr(app, "config", {}) or {}).get("temp_directory")
            or store.directory
        )
        export_root = Path(temp_directory) / "diagnostic_exports"
        export_root.mkdir(parents=True, exist_ok=True)

        system_logs_text = self.export_system_logs(today_only=False)
        zip_path = build_diagnostic_bundle(
            work_dir=export_root,
            version=__version__,
            config_yaml_path=config_path if config_path.is_file() else None,
            global_config_path=Path(GLOBAL_CONFIG_PATH),
            session_directory=session_directory,
            transfer_db_path=Path(store.path),
            store=store,
            system_logs_text=system_logs_text,
            app_log_path=Path(LOG_PATH),
            probe_items=probe_items,
            probe_results=probe_results,
            task_id=task_id,
            probe_limit=probe_limit,
            extra_meta={
                "target_chat_id": target_chat,
                "run_probe": run_probe,
            },
        )
        return {
            "path": str(zip_path),
            "filename": zip_path.name,
            "task_id": task_id,
            "probe_item_count": len(probe_items),
            "contains_secrets": True,
        }
