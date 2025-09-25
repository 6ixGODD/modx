import typing as t

from dependency_injector.wiring import inject
from dependency_injector.wiring import Provide
import fastapi

from modx.containers import Container
from modx.helpers.sse import SSEStream
from modx.interface.compat import ICompatInterface
from modx.interface.dtos.compat import ChatCompletion
from modx.interface.dtos.compat import ChatCompletionChunk
from modx.interface.dtos.compat import ChatCompletionParams
from modx.interface.dtos.compat import Model
from modx.interface.dtos.compat import ModelList

router = fastapi.APIRouter(prefix='/compat')


@router.post(
    '/chat/completions',
    response_model=t.Union[ChatCompletion, ChatCompletionChunk],
    status_code=fastapi.status.HTTP_200_OK,
)
@inject
async def chat_completions(
    body: ChatCompletionParams = fastapi.Body(...),
    compat: ICompatInterface = fastapi.Depends(Provide[Container.interfaces.compat]),
) -> t.Union[fastapi.responses.JSONResponse, fastapi.responses.StreamingResponse]:
    completion = await compat.chat_completions(body)
    if isinstance(completion, t.AsyncIterable):
        return fastapi.responses.StreamingResponse(
            SSEStream(completion),
            media_type='text/event-stream; charset=utf-8',
        )
    else:
        return fastapi.responses.JSONResponse(
            completion,
            media_type='application/json; charset=utf-8',
        )


@router.get(
    '/models',
    response_model=ModelList,
    status_code=fastapi.status.HTTP_200_OK,
)
@inject
async def list_models(
    compat: ICompatInterface = fastapi.Depends(Provide[Container.interfaces.compat]),
) -> fastapi.responses.JSONResponse:
    models = await compat.list_models()
    return fastapi.responses.JSONResponse(
        models,
        media_type='application/json; charset=utf-8',
    )


@router.get(
    '/models/{model_id}',
    response_model=Model,
    status_code=fastapi.status.HTTP_200_OK,
)
@inject
async def retrieve_model(
    model_id: str = fastapi.Path(..., min_length=1, max_length=100),
    compat: ICompatInterface = fastapi.Depends(Provide[Container.interfaces.compat]),
) -> fastapi.responses.JSONResponse:
    model = await compat.retrieve_model(model_id)
    return fastapi.responses.JSONResponse(
        model,
        media_type='application/json; charset=utf-8',
    )
