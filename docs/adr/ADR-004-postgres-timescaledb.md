# ADR-004: PostgreSQL + TimescaleDB para persistencia

**Estado**: Aceptado

## Contexto
QLL necesita persistir tanto datos de referencia (underlyings, contratos) como series temporales de alto volumen (snapshots de chain, Gamma Exposure, eventos de flujo). Se evaluó usar una base de series temporales dedicada (ClickHouse, InfluxDB) separada de la base relacional.

## Alternativas consideradas
- **InfluxDB / ClickHouse dedicada + PostgreSQL separado**: mejor rendimiento en escritura masiva a muy gran escala, pero dos motores de base de datos que mantener, dos conexiones, dos esquemas de backup — complejidad operativa alta para un proyecto de uso personal.
- **PostgreSQL + extensión TimescaleDB**: un solo motor, un solo esquema de conexión, hypertables para las tablas de series temporales con rendimiento adecuado al volumen de un usuario individual (no es un ticker plant institucional).

## Decisión
PostgreSQL con extensión TimescaleDB. Tablas de referencia como tablas normales; tablas de snapshots (`option_chain_snapshots`, `gamma_exposure_snapshots`, `market_snapshots`, `flow_events`) como hypertables.

## Consecuencias
- Un solo motor de base de datos que operar y respaldar, corre bien en Docker local sobre Windows.
- Si en el futuro el volumen de datos lo justifica (cobertura de opciones ampliada, mayor frecuencia de snapshot), se puede migrar la capa de series temporales a un motor dedicado sin tocar el núcleo — `IStorage` es la única interfaz que el dominio conoce (ADR-001).
