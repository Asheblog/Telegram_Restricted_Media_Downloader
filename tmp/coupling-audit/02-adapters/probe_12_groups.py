import ast, os, json
ROOT = r"E:\codebase\tgbot"
P = os.path.join(ROOT, "module/adapters/webui/operations.py")
src = open(P, encoding="utf-8").read()
t = ast.parse(src)
mixin = [n for n in t.body if isinstance(n, ast.ClassDef) and n.name == "WebOperationsMixin"][0]
met = [m for m in mixin.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]

G = {
"任务控制(含区间检测)": """_ensure_transfer_store _bind_transfer_store_runtime _web_ui_operations _require_web_task_manager
should_continue_web_transfer_task should_continue_web_transfer_item should_start_next_web_transfer_item
has_active_transfer_io settle_web_task_pause_request cancel_task_uploads pause_task_uploads
_transfer_download_registry _register_transfer_download_task _unregister_transfer_download_task cancel_task_downloads
submit_web_task discard_web_task_submission drop_web_task_from_queue delete_web_task pause_web_task resume_web_task
retry_failed_web_task next_web_operation_id submit_web_operation create_upload create_channel_download list_operations
process_web_operation apply_web_upload apply_web_channel_download process_web_task_queue start_next_web_transfer_task
is_web_transfer_task_schedulable finish_web_transfer_task detect_transfer_range detect_transfer_range_async
detect_transfer_range_by_history_scan detect_transfer_range_fast get_first_transfer_range_history_message
iter_transfer_range_history recover_pikpak_failed_item_before_retry""",
"监听(watch+评论延迟抓取)": """_persisted_watch_records _set_live_watch_status _watch_payload_from_record list_watches
mark_pending_watch set_live_watch_status persisted_watches watch_payload_from_record create_watch
export_forward_watches delete_watch update_watch list_watch_events restore_live_transfer_watches
_ensure_watch_applicator apply_web_watch remove_web_watch _ensure_comment_delay_scheduler
_has_active_derived_tasks_for_deferred_capture _cancel_derived_tasks_for_deferred_capture
schedule_or_forward_discussion_replies list_deferred_discussion_captures cancel_deferred_discussion_capture
run_deferred_discussion_capture_now retry_deferred_discussion_capture""",
"账号与设置": """start_web_ui recover_web_runtime _archive_settings _set_archive_settings _normalize_account_remote
_next_pikpak_remote_name _invalidate_pikpak_archive_client _setup_coordinator _read_rclone_remotes get_web_settings
update_web_settings _pikpak_accounts _set_pikpak_accounts list_pikpak_accounts add_pikpak_account
switch_pikpak_account remove_pikpak_account""",
"安装向导": """is_setup_ready get_setup_status save_setup_api_credentials configure_setup_rclone skip_setup_rclone
test_setup_rclone save_setup_bot_token skip_setup_bot_token""",
"媒体清理": "_ensure_media_manager scan_media_for_cleanup cleanup_media_files maybe_run_scheduled_media_cleanup list_cleanup_logs",
"归档工具": """_run_telegram_coro _archive_author_ops list_archive_author_channels resume_interrupted_archive_author_jobs
stop_archive_author_job scan_archive_author_reorganize resolve_archive_author_reorganize execute_archive_author_reorganize
list_archive_author_plan_moves get_archive_author_job get_active_archive_author_job retry_archive_from_system_log""",
"诊断导出": "list_system_logs export_diagnostic_bundle export_system_logs",
"统计": "statistics export_table _export_channel_statistics_table",
}
assign = {}
for g, names in G.items():
    for n in names.split():
        assign[n] = g
names_all = [m.name for m in met]
missing = [n for n in names_all if n not in assign]
extra = [n for n in assign if n not in names_all]
print("total methods:", len(names_all))
print("unassigned:", missing)
print("assigned-but-missing-in-file:", extra)
tot = 0
print(f"\n{'组':30s} {'方法数':>5s}  行号区间            占 mixin 主体")
print("-" * 84)
for g in G:
    ms = sorted([m for m in met if assign.get(m.name) == g], key=lambda m: m.lineno)
    tot += len(ms)
    a, b = ms[0].lineno, ms[-1].end_lineno
    print(f"{g:30s} {len(ms):5d}  L{a}-{b:<14d} {100*len(ms)/len(met):.1f}%")
print("-" * 84)
print(f"{'合计':30s} {tot:5d}  L104-1860")
# shim count per group
def is_shim(m):
    body = [b for b in m.body if not (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant))]
    if len(body) != 1: return False
    b = body[0]
    v = b.value if isinstance(b, (ast.Return, ast.Expr)) else None
    return isinstance(v, ast.Call)
print("\n每组纯转发 shim(单语句转发) 数：")
for g in G:
    ms = [m for m in met if assign.get(m.name) == g]
    s = sum(1 for m in ms if is_shim(m))
    print(f"  {g:30s} shim {s:3d}/{len(ms)}")
sh = sum(1 for m in met if is_shim(m))
print(f"  {'TOTAL':30s} shim {sh:3d}/{len(met)}")
