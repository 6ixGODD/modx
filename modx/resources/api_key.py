from __future__ import annotations

import typing as t

from modx.config import ModXConfig
from modx.logger import Logger
from modx.resources import WatchedResource


class APIKey(WatchedResource[t.List[str]], t.Sequence[str]):
    __logging_tag__ = 'modx.resources.apikey'

    def __init__(self, config: ModXConfig, logger: Logger):
        self.config = config
        WatchedResource.__init__(self, fpath=config.keys_file, logger=logger)

    def _parse(self) -> t.List[str]:
        content = self.fpath.read_text(encoding='utf-8').strip()
        return [line.strip()
                for line in content.splitlines()
                if line.strip()]

    def __contains__(self, key: object, /) -> bool:
        if not isinstance(key, str):
            return False
        return key in (self.data or [])

    def __len__(self) -> int:
        return len(self.data or [])

    def __iter__(self) -> t.Iterator[str]:
        return iter(self.data) if self.data else iter([])

    def __getitem__(self, index: int) -> str:
        if self.data is None:
            raise IndexError("Index out of range")
        return self.data[index]

    @property
    def api_keys(self) -> t.List[str]:
        return list(self.data or [])
