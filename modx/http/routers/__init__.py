from __future__ import annotations

import fastapi

router = fastapi.APIRouter()
router.add_api_route('/ping', lambda: 'pong', methods={'GET'})


def register_routers(app: fastapi.FastAPI, prefix: str | None) -> None:
    from modx.http.routers import compat
    router.include_router(compat.router)
    app.include_router(router, prefix=prefix or '')
