from __future__ import annotations

import typing as t

import pydantic as pydt


class LoggingConfig(pydt.BaseModel):
    colorize: bool = True
    """Whether to apply ANSI color formatting. Defaults to True."""

    request_id_header: str = "X-Request-ID"
    """Header name for request ID. Defaults to 'X-Request-ID'."""

    trace_id_header: str = "X-Trace-ID"
    """Header name for trace ID. Defaults to 'X-Trace-ID'."""

    span_id_header: str = "X-Span-ID"
    """Header name for span ID. Defaults to 'X-Span-ID'."""

    parent_span_id_header: str = "X-Parent-ID"
    """Header name for parent span ID. Defaults to 'X-Parent-ID'."""

    log_headers: bool = False
    """Whether to log request/response headers. Defaults to False."""

    log_query_string: bool = True
    """Whether to log query string. Defaults to True."""

    exclude_paths: t.Set[str] | None = None
    """Paths to exclude from logging. Defaults to None."""
