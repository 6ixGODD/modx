from __future__ import annotations

import typing as t

from modx.interface import BaseInterface
from modx.interface.dtos.compat import (
    ChatCompletionParams,
    CompatResponse,
    Model,
    ModelList,
)
from modx.logger import Logger
from modx.service.compat import ICompatService


@t.runtime_checkable
class ICompatInterface(t.Protocol):
    async def chat_completions(
        self,
        params: ChatCompletionParams
    ) -> CompatResponse: ...

    async def list_models(self) -> ModelList: ...

    async def retrieve_model(self, model_id: str) -> Model: ...


class CompatInterface(BaseInterface):
    def __init__(
        self,
        *,
        logger: Logger,
        compat_service: ICompatService
    ):
        super().__init__(logger)
        self.compat_service = compat_service

    async def chat_completions(
        self,
        params: ChatCompletionParams
    ) -> CompatResponse:
        pass

    async def list_models(self) -> ModelList:
        pass

    async def retrieve_model(self, model_id: str) -> Model:
        pass
