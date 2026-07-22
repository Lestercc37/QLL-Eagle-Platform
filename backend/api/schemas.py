from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.domain.models import ContractType, Greeks, OptionChain, OptionContract


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
