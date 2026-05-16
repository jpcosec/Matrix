# Matrix TKM Documentation Index

Bienvenido a la documentación técnica del motor **MEEL (Matrix Engine for Evolutionary Logic)** bajo la arquitectura **TKM (Tractatus Knowledge Machine)**.

## Core Documentation
- [Architecture](./architecture.md): Visión general de la infraestructura de 4 capas y el flujo de datos.
- [Concepts](./concepts.md): Fundamentos filosóficos (Tractatus) y matemáticos (JAX, Energía de Información).
- [Data Models](./data_models.md): Estructuras de datos (`Context`, `Bridge`, `SymbolRegistry`).
- [Operations](./operations.md): Guía de operaciones lógicas, ruteo y reconstrucción de texto.

## Project Resources
- **Source Code**: [Matrix/src/](../src/)
- **Whitepaper**: [Matrix/Whitepaper](../Whitepaper)
- **Tests & Demos**: [Matrix/tests/](../tests/)

## Getting Started
Para ejecutar las validaciones actuales:
```bash
PYTHONPATH=src python3 tests/test_tkm_roundtrip_suite.py
```
