from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.domain.models import (
    CallWall,
    ContractType,
    DealerPositioningInput,
    GammaAggregate,
    GammaAggregateItem,
    Greeks,
    OptionChain,
    OptionContract,
    PutWall,
    GammaExposure,
    GammaFlip,
    MaxPain,
)


Number = int | float


class MarketSnapshotResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    symbol: str = Field(examples=["SPY"])
    as_of: str = Field(examples=["2026-01-15T14:30:00Z"])
    price: Number = Field(examples=[552.25])
    volume: int = Field(examples=[1250000])


class OptionContractResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    occ_symbol: str = Field(examples=["SPY260220C00540000"])
    strike: Number = Field(examples=[540])
    contract_type: Literal["call", "put"] = Field(alias="type", examples=["call"])
    bid: Number = Field(examples=[1.2])
    ask: Number = Field(examples=[1.25])
    iv: Number = Field(examples=[0.18])
    delta: Number = Field(examples=[0.42])
    gamma: Number = Field(examples=[0.03])
    open_interest: int = Field(examples=[8000])
    volume: int = Field(examples=[3400])


class OptionChainResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    symbol: str = Field(examples=["SPY"])
    as_of: str = Field(examples=["2026-01-15T14:30:00Z"])
    contracts: list[OptionContractResponse]


class GreeksContractResponse(OptionContractResponse):
    theta: Number | None = Field(default=None, examples=[-0.015])
    vega: Number | None = Field(default=None, examples=[0.12])


class GreeksResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    symbol: str = Field(examples=["SPY"])
    as_of: str = Field(examples=["2026-01-15T14:30:00Z"])
    contracts: list[GreeksContractResponse]


class GammaExposureItemResponse(BaseModel):
    occ_symbol: str = Field(examples=["SPY260220C00540000"])
    strike: Number = Field(examples=[540])
    contract_type: Literal["call", "put"] = Field(examples=["call"])
    expiration: date = Field(examples=["2026-02-20"])
    gamma: Number = Field(examples=[0.03])
    open_interest: int = Field(examples=[8000])
    dealer_gamma_exposure: Number = Field(examples=[17820000])
    sign: Number = Field(examples=[1])


class GammaExposureResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    items: list[GammaExposureItemResponse]


class GammaAggregateItemResponse(BaseModel):
    strike: Number = Field(examples=[540])
    total_gamma_exposure: Number = Field(examples=[390])
    call_gamma_exposure: Number = Field(examples=[240])
    put_gamma_exposure: Number = Field(examples=[-150])
    net_gamma: Number = Field(examples=[90])
    contract_count: int = Field(examples=[2])
    absolute_gamma: Number = Field(examples=[90])
    open_interest: int = Field(default=0, ge=0, examples=[14000])
    volume: int = Field(default=0, ge=0, examples=[6800])


GammaAggregateStrikeResponse = GammaAggregateItemResponse


class GammaAggregateResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    symbol: str = Field(examples=["SPY"])
    as_of: str = Field(examples=["2026-01-15T14:30:00Z"])
    total_market_gamma: Number = Field(examples=[280])
    positive_gamma: Number = Field(examples=[280])
    negative_gamma: Number = Field(examples=[0])
    peak_gamma_strike: Number = Field(examples=[545])
    peak_gamma_value: Number = Field(examples=[190])
    items: list[GammaAggregateItemResponse]


class GammaFlipRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    symbol: str = Field(min_length=1, examples=["SPY"])
    as_of: datetime = Field(examples=["2026-01-15T14:30:00Z"])
    items: list[GammaAggregateItemResponse] = Field(min_length=1)

    def to_domain(self) -> GammaAggregate:
        return GammaAggregate(
            symbol=self.symbol,
            as_of=self.as_of,
            items=tuple(
                GammaAggregateItem(
                    strike=Decimal(str(item.strike)),
                    total_gamma_exposure=Decimal(str(item.total_gamma_exposure)),
                    call_gamma_exposure=Decimal(str(item.call_gamma_exposure)),
                    put_gamma_exposure=Decimal(str(item.put_gamma_exposure)),
                    net_gamma=Decimal(str(item.net_gamma)),
                    contract_count=item.contract_count,
                    absolute_gamma=Decimal(str(item.absolute_gamma)),
                    open_interest=item.open_interest,
                    volume=item.volume,
                )
                for item in self.items
            ),
        )


class WallResponse(BaseModel):
    strike: Number = Field(examples=[545])
    gamma: Number = Field(examples=[200])
    open_interest: int = Field(examples=[6000])
    volume: int = Field(examples=[4200])
    confidence_score: Number = Field(examples=[0.4545])


class WallsResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    symbol: str = Field(examples=["SPY"])
    as_of: str = Field(examples=["2026-01-15T14:30:00Z"])
    call_wall: WallResponse | None = None
    put_wall: WallResponse | None = None


class GammaFlipResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    gamma_flip_price: Number | None = Field(default=None, examples=[544.5])
    lower_strike: Number | None = Field(default=None, examples=[540])
    upper_strike: Number | None = Field(default=None, examples=[545])
    lower_gamma: Number | None = Field(default=None, examples=[90])
    upper_gamma: Number | None = Field(default=None, examples=[-10])
    interpolation_ratio: Number | None = Field(default=None, examples=[0.9])
    flip_found: bool = Field(examples=[True])


class MaxPainStrikePainResponse(BaseModel):
    strike: Number = Field(examples=[540])
    total_call_pain: Number = Field(examples=[12500])
    total_put_pain: Number = Field(examples=[9000])
    total_pain: Number = Field(examples=[21500])


class MaxPainResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    symbol: str = Field(examples=["SPY"])
    as_of: str = Field(examples=["2026-01-15T14:30:00Z"])
    max_pain_strike: Number = Field(examples=[540])
    total_call_pain: Number = Field(examples=[12500])
    total_put_pain: Number = Field(examples=[9000])
    total_pain: Number = Field(examples=[21500])
    ranking: list[MaxPainStrikePainResponse] = Field(max_length=5)


class DealerPositioningGammaExposureItemRequest(GammaExposureItemResponse):
    pass


class DealerPositioningGammaFlipRequest(BaseModel):
    gamma_flip_price: Number | None = None
    lower_strike: Number | None = None
    upper_strike: Number | None = None
    lower_gamma: Number | None = None
    upper_gamma: Number | None = None
    interpolation_ratio: Number | None = None
    flip_found: bool = False

    def to_domain(self) -> GammaFlip:
        return GammaFlip(
            gamma_flip_price=_optional_decimal(self.gamma_flip_price),
            lower_strike=_optional_decimal(self.lower_strike),
            upper_strike=_optional_decimal(self.upper_strike),
            lower_gamma=_optional_decimal(self.lower_gamma),
            upper_gamma=_optional_decimal(self.upper_gamma),
            interpolation_ratio=_optional_decimal(self.interpolation_ratio),
            flip_found=self.flip_found,
        )


class DealerPositioningMaxPainRequest(MaxPainResponse):
    def to_domain(self) -> MaxPain:
        return MaxPain(
            symbol=self.symbol,
            as_of=datetime.fromisoformat(self.as_of.replace("Z", "+00:00")),
            max_pain_strike=Decimal(str(self.max_pain_strike)),
            total_call_pain=Decimal(str(self.total_call_pain)),
            total_put_pain=Decimal(str(self.total_put_pain)),
            total_pain=Decimal(str(self.total_pain)),
        )


class DealerPositioningRequest(BaseModel):
    symbol: str = Field(min_length=1, examples=["SPY"])
    as_of: datetime = Field(examples=["2026-01-15T14:30:00Z"])
    gamma_exposure: list[DealerPositioningGammaExposureItemRequest] = Field(min_length=1)
    gamma_aggregate: GammaFlipRequest
    gamma_flip: DealerPositioningGammaFlipRequest
    call_wall: WallResponse | None = None
    put_wall: WallResponse | None = None
    max_pain: DealerPositioningMaxPainRequest

    def to_domain(self) -> DealerPositioningInput:
        return DealerPositioningInput(
            gamma_exposure=tuple(
                GammaExposure(
                    occ_symbol=item.occ_symbol,
                    strike=Decimal(str(item.strike)),
                    contract_type=ContractType(item.contract_type),
                    expiration=item.expiration,
                    gamma=Decimal(str(item.gamma)),
                    open_interest=item.open_interest,
                    dealer_gamma_exposure=Decimal(str(item.dealer_gamma_exposure)),
                    sign=Decimal(str(item.sign)),
                )
                for item in self.gamma_exposure
            ),
            gamma_aggregate=self.gamma_aggregate.to_domain(),
            gamma_flip=self.gamma_flip.to_domain(),
            call_wall=_wall_to_domain(self.call_wall, CallWall),
            put_wall=_wall_to_domain(self.put_wall, PutWall),
            max_pain=self.max_pain.to_domain(),
        )


class InstitutionalAnalysisResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    timestamp: str = Field(examples=["2026-01-15T14:30:00Z"])
    overall_bias: Literal["Bullish", "Bearish", "Neutral"]
    confidence_score: Number = Field(examples=[0.85])
    market_regime: str = Field(examples=["Normal"])
    market_snapshot: MarketSnapshotResponse
    option_chain: GreeksResponse
    gamma_exposure: GammaExposureResponse
    gamma_aggregate: GammaAggregateResponse
    peak_gamma_strike: Number = Field(examples=[545])
    gamma_flip: GammaFlipResponse
    call_wall: WallResponse | None = None
    put_wall: WallResponse | None = None
    max_pain: MaxPainResponse
    dealer_positioning: "DealerPositioningResponse"


class DealerPositioningResponse(BaseModel):
    schema_version: int = Field(examples=[1])
    symbol: str = Field(examples=["SPY"])
    as_of: str = Field(examples=["2026-01-15T14:30:00Z"])
    dealer_state: Literal["Long Gamma", "Short Gamma", "Neutral"]
    dealer_bias: Literal["Bullish", "Bearish", "Neutral"]
    hedging_pressure: Number = Field(examples=[0.75])
    expected_volatility: Literal["High", "Low", "Normal"]
    liquidity_regime: Literal["Deep", "Balanced", "Thin"]
    confidence_score: Number = Field(examples=[0.85])


def _optional_decimal(value: Number | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _wall_to_domain(wall: WallResponse | None, wall_type):  # noqa: ANN001
    if wall is None:
        return None
    return wall_type(
        strike=Decimal(str(wall.strike)),
        gamma=Decimal(str(wall.gamma)),
        open_interest=wall.open_interest,
        volume=wall.volume,
        confidence_score=Decimal(str(wall.confidence_score)),
    )


class OptionContractRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    occ_symbol: str = Field(min_length=1, examples=["SPY260220C00540000"])
    underlying: str | None = Field(default=None, examples=["SPY"])
    strike: Decimal = Field(gt=0, examples=[540])
    expiration: date = Field(examples=["2026-02-20"])
    contract_type: Literal["call", "put"] = Field(alias="type", examples=["call"])
    bid: Decimal = Field(ge=0, examples=[1.2])
    ask: Decimal = Field(ge=0, examples=[1.25])
    last: Decimal | None = Field(default=None, ge=0, examples=[1.22])
    iv: Decimal = Field(ge=0, examples=[0.18])
    delta: Decimal = Field(default=Decimal("0"), ge=-1, le=1, examples=[0])
    gamma: Decimal = Field(default=Decimal("0"), examples=[0.03])
    theta: Decimal | None = Field(default=None, examples=[-0.015])
    vega: Decimal | None = Field(default=None, examples=[0.12])
    open_interest: int = Field(ge=0, examples=[8000])
    volume: int = Field(ge=0, examples=[3400])

    @model_validator(mode="after")
    def validate_quote(self) -> "OptionContractRequest":
        if self.ask < self.bid:
            raise ValueError("ask cannot be lower than bid")
        return self

    def to_domain(self, default_symbol: str) -> OptionContract:
        return OptionContract(
            underlying=self.underlying or default_symbol,
            strike=self.strike,
            expiration=self.expiration,
            contract_type=ContractType(self.contract_type),
            occ_symbol=self.occ_symbol,
            bid=self.bid,
            ask=self.ask,
            last=self.last if self.last is not None else self.bid,
            volume=self.volume,
            open_interest=self.open_interest,
            iv=self.iv,
            greeks=Greeks(
                delta=self.delta,
                gamma=self.gamma,
                theta=self.theta,
                vega=self.vega,
            ),
        )


class OptionChainRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
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
            ],
            "example": {
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
            },
        }
    )

    symbol: str = Field(min_length=1, examples=["SPY"])
    as_of: datetime = Field(examples=["2026-01-15T14:30:00Z"])
    contracts: list[OptionContractRequest] = Field(min_length=1)

    def to_domain(self) -> OptionChain:
        return OptionChain(
            symbol=self.symbol,
            as_of=self.as_of,
            contracts=tuple(contract.to_domain(self.symbol) for contract in self.contracts),
        )
