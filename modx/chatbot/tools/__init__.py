from __future__ import annotations

import abc
import functools as ft
import inspect
import json
import re
import typing as t

import pydantic as pydt

# JSON serializable types
JsonPrimitive = t.Union[str, int, float, bool, None]

if t.TYPE_CHECKING:
    JsonValue = t.Union[
        JsonPrimitive,
        t.Dict[str, 'JsonValue'],
        t.List['JsonValue']
    ]
else:
    JsonValue = t.Any

# JSON Schema types
JsonSchemaType = t.Literal[
    "string",
    "integer",
    "number",
    "boolean",
    "array",
    "object"
]


class PropertySchema(pydt.BaseModel):
    type: JsonSchemaType
    description: str | None = None
    enum: t.List[JsonValue] | None = None
    items: t.Dict[str, JsonValue] | None = None
    properties: t.Dict[str, t.Dict[str, JsonValue]] | None = None
    required: t.List[str] | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    minLength: int | None = None
    maxLength: int | None = None
    pattern: str | None = None
    format: str | None = None
    default: JsonValue | None = None
    examples: t.List[JsonValue] | None = None
    minItems: int | None = None
    maxItems: int | None = None
    uniqueItems: bool | None = None
    additionalProperties: t.Union[bool, t.Dict[str, JsonValue]] | None = None

    model_config = pydt.ConfigDict(extra='allow')


class ParameterSchema(pydt.BaseModel):
    type: t.Literal['object'] = 'object'
    """The type of the parameter, which is 'object'."""

    properties: t.Dict[str, PropertySchema]
    """A dictionary of properties that define the parameters for the function.
    Each key is the name of a parameter, and the value is a schema that
    describes the parameter's type and constraints."""

    required: t.List[str] = pydt.Field(default_factory=list)
    """List of required parameter names."""


class FunctionSchema(pydt.BaseModel):
    name: t.Annotated[
        str,
        pydt.Field(
            min_length=1,
            max_length=64,
            description="The name of the function to be called by the tool.",
            examples=["get_weather", "calculate_sum"]
        )
    ]
    """The name of the function to be called by the tool."""

    description: str
    """A description of what the function does. This should provide enough
    information for the tool to understand how to use the function."""

    parameters: ParameterSchema | None = None
    """The parameters that the function accepts. This should be a valid
    schema that defines the input parameters for the function."""


class ToolSchema(pydt.BaseModel):
    type: t.Literal['function'] = 'function'
    """The type of the tool, which is 'function'."""

    function: FunctionSchema
    """The function that the tool will call. This should be a valid function
    that can be executed by the tool."""


class Property:
    __slots__ = (
        'description',
        'enums',
        'minimum',
        'maximum',
        'min_length',
        'max_length',
        'pattern',
        'format',
        'default',
        'examples',
        'min_items',
        'max_items',
        'unique_items',
        'extra'
    )

    def __init__(
        self,
        *,
        description: str | None = None,
        enums: t.List[JsonValue] | None = None,
        minimum: int | float | None = None,
        maximum: int | float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        format: str | None = None,
        default: JsonValue | None = None,
        examples: t.List[JsonValue] | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        unique_items: bool | None = None,
        **kwargs: JsonValue
    ):
        self.description = description
        self.enums = enums
        self.minimum = minimum
        self.maximum = maximum
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.format = format
        self.default = default
        self.examples = examples
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items
        self.extra = kwargs


def _get_json_schema_type(python_type: type) -> JsonSchemaType:
    """Get the JSON schema type for a Python type."""
    origin = t.get_origin(python_type)
    args = t.get_args(python_type)

    if origin is t.Union:
        # Handle Optional[T] which is Union[T, None]
        non_none_types = [arg for arg in args if arg is not type(None)]
        if len(non_none_types) == 1:
            return _get_json_schema_type(non_none_types[0])
        # Handle other Union types - for now just take the first type
        return _get_json_schema_type(non_none_types[0])

    # Handle List types
    if origin is list or python_type is list:
        return "array"

    # Handle Dict types
    if origin is dict or python_type is dict:
        return "object"

    # Handle Literal types
    if origin is t.Literal:
        first_arg = args[0]
        if isinstance(first_arg, str):
            return "string"
        elif isinstance(first_arg, int):
            return "integer"
        elif isinstance(first_arg, float):
            return "number"
        elif isinstance(first_arg, bool):
            return "boolean"
        else:
            return "string"

    # Basic types
    type_mapping: t.Dict[type, JsonSchemaType] = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        dict: "object",
        list: "array",
    }

    return type_mapping.get(python_type, "string")


def _get_array_items_schema(python_type: type) -> t.Dict[str, JsonValue] | None:
    """Get the items schema for array types."""
    origin = t.get_origin(python_type)
    args = t.get_args(python_type)

    if origin is list and args:
        item_type = args[0]
        return {"type": _get_json_schema_type(item_type)}

    return None


def _get_literal_enum_values(python_type: type) -> t.List[JsonValue] | None:
    """Get enum values for Literal types."""
    origin = t.get_origin(python_type)
    args = t.get_args(python_type)

    if origin is t.Literal:
        return list(args)

    return None


def _extract_property_from_annotation(
    annotation: t.Any
) -> t.Tuple[type, Property | None]:
    """Extract the actual type and Property descriptor from a type
    annotation."""
    if t.get_origin(annotation) is t.Annotated:
        args = t.get_args(annotation)
        actual_type = args[0]

        # Look for Property in the metadata
        for metadata in args[1:]:
            if isinstance(metadata, Property):
                return actual_type, metadata

        return actual_type, None

    return annotation, None


class BaseTool(abc.ABC):
    __function_description__: t.ClassVar[str]

    @abc.abstractmethod
    def __call__(self, **kwargs) -> JsonValue:
        """The actual implementation of the tool."""
        pass

    @staticmethod
    def _parse_arguments(args: str) -> t.Dict[str, JsonValue]:
        """Parse a string of arguments into a dictionary."""
        if not args:
            return {}
        try:
            return json.loads(args)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {args}") from e

    @ft.cached_property
    def __function_name__(self) -> str:
        """Generate function name from class name in snake_case."""
        cls_name = self.__class__.__name__
        s1 = re.sub('([A-Z]+)([A-Z][a-z])', r'\1_\2', cls_name)
        s2 = re.sub('([a-z\d])([A-Z])', r'\1_\2', s1)
        return s2.lower().replace(' ', '_').replace('-', '_')

    @ft.cached_property
    def schema(self) -> ToolSchema:
        """Generate Tool schema from the __call__ method signature."""
        sig = inspect.signature(self.__call__)
        properties: t.Dict[str, PropertySchema] = {}
        required: t.List[str] = []
        type_hints = t.get_type_hints(self.__call__, include_extras=True)

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            actual_annotation = type_hints[param_name]
            # Extract type and Property descriptor
            actual_type, prop_desc = (
                _extract_property_from_annotation(actual_annotation)
            )

            # Get basic JSON schema type
            json_type = _get_json_schema_type(actual_type)

            # Build PropertySchema directly
            property_schema = PropertySchema(
                type=json_type,
                description=prop_desc.description if prop_desc else None,
                enum=(prop_desc.enums
                      if prop_desc and prop_desc.enums
                      else _get_literal_enum_values(actual_type)),
                items=_get_array_items_schema(actual_type),
                minimum=prop_desc.minimum if prop_desc else None,
                maximum=prop_desc.maximum if prop_desc else None,
                minLength=prop_desc.min_length if prop_desc else None,
                maxLength=prop_desc.max_length if prop_desc else None,
                pattern=prop_desc.pattern if prop_desc else None,
                format=prop_desc.format if prop_desc else None,
                default=prop_desc.default if prop_desc else None,
                examples=prop_desc.examples if prop_desc else None,
                minItems=prop_desc.min_items if prop_desc else None,
                maxItems=prop_desc.max_items if prop_desc else None,
                uniqueItems=prop_desc.unique_items if prop_desc else None,
            )

            # Add any extra properties from Property descriptor
            if prop_desc and prop_desc.extra:
                for key, value in prop_desc.extra.items():
                    setattr(property_schema, key, value)

            properties[param_name] = property_schema

            # Check if parameter is required (no default value)
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        return ToolSchema(
            function=FunctionSchema(
                name=self.__function_name__,
                description=self.__function_description__,
                parameters=ParameterSchema(
                    properties=properties,
                    required=required
                ) if properties else None
            )
        )

    @property
    def schema_dict(self) -> t.Dict[str, JsonValue]:
        """Convert tool schema to dictionary."""
        return self.schema.model_dump(exclude_none=True, mode='json')

    @property
    def schema_json(self) -> str:
        """Convert tool schema to JSON string."""
        return self.schema.model_dump_json(indent=2, exclude_none=True)
