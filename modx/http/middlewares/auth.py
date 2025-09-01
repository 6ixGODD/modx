from __future__ import annotations

import starlette.types as types

from modx.context import Context
from modx.helpers.mixin import LoggingTagMixin
from modx.http.middlewares import BaseMiddleware
from modx.interface.auth import IAuthInterface
from modx.logger import Logger


class AuthMiddleware(BaseMiddleware, LoggingTagMixin):
    __logging_tag__ = 'modx.http.middlewares.auth'

    def __init__(
        self,
        app: types.ASGIApp,
        auth_interface: IAuthInterface,
        context: Context,
        logger: Logger,
    ):
        BaseMiddleware.__init__(self, app)
        LoggingTagMixin.__init__(self, logger)

        self.auth_interface = auth_interface
        self.context = context
