from __future__ import annotations

from modx.helpers.mixin import LoggingTagMixin
from modx.logger import Logger


class BaseInterface(LoggingTagMixin):
    __logging_tag__ = "modx.interface"

    def __init__(self, logger: Logger):
        LoggingTagMixin.__init__(self, logger)
