from __future__ import annotations

import logging

import fastapi
import uvicorn

from modx.config import ModXConfig
from modx.context import Context
from modx.http import exc_handler, middlewares, routers
from modx.http.lifespan import Lifespan
from modx.interface.auth import IAuthInterface
from modx.logger import Logger


class HTTPServer:
    def __init__(
        self,
        config: ModXConfig,
        logger: Logger,
        context: Context,
        lifespan: Lifespan,
        auth_interface: IAuthInterface
    ):
        self.config = config
        self.logger = logger
        self.context = context
        self.lifespan = lifespan
        self.app = fastapi.FastAPI(
            title=self.config.server.appname,
            version=self.config.server.version,
            description=self.config.server.description,
            lifespan=self.lifespan,
            redoc_url=None,
            docs_url=None,
            openapi_url=self.config.server.openapi_route,
            debug=self.config.server.debug,
        )
        routers.register_routers(
            self.app,
            prefix=self.config.server.route_prefix
        )
        exc_handler.register_exception_handlers(self.app)
        middlewares.register_middleware(
            self.app,
            middleware_config=self.config.middleware,
            prom_config=self.config.prometheus,
            logger=self.logger,
            context=self.context,
            auth_interface=auth_interface
        )

    def run(self):
        headers = ()
        for k, v in self.config.server.headers.items():
            headers += ((k, str(v)),)

        uvicorn.run(
            self.app,
            host=self.config.server.http_host,
            port=self.config.server.http_port,
            log_level=(logging.DEBUG
                       if self.config.server.debug else logging.FATAL + 1),
            reload=False,
            # workers=self.config.server.workers,
            ssl_keyfile=self.config.server.ssl_keyfile,
            ssl_certfile=self.config.server.ssl_certfile,
            ssl_keyfile_password=self.config.server.ssl_keyfile_password,
            ssl_version=self.config.server.ssl_version,
            ssl_cert_reqs=self.config.server.ssl_cert_reqs,
            ssl_ca_certs=self.config.server.ssl_ca_certs,
            ssl_ciphers=self.config.server.ssl_ciphers,
            headers=headers,
            h11_max_incomplete_event_size=(
                self.config.server.h11_max_incomplete_event_size
            )
        )
