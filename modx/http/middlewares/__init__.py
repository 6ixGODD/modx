from __future__ import annotations

import fastapi
import starlette.types as types

from modx.config.middleware import MiddlewareConfig
from modx.config.prometheus import PrometheusConfig
from modx.context import Context
from modx.interface.auth import IAuthInterface
from modx.logger import Logger


class BaseMiddleware:
    def __init__(self, app: types.ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: types.Scope,
        receive: types.Receive,
        send: types.Send
    ) -> None:
        await self.app(scope, receive, send)


def register_middleware(
    app: fastapi.FastAPI,
    middleware_config: MiddlewareConfig,
    prom_config: PrometheusConfig,
    context: Context,
    logger: Logger,
    auth_interface: IAuthInterface
) -> None:
    from modx.http.middlewares.prometheus import PrometheusMiddleware
    app.add_middleware(
        PrometheusMiddleware,  # type: ignore[arg-type]
        logger=logger,
        context=context,
        config=prom_config
    )

    from modx.http.middlewares.logging import LoggingMiddleware
    app.add_middleware(
        LoggingMiddleware,  # type: ignore[arg-type]
        logger=logger,
        context=context,
        config=middleware_config.logging,
    )

    from modx.http.middlewares.auth import AuthMiddleware
    app.add_middleware(
        AuthMiddleware,  # type: ignore[arg-type]
        logger=logger,
        context=context,
        config=middleware_config.auth,
        auth_interface=auth_interface,
    )

    if middleware_config.security.enabled:
        from modx.http.middlewares.security import SecurityMiddleware
        app.add_middleware(
            SecurityMiddleware,  # type: ignore[arg-type]
            logger=logger,
            context=context,
            config=middleware_config.security
        )

    if middleware_config.gzip.enabled:
        from fastapi.middleware.gzip import GZipMiddleware
        app.add_middleware(
            GZipMiddleware,  # type: ignore[arg-type]
            minimum_size=middleware_config.gzip.minimum_size,
            compresslevel=middleware_config.gzip.compresslevel
        )

    if middleware_config.cors.enabled:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,  # type: ignore[arg-type]
            allow_origins=middleware_config.cors.allow_origins,
            allow_credentials=middleware_config.cors.allow_credentials,
            allow_methods=middleware_config.cors.allow_methods,
            allow_headers=middleware_config.cors.allow_headers,
            allow_origin_regex=middleware_config.cors.allow_origin_regex,
            expose_headers=middleware_config.cors.expose_headers,
            max_age=middleware_config.cors.max_age
        )
