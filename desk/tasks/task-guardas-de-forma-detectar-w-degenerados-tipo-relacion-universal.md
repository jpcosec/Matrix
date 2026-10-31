---
id: task-guardas-de-forma-detectar-w-degenerados-tipo-relacion-universal
status: closed
summary: ''
tags:
- workspace:desk
- artifact:task
current_node: ritual-execution
history: []
references: []
depends_on: []
pills: []
files: []
task_type: ''
inherits_from: []
inherit_acceptance_context: false
atoms: []
---

# Guardas de forma: detectar W degenerados tipo relacion universal

## Rationale

_Explain why this task exists or the business driver behind it._

El W mas ancho posible se llena de casos como (* pedrito es_hermano_de_maria), donde el objeto empaqueta relacion+objeto en un solo simbolo y 'maria' deja de ser indexable. Medido: ese W da E=0.5278 con 18 celdas contra E=0.5556 con 9 celdas del factorizado. Hay que rechazar esa forma, no solo medirla.

## Goal

_Describe the concrete result this task must produce._

Diagnostico de forma de un WiGame que detecte relacion universal, objetos que empaquetan relacion, objetos conjuntivos y columnas no discriminativas, con severidad y motivo.

## Scope

_State what is in scope and what is out of scope._

src/operational_model/system/shape_guard.py (nuevo)

## Implementation Path

_Outline the expected implementation route or affected surface._

diagnose_shape(wigame) -> lista de hallazgos tipificados: relation_id comodin, objeto cuyo nombre contiene un simbolo registrado del sistema (empaquetado), objeto conjuntivo, columna tautologica, densidad de hechos por celda; cada hallazgo con severidad y explicacion; tests en tests/test_shape_guard.py

## Validation

_List the checks required before this task can close._

- pytest -q tests/test_shape_guard.py
- pytest -q

## Done When

_Name the observable condition that makes the task complete._

El W con r='*' y objetos es_hermano_de_maria es marcado con empaquetado y relacion universal; el W con r=es_hermano_de sobre ejes de personas pasa limpio.
