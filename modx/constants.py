from __future__ import annotations

import enum
import http
import typing as t


class BusinessCode(enum.StrEnum):
    SUCCESS = "SUCCESS"

    # General Errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"

    # Auth & Permission
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # Params & Validation
    INVALID_PARAMS = "INVALID_PARAMS"
    MISSING_PARAMS = "MISSING_PARAMS"
    VALIDATION_FAILED = "VALIDATION_FAILED"

    # Resource & Data
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"

    # Quota & Limits
    RATE_LIMITED = "RATE_LIMITED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

    # Business
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    STATE_ERROR = "STATE_ERROR"

    @classmethod
    def from_http_status(cls, status_code: int) -> t.Self:
        return (http.HTTPStatus(status_code).phrase.upper().replace(' ', '_').replace('.', ''))


class IDPrefix(enum.StrEnum):
    REQUEST = "req-"
    USER = "uid-"
    TRACE = "trace-"
    SPAN = "span-"
    CHATCMPL = "chatcmpl-"


class ContextKey(enum.StrEnum):
    USER_ID = "user_id"
    REQUEST_ID = "request_id"
    TRACE_ID = "trace_id"
    SPAN_ID = "span_id"
    PARENT_SPAN_ID = "parent_span_id"


class HeaderKey(enum.StrEnum):
    REQUEST_ID = "X-Request-ID"


DEFAULT_PROMPT = "You are a helpful assistant."
