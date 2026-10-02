import glob, os, re
rows=[]; tot_obj=tot_host=0
for p in sorted(glob.glob("unit_tests/*_case.py")):
    s=open(p,encoding="utf-8").read()
    obj=len(re.findall(r"object\.__new__\(", s))
    host=len(re.findall(r"TelegramRestrictedMediaDownloader\.__new__\(", s))
    alln=len(re.findall(r"\.__new__\(", s))
    if alln:
        rows.append((os.path.basename(p), obj, host, alln)); tot_obj+=obj; tot_host+=host
rows.sort(key=lambda r:-r[3])
print("file".ljust(54), "object", "host", "all")
for r in rows[:16]:
    print(r[0].ljust(54), str(r[1]).rjust(6), str(r[2]).rjust(5), str(r[3]).rjust(5))
print("TOTAL".ljust(54), str(tot_obj).rjust(6), str(tot_host).rjust(5), str(sum(r[3] for r in rows)).rjust(5))
print("files with __new__:", len(rows))
