from __future__ import annotations

from fastapi import APIRouter

from backend.api.routes.health import router as health_router


def api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    return router
