# coding=UTF-8
from module import console, log as _module_log


class RichDiagnosticAdapter:
    def __init__(self, console=None, log=None):
        self._console = console
        self._log = log

    def info(self, message, *args, **kwargs):
        if self._log:
            self._log.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        if self._log:
            self._log.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        if self._log:
            self._log.error(message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        if self._log:
            self._log.debug(message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        if self._log:
            self._log.exception(message, *args, **kwargs)

    def console_log(self, *args, **kwargs):
        if self._console:
            self._console.log(*args, **kwargs)

    def console_print(self, *args, **kwargs):
        if self._console:
            self._console.print(*args, **kwargs)


default_diagnostic = RichDiagnosticAdapter(console, _module_log)
