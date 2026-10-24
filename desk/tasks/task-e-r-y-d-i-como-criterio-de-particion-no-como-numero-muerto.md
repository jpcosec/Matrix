---
id: task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto
status: closed
summary: ''
tags:
- workspace:desk
- artifact:task
current_node: ritual-execution
history: []
references: []
depends_on: []
pills: []
files: []
task_type: ''
inherits_from: []
inherit_acceptance_context: false
atoms: []
---

# E(R) y D_i como criterio de particion, no como numero muerto

## Rationale

_Explain why this task exists or the business driver behind it._

information_energy() y tautological_columns() se calculan pero no alimentan ninguna decision: el unico consumidor es capabilities.py, que solo verifica que E sea un float. El criterio para partir el hipertensor en W cerrados tiene que leer esos numeros. Medido: descomponer grosor_hoja en tiene_parte+grosor baja E de 0.75 a 0.625 porque 'hoja' queda como columna tautologica, asi que el criterio no es 'menos entropia' sino poder discriminativo mas reuso del termino medio.

## Goal

_Describe the concrete result this task must produce._

Funcion de particion que compare una forma compuesta contra su descomposicion por termino medio y decida, usando D_i, E(R), celdas y reuso, cual conviene.

## Scope

_State what is in scope and what is out of scope._

src/operational_model/system/partition.py (nuevo)

## Implementation Path

_Outline the expected implementation route or affected surface._

score_wigame(wigame) -> metricas (celdas, densidad, E, columnas tautologicas, D_i); compare_partition(compuesto, partes) -> veredicto con motivo, contando el reuso del termino medio y el costo en celdas; debe reproducir que con 3 sujetos gana el compuesto y con muchos sujetos gana el descompuesto; tests en tests/test_partition.py

## Validation

_List the checks required before this task can close._

- pytest -q tests/test_partition.py
- pytest -q

## Done When

_Name the observable condition that makes the task complete._

El veredicto cambia de compuesto a descompuesto al crecer el numero de sujetos que comparten el termino medio, y el motivo cita la metrica que decidio.
