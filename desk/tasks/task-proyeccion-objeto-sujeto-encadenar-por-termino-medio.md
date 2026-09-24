---
id: task-proyeccion-objeto-sujeto-encadenar-por-termino-medio
status: closed
summary: ''
tags:
- workspace:desk
- artifact:task
routine: routine-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio
current_node: checklist-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-execution-ready
history: []
references: []
depends_on: []
pills: []
files: []
checklists:
- checklist-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-execution-ready
- checklist-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-testing-ready
- checklist-task-proyeccion-objeto-sujeto-encadenar-por-termino-medio-closeout-ready
task_type: ''
inherits_from: []
inherit_acceptance_context: false
atoms: []
---

# Proyeccion objeto-sujeto: encadenar por termino medio

## Rationale

_Explain why this task exists or the business driver behind it._

RoutingProjection solo conecta sujeto con sujeto. El cruce real entre W es el termino medio: objeto de W1 que es sujeto de W2, como 'guisarse' en (debe legumbre guisarse)+(necesita guisarse fuego) o 'hoja' en (tiene_parte planta hoja)+(grosor hoja gruesa). Hoy ese encadenamiento no existe y TransitiveInference filtra por relation_id, asi que relaciones distintas nunca encadenan.

## Goal

_Describe the concrete result this task must produce._

Proyeccion objeto->sujeto entre dos WiGame que comparten termino medio, con composicion de hechos a traves del cruce y sin inventar simbolos.

## Scope

_State what is in scope and what is out of scope._

src/operational_model/routing/middle_term.py (nuevo)

## Implementation Path

_Outline the expected implementation route or affected surface._

middle_terms(w1,w2) = interseccion de w1.axis_b con w2.axis_a; compose(w1,w2) devuelve los pares (sujeto_w1, objeto_w2) alcanzables via termino medio, respetando Vi AND Si en ambos lados; no crea simbolos ni relaciones nuevas; tests en tests/test_middle_term.py

## Validation

_List the checks required before this task can close._

- pytest -q tests/test_middle_term.py
- pytest -q

## Done When

_Name the observable condition that makes the task complete._

Con (debe legumbre guisarse)+(necesita guisarse fuego) la composicion entrega (legumbre, fuego) y el termino medio queda explicito; una celda sinnlos o unsinnig en cualquiera de los dos lados corta la cadena.
