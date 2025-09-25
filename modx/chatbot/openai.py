from __future__ import annotations

import time
import typing as t

import openai
import openai.types.chat as openai_chat

from modx import constants
from modx import exceptions
from modx import utils
from modx.cache import KVCache
from modx.chatbot import Chatbot
from modx.chatbot.tools import BaseTool
from modx.chatbot.types.completion import Completion
from modx.chatbot.types.completion import CompletionMessage
from modx.chatbot.types.completion_chunk import CompletionChunk
from modx.chatbot.types.completion_chunk import CompletionChunkDelta
from modx.chatbot.types.message import Messages
from modx.chatbot.types.stream import AsyncStream
from modx.client.http import HTTPClient
from modx.config import ModXConfig
from modx.helpers.mixin import LoggingTagMixin
from modx.logger import Logger
from modx.resources.models import Models


def map_finish_reason(
    reason: t.Literal["stop", "length", "tool_calls", "content_filter", "function_call"]
) -> t.Literal['stop', 'length', 'content_filter']:
    if reason == 'stop':
        return 'stop'
    elif reason == 'length':
        return 'length'
    elif reason == 'content_filter':
        return 'content_filter'
    else:
        return 'stop'


class ChatCompletion(Chatbot, LoggingTagMixin):
    __logging_tag__ = 'modx.chatbot.openai'

    def __init__(self, models: Models, logger: Logger, http_client: HTTPClient, cache: KVCache,
                 config: ModXConfig):
        LoggingTagMixin.__init__(self, logger)
        self.models = models
        self.http_client = http_client
        self.cache = cache
        self.config = config.chatbot

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
        messages = list(messages)
        cached_message = []
        key = cache and cache_key
        if key:
            cached_message = self.cache.get(key) or []
        chatcmpl_id = chatcmpl_id or utils.gen_id(pref=constants.IDPrefix.CHATCMPL)
        created = int(time.time())
        if model not in self.models:
            raise exceptions.NotFoundError(f'Model {model} not found')
        model_def = self.models[model]
        sysprompt = self.models.render_safe(model, **kwargs)
        message_list = (
            [openai_chat.ChatCompletionSystemMessageParam(role='system', content=sysprompt)] +
            cached_message + [
                openai_chat.ChatCompletionUserMessageParam(role='user', content=m.content) if m.role
                == 'user' else openai_chat.ChatCompletionAssistantMessageParam(role='assistant',
                                                                               content=m.content)
                for m in messages
            ])
        client = openai.AsyncClient(
            api_key=model_def.client.api_key,
            organization=model_def.client.organization,
            project=model_def.client.project,
            base_url=model_def.client.base_url,
            timeout=model_def.client.timeout,
            max_retries=model_def.client.max_retries,
            default_headers=model_def.client.default_headers,
            default_query=model_def.client.default_query,
            http_client=self.http_client.client  # Use shared HTTP client
        )
        completion = await client.chat.completions.create(
            messages=message_list,
            model=model_def.runtime.model,
            max_completion_tokens=(max_completion_tokens
                                   or model_def.runtime.max_completion_tokens),
            temperature=model_def.runtime.temperature,
            presence_penalty=model_def.runtime.presence_penalty,
            verbosity=model_def.runtime.verbosity,
            top_p=model_def.runtime.top_p,
            stream=stream)
        if stream:

            def map_chunk(chunk: openai_chat.ChatCompletionChunk) -> CompletionChunk:
                if chunk.usage:
                    return CompletionChunk(
                        id=chatcmpl_id,
                        created=created,
                        model=model,
                        delta=CompletionChunkDelta(),
                        # TODO: Usage handling. Should design a usage rule first
                    )
                elif (len(chunk.choices) and chunk.choices[0].delta.content
                      or chunk.choices[0].delta.refusal):
                    return CompletionChunk(
                        id=chatcmpl_id,
                        created=created,
                        model=model,
                        delta=CompletionChunkDelta(content=chunk.choices[0].delta.content,
                                                   refusal=chunk.choices[0].delta.refusal),
                    )
                elif (len(chunk.choices) and chunk.choices[0].finish_reason):
                    return CompletionChunk(
                        id=chatcmpl_id,
                        created=created,
                        model=model,
                        delta=CompletionChunkDelta(),
                        finish_reason=map_finish_reason(
                            chunk.choices[0].finish_reason  # type: ignore
                        ))
                else:
                    return CompletionChunk(
                        id=chatcmpl_id,
                        created=created,
                        model=model,
                        delta=CompletionChunkDelta(),
                    )

            astream = AsyncStream(completion, mapper=map_chunk)

            if cache:
                full_content = ''

                def collect_content(chunk: CompletionChunk):
                    nonlocal full_content
                    if chunk.delta.content:
                        full_content += chunk.delta.content

                cached_stream = astream.tap(collect_content)

                async def cache_on_complete() -> t.AsyncIterable[CompletionChunk]:
                    async for chunk in cached_stream:
                        yield chunk

                    if key and full_content.strip():
                        self.cache.setx(key,
                                        cached_message + [
                                            openai_chat.ChatCompletionUserMessageParam(
                                                role='user', content=messages[-1].content),
                                            openai_chat.ChatCompletionAssistantMessageParam(
                                                role='assistant', content=full_content)
                                        ],
                                        ttl=self.config.cache_ttl)

                return AsyncStream(cache_on_complete())
            return astream
        else:
            if cache and key:
                self.cache.setx(
                    key,
                    cached_message + [
                        openai_chat.ChatCompletionUserMessageParam(role='user',
                                                                   content=messages[-1].content),
                        openai_chat.ChatCompletionAssistantMessageParam(
                            role='assistant', content=completion.choices[0].message.content)
                    ],
                    ttl=self.config.cache_ttl)
            return Completion(id=chatcmpl_id,
                              created=created,
                              model=model,
                              message=CompletionMessage(
                                  content=completion.choices[0].message.content,
                                  refusal=completion.choices[0].message.refusal),
                              finish_reason=map_finish_reason(completion.choices[0].finish_reason))
