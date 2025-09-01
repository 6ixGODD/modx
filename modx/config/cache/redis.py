from __future__ import annotations

import secrets
import typing as t

import pydantic as pydt


class RedisConfig(pydt.BaseModel):
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: str | None = None
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    max_connections: int = 10
    health_check_interval: int = 30
    ssl: bool = False
    ssl_cert_reqs: t.Literal['required', 'optional'] = "required"
    secure_serialization: bool = False
    secret_key: str = secrets.token_urlsafe(32)
