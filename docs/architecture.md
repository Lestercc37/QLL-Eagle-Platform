# QLL — Arquitectura (Etapa 0)

Estado: aprobado para inicio de implementación
Ámbito: decisiones caras de cambiar después (capas, esquema DB, contratos API/WS) y roadmap del Motor Cuantitativo. Convenciones de naming y estrategia de testing se resuelven como guía ligera (ver `docs/conventions.md`, se escribe durante Etapa 1, no bloquea el inicio).

## 1. Arquitectura general

QLL usa **Arquitectura Hexagonal (Ports & Adapters)**. El núcleo de negocio (dominio + motores de cálculo) no conoce la existencia de Polygon/Massive, PostgreSQL, React ni NinjaTrader. Todo lo externo entra y sale a través de interfaces (ports) definidas por el núcleo, implementadas por adaptadores reemplazables.

```
                        ┌─────────────────────────────┐
                        │        Adaptadores In        │
                        │  REST API │ WebSocket Server  │
                        └──────────────┬────────────────┘
                                       │
        ┌──────────────────────────────▼──────────────────────────────┐
        │                        NÚCLEO (dominio)                      │
        │                                                              │
        │   Entidades: Underlying, OptionContract, OptionChain,        │
        │   Expiration, Greeks, GammaAggregate, FlowEvent              │
        │   Proyecciones: MarketSnapshot                               │
        │                                                              │
        │   Motores: OptionsEngine, GammaEngine, FlowEngine            │
        │                                                              │
        │   Ports (interfaces): IDataProvider, IGreeksCalculator,      │
        │   IStorage, INotificationService                             │
        └──────────────┬───────────────────────────────┬───────────────┘
                       │                                │
        ┌──────────────▼──────────────┐   ┌─────────────▼─────────────┐
        │      Adaptadores Out         │   │     Adaptadores Out        │
        │  PolygonProvider (IDataProvider) │  TimescaleStorage (IStorage) │
        │  ORATSProvider (IDataProvider)   │  ORATSGreeksCalc (IGreeksCalc)│
        │  MockProvider (IDataProvider)    │                              │
        └───────────────────────────────┘   └────────────────────────────┘
```

Regla de dependencia: las flechas de importación siempre apuntan **hacia el núcleo**. Un adaptador puede importar del dominio; el dominio nunca importa de un adaptador. Ver ADR-001.

## 2. Modelo de dominio (v1.1)

Principio: el dominio no conoce Massive/Polygon, HTTP, SQL, WebSocket ni NinjaTrader. Las **entidades** representan el negocio; las **proyecciones** son vistas de lectura para clientes (Web UI, NT8) y no se persisten como tal — se construyen combinando entidades.

### Entidades (persistidas)

| Entidad | Descripción | Persistencia |
|---|---|---|
| `Underlying` | Activo subyacente (ticker, exchange, tipo) | Tabla de referencia (PostgreSQL) |
| `Expiration` | Fecha de vencimiento con DTE | Derivado de `OptionContract` |
| `OptionContract` | Datos base del contrato (strike, tipo, bid/ask/last, volumen, OI) | Tabla de referencia + snapshot en serie temporal |
| `Greeks` | MVP: Delta y Gamma. Theta/Vega se agregan según necesidad. Charm/Vanna/Vomma **pospuestos** — se agregan solo cuando el Gamma Engine los necesite para el modelo de Dealer Bias, no antes | Serie temporal, embebido en snapshot de `OptionContract` |
| `FlowEvent` | Evento de flujo institucional (sweep/block, premium, dirección) | Tabla append-only (TimescaleDB) |
| `GammaAggregate` | Estado agregado del mercado para un `Underlying` en un instante: Net Gamma, Gamma Flip, Absolute Gamma / Peak Gamma Strike, Call Wall, Put Wall, Max Pain, Dealer Gamma Notional y demás métricas definidas por el proyecto. Es el resultado agregado del Gamma Engine; **no** es un `OptionChain` | Serie temporal en `gamma_aggregates` — snapshot persistido en TimescaleDB (cadencia configurable, default aprox. 1 min) |

### Proyecciones (no persistidas — se construyen bajo demanda)

- **`MarketSnapshot`** — combina precio actual (frecuencia alta, barato) + último `GammaAggregate` (frecuencia baja, costoso) + Flow reciente. Es una proyección de dominio construida bajo demanda para API/WS; no representa una tabla de persistencia del estado completo del mercado.
- **Contribución/Ranking por contrato** (qué tanto aporta cada `OptionContract` al Gamma total) — se calcula on-demand desde el `OptionChain` ya guardado, nunca se persiste por contrato (evita multiplicar la tabla de series temporales por el número de contratos en cada snapshot).
- **`dealer_position`** (`long_gamma` / `short_gamma`) — métrica derivada dentro de `GammaAggregate` a partir de `Net Gamma`; no es una columna propia persistida.
- Vistas de Dashboard / NT8 — composiciones de lo anterior, específicas de cada cliente.

### Casos de uso del dominio

`GetOptionChain`, `CalculateGammaAggregate`, `CalculateGammaFlip`, `CalculateCallPutWall`, `BuildMarketSnapshot`, `ProcessFlow` — especificados en detalle, incluyendo qué dispara cada uno y su mapeo a REST/WebSocket, en `docs/use-cases.md`.

## 3. Interfaces (Ports)

Definidas en `backend/domain/ports/`. Son las únicas puertas de entrada/salida del núcleo.

```python
class IDataProvider(Protocol):
    def get_option_chain(self, underlying: str, expiration: date | None = None) -> OptionChain: ...
    def get_underlying_snapshot(self, underlying: str) -> MarketSnapshot: ...
    def stream_trades(self, underlying: str) -> AsyncIterator[FlowEvent]: ...

class IGreeksCalculator(Protocol):
    def calculate(self, contract: OptionContract, market: MarketSnapshot) -> Greeks: ...

class IStorage(Protocol):
    def save_chain_snapshot(self, chain: OptionChain) -> None: ...
    def save_gamma_aggregate(self, gamma: GammaAggregate) -> None: ...
    def get_gamma_history(self, underlying: str, start: datetime, end: datetime) -> list[GammaAggregate]: ...
    # ... resto de operaciones de persistencia

class INotificationService(Protocol):
    def notify(self, event: FlowEvent | GammaAggregate) -> None: ...
    # implementación inicial: no-op. Con Alerts (Etapa 8+), se agrega un adaptador real.
```

Regla (ADR-006): **ningún módulo del núcleo o de otro adaptador llama directamente a `polygon.*`, `massive.*`, `orats.*` ni a un cliente HTTP de un proveedor.** Siempre pasa por `provider.get_option_chain(...)`, nunca por el SDK del proveedor importado fuera de su propio adaptador.

## 4. Adaptadores externos (implementaciones iniciales)

- `MockDataProvider` — implementa `IDataProvider` con datos simulados o registrados (fixtures). Es el que se usa mientras no haya feed contratado. Vive en `backend/adapters/providers/mock/`.
- `PolygonDataProvider` (Massive) — implementación real, se agrega cuando se contrate el plan. Mismo contrato `IDataProvider`, sin tocar el núcleo.
- `TimescaleStorage` — implementa `IStorage` sobre PostgreSQL + TimescaleDB.
- `InternalGreeksCalculator` — implementa `IGreeksCalculator` con `py_vollib`/`QuantLib`. Alternativa futura: `ORATSGreeksCalculator` si se decide no calcular in-house.
- `NoopNotificationService` — implementación inicial de `INotificationService`, no hace nada. Se reemplaza en Etapa 8+.

## 5. Esquema de base de datos

Ver `docs/database-schema.md`.

## 6. API REST

Ver `docs/api-contract.md`.

## 7. WebSocket

Ver `docs/websocket-contract.md`.

## 8. Contrato NT8

Ver `docs/nt8-contract.md`.

## 9. Decisiones tecnológicas

Ver `docs/adr/` — ADR-001 a ADR-006.

## 10. Roadmap oficial — Motor Cuantitativo

Principios obligatorios para la secuencia de implementación:

- **Un PR = una responsabilidad.**
- **Primero arquitectura.**
- **Después implementación.**
- **Primero Fake determinístico.**
- **Después implementación real.**

Separación de Clean Architecture para el Motor Cuantitativo:

```text
Provider
↓
Application
↓
Domain
↓
Aggregation
↓
Persistence
↓
Streaming
↓
Frontend
```

### PR #8 — Greeks Engine

- Definir el puerto `GreeksCalculator`.
- Implementación `FakeGreeksCalculator` determinística.
- `CalculateGreeksUseCase`.
- Endpoint de validación.
- Tests.

### PR #9 — Gamma Exposure Engine

- **Entrada:** `OptionChain` con `Greeks`.
- **Salida:** `GammaExposure[]` por contrato.

`GammaExposure[]` es un valor intermedio en memoria. No se persiste, no se almacena en base de datos y no utiliza `IStorage`. Su única finalidad es alimentar el proceso de agregación.

### PR #10 — Gamma Aggregation

- **Entrada:** `GammaExposure[]`.
- **Salida:** `GammaAggregate`.

`GammaAggregate` debe contener al menos:

- Net Gamma.
- Gamma Flip.
- Absolute Gamma / Peak Gamma Strike.
- Call Wall.
- Put Wall.
- Max Pain.
- Dealer Gamma Notional.

Nota: Absolute Gamma (Peak Gamma Strike) forma parte del agregado principal debido a su relevancia operacional para el análisis institucional.

Nota: Max Pain se calcula y se expone como dato analítico, pero no constituye por sí mismo una señal principal para la lógica de alertas intradía.

### PR #11 — Persistencia

Únicamente `GammaAggregate` llega a `IStorage`. Nunca `GammaExposure[]`.

### PR #12 — Background Jobs

### PR #13 — WebSockets

### PR #14 — Chart Engine
