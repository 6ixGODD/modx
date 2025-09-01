from __future__ import annotations

import pydantic as pydt


class TraceConfig(pydt.BaseModel):
    enabled: bool = False
    """Whether tracing middleware is enabled. Defaults to False."""

    trace_id_header: str = "X-Trace-ID"
    """Header name for trace ID. Defaults to "X-Trace-ID"."""

    span_id_header: str = "X-Span-ID"
    """Header name for span ID. Defaults to "X-Span-ID"."""

    parent_span_id_header: str = "X-Parent-ID"
    """Header name for parent span ID. Defaults to "X-Parent-ID"."""

    log_trace_info: bool = True
    """Whether to log trace information. Defaults to True."""
