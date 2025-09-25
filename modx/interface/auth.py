from __future__ import annotations

import typing as t

from modx import exceptions
from modx.interface import BaseInterface
from modx.logger import Logger
from modx.service.auth import IAuthService


@t.runtime_checkable
class IAuthInterface(t.Protocol):

    async def authenticate(self, api_key: str) -> None:
        ...


class AuthInterface(BaseInterface):

    def __init__(self, *, logger: Logger, auth_service: IAuthService):
        super().__init__(logger)
        self.auth_service = auth_service

    async def authenticate(self, api_key: str) -> None:
        if not await self.auth_service.authenticate(api_key):
            raise exceptions.UnauthorizedError("Invalid API key provided.")
