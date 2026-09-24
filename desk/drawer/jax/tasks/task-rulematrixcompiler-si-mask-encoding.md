---
# task-xxx, unique task identifier
id: task-rulematrixcompiler-si-mask-encoding
# draft | active | blocked | closed | deferred
status: deferred
# Relevant file or doc paths
references: []
# Task identifiers that must complete first
depends_on: []
# Pill identifiers required
pills: []
# Files expected to change
files: []
# Routine identifier for operations
routine: routine-task-rulematrixcompiler-si-mask-encoding
# Checklist identifiers for verification
checklists:
- checklist-task-rulematrixcompiler-si-mask-encoding-execution-ready
- checklist-task-rulematrixcompiler-si-mask-encoding-testing-ready
- checklist-task-rulematrixcompiler-si-mask-encoding-closeout-ready
# Active routine node
current_node: checklist-task-rulematrixcompiler-si-mask-encoding-execution-ready
# Execution history references
history: []
# e.g., system:deskops, topic:cli
tags:
- workspace:desk
- artifact:task
---

# RuleMatrixCompiler: Si Mask Encoding

## Rationale

_Explain why this task exists or the business driver behind it._

Not provided.

## Goal

_Describe the concrete result this task must produce._

Traducir SOP a coordenadas cartesianas de la matriz Si

## Scope

_State what is in scope and what is out of scope._

src/operational_model/compiler/rule_compiler.py

## Implementation Path

_Outline the expected implementation route or affected surface._



## Validation

_List the checks required before this task can close._

- Convierte Mintermos a (row, col) compatibles con JAX

## Done When

_Name the observable condition that makes the task complete._
