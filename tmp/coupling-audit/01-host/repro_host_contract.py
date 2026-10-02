# coding=UTF-8
r"""Executable proofs for A1 findings (read-only, no repo writes).

Run:  .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\repro_host_contract.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, r"E:\codebase\tgbot")

from module.downloader import TelegramRestrictedMediaDownloader as Facade  # noqa: E402
from module.transfer.live_transfer import LiveTransferService  # noqa: E402
from module.transfer.runner import WebTransferHost  # noqa: E402


def main() -> None:
    print('== [A] @runtime_checkable WebTransferHost accepts a never-wired host ==')
    bare = object.__new__(Facade)  # __init__ never ran
    print('    isinstance(bare, WebTransferHost) :', isinstance(bare, WebTransferHost))
    missing = [a for a in ('app', 'gc', 'loop', 'transfer_store', 'uploader') if not hasattr(bare, a)]
    print('    data attrs still missing          :', missing)
    print('    -> the Protocol checks NAME PRESENCE on the class, not signatures or state.')

    print('\n== [B] LiveTransferService.__getattr__ (live_transfer.py:91-92) ==')
    class FakeHost:
        gc = 'HOST-GC'
        listen_download_chat = {'x': 1}

        def _log_system_chain(self, **kw):
            return 'HOST-LOG'

        def create_download_task(self, **kw):
            return 'HOST-CREATE'

    svc = LiveTransferService(FakeHost())
    print('    svc.gc                            :', svc.gc)
    print('    svc.create_download_task          :', svc.create_download_task())
    print("    hasattr(svc,'transfer_store')     :", hasattr(svc, 'transfer_store'))
    print('    svc.listen_download_chat          :', svc.listen_download_chat)
    print('    class own member called "gc"?     :', 'gc' in LiveTransferService.__dict__)

    print('\n== [C] a typo inside LiveTransferService resolves to the HOST ==')
    class HostWithTypo:
        gcc = 'HOST-gcc'  # the typo'd name only exists on the host

    svc2 = LiveTransferService(HostWithTypo())
    print('    svc2.gcc (not defined by service) :', svc2.gcc)
    try:
        svc2.gc
    except AttributeError as exc:
        print('    svc2.gc (absent on both)          :', exc)
        print('    -> the AttributeError names the HOST class, not LiveTransferService.')

    print('\n== [D] signature erasure: 17 shims in composition_root.py:320-369 ==')
    import inspect
    from module.composition_root import TrmdCompositionRoot
    from module.transfer.progress import TransferProgressTracker
    for name in ('record_transfer_download_success', 'transfer_percent'):
        shim = getattr(TrmdCompositionRoot, name)
        real = getattr(TransferProgressTracker, name)
        print(f'    {name:34s} shim{inspect.signature(shim)}')
        print(f'    {"":34s} real{inspect.signature(real)}')


if __name__ == '__main__':
    main()
