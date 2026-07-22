# QLL — Esquema de Base de Datos

Motor: PostgreSQL + extensión TimescaleDB para las tablas de series temporales (hypertables).

## Tablas de referencia (PostgreSQL estándar)

### `underlyings`
| Columna | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| symbol | text UNIQUE | ej. "SPY" |
| kind | text | 'equity' \| 'index' |
| is_priority | boolean | true para índices principales / alta liquidez (soporte a la UI, sección 5.1 del blueprint) |

### `option_contracts`
| Columna | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| underlying_id | FK → underlyings | |
| strike | numeric | |
| expiration | date | |
| contract_type | text | 'call' \| 'put' |
| occ_symbol | text UNIQUE | símbolo estándar OCC |

## Hypertables (TimescaleDB — series temporales)

### `option_chain_snapshots`
| Columna | Tipo | Notas |
|---|---|---|
| time | timestamptz | partición TimescaleDB |
| contract_id | FK → option_contracts | |
| bid | numeric | |
| ask | numeric | |
| last | numeric | |
| volume | integer | |
| open_interest | integer | |
| iv | numeric | |
| delta | numeric | MVP — siempre presente |
| gamma | numeric | MVP — siempre presente |
| theta | numeric | nullable — se agrega según necesidad (Domain Model v1.1) |
| vega | numeric | nullable — se agrega según necesidad |

Charm/Vanna/Vomma: no tienen columna todavía — se agregan solo cuando el Gamma Engine (Etapa 7) los necesite para el modelo de Dealer Bias.

Índice compuesto: `(contract_id, time DESC)`.

### `gamma_aggregates`
Corresponde a la entidad `GammaAggregate` (Domain Model v1.1) — nivel `Underlying`, no por contrato.

| Columna | Tipo | Notas |
|---|---|---|
| time | timestamptz | partición TimescaleDB |
| underlying_id | FK → underlyings | |
| gamma_flip | numeric | precio |
| call_wall | numeric | precio |
| put_wall | numeric | precio |
| max_pain | numeric | precio |
| net_gamma | numeric | |
| dealer_gamma_notional | numeric | |

`dealer_position` (`long_gamma`/`short_gamma`) **no es columna** — se deriva del signo de `net_gamma` en el dominio (`dealer_position(net_gamma) -> str`), tanto en la API como en cualquier consumidor.

Índice compuesto: `(underlying_id, time DESC)`.

### `market_snapshots`
| Columna | Tipo | Notas |
|---|---|---|
| time | timestamptz | partición TimescaleDB |
| underlying_id | FK → underlyings | |
| price | numeric | |
| volume | bigint | |

### `flow_events`
| Columna | Tipo | Notas |
|---|---|---|
| time | timestamptz | partición TimescaleDB |
| contract_id | FK → option_contracts | |
| event_type | text | 'sweep' \| 'block' \| 'unusual' |
| premium | numeric | |
| size | integer | |
| aggressor_side | text | 'buy' \| 'sell' \| 'unknown' |

## Política de retención

Configurable por tabla vía `timescaledb.retention_policy`. Default propuesto: sin purga automática al inicio (uso personal, volumen manejable); revisar cuando el histórico pese lo suficiente para justificar compresión/purga.

## Notas de migración

- Migraciones gestionadas con Alembic (`backend/db/migrations/`).
- Ninguna migración debe asumir un proveedor de datos específico — los nombres de columnas reflejan el modelo de dominio (`docs/architecture.md` sección 2), no la forma de la respuesta de Polygon/Massive/ORATS.
