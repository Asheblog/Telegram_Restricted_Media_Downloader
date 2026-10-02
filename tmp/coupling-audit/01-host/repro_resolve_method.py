# coding=UTF-8
r"""Repro: WebTransferRunner._resolve_method (module/transfer/runner.py:80-86).

Claim: for any ordinary instance method,
    `getattr(host, name) is not getattr(type(host), name)`  ==  True
so line 84 always returns the host's method and lines 85-86
(`return getattr(self, name)` -> the runner's own duplicate implementation)
are unreachable whenever the host has the attribute at all.

Read-only. Run:
    .\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\repro_resolve_method.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, r"E:\codebase\tgbot")

from module.transfer.runner import WebTransferRunner  # noqa: E402


class Host:
    def should_continue_web_transfer_task(self, task_id):
        return 'HOST-IMPLEMENTATION'

    @staticmethod
    def static_marker():
        return 'HOST-STATIC'


class BareHost:
    """Has none of the 15 WebTransferHost members; WebOperationsMixin is absent."""
    transfer_store = None


def main() -> None:
    h = Host()
    print('[1] bound method identity')
    print('    h.m is h.m                    :', h.should_continue_web_transfer_task is h.should_continue_web_transfer_task)
    print('    h.m is type(h).m              :', h.should_continue_web_transfer_task is Host.should_continue_web_transfer_task)
    print('    => runner.py:84 condition "is not" is', h.should_continue_web_transfer_task is not Host.should_continue_web_transfer_task)

    r = WebTransferRunner(h)
    print('[2] _resolve_method picks host impl, not runner-local impl')
    print('    resolves to                   :', r._resolve_method('should_continue_web_transfer_task')(1))

    print('[3] host whose class lacks the attr -> AttributeError, local fallback NOT used')
    r2 = WebTransferRunner(BareHost())
    try:
        r2._resolve_method('should_continue_web_transfer_task')
        print('    resolved (unexpected)')
    except AttributeError as exc:
        print('    AttributeError                :', exc)
    print('    runner DOES define its own    :', WebTransferRunner.should_continue_web_transfer_task.__qualname__)
    print('    runner local impl result      :', r2.should_continue_web_transfer_task(1))

    print('[4] staticmethod is the only shape where the branch can take lines 85-86')
    print('    h.static_marker is type(h).static_marker :', h.static_marker is Host.static_marker)


if __name__ == '__main__':
    main()
