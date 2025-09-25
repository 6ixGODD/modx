from __future__ import annotations

import typing as t

import pydantic as pydt

from modx import __title__
from modx import __version__


class PrometheusConfig(pydt.BaseModel):
    enabled: bool = True
    metrics_path: str = "/metrics"
    track_in_progress: bool = True
    buckets: t.Tuple[float, ...] | None = None
    exclude_paths: t.Set[str] | None = None
    custom_labels: t.Dict[str, str] | None = None
    enable_exemplars: bool = False
    app_name: str = __title__
    app_version: str = __version__
