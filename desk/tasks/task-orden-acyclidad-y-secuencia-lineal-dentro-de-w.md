---
id: task-orden-acyclidad-y-secuencia-lineal-dentro-de-w
status: draft
summary: ''
tags:
- workspace:desk
- artifact:task
routine: routine-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w
current_node: checklist-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-execution-ready
history: []
references: []
depends_on: []
pills: []
files: []
checklists:
- checklist-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-execution-ready
- checklist-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-testing-ready
- checklist-task-orden-acyclidad-y-secuencia-lineal-dentro-de-w-closeout-ready
task_type: ''
inherits_from: []
inherit_acceptance_context: false
atoms: []
---

# Orden: acyclidad y secuencia lineal dentro de W

## Rationale

_Explain why this task exists or the business driver behind it._

Una relacion transitiva sola no da una secuencia: sin antisimetria y totalidad no se sabe si el orden es unico ni se puede emitir en orden. reach.py obtiene alcanzabilidad por BFS pero nunca valida ni extrae la secuencia.

## Goal

_Describe the concrete result this task must produce._

Modulo de orden sobre aristas: validacion de acyclidad con error tipificado, orden topologico determinista, deteccion de totalidad y extension lineal.

## Scope

_State what is in scope and what is out of scope._

src/operational_model/core/relations/order.py (nuevo)

## Implementation Path

_Outline the expected implementation route or affected surface._

assert_acyclic, topological_sequence, is_total, linear_extension sobre (nodes, edges) planos, sin depender de WiGame; tests en tests/test_order_sequence.py

## Validation

_List the checks required before this task can close._

- pytest -q tests/test_order_sequence.py
- pytest -q

## Done When

_Name the observable condition that makes the task complete._

Sobre las maquinas de tools/kb/machines/ se recupera la secuencia exacta declarada en el YAML y un ciclo es rechazado con error tipificado.
