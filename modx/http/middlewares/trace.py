from __future__ import annotations

import typing as t

import starlette.types as types

import modx.constants as const
import modx.utils as utils
import modx.utils.ansi as ansi_utils
from modx.config import ModXConfig
from modx.context import Context
from modx.helpers.mixin import LoggingTagMixin
from modx.http.middlewares import BaseMiddleware
from modx.logger import Logger


class TraceMiddleware(BaseMiddleware, LoggingTagMixin):
    """Middleware for adding distributed tracing headers to requests and
    responses.

    This middleware manages trace ID, span ID, and parent span ID for
    distributed tracing across services. It follows OpenTelemetry-like
    conventions for trace propagation.
    """
    __logging_tag__ = 'modx.http.middlewares.trace'

    def __init__(
        self,
        app: types.ASGIApp,
        logger: Logger,
        context: Context,  # [!] should be a singleton object
        config: ModXConfig,
    ):
        BaseMiddleware.__init__(self, app)
        LoggingTagMixin.__init__(self, logger)

        self.logger = logger
        self.context = context
        self.config = config.middleware.trace
        self.trace_id_header = self.config.trace_id_header
        self.span_id_header = self.config.span_id_header
        self.parent_span_id_header = self.config.parent_span_id_header
        self.log_trace_info = self.config.log_trace_info

    @staticmethod
    def _extract_header_value(
        headers: t.List[t.Tuple[bytes, bytes]],
        header_name: str
    ) -> t.Optional[str]:
        """Extract header value by name (case-insensitive)."""
        header_name_bytes = header_name.lower().encode()
        for name, value in headers:
            if name.lower() == header_name_bytes:
                return value.decode('utf-8', 'replace')
        return None

    def _get_trace_headers(self) -> t.Dict[bytes, bytes]:
        """Get current trace headers from context."""
        headers = {}

        trace_id = self.context.get(const.ContextKey.TRACE_ID)
        span_id = self.context.get(const.ContextKey.SPAN_ID)
        parent_span_id = self.context.get(const.ContextKey.PARENT_SPAN_ID)

        if trace_id:
            headers[self.trace_id_header.encode('utf-8')] = trace_id.encode(
                'utf-8'
            )
        if span_id:
            headers[self.span_id_header.encode('utf-8')] = span_id.encode(
                'utf-8'
            )
        if parent_span_id:
            headers[self.parent_span_id_header.encode(
                'utf-8'
            )] = parent_span_id.encode('utf-8')

        return headers

    def _process_tracing_headers(
        self,
        headers: t.List[t.Tuple[bytes, bytes]]
    ) -> t.Dict[str, t.Optional[str]]:
        """Process incoming tracing headers and generate new ones as needed."""
        # Extract existing headers
        incoming_trace_id = self._extract_header_value(
            headers,
            self.trace_id_header
        )
        incoming_span_id = self._extract_header_value(
            headers,
            self.span_id_header
        )

        # Determine trace ID (generate if root request)
        if incoming_trace_id:
            trace_id = incoming_trace_id
            is_root = False
        else:
            trace_id = utils.gen_id(pref=const.IDPrefix.TRACE)
            is_root = True

        # Determine parent span ID and new span ID
        if incoming_span_id:
            parent_span_id = incoming_span_id
            span_id = utils.gen_id(pref=const.IDPrefix.SPAN)
        else:
            parent_span_id = None
            span_id = utils.gen_id(pref=const.IDPrefix.SPAN)

        return {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "is_root": is_root
        }

    def _log_trace_info(self, trace_info: t.Dict[str, t.Any]) -> None:
        """Log trace information with appropriate formatting."""
        if not self.log_trace_info:
            return

        trace_type = "ROOT" if trace_info["is_root"] else "CHILD"
        trace_id = trace_info["trace_id"]
        span_id = trace_info["span_id"]
        parent_span_id = trace_info.get("parent_span_id")

        if trace_info["is_root"]:
            trace_msg = ansi_utils.ANSIFormatter.format(
                f"🌟 {trace_type} trace started: trace={trace_id}, "
                f"span={span_id}",
                ansi_utils.ANSIFormatter.FG.BLUE,
                ansi_utils.ANSIFormatter.STYLE.BOLD
            )
        else:
            trace_msg = ansi_utils.ANSIFormatter.format(
                f"🔗 {trace_type} trace continued: trace={trace_id}, "
                f"span={span_id}, parent={parent_span_id}",
                ansi_utils.ANSIFormatter.FG.CYAN
            )

        self.logger.with_context(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            is_root_trace=trace_info["is_root"]
        ).debug(trace_msg)

    async def __call__(
        self,
        scope: types.Scope,
        receive: types.Receive,
        send: types.Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = scope.get('headers', [])

        # Process tracing headers
        trace_info = self._process_tracing_headers(headers)

        # Store in context
        self.context[const.ContextKey.TRACE_ID] = trace_info["trace_id"]
        self.context[const.ContextKey.SPAN_ID] = trace_info["span_id"]
        if trace_info["parent_span_id"]:
            self.context[const.ContextKey.PARENT_SPAN_ID] = trace_info[
                "parent_span_id"]
        else:
            # Clear parent span ID if not present
            if const.ContextKey.PARENT_SPAN_ID in self.context:
                del self.context[const.ContextKey.PARENT_SPAN_ID]

        # Log trace information
        self._log_trace_info(trace_info)

        async def send_wrapper(message: t.MutableMapping[str, t.Any]) -> None:
            if message["type"] == "http.response.start":
                # Add tracing headers to the response
                message.setdefault("headers", [])

                trace_headers = self._get_trace_headers()

                # Add all tracing headers
                for name, value in trace_headers.items():
                    # Only add if not already present (allow app to override)
                    if not any(
                        h[0].lower() == name.lower()
                        for h in message["headers"]
                    ):
                        message["headers"].append((name, value))

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Clean up context after request
            if const.ContextKey.TRACE_ID in self.context:
                del self.context[const.ContextKey.TRACE_ID]
            if const.ContextKey.SPAN_ID in self.context:
                del self.context[const.ContextKey.SPAN_ID]
            if const.ContextKey.PARENT_SPAN_ID in self.context:
                del self.context[const.ContextKey.PARENT_SPAN_ID]
