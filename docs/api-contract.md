# QLL — Contrato API REST

Base path: `/api/v1`. Formato: JSON. Toda respuesta incluye `schema_version` (ver `docs/nt8-contract.md` para por qué esto es una regla del proyecto, no solo de NT8).

## `GET /api/v1/underlyings`
Lista de underlyings soportados, con flag `is_priority`.

## `GET /api/v1/chain/{symbol}`
Cadena de opciones actual (último snapshot persistido).

Query params: `expiration` (opcional, filtra por vencimiento).

Respuesta (resumen):
```json
{
  "schema_version": 1,
  "symbol": "SPY",
  "as_of": "2026-07-21T14:32:00Z",
  "contracts": [
    { "occ_symbol": "...", "strike": 550, "type": "call", "bid": 1.2, "ask": 1.25,
      "iv": 0.18, "delta": 0.42, "gamma": 0.03, "open_interest": 12000, "volume": 3400 }
  ]
}
```

## `GET /api/v1/gamma/{symbol}`
Último snapshot de Gamma Exposure.

Respuesta (resumen):
```json
{
  "schema_version": 1,
  "symbol": "SPY",
  "as_of": "2026-07-21T14:32:00Z",
  "gamma_flip": 548.5,
  "call_wall": 555,
  "put_wall": 540,
  "max_pain": 550,
  "net_gamma": -1250000,
  "dealer_position": "short_gamma"
}
```
`dealer_position` es un campo **derivado** (signo de `net_gamma`), calculado al construir la respuesta — no existe como columna en la base de datos (ver `docs/database-schema.md`, tabla `gamma_aggregates`).

## `GET /api/v1/gamma/{symbol}/history`
Serie histórica de Gamma Exposure. Query params: `start`, `end`.

## `GET /api/v1/flow/{symbol}`
Últimos eventos de flujo clasificados (sweeps/blocks). Query params: `since`, `limit`.

## `GET /api/v1/market/{symbol}`
Último snapshot de precio/volumen del underlying.

## Errores

Formato uniforme:
```json
{ "schema_version": 1, "error": { "code": "PROVIDER_UNAVAILABLE", "message": "..." } }
```

Códigos base: `NOT_FOUND`, `PROVIDER_UNAVAILABLE`, `INVALID_PARAMS`, `INTERNAL_ERROR`.

## Versionado

Cambios incompatibles → nueva versión de path (`/api/v2/...`), nunca se rompe `/v1` en producción mientras exista un cliente activo (incluyendo el indicador NT8). Cambios aditivos (campos nuevos opcionales) no incrementan `schema_version`.
