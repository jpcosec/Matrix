---
id: task-relaciones-axiomas-de-orden-en-relationalgebra
status: draft
summary: ''
tags:
- workspace:desk
- artifact:task
routine: routine-task-relaciones-axiomas-de-orden-en-relationalgebra
current_node: checklist-task-relaciones-axiomas-de-orden-en-relationalgebra-execution-ready
history: []
references: []
depends_on: []
pills: []
files: []
checklists:
- checklist-task-relaciones-axiomas-de-orden-en-relationalgebra-execution-ready
- checklist-task-relaciones-axiomas-de-orden-en-relationalgebra-testing-ready
- checklist-task-relaciones-axiomas-de-orden-en-relationalgebra-closeout-ready
task_type: ''
inherits_from: []
inherit_acceptance_context: false
atoms: []
---

# Relaciones: axiomas de orden en RelationAlgebra

## Rationale

_Explain why this task exists or the business driver behind it._

Para proyectar una matriz a s-expressions con significado hace falta poder declarar que una relacion es un orden. Hoy RelationAlgebra solo expone transitive/associative/distributive/commutative: no se puede distinguir un preorden de un orden parcial ni afirmar totalidad, y `commutative` (simetria) es el axioma opuesto.

## Goal

_Describe the concrete result this task must produce._

Extender RelationAlgebra con irreflexive, antisymmetric y total, con clasificadores is_strict_partial_order()/is_total_order() y validacion de hechos compatible con los flags legacy.

## Scope

_State what is in scope and what is out of scope._

src/operational_model/core/relations/relation_algebra.py, src/operational_model/core/relation.py

## Implementation Path

_Outline the expected implementation route or affected surface._

Agregar campos y metodos a RelationAlgebra respetando los flags legacy; clasificadores; validacion de pares; tests en tests/test_relation_order_axioms.py

## Validation

_List the checks required before this task can close._

- pytest -q tests/test_relation_order_axioms.py
- pytest -q

## Done When

_Name the observable condition that makes the task complete._

Se puede declarar un orden estricto total y el algebra lo clasifica como tal; los flags legacy siguen funcionando y la suite completa pasa.
