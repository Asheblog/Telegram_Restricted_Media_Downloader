# coding=UTF-8
"""Transfer subpackage for TRMD."""
from module.transfer.context import TransferContext, TransferPorts  # noqa: F401
from module.transfer.engine import TransferEngine  # noqa: F401

__all__ = [
    'TransferContext',
    'TransferEngine',
    'TransferPorts',
    'WebTransferRunner',
]


def __getattr__(name: str):
    if name == 'WebTransferRunner':
        from module.transfer.runner import WebTransferRunner
        return WebTransferRunner
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
