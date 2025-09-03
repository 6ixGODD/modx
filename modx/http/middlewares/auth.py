from __future__ import annotations

import fnmatch
import re

import starlette.types as types

from modx import constants, exceptions
from modx.config.middleware.auth import AuthConfig
from modx.context import Context
from modx.helpers.mixin import LoggingTagMixin
from modx.http.middlewares import BaseMiddleware
from modx.interface.auth import IAuthInterface
from modx.interface.dtos import ErrorResponse
from modx.logger import Logger


def extract_route(path: str) -> str:
    match = re.search(r'(?:^/)?(?:api/)?v\d+(?:\.\d+)?(/.*)', path)
    if match:
        return match.group(1)
    if path.startswith('/api/'):
        return path[4:]
    return path


class AuthMiddleware(BaseMiddleware, LoggingTagMixin):
    __logging_tag__ = 'modx.http.middlewares.auth'

    def __init__(
        self,
        app: types.ASGIApp,
        auth_interface: IAuthInterface,
        context: Context,
        config: AuthConfig,
        logger: Logger,
    ):
        BaseMiddleware.__init__(self, app)
        LoggingTagMixin.__init__(self, logger)

        self.auth_interface = auth_interface
        self.context = context
        self.config = config
        self.unprotected_routes = (set(config.unprotected_routes) |
                                   {'/ping', '/metrics'})

    async def __call__(
        self,
        scope: types.Scope,
        receive: types.Receive,
        send: types.Send
    ) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        route = extract_route(path)
        if any(
            fnmatch.fnmatch(route, pattern)
            for pattern in self.unprotected_routes
        ):
            await self.app(scope, receive, send)
            return

        headers = scope.get('headers', [])
        auth_header = None
        for key, value in headers:
            if key.decode().lower() == "authorization":
                auth_header = value.decode()
                break

        async def send_unauthorized(
            message: str = "Unauthorized",
            business_code: constants.BusinessCode =
            constants.BusinessCode.UNAUTHORIZED,
            status_code: int = 401
        ):
            await send(
                {
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": [(b"content-type", b"application/json")]
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": ErrorResponse(
                        success=False,
                        code=business_code,
                        data=exceptions.ExceptionDetails(message=message)
                    ).model_dump_json().encode(),
                }
            )

        if not auth_header:
            self.logger.debug("Missing Authorization header", path=path)
            await send_unauthorized("Authentication required")
            return

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            self.logger.debug(
                "Invalid Authorization header format", path=path
            )
            await send_unauthorized("Invalid authorization header format")
            return
        token = parts[1]
        try:
            await self.auth_interface.authenticate(token)
        except exceptions.UnauthorizedError as e:
            self.logger.debug(f"Authentication failed: {e.msg}", path=path)
            await send_unauthorized(e.msg)
            return
        except exceptions.ForbiddenError as e:
            self.logger.debug(f"Access forbidden: {e.msg}", path=path)
            await send_unauthorized(
                e.msg, constants.BusinessCode.FORBIDDEN, status_code=403
            )
            return
        return await self.app(scope, receive, send)
