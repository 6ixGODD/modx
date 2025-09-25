from __future__ import annotations

import abc
import typing as t

from modx.chatbot.tools import BaseTool
from modx.chatbot.types.completion import Completion
from modx.chatbot.types.completion_chunk import CompletionChunk
from modx.chatbot.types.message import Messages
from modx.chatbot.types.stream import AsyncStream


class Chatbot(abc.ABC):

    @abc.abstractmethod
    async def chat(self,
                   messages: Messages,
                   *,
                   model: str,
                   stream: bool = False,
                   max_completion_tokens: int | None = None,
                   cache: bool = True,
                   cache_key: str | None = None,
                   chatcmpl_id: str | None = None,
                   toolset: t.Iterable[BaseTool] | None = None,
                   **kwargs: t.Any) -> AsyncStream[CompletionChunk] | Completion:
        pass
