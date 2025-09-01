from __future__ import annotations

import typing as t

import pydantic as pydt

import modx.constants as const
import modx.exceptions as exc
import modx.utils as utils
from modx.chatbot.types.message import Messages
from modx.value_obj import BaseValueObject


class MessagesObject(BaseValueObject):
    messages: Messages

    @pydt.model_validator(mode='after')
    def val_messages(self) -> t.Self:
        iterator = iter(self.messages)

        try:
            first = next(iterator)
        except StopIteration:
            raise exc.InvalidParametersError("Messages cannot be empty", )

        if first.role not in ('user', 'assistant'):
            raise exc.InvalidParametersError(
                f"Role must be 'user' or 'assistant', got {first.role!r}"
            )

        if first.role != 'user':
            raise exc.InvalidParametersError(
                "First message must be from 'user'"
            )

        prev = first
        last = first
        for i, curr in enumerate(iterator, start=1):
            if curr.role not in ('user', 'assistant'):
                raise exc.InvalidParametersError(
                    f"Role must be 'user' or 'assistant', got {curr.role!r}"
                )
            if prev.role == curr.role:
                raise exc.InvalidParametersError(
                    "Messages must alternate between 'user' and 'assistant'"
                )
            prev = curr
            last = curr

        if last.role != 'user':
            raise exc.InvalidParametersError("Last message must be from 'user'")

        return self


class ChatCompletionID(BaseValueObject):
    id: str

    def __init__(self, id: str | None = None):
        id = id or utils.gen_id(const.IDPrefix.CHATCMPL, without_hyphen=True)
        super().__init__(id=id)

    @pydt.model_validator(mode='after')
    def val_id(self) -> t.Self:
        if not self.id.startswith(const.IDPrefix.CHATCMPL):
            raise exc.InvalidParametersError(
                f"ID must start with '{const.IDPrefix.CHATCMPL}', "
                f"got {self.id!r}"
            )
        if not len(self.id[len(const.IDPrefix.CHATCMPL):]) == 32:
            raise exc.InvalidParametersError("ID must be a valid UUID")
        return self


class ModelID(BaseValueObject):
    id: t.Annotated[
        str,
        pydt.Field(min_length=1, max_length=100)
    ]
