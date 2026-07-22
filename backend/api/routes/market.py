from __future__ import annotations

from fastapi import APIRouter, Request

from backend.api.serializers import market_response
from backend.core.container import Container

router = APIRouter(tags=["market"])


@router.get("/market/{symbol}", summary="Get market snapshot")
def get_market_snapshot(symbol: str, request: Request) -> dict[str, object]:
    container: Container = request.app.state.container
    snapshot = container.get_market_snapshot_use_case.execute(symbol)
    return market_response(snapshot)
