---
# board-xxx
id: board-001
# Affected workspace or domain
scope: desk
# List of task-xxx paths
tasks:
- desk/tasks/task-relaciones-axiomas-de-orden-en-relationalgebra.md
- desk/tasks/task-orden-acyclidad-y-secuencia-lineal-dentro-de-w.md
- desk/tasks/task-proyeccion-wigame-y-matrices-a-s-expressions.md
- desk/tasks/task-proyeccion-objeto-sujeto-encadenar-por-termino-medio.md
- desk/tasks/task-guardas-de-forma-detectar-w-degenerados-tipo-relacion-universal.md
- desk/tasks/task-blockmatrix-desde-el-logicalsystem-ensamblar-el-hipertensor.md
- desk/tasks/task-e-r-y-d-i-como-criterio-de-particion-no-como-numero-muerto.md
# List of pill-xxx paths
pills:
- desk/contexts/pills.md
# List of ritual-xxx paths
rituals:
- desk/rituals/execution.md
- desk/rituals/testing.md
- desk/rituals/closeout.md
# e.g., system:sldb, workspace:desk
tags:
- workspace:desk
---

# Matrix Board

## Purpose

_Explain what this board routes and why it exists._



## Notes

_Add short operational notes about the current routed set._

The state of the engine lives in each `WiGame`; there is no global
Hipertensor. See `desk/drawer/jax/README.md`.

## Task Details

_Generated from the task references above._

- Relaciones: axiomas de orden en RelationAlgebra [closed] - Extender RelationAlgebra con irreflexive, antisymmetric y total, con clasificadores is_strict_partial_order()/is_total_order() y validacion de hechos compatible con los flags legacy.
- Orden: acyclidad y secuencia lineal dentro de W [closed] - Modulo de orden sobre aristas: validacion de acyclidad con error tipificado, orden topologico determinista, deteccion de totalidad y extension lineal.
- Proyeccion: WiGame y matrices a s-expressions [closed] - Emisor inverso: recuperar proposiciones desde Vi/Si usando los ejes y volcarlas como s-expressions, con modo ordenado cuando hay secuencia declarada.
- Proyeccion objeto-sujeto: encadenar por termino medio [draft] - Proyeccion objeto->sujeto entre dos WiGame que comparten termino medio, con composicion de hechos a traves del cruce y sin inventar simbolos.
- Guardas de forma: detectar W degenerados tipo relacion universal [draft] - Diagnostico de forma de un WiGame que detecte relacion universal, objetos que empaquetan relacion, objetos conjuntivos y columnas no discriminativas, con severidad y motivo.
- BlockMatrix desde el LogicalSystem: ensamblar el hipertensor [draft] - Ensamblar un BlockMatrix desde un LogicalSystem real: WCi desde las rutas de Context, Si y Vi desde los WiGame, preservando la indexacion de simbolos.
- E(R) y D_i como criterio de particion, no como numero muerto [draft] - Funcion de particion que compare una forma compuesta contra su descomposicion por termino medio y decida, usando D_i, E(R), celdas y reuso, cual conviene.
