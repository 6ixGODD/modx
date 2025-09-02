from __future__ import annotations

import http
import typing as t

import pydantic as pydt
import typing_extensions as te

import modx.constants as const


class ExceptionDetails(te.TypedDict, total=False):
    message: t.Required[str | t.Sequence[t.Any]]
    params: t.Dict[int | str, str] | None


class ModXException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg

    def __str__(self) -> str:
        return self.msg

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.msg!r})"

    @property
    def details(self) -> ExceptionDetails:
        return ExceptionDetails(message=self.msg)


class BootstrapException(ModXException):
    """Exception raised during the startup or initialization phase of the
    service.

    This exception should be used to indicate errors that occur while the
    application is starting up—such as configuration loading, dependency
    injection, or essential resource acquisition. When this exception is
    raised, the service should fail fast and terminate, as it indicates that
    the application cannot safely start.

    Examples where this exception is appropriate:
        - Configuration files are missing or malformed.
        - A required service (e.g., database, cache) is unreachable during
        startup.
        - Environment variables or secrets are not set.

    Attributes:
        exit_code (int): The return value code for the bootstrap process.
    """
    exit_code: int = 100


class NotImplementedException(BootstrapException, NotImplementedError):
    exit_code = 101


class RequiredModuleNotFoundException(BootstrapException, ImportError):
    exit_code = 102


class InvalidConfigurationException(BootstrapException):
    exit_code = 103


class RuntimeException(ModXException):
    """Exception raised during the runtime (request handling) phase of the
    service.

    This exception should be used for errors that occur while the service is
    running and handling requests—such as user input errors, business logic
    validation failures, or transient issues with third-party services. When
    this exception is raised, it should be caught and handled gracefully (
    e.g., by returning an error response), without causing the service to
    terminate.

    Examples where this exception is appropriate:
        - Invalid user input detected during a request.
        - A business rule is violated while processing a request.
        - A third-party API call fails or times out.

    Attributes:
        msg (str): A human-readable error message.
        code (constants.BusinessCode): A business-specific error code.
        status_code (int): The HTTP status code to return.
    """

    def __init__(
        self,
        msg: str, /,
        *,
        code: const.BusinessCode = const.BusinessCode.UNKNOWN_ERROR,
        status_code: int = http.HTTPStatus.INTERNAL_SERVER_ERROR,
    ):
        super().__init__(msg)
        self.code = code
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{self.msg} (code: {self.code}, status: {self.status_code})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"msg={self.msg!r}, "
            f"code={self.code!r}, "
            f"status_code={self.status_code!r}, "
            f"details={self.details!r})"
        )


class BadRequestError(RuntimeException):

    def __init__(
        self,
        msg: str = http.HTTPStatus.BAD_REQUEST.phrase, /,
        *,
        code: const.BusinessCode = const.BusinessCode.BAD_REQUEST,
    ):
        super().__init__(
            msg,
            code=code,
            status_code=http.HTTPStatus.BAD_REQUEST.value,
        )


class InvalidParametersError(BadRequestError):
    def __init__(
        self,
        msg: str = http.HTTPStatus.BAD_REQUEST.phrase, /,
        *,
        params: t.Dict[str, str] | None = None,
    ):
        super().__init__(
            msg,
            code=const.BusinessCode.INVALID_PARAMS,
        )
        self.params = params

    @property
    def details(self) -> ExceptionDetails:
        return ExceptionDetails(
            message=self.msg,
            params=self.params
        )

    @classmethod
    def from_pydantic_validation_err(
        cls,
        exc: pydt.ValidationError,
        msg: str = "Invalid parameters.",
    ):
        params = {}
        for detail in exc.errors():
            try:
                params[detail['loc'][0]] = detail['msg']
            except IndexError:
                params['msg'] = detail['msg']
        return cls(msg, params=params)


class UnauthorizedError(RuntimeException):
    def __init__(
        self,
        msg: str = http.HTTPStatus.UNAUTHORIZED.phrase, /,
        *,
        code: const.BusinessCode = const.BusinessCode.UNAUTHORIZED,
    ):
        super().__init__(
            msg,
            code=code,
            status_code=http.HTTPStatus.UNAUTHORIZED.value,
        )


class ForbiddenError(RuntimeException):
    def __init__(
        self,
        msg: str = http.HTTPStatus.FORBIDDEN.phrase, /,
        *,
        code: const.BusinessCode = const.BusinessCode.FORBIDDEN,
    ):
        super().__init__(
            msg,
            code=code,
            status_code=http.HTTPStatus.FORBIDDEN.value,
        )


class NotFoundError(RuntimeException):
    def __init__(
        self,
        msg: str = http.HTTPStatus.NOT_FOUND.phrase, /,
        *,
        code: const.BusinessCode = const.BusinessCode.NOT_FOUND,
    ):
        super().__init__(
            msg,
            code=code,
            status_code=http.HTTPStatus.NOT_FOUND.value,
        )


class ServiceUnavailableError(RuntimeException):
    def __init__(
        self,
        msg: str = http.HTTPStatus.SERVICE_UNAVAILABLE.phrase, /,
        *,
        code: const.BusinessCode = const.BusinessCode.SERVICE_UNAVAILABLE,
    ):
        super().__init__(
            msg,
            code=code,
            status_code=http.HTTPStatus.SERVICE_UNAVAILABLE.value,
        )
