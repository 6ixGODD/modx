from __future__ import annotations

import pydantic as pydt


class ChatbotConfig(pydt.BaseModel):
    cache_ttl: int = 60 * 60 * 60  # 60 minutes
