from __future__ import annotations

import pydantic as pydt

from modx import __title__
from modx.config.cache.redis import RedisConfig


class CacheConfig(pydt.BaseModel):
    split: str = ':'
    pref: str = f'{__title__}{split}'
    default_ttl: int = 3600  # seconds
    negative_ttl: int = 60  # avoids cache penetration, seconds
    redis: RedisConfig | None = None
