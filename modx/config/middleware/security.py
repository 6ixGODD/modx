from __future__ import annotations

import pydantic as pydt

from modx import __version__


class SecurityConfig(pydt.BaseModel):
    enabled: bool = True
    """Whether to enable the security middleware. Defaults to True."""

    enforce_https: bool = False
    """Whether to enforce HTTPS via HSTS header. Defaults to False."""

    hsts_max_age: int = 31536000  # 1 year
    """Max age for HSTS header in seconds. Defaults to 31536000 (1 year)."""

    add_content_type_options: bool = True
    """Whether to add X-Content-Type-Options header. Defaults to True."""

    cache_control: str = "no-cache, no-store, must-revalidate"
    """Cache-Control header value. Defaults to "no-cache, no-store, 
    must-revalidate"."""

    add_request_id: bool = True
    """Whether to generate and add X-Request-ID header. Defaults to True."""

    add_api_version: bool = True
    """Whether to add X-API-Version header. Defaults to False."""

    api_version: str = __version__
    """API version string to use if enabled. Defaults to __version__."""
