from __future__ import annotations

import httpx

from modx.config import ModXConfig
from modx.helpers.mixin import AsyncContextMixin


class HTTPClient(AsyncContextMixin):

    def __init__(self, config: ModXConfig) -> None:
        self.config = config.http_client
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout,
            max_redirects=self.config.max_redirects,
            http1=not self.config.http2,
            http2=self.config.http2,
            trust_env=self.config.trust_env,
            limits=httpx.Limits(max_connections=self.config.max_connections,
                                max_keepalive_connections=self.config.max_keepalive_connections),
            headers={'User-Agent': self.config.user_agent})

    async def init(self) -> None:
        pass

    async def close(self) -> None:
        await self.client.aclose()
