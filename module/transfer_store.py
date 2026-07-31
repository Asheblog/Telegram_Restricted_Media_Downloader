# coding=UTF-8
"""Compatibility shim — implementation in module.persistence.transfer_store. Deprecated: import from module.persistence.transfer_store instead."""
import datetime  # noqa: F401 — re-export for tests that patch module.transfer_store.datetime
from module.persistence.transfer_store import *  # noqa: F401,F403
