---
# task-xxx, unique task identifier
id: task-canonicalhypertensor-jit-bitwise-operations
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
routine: routine-task-canonicalhypertensor-jit-bitwise-operations
# Checklist identifiers for verification
checklists:
- checklist-task-canonicalhypertensor-jit-bitwise-operations-execution-ready
- checklist-task-canonicalhypertensor-jit-bitwise-operations-testing-ready
- checklist-task-canonicalhypertensor-jit-bitwise-operations-closeout-ready
# Active routine node
current_node: checklist-task-canonicalhypertensor-jit-bitwise-operations-execution-ready
# Execution history references
history: []
# e.g., system:deskops, topic:cli
tags:
- workspace:desk
- artifact:task
---

# CanonicalHypertensor: JIT Bitwise Operations

## Rationale

_Explain why this task exists or the business driver behind it._

Not provided.

## Goal

_Describe the concrete result this task must produce._

Funciones JAX compiladas para multiplicacion booleana densa

## Scope

_State what is in scope and what is out of scope._

src/operational_model/system/canonical_hypertensor.py

## Implementation Path

_Outline the expected implementation route or affected surface._



## Validation

_List the checks required before this task can close._

- Multiplicacion matricial compila exitosamente en XLA

## Done When

_Name the observable condition that makes the task complete._
