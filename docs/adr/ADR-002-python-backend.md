# ADR-002: Python como lenguaje del backend

**Estado**: Aceptado

## Contexto
El backend debe implementar cálculo de Greeks (Black-Scholes y variantes) y Gamma Exposure — matemática financiera no trivial. También debe exponer una API REST/WebSocket consumida por un frontend React y por un indicador NinjaScript (.NET/C#).

## Alternativas consideradas
- **Node.js/TypeScript**: mismo lenguaje que el frontend, reduce el número de lenguajes en el proyecto. Ecosistema de cálculo cuantitativo más limitado.
- **Python**: ecosistema maduro para finanzas cuantitativas (`py_vollib`, `QuantLib`, `NumPy`, `Pandas`, `SciPy`, `Polars`).
- El indicador NT8 se comunica por HTTP/WebSocket sin importar el lenguaje del backend, así que no es un factor de decisión aquí.

## Decisión
Python para el backend. El motor de Greeks/Gamma es el corazón del proyecto y ahí el ecosistema de Python tiene ventaja real; el frontend seguirá en TypeScript/React de forma independiente (dos lenguajes en el proyecto es un costo aceptable frente al beneficio).

## Consecuencias
- Se requiere definir el framework web (FastAPI es la opción por defecto: soporta REST + WebSocket nativamente, tipado con Pydantic, alto rendimiento relativo dentro del ecosistema Python) — a confirmar en Etapa 1.
- Abre la puerta a experimentación futura con modelos estadísticos/IA sobre los mismos datos, sin cambiar de stack.
