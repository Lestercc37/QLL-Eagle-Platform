from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Request

from backend.api.serializers import (
    chain_response,
    gamma_exposure_response,
    greeks_chain_response,
    option_chain_from_payload,
)
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


@router.post("/options/greeks", summary="Calculate deterministic Greeks for an option chain")
def calculate_greeks(payload: dict[str, Any], request: Request) -> dict[str, object]:
    container: Container = request.app.state.container
    chain = option_chain_from_payload(payload)
    enriched_chain = container.calculate_greeks_use_case.execute(chain)
    return greeks_chain_response(enriched_chain)


@router.post(
    "/options/gamma-exposure",
    summary="Calculate deterministic Gamma Exposure for an option chain",
)
def calculate_gamma_exposure(payload: dict[str, Any], request: Request) -> dict[str, object]:
    container: Container = request.app.state.container
    chain = option_chain_from_payload(payload)
    gamma_exposures = container.calculate_gamma_exposure_use_case.execute(chain)
    return gamma_exposure_response(gamma_exposures)
