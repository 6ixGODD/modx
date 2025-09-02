from __future__ import annotations

import pydantic as pydt

from modx.config.middleware.auth import AuthConfig
from modx.config.middleware.cors import CorsConfig
from modx.config.middleware.gzip import GzipConfig
from modx.config.middleware.logging import LoggingConfig
from modx.config.middleware.security import SecurityConfig
from modx.config.middleware.trace import TraceConfig


class MiddlewareConfig(pydt.BaseModel):
    auth: AuthConfig = AuthConfig()
    logging: LoggingConfig = LoggingConfig()
    security: SecurityConfig = SecurityConfig()
    trace: TraceConfig = TraceConfig()
    cors: CorsConfig = CorsConfig()
    gzip: GzipConfig = GzipConfig()
