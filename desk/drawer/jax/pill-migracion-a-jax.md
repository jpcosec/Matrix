---
# pill-xxx, unique pill identifier
id: pill-migracion-a-jax
# draft | active | deprecated
status: deprecated
# Primary routine identifier that makes the artifact actionable
routine: ""
# Current node in the operational routine or state machine
current_node: ""
# Operational transition history
history: []
# e.g., language:python, concept:architecture
tags:
- concept:architecture
- context:migration
---

# Migración a Arquitectura JAX (CanonicalHypertensor)

## Summary

_Short semantic summary for the primitive._

Guía de qué preservar y qué desechar de la implementación en Python nativo al migrar a tensores JAX.

## What

_What the pill defines or clarifies._

Define el límite entre la lógica de negocio reusable y el backend físico obsoleto basado en listas y diccionarios nativos.

## Why

_Why this context matters for implementation or refactoring._

Es vital evitar refactorizar o reescribir código fundacional de la capa lógica (dataclasses y compilación) que ya funciona, pero al mismo tiempo no arrastrar estructuras de datos (matrices de Python) que causan problemas de rendimiento (Memory Wall).

## When

_When this pill should be applied._

Al implementar nuevas tareas relacionadas con `CanonicalHypertensor`, `MEELEngine` o `RuleMatrixCompiler`.

## Where

_Where this pill applies, either as general scope or as references to existing code or docs._

Aplicable a toda la refactorización dentro de `src/operational_model/`.

## How

_How to apply the guidance in practice._

- **Mantener y reusar:** Todo lo que está en `core/` (Dataclasses como Symbol, Relation, Proposition, Fact) y `kernel/` (matemática para compilar reglas a matrices $I, C^+, C^-$).
- **Refinar:** `logical_system.py` debe perder su estado interno y quedar solo como Registry (traductor de Strings a Ints).
- **Delegar:** Usar `CanonicalHypertensor` para guardar los hechos de WiGame, ya no diccionarios nativos.

## How Not

_How not to apply the guidance or what to avoid._

- NO reusar `matrices/boolean_matrix.py`, `si_matrix.py` o `vi_matrix.py`. Deben ser vaciados y reemplazados por wrappers sobre `jax.numpy.ndarray`.
- NO usar el serializador `wi_game_serialization.py` o los conversores viejos de S-Expressions que hacían bypass.
