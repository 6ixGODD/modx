from __future__ import annotations

from modx.helpers.mixin import LoggingTagMixin
from modx.logger import Logger


class BaseService(LoggingTagMixin):
    __logging_tag__ = 'modx.service'

    def __init__(self, logger: Logger):
        LoggingTagMixin.__init__(self, logger)
