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

Charm/Vanna/Vomma: no tienen columna todavía — se agregan solo cuando el Gamma Engine los necesite para el modelo de Dealer Bias.

Índice compuesto: `(contract_id, time DESC)`.

### `gamma_aggregates`
Tabla oficial para el histórico de la entidad de dominio `GammaAggregate` (Domain Model v1.1) — estado agregado a nivel `Underlying`, no por contrato y no equivalente a un `OptionChain`.

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
| peak_gamma_strike | numeric | Absolute Gamma / Peak Gamma Strike |

`dealer_position` (`long_gamma`/`short_gamma`) **no es columna** — es una métrica derivada dentro de `GammaAggregate` a partir del signo de `net_gamma`, tanto en la API como en cualquier consumidor. `GammaExposure[]` nunca se persiste y nunca llega a `IStorage`; solo `GammaAggregate` se almacena en `gamma_aggregates`. `dealer_bias` y demás métricas agregadas se agregan a esta tabla solo cuando el modelo oficial del Gamma Engine las defina.

Índice compuesto: `(underlying_id, time DESC)`.

### `market_snapshots`
Esta tabla física almacena datos básicos de mercado del subyacente (precio, volumen u otros campos simples que se agreguen después). **No equivale** al objeto de dominio `MarketSnapshot`: ese objeto es una proyección construida bajo demanda combinando último `GammaAggregate`, precio actual y flow reciente.

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
