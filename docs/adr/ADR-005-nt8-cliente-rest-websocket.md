# ADR-005: NinjaTrader 8 como cliente vía REST/WebSocket

**Estado**: Aceptado

## Contexto
Lester ya opera con un indicador de footprint/volume profile propio en NinjaScript (NT8, .NET/C#) y quiere ver Gamma Exposure/Options en la misma pantalla. NinjaScript corre en un runtime distinto (.NET/C#) al backend (Python) — no existe forma de "importar" código entre ambos.

## Alternativas consideradas
- **Reimplementar el cálculo de Gamma/Greeks directamente en NinjaScript (C#)**: eliminaría la dependencia de red, pero duplica toda la lógica de negocio en dos lenguajes/runtimes, con el riesgo de que diverjan con el tiempo.
- **NT8 como cliente delgado vía REST/WebSocket**: el indicador NinjaScript solo consulta y dibuja; toda la lógica vive una sola vez en el backend de QLL.

## Decisión
NT8 es un cliente más de la API, igual que el dashboard web. El indicador NinjaScript no calcula Gamma, Max Pain ni Dealer Position — solo consume `GET /api/v1/gamma/{symbol}` y el canal `gamma` del WebSocket, y dibuja el resultado.

Regla obligatoria de versionado: todo mensaje incluye `schema_version`; el indicador rechaza versiones que no soporta en vez de fallar silenciosamente (ver `docs/nt8-contract.md`).

La integración con NT8 se construye en Etapa 4 del roadmap (temprano, con datos simulados vía `MockDataProvider`), no al final — para detectar problemas de integración cuando el sistema todavía es pequeño.

## Consecuencias
- El backend puede evolucionar (nuevos cálculos, nuevos campos) sin tener que recompilar y redistribuir el indicador NT8, salvo cambios incompatibles de `schema_version`.
- Requiere que NT8 tenga conectividad de red al backend (localhost si corren en la misma máquina Windows, que es el caso planeado).
