from __future__ import annotations

import typing as t

from modx.chatbot.types import BaseSchema
from modx.chatbot.types.usage import Usage


class CompletionMessage(BaseSchema):
    content: str | None
    refusal: str | None

    __slots__ = ('content', 'refusal')

    def __init__(
        self,
        *,
        content: str | None = None,
        refusal: str | None = None,
    ) -> None:
        self.content = content
        self.refusal = refusal


class Completion(BaseSchema):
    id: str
    message: CompletionMessage
    finish_reason: t.Literal['stop', 'length', 'content_filter']
    created: int
    model: str
    usage: Usage

    __slots__ = (
        "id",
        "message",
        "finish_reason",
        "created",
        "model",
        "usage",
    )

    def __init__(
        self,
        *,
        id: str,
        message: CompletionMessage,
        finish_reason: t.Literal['stop', 'length', 'content_filter'],
        created: int,
        model: str,
        usage: Usage,
    ) -> None:
        self.id = id
        self.message: CompletionMessage = message
        self.finish_reason = finish_reason
        self.created = created
        self.model = model
        self.usage = usage
