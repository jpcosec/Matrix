---
id: task-proyeccion-wigame-y-matrices-a-s-expressions
status: draft
summary: ''
tags:
- workspace:desk
- artifact:task
routine: routine-task-proyeccion-wigame-y-matrices-a-s-expressions
current_node: checklist-task-proyeccion-wigame-y-matrices-a-s-expressions-execution-ready
history: []
references: []
depends_on: []
pills: []
files: []
checklists:
- checklist-task-proyeccion-wigame-y-matrices-a-s-expressions-execution-ready
- checklist-task-proyeccion-wigame-y-matrices-a-s-expressions-testing-ready
- checklist-task-proyeccion-wigame-y-matrices-a-s-expressions-closeout-ready
task_type: ''
inherits_from: []
inherit_acceptance_context: false
atoms: []
---

# Proyeccion: WiGame y matrices a s-expressions

## Rationale

_Explain why this task exists or the business driver behind it._

La flecha existe en un solo sentido: hay formula -> matriz (RuleMatrixCompiler) y s-expr -> sistema (SExpressionRuntime), pero no hay inverso. Ningun to_formula/from_matrix/decode existe. BooleanMatrix ya preserva row_axis y column_axis etiquetados, asi que (R a b) es recuperable.

## Goal

_Describe the concrete result this task must produce._

Emisor inverso: recuperar proposiciones desde Vi/Si usando los ejes y volcarlas como s-expressions, con modo ordenado cuando hay secuencia declarada.

## Scope

_State what is in scope and what is out of scope._

src/operational_model/system/projection_emit.py (nuevo)

## Implementation Path

_Outline the expected implementation route or affected surface._

matrix_to_s_expressions(vi, si, relation_id) sobre TRUE interseccion sinnvoll; wigame_to_s_expressions(system, wigame_id, sequence=None) estable y determinista; tests en tests/test_projection_emit.py

## Validation

_List the checks required before this task can close._

- pytest -q tests/test_projection_emit.py
- pytest -q

## Done When

_Name the observable condition that makes the task complete._

Ida y vuelta: una KB de examples/ se emite a s-expressions y al reingerirla reproduce los mismos hechos; con --sequence el orden declarado se preserva.
