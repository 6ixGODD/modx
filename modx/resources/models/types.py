from __future__ import annotations

import typing as t

import pydantic as pydt
import typing_extensions as te


class BaseModel(pydt.BaseModel):
    model_config: t.ClassVar[pydt.ConfigDict] = pydt.ConfigDict(
        extra="allow",
        frozen=True,
    )

    @classmethod
    def from_dict(cls, data: dict) -> t.Self:
        return cls.model_validate(data, strict=True)


class OpenAIClientConfig(BaseModel):
    api_key: str
    organization: str | None = None
    project: str | None = None
    timeout: float | None = None
    base_url: str
    max_retries: int = 3
    default_headers: t.Mapping[str, str] | None = None
    default_query: t.Mapping[str, object] | None = None


class RuntimeConfig(BaseModel):
    model: str
    max_completion_tokens: int | None = None
    temperature: float | None = None
    presence_penalty: float | None = None
    verbosity: t.Literal["low", "medium", "high"] | None = None
    top_p: float | None = None


class ModelDefinition(BaseModel):
    id: str = pydt.Field(..., description="The model's unique identifier")
    created: int = pydt.Field(
        ...,
        description="Unix timestamp when model was created"
    )
    owned_by: t.Literal['modx'] | str = pydt.Field(
        default='modx',
        description="Model owner"
    )

    prompt_path: str | None = pydt.Field(
        None,
        description="Path to prompt template file"
    )

    client: OpenAIClientConfig = pydt.Field(
        ...,
        description="Configuration for OpenAI client"
    )

    runtime: RuntimeConfig = pydt.Field(
        ...,
        description="Runtime configuration for model"
    )


class Model(te.TypedDict, total=False):
    id: t.Required[str]
    """The model's unique identifier."""

    object: t.Required[t.Literal["model"]]
    """The object type, which is always `model`."""

    name: str
    """The name of the model."""

    summary: str
    """A brief description of the model."""

    description: str
    """A detailed description of the model."""

    created: t.Required[int]
    """The Unix timestamp (in seconds) of when the model was created."""

    owned_by: t.Required[t.Literal['modx'] | str]
    """The organization or user that owns the model."""


class ModelList(te.TypedDict, total=False):
    object: t.Required[t.Literal["list"]]
    """The object type, which is always `list`."""

    data: t.Required[t.List[Model]]
    """A list of models available in the API."""
