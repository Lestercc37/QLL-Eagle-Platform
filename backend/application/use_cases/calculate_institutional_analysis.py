from __future__ import annotations

from decimal import Decimal

from backend.domain.models import (
    DealerPositioningInput,
    InstitutionalAnalysis,
    MarketSnapshot,
    OptionChain,
    SCHEMA_VERSION,
    utc_now,
)

from backend.application.use_cases.calculate_dealer_positioning import (
    CalculateDealerPositioningUseCase,
)
from backend.application.use_cases.calculate_gamma_aggregate import CalculateGammaAggregateUseCase
from backend.application.use_cases.calculate_gamma_exposure import CalculateGammaExposureUseCase
from backend.application.use_cases.calculate_gamma_flip import CalculateGammaFlipUseCase
from backend.application.use_cases.calculate_greeks import CalculateGreeksUseCase
from backend.application.use_cases.calculate_max_pain import CalculateMaxPainUseCase
from backend.application.use_cases.calculate_walls import CalculateWallsUseCase
from backend.application.use_cases.market_snapshot import GetMarketSnapshotUseCase


class CalculateInstitutionalAnalysisUseCase:
    """Run all institutional engines and compose a complete analysis."""

    def __init__(
        self,
        get_market_snapshot_use_case: GetMarketSnapshotUseCase,
        calculate_greeks_use_case: CalculateGreeksUseCase,
        calculate_gamma_exposure_use_case: CalculateGammaExposureUseCase,
        calculate_gamma_aggregate_use_case: CalculateGammaAggregateUseCase,
        calculate_gamma_flip_use_case: CalculateGammaFlipUseCase,
        calculate_walls_use_case: CalculateWallsUseCase,
        calculate_max_pain_use_case: CalculateMaxPainUseCase,
        calculate_dealer_positioning_use_case: CalculateDealerPositioningUseCase,
    ) -> None:
        self._get_market_snapshot_use_case = get_market_snapshot_use_case
        self._calculate_greeks_use_case = calculate_greeks_use_case
        self._calculate_gamma_exposure_use_case = calculate_gamma_exposure_use_case
        self._calculate_gamma_aggregate_use_case = calculate_gamma_aggregate_use_case
        self._calculate_gamma_flip_use_case = calculate_gamma_flip_use_case
        self._calculate_walls_use_case = calculate_walls_use_case
        self._calculate_max_pain_use_case = calculate_max_pain_use_case
        self._calculate_dealer_positioning_use_case = calculate_dealer_positioning_use_case

    def execute(self, chain: OptionChain) -> InstitutionalAnalysis:
        market_snapshot = self._get_market_snapshot_use_case.execute(chain.symbol)
        option_chain = self._calculate_greeks_use_case.execute(chain)
        gamma_exposure = self._calculate_gamma_exposure_use_case.execute(option_chain)
        gamma_aggregate = self._calculate_gamma_aggregate_use_case.execute(option_chain)
        gamma_flip = self._calculate_gamma_flip_use_case.execute(gamma_aggregate)
        walls = self._calculate_walls_use_case.execute(gamma_aggregate)
        max_pain = self._calculate_max_pain_use_case.execute(option_chain)
        dealer_positioning = self._calculate_dealer_positioning_use_case.execute(
            DealerPositioningInput(
                gamma_exposure=gamma_exposure,
                gamma_aggregate=gamma_aggregate,
                gamma_flip=gamma_flip,
                call_wall=walls.call_wall,
                put_wall=walls.put_wall,
                max_pain=max_pain,
            )
        )
        return InstitutionalAnalysis(
            market_snapshot=_align_market_snapshot(market_snapshot, option_chain),
            option_chain=option_chain,
            gamma_exposure=gamma_exposure,
            gamma_aggregate=gamma_aggregate,
            gamma_flip=gamma_flip,
            walls=walls,
            max_pain=max_pain,
            dealer_positioning=dealer_positioning,
            overall_bias=dealer_positioning.dealer_bias,
            confidence_score=_confidence_score(dealer_positioning.confidence_score, walls),
            market_regime=_market_regime(dealer_positioning.expected_volatility),
            timestamp=utc_now(),
            schema_version=SCHEMA_VERSION,
        )


def _align_market_snapshot(snapshot: MarketSnapshot, chain: OptionChain) -> MarketSnapshot:
    if snapshot.symbol == chain.symbol:
        return snapshot
    return MarketSnapshot(
        symbol=chain.symbol,
        as_of=snapshot.as_of,
        price=snapshot.price,
        volume=snapshot.volume,
        gamma=snapshot.gamma,
        recent_flow=snapshot.recent_flow,
        state=snapshot.state,
    )


def _confidence_score(dealer_confidence: Decimal, walls) -> Decimal:  # noqa: ANN001
    wall_scores = [
        wall.confidence_score for wall in (walls.call_wall, walls.put_wall) if wall is not None
    ]
    if not wall_scores:
        return dealer_confidence
    return (dealer_confidence + sum(wall_scores, Decimal("0"))) / Decimal(len(wall_scores) + 1)


def _market_regime(expected_volatility: str) -> str:
    return {
        "High": "High Volatility",
        "Low": "Low Volatility",
    }.get(expected_volatility, "Normal")
