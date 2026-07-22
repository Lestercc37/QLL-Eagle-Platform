from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum


SCHEMA_VERSION = 1


class DomainError(ValueError):
    """Base exception for pure domain invariant violations."""


class InvalidStrikeError(DomainError):
    """Raised when an option strike is not strictly positive."""


class InvalidExpirationError(DomainError):
    """Raised when an expiration date violates domain invariants."""


class InvalidOptionError(DomainError):
    """Raised when option contract, quote, or Greek invariants fail."""


class ContractType(StrEnum):
    CALL = "call"
    PUT = "put"


OptionType = ContractType


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


class MarketState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"
    UNKNOWN = "unknown"


class UnderlyingKind(StrEnum):
    EQUITY = "equity"
    INDEX = "index"


class FlowEventType(StrEnum):
    SWEEP = "sweep"
    BLOCK = "block"
    UNUSUAL = "unusual"


AggressorSide = Side


@dataclass(frozen=True, slots=True)
class Underlying:
    symbol: str
    kind: UnderlyingKind
    is_priority: bool = False

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise InvalidOptionError("underlying symbol is required")
        object.__setattr__(self, "symbol", self.symbol.upper())


@dataclass(frozen=True, slots=True)
class OptionGreeks:
    delta: Decimal
    gamma: Decimal
    theta: Decimal | None = None
    vega: Decimal | None = None

    def __post_init__(self) -> None:
        _ensure_finite_decimal(self.delta, InvalidOptionError, "delta")
        _ensure_finite_decimal(self.gamma, InvalidOptionError, "gamma")
        if not Decimal("-1") <= self.delta <= Decimal("1"):
            raise InvalidOptionError("delta must be between -1 and 1")
        if self.theta is not None:
            _ensure_finite_decimal(self.theta, InvalidOptionError, "theta")
        if self.vega is not None:
            _ensure_finite_decimal(self.vega, InvalidOptionError, "vega")


Greeks = OptionGreeks


@dataclass(frozen=True, slots=True)
class Expiration:
    expiration: date
    as_of: date

    def __post_init__(self) -> None:
        if not isinstance(self.expiration, date) or not isinstance(self.as_of, date):
            raise InvalidExpirationError("expiration and as_of must be dates")
        if self.expiration < self.as_of:
            raise InvalidExpirationError("expiration cannot be before as_of")

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
    greeks: OptionGreeks

    def __post_init__(self) -> None:
        if not self.underlying or not self.underlying.strip():
            raise InvalidOptionError("underlying is required")
        object.__setattr__(self, "underlying", self.underlying.upper())
        _ensure_positive_decimal(self.strike, InvalidStrikeError, "strike")
        if not isinstance(self.expiration, date):
            raise InvalidExpirationError("expiration must be a date")
        if not self.occ_symbol:
            raise InvalidOptionError("occ_symbol is required")
        for name in ("bid", "ask", "last", "iv"):
            _ensure_finite_decimal(getattr(self, name), InvalidOptionError, name)
        if self.bid < 0 or self.ask < 0 or self.last < 0 or self.iv < 0:
            raise InvalidOptionError("quote monetary values and iv cannot be negative")
        if self.ask < self.bid:
            raise InvalidOptionError("ask cannot be lower than bid")
        if self.volume < 0 or self.open_interest < 0:
            raise InvalidOptionError("volume and open_interest cannot be negative")


@dataclass(frozen=True, slots=True)
class OptionChain:
    symbol: str
    as_of: datetime
    contracts: tuple[OptionContract, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise InvalidOptionError("chain symbol is required")
        object.__setattr__(self, "symbol", self.symbol.upper())


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

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise InvalidOptionError("gamma aggregate symbol is required")
        object.__setattr__(self, "symbol", self.symbol.upper())
        for name in (
            "gamma_flip",
            "call_wall",
            "put_wall",
            "max_pain",
            "net_gamma",
            "dealer_gamma_notional",
        ):
            _ensure_finite_decimal(getattr(self, name), InvalidOptionError, name)

    @property
    def dealer_position(self) -> str:
        return dealer_position(self.net_gamma)


@dataclass(frozen=True, slots=True)
class MarketPrice:
    symbol: str
    as_of: datetime
    price: Decimal
    volume: int

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise InvalidOptionError("market price symbol is required")
        object.__setattr__(self, "symbol", self.symbol.upper())
        _ensure_finite_decimal(self.price, InvalidOptionError, "price")
        if self.price < 0 or self.volume < 0:
            raise InvalidOptionError("price and volume cannot be negative")


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
class OptionSnapshot:
    contract: OptionContract
    greeks: OptionGreeks
    as_of: datetime


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    symbol: str
    as_of: datetime
    price: Decimal
    volume: int
    gamma: GammaAggregate | None = None
    recent_flow: tuple[FlowEvent, ...] = field(default_factory=tuple)
    state: MarketState = MarketState.UNKNOWN

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise InvalidOptionError("market snapshot symbol is required")
        object.__setattr__(self, "symbol", self.symbol.upper())
        _ensure_finite_decimal(self.price, InvalidOptionError, "price")
        if self.price < 0 or self.volume < 0:
            raise InvalidOptionError("price and volume cannot be negative")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def dealer_position(net_gamma: Decimal) -> str:
    return "long_gamma" if net_gamma >= 0 else "short_gamma"


def _ensure_finite_decimal(value: Decimal, error_type: type[DomainError], name: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise error_type(f"{name} must be a finite Decimal")


def _ensure_positive_decimal(value: Decimal, error_type: type[DomainError], name: str) -> None:
    _ensure_finite_decimal(value, error_type, name)
    if value <= 0:
        raise error_type(f"{name} must be greater than zero")
