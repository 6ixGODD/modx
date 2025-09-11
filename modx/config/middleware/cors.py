from __future__ import annotations

import typing as t

import pydantic as pydt


class CorsConfig(pydt.BaseModel):
    enabled: bool = True
    allow_origins: t.List[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: t.List[t.Literal[
        "*",
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "OPTIONS",
        "HEAD"
    ]] = ["*"]
    allow_headers: t.List[str] = ["*"]
    allow_origin_regex: str | None = None
    expose_headers: t.List[str] = []
    max_age: int = 600
