import ast, os, re, json, collections

ROOT = r"E:\codebase\tgbot"
P = os.path.join(ROOT, "module", "adapters", "webui", "operations.py")
src = open(P, encoding="utf-8").read()
tree = ast.parse(src)

mixin = None
for n in tree.body:
    if isinstance(n, ast.ClassDef) and n.name == "WebOperationsMixin":
        mixin = n

met = [m for m in mixin.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
print(f"WebOperationsMixin: {len(met)} methods, class lines {mixin.lineno}-{mixin.end_lineno}")

buckets = collections.Counter()
for m in met:
    n = m.end_lineno - m.lineno + 1
    if n <= 3: buckets["<=3"] += 1
    elif n <= 10: buckets["4-10"] += 1
    elif n <= 30: buckets["11-30"] += 1
    elif n <= 60: buckets["31-60"] += 1
    else: buckets[">60"] += 1
print("size buckets:", dict(buckets))

# ---- delegation shim detection: body is only return/expr delegation ----
def is_shim(m):
    body = [b for b in m.body if not (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str))]
    if len(body) != 1:
        return None
    b = body[0]
    if isinstance(b, ast.Return) and isinstance(b.value, ast.Call):
        c = b.value
    elif isinstance(b, ast.Expr) and isinstance(b.value, ast.Call):
        c = b.value
    else:
        return None
    f = c.func
    if isinstance(f, ast.Attribute):
        try:
            return ast.unparse(c.func)
        except Exception:
            return None
    return None

shims = []
for m in met:
    t = is_shim(m)
    if t:
        shims.append((m.name, m.lineno, m.end_lineno, t))
print(f"\n=== pure delegation shims (1 stmt, call): {len(shims)}/{len(met)} ===")
for name, s, e, t in shims:
    print(f"  {name}  L{s}-{e}  ->  {t}")

# ---- self.<attr> usage across whole mixin ----
attrs = collections.Counter()
for node in ast.walk(mixin):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        attrs[node.attr] += 1
print(f"\n=== distinct self.<attr> touched in mixin: {len(attrs)} ===")
print("top 40:", attrs.most_common(40))
json.dump(attrs.most_common(), open(os.path.join(ROOT,"tmp","coupling-audit","02-adapters","self_attrs.json"),"w"), indent=1)

# ---- which attrs look like host-manager delegation ----
mgr = [a for a in attrs if re.search(r"(manager|store|registry|_host|_ops|coordinator|client|service|_app|_bot|_downloader)", a)]
print(f"\n=== manager-ish self.<attr> count: {len(mgr)} ===")
print(sorted(mgr))

# ---- method groups ----
GROUPS = [
 ("task-control", r"^(submit_web_task|discard_web_task_submission|drop_web_task_from_queue|delete_web_task|pause_web_task|resume_web_task|retry_failed_web_task|cancel_task_uploads|pause_task_uploads|cancel_task_downloads|create_upload|create_channel_download|list_operations|next_web_operation_id|submit_web_operation|process_web_operation|process_web_task_queue|start_next_web_transfer_task|finish_web_transfer_task|is_web_transfer_task_schedulable|should_|has_active_transfer_io|settle_web_task_pause_request|apply_web_upload|apply_web_channel_download|_ensure_transfer_store|_bind_transfer_store_runtime|_transfer_download_registry|_register_transfer_download_task|_unregister_transfer_download_task|_web_ui_operations|_require_web_task_manager)"),
 ("watches-listeners", r"^(list_watches|mark_pending_watch|set_live_watch_status|persisted_watches|watch_payload_from_record|create_watch|export_forward_watches|delete_watch|update_watch|list_watch_events|restore_live_transfer_watches|apply_web_watch|remove_web_watch|_ensure_watch_applicator|_persisted_watch_records|_set_live_watch_status|_watch_payload_from_record)"),
 ("accounts-settings", r"(pikpak_account|web_settings|_archive_settings|_set_archive_settings|_invalidate_pikpak_archive_client|_read_rclone_remotes|_setup_coordinator|_normalize_account_remote|_next_pikpak_remote_name|start_web_ui|recover_web_runtime)"),
 ("setup-wizard", r"^(is_setup_ready|get_setup_status|save_setup_api_credentials|configure_setup_rclone|skip_setup_rclone|test_setup_rclone|save_setup_bot_token|skip_setup_bot_token)"),
 ("media-cleanup", r"(media|cleanup)"),
 ("archive-tools", r"archive_author|archive_from_system_log|_archive_author_ops"),
 ("diagnostics-export", r"(export_diagnostic_bundle|export_system_logs|list_system_logs|export_table|_export_channel_statistics_table|statistics)"),
 ("transfer-range-detect", r"transfer_range|history"),
 ("deferred-capture", r"deferred|discussion"),
 ("other", r".*"),
]
seen = {}
for g, pat in GROUPS:
    for m in met:
        if m.name in seen: continue
        if re.match(pat, m.name):
            seen[m.name] = g
print("\n=== method groups ===")
by = collections.defaultdict(list)
for m in met:
    by[seen.get(m.name, "other")].append(m)
for g in by:
    ms = sorted(by[g], key=lambda x: x.lineno)
    print(f"{g}: {len(ms)} methods, lines {ms[0].lineno}-{ms[-1].end_lineno}")
    print("   ", ", ".join(x.name for x in ms))
