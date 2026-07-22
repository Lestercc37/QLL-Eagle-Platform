# QLL — Contrato para NinjaTrader 8

## Principio (ADR-005)

NinjaTrader nunca es el centro del sistema — es un cliente más, igual que el dashboard web. El indicador NinjaScript:

- **No calcula** Gamma, Max Pain, Dealer Position, Greeks ni ninguna lógica de negocio.
- Solo consulta la API (REST para datos puntuales, WebSocket para streaming) y **dibuja** el resultado.
- Toda la lógica vive una sola vez en el backend de QLL.

## Regla de versionado (obligatoria desde el día uno)

Todo mensaje REST o WebSocket que consuma NT8 incluye el campo `schema_version` (entero). El indicador NinjaScript:

1. Lee `schema_version` antes de parsear el resto del mensaje.
2. Si la versión es mayor a la que el indicador soporta, **no intenta parsear** — muestra un aviso visual ("QLL: versión de API no soportada, actualizar indicador") y deja de dibujar datos nuevos, en vez de fallar silenciosamente o crashear.
3. Esto evita que un cambio futuro en el backend rompa el indicador sin que Lester se entere.

## Transporte

- Consulta inicial / fallback: `GET /api/v1/gamma/{symbol}` por HTTP (System.Net.Http en C#).
- Streaming: WebSocket a `/ws/v1/stream`, suscripción a canal `gamma` (y `flow` cuando esté disponible) para el/los símbolos visibles en el gráfico activo.

## Qué dibuja el indicador (alcance inicial)

- Gamma Flip, Call Wall, Put Wall, Max Pain como líneas horizontales en el gráfico del subyacente.
- Indicador de estado de conexión (conectado / reconectando / versión no soportada) — visible en todo momento, no solo en log.

## Etapa 4 (implementación temprana con datos simulados)

Durante la Etapa 4 del roadmap, el backend responde con datos del `MockDataProvider` (ver `docs/architecture.md` sección 4). El objetivo de esa etapa es validar que:

- El indicador se conecta, se suscribe y dibuja correctamente.
- La reconexión funciona si se reinicia el backend mientras NT8 sigue corriendo.
- El manejo de `schema_version` funciona (se puede probar forzando una versión mayor desde el backend).

Ningún dato mostrado en esta etapa es real — es deliberado, sirve para probar la integración antes de que exista el Gamma Engine real (Etapa 7).
