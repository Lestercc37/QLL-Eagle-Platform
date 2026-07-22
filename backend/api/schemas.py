from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OptionContractRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    occ_symbol: str = Field(examples=["SPY260220C00540000"])
    underlying: str | None = Field(default=None, examples=["SPY"])
    strike: Decimal = Field(examples=[540])
    expiration: date = Field(examples=["2026-02-20"])
    contract_type: Literal["call", "put"] = Field(alias="type", examples=["call"])
    bid: Decimal = Field(examples=[1.2])
    ask: Decimal = Field(examples=[1.25])
    last: Decimal | None = Field(default=None, examples=[1.22])
    iv: Decimal = Field(examples=[0.18])
    delta: Decimal = Field(default=Decimal("0"), examples=[0])
    gamma: Decimal = Field(default=Decimal("0"), examples=[0.03])
    theta: Decimal | None = Field(default=None, examples=[-0.015])
    vega: Decimal | None = Field(default=None, examples=[0.12])
    open_interest: int = Field(examples=[8000])
    volume: int = Field(examples=[3400])


class OptionChainRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
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
                        "open_interest": 8000,
                        "volume": 3400,
                    }
                ],
            }
        }
    )

    symbol: str = Field(examples=["SPY"])
    as_of: datetime = Field(examples=["2026-01-15T14:30:00Z"])
    contracts: list[OptionContractRequest] = Field(min_length=1)

    def to_payload(self) -> dict[str, object]:
        return self.model_dump(mode="json", by_alias=True)
