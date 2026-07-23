from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from backend.domain.models import (
    ContractType,
    FlowEvent,
    GammaAggregate,
    GammaExposure,
    GammaFlip,
    Greeks,
    MarketSnapshot,
    OptionChain,
    OptionContract,
    SCHEMA_VERSION,
    Underlying,
)
from backend.domain.use_cases.errors import QllError


def underlyings_response(items: list[Underlying]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "underlyings": [
            {"symbol": i.symbol, "kind": i.kind.value, "is_priority": i.is_priority}
            for i in items
        ],
    }


def chain_response(chain: OptionChain) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "symbol": chain.symbol, "as_of": _dt(chain.as_of), "contracts": [{"occ_symbol": c.occ_symbol, "strike": _num(c.strike), "type": c.contract_type.value, "bid": _num(c.bid), "ask": _num(c.ask), "iv": _num(c.iv), "delta": _num(c.greeks.delta), "gamma": _num(c.greeks.gamma), "open_interest": c.open_interest, "volume": c.volume} for c in chain.contracts]}


def greeks_chain_response(chain: OptionChain) -> dict[str, Any]:
    payload = chain_response(chain)
    for contract_payload, contract in zip(payload["contracts"], chain.contracts, strict=True):
        contract_payload["theta"] = (
            _num(contract.greeks.theta) if contract.greeks.theta is not None else None
        )
        contract_payload["vega"] = (
            _num(contract.greeks.vega) if contract.greeks.vega is not None else None
        )
    return payload


def gamma_aggregate_response(gamma: GammaAggregate) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "symbol": gamma.symbol,
        "as_of": _dt(gamma.as_of),
        "total_market_gamma": _num(gamma.total_market_gamma),
        "positive_gamma": _num(gamma.positive_gamma),
        "negative_gamma": _num(gamma.negative_gamma),
        "peak_gamma_strike": _num(gamma.peak_gamma_strike),
        "peak_gamma_value": _num(gamma.peak_gamma_value),
        "items": [
            {
                "strike": _num(item.strike),
                "total_gamma_exposure": _num(item.total_gamma_exposure),
                "call_gamma_exposure": _num(item.call_gamma_exposure),
                "put_gamma_exposure": _num(item.put_gamma_exposure),
                "net_gamma": _num(item.net_gamma),
                "contract_count": item.contract_count,
                "absolute_gamma": _num(item.absolute_gamma),
            }
            for item in gamma.items
        ],
    }


def gamma_exposure_response(items: tuple[GammaExposure, ...]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "items": [
            {
                "occ_symbol": item.occ_symbol,
                "strike": _num(item.strike),
                "contract_type": item.contract_type.value,
                "expiration": item.expiration.isoformat(),
                "gamma": _num(item.gamma),
                "open_interest": item.open_interest,
                "dealer_gamma_exposure": _num(item.dealer_gamma_exposure),
                "sign": _num(item.sign),
            }
            for item in items
        ],
    }


def gamma_flip_response(flip: GammaFlip) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "gamma_flip_price": _optional_num(flip.gamma_flip_price),
        "lower_strike": _optional_num(flip.lower_strike),
        "upper_strike": _optional_num(flip.upper_strike),
        "lower_gamma": _optional_num(flip.lower_gamma),
        "upper_gamma": _optional_num(flip.upper_gamma),
        "interpolation_ratio": _optional_num(flip.interpolation_ratio),
        "flip_found": flip.flip_found,
    }


def option_chain_from_payload(payload: dict[str, Any]) -> OptionChain:
    return OptionChain(
        symbol=str(payload["symbol"]),
        as_of=_parse_datetime(str(payload["as_of"])),
        contracts=tuple(
            _contract_from_payload(str(payload["symbol"]), item)
            for item in payload.get("contracts", ())
        ),
    )


def gamma_response(gamma: GammaAggregate) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "symbol": gamma.symbol, "as_of": _dt(gamma.as_of), "gamma_flip": _num(gamma.gamma_flip), "call_wall": _num(gamma.call_wall), "put_wall": _num(gamma.put_wall), "max_pain": _num(gamma.max_pain), "net_gamma": _num(gamma.net_gamma), "dealer_position": gamma.dealer_position}


def gamma_history_response(symbol: str, items: list[GammaAggregate]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "symbol": symbol.upper(), "items": [gamma_response(item) for item in items]}


def market_response(snapshot: MarketSnapshot) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "symbol": snapshot.symbol, "as_of": _dt(snapshot.as_of), "price": _num(snapshot.price), "volume": snapshot.volume}


def flow_response(symbol: str, events: list[FlowEvent]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "symbol": symbol.upper(), "events": [{"as_of": _dt(e.as_of), "occ_symbol": e.occ_symbol, "event_type": e.event_type.value, "premium": _num(e.premium), "size": e.size, "aggressor_side": e.aggressor_side.value} for e in events]}


def websocket_message(channel: str, symbol: str, payload: dict[str, Any], as_of: datetime) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "channel": channel, "type": "update", "symbol": symbol.upper(), "payload": payload, "as_of": _dt(as_of)}


def error_response(error: QllError) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "error": {"code": error.code, "message": str(error)}}


def _contract_from_payload(default_symbol: str, payload: dict[str, Any]) -> OptionContract:
    contract_type = ContractType(str(payload.get("type") or payload.get("contract_type")))
    greeks_payload = payload.get("greeks", payload)
    return OptionContract(
        underlying=str(payload.get("underlying", default_symbol)),
        strike=Decimal(str(payload["strike"])),
        expiration=date.fromisoformat(str(payload["expiration"])),
        contract_type=contract_type,
        occ_symbol=str(payload["occ_symbol"]),
        bid=Decimal(str(payload["bid"])),
        ask=Decimal(str(payload["ask"])),
        last=Decimal(str(payload.get("last", payload["bid"]))),
        volume=int(payload["volume"]),
        open_interest=int(payload["open_interest"]),
        iv=Decimal(str(payload["iv"])),
        greeks=Greeks(
            delta=Decimal(str(greeks_payload.get("delta", "0"))),
            gamma=Decimal(str(greeks_payload.get("gamma", "0"))),
            theta=_optional_decimal(greeks_payload.get("theta")),
            vega=_optional_decimal(greeks_payload.get("vega")),
        ),
    )


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _dt(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _num(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _optional_num(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    return _num(value)
