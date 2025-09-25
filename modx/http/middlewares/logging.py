from __future__ import annotations

import http
import time
import traceback
import typing as t

import starlette.types as types

from modx import constants
from modx import exceptions
from modx.config.middleware.logging import LoggingConfig
from modx.context import Context
from modx.helpers.mixin import LoggingTagMixin
from modx.http.middlewares import BaseMiddleware
from modx.logger import Logger
from modx.utils import ansi as ansi_utils


class LoggingMiddleware(BaseMiddleware, LoggingTagMixin):
    """Middleware for logging HTTP requests and responses with colorized output.

    This middleware logs detailed information about incoming requests and their
    corresponding responses with ANSI color formatting for better visibility
    in console.
    """
    __logging_tag__ = 'modx.http.middlewares.logging'

    # Status code color mapping
    STATUS_COLORS: t.ClassVar[t.Dict[int, ansi_utils.ANSIFormatter.FG]] = {
        1: ansi_utils.ANSIFormatter.FG.BLUE,  # 1xx - Informational
        2: ansi_utils.ANSIFormatter.FG.GREEN,  # 2xx - Success
        3: ansi_utils.ANSIFormatter.FG.CYAN,  # 3xx - Redirection
        4: ansi_utils.ANSIFormatter.FG.YELLOW,  # 4xx - Client Error
        5: ansi_utils.ANSIFormatter.FG.RED,  # 5xx - Server Error
    }

    # HTTP Method color mapping
    METHOD_COLORS: t.ClassVar[t.Dict[str, ansi_utils.ANSIFormatter.FG]] = {
        'GET': ansi_utils.ANSIFormatter.FG.GREEN,
        'POST': ansi_utils.ANSIFormatter.FG.BLUE,
        'PUT': ansi_utils.ANSIFormatter.FG.YELLOW,
        'PATCH': ansi_utils.ANSIFormatter.FG.MAGENTA,
        'DELETE': ansi_utils.ANSIFormatter.FG.RED,
        'OPTIONS': ansi_utils.ANSIFormatter.FG.CYAN,
        'HEAD': ansi_utils.ANSIFormatter.FG.BRIGHT_GREEN,
    }

    def __init__(self, app: types.ASGIApp, logger: Logger, context: Context, config: LoggingConfig):
        BaseMiddleware.__init__(self, app)
        LoggingTagMixin.__init__(self, logger)

        self.config = config
        self.colorize = self.config.colorize
        self.context = context
        self.trace_id_header = self.config.trace_id_header.lower().encode()
        self.span_id_header = self.config.span_id_header.lower().encode()
        self.parent_span_id_header = (self.config.parent_span_id_header.lower().encode())
        self.exclude_paths = self.config.exclude_paths or set()

        ansi_utils.ANSIFormatter.enable(self.config.colorize)

    @staticmethod
    def _extract_header_value(headers: t.List[t.Tuple[bytes, bytes]],
                              header_name: bytes) -> str | None:
        for name, value in headers:
            if name.lower() == header_name:
                return value.decode('utf-8', 'replace')
        return None

    async def __call__(self, scope: types.Scope, receive: types.Receive, send: types.Send) -> None:
        if scope["type"] != "http" or scope['path'] in self.exclude_paths:
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        headers = scope.get('headers', [])

        # Extract identifiers
        if constants.ContextKey.REQUEST_ID in self.context:
            request_id = self.context[constants.ContextKey.REQUEST_ID]
        else:
            request_id = "unknown"
        trace_id = self._extract_header_value(headers, self.trace_id_header)
        span_id = self._extract_header_value(headers, self.span_id_header)
        parent_span_id = self._extract_header_value(headers, self.parent_span_id_header)

        # Format request info inline
        method = scope['method']
        path = scope['path']
        client = f"{scope['client'][0]}:{scope['client'][1]}" if scope.get('client') else "Unknown"

        # Color mappings
        method_colors = {
            "GET": ansi_utils.ANSIFormatter.FG.GREEN,
            "POST": ansi_utils.ANSIFormatter.FG.BLUE,
            "PUT": ansi_utils.ANSIFormatter.FG.YELLOW,
            "PATCH": ansi_utils.ANSIFormatter.FG.MAGENTA,
            "DELETE": ansi_utils.ANSIFormatter.FG.RED,
            "OPTIONS": ansi_utils.ANSIFormatter.FG.CYAN,
            "HEAD": ansi_utils.ANSIFormatter.FG.BRIGHT_GREEN
        }

        # Format components
        method_colored = ansi_utils.ANSIFormatter.format(
            method, method_colors.get(method, ansi_utils.ANSIFormatter.FG.WHITE),
            ansi_utils.ANSIFormatter.STYLE.BOLD)
        path_colored = ansi_utils.ANSIFormatter.format(path, ansi_utils.ANSIFormatter.FG.WHITE,
                                                       ansi_utils.ANSIFormatter.STYLE.BOLD)
        client_colored = ansi_utils.ANSIFormatter.format(client, ansi_utils.ANSIFormatter.FG.GRAY)

        # Trace info
        trace_parts = []
        if trace_id:
            trace_parts.append(f"trace:{trace_id}")
        if span_id:
            trace_parts.append(f"span:{span_id}")
        if parent_span_id:
            trace_parts.append(f"parent:{parent_span_id}")
        trace_info = ansi_utils.ANSIFormatter.format(
            f" [{' | '.join(trace_parts)}]",
            ansi_utils.ANSIFormatter.FG.CYAN) if trace_parts else ""

        # Log request
        request_log = (f"[{request_id}] → {method_colored} "
                       f"{path_colored} from "
                       f"{client_colored}{trace_info}")

        log_ctx = {
            "method": method,
            "path": path,
            "client": client,
            "request_id": request_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "user_agent": self._extract_header_value(headers, b'user-agent')
        }
        if trace_id:
            log_ctx["trace_id"] = trace_id
        if span_id:
            log_ctx["span_id"] = span_id
        if parent_span_id:
            log_ctx["parent_span_id"] = parent_span_id

        if self.config.log_query_string and scope.get('query_string'):
            log_ctx["query_string"] = scope['query_string'].decode('utf-8', 'replace')
        if self.config.log_headers:
            log_ctx["headers"] = {
                k.decode('utf-8', 'replace'): v.decode('utf-8', 'replace') for k, v in headers
            }

        self.logger.with_context(**log_ctx).info(request_log)

        # Response wrapper
        async def send_wrapper(message: t.MutableMapping[str, t.Any]) -> None:
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration_ms = round((time.time() - start_time) * 1000, 2)

                # Status color
                status_family = status_code // 100
                status_colors = {
                    1: ansi_utils.ANSIFormatter.FG.BLUE,
                    2: ansi_utils.ANSIFormatter.FG.GREEN,
                    3: ansi_utils.ANSIFormatter.FG.CYAN,
                    4: ansi_utils.ANSIFormatter.FG.YELLOW,
                    5: ansi_utils.ANSIFormatter.FG.RED
                }

                try:
                    status_text = (f"{status_code} "
                                   f"{http.HTTPStatus(status_code).phrase}")
                except ValueError:
                    status_text = str(status_code)

                status_colored = ansi_utils.ANSIFormatter.format(
                    status_text, status_colors.get(status_family,
                                                   ansi_utils.ANSIFormatter.FG.WHITE),
                    ansi_utils.ANSIFormatter.STYLE.BOLD if status_family >= 4 else None)

                # Duration color
                if duration_ms < 100:
                    duration_colored = ansi_utils.ANSIFormatter.format(
                        f"{duration_ms}ms", ansi_utils.ANSIFormatter.FG.GREEN)
                elif duration_ms < 500:
                    duration_colored = ansi_utils.ANSIFormatter.format(
                        f"{duration_ms}ms", ansi_utils.ANSIFormatter.FG.YELLOW)
                else:
                    duration_colored = ansi_utils.ANSIFormatter.format(
                        f"{duration_ms}ms", ansi_utils.ANSIFormatter.FG.RED,
                        ansi_utils.ANSIFormatter.STYLE.BOLD)

                response_log = (f"[{request_id}] ← {status_colored} in "
                                f"{duration_colored}{trace_info}")

                response_ctx = {
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "request_id": request_id
                }
                if trace_id:
                    response_ctx["trace_id"] = trace_id
                if span_id:
                    response_ctx["span_id"] = span_id
                if parent_span_id:
                    response_ctx["parent_span_id"] = parent_span_id

                self.logger.with_context(**response_ctx).info(response_log)

            await send(message)

        # Execute with error handling
        try:
            with self.logger.catch("Failed to process request",
                                   excl_exc=exceptions.RuntimeException):
                await self.app(scope, receive, send_wrapper)
        except Exception as e:
            error_duration = round((time.time() - start_time) * 1000, 2)
            error_msg = (f"[{request_id}] "
                         f"❌ Exception after "
                         f"{error_duration}ms: "
                         f"{str(e)}{trace_info}")
            error_ctx = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "duration_ms": error_duration,
                "request_id": request_id
            }
            if trace_id:
                error_ctx["trace_id"] = trace_id
            if span_id:
                error_ctx["span_id"] = span_id

            self.logger.with_context(**error_ctx).error(
                ansi_utils.ANSIFormatter.format(error_msg, ansi_utils.ANSIFormatter.FG.RED,
                                                ansi_utils.ANSIFormatter.STYLE.BOLD))
            raise
