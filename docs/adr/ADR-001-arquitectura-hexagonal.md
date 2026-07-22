# ADR-001: Arquitectura Hexagonal (Ports & Adapters)

**Estado**: Aceptado

## Contexto
QLL depende de proveedores de datos externos (Polygon/Massive, ORATS, Tradier) que pueden cambiar de nombre, precio o incluso dejar de existir — ya ocurrió una vez durante el diseño de este proyecto (Polygon → Massive). También hay más de un cliente consumidor (dashboard web, indicador NT8, potencialmente móvil a futuro). El riesgo principal del proyecto no está en la lógica de negocio (Gamma, Greeks), sino en el acoplamiento a piezas externas que cambian.

## Alternativas consideradas
- **Arquitectura en capas simple (MVC clásico)**: más rápida de arrancar, pero tiende a que la lógica de negocio termine llamando directamente a SDKs de proveedores, dificultando el cambio de proveedor sin tocar el núcleo.
- **Arquitectura hexagonal (Ports & Adapters)**: más disciplina inicial, pero aísla el núcleo de negocio de cualquier dependencia externa mediante interfaces.

## Decisión
Se adopta Arquitectura Hexagonal. El núcleo de dominio define interfaces (`IDataProvider`, `IGreeksCalculator`, `IStorage`, `INotificationService`); los adaptadores externos las implementan. El núcleo nunca importa un SDK de proveedor directamente.

## Consecuencias
- Cambiar de proveedor de datos (o combinar varios) implica agregar/reemplazar un adaptador, sin tocar motores de cálculo ni modelo de dominio.
- Costo inicial: más archivos/capas que una arquitectura simple; se acepta porque el proyecto está pensado para evolucionar por años, no es un script desechable.
