from __future__ import annotations

import os
import typing as t

import pydantic as pydt
import pydantic_settings as ps

import modx.exceptions as exc
from modx.config.cache import CacheConfig
from modx.config.chatbot import ChatbotConfig
from modx.config.http_client import HttpClientConfig
from modx.config.logging import LoggingConfig
from modx.config.middleware import MiddlewareConfig
from modx.config.prometheus import PrometheusConfig
from modx.config.server import ServerConfig


class ModXConfig(ps.BaseSettings):
    model_config: t.ClassVar[pydt.ConfigDict] = ps.SettingsConfigDict(
        env_prefix='MODX__',
        validate_default=False,
        env_nested_delimiter='__',
        env_file='.env',
        extra='allow'
    )

    server: ServerConfig = ServerConfig()
    chatbot: ChatbotConfig = ChatbotConfig()
    logging: LoggingConfig = LoggingConfig()
    middleware: MiddlewareConfig = MiddlewareConfig()
    prometheus: PrometheusConfig = PrometheusConfig()
    cache: CacheConfig = CacheConfig()
    http_client: HttpClientConfig = HttpClientConfig()

    # TODO: It is a temporary solution. NOT production-ready.
    #  It is not secure and only ensures flexibility during development.
    #  DONT USE IT IN PRODUCTION
    keys_file: str = '.keys'
    models_file: str = '.models.json'

    @classmethod
    def from_yaml(cls, fpath: t.AnyStr | os.PathLike[t.AnyStr]) -> t.Self:
        try:
            import yaml
            with open(fpath, 'r') as f:
                data = yaml.safe_load(f)
            return cls.model_validate(data, strict=True)
        except ImportError:
            raise exc.RequiredModuleNotFoundException(
                '`yaml` module is required to load configuration from YAML '
                'files. Please install it using `pip install pyyaml`.'
            )

    @classmethod
    def from_json(cls, fpath: t.AnyStr | os.PathLike[t.AnyStr]) -> t.Self:
        import json
        with open(fpath, 'r') as f:
            data = json.load(f)
        return cls.model_validate(data, strict=True)


config = ModXConfig()


def set(c: ModXConfig) -> None:
    global config
    config = c


def get() -> ModXConfig:
    return config
