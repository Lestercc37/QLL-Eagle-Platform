from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Request

from backend.api.schemas import OptionChainRequest
from backend.api.serializers import (
    chain_response,
    gamma_exposure_response,
    greeks_chain_response,
)
from backend.core.container import Container
from backend.domain.models import DomainError, OptionChain

OPTION_CHAIN_REQUEST_EXAMPLE = {
    "symbol": "SPY",
    "as_of": "2026-01-15T14:30:00Z",
    "contracts": [
        {
            "occ_symbol": "SPY260220C00540000",
            "underlying": "SPY",
            "strike": 540,
            "expiration": "2026-02-20",
            "type": "call",
            "bid": 1.2,
            "ask": 1.25,
            "last": 1.22,
            "iv": 0.18,
            "delta": 0,
            "gamma": 0.03,
            "theta": -0.015,
            "vega": 0.12,
            "open_interest": 8000,
            "volume": 3400,
        }
    ],
}

OptionChainBody = Annotated[
    OptionChainRequest,
    Body(
        openapi_examples={
            "option_chain": {
                "summary": "Option chain request",
                "value": OPTION_CHAIN_REQUEST_EXAMPLE,
            }
        },
    ),
]

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
def calculate_greeks(payload: OptionChainBody, request: Request) -> dict[str, object]:
    container: Container = request.app.state.container
    chain = _chain_from_request(payload)
    enriched_chain = container.calculate_greeks_use_case.execute(chain)
    return greeks_chain_response(enriched_chain)


@router.post(
    "/options/gamma-exposure",
    summary="Calculate deterministic Gamma Exposure for an option chain",
)
def calculate_gamma_exposure(payload: OptionChainBody, request: Request) -> dict[str, object]:
    container: Container = request.app.state.container
    chain = _chain_from_request(payload)
    gamma_exposures = container.calculate_gamma_exposure_use_case.execute(chain)
    return gamma_exposure_response(gamma_exposures)


def _chain_from_request(payload: OptionChainRequest) -> OptionChain:
    try:
        return payload.to_domain()
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
