from __future__ import annotations

import typing as t

import pydantic as pydt

from modx import constants, exceptions, utils
from modx.chatbot.types.message import Message
from modx.value_obj import BaseValueObject


class MessagesObject(BaseValueObject):
    messages: t.List[Message]

    @pydt.model_validator(mode='after')
    def val_messages(self) -> t.Self:
        iterator = iter(self.messages)

        try:
            first = next(iterator)
        except StopIteration:
            raise exceptions.InvalidParametersError(
                "Messages cannot be empty",
            )

        if first.role not in ('user', 'assistant'):
            raise exceptions.InvalidParametersError(
                f"Role must be 'user' or 'assistant', got {first.role!r}"
            )

        if first.role != 'user':
            raise exceptions.InvalidParametersError(
                "First message must be from 'user'"
            )

        prev = first
        last = first
        for i, curr in enumerate(iterator, start=1):
            if curr.role not in ('user', 'assistant'):
                raise exceptions.InvalidParametersError(
                    f"Role must be 'user' or 'assistant', got {curr.role!r}"
                )
            if prev.role == curr.role:
                raise exceptions.InvalidParametersError(
                    "Messages must alternate between 'user' and 'assistant'"
                )
            prev = curr
            last = curr

        if last.role != 'user':
            raise exceptions.InvalidParametersError(
                "Last message must be from 'user'"
                )

        return self


class ChatCompletionID(BaseValueObject):
    id: str

    def __init__(self, id: str | None = None):
        id = id or utils.gen_id(
            constants.IDPrefix.CHATCMPL,
            without_hyphen=True
            )
        super().__init__(id=id)

    @pydt.model_validator(mode='after')
    def val_id(self) -> t.Self:
        if not self.id.startswith(constants.IDPrefix.CHATCMPL):
            raise exceptions.InvalidParametersError(
                f"ID must start with '{constants.IDPrefix.CHATCMPL}', "
                f"got {self.id!r}"
            )
        if not len(self.id[len(constants.IDPrefix.CHATCMPL):]) == 32:
            raise exceptions.InvalidParametersError("ID must be a valid UUID")
        return self


class ModelID(BaseValueObject):
    id: t.Annotated[
        str,
        pydt.Field(min_length=1, max_length=100)
    ]
