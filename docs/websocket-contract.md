# QLL — Contrato WebSocket

Endpoint: `/ws/v1/stream`. Todo mensaje, en ambas direcciones, lleva `schema_version` (regla del proyecto — ver `docs/nt8-contract.md`).

## Suscripción (cliente → servidor)

```json
{ "schema_version": 1, "action": "subscribe", "channel": "gamma", "symbol": "SPY" }
```

Canales disponibles: `gamma`, `chain`, `flow`, `market`.

## Mensajes (servidor → cliente)

Mismo shape que los recursos REST equivalentes, envueltos con `channel` y `type`:

```json
{
  "schema_version": 1,
  "channel": "gamma",
  "type": "update",
  "symbol": "SPY",
  "payload": { "gamma_flip": 548.5, "call_wall": 555, "put_wall": 540, "max_pain": 550, "dealer_position": "short_gamma" },
  "as_of": "2026-07-21T14:32:00Z"
}
```

## Heartbeat

Servidor envía `{ "schema_version": 1, "type": "ping" }` cada 30s. Cliente responde `{ "schema_version": 1, "type": "pong" }`. Si no hay `pong` en 10s, el servidor cierra la conexión — importante para que el indicador NT8 detecte desconexión y lo muestre en pantalla en vez de congelar el último valor silenciosamente.

## Reconexión

Cliente reconecta con backoff exponencial (1s, 2s, 4s... máx 30s). Al reconectar, vuelve a enviar todas sus suscripciones activas — el servidor no recuerda estado de sesiones caídas.
