from __future__ import annotations

from decimal import Decimal

from backend.domain.models import DealerPositioning, DealerPositioningInput
from backend.domain.ports import IDealerPositioningCalculator


class DealerPositioningCalculator(IDealerPositioningCalculator):
    """Deterministic institutional Dealer Positioning engine."""

    _NEUTRAL_GAMMA_THRESHOLD = Decimal("0.05")

    def calculate(self, positioning_input: DealerPositioningInput) -> DealerPositioning:
        aggregate = positioning_input.gamma_aggregate
        net_gamma = aggregate.net_gamma or aggregate.total_market_gamma
        total_abs_gamma = sum((item.absolute_gamma for item in aggregate.items), Decimal("0"))
        if total_abs_gamma == 0:
            total_abs_gamma = abs(aggregate.positive_gamma) + abs(aggregate.negative_gamma)
        gamma_ratio = abs(net_gamma) / total_abs_gamma if total_abs_gamma else Decimal("0")

        dealer_state = self._dealer_state(net_gamma, gamma_ratio)
        hedging_pressure = min(Decimal("1"), gamma_ratio)
        dealer_bias = self._dealer_bias(positioning_input, dealer_state)
        expected_volatility = self._expected_volatility(dealer_state, hedging_pressure)
        liquidity_regime = self._liquidity_regime(dealer_state, hedging_pressure)
        confidence_score = self._confidence_score(positioning_input, hedging_pressure)

        return DealerPositioning(
            symbol=aggregate.symbol,
            as_of=aggregate.as_of,
            dealer_state=dealer_state,
            dealer_bias=dealer_bias,
            hedging_pressure=hedging_pressure,
            expected_volatility=expected_volatility,
            liquidity_regime=liquidity_regime,
            confidence_score=confidence_score,
        )

    def _dealer_state(self, net_gamma: Decimal, gamma_ratio: Decimal) -> str:
        if gamma_ratio <= self._NEUTRAL_GAMMA_THRESHOLD or net_gamma == 0:
            return "Neutral"
        if net_gamma > 0:
            return "Long Gamma"
        return "Short Gamma"

    def _dealer_bias(self, positioning_input: DealerPositioningInput, dealer_state: str) -> str:
        call_wall = positioning_input.call_wall
        put_wall = positioning_input.put_wall
        max_pain = positioning_input.max_pain
        gamma_flip = positioning_input.gamma_flip
        bullish_votes = 0
        bearish_votes = 0

        if call_wall is not None and put_wall is not None:
            if abs(call_wall.gamma) > abs(put_wall.gamma):
                bullish_votes += 1
            elif abs(put_wall.gamma) > abs(call_wall.gamma):
                bearish_votes += 1
        elif call_wall is not None:
            bullish_votes += 1
        elif put_wall is not None:
            bearish_votes += 1

        if gamma_flip.flip_found and gamma_flip.gamma_flip_price is not None:
            if max_pain.max_pain_strike > gamma_flip.gamma_flip_price:
                bullish_votes += 1
            elif max_pain.max_pain_strike < gamma_flip.gamma_flip_price:
                bearish_votes += 1

        if dealer_state == "Long Gamma":
            bullish_votes += 2
        elif dealer_state == "Short Gamma":
            bearish_votes += 3

        if bullish_votes > bearish_votes:
            return "Bullish"
        if bearish_votes > bullish_votes:
            return "Bearish"
        return "Neutral"

    def _expected_volatility(self, dealer_state: str, hedging_pressure: Decimal) -> str:
        if dealer_state == "Short Gamma" and hedging_pressure >= Decimal("0.50"):
            return "High"
        if dealer_state == "Long Gamma" and hedging_pressure >= Decimal("0.50"):
            return "Low"
        return "Normal"

    def _liquidity_regime(self, dealer_state: str, hedging_pressure: Decimal) -> str:
        if dealer_state == "Short Gamma" and hedging_pressure >= Decimal("0.66"):
            return "Thin"
        if dealer_state == "Long Gamma" and hedging_pressure >= Decimal("0.66"):
            return "Deep"
        return "Balanced"

    def _confidence_score(
        self, positioning_input: DealerPositioningInput, hedging_pressure: Decimal
    ) -> Decimal:
        scores = [hedging_pressure]
        if positioning_input.gamma_flip.flip_found:
            scores.append(Decimal("1"))
        if positioning_input.call_wall is not None:
            scores.append(positioning_input.call_wall.confidence_score)
        if positioning_input.put_wall is not None:
            scores.append(positioning_input.put_wall.confidence_score)
        if positioning_input.gamma_exposure:
            scores.append(Decimal("1"))
        return min(Decimal("1"), sum(scores, Decimal("0")) / Decimal(len(scores)))


class FakeDealerPositioningCalculator(DealerPositioningCalculator):
    """Fake adapter wired by the application container for deterministic tests."""
