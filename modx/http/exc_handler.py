from __future__ import annotations

import fastapi
import starlette.exceptions as st_exc

from modx import constants
from modx import exceptions
from modx.interface.dtos import ErrorResponse


def register_exception_handlers(app: fastapi.FastAPI):

    @app.exception_handler(exceptions.RuntimeException)
    async def handle_runtime_exception(
            _: fastapi.Request, e: exceptions.RuntimeException) -> fastapi.responses.JSONResponse:
        return fastapi.responses.JSONResponse(status_code=e.status_code,
                                              content=ErrorResponse(code=e.code,
                                                                    data=e.details).to_dict())

    @app.exception_handler(fastapi.exceptions.RequestValidationError)
    async def handle_request_validation_error(
            _: fastapi.Request,
            e: fastapi.exceptions.RequestValidationError) -> fastapi.responses.JSONResponse:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(code=constants.BusinessCode.INVALID_PARAMS,
                                  data=exceptions.ExceptionDetails(message=e.errors())).to_dict())

    @app.exception_handler(st_exc.HTTPException)
    async def handle_http_exception(_: fastapi.Request,
                                    e: st_exc.HTTPException) -> fastapi.responses.JSONResponse:
        return fastapi.responses.JSONResponse(
            status_code=e.status_code,
            content=ErrorResponse(code=constants.BusinessCode.from_http_status(e.status_code),
                                  data=exceptions.ExceptionDetails(message=e.detail)).to_dict())

    @app.exception_handler(Exception)
    async def handle_exception(_: fastapi.Request, _e: Exception) -> fastapi.responses.JSONResponse:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse().to_dict())
