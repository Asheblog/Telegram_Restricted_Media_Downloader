# coding=UTF-8
"""受控实验：把 WebUiTestConnection 的重放与 deferred-close 都拿掉（按行号精确替换），
看 transfer_store_webui_case 是否仍全绿。实验后自动还原。

结论用于决定这两处机制该删（已成死代码）还是该留（仍在兜底）。
"""
import pathlib
import subprocess
import sys

REPO = pathlib.Path(r"E:\codebase\tgbot")
TARGET = REPO / "unit_tests" / "transfer_store_webui_case.py"
BACKUP = REPO / "tmp" / "tswc_backup.py"

original = BACKUP.read_text(encoding="utf-8")
lines = original.splitlines(keepends=True)

# 1-based 行号（见 read 输出）
# 86-103: request()（含 deferred-close 分支）
# 105-127: getresponse()（含重放）
new_request = '''    def request(self, method, url, body=None, headers=None, *, encode_chunked=False):
        headers = {} if headers is None else headers
        super().request(
            method, url, body=body, headers=headers, encode_chunked=encode_chunked
        )

'''
new_getresponse = '''    def getresponse(self):
        return super().getresponse()

'''
# 替换 105..127 与 86..103（先替换后面的，避免行号漂移）
head = lines[:104]          # 1..104
mid = lines[85:104]         # 86..104 -> 待替换区(86..103)+空行
tail = lines[127:]          # 128..
new_text = "".join(head[:-1]) + "\n" + new_getresponse + "\n"
# 重新组装：1..85 + new_request + new_getresponse + 128..
assembled = "".join(lines[:85]) + new_request + new_getresponse + "".join(lines[127:])

TARGET.write_text(assembled, encoding="utf-8")
print("experiment version written")
try:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "unit_tests/transfer_store_webui_case.py",
         "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=str(REPO), capture_output=True,
    )
    out = proc.stdout.decode("utf-8", "replace")
    print("EXIT =", proc.returncode)
    for line in out.splitlines():
        if "passed" in line or "failed" in line or line.startswith("FAILED"):
            print(" ", line.strip())
finally:
    TARGET.write_text(original, encoding="utf-8")
    print("restored:", TARGET.read_text(encoding="utf-8") == original)
