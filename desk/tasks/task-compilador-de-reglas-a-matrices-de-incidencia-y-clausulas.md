---
# task-xxx, unique task identifier
id: task-compilador-de-reglas-a-matrices-de-incidencia-y-clausulas
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
routine: routine-task-compilador-de-reglas-a-matrices-de-incidencia-y-clausulas
# Checklist identifiers for verification
checklists:
- checklist-task-compilador-de-reglas-a-matrices-de-incidencia-y-clausulas-execution-ready
- checklist-task-compilador-de-reglas-a-matrices-de-incidencia-y-clausulas-testing-ready
- checklist-task-compilador-de-reglas-a-matrices-de-incidencia-y-clausulas-closeout-ready
# Active routine node
current_node: checklist-task-compilador-de-reglas-a-matrices-de-incidencia-y-clausulas-closeout-ready
# Execution history references
history:
- operator-task-compilador-de-reglas-a-matrices-de-incidencia-y-clausulas-activate
- operator-task-compilador-de-reglas-a-matrices-de-incidencia-y-clausulas-ready-for-testing
# e.g., system:deskops, topic:cli
tags:
- workspace:desk
- artifact:task
---

# Compilador de Reglas a Matrices de Incidencia y Clausulas

## Rationale

_Explain why this task exists or the business driver behind it._

Compilar formulas FBF a matrices de implicaciones I y matrices de clausulas (C+, C-)

## Goal

_Describe the concrete result this task must produce._

Crear RuleMatrixCompiler para eliminar la necesidad de interpretar AST en tiempo de inferencia

## Scope

_State what is in scope and what is out of scope._

src/operational_model/kernel/rule_matrix.py

## Implementation Path

_Outline the expected implementation route or affected surface._



## Validation

_List the checks required before this task can close._

- RuleMatrixCompiler compila implicaciones y clausulas CNF a BooleanMatrix y pasa pytest

## Done When

_Name the observable condition that makes the task complete._
