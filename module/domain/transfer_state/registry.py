# coding=UTF-8
"""Transfer registry domain state."""
import asyncio
from typing import Optional, Callable


class TransferRegistry:
    def __init__(self):
        self.link_info: dict = {}
        self.complete_link: set = set()
        self.tasks: set = set()
        self.task_counter: int = 0
        self.notify: Optional[Callable] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.directory_name: str = ""

    def reset(self):
        self.link_info.clear()
        self.complete_link.clear()
        self.tasks.clear()
        self.task_counter = 0
        self.notify = None
        self.loop = None
        self.directory_name = ""


transfer_registry = TransferRegistry()
