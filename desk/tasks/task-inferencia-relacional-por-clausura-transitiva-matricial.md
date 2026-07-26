---
# task-xxx, unique task identifier
id: task-inferencia-relacional-por-clausura-transitiva-matricial
# draft | active | blocked | closed
status: ready_for_testing
# Relevant file or doc paths
references: []
# Task identifiers that must complete first
depends_on:
- task-vectorizacion-bitwise-denso-de-booleanmatrix
# Pill identifiers required
pills: []
# Files expected to change
files: []
# Routine identifier for operations
routine: routine-task-inferencia-relacional-por-clausura-transitiva-matricial
# Checklist identifiers for verification
checklists:
- checklist-task-inferencia-relacional-por-clausura-transitiva-matricial-execution-ready
- checklist-task-inferencia-relacional-por-clausura-transitiva-matricial-testing-ready
- checklist-task-inferencia-relacional-por-clausura-transitiva-matricial-closeout-ready
# Active routine node
current_node: checklist-task-inferencia-relacional-por-clausura-transitiva-matricial-closeout-ready
# Execution history references
history:
- operator-task-inferencia-relacional-por-clausura-transitiva-matricial-activate
- operator-task-inferencia-relacional-por-clausura-transitiva-matricial-ready-for-testing
# e.g., system:deskops, topic:cli
tags:
- workspace:desk
- artifact:task
---

# Inferencia Relacional por Clausura Transitiva Matricial

## Rationale

_Explain why this task exists or the business driver behind it._

Sustituir recorridos sobre diccionarios por clausura transitiva matricial MR*

## Goal

_Describe the concrete result this task must produce._

Calcular la inferencia transitiva aRb ∧ bRc => aRc mediante MR.recursive_power()

## Scope

_State what is in scope and what is out of scope._

src/operational_model/core/transitive_inference.py

## Implementation Path

_Outline the expected implementation route or affected surface._



## Validation

_List the checks required before this task can close._

- transitive_inference.py usa BooleanMatrix.transitive_closure y pasa 100% de pytest

## Done When

_Name the observable condition that makes the task complete._
