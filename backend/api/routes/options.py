from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Request

from backend.api.serializers import chain_response
from backend.core.container import Container

router = APIRouter(tags=["options"])


@router.get("/options/{symbol}", summary="Load option chain")
def load_option_chain(
    symbol: str,
    request: Request,
    expiration: date | None = None,
) -> dict[str, object]:
    container: Container = request.app.state.container
    chain = container.load_option_chain_use_case.execute(symbol, expiration)
    return chain_response(chain)
