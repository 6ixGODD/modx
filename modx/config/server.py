from __future__ import annotations

import os
import ssl
import typing as t

import pydantic as pydt

from modx import __description__, __title__, __version__


class ServerConfig(pydt.BaseModel):
    appname: t.Annotated[str, pydt.Field(max_length=50)] = __title__

    description: t.Annotated[str, pydt.Field(max_length=200)] = __description__

    version: t.Annotated[
        str,
        pydt.Field(
            ...,
            pattern=r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
                    r'(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
                    r'(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$',
        )
    ] = __version__  # Semantic versioning

    http_host: t.Annotated[
        str,
        pydt.Field(pattern=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
    ] = '0.0.0.0'

    http_port: t.Annotated[int, pydt.Field(ge=1, le=65535)] = 8000

    route_prefix: t.Annotated[
        str | None,
        pydt.Field(..., pattern=r"^\/[a-z0-9_\/]*$")
    ] = f'/v{version.split(".")[0]}'

    openapi_route: t.Annotated[
        str | None,
        pydt.Field(..., pattern=r"^\/[a-z0-9_\/]*$")
    ] = None

    debug: bool = True

    workers: t.Annotated[int, pydt.Field(ge=1, le=64)] = os.cpu_count() or 1

    ssl_keyfile: str | None = None

    ssl_certfile: str | None = None

    ssl_keyfile_password: str | None = None

    ssl_version: t.Annotated[
        int,
        pydt.Field(ge=1, le=6)
    ] = ssl.PROTOCOL_TLS_SERVER

    ssl_cert_reqs: t.Annotated[int, pydt.Field(ge=0, le=2)] = ssl.CERT_NONE

    ssl_ca_certs: str | None = None

    ssl_ciphers: str = "TLSv1"

    headers: t.Dict[str, str] = {
        "Server": f"{__title__}/{__version__}",
    }

    h11_max_incomplete_event_size: t.Annotated[
        int | None, pydt.Field(ge=0)
    ] = None
