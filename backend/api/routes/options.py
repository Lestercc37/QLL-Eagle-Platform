from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Request

from backend.api.schemas import (
    DealerPositioningRequest,
    DealerPositioningResponse,
    GammaAggregateResponse,
    GammaExposureResponse,
    GammaFlipRequest,
    GammaFlipResponse,
    InstitutionalAnalysisResponse,
    MaxPainResponse,
    WallsResponse,
    GreeksResponse,
    OptionChainRequest,
    OptionChainResponse,
)
from backend.api.serializers import (
    chain_response,
    dealer_positioning_response,
    gamma_aggregate_response,
    gamma_exposure_response,
    gamma_flip_response,
    institutional_analysis_response,
    max_pain_response,
    walls_response,
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

GAMMA_AGGREGATE_REQUEST_EXAMPLE = {
    "symbol": "SPY",
    "as_of": "2026-01-15T14:30:00Z",
    "items": [
        {
            "strike": 540,
            "total_gamma_exposure": 390,
            "call_gamma_exposure": 240,
            "put_gamma_exposure": 150,
            "net_gamma": 90,
            "contract_count": 2,
            "absolute_gamma": 90,
        },
        {
            "strike": 545,
            "total_gamma_exposure": 210,
            "call_gamma_exposure": 200,
            "put_gamma_exposure": 10,
            "net_gamma": -10,
            "contract_count": 2,
            "absolute_gamma": 10,
        },
    ],
}

DEALER_POSITIONING_REQUEST_EXAMPLE = {
    "symbol": "SPY",
    "as_of": "2026-01-15T14:30:00Z",
    "gamma_exposure": [
        {
            "occ_symbol": "SPY260220C00540000",
            "strike": 540,
            "contract_type": "call",
            "expiration": "2026-02-20",
            "gamma": 0.03,
            "open_interest": 8000,
            "dealer_gamma_exposure": 90,
            "sign": 1,
        }
    ],
    "gamma_aggregate": GAMMA_AGGREGATE_REQUEST_EXAMPLE,
    "call_wall": {
        "strike": 545,
        "gamma": 200,
        "open_interest": 6000,
        "volume": 4200,
        "confidence_score": 0.8,
    },
    "put_wall": {
        "strike": 530,
        "gamma": -100,
        "open_interest": 5000,
        "volume": 3600,
        "confidence_score": 0.4,
    },
    "max_pain": {
        "schema_version": 1,
        "symbol": "SPY",
        "as_of": "2026-01-15T14:30:00Z",
        "max_pain_strike": 540,
        "total_call_pain": 1000,
        "total_put_pain": 900,
        "total_pain": 1900,
        "ranking": [],
    },
}

GammaFlipBody = Annotated[
    GammaFlipRequest,
    Body(
        openapi_examples={
            "gamma_aggregate": {
                "summary": "Gamma Aggregate request",
                "value": GAMMA_AGGREGATE_REQUEST_EXAMPLE,
            }
        },
    ),
]

DealerPositioningBody = Annotated[
    DealerPositioningRequest,
    Body(
        description=(
            "Dealer Positioning can calculate gamma_flip from gamma_aggregate when "
            "gamma_flip is omitted. If gamma_flip.gamma_flip_price is provided, it must be "
            "greater than zero."
        ),
        openapi_examples={
            "dealer_positioning": {
                "summary": "Dealer Positioning request with calculated gamma_flip",
                "value": DEALER_POSITIONING_REQUEST_EXAMPLE,
            }
        },
    ),
]

router = APIRouter(tags=["options"])


@router.get(
    "/options/{symbol}",
    response_model=OptionChainResponse,
    summary="Load option chain",
)
def load_option_chain(
    symbol: str,
    request: Request,
    expiration: date | None = None,
) -> OptionChainResponse:
    container: Container = request.app.state.container
    chain = container.load_option_chain_use_case.execute(symbol, expiration)
    return OptionChainResponse.model_validate(chain_response(chain))


@router.post(
    "/options/greeks",
    response_model=GreeksResponse,
    summary="Calculate deterministic Greeks for an option chain",
)
def calculate_greeks(payload: OptionChainBody, request: Request) -> GreeksResponse:
    print(
        "calculate_greeks runtime evidence:",
        {
            "__file__": __file__,
            "co_firstlineno": calculate_greeks.__code__.co_firstlineno,
            "payload_type": type(payload),
            "option_chain_from_payload_exists": "option_chain_from_payload" in globals(),
            "calculate_greeks_calls_option_chain_from_payload": "option_chain_from_payload"
            in calculate_greeks.__code__.co_names,
        },
        flush=True,
    )
    container: Container = request.app.state.container
    chain = _chain_from_request(payload)
    enriched_chain = container.calculate_greeks_use_case.execute(chain)
    return GreeksResponse.model_validate(greeks_chain_response(enriched_chain))


@router.post(
    "/options/gamma-aggregate",
    response_model=GammaAggregateResponse,
    summary="Calculate Gamma Aggregate by strike for an option chain",
)
def calculate_gamma_aggregate(payload: OptionChainBody, request: Request) -> GammaAggregateResponse:
    container: Container = request.app.state.container
    chain = _chain_from_request(payload)
    gamma_aggregate = container.calculate_gamma_aggregate_use_case.execute(chain)
    return GammaAggregateResponse.model_validate(gamma_aggregate_response(gamma_aggregate))


@router.post(
    "/options/gamma-exposure",
    response_model=GammaExposureResponse,
    summary="Calculate deterministic Gamma Exposure for an option chain",
)
def calculate_gamma_exposure(payload: OptionChainBody, request: Request) -> GammaExposureResponse:
    container: Container = request.app.state.container
    chain = _chain_from_request(payload)
    gamma_exposures = container.calculate_gamma_exposure_use_case.execute(chain)
    return GammaExposureResponse.model_validate(gamma_exposure_response(gamma_exposures))


@router.post(
    "/options/max-pain",
    response_model=MaxPainResponse,
    summary="Calculate institutional Max Pain for an option chain",
)
def calculate_max_pain(payload: OptionChainBody, request: Request) -> MaxPainResponse:
    container: Container = request.app.state.container
    chain = _chain_from_request(payload)
    max_pain = container.calculate_max_pain_use_case.execute(chain)
    return MaxPainResponse.model_validate(max_pain_response(max_pain))


@router.post(
    "/options/walls",
    response_model=WallsResponse,
    summary="Calculate institutional Call Wall and Put Wall from Gamma Aggregate",
)
def calculate_walls(payload: GammaFlipBody, request: Request) -> WallsResponse:
    container: Container = request.app.state.container
    aggregate = _gamma_aggregate_from_request(payload)
    walls = container.calculate_walls_use_case.execute(aggregate)
    return WallsResponse.model_validate(walls_response(walls))


@router.post(
    "/options/dealer-positioning",
    response_model=DealerPositioningResponse,
    summary="Calculate institutional Dealer Positioning",
)
def calculate_dealer_positioning(
    payload: DealerPositioningBody, request: Request
) -> DealerPositioningResponse:
    container: Container = request.app.state.container
    aggregate = _gamma_aggregate_from_request(payload.gamma_aggregate)
    gamma_flip = payload.gamma_flip.to_domain() if payload.gamma_flip is not None else None
    if gamma_flip is None or gamma_flip.gamma_flip_price is None:
        try:
            gamma_flip = container.calculate_gamma_flip_use_case.execute(aggregate)
        except DomainError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    positioning_input = _dealer_positioning_from_request(payload, gamma_flip)
    positioning = container.calculate_dealer_positioning_use_case.execute(positioning_input)
    return DealerPositioningResponse.model_validate(dealer_positioning_response(positioning))


@router.post(
    "/options/gamma-flip",
    response_model=GammaFlipResponse,
    summary="Calculate Gamma Flip from Gamma Aggregate",
)
def calculate_gamma_flip(payload: GammaFlipBody, request: Request) -> GammaFlipResponse:
    container: Container = request.app.state.container
    aggregate = _gamma_aggregate_from_request(payload)
    gamma_flip = container.calculate_gamma_flip_use_case.execute(aggregate)
    return GammaFlipResponse.model_validate(gamma_flip_response(gamma_flip))


@router.post(
    "/options/institutional-analysis",
    response_model=InstitutionalAnalysisResponse,
    summary="Run the complete institutional options analysis engine",
)
def calculate_institutional_analysis(
    payload: OptionChainBody, request: Request
) -> InstitutionalAnalysisResponse:
    container: Container = request.app.state.container
    chain = _chain_from_request(payload)
    analysis = container.calculate_institutional_analysis_use_case.execute(chain)
    return InstitutionalAnalysisResponse.model_validate(
        institutional_analysis_response(analysis)
    )


def _chain_from_request(payload: OptionChainRequest) -> OptionChain:
    try:
        return payload.to_domain()
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _gamma_aggregate_from_request(payload: GammaFlipRequest):
    try:
        return payload.to_domain()
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _dealer_positioning_from_request(payload: DealerPositioningRequest, gamma_flip=None):
    try:
        return payload.to_domain(gamma_flip=gamma_flip)
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
