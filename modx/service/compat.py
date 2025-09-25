from __future__ import annotations

import typing as t

from modx.chatbot import Chatbot
from modx.chatbot.types.completion import Completion
from modx.chatbot.types.completion_chunk import CompletionChunk
from modx.chatbot.types.stream import AsyncStream
from modx.logger import Logger
from modx.resources.models import Models
from modx.resources.models.types import Model
from modx.resources.models.types import ModelList
from modx.service import BaseService
from modx.value_obj.chat_completion import ChatCompletionID
from modx.value_obj.chat_completion import MessagesObject
from modx.value_obj.chat_completion import ModelID


@t.runtime_checkable
class ICompatService(t.Protocol):

    async def chat_completions(self,
                               messages: MessagesObject,
                               *,
                               chatcmpl_id: ChatCompletionID | None = None,
                               model: ModelID,
                               stream: bool = True,
                               max_completion_tokens: int | None = None,
                               cache: bool = True) -> Completion | AsyncStream[CompletionChunk]:
        ...

    async def list_models(self) -> ModelList:
        ...

    async def retrieve_model(self, model_id: ModelID) -> Model:
        ...


class CompatService(BaseService):

    def __init__(self, logger: Logger, chatbot: Chatbot, models: Models):
        super().__init__(logger)
        self.chatbot = chatbot
        self.models = models

    async def chat_completions(self,
                               messages: MessagesObject,
                               *,
                               chatcmpl_id: ChatCompletionID | None = None,
                               model: ModelID,
                               stream: bool = True,
                               max_completion_tokens: int | None = None,
                               cache: bool = True) -> Completion | AsyncStream[CompletionChunk]:
        return await self.chatbot.chat(
            messages.messages,
            model=model.id,
            stream=stream,
            max_completion_tokens=max_completion_tokens,
            cache=cache,
            cache_key=chatcmpl_id.id if cache and chatcmpl_id else None,
            chatcmpl_id=chatcmpl_id.id if cache and chatcmpl_id else None)

    async def list_models(self) -> ModelList:
        return self.models.list_models()

    async def retrieve_model(self, model_id: ModelID) -> Model:
        return self.models.retrieve_model(model_id.id)
