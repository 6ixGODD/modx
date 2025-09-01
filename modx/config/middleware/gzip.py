from __future__ import annotations

import pydantic as pydt


class GzipConfig(pydt.BaseModel):
    enabled: bool = True
    minimum_size: int = 1024
    compresslevel: int = 9
