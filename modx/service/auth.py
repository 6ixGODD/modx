from __future__ import annotations

import typing as t

from modx.logger import Logger
from modx.resources.api_key import APIKey
from modx.service import BaseService


@t.runtime_checkable
class IAuthService(t.Protocol):
    async def authenticate(self, api_key: str) -> bool: ...


class AuthService(BaseService):
    def __init__(self, logger: Logger, api_key: APIKey):
        super().__init__(logger)
        self.api_key = api_key

    async def authenticate(self, api_key: str) -> bool:
        return api_key in self.api_key
