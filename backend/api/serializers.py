from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from backend.domain.models import FlowEvent, GammaAggregate, MarketSnapshot, OptionChain, SCHEMA_VERSION, Underlying
from backend.domain.use_cases.errors import QllError


def underlyings_response(items: list[Underlying]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "underlyings": [{"symbol": i.symbol, "kind": i.kind.value, "is_priority": i.is_priority} for i in items]}


def chain_response(chain: OptionChain) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "symbol": chain.symbol, "as_of": _dt(chain.as_of), "contracts": [{"occ_symbol": c.occ_symbol, "strike": _num(c.strike), "type": c.contract_type.value, "bid": _num(c.bid), "ask": _num(c.ask), "iv": _num(c.iv), "delta": _num(c.greeks.delta), "gamma": _num(c.greeks.gamma), "open_interest": c.open_interest, "volume": c.volume} for c in chain.contracts]}


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


def _dt(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _num(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)
