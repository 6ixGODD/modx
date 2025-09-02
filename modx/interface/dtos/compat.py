from __future__ import annotations

import typing as t

import typing_extensions as te

import modx.resources.models.types as types
from modx.interface.dtos import BaseModel


class ChatCompletionContentPartParamsBase(BaseModel):
    type: t.Literal['text', 'image']
    """The type of the content part. Currently, only 'text' and 'image' are 
    supported."""


class ChatCompletionContentPartTextParams(ChatCompletionContentPartParamsBase):
    type: t.Literal['text'] = 'text'
    """The type of the content part, which is 'text'."""

    text: str
    """The text content of the message."""


class ChatCompletionContentPartImageParams(ChatCompletionContentPartParamsBase):
    type: t.Literal['image'] = 'image'
    """The type of the content part, which is 'image'."""

    image_url: str
    """The URL of the image content. This should be a publicly accessible URL 
    where the image can be retrieved."""


ChatCompletionContentPartParams = t.Union[
    ChatCompletionContentPartTextParams,
    ChatCompletionContentPartImageParams
]


class ChatCompletionsMessageParams(BaseModel):
    role: t.Literal['user', 'assistant']
    """When the value is "user", messages sent by an end user, containing 
    prompts or additional context information. Otherwise, Messages sent by the 
    model in response to user messages."""

    content: str | t.List[ChatCompletionContentPartParams]
    """The contents of the message. """

    name: t.Literal[None] = None
    """Used for completeness now."""

    refusal: str | None = None
    """The refusal message by the assistant."""

    tool_calls: t.Literal[None] = None
    """This field is only used for completeness now. It may be used in the 
    future :)"""


class ChatCompletionStreamOptionsParams(BaseModel):
    include_usage: bool
    """If set, an additional chunk will be streamed before the data: [DONE] 
    message. The usage field on this chunk shows the token usage statistics 
    for the entire request, and the choices field will always be an empty array.

    All other chunks will also include a usage field, but with a null value. 
    NOTE: If the stream is interrupted, you may not receive the final usage 
    chunk which contains the total token usage for the request."""


class ChatCompletionParams(BaseModel):
    messages: t.List[ChatCompletionsMessageParams]
    """A list of messages comprising the conversation so far. Depending on 
    the model you use, different message types (modalities) are supported, 
    like text, images, and audio."""

    model: str
    """Model ID used to generate the response"""

    max_completion_tokens: int | None = None
    """An upper bound for the number of tokens that can be generated for a 
    completion, including visible output tokens and reasoning tokens."""

    max_tokens: int | None = None
    """The maximum number of tokens that can be generated in the chat 
    completion. This value can be used to control costs for text generated 
    via API.

    This value is now deprecated in favor of `max_completion_tokens`"""

    n: int | None = None
    """How many chat completion choices to generate for each input message. 
    Note that you will be charged based on the number of generated tokens 
    across all of the choices. Keep n as 1 to minimize costs."""

    stream: bool | None = None
    """If set to true, the model response data will be streamed to the client 
    as it is generated using server-sent events. See the Streaming section 
    below for more information, along with the streaming responses guide for 
    more information on how to handle the streaming events."""

    stream_options: ChatCompletionStreamOptionsParams | None = None
    """Options for streaming response. Only set this when you set stream: 
    true."""

    user: str | None = None
    """A stable identifier for your end-users. Used to boost cache hit rates 
    by better bucketing similar requests and to help OpenAI detect and 
    prevent abuse."""

    prompt_cache_key: str | None = None
    """Cache responses for similar requests to optimize your cache hit rates. 
    Replaces the user field."""

    cache: bool | None = None
    """This field is NOT standard in the OpenAI API, but can be used for 
    “stateful” session management. If set true, the session (current message 
    context) will be cached for a period of time, keyed by `chatcmpl-id`. If 
    a `chat_id` field value is also present, an attempt will be made to 
    provide the cached message context using the `chat_id` (if hit). This is 
    useful for resource-constrained clients, such as embedded devices. This 
    will be deprecated in favor of a dedicated API for edge devices."""

    chat_id: str | None = None
    """This field is NOT standard in the OpenAI API. If provided with a 
    `cache: true` field, an attempt will be made to provide the cached 
    message context using the `chat_id` (if hit)."""


class ChatCompletionMessage(te.TypedDict, total=False):
    reasoning: str
    """The reasoning message by the assistant, if applicable. 

    (!) It is not a standard field in the OpenAI API, but can be used to 
    provide additional context or explanation for the assistant's response. 
    This field is not guaranteed to be present in all responses, and its 
    content may vary based on the model and the specific implementation of 
    the chat completion API."""

    content: str
    """The contents of the message."""

    refusal: str
    """The refusal message by the assistant."""

    role: t.Required[t.Literal["assistant"]]
    """The role of the message sender. Can be 'user' or 'assistant'."""

    annotations: t.List[t.Any]
    audio: t.Literal[None]
    function_call: t.Literal[None]
    tool_calls: t.Literal[None]


class ChatCompletionChoice(te.TypedDict, total=False):
    finish_reason: t.Literal["stop", "length", "content_filter"]
    """The reason the model stopped generating tokens."""

    index: t.Required[int]
    """The index of the choice in the list of choices."""

    logprobs: t.Literal[None]
    """Log probability information for the choice."""

    message: t.Required[ChatCompletionMessage]


class ChatCompletionUsage(te.TypedDict, total=False):
    completion_tokens: t.Required[int]
    """Number of tokens in the generated completion."""

    prompt_tokens: t.Required[int]
    """Number of tokens in the prompt."""

    total_tokens: t.Required[int]
    """Total number of tokens used in the request (prompt + completion)."""

    completion_tokens_details: t.Literal[None]
    prompt_tokens_details: t.Literal[None]


class ChatCompletion(te.TypedDict, total=False):
    id: t.Required[str]
    """A unique identifier for the chat completion."""

    choices: t.Required[t.List[ChatCompletionChoice]]
    """A list of chat completion choices.

    Can be more than one if `n` is greater than 1.
    """

    created: t.Required[int]
    """The Unix timestamp (in seconds) of when the chat completion was 
    created."""

    model: t.Required[str]
    """The model used for the chat completion."""

    object: t.Required[t.Literal["chat.completion"]]
    """The object type, which is always `chat.completion`."""

    service_tier: t.Literal[None]

    system_fingerprint: str
    """This fingerprint represents the backend configuration that the model 
    runs with."""

    usage: ChatCompletionUsage


class ChatCompletionChunkDelta(te.TypedDict, total=False):
    reasoning: str
    """The reasoning delta by the assistant, if applicable."""

    content: str
    """The content of the message chunk. This is the text that is being 
    generated by the model in this chunk."""

    function_call: t.Literal[None]

    refusal: str
    """The refusal message by the assistant, if applicable."""

    role: t.Required[t.Literal["assistant"]]
    """The role of the message sender, which is always 'assistant' for 
    chunks."""

    tool_calls: t.Literal[None]


class ChatCompletionChunkChoice(te.TypedDict, total=False):
    delta: t.Required[ChatCompletionChunkDelta]
    """A chat completion delta generated by streamed model responses."""

    finish_reason: t.Literal["stop", "length", "content_filter"] | None
    """The reason the model stopped generating tokens for this choice."""

    index: t.Required[t.Literal[0]]
    """The index of the choice in the list of choices. This is always 0 for
    streamed responses, as each chunk contains only one choice."""

    logprobs: t.Literal[None]


class ChatCompletionChunk(te.TypedDict, total=False):
    id: t.Required[str]
    """A unique identifier for the chat completion. Each chunk has the same 
    ID."""

    choices: t.Required[t.List[ChatCompletionChunkChoice]]
    """A list of chat completion choices.

    Can contain more than one elements if `n` is greater than 1. Can also be 
    empty
    for the last chunk if you set `stream_options: {"include_usage": true}`.
    """

    created: t.Required[int]
    """The Unix timestamp (in seconds) of when the chat completion chunk was 
    created."""

    model: t.Required[str]
    """The model used for the chat completion chunk."""

    object: t.Required[t.Literal["chat.completion.chunk"]]
    """The object type, which is always `chat.completion.chunk`."""

    system_fingerprint: str
    """This fingerprint represents the backend configuration that the model 
    runs with."""

    usage: ChatCompletionUsage


AsyncCompletion = ChatCompletion
AsyncCompletionStream = t.AsyncIterable[ChatCompletionChunk]
CompatResponse = t.Union[AsyncCompletion, AsyncCompletionStream]
Model = types.Model
ModelList = types.ModelList
