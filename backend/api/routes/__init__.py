from __future__ import annotations

from fastapi import APIRouter

from backend.api.routes.health import router as health_router
from backend.api.routes.market import router as market_router
from backend.api.routes.options import router as options_router


def api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(market_router)
    router.include_router(options_router)
    return router
