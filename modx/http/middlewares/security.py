from __future__ import annotations

import typing as t

import starlette.types as types

from modx import constants
from modx import utils
from modx.config.middleware.security import SecurityConfig
from modx.context import Context
from modx.helpers.mixin import LoggingTagMixin
from modx.http.middlewares import BaseMiddleware
from modx.logger import Logger
from modx.utils import ansi as ansi_utils


class SecurityMiddleware(BaseMiddleware, LoggingTagMixin):
    """Middleware for adding security headers to RESTful API responses.

    This middleware applies appropriate security headers for API services.
    CORS functionality is not included as it's handled by a separate
    middleware.
    """
    __logging_tag__ = 'modx.http.middlewares.security'

    def __init__(self, app: types.ASGIApp, *, logger: Logger, context: Context,
                 config: SecurityConfig):
        BaseMiddleware.__init__(self, app)
        LoggingTagMixin.__init__(self, logger)

        self.context = context
        self.config = config
        self.enforce_https = self.config.enforce_https
        self.hsts_max_age = self.config.hsts_max_age
        self.add_content_type_options = self.config.add_content_type_options
        self.cache_control = self.config.cache_control
        self.add_request_id = self.config.add_request_id
        self.add_api_version = self.config.add_api_version
        self.api_version = self.config.api_version

    def _get_security_headers(self):
        headers = {}

        # X-Content-Type-Options
        if self.add_content_type_options:
            headers[b"X-Content-Type-Options"] = b"nosniff"

        # Cache-Control
        if self.cache_control:
            headers[b"Cache-Control"] = self.cache_control.encode("utf-8")
            headers[b"Pragma"] = b"no-cache"
            headers[b"Expires"] = b"0"

        # API Version
        if self.add_api_version:
            headers[b"X-API-Version"] = self.api_version.encode("utf-8")

        # HSTS (only if HTTPS is enforced)
        if self.enforce_https:
            hsts_value = f"max-age={self.hsts_max_age}"
            headers[b"Strict-Transport-Security"] = hsts_value.encode("utf-8")

        return headers

    def _log_headers(self, response_headers: t.List[t.Tuple[bytes, bytes]]) -> None:
        headers_dict = {
            k.decode("utf-8"): v.decode("utf-8")
            for k, v in response_headers
            if k.startswith(b"X-") or k in (b"Cache-Control", b"Strict-Transport-Security")
        }

        if headers_dict:
            header_str = ansi_utils.ANSIFormatter.format(
                f"Applied API security headers: "
                f"{', '.join(headers_dict.keys())}", ansi_utils.ANSIFormatter.FG.GREEN)
            self.logger.debug(header_str)

    async def __call__(self, scope: types.Scope, receive: types.Receive, send: types.Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        security_headers = self._get_security_headers()

        # Generate request ID if needed
        if self.add_request_id:
            del self.context[constants.ContextKey.REQUEST_ID]
            request_id = utils.gen_id(pref=constants.IDPrefix.REQUEST)
            security_headers[constants.HeaderKey.REQUEST_ID.encode('utf-8')] = request_id.encode(
                "utf-8")
            self.context[constants.ContextKey.REQUEST_ID] = request_id

        async def send_wrapper(message: types.Message) -> None:
            if message["type"] == "http.response.start":
                # Add security headers to the response
                message.setdefault("headers", [])

                # Add all security headers
                for name, value in security_headers.items():
                    # Only add if not already present (allow app to override)
                    if not any(h[0].lower() == name.lower() for h in message["headers"]):
                        message["headers"].append((name, value))

                # Log applied headers at debug level
                self._log_headers(message["headers"])

            await send(message)

        await self.app(scope, receive, send_wrapper)
