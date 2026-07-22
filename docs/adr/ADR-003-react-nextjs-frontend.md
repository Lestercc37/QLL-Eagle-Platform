# ADR-003: React/Next.js para la interfaz web

**Estado**: Aceptado (riesgo bajo — reversible sin afectar el núcleo)

## Contexto
Se necesita un dashboard web para visualizar Options Chain, Gamma Analytics y Flow. A diferencia de ADR-001/002/004/005, esta decisión no afecta al núcleo de dominio ni al esquema de datos — el frontend es un adaptador de entrada más (consume la misma API REST/WebSocket que consumiría cualquier otro cliente).

## Decisión
React con Next.js. Motivo práctico: ecosistema amplio de librerías de visualización financiera, y es el framework ya contemplado desde el blueprint original.

## Consecuencias
- Al ser un cliente desacoplado detrás de la API (igual que NT8), cambiar de framework de frontend en el futuro no requiere tocar el backend ni el modelo de dominio — de ahí el riesgo bajo de esta decisión frente a las demás.
