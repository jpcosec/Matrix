---
# task-xxx, unique task identifier
id: task-inferencia-deductiva-proposicional-matricial
# draft | active | blocked | closed
status: ready_for_testing
# Relevant file or doc paths
references: []
# Task identifiers that must complete first
depends_on:
- task-compilador-de-reglas-a-matrices-de-incidencia-y-clausulas
# Pill identifiers required
pills: []
# Files expected to change
files: []
# Routine identifier for operations
routine: routine-task-inferencia-deductiva-proposicional-matricial
# Checklist identifiers for verification
checklists:
- checklist-task-inferencia-deductiva-proposicional-matricial-execution-ready
- checklist-task-inferencia-deductiva-proposicional-matricial-testing-ready
- checklist-task-inferencia-deductiva-proposicional-matricial-closeout-ready
# Active routine node
current_node: checklist-task-inferencia-deductiva-proposicional-matricial-closeout-ready
# Execution history references
history:
- operator-task-inferencia-deductiva-proposicional-matricial-activate
- operator-task-inferencia-deductiva-proposicional-matricial-ready-for-testing
# e.g., system:deskops, topic:cli
tags:
- workspace:desk
- artifact:task
---

# Inferencia Deductiva Proposicional Matricial

## Rationale

_Explain why this task exists or the business driver behind it._

Reemplazar la inferencia sobre AST por Modus Ponens matricial (v ⊗ I*) y evaluacion de bitmasks

## Goal

_Describe the concrete result this task must produce._

Ejecutar Modus Ponens, Silogismo Hipotetico y Silogismo Disyuntivo como multiplicaciones matriciales y bitwise masks

## Scope

_State what is in scope and what is out of scope._

src/operational_model/kernel/formula_inference.py

## Implementation Path

_Outline the expected implementation route or affected surface._



## Validation

_List the checks required before this task can close._

- formula_inference.py usa v ⊗ I* sin bucles AST y pasa 100% de pytest

## Done When

_Name the observable condition that makes the task complete._
