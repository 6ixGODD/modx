from __future__ import annotations

import typing as t

import beanie
import pydantic as pydt

import modx.exceptions as exc


class BaseValueObject(pydt.BaseModel):
    model_config: t.ClassVar[pydt.ConfigDict] = pydt.ConfigDict(
        validate_assignment=True,  # Validate on assignment
        extra="forbid",  # Disallow extra fields
        arbitrary_types_allowed=True,  # Allow arbitrary types
        populate_by_name=True,  # Allow population by field name
        use_enum_values=True,  # Use enum values directly
        frozen=True  # Make the model immutable
    )

    @pydt.model_validator(mode='wrap')
    @classmethod
    def reraise_val_error(cls, data: t.Any,
                          handler: pydt.ModelWrapValidatorHandler[t.Self]) -> t.Self:
        try:
            return handler(data)
        except pydt.ValidationError as e:
            raise exc.InvalidParametersError.from_pydantic_validation_err(e)


class ObjectID(BaseValueObject):
    id: str

    @pydt.model_validator(mode='after')
    def check_object_id(self) -> t.Self:
        if len(self.id) != 24:
            raise exc.InvalidParametersError("Invalid object ID",
                                             params={"id": "id must be 24 characters long"})
        return self

    def to_object_id(self) -> beanie.BeanieObjectId:
        return beanie.BeanieObjectId(self.id)

    def __str__(self):
        return self.id


class PaginationParams(BaseValueObject):
    page: int = pydt.Field(default=1,
                           ge=1,
                           description="Page number for pagination, starting from 1")
    limit: int = pydt.Field(default=10,
                            ge=1,
                            le=100,
                            description="Number of items per page, between 1 and 100")
