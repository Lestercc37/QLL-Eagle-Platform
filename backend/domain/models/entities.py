from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum


SCHEMA_VERSION = 1


class ContractType(StrEnum):
    CALL = "call"
    PUT = "put"


class UnderlyingKind(StrEnum):
    EQUITY = "equity"
    INDEX = "index"


class FlowEventType(StrEnum):
    SWEEP = "sweep"
    BLOCK = "block"
    UNUSUAL = "unusual"


class AggressorSide(StrEnum):
    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Underlying:
    symbol: str
    kind: UnderlyingKind
    is_priority: bool = False


@dataclass(frozen=True, slots=True)
class Greeks:
    delta: Decimal
    gamma: Decimal
    theta: Decimal | None = None
    vega: Decimal | None = None


@dataclass(frozen=True, slots=True)
class Expiration:
    expiration: date
    as_of: date

    @property
    def dte(self) -> int:
        return max((self.expiration - self.as_of).days, 0)


@dataclass(frozen=True, slots=True)
class OptionContract:
    underlying: str
    strike: Decimal
    expiration: date
    contract_type: ContractType
    occ_symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    open_interest: int
    iv: Decimal
    greeks: Greeks


@dataclass(frozen=True, slots=True)
class OptionChain:
    symbol: str
    as_of: datetime
    contracts: tuple[OptionContract, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class GammaAggregate:
    symbol: str
    as_of: datetime
    gamma_flip: Decimal
    call_wall: Decimal
    put_wall: Decimal
    max_pain: Decimal
    net_gamma: Decimal
    dealer_gamma_notional: Decimal

    @property
    def dealer_position(self) -> str:
        return dealer_position(self.net_gamma)


@dataclass(frozen=True, slots=True)
class MarketPrice:
    symbol: str
    as_of: datetime
    price: Decimal
    volume: int


@dataclass(frozen=True, slots=True)
class FlowEvent:
    symbol: str
    occ_symbol: str
    as_of: datetime
    event_type: FlowEventType
    premium: Decimal
    size: int
    aggressor_side: AggressorSide


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    symbol: str
    as_of: datetime
    price: Decimal
    volume: int
    gamma: GammaAggregate | None = None
    recent_flow: tuple[FlowEvent, ...] = field(default_factory=tuple)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def dealer_position(net_gamma: Decimal) -> str:
    return "long_gamma" if net_gamma >= 0 else "short_gamma"
