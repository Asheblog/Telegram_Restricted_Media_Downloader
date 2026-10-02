import ast, os, re, collections
ROOT = r"E:\codebase\tgbot"
ch = open(os.path.join(ROOT, "module/adapters/bot/callback_handler.py"), encoding="utf-8").read()
members = {
 "bot","cd","download_upload_window","listen_download_chat","listen_forward_chat",
 "web_watch_handler_clients","web_pending_watches","adding_keywords","download_chat_filter",
 "last_message","last_client",
 "help","table","get_download_link_from_bot","build_download_upload_meta",
 "download_watch_id","forward_watch_id","add_keyword_mode_handler","download_chat",
}
cnt = {}
for m in sorted(members):
    n = len(re.findall(r"self\._host\.\s*" + m + r"\b", ch)) + len(re.findall(r"self\._downloader\.\s*" + m + r"\b", ch))
    n += len(re.findall(r"\bhost\.\s*" + m + r"\b", ch))
    cnt[m] = n
print("IBotCallbackHost member usage via self._host / self._downloader / host:")
for m, n in sorted(cnt.items(), key=lambda kv: -kv[1]):
    print(f"  {m:32s} {n}")
unused = [m for m, n in cnt.items() if n == 0]
print(f"\nused: {len([m for m,n in cnt.items() if n])}/19   UNUSED: {len(unused)} -> {unused}")
print(f"total access sites: {sum(cnt.values())}")
# accesses via host that are NOT in the protocol
allh = collections.Counter(re.findall(r"self\._host\.\s*([A-Za-z_][A-Za-z0-9_]*)", ch))
allh += collections.Counter(re.findall(r"self\._downloader\.\s*([A-Za-z_][A-Za-z0-9_]*)", ch))
print(f"\ndistinct members actually reached: {len(allh)}")
print(f"reached but NOT declared in IBotCallbackHost: {sorted(set(allh) - members)}")
