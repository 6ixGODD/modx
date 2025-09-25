from __future__ import annotations

import typing as t

from modx.chatbot.types import BaseSchema


class Message(BaseSchema):
    role: t.Literal['user', 'assistant']
    content: str | bytes

    __slots__ = ('role', 'content')

    def __init__(self, *, role: t.Literal['user', 'assistant'], content: str) -> None:
        super().__init__()
        self.role = role
        self.content = content


Messages: t.TypeAlias = t.Iterable[Message]
