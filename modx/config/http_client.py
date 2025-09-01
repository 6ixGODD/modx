from __future__ import annotations

import pydantic as pydt


class HttpClientConfig(pydt.BaseModel):
    timeout: float = 10.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
    max_redirects: int = 10
    http2: bool = True
    trust_env: bool = True
    user_agent: str = "ModX-Client/1.0"
