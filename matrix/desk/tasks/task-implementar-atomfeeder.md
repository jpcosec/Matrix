---
# task-xxx, unique task identifier
id: task-implementar-atomfeeder
# draft | active | blocked | closed
status: draft
# Relevant file or doc paths
references: []
# Task identifiers that must complete first
depends_on: []
# Pill identifiers required
pills: []
# Files expected to change
files: []
# Routine identifier for operations
routine: routine-task-implementar-atomfeeder
# Checklist identifiers for verification
checklists:
- checklist-task-implementar-atomfeeder-execution-ready
- checklist-task-implementar-atomfeeder-testing-ready
- checklist-task-implementar-atomfeeder-closeout-ready
# Active routine node
current_node: checklist-task-implementar-atomfeeder-execution-ready
# Execution history references
history: []
# e.g., system:deskops, topic:cli
tags:
- workspace:desk
- artifact:task
---

# Implementar AtomFeeder

## Rationale

_Explain why this task exists or the business driver behind it._

Not provided.

## Goal

_Describe the concrete result this task must produce._

Ingesta O(1) de hechos puros saltando el parser

## Scope

_State what is in scope and what is out of scope._

src/operational_model/compiler/feeders/atom_feeder.py

## Implementation Path

_Outline the expected implementation route or affected surface._



## Validation

_List the checks required before this task can close._

- Inyecta coordenadas directas al compiler

## Done When

_Name the observable condition that makes the task complete._
