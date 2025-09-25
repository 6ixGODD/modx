from __future__ import annotations

from modx.chatbot.types import BaseSchema


class Usage(BaseSchema):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    __slots__ = ('prompt_tokens', 'completion_tokens', 'total_tokens')

    def __init__(self, *, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
