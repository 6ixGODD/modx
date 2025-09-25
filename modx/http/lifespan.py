from __future__ import annotations

import contextlib
import types
import typing as t

import fastapi

from modx.client.http import HTTPClient
from modx.config import ModXConfig
from modx.helpers.display import Display
from modx.helpers.mixin import LoggingTagMixin
from modx.logger import Logger


class Lifespan(contextlib.AbstractAsyncContextManager[None], LoggingTagMixin):
    __logging_tag__ = 'modx.http.lifespan'

    def __init__(self, logger: Logger, config: ModXConfig, http_client: HTTPClient):
        LoggingTagMixin.__init__(self, logger)
        self.config = config
        self.http_client = http_client
        self.display = Display(config)

    def __call__(self, app: fastapi.FastAPI) -> t.Self:
        return self

    async def __aenter__(self):
        self.logger.info('Starting up ModX...')
        await self.http_client.init()
        self.display.display_startup()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None,
                        traceback: types.TracebackType | None):
        self.logger.info('Shutting down ModX...')
        await self.http_client.close()
        self.display.display_shutdown(exc_type, exc_value, traceback)
