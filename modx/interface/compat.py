from __future__ import annotations

import typing as t

from modx.chatbot.types.completion_chunk import CompletionChunk
from modx.chatbot.types.message import Message
from modx.chatbot.types.stream import AsyncStream
from modx.interface import BaseInterface
from modx.interface.dtos.compat import (
    ChatCompletion,
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatCompletionMessage,
    ChatCompletionParams,
    CompatResponse,
    Model,
    ModelList,
)
from modx.logger import Logger
from modx.service.compat import ICompatService
from modx.value_obj.chat_completion import (
    ChatCompletionID,
    MessagesObject,
    ModelID,
)


@t.runtime_checkable
class ICompatInterface(t.Protocol):
    async def chat_completions(
        self,
        params: ChatCompletionParams
    ) -> CompatResponse: ...

    async def list_models(self) -> ModelList: ...

    async def retrieve_model(self, model_id: str) -> Model: ...


class CompatInterface(BaseInterface):
    def __init__(
        self,
        *,
        logger: Logger,
        compat_service: ICompatService
    ):
        super().__init__(logger)
        self.compat_service = compat_service

    async def chat_completions(
        self,
        params: ChatCompletionParams
    ) -> CompatResponse:
        # Convert to value objects
        messages = MessagesObject(
            messages=[Message(role=m.role, content=m.content)
                      for m in params.messages]
        )
        chatcmpl_id = (ChatCompletionID(id=params.chat_id)
                       if params.chat_id and params.cache else None)
        model = ModelID(id=params.model)

        completion = await self.compat_service.chat_completions(
            messages=messages,
            chatcmpl_id=chatcmpl_id,
            model=model,
            stream=params.stream,
            max_completion_tokens=params.max_completion_tokens,
            cache=params.cache
        )
        if isinstance(completion, AsyncStream):
            def map_chunk(chunk: CompletionChunk) -> ChatCompletionChunk:
                return ChatCompletionChunk(
                    id=chunk.id,
                    object='chat.completion.chunk',
                    created=chunk.created,
                    model=chunk.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0,
                            delta=ChatCompletionChunkDelta(
                                role='assistant',
                                content=chunk.delta.content,
                                refusal=chunk.delta.refusal,
                            ),
                            finish_reason=chunk.finish_reason,
                        )
                    ],
                )

            return completion.map(map_chunk)
        else:
            return ChatCompletion(
                id=completion.id,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatCompletionMessage(
                            role='assistant',
                            content=completion.message.content,
                            refusal=completion.message.refusal,
                        )
                    )
                ],
                created=completion.created,
                model=completion.model,
                object='chat.completion',
                service_tier=None,
            )

    async def list_models(self) -> ModelList:
        return await self.compat_service.list_models()

    async def retrieve_model(self, model_id: str) -> Model:
        return await self.compat_service.retrieve_model(ModelID(id=model_id))
