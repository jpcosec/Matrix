---
id: task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor
status: closed
summary: ''
tags:
- workspace:desk
- artifact:task
routine: routine-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor
current_node: checklist-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-execution-ready
history: []
references: []
depends_on: []
pills: []
files: []
checklists:
- checklist-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-execution-ready
- checklist-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-testing-ready
- checklist-task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor-closeout-ready
task_type: ''
inherits_from: []
inherit_acceptance_context: false
atoms: []
---

# BlockMatrix desde el LogicalSystem: ensamblar el hipertensor

## Rationale

_Explain why this task exists or the business driver behind it._

BlockMatrix implementa la omnirrepresentacion WCi + Si + Vi y to_global_matrix() arma la matriz global de 4 bloques con ejes etiquetados, pero solo se construye en su propio test. Nadie lo ensambla desde el sistema, asi que el hipertensor existe como clase y no como capacidad.

## Goal

_Describe the concrete result this task must produce._

Ensamblar un BlockMatrix desde un LogicalSystem real: WCi desde las rutas de Context, Si y Vi desde los WiGame, preservando la indexacion de simbolos.

## Scope

_State what is in scope and what is out of scope._

src/operational_model/system/hypertensor.py (nuevo)

## Implementation Path

_Outline the expected implementation route or affected surface._

assemble_block_matrix(system, context_ids=None) construye WCi desde Context.routes (contexto x contexto), apila Si y Vi de los WiGame ruteados con ejes prefijados por wigame_id para no colisionar, y delega en BlockMatrix.to_global_matrix(); evaluate_operational() debe seguir dando Vi AND Si; tests en tests/test_hypertensor.py

## Validation

_List the checks required before this task can close._

- pytest -q tests/test_hypertensor.py
- pytest -q

## Done When

_Name the observable condition that makes the task complete._

Desde un LogicalSystem con dos contextos y dos WiGame se obtiene una matriz global cuyos ejes contienen los contextos y los sujetos, y ninguna etiqueta de simbolo se pierde ni se duplica.
