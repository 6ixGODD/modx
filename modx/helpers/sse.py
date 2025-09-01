from __future__ import annotations

import json
import typing as t

from modx.interface.dtos import BaseModel

ItemType: t.TypeAlias = t.Union[str, dict, BaseModel]


class SSEStream(t.AsyncIterable[str]):
    def __init__(
        self,
        stream: t.AsyncIterable[ItemType],
        *,
        event: str | None = None,
        end: str | None = '[DONE]',
        retry: int | None = None,
    ) -> None:
        self.source = stream
        self.event = event
        self.end = end
        self.retry = retry

    async def __aiter__(self) -> t.AsyncIterator[str]:
        if self.retry:
            yield f"retry: {self.retry}\n\n"

        async for item in self.source:
            yield self.format(item)

        if self.end:
            yield self.format(self.end, event='end')

    def format(self, data: ItemType, *, event: str | None = None) -> str:
        lines = []

        if event or self.event:
            lines.append(f"event: {event or self.event}")

        if isinstance(data, BaseModel):
            content = data.to_json()
        elif isinstance(data, dict):
            content = json.dumps(data, ensure_ascii=False)
        else:
            content = str(data)

        lines.append(f"data: {content}")
        lines.append("")

        return "\n".join(lines) + "\n"
