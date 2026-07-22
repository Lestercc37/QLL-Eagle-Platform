from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import text

from backend.core.container import Container

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service health check")
def health_check(request: Request) -> dict[str, str]:
    container: Container = request.app.state.container
    settings = container.settings
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.version,
    }


@router.get("/health/db", summary="Database health check")
async def database_health_check(request: Request) -> dict[str, str]:
    container: Container = request.app.state.container
    async with container.session_factory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
