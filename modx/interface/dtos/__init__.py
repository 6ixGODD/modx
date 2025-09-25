import typing as t

import pydantic as pydt

import modx.constants as const
import modx.exceptions as exc


class BaseModel(pydt.BaseModel):
    model_config: t.ClassVar[pydt.ConfigDict] = (pydt.ConfigDict(extra='allow',
                                                                 use_enum_values=True,
                                                                 validate_assignment=True,
                                                                 ser_json_bytes='base64',
                                                                 val_json_bytes='base64',
                                                                 ser_json_inf_nan='strings',
                                                                 serialize_by_alias=True))

    def to_dict(self) -> t.Dict[str, t.Any]:
        return self.model_dump(mode='json', exclude_none=True, by_alias=True)

    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True, by_alias=True)

    @pydt.model_validator(mode='wrap')
    @classmethod
    def reraise_val_error(cls, data: t.Any,
                          handler: pydt.ModelWrapValidatorHandler[t.Self]) -> t.Self:
        try:
            return handler(data)
        except pydt.ValidationError as e:
            raise exc.InvalidParametersError.from_pydantic_validation_err(e)


_ResponseT = t.TypeVar("_ResponseT", bound=t.Union[BaseModel, t.Mapping[str, t.Any], t.List])


class Response(BaseModel, t.Generic[_ResponseT]):
    success: t.Annotated[
        bool,
        pydt.Field(..., description="Indicates if the request was successful", examples=[True]
                  )] = True

    code: t.Annotated[
        const.BusinessCode,
        pydt.Field(...,
                   description="Business code indicating the status of the operation",
                   examples=[const.BusinessCode.SUCCESS])] = const.BusinessCode.SUCCESS

    data: t.Annotated[_ResponseT | None,
                      pydt.Field(
                          ...,
                          description="The actual response data. Structure varies based on "
                          "the endpoint.",
                          examples=[{
                              "key": "value"
                          }, {
                              "items": [1, 2, 3]
                          }])] = None


class ErrorResponse(Response[exc.ExceptionDetails]):
    success: t.Annotated[bool,
                         pydt.Field(default=False,
                                    description="Indicates if the request was successful",
                                    examples=[False])] = False

    code: t.Annotated[const.BusinessCode,
                      pydt.Field(
                          ...,
                          description="Business code indicating the error status",
                          examples=[
                              const.BusinessCode.UNKNOWN_ERROR, const.BusinessCode.
                              INTERNAL_ERROR, const.BusinessCode.INVALID_PARAMS
                          ])] = const.BusinessCode.INTERNAL_ERROR

    data: t.Annotated[
        exc.ExceptionDetails,
        pydt.Field(...,
                   description="Details of the error that occurred",
                   examples=[{
                       "message": "An error occurred",
                       "code": 500
                   }])] = exc.ExceptionDetails(
                       message="An internal server error occurred. Please try again later, "
                       "or record the `x-request-id` response header and report to "
                       "the administrator",)


class Pagination(BaseModel):
    current_page: t.Annotated[int,
                              pydt.Field(..., description="Current page number", examples=[1])] = 1

    total_pages: t.Annotated[
        int, pydt.Field(..., description="Total number of pages available", examples=[10])] = 1

    total_items: t.Annotated[
        int,
        pydt.Field(..., description="Total number of items across all pages", examples=[100])] = 0

    items_per_page: t.Annotated[
        int, pydt.Field(..., description="Number of items per page", examples=[10])] = 10
