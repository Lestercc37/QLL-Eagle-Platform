# ADR-006: Capa de proveedores de datos desacoplada mediante IDataProvider

**Estado**: Aceptado

## Contexto
Durante el diseño de este mismo proyecto, Polygon.io se rebrandeó a Massive — un ejemplo concreto y no hipotético de por qué depender directamente del SDK de un proveedor es un riesgo. Además, el plan de datos aún no está contratado (se desarrolla inicialmente contra datos simulados).

## Decisión
Ningún módulo del núcleo, motor de cálculo o adaptador de storage llama directamente a un SDK o cliente HTTP de un proveedor externo (Polygon/Massive, ORATS, Tradier). Todo pasa por la interfaz `IDataProvider` (ver `docs/architecture.md` sección 3). Cada proveedor tiene su propio adaptador (`PolygonDataProvider`, `MockDataProvider`, etc.) que traduce la respuesta externa al modelo de dominio de QLL (`OptionChain`, `Greeks`, etc.).

## Consecuencias
- Empezar a construir sin tener el feed contratado es viable desde el día uno: `MockDataProvider` implementa el mismo contrato que usará el proveedor real.
- Cambiar de proveedor, o combinar varios (ej. chain de Polygon + Greeks de ORATS), es agregar/ajustar un adaptador — el núcleo de negocio no se entera del cambio.
- Costo: cada proveedor nuevo requiere escribir su adaptador de traducción; se acepta como el costo correcto a cambio de estabilidad del núcleo.
